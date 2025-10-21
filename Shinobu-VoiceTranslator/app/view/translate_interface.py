from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton

from ..components.info_card import TranslateModeInfoCard
from ..components.config_card import TranslateConfigCard

class TranslateInterface(ScrollArea):
    """翻译界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None

        self.translateModeInfoCard = TranslateModeInfoCard()
        self.translateConfigCard = TranslateConfigCard()

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
            self.translateModeInfoCard, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(
            self.translateConfigCard, 0, Qt.AlignmentFlag.AlignTop)
        
        self.resize(780, 800)
        self.setObjectName("translateInterface")
        self.enableTransparentBackground()

        self._connectSignalToSlot()

    # 翻译按钮点击事件
    def _onTranslateButtonClicked(self):
        pass

    # 连接信号与槽
    def _connectSignalToSlot(self):
        self.translateConfigCard.translateButton.clicked.connect(self._onTranslateButtonClicked)

    # 拖拽事件
    def dragEnterEvent(self, a0):
        return super().dragEnterEvent(a0)

    def dropEvent(self, a0):
        return super().dropEvent(a0)