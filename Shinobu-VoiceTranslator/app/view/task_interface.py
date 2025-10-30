# coding:utf-8
import os
from typing import Dict, List
from PySide6.QtCore import Qt, Signal, Property, QSize, QDateTime
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QGraphicsDropShadowEffect

from qfluentwidgets import (Action, FluentIcon, SegmentedWidget, InfoBar, InfoBarPosition,
                            BodyLabel, PlainTextEdit, PushButton, Flyout, CommandBarView, isDarkTheme, setFont)

from ..common.icon import Logo, Icon
from ..components.interface import Interface
from ..common.database.entity.task import Task, TaskStatus
from ..components.task_card import (ProgressingTaskCard, Task, SuccessTaskCard, TaskCardBase, FailedTaskCard,
                                     DeleteTaskDialog)
from ..common.signal_bus import signalBus
from ..services.downloadservice.download_service import downloadService
from ..services.translation_service import translationService  
from ..services.transcription_service import transcriptionService
from ..common.database import sqlRequest
from ..components.empty_status_widget import EmptyStatusWidget
from ..common.setting import LOG_PATH

from PySide6.QtCore import QTimer




class TaskInterface(Interface):
    """任务管理界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("任务管理"))

        self.pivot = SegmentedWidget()                  # 分页标签控件
        self.stackedWidget = TaskStackedWidget()        # 堆叠窗口 
        self.progressingTaskView = ProgressingTaskView(self)    # 任务进行中视图
        self.successTaskView = SuccessTaskView(self)            # 已完成视图
        self.failedTaskView = FailedTaskView(self)              # 失败视图
        self.logTaskView = LogTaskView(self)                    # 日志视图
        self.emptyStatusWidget = EmptyStatusWidget(
            Logo.SMILEFACE, 
            self.tr("任务列表为空"), self)                      # 空状态提示
        self.SERVICE_MAP = {
            "download":{
                "service": downloadService,
                "unavailable_msg": self.tr("下载服务不可用，请检查设置"),
                "log_viewer": downloadService.showLog,
            },
            "translate": {
                "service": translationService,
                "unavailable_msg": self.tr("翻译服务不可用，请检查设置"),
                "log_viewer": translationService.showLog,
            },
            "transcribe": {
                "service": transcriptionService,
                "unavailable_msg": self.tr("听写服务不可用，请检查设置"),
                "log_viewer": transcriptionService.showLog,
            }
        }
        
        self.__initWidgets()
        
    def __initWidgets(self):
        self.setViewportMargins(0, 140, 0, 10)

        # 添加分页标签
        self.pivot.addItem("progressing", self.tr("正在进行"), icon=FluentIcon.SYNC)
        self.pivot.addItem("finished", self.tr("任务完成"), icon=FluentIcon.COMPLETED)
        self.pivot.addItem("failed", self.tr("任务失败"), icon=FluentIcon.INFO)
        self.pivot.addItem("log", self.tr("运行日志"), icon=FluentIcon.DOCUMENT)
        self.pivot.setCurrentItem("progressing")   # 默认进行中

        self.emptyStatusWidget.setMinimumWidth(200)

        # 将视图添加到堆叠窗口
        self.stackedWidget.addWidget(self.progressingTaskView)
        self.stackedWidget.addWidget(self.successTaskView)
        self.stackedWidget.addWidget(self.failedTaskView)
        self.stackedWidget.addWidget(self.logTaskView)

        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.viewLayout.addWidget(self.stackedWidget)

    def _onTaskCreated(self, task: Task):
        self.progressingTaskView.addTask(task)              # 添加到进行中视图
        if self.stackedWidget.currentIndex() == 0:          # 如果当前显示在进行中视图，便隐藏空状态
            self.emptyStatusWidget.hide()


    def _Finished(self, task: Task, isSuccess, errorMsg):
        self.progressingTaskView.removeTask(task)           # 从进行中视图移除

        if isSuccess:
            self.successTaskView.addTask(task)              # 添加到已完成视图
        else:
            self.failedTaskView.addTask(task)               # 添加到失败视图

        self._updateEmptyStatus()                           # 更新空状态

    def _connectSignalToSlot(self):
        # 分页切换信号
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k)))
        self.stackedWidget.currentChanged.connect(self._onCurrentWidgetChanged)

        # 任务数量变化信号
        self.progressingTaskView.cardCountChanged.connect(self._updateEmptyStatus)
        self.successTaskView.cardCountChanged.connect(self._updateEmptyStatus)
        self.failedTaskView.cardCountChanged.connect(self._updateEmptyStatus)

        signalBus.restartTask.connect(self._restart)

        # 服务信号

    def _onCurrentWidgetChanged(self, index: int):
        # 日志视图不显示 "任务列表为空" 的提示
        if self.stackedWidget.widget(index) is self.logTaskView:
            self.emptyStatusWidget.hide()
        else:
            self._updateEmptyStatus()

    def _restart(self, task: Task):
        # 判断任务类型并获取服务信息
        service_info = self._get_service_info(task)

        # 如果任务类型未知或服务未在地图中定义
        if not service_info:
            InfoBar.error(
                self.tr("Task failed"),
                self.tr("未知服务类型：{0}").format(getattr(task, 'type', 'N/A')),
                duration=-1,
                position=InfoBarPosition.BOTTOM,
                parent=self
            )
            return
        
        service = service_info["service"]

        # 判断该服务是否可用
        if not service.isAvailable():
            InfoBar.error(
                self.tr("Task failed"),
                service_info["unavailable_msg"],  # 使用映射表中的特定错误消息
                duration=-1,
                position=InfoBarPosition.BOTTOM,
                parent=self
            )
            return
        
        # 重启任务前先删除旧视图
        if task.status == TaskStatus.SUCCESS:
            self.successTaskView.removeTask(task)
        elif task.status == TaskStatus.FAILED:
            self.failedTaskView.removeTask(task)
        
        # 重新启动任务
        success = service.restart(task)  
        button = PushButton(self.tr('Check'))

        if success:
            w = InfoBar.success(
                self.tr("Task created"),
                self.tr("任务已重新开始，请在“正在进行”中查看"), # 使用更通用的提示
                duration=3000,
                position=InfoBarPosition.BOTTOM,
                parent=self
            )
            # 成功后统一跳转到任务界面
            button.clicked.connect(signalBus.switchToTaskInterfaceSig)
        
        
        else:
            w = InfoBar.error(
                self.tr("Task failed"),
                self.tr("任务执行错误，请点击查看错误日志"),
                duration=-1,
                position=InfoBarPosition.BOTTOM,
                parent=self
            )
            # 失败后连接到该服务特定的日志查看器
            button.clicked.connect(service_info["log_viewer"])

        
        w.widgetLayout.insertSpacing(0, 10)
        w.addWidget(button)


    def _get_service_info(self, task: Task) -> dict | None:
        # 根据任务类型从映射表中获取服务信息
        task_type = getattr(task, 'type', None) 
        return self.SERVICE_MAP.get(task_type)
    
    def _updateEmptyStatus(self):
        # 确保当前 widget 不是 None
        current_widget = self.stackedWidget.currentWidget()
        if not current_widget or current_widget is self.logTaskView:
            self.emptyStatusWidget.hide()
            return

        # 确保 current_widget 有 count 方法
        if hasattr(current_widget, 'count'):
            visible = current_widget.count() == 0
            self.emptyStatusWidget.setVisible(visible)
        else:
            self.emptyStatusWidget.hide()


    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.emptyStatusWidget.adjustSize()
        w, h = self.emptyStatusWidget.width(), self.emptyStatusWidget.height()
        y = self.height() // 2 - h //2
        self.emptyStatusWidget.move(int(self.width()/2 - w/2), y)   # 居中显示
    
class TaskStackedWidget(QStackedWidget):
    def sizeHint(self):
        return self.currentWidget().sizeHint()  # 返回当前窗口的尺寸提示
    
    def minimumSizeHint(self):
        return self.currentWidget().minimumSizeHint()  # 返回当前窗口的最小尺寸提示


class TaskCardView(QWidget):
    """任务视图"""
    cardCountChanged = Signal(int) # 卡片数量变化信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cards = []     # 卡片列表
        self.selectionCount = 0  # 选中数量
        self.isSelectionMode = False  # 是否处于选择模式
        self.commandView = TaskCommandBarView(self.window())  # 命令栏
        self.cardMap = {}   # 任务ID到卡片的映射

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)
        self._connectSignalToSlot()  # 连接信号

    def createCard(self, task: Task) -> TaskCardBase:
        raise NotImplementedError

    def addTask(self, task: Task) -> TaskCardBase:
        card = self.createCard(task)                            # 创建卡片
        card.deleted.connect(self.removeTask)                   # 连接删除信号
        card.checkedChanged.connect(self._onCardCheckedChanged) # 连接选中状态变化信号

        if self.isSelectionMode:
            card.setSelectionMode(True) # 处于选择模式时，设置卡片选择模式

        self.vBoxLayout.insertWidget(0, card, 0, Qt.AlignmentFlag.AlignTop)     # 添加到顶部
        self.cards.insert(0, card)
        self.cardMap[task.id] = card    # 添加映射

        # 添加缺失的信号发送
        self.cardCountChanged.emit(self.count())
        return card

    def removeTask(self, task: Task):
        if task.id not in self.cardMap:
            return

        card = self.cardMap.pop(task.id)    # 从映射中删除
        self.cards.remove(card)             # 从列表删除
        self.vBoxLayout.removeWidget(card)  # 从布局中删除

        if card.isSelectionMode:
            self._onCardCheckedChanged(False)   # 更新选中计数

        card.hide()
        card.deleteLater()      # 释放内存

        self.cardCountChanged.emit(self.count())    # 发出数量变化信号

    def findCard(self, task: Task):
        return self.cardMap.get(task.id)

    def count(self):
        return len(self.cards)

    def _onCardCheckedChanged(self, checked: bool):
        if checked:
            self.selectionCount += 1
            self.setSelectionMode(True)
        else:
            self.selectionCount -= 1
            if self.selectionCount == 0:
                self.setSelectionMode(False)

    def setSelectionMode(self, enter: bool):
        if self.isSelectionMode == enter:
            return

        self.isSelectionMode = enter

        for card in self.cards:
            card.setSelectionMode(enter)

        if enter:
            self.commandView.setVisible(True)
            self.commandView.raise_()
        else:
            self.commandView.setVisible(False)
            self.selectionCount = 0

    def resizeEvent(self, event):
        super().resizeEvent(event)
        x = self.window().width() // 2 - self.commandView.width() // 2
        y = self.window().height() - self.commandView.sizeHint().height() - 20
        self.commandView.move(x, y)

    def selectAll(self):
        for card in self.cards:
            card.setChecked(True)

    def _removeSelectedTasks(self):
        w = DeleteTaskDialog(self.window(), deleteOnClose=False)
        w.contentLabel.setText(self.tr("Are you sure to delete these selected tasks?"))
        w.deleteFileCheckBox.setChecked(False)

        if w.exec():
            for card in self.cards.copy():
                if card.isChecked():
                    card.removeTask(w.deleteFileCheckBox.isChecked())

        w.deleteLater()

    def _restartSelectedTasks(self):
        for card in self.cards:
            if card.isChecked():
                # 发射全局信号，由 TaskInterface 的 _restart 方法统一处理
                signalBus.restartTask.emit(card.task)
        self.setSelectionMode(False) # 重启后退出选择模式


    def _connectSignalToSlot(self):
        self.commandView.restartAction.triggered.connect(self._restartSelectedTasks)
        self.commandView.deleteAction.triggered.connect(self._removeSelectedTasks)
        self.commandView.selectAllAction.triggered.connect(self.selectAll)
        self.commandView.cancelAction.triggered.connect(lambda: self.setSelectionMode(False))

class ProgressingTaskView(TaskCardView):
    """任务进行中视图"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("progressing")
        self.commandView.bar.commandButtons[0].hide()

    def createCard(self, task: Task):
        return ProgressingTaskCard(task)

