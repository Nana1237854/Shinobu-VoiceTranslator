# coding:utf-8
"""日志重定向系统 - 将标准输出/错误同时输出到控制台和文件"""
import sys
import os
from pathlib import Path
from datetime import datetime


class TeeOutput:
    """同时输出到文件和原始输出流的 Tee 类"""
    
    def __init__(self, file_path: Path, original_stream, mode='a'):
        self.file_path = file_path
        self.original_stream = original_stream
        self.file = None
        self.mode = mode
        self._open_file()
    
    def _open_file(self):
        """打开文件用于写入"""
        try:
            # 确保目录存在
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            # buffering=1 表示行缓冲，每写入一行就刷新
            self.file = open(self.file_path, self.mode, encoding='utf-8', buffering=1)
        except Exception as e:
            if self.original_stream:
                print(f"无法打开日志文件 {self.file_path}: {e}", file=self.original_stream)
    
    def write(self, message):
        """写入消息到文件和原始流"""
        # 写入原始流（控制台）
        if self.original_stream:
            try:
                self.original_stream.write(message)
                self.original_stream.flush()
            except:
                pass
        
        # 写入文件
        if self.file and not self.file.closed:
            try:
                # 如果 message 是 bytes，尝试解码
                if isinstance(message, bytes):
                    # 优先尝试 UTF-8，失败则使用 GBK，最后使用 replace 模式
                    try:
                        message = message.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            message = message.decode('gbk')
                        except UnicodeDecodeError:
                            message = message.decode('utf-8', errors='replace')
                
                self.file.write(message)
                self.file.flush()  # 立即刷新到磁盘
            except Exception as e:
                # 如果写入失败，尝试用 replace 模式
                try:
                    if isinstance(message, str):
                        self.file.write(message.encode('utf-8', errors='replace').decode('utf-8'))
                        self.file.flush()
                except:
                    pass
    
    def flush(self):
        """刷新缓冲区"""
        if self.original_stream:
            try:
                self.original_stream.flush()
            except:
                pass
        if self.file and not self.file.closed:
            try:
                self.file.flush()
            except:
                pass
    
    def close(self):
        """关闭文件"""
        if self.file and not self.file.closed:
            try:
                self.file.close()
            except:
                pass
    
    def fileno(self):
        """返回文件描述符（如果有），用于子进程继承"""
        if self.file and not self.file.closed:
            return self.file.fileno()
        return None


class LogRedirector:
    """日志重定向管理器（单例模式）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.log_path = None
        self.stdout_redirector = None
        self.stderr_redirector = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def setup(self, log_path: Path = None):
        """设置日志重定向
        
        Args:
            log_path: 日志文件路径，默认为项目根目录下的 log.txt
        """
        if log_path is None:
            # 使用项目根目录的 log.txt
            log_path = Path('log.txt').absolute()
        
        self.log_path = Path(log_path)
        
        # 创建日志文件并写入启动信息
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入启动分隔符
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"应用启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
        
        # 重定向标准输出和标准错误（同时输出到控制台和文件）
        self.stdout_redirector = TeeOutput(self.log_path, self.original_stdout, mode='a')
        self.stderr_redirector = TeeOutput(self.log_path, self.original_stderr, mode='a')
        
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stderr_redirector
        
        print(f"[日志系统] 日志重定向已设置: {self.log_path}")
        print(f"[日志系统] 所有输出将同时显示在控制台和日志文件中\n")
    
    def get_log_path(self) -> Path:
        """获取日志文件路径"""
        return self.log_path
    
    def restore(self):
        """恢复原始的标准输出和标准错误"""
        if self.stdout_redirector:
            self.stdout_redirector.close()
        if self.stderr_redirector:
            self.stderr_redirector.close()
        
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        if self.original_stdout:
            print(f"日志系统已恢复到原始输出", file=self.original_stdout)


# 全局实例
logRedirector = LogRedirector()

