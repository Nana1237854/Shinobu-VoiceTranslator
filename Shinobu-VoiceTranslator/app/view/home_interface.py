from PySide6.QtCore import Qt, QFileInfo
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton
from pathlib import Path
from typing import List

from ..components.config_card import DownloadConfigCard

class HomeInterface(ScrollArea):
    """首页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None 
