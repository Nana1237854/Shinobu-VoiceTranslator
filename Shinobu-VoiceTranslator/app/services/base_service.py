from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from PySide6.QtCore import QObject, QThread, Signal

from ..common.database.entity.task import Task, TaskStatus, TaskType
from ..common.database import getTaskService
from ..common.signal_bus import signalBus

class BaseService(QObject, ABC):
    """服务基类"""
    def __init__(self, service_type: TaskType):
        super().__init__()
        self.service_type = service_type
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = getTaskService()
        self.workers = {}  # 任务ID -> Worker映射
        self._available = False
        self.log_cache = []  # 日志缓存


    @abstractmethod
    def isAvailable(self) -> bool:
        """判断服务是否可用"""
        return self._available

    @abstractmethod
    def createTask(self, **kwargs) -> Optional[Task]:
        """创建任务 - 子类实现具体逻辑"""
        raise NotImplementedError

    @abstractmethod
    def start(self, task: Task) -> bool:
        """开始任务 - 子类实现具体逻辑"""
        raise NotImplementedError

    def restart(self, task: Task) -> bool:
        """重启任务 - 通用实现"""
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
        """取消任务 - 通用实现"""
        if task.id in self.workers:
            worker = self.workers[task.id]
            if hasattr(worker, 'cancel'):
                worker.cancel()
            if hasattr(worker, 'wait'):
                worker.wait(3000)  # 等待最多3秒
            if hasattr(worker, 'isRunning') and worker.isRunning():
                if hasattr(worker, 'terminate'):
                    worker.terminate()  # 强制终止
            del self.workers[task.id]
            
            task.status = TaskStatus.CANCELLED
            self.db.save_task(task)
            self._emit_task_updated(task)
            return True
        else:
            return False

    def cleanup(self):
        """清理所有工作线程 - 通用实现"""
        for task_id, worker in list(self.workers.items()):
            if worker and hasattr(worker, 'isRunning') and worker.isRunning():
                if hasattr(worker, 'cancel'):
                    worker.cancel()
                if hasattr(worker, 'wait'):
                    worker.wait(1000)  # 等待最多1秒
                if hasattr(worker, 'isRunning') and worker.isRunning():
                    if hasattr(worker, 'terminate'):
                        worker.terminate()  # 强制终止
        self.workers.clear()
        
    def showLog(self):
        """显示日志"""
        # 切换到日志标签，可以指定服务类型
        signalBus.switchToTaskInterfaceSig.emit(self.service_type)

    def _addLog(self, level: str, message: str):
        """添加日志"""
        self.log_cache.append((level, message))
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message)
        
        # 发射通用信号
        self.logGenerated.emit(level, message)
        # 同时发射到全局信号总线
        signalBus.logGenerated.emit(self.service_type, level, message)

    def _emit_task_created(self, task: Task):
        """发射任务创建信号"""
        self.taskCreated.emit(task)
        signalBus.taskCreated.emit(self.service_type, task)

    def _emit_task_updated(self, task: Task):
        """发射任务更新信号"""
        self.taskUpdated.emit(task)
        signalBus.taskUpdated.emit(self.service_type, task)

    def _emit_task_finished(self, task: Task, success: bool, error_msg: str = ""):
        """发射任务完成信号"""
        self.taskFinished.emit(task, success, error_msg)
        signalBus.taskFinished.emit(self.service_type, task, success, error_msg)

    def _onWorkerProgress(self, task: Task, progress: float, speed: str = "", eta: str = ""):
        """处理进度变化 - 子类可以重写"""
        task.progress = progress
        task.speed = speed
        task.eta = eta
        self.db.save_task(task)
        self._emit_task_updated(task)

    def _onWorkerFinished(self, task: Task, success: bool, error_msg: str = ""):
        """处理任务完成 - 子类可以重写"""
        task.endTime = datetime.now()
        
        if success:
            task.status = TaskStatus.SUCCESS
            task.progress = 100.0
            self._addLog("INFO", f"任务完成: {task.name}")
        else:
            task.status = TaskStatus.FAILED
            task.errorMsg = error_msg
            self._addLog("ERROR", f"任务失败: {task.name} - {error_msg}")
        
        self.db.save_task(task)
        self._emit_task_finished(task, success, error_msg)
        
        # 清理worker
        if task.id in self.workers:
            del self.workers[task.id]

