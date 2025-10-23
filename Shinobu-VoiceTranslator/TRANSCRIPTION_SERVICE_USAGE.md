# TranscriptionService 使用文档

## 📋 概述

`TranscriptionService` 是一个完整的语音转文字服务，使用 `TaskExecutor` 进行线程管理，支持多种 Whisper 引擎和输出格式。

## ✨ 主要特性

- **🎯 线程池管理**：使用项目的 `concurrent` 模块进行异步任务处理
- **🎙️ 多引擎支持**：支持 whisper.cpp (ggml) 和 faster-whisper
- **📝 多格式输出**：支持 SRT、CSV 等多种输出格式
- **🔄 音频提取**：自动从视频中提取 16k 采样率的音频
- **📊 进度追踪**：实时任务状态和进度更新
- **🛡️ 异常处理**：完善的错误处理和日志记录

## 🚀 基本用法

### 1. 导入服务

```python
from app.services.transcription_service import transcriptionService, WhisperEngine, OutputFormat
```

### 2. 创建听写任务

```python
# 基础用法 - 使用默认参数
task = transcriptionService.createTask(
    input_path="/path/to/video.mp4"
)

# 完整参数示例
task = transcriptionService.createTask(
    input_path="/path/to/video.mp4",
    whisper_model="ggml-medium.bin",  # Whisper 模型
    language="ja",                     # 源语言（ja=日语, en=英语, zh=中文）
    output_format=OutputFormat.SRT_ORIGINAL,  # 输出格式
    whisper_params="--threads 4",      # Whisper 额外参数
    csv_include_timestamp=True         # CSV 是否包含时间戳
)
```

### 3. 监听任务状态

```python
# 连接信号
transcriptionService.taskCreated.connect(on_task_created)
transcriptionService.taskUpdated.connect(on_task_updated)
transcriptionService.taskFinished.connect(on_task_finished)
transcriptionService.logGenerated.connect(on_log_generated)

def on_task_created(task):
    print(f"任务已创建: {task.fileName}")

def on_task_updated(task):
    print(f"进度: {task.progress}%")

def on_task_finished(task, success, error_msg):
    if success:
        print(f"任务完成: {task.outputPath}")
    else:
        print(f"任务失败: {error_msg}")

def on_log_generated(level, message):
    print(f"[{level}] {message}")
```

## 🔧 配置选项

### Whisper 引擎类型

```python
from app.services.transcription_service import WhisperEngine

# whisper.cpp (ggml 格式)
whisper_model = "ggml-medium.bin"
# 或 "ggml-small.bin", "ggml-large.bin" 等

# faster-whisper
whisper_model = "faster-whisper-medium"
# 或 "faster-whisper-small", "faster-whisper-large" 等

# 跳过听写（仅格式转换）
whisper_model = WhisperEngine.NONE
```

### 支持的语言

```python
# 常用语言代码
"ja"  # 日语
"en"  # 英语
"zh"  # 中文
"ko"  # 韩语
"fr"  # 法语
"de"  # 德语
"es"  # 西班牙语
# ... 更多语言请参考 Whisper 文档
```

### 输出格式

```python
from app.services.transcription_service import OutputFormat

OutputFormat.SRT_ORIGINAL   # 原文 SRT
OutputFormat.CSV            # CSV 格式
OutputFormat.SRT_TRANSLATED # 中文 SRT（需配合翻译服务）
OutputFormat.SRT_BILINGUAL  # 双语 SRT（需配合翻译服务）
OutputFormat.LRC            # LRC 歌词格式（需配合翻译服务）
```

## 📖 完整示例

### 示例 1：处理单个视频文件

```python
from app.services.transcription_service import (
    transcriptionService, 
    WhisperEngine, 
    OutputFormat
)

# 创建任务
task = transcriptionService.createTask(
    input_path="E:/Videos/anime_episode.mp4",
    whisper_model="ggml-medium.bin",
    language="ja",
    output_format=OutputFormat.SRT_ORIGINAL,
    whisper_params="--threads 4 --max-len 42"
)

# 任务会自动开始执行
# 完成后会在视频同目录生成 anime_episode.srt
```

### 示例 2：批量处理文件

```python
import os
from pathlib import Path

video_folder = Path("E:/Videos")
video_files = list(video_folder.glob("*.mp4"))

for video_file in video_files:
    task = transcriptionService.createTask(
        input_path=str(video_file),
        whisper_model="faster-whisper-medium",
        language="ja",
        output_format=OutputFormat.CSV,
        csv_include_timestamp=True
    )
    print(f"已提交任务: {video_file.name}")

# 所有任务会在线程池中并发执行
```

### 示例 3：SRT 格式转换

```python
# 如果已有 SRT 文件，只需要转换格式
task = transcriptionService.createTask(
    input_path="E:/Subtitles/subtitle.srt",
    output_format=OutputFormat.CSV,
    csv_include_timestamp=False  # 仅输出文本，不含时间戳
)
```

### 示例 4：在 UI 中集成

