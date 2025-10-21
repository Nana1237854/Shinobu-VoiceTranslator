from PySide6.QtCore import Qt, Signal, QTime

from PySide6.QtWidgets import QWidget, QHBoxLayout, QFileDialog

from qfluentwidgets import (IconWidget, BodyLabel, FluentIcon, InfoBarIcon, ComboBox,
                            PrimaryPushButton, LineEdit, GroupHeaderCardWidget, PushButton,
                            CompactSpinBox, SwitchButton, IndicatorPosition, PlainTextEdit,
                            ToolTipFilter, ConfigItem)

from ..common.config import cfg

class DownloadConfigCard(GroupHeaderCardWidget):
    """下载配置卡片"""
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setTitle(self.tr("下载设置"))
        self.setBorderRadius(8)

        self.urlLineEdit = LineEdit()
        self.targetFileButton = PushButton()
        self.saveFolderButton = PushButton(self.tr("选择"), self, FluentIcon.FOLDER)

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(
            self.tr("点击下载按钮开始下载") + ' 👉')
        self.downloadButton = PrimaryPushButton(
            self.tr("下载"), self, FluentIcon.PLAY_SOLID)

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.urlLineEdit.setPlaceholderText(self.tr("请输入下载链接"))
        self.urlLineEdit.setClearButtonEnabled(True)
        self.urlLineEdit.setFixedWidth(600)

        self.targetFileButton.setText(self.tr("选择文件"))
        self.targetFileButton.setFixedWidth(120)
        

        self._initLayout()

    def _initLayout(self):
        # 添加小组件在卡片中
        self.addGroup(
            icon=FluentIcon.LINK,  # 链接图标
            title=self.tr("下载链接"),
            content=self.tr("请输入需要下载的链接"),
            widget=self.urlLineEdit
        )
        self.addGroup(
            icon=FluentIcon.DOCUMENT,  # 文档图标
            title=self.tr("目标文件"),
            content=self.tr("选择下载后的文件"),
            widget=self.targetFileButton
        )
        self.addGroup(
            icon=FluentIcon.FOLDER,  # 文件夹图标
            title=self.tr("保存目录"),
            content=self.tr("点击选择保存目录"),
            widget=self.saveFolderButton
        )
        

        # 设置底部工具栏布局
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(
            self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(
            self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(
            self.downloadButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)


class TranslateConfigCard(GroupHeaderCardWidget):
    """翻译配置卡片"""

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setTitle(self.tr("翻译设置"))

        self.targetFileButton = PushButton(self.tr("选择"))
        self.translateModelComboBox = ComboBox()
        self.targetLanguageComboBox = ComboBox()
        self.saveFolderButton = PushButton(self.tr("选择"))

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(
            self.tr("点击翻译按钮开始翻译") + ' 👉'
        )
        self.translateButton = PrimaryPushButton(
            self.tr("翻译"), self, FluentIcon.PLAY_SOLID
        )

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.targetFileButton.setFixedWidth(120)
        self.translateModelComboBox.setFixedWidth(320)
        self.targetLanguageComboBox.setFixedWidth(320)
        self.translateModelComboBox.addItems(["galtransl", "sakura", "llamacpp"])
        self.targetLanguageComboBox.addItems(["中文", "日语", "英语", "韩语", "俄语", "法语"])


        self._initLayout()

    
    def _initLayout(self):
        # 添加小组件在卡片中
        self.addGroup(
            icon=FluentIcon.DOCUMENT,
            title=self.tr("目标文件"),
            content=self.tr("选择待翻译的文件"),
            widget=self.targetFileButton
        )
        self.addGroup(
            icon=FluentIcon.IOT,
            title=self.tr("翻译模型"),
            content=self.tr("选择用于翻译的模型类别"),
            widget=self.translateModelComboBox
        )
        self.addGroup(
            icon=FluentIcon.LANGUAGE,
            title=self.tr("输出语言"),
            content=self.tr("选择输出的语言"),
            widget=self.targetLanguageComboBox
        )
        self.addGroup(
            icon=FluentIcon.FOLDER,
            title=self.tr("保存目录"),
            content=self.tr("点击选择保存目录"),
            widget=self.saveFolderButton
        )
        

        # 设置底部工具栏布局
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(
            self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(
            self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(
            self.translateButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)

class TranscribeConfigCard(GroupHeaderCardWidget):
    """听写配置卡片"""
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setTitle(self.tr("听写设置"))
        self.mediaParser = None

        self.targetFileButton = PushButton(self.tr("选择"))
        self.transcribeModelComboBox = ComboBox()
        self.inputLanguageComboBox = ComboBox()
        self.outputFileTypeComBox = ComboBox()
        self.saveFolderButton = PushButton(self.tr("选择"))
        self.openWhisperFileButton = PushButton(self.tr("打开whisper目录"))
        self.openWhisperFasterFileButton = PushButton(self.tr("打开whisper目录"))
        
        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(
            self.tr("点击听写按钮开始听写") + ' 👉')
        self.transcribeButton = PrimaryPushButton(
            self.tr("听写"), self, FluentIcon.PLAY_SOLID)
        
        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.targetFileButton.setFixedWidth(120)
        self.transcribeModelComboBox.setFixedWidth(320)
        self.inputLanguageComboBox.setFixedWidth(320)
        self.transcribeModelComboBox.addItems(["whisper", "whisper-faster(仅限N卡)"])
        self.inputLanguageComboBox.addItems(["中文", "日语", "英语", "韩语", "俄语", "法语"])
        self.outputFileTypeComBox.addItems(
            ["原文SRT", "双语SRT", "原文LRC", "原文TXT", 
             "双语TXT", "原文XLSX", "双语XLSX"]
            )

        self._initLayout()

    
    def _initLayout(self):
        # 添加小组件在卡片中
        self.addGroup(
            icon=FluentIcon.DOCUMENT,
            title=self.tr("目标文件"),
            content=self.tr("选择待听写的文件"),
            widget=self.targetFileButton
        )
        self.addGroup(
            icon=FluentIcon.IOT,
            title=self.tr("听写模型"),
            content=self.tr("选择用于听写的模型类别"),
            widget=self.transcribeModelComboBox
        )
        self.addGroup(
            icon=FluentIcon.LANGUAGE,
            title=self.tr("输入语言"),
            content=self.tr("选择输入的语言"),
            widget=self.inputLanguageComboBox
        )
        self.addGroup(
            icon=FluentIcon.SAVE,
            title=self.tr("输出文件"),
            content=self.tr("选择输出的文件"),
            widget=self.outputFileTypeComBox
        )
        self.addGroup(
            icon=FluentIcon.FOLDER,
            title=self.tr("保存目录"),
            content=self.tr("点击选择保存目录"),
            widget=self.saveFolderButton
        )
        

        # 设置底部工具栏布局
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(
            self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(
            self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(
            self.transcribeButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)

class AudioSeparationConfigCard(GroupHeaderCardWidget):
    """人声分离配置卡片"""
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setTitle(self.tr("人声分离"))
        self.mediaParser = None

        self.targetFileButton = PushButton(self.tr("选择"))
        self.audioSeparationModelComboBox = ComboBox()

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(
            self.tr("点击分离按钮开始分离") + ' 👉')
        self.audioSeparationButton = PrimaryPushButton(
            self.tr("分离"), self, FluentIcon.PLAY_SOLID)

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.targetFileButton.setFixedWidth(120)
        self.audioSeparationModelComboBox.setFixedWidth(320)
        self.audioSeparationModelComboBox.addItem(self.tr("默认"))

        self._initLayout()

    def _initLayout(self):
        # 添加小组件在卡片中
        self.addGroup(
            icon=FluentIcon.MUSIC,
            title=self.tr("目标文件"),
            content=self.tr("选择待分离的文件"),
            widget=self.targetFileButton
        )
        self.addGroup(
            icon=FluentIcon.IOT,
            title=self.tr("分离模型"),
            content=self.tr("选择用于分离的模型类别"),
            widget=self.audioSeparationModelComboBox
        )

        # 设置底部工具栏布局
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(
            self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(
            self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(
            self.audioSeparationButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)

class ClipSectionConfigCard(GroupHeaderCardWidget):
    """音视频切分配置卡片"""
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setTitle(self.tr("音视频切分"))
        self.mediaParser = None

        self.targetFileButton = PushButton(self.tr("选择"))
        self.clipFileStartLineEdit = LineEdit()
        self.clipFileEndLineEdit = LineEdit()

        self.time_widget = QWidget(self)
        self.time_layout = QHBoxLayout(self.time_widget)
        
        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(
            self.tr("点击切分按钮开始切分") + ' 👉')
        self.clipSectionButton = PrimaryPushButton(
            self.tr("切分"), self, FluentIcon.PLAY_SOLID)
        
        

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.targetFileButton.setFixedWidth(120)
        self.clipFileStartLineEdit.setFixedWidth(120)
        self.clipFileEndLineEdit.setFixedWidth(120)

        self.clipFileStartLineEdit.setClearButtonEnabled(True)    # 用于启用清除按钮功能 (文字旁边的x)
        self.clipFileEndLineEdit.setClearButtonEnabled(True)

        self.clipFileStartLineEdit.setPlaceholderText(self.tr("开始时间（HH:MM:SS.xxx）"))
        self.clipFileEndLineEdit.setPlaceholderText(self.tr("结束时间（HH:MM:SS.xxx）"))

        self.time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_layout.setSpacing(10)
        self.time_layout.addWidget(self.clipFileStartLineEdit)
        self.time_layout.addWidget(self.clipFileEndLineEdit)
        self.time_layout.addStretch(1)

        self._initLayout()

    def _initLayout(self):
        self.addGroup(
            icon=FluentIcon.VIDEO,
            title=self.tr("目标文件"),
            content=self.tr("选择待切分的文件"),
            widget=self.targetFileButton
        )
        
        self.addGroup(
            icon=FluentIcon.CALENDAR,
            title=self.tr("开始与结束时间"),
            content=self.tr("填写开始和结束时间"),
            widget=self.time_widget
        )

        # 设置底部工具栏布局
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(
            self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(
            self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(
            self.clipSectionButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)



        

        


    


