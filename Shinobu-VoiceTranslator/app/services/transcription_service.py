# coding:utf-8
"""听写服务 - 占位实现"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal

from ..common.database.entity.task import Task, TaskStatus, TaskType
from ..common.database import getTaskService
from .base_service import BaseService
from ..common.signal_bus import signalBus


class TranscriptionService(BaseService):
    """听写服务基类 - 占位"""
    
    taskCreated = Signal(Task)   # 任务创建信号
    taskUpdated = Signal(Task)   # 任务更新信号
    taskFinished = Signal(Task, bool, str)   # 任务完成信号
    logGenerated = Signal(str, str)   # 日志生成信号
    
    def __init__(self):
        super().__init__(TaskType.TRANSCRIBE)  # 修改：传递 TaskType.TRANSCRIBE
    
    def isAvailable(self) -> bool:
        """检查服务是否可用"""
        return self._available
    
    def createTask(self, input_path: str, **kwargs) -> Optional[Task]:
        """创建听写任务 - 待实现"""
        self._addLog("WARNING", "听写服务尚未实现")
        return None
    
    def start(self, task: Task) -> bool:
        """开始任务 - 待实现"""
        self._addLog("WARNING", "听写服务尚未实现")
        return False
    


# 全局服务实例
transcriptionService = TranscriptionService()