```python
from PySide6.QtWidgets import QPushButton, QFileDialog, QTextEdit

class TranscribeWindow:
    def __init__(self):
        self.start_button = QPushButton("开始听写")
        self.log_text = QTextEdit()
        
        # 连接信号
        self.start_button.clicked.connect(self.on_start_clicked)
        transcriptionService.logGenerated.connect(self.on_log)
        transcriptionService.taskFinished.connect(self.on_finished)
    
    def on_start_clicked(self):
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mkv *.avi)"
        )
        
        if file_path:
            # 创建任务
            transcriptionService.createTask(
                input_path=file_path,
                whisper_model="ggml-medium.bin",
                language="ja",
                output_format=OutputFormat.SRT_ORIGINAL
            )
    
    def on_log(self, level, message):
        # 显示日志
        self.log_text.append(f"[{level}] {message}")
    
    def on_finished(self, task, success, error_msg):
        if success:
            self.log_text.append(f"✅ 完成: {task.outputPath}")
        else:
            self.log_text.append(f"❌ 失败: {error_msg}")
```

## 🔄 任务管理

### 取消任务

```python
# 创建任务
task = transcriptionService.createTask(input_path="video.mp4")

# 取消任务
transcriptionService.cancel(task)
```

### 重启任务

```python
# 重启失败的任务
transcriptionService.restart(task)
```

### 检查服务状态

```python
if transcriptionService.isAvailable():
    print("听写服务可用")
else:
    print("请安装 ffmpeg")
```

## ⚙️ 高级配置

### 自定义 Whisper 参数

```python
# whisper.cpp 参数
task = transcriptionService.createTask(
    input_path="video.mp4",
    whisper_model="ggml-medium.bin",
    whisper_params="--threads 8 --max-len 42 --max-context 448"
)

# faster-whisper 参数
task = transcriptionService.createTask(
    input_path="video.mp4",
    whisper_model="faster-whisper-medium",
    faster_whisper_params="--beam_size 5 --best_of 5"
)
```

### CSV 输出选项

```python
# 包含时间戳的 CSV
task = transcriptionService.createTask(
    input_path="video.mp4",
    output_format=OutputFormat.CSV,
    csv_include_timestamp=True
)
# 输出: start,end,text

# 仅文本的 CSV
task = transcriptionService.createTask(
    input_path="video.mp4",
    output_format=OutputFormat.CSV,
    csv_include_timestamp=False
)
# 输出: text
```

## 🐛 故障排除

### 1. 服务不可用

```python
问题: transcriptionService.isAvailable() 返回 False
解决: 
- 确保已安装 ffmpeg 并添加到系统 PATH
- Windows: 下载 ffmpeg.exe 并放到项目目录或 PATH
- Linux/Mac: sudo apt install ffmpeg 或 brew install ffmpeg
```

### 2. Whisper 模型未找到

```python
错误: 未生成 SRT 文件
解决:
- 确保模型文件在正确的目录（whisper/ 或 whisper-faster/）
- 检查模型文件名是否正确
- 验证 Whisper 可执行文件是否存在
```

### 3. 音频提取失败

```python
错误: 音频提取失败
解决:
- 检查输入文件是否损坏
- 确保有足够的磁盘空间
- 尝试用其他播放器打开视频验证
```

## 📊 性能优化

### 1. 线程数配置

```python
# 根据 CPU 核心数调整线程数
import os
cpu_count = os.cpu_count()

task = transcriptionService.createTask(
    input_path="video.mp4",
    whisper_params=f"--threads {cpu_count}"
)
```

### 2. 选择合适的模型

- **ggml-tiny**: 最快，准确度较低
- **ggml-base**: 快速，准确度一般
- **ggml-small**: 平衡
- **ggml-medium**: 较慢，准确度高（推荐）
- **ggml-large**: 最慢，准确度最高

### 3. 批处理优化

```python
# 使用 Future.gather 等待所有任务完成
from app.common.concurrent import Future

tasks = []
for video in video_list:
    task = transcriptionService.createTask(input_path=video)
    if task and task.id in transcriptionService.futures:
        tasks.append(transcriptionService.futures[task.id])

# 等待所有任务完成
if tasks:
    batch_future = Future.gather(tasks)
    batch_future.done.connect(lambda: print("所有任务已完成！"))
```

## 🎯 与其他服务集成

### 与下载服务配合

```python
from app.services.downloadservice.download_service import downloadService
from app.services.transcription_service import transcriptionService

# 先下载视频
download_task = downloadService.createTask("https://www.bilibili.com/video/BV...")

# 监听下载完成，然后听写
def on_download_finished(task, success, error_msg):
    if success and task.outputPath:
        # 下载完成后自动听写
        transcriptionService.createTask(
            input_path=task.outputPath,
            whisper_model="ggml-medium.bin",
            language="ja"
        )

downloadService.taskFinished.connect(on_download_finished)
```

## 📝 注意事项

1. **文件路径**：支持中文路径，但建议使用英文路径避免潜在问题
2. **临时文件**：`.16k.wav` 文件会在任务完成后自动删除
3. **输出位置**：输出文件默认保存在输入文件同目录
4. **并发限制**：线程池默认最大线程数为 `2 * CPU核心数`
5. **取消任务**：由于 `cancelTask` 可能不稳定，建议让任务自然完成

## 🔗 相关文档

- [concurrent 模块说明](./app/common/concurrent/)
- [BaseService 基类](./app/services/base_service.py)
- [Whisper 官方文档](https://github.com/openai/whisper)

---

**版本**: 1.0  
**最后更新**: 2025-10-23

