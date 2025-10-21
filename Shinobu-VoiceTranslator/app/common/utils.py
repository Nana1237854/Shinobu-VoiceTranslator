# coding:utf-8
import os
import subprocess
import sys
import re
from typing import Union
from pathlib import Path
from typing import Optional
from json import loads

from PySide6.QtCore import QFile, QUrl, QFileInfo, QDir, QProcess, QStandardPaths
from PySide6.QtGui import QDesktopServices


def removeFile(file_path: str) -> bool:
    """删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否成功删除
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def showInFolder(file_path: str) -> bool:
    """在文件管理器中显示文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否成功打开
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False
        
        if sys.platform == 'win32':
            # Windows
            subprocess.run(['explorer', '/select,', str(path.absolute())])
        elif sys.platform == 'darwin':
            # macOS
            subprocess.run(['open', '-R', str(path.absolute())])
        else:
            # Linux
            subprocess.run(['xdg-open', str(path.parent.absolute())])
        
        return True
    except Exception as e:
        print(f"打开文件夹失败: {e}")
        return False


def openUrl(url: str) -> bool:
    """在浏览器中打开URL或文件
    
    Args:
        url: URL或文件路径
        
    Returns:
        是否成功打开
    """
    try:
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"打开URL失败: {e}")
        return False


def formatFileSize(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def formatDuration(seconds: float) -> str:
    """格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的字符串 (HH:MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def runProcess(executable: Union[str, Path], args=None, timeout=5000, cwd=None) -> str:
    process = QProcess()

    if cwd:
        process.setWorkingDirectory(str(cwd))

    process.start(str(executable).replace("\\", "/"), args or [])
    process.waitForFinished(timeout)
    return process.readAllStandardOutput().toStdString()


def runDetachedProcess(executable: Union[str, Path], args=None, cwd=None):
    process = QProcess()

    if cwd:
        process.setWorkingDirectory(str(cwd))

    process.startDetached(str(executable).replace("\\", "/"), args or [])

def getSystemProxy():
    """ get system proxy """
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Internet Settings') as key:
                enabled, _ = winreg.QueryValueEx(key, 'ProxyEnable')

                if enabled:
                    return "http://" + winreg.QueryValueEx(key, 'ProxyServer')
        except:
            pass
    elif sys.platform == "darwin":
        s = os.popen('scutil --proxy').read()
        info = dict(re.findall('(?m)^\s+([A-Z]\w+)\s+:\s+(\S+)', s))

        if info.get('HTTPEnable') == '1':
            return f"http://{info['HTTPProxy']}:{info['HTTPPort']}"
        elif info.get('ProxyAutoConfigEnable') == '1':
            return info['ProxyAutoConfigURLString']

    return os.environ.get("http_proxy")
