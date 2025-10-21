# coding:utf-8
from pathlib import Path
import sys
from PySide6.QtCore import Qt, Signal, Property, QFileInfo, QSize
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileIconProvider

from qfluentwidgets import (CardWidget, IconWidget, ToolButton, FluentIcon,
                            BodyLabel, CaptionLabel, ProgressBar, ImageLabel, setFont,
                            MessageBoxBase, SubtitleLabel, CheckBox, InfoBar, InfoBarPosition,
                            PushButton, ToolTipFilter, InfoLevel, DotInfoBadge, MessageBox,
                            isDarkTheme, themeColor, RoundMenu, Action, MenuAnimationType)

from ..common.signal_bus import signalBus
from ..services.downloadservice.download_service import UnifiedDownloadService
from ..common.database.entity.task import Task, TaskStatus
from ..common.database import sqlRequest
from ..common.utils import removeFile, showInFolder, openUrl

class TaskCardBase(CardWidget):
    """任务卡片基类"""

    deleted = Signal()
    checkedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkBox = CheckBox()
        self.checkBox.setFixedSize(23, 23)
        self.setSelectionMode(False)

        self.checkBox.stateChanged.connect(self._onCheckedChanged)

    def setSelectionMode(self, enter: bool):
        # 选择模式切换
        self.isSelectionMode = enter
        self.checkBox.setVisible(enter)
        if not enter:
            self.checkBox.setChecked(False)

    # 选中状态管理
    def isChecked(self):
        return self.checkBox.isChecked()
    
    def setChecked(self, checked: bool = True):
        self.checkBox.setChecked(checked)
    
    # 删除逻辑
    def removeTask(self):
        raise NotImplementedError
    
    # 鼠标交互逻辑
    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if self.isSelectionMode:
            self.setChecked()

    # 删除确认对话框
    def _onDeleteButtonClicked(self):
        w = DeleteTaskDialog(self.window(), deleteOnClose=False)
        w.deleteFileCheckBox.setChecked(False)

        if w.exec():
            self.removeTask(w.deleteFileCheckBox.isChecked())

        w.deleteLater()

    # 复选框状态同步
    def _onCheckChanged(self):
        self.setChecked(self.checkBox.isChecked())
        self.checkedChanged.emit(self.checkBox.isChecked())
        self.update()

    # 自定义绘制
    def paintEvent(self, e):
        if not (self.isSelectionMode and self.isChecked()):
            return super().paintEvent(e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        r = self.borderRadius
        painter.setPen(QPen(themeColor(), 2))
        painter.setBrush(QColor(255, 255, 255, 15) if isDarkTheme() else QColor(0, 0, 0, 8))
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), r, r)

class ProgressingTaskCard(TaskCardBase):
    """任务进行中卡片"""

    def __init__(self, task: Task, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()

        # 核心显示控件
        self.task = task                                        # 绑定的任务对象
        self.imageLabel = ImageLabel()                          # 文件类型图标
        self.flieNameLabel = BodyLabel(task.flieName)           # 文件名
        self.progressBar = ProgressBar()                        # 任务进度条
        
        # 核心信息控件
        


        # 操作按钮
        self.openFolderButton = ToolButton(FluentIcon.FOLDER)     # 打开文件夹按钮
        self.deleteButton = ToolButton(FluentIcon.DELETE)       # 删除任务按钮

        self._initWidget()

    def _initWidget(self):
        # 设置文件图标

        # 统一图标大小
        
        # 设置工具提示
        self.openFolderButton.setToolTip(self.tr("打开保存目录"))
        self.openFolderButton.setToolTipDuration(3000)    # 悬停3秒显示提示
        self.openFolderButton.installEventFilter(ToolTipFilter(self.openFolderButton))

        self.deleteButton.setToolTip(self.tr("删除文件"))
        self.deleteButton.setToolTipDuration(3000)
        self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))

        # 设置文件名样式
        setFont(self.flieNameLabel, 18, QFont.Weight.Bold)
        self.flieNameLabel.setWordWrap(True)

        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        # 水平布局 从走往右
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)                # 复选框
        self.hBoxLayout.addSpacing(5)                           # 间距
        self.hBoxLayout.addWidget(self.imageLabel)              # 文件图标
        self.hBoxLayout.addSpacing(5)                           
        self.hBoxLayout.addLayout(self.vBoxLayout)              # 主内容区域
        self.hBoxLayout.addSpacing(20)
        self.hBoxLayout.addWidget(self.openFolderButton)        # 打开文件夹按钮
        self.hBoxLayout.addWidget(self.deleteButton)            # 删除文件按钮

        # 垂直布局 从上到下
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)           # 文件名
        self.vBoxLayout.addLayout(self.infoLayout)              # 信息行
        self.vBoxLayout.addWidget(self.progressBar)             # 进度条

        # 信息行布局：状态信息水平排列
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(3)
        
    def _connectSignalToSlot(self):
        self.openFolderButton.clicked.connect(self._onOpenButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)

    def _onOpenButtonClicked(self):
        path = Path(self.task.saveFolder) / self.task.fileName
        showInFolder(path)

    def removeTask(self, deleteFile=False):
        if not self.task.isRunning():
            return


