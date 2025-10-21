# coding:utf-8
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import uuid


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 待处理
    RUNNING = "running"      # 运行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"        # 已暂停


class TaskType(Enum):
    """任务类型枚举"""
    DOWNLOAD = "download"          # 下载任务
    TRANSLATE = "translate"        # 翻译任务
    TRANSCRIBE = "transcribe"      # 听写任务
    VOCAL_SEPARATE = "vocal_separate"  # 人声分离任务
    MEDIA_SPLIT = "media_split"    # 音视频切分任务


class DownloadSource(Enum):
    """下载来源枚举"""
    BILIBILI = "bilibili"
    YOUTUBE = "youtube"
    LOCAL = "local"
    OTHER = "other"


class TranslationEngine(Enum):
    """翻译引擎枚举"""
    GOOGLE = "google"
    BAIDU = "baidu"
    DEEPL = "deepl"
    OPENAI = "openai"
    LOCAL = "local"


class TranscriptionEngine(Enum):
    """听写引擎枚举"""
    WHISPER = "whisper"
    BAIDU = "baidu"
    GOOGLE = "google"
    AZURE = "azure"


class VocalSeparateModel(Enum):
    """人声分离模型枚举"""
    SPLEETER = "spleeter"
    DEMUCS = "demucs"
    UVR = "uvr"


