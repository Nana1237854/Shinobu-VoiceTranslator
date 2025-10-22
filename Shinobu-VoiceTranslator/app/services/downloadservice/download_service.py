# coding:utf-8
from typing import Optional
from .bilibili_service import BilibiliService
from .youtube_service import YouTubeService
from .base_download_service import BaseDownloadService
from ...common.database import sqlRequest
from ...common.database.entity import Task
from ...common.utils import removeFile, showInFolder


class UnifiedDownloadService(BaseDownloadService):
    """统一下载服务 - 根据URL自动选择下载器"""
    
    def __init__(self):
        super().__init__()
        self.bilibili_service = BilibiliService()
        self.youtube_service = YouTubeService()
        
        # 连接子服务的信号
        for service in [self.bilibili_service, self.youtube_service]:
            service.taskCreated.connect(self.taskCreated.emit)
            service.taskUpdated.connect(self.taskUpdated.emit)
            service.taskFinished.connect(self.taskFinished.emit)
            service.logGenerated.connect(self.logGenerated.emit)
        
        # 服务可用性：至少一个下载器可用
        self._available = (self.bilibili_service.isAvailable() or 
                          self.youtube_service.isAvailable())
    
    def createTask(self, url: str, **kwargs) -> Optional[Task]:
        """根据URL自动创建相应的下载任务"""
        if 'bilibili.com' in url or 'BV' in url:
            return self.bilibili_service.createTask(url, **kwargs)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return self.youtube_service.createTask(url, **kwargs)
        else:
            self._addLog("ERROR", f"不支持的下载链接: {url}")
            return None
    
    def start(self, task: Task) -> bool:
        """开始任务"""
        if task.source == "bilibili":
            return self.bilibili_service.start(task)
        elif task.source == "youtube":
            return self.youtube_service.start(task)
        else:
            self._addLog("ERROR", f"未知的任务来源: {task.source}")
            return False
    
    def restart(self, task: Task) -> bool:
        """重启任务"""
        if task.source == "bilibili":
            return self.bilibili_service.restart(task)
        elif task.source == "youtube":
            return self.youtube_service.restart(task)
        else:
            return False
    
    def cancel(self, task: Task):
        """取消任务"""
        if task.source == "bilibili":
            self.bilibili_service.cancel(task)
        elif task.source == "youtube":
            self.youtube_service.cancel(task)


# 全局服务实例
downloadService = UnifiedDownloadService()