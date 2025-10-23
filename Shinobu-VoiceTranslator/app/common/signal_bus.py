# coding: utf-8
from PySide6.QtCore import QObject, Signal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .database.entity.task import Task, TaskType


class SignalBus(QObject):
    """ Signal bus """

    checkUpdateSig = Signal()
    micaEnableChanged = Signal(bool)

    # 界面切换信号
    switchToTaskInterfaceSig = Signal(object)  # TaskType

    # 任务重启信号
    restartTask = Signal(object)  # Task

    # 日志生成信号 (service_type, level, message)
    logGenerated = Signal(object, str, str)  # TaskType, level, message
    
    # 任务信号 (service_type, task)
    taskCreated = Signal(object, object)  # TaskType, Task
    taskUpdated = Signal(object, object)  # TaskType, Task
    taskFinished = Signal(object, object, bool, str)  # TaskType, Task, success, error_msg


signalBus = SignalBus()