class SuccessTaskView(TaskCardView):
    """任务完成视图"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("finished")
        
        # 从数据库加载已完成任务
        sqlRequest(
            "taskService",
            "listBy",
            self._loadTasks,
            status=TaskStatus.SUCCESS,
            orderBy="createTime",
            asc=True
        )

    def _loadTasks(self, tasks: List[Task]):
        if not tasks:
            return
            
        for task in tasks:
            self.addTask(task)  # 添加任务卡片
            
        self.cardCountChanged.emit(self.count())

    def createCard(self, task: Task):
        return SuccessTaskCard(task, self)

class FailedTaskView(TaskCardView):
    """任务失败视图"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("failed")
        
        # 从数据库加载失败任务
        sqlRequest(
            "taskService",
            "listBy",
            self._loadTasks,
            status=TaskStatus.FAILED,
            orderBy="createTime",
            asc=True
        )

    def _loadTasks(self, tasks: List[Task]):
        if not tasks:
            return
            
        for task in tasks:
            self.addTask(task)
            
        self.cardCountChanged.emit(self.count())

    def createCard(self, task: Task):
        return FailedTaskCard(task, self)

class LogTaskView(QWidget):
    """日志视图"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("log")

        self.titleLabel = BodyLabel(self.tr("服务运行日志"), self)
        self.logContent = PlainTextEdit(self)
        self.clearButton = PushButton(self.tr("清空日志"), self)

        # 日志文件读取相关
        self.timer = None
        self.last_read_position = 0
        self.file_not_found_message_shown = False
        self.LOG_PATH = LOG_PATH  # 从 setting.py 导入的路径

        self.__initWidgets()
        self.__initLayout()
        self._connectSignalToSlot()
        self._setup_timer()  # 初始化定时器

    def __initWidgets(self):
        self.logContent.setReadOnly(True)
        setFont(self.logContent, 15)
        self.titleLabel.setObjectName("logTitleLabel")

    def __initLayout(self):
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()

        button_layout.addWidget(self.titleLabel)
        button_layout.addStretch(1)
        button_layout.addWidget(self.clearButton)

        layout.addLayout(button_layout)
        layout.addWidget(self.logContent)
        self.setLayout(layout)

    def _connectSignalToSlot(self):
        self.clearButton.clicked.connect(self._clear_log_file)

    def _setup_timer(self):
        """设置定时器，每秒读取一次日志文件"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_log_file)
        self.timer.start(1000)  # 每秒读取一次
        
        # 初始读取位置
        self.last_read_position = 0
        self.file_not_found_message_shown = False
        
        # 立即读取一次日志
        self._read_log_file()

    def _read_log_file(self):
        """读取日志文件并更新显示（增量读取）"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.LOG_PATH):
                if not self.file_not_found_message_shown:
                    timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                    self.logContent.setPlainText(
                        f"[{timestamp}] 错误: 日志文件 '{self.LOG_PATH}' 未找到。\n"
                        f"正在等待文件创建...\n"
                    )
                    self.file_not_found_message_shown = True
                self.last_read_position = 0  # 如果文件消失了，重置读取位置
                return

            # 如果文件之前未找到但现在找到了
            if self.file_not_found_message_shown:
                self.logContent.clear()  # 清除之前的错误信息
                self.file_not_found_message_shown = False
                self.last_read_position = 0  # 从头开始读

            with open(self.LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                # 检查文件是否被截断或替换 (例如日志轮转)
                current_file_size = f.seek(0, os.SEEK_END)
                
                if current_file_size < self.last_read_position:
                    # 文件变小了，意味着文件被截断或替换了
                    timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                    self.logContent.appendPlainText(
                        f"\n[{timestamp}] 检测到日志文件截断或轮转。从头开始读取...\n"
                    )
                    self.last_read_position = 0

                # 从上次读取位置开始读取
                f.seek(self.last_read_position)
                new_content = f.read()
                
                if new_content:
                    # 移除末尾的换行符，appendPlainText 会自动添加
                    self.logContent.appendPlainText(new_content.rstrip())
                    
                    # 自动滚动到底部
                    scrollbar = self.logContent.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())

                # 更新下次读取的起始位置
                self.last_read_position = f.tell()

        except FileNotFoundError:
            if not self.file_not_found_message_shown:
                timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                self.logContent.setPlainText(
                    f"[{timestamp}] 错误: 日志文件 '{self.LOG_PATH}' 再次检查时未找到。\n"
                )
                self.file_not_found_message_shown = True
            self.last_read_position = 0
            
        except IOError as e:
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            self.logContent.appendPlainText(f"[{timestamp}] 读取日志文件IO错误: {e}\n")
            
        except Exception as e:
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            self.logContent.appendPlainText(f"[{timestamp}] 读取日志文件时发生未知错误: {e}\n")

    def _clear_log_file(self):
        """清空日志文件和显示"""
        try:
            # 清空显示
            self.logContent.clear()
            
            # 清空日志文件
            if os.path.exists(self.LOG_PATH):
                with open(self.LOG_PATH, 'w', encoding='utf-8') as f:
                    timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                    f.write(f"[{timestamp}] 日志已清空\n")
                
                # 重置读取位置
                self.last_read_position = 0
                
                # 立即读取新内容
                self._read_log_file()
        except Exception as e:
            print(f"清空日志文件时出错: {e}")

    def showEvent(self, event):
        """当视图显示时，确保定时器运行并立即读取最新日志"""
        super().showEvent(event)
        if self.timer and not self.timer.isActive():
            self.timer.start(1000)
        self._read_log_file()

    def hideEvent(self, event):
        """当视图隐藏时，可以选择停止定时器以节省资源"""
        super().hideEvent(event)
        # 可选：停止定时器以节省资源
        # if self.timer:
        #     self.timer.stop()

    def closeEvent(self, event):
        """确保在关闭窗口时停止定时器"""
        if self.timer:
            self.timer.stop()
        event.accept()


class TaskCommandBarView(CommandBarView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 定义操作
        self.restartAction = Action(FluentIcon.UPDATE, self.tr("Restart"), self)
        self.deleteAction = Action(FluentIcon.DELETE, self.tr("Delete"), self)
        self.selectAllAction = Action(Icon.SELECT, self.tr("Select All"), self)
        self.cancelAction = Action(FluentIcon.CLEAR_SELECTION, self.tr("Cancel"), self)

        # 设置样式
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(18, 18))
        
        # 添加操作
        self.addActions([self.restartAction, self.deleteAction])
        self.addSeparator()
        self.addActions([self.selectAllAction, self.cancelAction])
        self.resizeToSuitableWidth()
        self.setShadowEffect()  # 设置阴影效果

    def setShadowEffect(self, blurRadius=35, offset=(0, 8)):
        """ add shadow to dialog """
        color = QColor(0, 0, 0, 80 if isDarkTheme() else 30)  # 根据主题调整颜色
        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.setGraphicsEffect(None)
        self.setGraphicsEffect(self.shadowEffect)

