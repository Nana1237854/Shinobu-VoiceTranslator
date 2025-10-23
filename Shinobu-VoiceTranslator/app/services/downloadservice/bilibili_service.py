# coding:utf-8
import re
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .base_download_service import BaseDownloadService, DownloadWorker
from ...common.database.entity.task import Task, TaskStatus, TaskType
from ...common.config import cfg
from ...common.concurrent import Future, FutureFailed


class BilibiliDownloader:
    """B站下载器"""
    
    def __init__(self, output_dir: str = None):
        self.logger = logging.getLogger("BilibiliDownloader")
        self.output_dir = Path(output_dir or cfg.get(cfg.saveFolder))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试导入 bilibili_dl
        self.bilibili_dl_available = False
        try:
            from bilibili_dl.bilibili_dl.Video import Video
            from bilibili_dl.bilibili_dl.downloader import download
            from bilibili_dl.bilibili_dl.utils import send_request
            from bilibili_dl.bilibili_dl.constants import URL_VIDEO_INFO
            
            self.Video = Video
            self.download_func = download
            self.send_request = send_request
            self.URL_VIDEO_INFO = URL_VIDEO_INFO
            self.bilibili_dl_available = True
            self.logger.info("bilibili_dl 库加载成功")
        except ImportError as e:
            self.logger.warning(f"bilibili_dl 未安装: {e}")
    
    def download(self, video_id: str, proxy: Optional[str] = None, 
                 status_callback: Optional[callable] = None) -> str:
        """下载B站视频"""
        if not self.bilibili_dl_available:
            raise ImportError("bilibili_dl 库未安装")
        
        import os
        
        try:
            if not video_id.startswith('BV'):
                raise ValueError(f"无效的B站视频ID: {video_id}")
            
            self.logger.info(f"开始下载B站视频: {video_id}")
            if status_callback:
                status_callback("[INFO] 正在获取视频信息...")
            
            # 获取视频信息
            res = self.send_request(self.URL_VIDEO_INFO, params={'bvid': video_id})
            if not res:
                raise Exception("获取视频信息失败")
            
            # 处理视频信息
            is_single_video = res.get('videos', 1) == 1
            
            if is_single_video:
                video_info = self.Video(
                    bvid=res['bvid'],
                    cid=res['cid'],
                    title=res['title'],
                    up_name=res['owner']['name'],
                    cover_url=res['pic']
                )
                title = res['title']
            else:
                first_page = res['pages'][0]
                video_info = self.Video(
                    bvid=res['bvid'],
                    cid=first_page['cid'],
                    title=first_page['part'],
                    up_name=res['owner']['name'],
                    cover_url=first_page.get('first_frame', res['pic'])
                )
                title = first_page['part']
            
            self.logger.info(f"视频标题: {title}")
            if status_callback:
                status_callback(f"[INFO] 正在下载视频: {title}")
            
            safe_title = self._sanitize_filename(title)
            
            # 切换到输出目录进行下载
            original_cwd = os.getcwd()
            try:
                os.chdir(str(self.output_dir))
                self.download_func([video_info], False)
                output_file = self._find_downloaded_file(safe_title)
                
                if not output_file:
                    raise FileNotFoundError(f"下载完成但未找到文件: {safe_title}.mp4")
                
                self.logger.info(f"B站视频下载完成: {output_file}")
                if status_callback:
                    status_callback("[INFO] 视频下载完成！")
                
                return str(Path(output_file).absolute())
            finally:
                os.chdir(original_cwd)
        
        except Exception as e:
            self.logger.error(f"B站视频下载失败: {e}")
            if status_callback:
                status_callback(f"[ERROR] 下载失败: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        safe_name = re.sub(r'[.:?/\\*"<>|]', ' ', filename)
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
        return safe_name[:200] if len(safe_name) > 200 else safe_name
    
    def _find_downloaded_file(self, title: str) -> Optional[Path]:
        """查找下载的视频文件"""
        extensions = ['.mp4', '.flv', '.avi']
        
        # 精确匹配
        for ext in extensions:
            file_path = self.output_dir / f"{title}{ext}"
            if file_path.exists():
                return file_path
        
        # 模糊匹配
        for ext in extensions:
            for file in self.output_dir.glob(f"*{ext}"):
                if title in file.stem:
                    return file
        
        # 返回最新文件
        video_files = []
        for ext in extensions:
            video_files.extend(self.output_dir.glob(f"*{ext}"))
        
        if video_files:
            return max(video_files, key=lambda p: p.stat().st_mtime)
        
        return None


class BilibiliService(BaseDownloadService):
    """B站下载服务 - 使用 TaskExecutor"""
    
    def __init__(self):
        super().__init__()
        self.downloader = BilibiliDownloader()
        self._available = self.downloader.bilibili_dl_available
    
    def createTask(self, url: str, **kwargs) -> Optional[Task]:
        """创建B站下载任务"""
        # 从URL提取BV号
        video_id = self._extract_bv_id(url)
        if not video_id:
            self._addLog("ERROR", f"无效的B站链接: {url}")
            return None
        
        task = Task(
            type=TaskType.DOWNLOAD.value,
            status=TaskStatus.PENDING,
            url=video_id,
            source="bilibili",
            fileName=f"{video_id}.mp4",
            extraParams=kwargs
        )
        
        # 保存到数据库
        self.db.save_task(task)
        
        # 发出任务创建信号
        self.taskCreated.emit(task)
        
        # 自动开始任务
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
            def status_callback(message: str):
                # 注意：这里的日志会在工作线程中调用
                # Signal-Slot 机制会自动切换到主线程
                self._addLog("INFO", message)
            
            try:
                output_path = self.downloader.download(
                    task.url, 
                    status_callback=status_callback
                )
                return output_path
            except Exception as e:
                # 在工作线程中捕获异常并抛出
                raise e
        
        # 使用 TaskExecutor 异步执行
        future = self.asyncRun(download_task)
        
        # 绑定成功回调 - 会在主线程中执行
        future.result.connect(lambda result: self._onDownloadSuccess(task, result))
        
        # 绑定失败回调 - 会在主线程中执行
        future.failed.connect(lambda error: self._onDownloadFailed(task, error))
        
        # 保存 Future 引用
        self.futures[task.id] = future
        
        self._addLog("INFO", f"开始下载B站视频: {task.url}")
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
    
    def _extract_bv_id(self, url: str) -> Optional[str]:
        """从URL提取BV号"""
        if url.startswith('BV'):
            return url
        
        # 匹配 https://www.bilibili.com/video/BV...
        match = re.search(r'BV[\w]+', url)
        return match.group(0) if match else None