class MediaType(Enum):
    """媒体类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class TaskConfig:
    """任务配置基类"""
    pass


@dataclass
class DownloadConfig(TaskConfig):
    """下载任务配置"""
    source: str = DownloadSource.BILIBILI.value
    quality: str = "best"  # 视频质量
    format: str = "mp4"    # 输出格式
    proxy: str = ""        # 代理设置
    cookies: str = ""      # Cookie文件路径
    headers: Dict[str, str] = field(default_factory=dict)  # 自定义请求头


@dataclass
class TranslateConfig(TaskConfig):
    """翻译任务配置"""
    engine: str = TranslationEngine.GOOGLE.value  # 翻译引擎
    sourceLang: str = "auto"    # 源语言
    targetLang: str = "zh-CN"   # 目标语言
    apiKey: str = ""            # API密钥
    apiUrl: str = ""            # API地址
    modelName: str = ""         # 模型名称（如GPT-4）
    maxTokens: int = 2000       # 最大token数
    temperature: float = 0.3    # 温度参数
    glossary: Dict[str, str] = field(default_factory=dict)  # 术语表


@dataclass
class TranscribeConfig(TaskConfig):
    """听写任务配置"""
    engine: str = TranscriptionEngine.WHISPER.value  # 听写引擎
    language: str = "auto"      # 语言
    modelSize: str = "base"     # 模型大小 (tiny/base/small/medium/large)
    apiKey: str = ""            # API密钥
    outputFormat: str = "srt"   # 输出格式 (srt/vtt/txt/json)
    enableTimestamp: bool = True  # 启用时间戳
    enableWordLevel: bool = False  # 启用词级时间戳
    translate: bool = False     # 是否翻译为英文
    prompt: str = ""            # 提示词


@dataclass
class VocalSeparateConfig(TaskConfig):
    """人声分离任务配置"""
    model: str = VocalSeparateModel.SPLEETER.value  # 分离模型
    stems: int = 2              # 分离轨道数 (2/4/5)
    outputFormat: str = "wav"   # 输出格式
    bitrate: str = "256k"       # 比特率
    sampleRate: int = 44100     # 采样率
    exportVocals: bool = True   # 导出人声
    exportInstrumental: bool = True  # 导出伴奏
    exportOther: bool = False   # 导出其他轨道


@dataclass
class MediaSplitConfig(TaskConfig):
    """音视频切分任务配置"""
    mediaType: str = MediaType.VIDEO.value  # 媒体类型
    splitMode: str = "duration"  # 切分模式 (duration/size/count/custom)
    duration: int = 300         # 每段时长（秒）
    fileSize: int = 50          # 每段文件大小（MB）
    segmentCount: int = 1       # 切分段数
    customPoints: List[float] = field(default_factory=list)  # 自定义切分点（秒）
    outputFormat: str = "mp4"   # 输出格式
    keepAudio: bool = True      # 保留音频
    keepVideo: bool = True      # 保留视频
    quality: str = "same"       # 输出质量 (same/high/medium/low)


@dataclass
class Task:
    """任务模型 - 支持多种任务类型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = TaskType.DOWNLOAD.value  # 任务类型
    status: TaskStatus = TaskStatus.PENDING
    
    # 任务基本信息
    name: str = ""              # 任务名称
    fileName: str = ""          # 文件名
    description: str = ""       # 任务描述
    
    # 输入/输出
    url: str = ""               # 下载链接（下载任务）
    inputPath: str = ""         # 输入文件路径（处理任务）
    outputPath: str = ""        # 输出文件路径
    outputPaths: List[str] = field(default_factory=list)  # 多个输出文件
    logFile: str = ""           # 日志文件路径
    
    # 进度信息
    progress: float = 0.0       # 进度 0-100
    speed: str = ""             # 处理速度
    eta: str = ""               # 预计剩余时间
    currentStep: str = ""       # 当前步骤
    totalSteps: int = 1         # 总步骤数
    currentStepIndex: int = 0   # 当前步骤索引
    
    # 文件信息
    fileSize: int = 0           # 文件大小（字节）
    duration: float = 0.0       # 时长（秒，音视频文件）
    
    # 时间信息
    createTime: datetime = field(default_factory=datetime.now)
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None
    updateTime: Optional[datetime] = None
    
    # 错误信息
    errorMsg: str = ""
    errorCode: str = ""
    retryCount: int = 0         # 重试次数
    maxRetry: int = 3           # 最大重试次数
    
    # 任务特定配置（存储为JSON字符串）
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 标签和分类
    tags: List[str] = field(default_factory=list)
    category: str = ""
    
    # 优先级
    priority: int = 0           # 优先级（数字越大优先级越高）
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        if isinstance(self.type, str) and hasattr(TaskType, self.type.upper()):
            pass  # 保持字符串格式
        if isinstance(self.createTime, str):
            self.createTime = datetime.fromisoformat(self.createTime)
        if isinstance(self.startTime, str):
            self.startTime = datetime.fromisoformat(self.startTime)
        if isinstance(self.endTime, str):
            self.endTime = datetime.fromisoformat(self.endTime)
        if isinstance(self.updateTime, str):
            self.updateTime = datetime.fromisoformat(self.updateTime)
    
    @property
    def flieName(self):
        """兼容拼写错误"""
        return self.fileName
    
    @property
    def source(self) -> str:
        """获取任务来源（用于下载任务）"""
        return self.metadata.get('source', '')
    
    @source.setter
    def source(self, value: str):
        """设置任务来源"""
        self.metadata['source'] = value
    
    @property
    def isDownloadTask(self) -> bool:
        """是否为下载任务"""
        return self.type == TaskType.DOWNLOAD.value
    
    @property
    def isTranslateTask(self) -> bool:
        """是否为翻译任务"""
        return self.type == TaskType.TRANSLATE.value
    
    @property
    def isTranscribeTask(self) -> bool:
        """是否为听写任务"""
        return self.type == TaskType.TRANSCRIBE.value
    
    @property
    def isVocalSeparateTask(self) -> bool:
        """是否为人声分离任务"""
        return self.type == TaskType.VOCAL_SEPARATE.value
    
    @property
    def isMediaSplitTask(self) -> bool:
        """是否为音视频切分任务"""
        return self.type == TaskType.MEDIA_SPLIT.value
    
    @property
    def isRunning(self) -> bool:
        """是否正在运行"""
        return self.status == TaskStatus.RUNNING
    
    @property
    def isFinished(self) -> bool:
        """是否已完成"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def isSuccessful(self) -> bool:
        """是否成功"""
        return self.status == TaskStatus.SUCCESS
    
    @property
    def isFailed(self) -> bool:
        """是否失败"""
        return self.status == TaskStatus.FAILED
    
    def canRetry(self) -> bool:
        """是否可以重试"""
        return self.isFailed and self.retryCount < self.maxRetry
    
    def getElapsedTime(self) -> Optional[float]:
        """获取已用时间（秒）"""
        if not self.startTime:
            return None
        end = self.endTime or datetime.now()
        return (end - self.startTime).total_seconds()
    
    def getProgressPercentage(self) -> str:
        """获取进度百分比字符串"""
        return f"{self.progress:.1f}%"
    
    def toDict(self) -> Dict[str, Any]:
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'name': self.name,
            'fileName': self.fileName,
            'description': self.description,
            'url': self.url,
            'inputPath': self.inputPath,
            'outputPath': self.outputPath,
            'outputPaths': json.dumps(self.outputPaths),
            'logFile': self.logFile,
            'progress': self.progress,
            'speed': self.speed,
            'eta': self.eta,
            'currentStep': self.currentStep,
            'totalSteps': self.totalSteps,
            'currentStepIndex': self.currentStepIndex,
            'fileSize': self.fileSize,
            'duration': self.duration,
            'createTime': self.createTime.isoformat() if self.createTime else None,
            'startTime': self.startTime.isoformat() if self.startTime else None,
            'endTime': self.endTime.isoformat() if self.endTime else None,
            'updateTime': self.updateTime.isoformat() if self.updateTime else None,
            'errorMsg': self.errorMsg,
            'errorCode': self.errorCode,
            'retryCount': self.retryCount,
            'maxRetry': self.maxRetry,
            'config': json.dumps(self.config),
            'metadata': json.dumps(self.metadata),
            'tags': json.dumps(self.tags),
            'category': self.category,
            'priority': self.priority,
        }