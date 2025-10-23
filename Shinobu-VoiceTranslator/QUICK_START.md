# 🚀 快速开始指南

## 欢迎使用 Shinobu-VoiceTranslator 的 Concurrent 线程管理系统！

本指南将帮助您快速了解如何使用项目中的服务。

## 📦 前置要求

### 必需组件
- ✅ Python 3.8+
- ✅ PySide6
- ✅ ffmpeg (用于音视频处理)

### 可选组件
- Whisper 模型 (用于语音识别)
- yt-dlp (用于 YouTube 下载)
- bilibili-dl (用于 B站下载)

## 🎯 5分钟快速入门

### 1. 下载视频

```python
from Shinobu-VoiceTranslator.app.services.downloadservice.download_service import downloadService

# 下载 B站视频
task = downloadService.createTask("https://www.bilibili.com/video/BV1xx411c7XD")

# 或下载 YouTube 视频
task = downloadService.createTask("https://www.youtube.com/watch?v=...")

# 监听完成事件
downloadService.taskFinished.connect(
    lambda task, success, error: print(f"完成: {task.outputPath}")
)
```

### 2. 语音转文字

```python
from Shinobu-VoiceTranslator.app.services.transcription_service import (
    transcriptionService,
    WhisperEngine,
    OutputFormat
)

# 创建听写任务
task = transcriptionService.createTask(
    input_path="video.mp4",
    whisper_model="ggml-medium.bin",
    language="ja",  # 日语
    output_format=OutputFormat.SRT_ORIGINAL
)

# 监听进度
transcriptionService.logGenerated.connect(
    lambda level, msg: print(f"[{level}] {msg}")
)
```

### 3. 完整工作流

```python
from PySide6.QtCore import QCoreApplication
import sys

app = QCoreApplication(sys.argv)

# 步骤 1: 下载视频
def download_and_transcribe(url):
    task = downloadService.createTask(url)
    
    # 步骤 2: 下载完成后自动听写
    def on_download_finished(task, success, error):
        if success and task.outputPath:
            print(f"✅ 下载完成: {task.outputPath}")
            
            # 开始听写
            transcriptionService.createTask(
                input_path=task.outputPath,
                whisper_model="ggml-medium.bin",
                language="ja",
                output_format=OutputFormat.SRT_ORIGINAL
            )
    
    # 步骤 3: 听写完成
    def on_transcribe_finished(task, success, error):
        if success:
            print(f"✅ 听写完成: {task.outputPath}")
        app.quit()
    
    downloadService.taskFinished.connect(on_download_finished)
    transcriptionService.taskFinished.connect(on_transcribe_finished)

# 运行
download_and_transcribe("https://www.bilibili.com/video/BV1xx411c7XD")
sys.exit(app.exec())
```

## 📝 常用代码片段

### 批量下载

```python
urls = [
    "https://www.bilibili.com/video/BV1...",
    "https://www.bilibili.com/video/BV2...",
    "https://www.bilibili.com/video/BV3..."
]

for url in urls:
    downloadService.createTask(url)

print(f"已提交 {len(urls)} 个下载任务")
```

### 批量转录

```python
from pathlib import Path

video_folder = Path("E:/Videos")
videos = list(video_folder.glob("*.mp4"))

for video in videos:
    transcriptionService.createTask(
        input_path=str(video),
        whisper_model="ggml-medium.bin",
        language="ja"
    )

print(f"已提交 {len(videos)} 个转录任务")
```

### 监听所有事件

```python
# 下载服务
downloadService.taskCreated.connect(
    lambda task: print(f"📥 创建下载: {task.fileName}")
)
downloadService.taskUpdated.connect(
    lambda task: print(f"📊 下载进度: {task.progress}%")
)
downloadService.taskFinished.connect(
    lambda task, success, error: print(
        f"{'✅' if success else '❌'} 下载完成: {task.fileName}"
    )
)

# 听写服务
transcriptionService.logGenerated.connect(
    lambda level, msg: print(f"[{level}] {msg}")
)
transcriptionService.taskFinished.connect(
    lambda task, success, error: print(
        f"{'✅' if success else '❌'} 转录完成: {task.fileName}"
    )
)
```

## 🔧 配置选项

### Whisper 模型选择

