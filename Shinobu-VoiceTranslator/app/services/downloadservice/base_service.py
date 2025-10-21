import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from PySide6.QtCore import QObject, QThread, Signal

from ...common.database.entity.task import Task, TaskStatus
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

class BaseDownloadService(QObject):
    """下载服务基类"""
    taskCreated = Signal(Task)   # 任务创建信号
    taskFinished = Signal(Task, bool, str)   # 任务完成信号
    taskUpdated = Signal(Task)   # 任务更新信号
    logGenerated = Signal(str, str)   # 日志生成信号

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = getTaskService()
        self.workers = {}  # 任务ID -> Worker映射
        self._available = False
        self.log_cache = []  # 日志缓存

    def isAvailable(self) -> bool:
        """判断服务是否可用"""
        return self._available

    def createTask(self, url: str, **kwargs) -> Optional[Task]:
        """创建下载任务"""
        raise NotImplementedError

    def start(self, task: Task) -> bool:
        """开始任务"""
        raise NotImplementedError

    def restart(self, task: Task) -> bool:
        """重启任务"""
        # 重置任务状态
        task.status = TaskStatus.PENDING
        task.progress = 0.0
        task.errorMsg = ""
        task.startTime = None
        task.endTime = None

        # 保存到数据库
        self.db.save_task(task)

        # 开始任务
        return self.start(task)

    
    def cancel(self, task: Task) -> bool:
        """取消任务"""
        if task.id in self.workers:
            worker = self.workers[task.id]
            worker.cancel()
            worker.wait(3000)  # 等待最多3秒
            if worker.isRunning():
                worker.terminate()  # 强制终止
            del self.workers[task.id]
            
            task.status = TaskStatus.CANCELLED
            self.db.save_task(task)
            return True
        else:
            return False
    
    def cleanup(self):
        """清理所有工作线程"""
        for task_id, worker in list(self.workers.items()):
            if worker and worker.isRunning():
                worker.cancel()
                worker.wait(1000)  # 等待最多1秒
                if worker.isRunning():
                    worker.terminate()  # 强制终止
        self.workers.clear()
        
    def showLog(self):
        """显示日志"""
        # 切换到日志标签
        signalBus.switchToTaskInterfaceSig.emit()

    def _addLog(self, level: str, message: str):
        """添加日志"""
        self.log_cache.append((level, message))
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message)
        signalBus.logGenerated.emit(level, message)

    def _onWorkerProgress(self, task: Task, progress: float, speed: str, eta: str):
        """处理进度变化"""
        task.progress = progress
        task.speed = speed
        task.eta = eta
        self.db.save_task(task)
        self.taskUpdated.emit(task)
    
    def _onWorkerFinished(self, task: Task, success: bool, error_msg: str):
        """处理任务完成"""
        task.endTime = datetime.now()
        
        if success:
            task.status = TaskStatus.SUCCESS
            task.progress = 100.0
            self._addLog("INFO", f"任务完成: {task.fileName}")
        else:
            task.status = TaskStatus.FAILED
            task.errorMsg = error_msg
            self._addLog("ERROR", f"任务失败: {task.fileName} - {error_msg}")
        
        self.db.save_task(task)
        self.taskFinished.emit(task, success, error_msg)
        
        # 清理worker
        if task.id in self.workers:
            del self.workers[task.id]