class SuccessTaskCard(TaskCardBase):
    """已完成卡片"""
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()

        self.task = task

        # 核心显示控件
        self.imageLabel = ImageLabel()
        self.fileNameLabel = BodyLabel(task.fileName)

        # 状态信息控件
        self.createTimeIcon = IconWidget(FluentIcon.DATE_TIME)  # 创建时间图标
        self.createTimeLabel = CaptionLabel(
            task.createTime.toString("yyyy-MM-dd hh:mm:ss"))    # 创建时间
        

        # 操作按钮（多一个重新开始）
        self.restartButton = ToolButton(FluentIcon.UPDATE)
        self.openFolderButton = ToolButton(FluentIcon.FOLDER)
        self.deleteButton = ToolButton(FluentIcon.DELETE)

        self._initWidget()

    def _initWidget(self):
        # 设置封面图像尺寸和圆角
        self.imageLabel.setScaledSize(QSize(112, 63))  # 16:9 比例
        self.imageLabel.setBorderRadius(4, 4, 4, 4)    # 4像素圆角
        self.createTimeIcon.setFixedSize(16, 16)
        

        # 检查并更新封面
        if self.task.coverPath.exists():
            self.updateCover()

    def updateCover(self):
        self.imageLabel.setImage(str(self.task.coverPath))
        self.imageLabel.setScaledSize(QSize(112, 63))

        self.restartButton.setToolTip(self.tr("重新开始"))
        self.restartButton.setToolTipDuration(3000)
        self.restartButton.installEventFilter(ToolTipFilter(self.restartButton))

        self.openFolderButton.setToolTip(self.tr("打开目录"))
        self.openFolderButton.setToolTipDuration(3000)
        self.openFolderButton.installEventFilter(ToolTipFilter(self.openFolderButton))

        self.deleteButton.setToolTip(self.tr("删除文件"))
        self.deleteButton.setToolTipDuration(3000)
        self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))

        setFont(self.fileNameLabel, 18, QFont.Weight.Bold)
        self.fileNameLabel.setWordWrap(True)

        if self.task.coverPath.exists():
            self.updateCover()

        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        # 主布局
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.imageLabel)      # 封面图片
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)

        # 按键顺序
        self.hBoxLayout.addWidget(self.restartButton)
        self.hBoxLayout.addWidget(self.openFolderButton)
        self.hBoxLayout.addWidget(self.deleteButton)

        # 垂直布局
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)

        # 信息行布局
        self.infoLayout.setContentsMargins(0, 0, 0, 0)

        # 创建时间相关信息
        self.infoLayout.setSpacing(3)
        self.infoLayout.addWidget(self.createTimeIcon)
        self.infoLayout.addWidget(self.createTimeLabel, 0, Qt.AlignmentFlag.AlignLeft)

    def updateCover(self):
        self.imageLabel.setImage(str(self.task.coverPath))
        self.imageLabel.setScaledSize(QSize(112, 63))

    # 文件操作功能
    def _onOpenButtonClicked(self):
        exist = UnifiedDownloadService.showInFolder(self.task)
        if not exist:
            InfoBar.error(
                title=self.tr("打开失败"),
                content=self.tr("视频文件已删除"),
                duration=2000,
                parent=self.window().taskInterface
            )

    def removeTask(self, deleteFile=False):
        UnifiedDownloadService.removedSuccessTask(self.task, deleteFile)
        self.deleted.emit(self.task)

    def restart(self):
        signalBus.redownloadTask.emit(self.task)

    def _connectSignalToSlot(self):
        self.openFolderButton.clicked.connect(self._onOpenButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)
        self.restartButton.clicked.connect(self.restart)

class FailedTaskCard(TaskCardBase):

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()

        self.task = task
        self.imageLabel = ImageLabel()
        self.fileNameLabel = BodyLabel(task.fileName)

        self.createTimeIcon = IconWidget(FluentIcon.DATE_TIME)
        self.createTimeLabel = CaptionLabel(
            task.createTime.toString("yyyy-MM-dd hh:mm:ss"))
        

        self.restartButton = ToolButton(FluentIcon.UPDATE)
        self.logButton = ToolButton(FluentIcon.COMMAND_PROMPT)
        self.deleteButton = ToolButton(FluentIcon.DELETE)

        self._initWidget()

    def _initWidget(self):
        self.imageLabel.setImage(QFileIconProvider().icon(
            QFileInfo(self.task.videoPath)).pixmap(32, 32))
        self.createTimeIcon.setFixedSize(16, 16)
        self.sizeIcon.setFixedSize(16, 16)

        self.restartButton.setToolTip(self.tr("重新开始"))
        self.restartButton.setToolTipDuration(3000)
        self.restartButton.installEventFilter(
            ToolTipFilter(self.restartButton))

        self.logButton.setToolTip(self.tr("查看错误日志"))
        self.logButton.setToolTipDuration(3000)
        self.logButton.installEventFilter(ToolTipFilter(self.logButton))

        setFont(self.fileNameLabel, 18, QFont.Weight.Bold)
        self.fileNameLabel.setWordWrap(True)

        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)
        self.hBoxLayout.addSpacing(5)

        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addSpacing(5)

        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)

        self.hBoxLayout.addWidget(self.restartButton)
        self.hBoxLayout.addWidget(self.logButton)
        self.hBoxLayout.addWidget(self.deleteButton)

        # 垂直布局
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)
        
        # 信息行布局
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(3)
        self.infoLayout.addWidget(self.createTimeIcon)
        self.infoLayout.addWidget(self.createTimeLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.infoLayout.addSpacing(8)
        self.infoLayout.addWidget(self.sizeIcon)
        self.infoLayout.addWidget(self.sizeLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.infoLayout.addStretch(1)

    def _onLogButtonClicked(self):
        openUrl(self.task.logFile)

    def removeTask(self, deleteFile=False):
        UnifiedDownloadService.removeFailedTask(self.task, deleteFile)
        self.deleted.emit(self.task)

    def restart(self):
        signalBus.restartTask.emit(self.task)

    def _connectSignalToSlot(self):
        self.logButton.clicked.connect(self._onLogButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)
        self.restartButton.clicked.connect(self.restart)



class DeleteTaskDialog():
    pass