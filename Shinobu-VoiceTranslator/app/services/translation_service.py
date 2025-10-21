# coding:utf-8
"""翻译服务 - 占位实现"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal

from ..common.database.entity.task import Task, TaskStatus
from ..common.database import getTaskService
from ..common.signal_bus import signalBus


class TranslationService(QObject):
    """翻译服务基类 - 占位"""
    
    taskCreated = Signal(Task)   # 任务创建信号
    taskUpdated = Signal(Task)   # 任务更新信号
    taskFinished = Signal(Task, bool, str)   # 任务完成信号
    logGenerated = Signal(str, str)   # 日志生成信号
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = getTaskService()
        self._available = False  # 服务暂不可用
        self.log_cache = []
    
    def isAvailable(self) -> bool:
        """检查服务是否可用"""
        return self._available
    
    def createTask(self, input_path: str, **kwargs) -> Optional[Task]:
        """创建翻译任务 - 待实现"""
        self._addLog("WARNING", "翻译服务尚未实现")
        return None
    
    def start(self, task: Task) -> bool:
        """开始任务 - 待实现"""
        self._addLog("WARNING", "翻译服务尚未实现")
        return False
    
    def restart(self, task: Task) -> bool:
        """重启任务 - 待实现"""
        return self.start(task)
    
    def cancel(self, task: Task) -> bool:
        """取消任务 - 待实现"""
        return False
    
    def showLog(self):
        """显示日志"""
        signalBus.switchToTaskInterfaceSig.emit()
    
    def _addLog(self, level: str, message: str):
        """添加日志"""
        self.log_cache.append((level, message))
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message)
        signalBus.logGenerated.emit(level, message)


# 全局服务实例
translationService = TranslationService()