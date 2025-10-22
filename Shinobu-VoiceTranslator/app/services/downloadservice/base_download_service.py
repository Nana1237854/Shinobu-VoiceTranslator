import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from PySide6.QtCore import QObject, QThread, Signal

from ...common.database.entity.task import Task, TaskStatus, TaskType
from ..base_service import BaseService
from ...common.database import getTaskService
from ...common.signal_bus import signalBus

class DownloadWorker(QThread):
    """下载工作线程"""
    progressChanged = Signal(float, str, str)   # 进度，状态，消息
    finished = Signal(bool, str)   # 是否成功，消息
    logGenerated = Signal(str, str)   # 日志级别，日志消息

    def __init__(self, task: Task, downloader, parent=None):
        super().__init__(parent)
        self.task = task
        self.downloader = downloader
        self._is_cancelled = False

    def run(self):
        """运行下载任务"""
        try:
            self.logGenerated.emit("INFO", f"开始下载: {self.task.url}")

            # 状态回调
            def status_callback(message: str):
                self.logGenerated.emit("INFO", message)
                
            # 下载
            output_path = self.downloader.download(self.task.url, status_callback)

            if self._is_cancelled:
                self.finished.emit(False, "任务已取消")
                return
            
            self.task.outputPath = output_path
            self.task.progress = 100.0
            self.finished.emit(True, "下载完成")
            
        except Exception as e:
            error_msg = str(e)
            self.logGenerated.emit("ERROR", f"下载失败: {error_msg}")
            self.finished.emit(False, error_msg)

    def cancel(self):
        """取消下载"""
        self._is_cancelled = True

class BaseDownloadService(BaseService):
    """下载服务基类"""
    taskCreated = Signal(Task)   # 任务创建信号
    taskFinished = Signal(Task, bool, str)   # 任务完成信号
    taskUpdated = Signal(Task)   # 任务更新信号
    logGenerated = Signal(str, str)   # 日志生成信号

    def __init__(self):
        super().__init__(TaskType.DOWNLOAD)
        
    def isAvailable(self) -> bool:
        """判断服务是否可用"""
        # 具体可用性由子类实现
        return self._available

    def createTask(self, url: str, **kwargs) -> Optional[Task]:
        """创建下载任务"""
        # 具体下载创建逻辑由子类实现

    def start(self, task: Task) -> bool:
        """开始任务"""
        # 具体下载开始逻辑由子类实现
