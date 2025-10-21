# coding: utf-8
from PySide6.QtCore import QObject, Signal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .database.entity.task import Task


class SignalBus(QObject):
    """ Signal bus """

    checkUpdateSig = Signal()
    micaEnableChanged = Signal(bool)

    # 界面切换信号
    switchToTaskInterfaceSig = Signal()

    # 任务重启信号
    restartTask = Signal(object)

    # 日志生成信号
    logGenerated = Signal(str, str)


signalBus = SignalBus()