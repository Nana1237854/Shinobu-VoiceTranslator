# coding: utf-8
from PySide6.QtCore import QUrl, QSize
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QApplication

from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen
from qfluentwidgets import FluentIcon as FIF


from .setting_interface import SettingInterface
from .download_interface import DownloadInterface
from .task_interface import TaskInterface


from ..common.config import cfg
from ..common.icon import Logo, Icon
from ..common.signal_bus import signalBus
from ..common import resource


class MainWindow(MSFluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # TODO: create sub interface
        # self.homeInterface = HomeInterface(self)
        self.downloadInterface = DownloadInterface(self)
        self.settingInterface = SettingInterface(self)
        self.taskInterface = TaskInterface(self)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)

    def initNavigation(self):
        # self.navigationInterface.setAcrylicEnabled(True)

        # TODO: add navigation items
        # self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))

        # add custom widget to bottom
        self.addSubInterface(
            self.downloadInterface, FIF.DOWNLOAD, self.tr('下载设置'), isTransparent=True)
        self.addSubInterface(
            self.taskInterface, Icon.TASK, self.tr('任务设置'), Icon.CLOUD_DOWNLOAD, NavigationItemPosition.BOTTOM)
        self.addSubInterface(
            self.settingInterface, Icon.SETTINGS, self.tr('Settings'), Icon.SETTINGS_FILLED, NavigationItemPosition.BOTTOM)
        
        
        self.splashScreen.finish()

    def initWindow(self):
        self.resize(960, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(':/app/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')

        self.setCustomBackgroundColor(QColor(240, 244, 249), QColor(32, 32, 32))
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())
    
    def closeEvent(self, e):
        """窗口关闭事件 - 清理资源"""
        # 清理下载服务的工作线程
        try:
            from ..services.downloadservice.download_service import downloadService
            downloadService.cleanup()
        except Exception as ex:
            print(f"清理下载服务失败: {ex}")
        
        # 清理数据库服务的工作线程
        try:
            from ..common.database import getDatabaseService
            db = getDatabaseService()
            if hasattr(db, 'cleanup'):
                db.cleanup()
        except Exception as ex:
            print(f"清理数据库服务失败: {ex}")
        
        super().closeEvent(e)