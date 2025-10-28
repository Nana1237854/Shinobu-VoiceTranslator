# coding:utf-8
import os
import sys
import platform
from datetime import datetime

from PySide6.QtCore import Qt, QTranslator # type: ignore
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.common.log_redirector import logRedirector
from app.view.main_window import MainWindow


# 设置环境变量，强制使用 UTF-8 编码（必须在任何子进程创建前）
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 在 Windows 下设置控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        # 设置控制台代码页为 UTF-8 (65001)
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

# 设置日志重定向（在创建QApplication之前）
logRedirector.setup()

# 输出系统信息
print("="*80)
print(f"应用名称: Shinobu VoiceTranslator")
print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"操作系统: {platform.system()} {platform.release()}")
print(f"Python版本: {platform.python_version()}")
print("="*80 + "\n")

# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

# create application
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

# internationalization
locale = cfg.get(cfg.language).value
translator = FluentTranslator(locale)
galleryTranslator = QTranslator()
galleryTranslator.load(locale, "app", ".", ":/app/i18n")

app.installTranslator(translator)
app.installTranslator(galleryTranslator)

# create main window
w = MainWindow()
w.show()

try:
    app.exec()
finally:
    # 应用退出时恢复输出并记录
    print("\n" + "="*80)
    print(f"应用退出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    logRedirector.restore()
