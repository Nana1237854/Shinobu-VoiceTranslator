from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton

from ..components.config_card import DownloadConfigCard

from ..common.signal_bus import signalBus

from ..components.info_card import DownloadModeInfoCard
from ..services.downloadservice.download_service import UnifiedDownloadService


class DownloadInterface(ScrollArea):
    """下载界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None

        self.downloadModeInfoCard = DownloadModeInfoCard(self)
        self.downloadConfigCard = DownloadConfigCard(self)

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
            self.downloadModeInfoCard, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(
            self.downloadConfigCard, 0, Qt.AlignmentFlag.AlignTop)
        
        self.resize(780, 800)
        self.setObjectName("downloadInterface")
        self.enableTransparentBackground()

        self._connectSignalToSlot()

    # 下载按钮点击事件
    def _onDownloadButtonClicked(self):
        url = self.downloadConfigCard.urlLineEdit.text().strip()
        if not url:
            InfoBar.warning(
                self.tr("输入错误"),
                self.tr("请输入下载链接"),
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            return

        task = UnifiedDownloadService.createTask(url)
        if task:
            InfoBar.success(
                self.tr("任务创建成功"),
                self.tr("已创建下载任务，请到任务管理查看"),
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            # 清空输入框
            self.downloadConfigCard.urlLineEdit.clear()
        else:
            InfoBar.error(
                self.tr("任务创建失败"),
                self.tr("不支持的链接格式"),
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )

    # 连接信号与槽
    def _connectSignalToSlot(self):
        self.downloadConfigCard.downloadButton.clicked.connect(self._onDownloadButtonClicked)

    # 拖拽事件
    def dragEnterEvent(self, a0):
        return super().dragEnterEvent(a0)

    def dropEvent(self, a0):
        return super().dropEvent(a0)
