from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton

from ..components.info_card import TranscribeModeInfoCard
from ..components.config_card import TranscribeConfigCard

class TranscribeInterface(ScrollArea):
    """听写界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None

        self.transcribeModeInfoCard = TranscribeModeInfoCard()
        self.transcribeConfigCard = TranscribeConfigCard()
        

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
            self.transcribeModeInfoCard, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(
            self.transcribeConfigCard, 0, Qt.AlignmentFlag.AlignTop)
        
        self.resize(780, 800)
        self.setObjectName("transcribeInterface")
        self.enableTransparentBackground()

        self._connectSignalToSlot()

    # 听写按钮点击事件
    def _onTranscribeButtonClicked(self):
        pass

    # 连接信号与槽
    def _connectSignalToSlot(self):
        self.transcribeConfigCard.transcribeButton.clicked.connect(self._onTranscribeButtonClicked)

    # 拖拽事件
    def dragEnterEvent(self, a0):
        return super().dragEnterEvent(a0)

    def dropEvent(self, a0):
        return super().dropEvent(a0)