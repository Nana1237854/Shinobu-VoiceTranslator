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
        self.urlLineEdit.setFixedWidth(320)
        
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
            icon=FluentIcon.FOLDER,  # 文件夹图标
            title=self.tr("保存目录"),
            content=cfg.get(cfg.saveFolder),
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
        self.saveFolderButton = PushButton(self.tr("选择"), self, FluentIcon.FOLDER)

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
            content=cfg.get(cfg.saveFolder),
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
        self.saveFolderButton = PushButton(self.tr("选择"), self, FluentIcon.FOLDER)
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
        
        # 动态加载 Whisper 模型列表
        self._loadWhisperModels()
        
        self.inputLanguageComboBox.addItems(["中文", "日语", "英语", "韩语", "俄语", "法语"])
        self.outputFileTypeComBox.addItems(
            ["原文SRT", "双语SRT", "原文LRC", "原文TXT", 
             "双语TXT", "原文XLSX", "双语XLSX"]
            )

        self._initLayout()
    
    def _loadWhisperModels(self):
        """加载可用的 Whisper 模型到下拉菜单"""
        from ..services.transcription_service import transcriptionService
        
        # 获取可用模型列表
        available_models = transcriptionService.get_available_models()
        
        # 添加基础选项
        model_items = []
        
        # 如果有扫描到的模型，添加到列表
        if available_models:
            print(f"[UI] 加载 {len(available_models)} 个可用模型到下拉菜单")
            for model in available_models:
                # 生成用户友好的显示名称
                if model.startswith('faster-whisper-'):
                    display_name = f"Faster-Whisper ({model[15:]})"
                else:
                    display_name = model
                model_items.append(display_name)
        
        # 如果没有扫描到模型，添加默认选项
        if not model_items:
            model_items = ["whisper", "whisper-faster(仅限N卡)"]
            print("[UI] 未扫描到模型，使用默认选项")
        
        self.transcribeModelComboBox.addItems(model_items)
        
        # 保存模型映射关系（显示名称 -> 实际模型名）
        self._model_name_map = {}
        if available_models:
            for model, display in zip(available_models, model_items):
                self._model_name_map[display] = model
    
    def getSelectedModel(self) -> str:
        """
        获取用户选择的模型名称（实际模型名，非显示名）
        
        Returns:
            模型名称
        """
        display_name = self.transcribeModelComboBox.currentText()
        
        # 如果有映射关系，返回实际模型名
        if hasattr(self, '_model_name_map') and display_name in self._model_name_map:
            return self._model_name_map[display_name]
        
        # 否则返回显示名
        return display_name

    
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
        self.saveFolderGroup = self.addGroup(
            icon=FluentIcon.FOLDER,
            title=self.tr("Save Folder"),
            content=cfg.get(cfg.saveFolder),
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
        self.saveFolderButton = PushButton(self.tr("选择"), self, FluentIcon.FOLDER)

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
        self.addGroup(
            icon=FluentIcon.FOLDER,  # 文件夹图标
            title=self.tr("保存目录"),
            content=cfg.get(cfg.saveFolder),
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
        self.saveFolderButton = PushButton(self.tr("选择"), self, FluentIcon.FOLDER)

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
        self.clipFileStartLineEdit.setFixedWidth(250)
        self.clipFileEndLineEdit.setFixedWidth(250)

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
        self.addGroup(
            icon=FluentIcon.FOLDER,  # 文件夹图标
            title=self.tr("保存目录"),
            content=cfg.get(cfg.saveFolder),
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
            self.clipSectionButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)

class CompleteConfigCard(GroupHeaderCardWidget):
    """完整模式卡片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("完整模式设置"))
        self.mediaParser = None

        self.targetFileButton = PushButton(self.tr("选择"))
        self.urlLineEdit = LineEdit()
        self.transcribeModelComboBox = ComboBox()
        self.inputLanguageComboBox = ComboBox()
        self.timeStampButton = SwitchButton(self.tr("关闭"), self)
        self.averageCompactSpinBox = CompactSpinBox()
        self.translateModelComboBox = ComboBox()
        self.targetLanguageComboBox = ComboBox()
        self.outputWordFileTypeComboBox = ComboBox()
        self.fileNameLineEdit = LineEdit()
        self.saveFolderButton = PushButton(self.tr("选择"), self, FluentIcon.FOLDER)

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(
            self.tr("点击运行按钮开始运行") + ' 👉')
        self.runButton = PrimaryPushButton(
            self.tr("运行"), self, FluentIcon.PLAY_SOLID)

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.targetFileButton.setFixedWidth(120)

        self.urlLineEdit.setPlaceholderText(self.tr("请输入下载链接"))
        self.urlLineEdit.setClearButtonEnabled(True)
        self.urlLineEdit.setFixedWidth(320)

        self.transcribeModelComboBox.setFixedWidth(320)
        self.inputLanguageComboBox.setFixedWidth(320)
        self.transcribeModelComboBox.addItems(["whisper", "whisper-faster(仅限N卡)", "不进行听写"])
        self.inputLanguageComboBox.addItems(["中文", "日语", "英语", "韩语", "俄语", "法语"])

        # 更改按钮状态
        self.timeStampButton.setChecked(True)
        # 默认关闭
        self.timeStampButton.setOffText("关闭")
        self.timeStampButton.setOnText("开启")

        self.averageCompactSpinBox.setRange(0, 10)
        self.averageCompactSpinBox.setValue(0)

        self.translateModelComboBox.setFixedWidth(320)
        self.targetLanguageComboBox.setFixedWidth(320)
        self.translateModelComboBox.addItems(["galtransl", "sakura", "llamacpp","在线模型", "不进行翻译"])
        self.targetLanguageComboBox.addItems(["中文", "日语", "英语", "韩语", "俄语", "法语"])

        self.outputWordFileTypeComboBox.addItems(
            ["原文SRT", "双语SRT", "原文LRC", "原文TXT", 
             "双语TXT", "原文XLSX", "双语XLSX", "不生成文本文件"]
            )
        
        self.fileNameLineEdit.setFixedWidth(320)
        self.fileNameLineEdit.setPlaceholderText(self.tr("输入保存的文件名，不包含后缀"))

        self._initLayout()
        

    def _initLayout(self):
        self.addGroup(
            icon=FluentIcon.DOWNLOAD.icon(),
            title=self.tr("目标文件"),
            content=self.tr("选择你要处理的文件"),
            widget=self.targetFileButton
        )
        self.addGroup(
            icon=FluentIcon.GLOBE.icon(),
            title=self.tr("下载链接"),
            content=self.tr("请输入需要下载视频的链接"),
            widget=self.urlLineEdit
        )
        self.addGroup(
            icon=FluentIcon.HEADPHONE.icon(),
            title= self.tr("听写模型"),
            content=self.tr("选择用于听写的模型类别"),
            widget=self.transcribeModelComboBox
        )
        self.addGroup(
            icon=FluentIcon.FEEDBACK.icon(),
            title=self.tr("输入语言"),
            content=self.tr("选择输入的语言"),
            widget=self.inputLanguageComboBox
        )
        self.addGroup(
            icon=FluentIcon.UNIT.icon(),
            title=self.tr("时间戳"),
            content=self.tr("是否生成时间戳（仅用于快速定位原句，不保证精确）"),
            widget=self.timeStampButton
        )
        self.addGroup(
            icon=FluentIcon.CLIPPING_TOOL.icon(),
            title=self.tr("均分音频"),
            content=self.tr("按人数均分音频生成文件（用于字幕组快速分工）"),
            widget=self.averageCompactSpinBox
        )
        self.addGroup(
            icon=FluentIcon.LANGUAGE.icon(),
            title= self.tr("翻译模型"),
            content=self.tr("选择用于翻译的模型类别"),
            widget=self.translateModelComboBox
        )
        self.addGroup(
            icon=FluentIcon.LABEL.icon(),
            title=self.tr("输出语言"),
            content=self.tr("选择输出的语言"),
            widget=self.targetLanguageComboBox
        )
        self.addGroup(
            icon=FluentIcon.TAG.icon(),
            title=self.tr("输出文本文件"),
            content=self.tr("选择输出的文本文件"),
            widget=self.outputWordFileTypeComboBox
        )
        self.addGroup(
            icon=FluentIcon.INFO.icon(),
            title=self.tr("文件名"),
            content=self.tr("设置保存的视频文件名（当生成视频文件时使用）"),
            widget=self.fileNameLineEdit
        )
        self.addGroup(
            icon=FluentIcon.FOLDER,  # 文件夹图标
            title=self.tr("保存目录"),
            content=cfg.get(cfg.saveFolder),
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
            self.runButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)

        

        


    


