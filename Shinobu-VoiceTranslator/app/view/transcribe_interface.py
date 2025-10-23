from PySide6.QtCore import Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition

from ..components.info_card import TranscribeModeInfoCard
from ..components.config_card import TranscribeConfigCard
from ..services.transcription_service import transcriptionService, WhisperEngine, OutputFormat
from ..common.signal_bus import signalBus
from ..common.config import cfg


class TranscribeInterface(ScrollArea):
    """听写界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None
        
        # 当前选择的文件路径
        self.selectedFilePath = None

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

    def _onSelectFileButtonClicked(self):
        """选择文件按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("选择文件"),
            cfg.get(cfg.saveFolder),
            self.tr("视频/音频文件 (*.mp4 *.mkv *.avi *.mp3 *.wav *.flac);;所有文件 (*.*)")
        )
        
        if file_path:
            self.selectedFilePath = file_path
            # 更新按钮文本显示文件名
            from pathlib import Path
            file_name = Path(file_path).name
            # 截断过长的文件名
            if len(file_name) > 15:
                display_name = file_name[:12] + "..."
            else:
                display_name = file_name
            
            self.transcribeConfigCard.targetFileButton.setText(display_name)
            
            InfoBar.success(
                self.tr("文件已选择"),
                file_name,
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )

    def _onSaveFolderButtonClicked(self):
        """保存目录按钮点击事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("选择保存目录"),
            cfg.get(cfg.saveFolder)
        )
        
        if folder_path:
            cfg.set(cfg.saveFolder, folder_path)
            # 更新配置卡中显示的路径
            self.transcribeConfigCard.groups[4].contentLabel.setText(folder_path)
            
            InfoBar.success(
                self.tr("保存目录已更新"),
                folder_path,
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )
    
    def _onTranscribeButtonClicked(self):
        """听写按钮点击事件"""
        # 1. 检查服务是否可用
        if not transcriptionService.isAvailable():
            InfoBar.error(
                self.tr("服务不可用"),
                self.tr("听写服务当前不可用，请确保 ffmpeg 已安装"),
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            return
        
        # 2. 检查是否选择了文件
        if not self.selectedFilePath:
            InfoBar.warning(
                self.tr("未选择文件"),
                self.tr("请先选择要听写的文件"),
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            return
        
        # 3. 获取配置参数
        # 听写模型映射
        model_map = {
            "whisper": "ggml-medium.bin",  # 默认使用 medium 模型
            "whisper-faster(仅限N卡)": "faster-whisper-medium"
        }
        
        # 语言映射
        language_map = {
            "中文": "zh",
            "日语": "ja",
            "英语": "en",
            "韩语": "ko",
            "俄语": "ru",
            "法语": "fr"
        }
        
        # 获取选择的值
        model_text = self.transcribeConfigCard.transcribeModelComboBox.currentText()
        language_text = self.transcribeConfigCard.inputLanguageComboBox.currentText()
        output_format = self.transcribeConfigCard.outputFileTypeComBox.currentText()
        
        whisper_model = model_map.get(model_text, "ggml-medium.bin")
        language = language_map.get(language_text, "ja")
        
        # 4. 创建听写任务
        task = transcriptionService.createTask(
            input_path=self.selectedFilePath,
            whisper_model=whisper_model,
            language=language,
            output_format=output_format,
            include_timestamp=True  # 默认开启时间戳
        )
        
        if task:
            InfoBar.success(
                self.tr("任务创建成功"),
                self.tr("已创建听写任务，请到任务管理查看进度"),
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            # 重置文件选择
            self.selectedFilePath = None
            self.transcribeConfigCard.targetFileButton.setText(self.tr("选择"))
        else:
            InfoBar.error(
                self.tr("任务创建失败"),
                self.tr("无法创建听写任务，请检查文件和配置"),
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )

    def _onTaskCreated(self, task):
        """任务创建回调"""
        # 可以在这里添加额外的UI更新
        pass

    def _onTaskFinished(self, task, success, error_msg):
        """任务完成回调"""
        if success:
            InfoBar.success(
                self.tr("听写完成"),
                self.tr(f"文件 {task.fileName} 听写完成"),
                duration=5000,
                position=InfoBarPosition.TOP,
                parent=self
            )
        else:
            InfoBar.error(
                self.tr("听写失败"),
                error_msg,
                duration=5000,
                position=InfoBarPosition.TOP,
                parent=self
            )

    def _onLogGenerated(self, level, message):
        """日志生成回调"""
        # 可以在这里显示日志到界面
        # 例如在状态栏或专门的日志区域显示
        pass

    def _connectSignalToSlot(self):
        """连接信号与槽"""
        # 1. 连接配置卡片的按钮信号
        self.transcribeConfigCard.targetFileButton.clicked.connect(
            self._onSelectFileButtonClicked
        )
        self.transcribeConfigCard.saveFolderButton.clicked.connect(
            self._onSaveFolderButtonClicked
        )
        self.transcribeConfigCard.transcribeButton.clicked.connect(
            self._onTranscribeButtonClicked
        )
        
        # 2. 连接听写服务的信号
        transcriptionService.taskCreated.connect(self._onTaskCreated)
        transcriptionService.taskFinished.connect(self._onTaskFinished)
        transcriptionService.logGenerated.connect(self._onLogGenerated)
        
        # 3. 可选：连接全局信号总线（如果需要跨界面通信）
        # signalBus.taskCreated.connect(...)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        """拖拽释放事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # 检查文件扩展名
            from pathlib import Path
            valid_extensions = ['.mp4', '.mkv', '.avi', '.mp3', '.wav', '.flac', '.srt']
            if Path(file_path).suffix.lower() in valid_extensions:
                self.selectedFilePath = file_path
                file_name = Path(file_path).name
                
                # 更新按钮显示
                if len(file_name) > 15:
                    display_name = file_name[:12] + "..."
                else:
                    display_name = file_name
                
                self.transcribeConfigCard.targetFileButton.setText(display_name)
                
                InfoBar.success(
                    self.tr("文件已添加"),
                    file_name,
                    duration=2000,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
            else:
                InfoBar.warning(
                    self.tr("不支持的文件格式"),
                    self.tr("请拖入视频或音频文件"),
                    duration=2000,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
        
        event.acceptProposedAction()