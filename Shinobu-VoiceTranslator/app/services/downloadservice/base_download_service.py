import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from PySide6.QtCore import Signal

from ...common.database.entity.task import Task, TaskStatus, TaskType
from ..base_service import BaseService
from ...common.database import getTaskService
from ...common.signal_bus import signalBus


class BaseDownloadService(BaseService):
    """下载服务基类"""
    taskCreated = Signal(Task)   # 任务创建信号
    taskFinished = Signal(Task, bool, str)   # 任务完成信号
    taskUpdated = Signal(Task)   # 任务更新信号
    logGenerated = Signal(str, str)   # 日志生成信号

    def __init__(self):
        super().__init__(TaskType.DOWNLOAD)
        
    def isAvailable(self) -> bool:
        """
        判断服务是否可用
        子类应该根据下载器的可用性来设置 self._available
        """
        return self._available

    def createTask(self, url: str, **kwargs) -> Optional[Task]:
        """
        创建下载任务
        
        Args:
            url: 下载链接
            **kwargs: 额外参数（如 proxy, output_dir 等）
            
        Returns:
            创建的任务对象，如果创建失败返回 None
            
        Note:
            子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现 createTask 方法")

    def start(self, task: Task) -> bool:
        """
        开始下载任务
        
        Args:
            task: 要执行的任务对象
            
        Returns:
            True 表示任务成功启动，False 表示启动失败
            
        Note:
            子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现 start 方法")
    
    # 以下是通用辅助方法
    
    def validateUrl(self, url: str) -> bool:
        """
        验证 URL 是否有效
        
        Args:
            url: 要验证的 URL
            
        Returns:
            True 表示 URL 有效，False 表示无效
        """
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        if not url:
            return False
        
        # 基本的 URL 格式检查
        return url.startswith(('http://', 'https://', 'BV'))
    
    def _createDownloadTask(self, task_func: Callable, task: Task) -> bool:
        """
        通用的下载任务创建逻辑（辅助方法）
        
        Args:
            task_func: 要在线程池中执行的下载函数
            task: 任务对象
            
        Returns:
            True 表示任务成功提交到线程池
            
        Note:
            这是一个内部辅助方法，子类可以选择使用它来简化代码
        """
        if task.id in self.futures:
            self._addLog("WARNING", f"任务已在运行: {task.fileName}")
            return False
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.startTime = datetime.now()
        self.db.save_task(task)
        self._emit_task_updated(task)
        
        # 使用 TaskExecutor 异步执行
        future = self.asyncRun(task_func)
        
        # 保存 Future 引用
        self.futures[task.id] = future
        
        return True
    
    def _handleDownloadSuccess(self, task: Task, output_path: str):
        """
        处理下载成功的通用逻辑
        
        Args:
            task: 任务对象
            output_path: 下载文件的路径
        """
        task.outputPath = output_path
        task.progress = 100.0
        self._onWorkerFinished(task, True, "下载完成")
    
    def _handleDownloadFailure(self, task: Task, error):
        """
        处理下载失败的通用逻辑
        
        Args:
            task: 任务对象
            error: 错误对象（FutureFailed 或其他异常）
        """
        # 从错误对象中提取错误消息
        if hasattr(error, 'exception'):
            error_msg = str(error.exception)
        else:
            error_msg = str(error)
        
        self._onWorkerFinished(task, False, error_msg)
    
    def getOutputPath(self, task: Task) -> Optional[Path]:
        """
        获取任务的输出路径
        
        Args:
            task: 任务对象
            
        Returns:
            输出文件的 Path 对象，如果不存在返回 None
        """
        if task.outputPath:
            output_path = Path(task.outputPath)
            if output_path.exists():
                return output_path
        return None
    
    def openOutputFolder(self, task: Task) -> bool:
        """
        打开任务输出文件所在的文件夹
        
        Args:
            task: 任务对象
            
        Returns:
            True 表示成功打开，False 表示失败
        """
        output_path = self.getOutputPath(task)
        if not output_path:
            self._addLog("WARNING", f"输出文件不存在: {task.fileName}")
            return False
        
        try:
            from ...common.utils import showInFolder
            showInFolder(str(output_path))
            return True
        except Exception as e:
            self._addLog("ERROR", f"打开文件夹失败: {e}")
            return False
    
    def deleteOutputFile(self, task: Task) -> bool:
        """
        删除任务的输出文件
        
        Args:
            task: 任务对象
            
        Returns:
            True 表示成功删除，False 表示失败
        """
        output_path = self.getOutputPath(task)
        if not output_path:
            self._addLog("WARNING", f"输出文件不存在: {task.fileName}")
            return False
        
        try:
            from ...common.utils import removeFile
            removeFile(str(output_path))
            task.outputPath = None
            self.db.save_task(task)
            self._addLog("INFO", f"已删除文件: {output_path.name}")
            return True
        except Exception as e:
            self._addLog("ERROR", f"删除文件失败: {e}")
            return False
