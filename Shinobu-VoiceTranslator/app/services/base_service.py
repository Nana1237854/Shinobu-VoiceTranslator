from abc import ABC, abstractmethod, ABCMeta
import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ..common.database.entity.task import Task, TaskStatus, TaskType
from ..common.database import getTaskService
from ..common.signal_bus import signalBus
from ..common.concurrent import TaskExecutor, Future, FutureFailed

# 创建组合元类，解决 QObject 和 ABC 的元类冲突
class QABCMeta(type(QObject), ABCMeta):
    """组合 QObject 的元类和 ABCMeta"""
    pass

class BaseService(QObject, ABC, metaclass=QABCMeta):
    """服务基类"""
    
    # 定义信号
    logGenerated = Signal(str, str)  # level, message
    taskCreated = Signal(Task)
    taskUpdated = Signal(Task)
    taskFinished = Signal(Task, bool, str)  # task, success, error_msg
    
    def __init__(self, service_type: TaskType):
        super().__init__()
        self.service_type = service_type
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = getTaskService()
        
        # 使用 TaskExecutor 替代传统的 workers 字典
        self.executor = TaskExecutor(useGlobalThreadPool=False)
        self.futures = {}  # 任务ID -> Future映射
        
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

    def asyncRun(self, task_func: Callable, *args, **kwargs) -> Future:
        """
        通用的异步任务执行方法
        
        Args:
            task_func: 要执行的函数
            *args, **kwargs: 传递给函数的参数
            
        Returns:
            Future: 异步任务的 Future 对象
        """
        return self.executor.asyncRun(task_func, *args, **kwargs)

    def restart(self, task: Task) -> bool:
        """重启任务 - 通用实现"""
        # 先取消现有任务
        if task.id in self.futures:
            del self.futures[task.id]
        
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
        if task.id in self.futures:
            future = self.futures[task.id]
            
            # 注意：TaskExecutor.cancelTask 目前可能不稳定
            # 直接从字典中移除即可
            del self.futures[task.id]
            
            task.status = TaskStatus.CANCELLED
            self.db.save_task(task)
            self._emit_task_updated(task)
            
            self._addLog("INFO", f"任务已取消: {task.name}")
            return True
        else:
            return False

    def cleanup(self):
        """清理所有任务 - 通用实现"""
        self.futures.clear()
        if hasattr(self, 'executor'):
            self.executor.deleteLater()
        
    def showLog(self):
        """显示日志"""
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
        
        # 清理 future
        if task.id in self.futures:
            del self.futures[task.id]

