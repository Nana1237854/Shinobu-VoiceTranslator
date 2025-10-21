# coding:utf-8
from pathlib import Path
from typing import List
from PySide6.QtCore import Qt, Signal, QSize, QUrl
from PySide6.QtGui import QPixmap, QIcon, QColor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (BodyLabel, TransparentToolButton, FluentIcon, ElevatedCardWidget,
                            ImageLabel, SimpleCardWidget, HyperlinkLabel, VerticalSeparator,
                            PrimaryPushButton, TitleLabel, PillPushButton, setFont)


class SVTInfoCard(SimpleCardWidget):
    """ShinobuVoiceTranslator 信息卡片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        self.iconLabel = ImageLabel(QIcon(":/app/images/ico/SVT.ico").pixmap(120, 120), self)

        self.nameLabel = TitleLabel(self.tr("Shinobu-VoiceTranslator"), self)
        self.updateButton = PrimaryPushButton(self.tr("更新"), self)
        # self.companyLabel = HyperlinkLabel(self.tr("Shinobu"), self)

        self.descriptionLabel = BodyLabel(
            self.tr("Shinobu-VoiceTranslator是一款开源的一站式字幕生成翻译软件，从视频下载，音频提取，听写打轴，字幕翻译等各个环节为用户提供便利")
        )

        self.tagDownloadButton = PillPushButton(FluentIcon.DOWNLOAD, self.tr("视频下载"), self)
        self.tagAudioButton = PillPushButton(FluentIcon.MUSIC, self.tr("音频提取"), self)
        self.tagTranscribeButton = PillPushButton(FluentIcon.HEADPHONE, self.tr("识别听写"), self)
        self.tagTranslateButton = PillPushButton(FluentIcon.LANGUAGE, self.tr("字幕翻译"), self)
        self.tagClipSectionButton = PillPushButton(FluentIcon.CUT, self.tr("音视频切分"), self)
        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.__initWidgets()

    def __initWidgets(self):
        # 图标设置
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(120)

        self.updateButton.setFixedWidth(160)

        self.descriptionLabel.setWordWrap(True)
        # self.shareButton.clicked.connect(lambda: openUrl(DEPLOY_URL))

        self.tagDownloadButton.setCheckable(False)
        setFont(self.tagDownloadButton, 12)
        self.tagDownloadButton.setFixedSize(120, 32)

        self.tagAudioButton.setCheckable(False)
        setFont(self.tagAudioButton, 12)
        self.tagAudioButton.setFixedSize(120, 32)

        self.tagTranscribeButton.setCheckable(False)
        setFont(self.tagTranscribeButton, 12)
        self.tagTranscribeButton.setFixedSize(120, 32)

        self.tagTranslateButton.setCheckable(False)
        setFont(self.tagTranslateButton, 12)
        self.tagTranslateButton.setFixedSize(120, 32)

        self.tagClipSectionButton.setCheckable(False)
        setFont(self.tagClipSectionButton, 12)
        self.tagClipSectionButton.setFixedSize(120, 32)

        self.shareButton.setFixedSize(32, 32)
        self.shareButton.setIconSize(QSize(14, 14))

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.initLayout()

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # name label and install button
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.updateButton, 0, Qt.AlignRight)

        # company label
        # self.vBoxLayout.addSpacing(3)
        # self.vBoxLayout.addWidget(self.companyLabel)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # button
        self.vBoxLayout.addSpacing(12)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.tagDownloadButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.tagAudioButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.tagTranscribeButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.tagTranslateButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.tagClipSectionButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.shareButton, 0, Qt.AlignRight)

class DownloadModeInfoCard(SimpleCardWidget):
    """下载模式信息卡片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)

        self.iconLabel = ImageLabel(QIcon(":/app/images/ico/download_mode.ico").pixmap(80, 80), self)

        self.nameLabel = TitleLabel(self.tr("下载模式"), self)

        self.descriptionLabel = BodyLabel(
            self.tr("下载模式工作流：\n输入 bilibili/youtube 下载链接 -> 选择保存目录 -> 点击下载按钮")
        )

        self.tagBilibiliButton = PillPushButton(self.tr("bilibili"), self)
        self.tagYoutubeButton = PillPushButton(self.tr("youtube"), self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.tagsLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.__initWidgets()
    
    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(80)

        self.descriptionLabel.setWordWrap(True)     # 自动换行

        self.tagBilibiliButton.setCheckable(False)
        setFont(self.tagBilibiliButton, 12)
        self.tagBilibiliButton.setFixedSize(80, 32)

        self.tagYoutubeButton.setCheckable(False)
        setFont(self.tagYoutubeButton, 12)
        self.tagYoutubeButton.setFixedSize(80, 32)

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.initLayout()

    def initLayout(self):
        # 主水平布局：图标在左，内容在右
        self.hBoxLayout.setSpacing(20)
        self.hBoxLayout.setContentsMargins(24, 20, 24, 20)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        # 右侧垂直布局
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 顶部布局：标题
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addStretch(1)  # 添加弹性空间

        # 描述文本
        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # 标签按钮布局
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addLayout(self.tagsLayout)
        self.tagsLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsLayout.setSpacing(8)
        
        # 添加所有标签按钮
        self.tagsLayout.addWidget(self.tagBilibiliButton)
        self.tagsLayout.addWidget(self.tagYoutubeButton)
        self.tagsLayout.addStretch(1)  # 添加弹性空间使标签左对齐

class TranslateModeInfoCard(SimpleCardWidget):
    """翻译模式信息卡片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)

        self.iconLabel = ImageLabel(QIcon(":/app/images/ico/translate_mode.ico").pixmap(80, 80), self)

        self.nameLabel = TitleLabel(self.tr("翻译模式"), self)

        self.descriptionLabel = BodyLabel(
            self.tr("翻译模式工作流：\n选择翻译文件 -> 选择翻译模型 -> 选择输出语言 -> 选择保存目录 -> 点击翻译按钮进行翻译")
        )

        self.tagSakuraButton = PillPushButton(self.tr("Sakura"), self)
        self.tagGaltranslButton = PillPushButton(self.tr("Galtransl"), self)
        self.tagOllamaButton = PillPushButton(self.tr("Ollama"), self)
        self.tagLlamacppButton = PillPushButton(self.tr("Llamacpp"), self)
        self.tagOnlineButton = PillPushButton(self.tr("在线模型"), self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.tagsLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.__initWidgets()
    
    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(80)

        self.descriptionLabel.setWordWrap(True)     # 自动换行

        self.tagSakuraButton.setCheckable(False)
        setFont(self.tagSakuraButton, 12)
        self.tagSakuraButton.setFixedSize(80, 32)

        self.tagGaltranslButton.setCheckable(False)
        setFont(self.tagGaltranslButton, 12)
        self.tagGaltranslButton.setFixedSize(80, 32)

        self.tagOllamaButton.setCheckable(False)
        setFont(self.tagOllamaButton, 12)
        self.tagOllamaButton.setFixedSize(80, 32)

        self.tagLlamacppButton.setCheckable(False)
        setFont(self.tagLlamacppButton, 12)
        self.tagLlamacppButton.setFixedSize(80, 32)

        self.tagOnlineButton.setCheckable(False)
        setFont(self.tagOnlineButton, 12)
        self.tagOnlineButton.setFixedSize(80, 32)

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.initLayout()

    def initLayout(self):
        # 主水平布局：图标在左，内容在右
        self.hBoxLayout.setSpacing(20)
        self.hBoxLayout.setContentsMargins(24, 20, 24, 20)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        # 右侧垂直布局
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 顶部布局：标题
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addStretch(1)  # 添加弹性空间

        # 描述文本
        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # 标签按钮布局
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addLayout(self.tagsLayout)
        self.tagsLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsLayout.setSpacing(8)
        
        # 添加所有标签按钮
        self.tagsLayout.addWidget(self.tagSakuraButton)
        self.tagsLayout.addWidget(self.tagGaltranslButton)
        self.tagsLayout.addWidget(self.tagOllamaButton)
        self.tagsLayout.addWidget(self.tagLlamacppButton)
        self.tagsLayout.addWidget(self.tagOnlineButton)
        self.tagsLayout.addStretch(1)  # 添加弹性空间使标签左对齐


class TranscribeModeInfoCard(SimpleCardWidget):
    """听写模式信息卡片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)

        self.iconLabel = ImageLabel(QIcon(":/app/images/ico/transcribe_mode.ico").pixmap(80, 80), self)

        self.nameLabel = TitleLabel(self.tr("听写模式"), self)

        self.descriptionLabel = BodyLabel(
            self.tr("下载模式工作流：\n选择听写文件 -> 选择听写模型 -> 选择输入语言 -> 选择输出文件 -> 选择保存目录 -> 点击听写按钮进行听写")
        )

        self.tagWhisperButton = PillPushButton(self.tr("whisper"), self)
        self.tagWhisperfasterButton = PillPushButton(self.tr("whisper-faster"), self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.tagsLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.__initWidgets()
    
    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(80)

        self.descriptionLabel.setWordWrap(True)     # 自动换行

        self.tagWhisperButton.setCheckable(False)
        setFont(self.tagWhisperButton, 12)
        self.tagWhisperButton.setFixedSize(80, 32)

        self.tagWhisperfasterButton.setCheckable(False)
        setFont(self.tagWhisperfasterButton, 12)
        self.tagWhisperfasterButton.setFixedSize(120, 32)

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.initLayout()

    def initLayout(self):
        # 主水平布局：图标在左，内容在右
        self.hBoxLayout.setSpacing(20)
        self.hBoxLayout.setContentsMargins(24, 20, 24, 20)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        # 右侧垂直布局
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 顶部布局：标题
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addStretch(1)  # 添加弹性空间

        # 描述文本
        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # 标签按钮布局
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addLayout(self.tagsLayout)
        self.tagsLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsLayout.setSpacing(8)
        
        # 添加所有标签按钮
        self.tagsLayout.addWidget(self.tagWhisperButton)
        self.tagsLayout.addWidget(self.tagWhisperfasterButton)
        self.tagsLayout.addStretch(1)  # 添加弹性空间使标签左对齐

class OtherToolsInfoCard(SimpleCardWidget):
    """其他工具信息卡片基类 - 可扩展用于不同工具"""
    
    actionClicked = Signal()  # 动作按钮点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        
        # 通用组件
        self.iconLabel = ImageLabel(self)
        self.titleLabel = TitleLabel(self)
        self.descriptionLabel = BodyLabel(self)
        self.actionButton = PrimaryPushButton(self.tr("开始使用"), self)
        
        # 标签按钮列表（子类可以添加）
        self.tagButtons = []
        
        # 布局
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.tagsLayout = QHBoxLayout()
        
        self.__initWidgets()
    
    def __initWidgets(self):
        """初始化组件 - 子类可以重写以自定义"""
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(80)
        
        self.descriptionLabel.setWordWrap(True)
        self.actionButton.setFixedHeight(32)
        
        # 调用子类方法设置内容
        self._setupContent()
        
        self.titleLabel.setObjectName("titleLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        
        self.initLayout()
    
    def _setupContent(self):
        """设置内容 - 必须由子类实现"""
        # 子类应该重写此方法来设置：
        # - self.setIcon()
        # - self.setTitle()
        # - self.setDescription()
        # - self.addTagButton() (可选)
        raise NotImplementedError("子类必须实现 _setupContent 方法")
    
    def setIcon(self, icon: QIcon, size: int = 80):
        """设置图标"""
        self.iconLabel.setImage(icon.pixmap(size, size))
    
    def setTitle(self, title: str):
        """设置标题"""
        self.titleLabel.setText(title)
    
    def setDescription(self, description: str):
        """设置描述"""
        self.descriptionLabel.setText(description)
    
    def setActionButtonText(self, text: str):
        """设置动作按钮文本"""
        self.actionButton.setText(text)
    
    def addTagButton(self, text: str, icon=None, width: int = 80) -> PillPushButton:
        """添加标签按钮"""
        if icon:
            tagButton = PillPushButton(icon, text, self)
        else:
            tagButton = PillPushButton(text, self)
        
        tagButton.setCheckable(False)
        setFont(tagButton, 12)
        tagButton.setFixedSize(width, 32)
        
        self.tagButtons.append(tagButton)
        return tagButton
    
    def initLayout(self):
        """初始化布局"""
        # 主水平布局：图标在左，内容在右
        self.hBoxLayout.setSpacing(20)
        self.hBoxLayout.setContentsMargins(24, 20, 24, 20)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        
        # 右侧垂直布局
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        
        # 顶部布局：标题和动作按钮
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.titleLabel)
        self.topLayout.addStretch(1)
        self.topLayout.addWidget(self.actionButton)
        
        # 描述文本
        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.descriptionLabel)
        
        # 标签按钮布局
        if self.tagButtons:
            self.vBoxLayout.addSpacing(16)
            self.vBoxLayout.addLayout(self.tagsLayout)
            self.tagsLayout.setContentsMargins(0, 0, 0, 0)
            self.tagsLayout.setSpacing(8)
            
            for tagButton in self.tagButtons:
                self.tagsLayout.addWidget(tagButton)
            self.tagsLayout.addStretch(1)
        
        # 连接动作按钮信号
        self.actionButton.clicked.connect(self.actionClicked)

