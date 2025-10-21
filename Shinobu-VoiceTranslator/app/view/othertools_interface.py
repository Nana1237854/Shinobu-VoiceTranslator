# coding: utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget

from qfluentwidgets import ScrollArea, Pivot

from ..components.info_card import AudioSeparationInfoCard, ClipSectionInfoCard
from ..components.config_card import AudioSeparationConfigCard, ClipSectionConfigCard


class OtherToolsInterface(ScrollArea):
    """其他工具界面 - 包含人声分离和音视频切分"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        
        # Pivot 分页标签
        self.pivot = Pivot(self)
        
        # 堆叠窗口 - 存放不同工具的信息卡片和配置卡片
        self.infoStackedWidget = QStackedWidget(self)
        self.configStackedWidget = QStackedWidget(self)
        
        # 信息卡片
        self.audioSeparationInfoCard = AudioSeparationInfoCard()
        self.clipSectionInfoCard = ClipSectionInfoCard()
        
        # 配置卡片
        self.audioSeparationConfigCard = AudioSeparationConfigCard()
        self.clipSectionConfigCard = ClipSectionConfigCard()
        
        self.vBoxLayout = QVBoxLayout(self.view)
        
        self.__initWidget()
    
    def __initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("otherToolsInterface")
        
        # 添加 Pivot 选项
        self.pivot.addItem(
            routeKey="audioSeparation",
            text=self.tr("人声分离"),
            onClick=lambda: self._switchTool(0)
        )
        self.pivot.addItem(
            routeKey="clipSection",
            text=self.tr("音视频切分"),
            onClick=lambda: self._switchTool(1)
        )
        
        # 添加信息卡片到堆叠窗口
        self.infoStackedWidget.addWidget(self.audioSeparationInfoCard)
        self.infoStackedWidget.addWidget(self.clipSectionInfoCard)
        
        # 添加配置卡片到堆叠窗口
        self.configStackedWidget.addWidget(self.audioSeparationConfigCard)
        self.configStackedWidget.addWidget(self.clipSectionConfigCard)
        
        # 设置布局
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 10, 10)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 添加组件到布局
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.infoStackedWidget, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.configStackedWidget, 0, Qt.AlignmentFlag.AlignTop)
        
        # 默认显示第一个工具
        self.pivot.setCurrentItem("audioSeparation")
        
        self.resize(780, 800)
        self.enableTransparentBackground()
        
        self._connectSignalToSlot()
    
    def _switchTool(self, index: int):
        """切换工具"""
        self.infoStackedWidget.setCurrentIndex(index)
        self.configStackedWidget.setCurrentIndex(index)
    
    def _connectSignalToSlot(self):
        """连接信号与槽"""
        # 连接信息卡片的动作按钮信号
        self.audioSeparationInfoCard.actionClicked.connect(
            self._onAudioSeparationButtonClicked
        )
        self.clipSectionInfoCard.actionClicked.connect(
            self._onClipSectionButtonClicked
        )
        
        # 连接配置卡片的按钮
        self.audioSeparationConfigCard.audioSeparationButton.clicked.connect(
            self._onAudioSeparationButtonClicked
        )
        self.clipSectionConfigCard.clipSectionButton.clicked.connect(
            self._onClipSectionButtonClicked
        )
    
    def _onAudioSeparationButtonClicked(self):
        """人声分离按钮点击事件"""
        # TODO: 实现人声分离逻辑
        pass
    
    def _onClipSectionButtonClicked(self):
        """音视频切分按钮点击事件"""
        # TODO: 实现音视频切分逻辑
        pass