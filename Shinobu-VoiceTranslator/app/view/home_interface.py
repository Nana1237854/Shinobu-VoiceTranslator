from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton
from pathlib import Path
from typing import List

from ..components.info_card import SVTInfoCard
from ..components.config_card import CompleteConfigCard

class HomeInterface(ScrollArea):
    """首页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None 

        self.svtInfoCard = SVTInfoCard()
        self.completeConfigCard = CompleteConfigCard()

        self.vBoxLayout = QVBoxLayout(self.view)

        self.__initWidget()

    def __initWidget(self):
        self.setWidget(self.view)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 10, 10)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(
            self.svtInfoCard, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(
            self.completeConfigCard, 0, Qt.AlignmentFlag.AlignTop)

        self.resize(780, 800)
        self.setObjectName("homeInterface")
        self.enableTransparentBackground()

        self._connectSignalToSlot()

    def _onRunButtonClicked(self):
        pass

    # 连接信号与槽
    def _connectSignalToSlot(self):
        self.completeConfigCard.runButton.clicked.connect(self._onRunButtonClicked)

    # 拖拽事件
    def dragEnterEvent(self, a0):
        return super().dragEnterEvent(a0)

    def dropEvent(self, a0):
        return super().dropEvent(a0)