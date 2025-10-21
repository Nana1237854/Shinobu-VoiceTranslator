# coding:utf-8
import re
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .base_service import BaseDownloadService, DownloadWorker
from ...common.database.entity.task import Task, TaskStatus, TaskType
from ...common.config import cfg


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
    """B站下载服务"""
    
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
        """开始下载任务"""
        if task.id in self.workers:
            self._addLog("WARNING", f"任务已在运行: {task.fileName}")
            return False
        
        task.status = TaskStatus.RUNNING
        task.startTime = datetime.now()
        self.db.save_task(task)
        
        # 创建工作线程
        worker = DownloadWorker(task, self.downloader)
        worker.progressChanged.connect(lambda p, s, e: self._onWorkerProgress(task, p, s, e))
        worker.finished.connect(lambda success, msg: self._onWorkerFinished(task, success, msg))
        worker.logGenerated.connect(self._addLog)
        
        self.workers[task.id] = worker
        worker.start()
        
        self._addLog("INFO", f"开始下载B站视频: {task.url}")
        return True
    
    def _extract_bv_id(self, url: str) -> Optional[str]:
        """从URL提取BV号"""
        if url.startswith('BV'):
            return url
        
        # 匹配 https://www.bilibili.com/video/BV...
        match = re.search(r'BV[\w]+', url)
        return match.group(0) if match else None