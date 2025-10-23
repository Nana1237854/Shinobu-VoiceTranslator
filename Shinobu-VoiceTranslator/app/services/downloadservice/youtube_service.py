# coding:utf-8
import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

from .base_download_service import BaseDownloadService
from ...common.database.entity import Task, TaskStatus, TaskType
from ...common.config import cfg
from ...common.concurrent import Future, FutureFailed


class YouTubeDownloader:
    """YouTube下载器"""
    
    def __init__(self, output_dir: str = None):
        self.logger = logging.getLogger("YouTubeDownloader")
        self.output_dir = Path(output_dir or cfg.get(cfg.saveFolder))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查 yt-dlp 是否可用
        self.ytdlp_available = False
        try:
            import yt_dlp
            self.YoutubeDL = yt_dlp.YoutubeDL
            self.ytdlp_available = True
            self.logger.info("yt-dlp 库加载成功")
        except ImportError as e:
            self.logger.warning(f"yt-dlp 未安装: {e}")
    
    def download(self, url: str, proxy: str = None, 
                 status_callback: Optional[callable] = None) -> str:
        """下载YouTube视频"""
        if not self.ytdlp_available:
            raise ImportError("yt-dlp 库未安装")
        
        try:
            self.logger.info(f"开始下载YouTube视频: {url}")
            if status_callback:
                status_callback("[INFO] 正在下载YouTube视频...")
            
            # 从URL提取视频ID
            video_id = self._extract_video_id(url)
            output_template = str(self.output_dir / f"{video_id}.%(ext)s")
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_template,
                'quiet': False,
            }
            
            if proxy:
                ydl_opts['proxy'] = proxy
            
            with self.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            if not Path(filename).exists():
                raise FileNotFoundError(f"下载失败: {filename}")
            
            self.logger.info(f"YouTube视频下载完成: {filename}")
            if status_callback:
                status_callback("[INFO] 视频下载完成！")
            
            return filename
        
        except Exception as e:
            self.logger.error(f"YouTube视频下载失败: {e}")
            if status_callback:
                status_callback(f"[ERROR] 下载失败: {e}")
            raise
    
    def _extract_video_id(self, url: str) -> str:
        """从URL提取视频ID"""
        # 匹配 youtube.com/watch?v=VIDEO_ID 或 youtu.be/VIDEO_ID
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 如果没有匹配到，可能直接是视频ID
        return url.split('/')[-1].split('?')[0]


class YouTubeService(BaseDownloadService):
    """YouTube下载服务 - 使用 TaskExecutor"""
    
    def __init__(self):
        super().__init__()
        self.downloader = YouTubeDownloader()
        self._available = self.downloader.ytdlp_available
    
    def createTask(self, url: str, **kwargs) -> Optional[Task]:
        """创建YouTube下载任务"""
        video_id = self.downloader._extract_video_id(url)
        
        task = Task(
            type=TaskType.DOWNLOAD.value,
            status=TaskStatus.PENDING,
            url=url,
            source="youtube",
            fileName=f"{video_id}.mp4",
            config=kwargs
        )
        
        self.db.save_task(task)
        self.taskCreated.emit(task)
        self.start(task)
        
        return task
    
    def start(self, task: Task) -> bool:
        """使用 TaskExecutor 开始下载任务"""
        if task.id in self.futures:
            self._addLog("WARNING", f"任务已在运行: {task.fileName}")
            return False
        
        task.status = TaskStatus.RUNNING
        task.startTime = datetime.now()
        self.db.save_task(task)
        self._emit_task_updated(task)
        
        # 定义下载任务函数
        def download_task():
            """在线程池中执行的下载函数"""
            # 创建状态回调函数
            def status_callback(message: str):
                # Signal-Slot 机制会自动切换到主线程
                self._addLog("INFO", message)
            
            # 执行下载
            output_path = self.downloader.download(
                task.url, 
                proxy=task.config.get('proxy'),
                status_callback=status_callback
            )
            return output_path
        
        # 使用 TaskExecutor 异步执行
        future = self.asyncRun(download_task)
        
        # 绑定成功回调 - 会在主线程中执行
        future.result.connect(lambda output_path: self._onDownloadSuccess(task, output_path))
        
        # 绑定失败回调 - 会在主线程中执行
        future.failed.connect(lambda error: self._onDownloadFailed(task, error))
        
        # 保存 Future 引用
        self.futures[task.id] = future
        
        self._addLog("INFO", f"开始下载YouTube视频: {task.url}")
        return True
    
    def _onDownloadSuccess(self, task: Task, output_path: str):
        """下载成功的回调 - 在主线程中执行"""
        task.outputPath = output_path
        task.progress = 100.0
        self._onWorkerFinished(task, True, "下载完成")
    
    def _onDownloadFailed(self, task: Task, error: FutureFailed):
        """下载失败的回调 - 在主线程中执行"""
        error_msg = str(error.exception) if hasattr(error, 'exception') else str(error)
        self._onWorkerFinished(task, False, error_msg)