class AudioSeparationInfoCard(OtherToolsInfoCard):
    """人声分离工具信息卡片"""
    
    def _setupContent(self):
        """设置人声分离工具的内容"""
        # 设置图标（使用 FluentIcon 或自定义图标）
        self.setIcon(FluentIcon.MUSIC.icon())
        
        # 设置标题
        self.setTitle(self.tr("人声分离"))
        
        # 设置描述
        self.setDescription(
            self.tr("将音频中的人声和伴奏分离，适用于音乐制作、音频处理和字幕制作等场景")
        )
        
        # 设置动作按钮文本
        self.setActionButtonText(self.tr("开始分离"))
        
        # 添加标签按钮（可选）
        self.uvr5Tag = self.addTagButton(self.tr("UVR5"), width=60)
        self.demucsTag = self.addTagButton(self.tr("Demucs"), width=70)

class ClipSectionInfoCard(OtherToolsInfoCard):
    """音视频切分工具信息卡片"""
    
    def _setupContent(self):
        """设置音视频切分工具的内容"""
        # 设置图标
        self.setIcon(FluentIcon.CUT.icon())
        
        # 设置标题
        self.setTitle(self.tr("音视频切分"))
        
        # 设置描述
        self.setDescription(
            self.tr("按照指定时间范围切分音视频文件，快速提取所需片段，支持多种格式")
        )
        
        # 设置动作按钮文本
        self.setActionButtonText(self.tr("开始切分"))
        
        # 添加标签按钮（可选）
        self.videoTag = self.addTagButton(self.tr("视频"), FluentIcon.VIDEO, width=100)
        self.audioTag = self.addTagButton(self.tr("音频"), FluentIcon.MUSIC, width=100)