```python
# 速度快，准确度较低
whisper_model = "ggml-tiny.bin"

# 平衡（推荐）
whisper_model = "ggml-medium.bin"

# 准确度高，速度慢
whisper_model = "ggml-large.bin"

# 使用 faster-whisper
whisper_model = "faster-whisper-medium"
```

### 输出格式

```python
from Shinobu-VoiceTranslator.app.services.transcription_service import OutputFormat

# SRT 字幕文件
output_format = OutputFormat.SRT_ORIGINAL

# CSV 文件（包含时间戳）
output_format = OutputFormat.CSV
csv_include_timestamp = True

# CSV 文件（仅文本）
output_format = OutputFormat.CSV
csv_include_timestamp = False
```

### 语言设置

```python
language = "ja"  # 日语
language = "en"  # 英语
language = "zh"  # 中文
language = "ko"  # 韩语
```

## 🎨 在 GUI 中使用

### 简单的窗口示例

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtCore import QCoreApplication

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shinobu Voice Translator")
        self.resize(800, 600)
        
        # UI 组件
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.download_btn = QPushButton("下载视频")
        self.download_btn.clicked.connect(self.on_download)
        layout.addWidget(self.download_btn)
        
        self.transcribe_btn = QPushButton("转录视频")
        self.transcribe_btn.clicked.connect(self.on_transcribe)
        layout.addWidget(self.transcribe_btn)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # 连接服务信号
        downloadService.logGenerated.connect(self.add_log)
        transcriptionService.logGenerated.connect(self.add_log)
    
    def add_log(self, level, message):
        self.log_text.append(f"[{level}] {message}")
    
    def on_download(self):
        url = "https://www.bilibili.com/video/BV1xx411c7XD"
        downloadService.createTask(url)
    
    def on_transcribe(self):
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mkv *.avi)"
        )
        
        if file_path:
            transcriptionService.createTask(
                input_path=file_path,
                whisper_model="ggml-medium.bin",
                language="ja"
            )

# 运行
app = QCoreApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
```

## 🐛 常见问题

### 1. 服务不可用

**问题**: `transcriptionService.isAvailable()` 返回 False

**解决**:
```bash
# Windows
# 下载 ffmpeg 并添加到 PATH

# Linux
sudo apt install ffmpeg

# Mac
brew install ffmpeg
```

### 2. 任务没有执行

**问题**: 创建任务后没有任何反应

**解决**:
```python
# 确保 Qt 事件循环在运行
app = QCoreApplication(sys.argv)
# ... 创建任务 ...
sys.exit(app.exec())  # 保持事件循环
```

### 3. 找不到模型文件

**问题**: Whisper 模型未找到

**解决**:
```bash
# 确保模型文件在正确的目录
whisper/
├── ggml-tiny.bin
├── ggml-base.bin
├── ggml-small.bin
├── ggml-medium.bin
└── ggml-large.bin
```

## 📚 进阶阅读

- [TranscriptionService 详细文档](./TRANSCRIPTION_SERVICE_USAGE.md)
- [Concurrent 集成总结](./CONCURRENT_INTEGRATION_SUMMARY.md)
- [测试示例](./test_transcription_service.py)

## 💡 提示

1. **性能优化**: 根据 CPU 核心数调整线程数
   ```python
   import os
   threads = os.cpu_count()
   whisper_params = f"--threads {threads}"
   ```

2. **批量处理**: 多个任务会自动并发执行
   ```python
   # 所有任务会在线程池中同时运行
   for file in files:
       transcriptionService.createTask(input_path=file)
   ```

3. **错误处理**: 始终监听 `taskFinished` 信号
   ```python
   service.taskFinished.connect(
       lambda task, success, error: 
           print(error) if not success else None
   )
   ```

4. **资源清理**: 应用关闭时清理服务
   ```python
   def closeEvent(self, event):
       downloadService.cleanup()
       transcriptionService.cleanup()
       event.accept()
   ```

## 🎉 开始使用

现在您已经准备好开始使用了！

1. 查看 [测试示例](./test_transcription_service.py)
2. 阅读 [详细文档](./TRANSCRIPTION_SERVICE_USAGE.md)
3. 开始构建您的应用！

祝您使用愉快！ 🎊

---

**有问题？** 查看 [CONCURRENT_INTEGRATION_SUMMARY.md](./CONCURRENT_INTEGRATION_SUMMARY.md) 获取更多信息。

