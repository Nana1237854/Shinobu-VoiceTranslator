# coding: utf-8
from enum import Enum

from qfluentwidgets import FluentIconBase, getIconColor, Theme, FluentIcon


class Icon(FluentIconBase, Enum):
    """自定义图标枚举"""

    # 设置相关图标（使用自定义SVG）
    SETTINGS = "Settings"
    SETTINGS_FILLED = "SettingsFilled"
    
    # 其他图标（直接使用FluentIcon的值）
    # 这些不需要自定义SVG文件
    TASK = "Task"
    CLOUD_DOWNLOAD = "CloudDownload"
    SELECT = "Select"

    def path(self, theme=Theme.AUTO):
        # 自定义SVG图标
        if self.value in ["Settings", "SettingsFilled"]:
            return f":/app/images/icons/{self.value}_{getIconColor(theme)}.svg"
        
        # 映射到FluentIcon
        icon_map = {
            "Task": FluentIcon.CHECKBOX,
            "CloudDownload": FluentIcon.CLOUD_DOWNLOAD,
            "Select": FluentIcon.ACCEPT,
        }
        
        if self.value in icon_map:
            return icon_map[self.value].path(theme)
        
        return ""


class Logo(FluentIconBase, Enum):
    """Logo图标枚举"""
    
    SMILEFACE = "SmileFace"
    EMPTY = "Empty"
    ERROR = "Error"
    SUCCESS = "Success"
    
    def path(self, theme=Theme.AUTO):
        # 映射到FluentIcon
        logo_map = {
            "SmileFace": FluentIcon.EMOJI_TAB_SYMBOLS,
            "Empty": FluentIcon.FOLDER,
            "Error": FluentIcon.CANCEL,
            "Success": FluentIcon.COMPLETED,
        }
        
        if self.value in logo_map:
            return logo_map[self.value].path(theme)
        
        return ""
