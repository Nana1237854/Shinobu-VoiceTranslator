# 线程管理优化文档

## 优化日期
2025-01-XX

## 问题描述

程序退出时出现警告：
```
QThread: Destroyed while thread '' is still running
```

这表明在应用程序关闭时，某些后台线程还在运行就被销毁了，导致线程没有正确清理。

## 问题根源

1. **数据库异步查询线程** (`AsyncDatabaseWorker`) 在程序退出时没有被正确停止
2. **下载工作线程** (`DownloadWorker`) 在窗口关闭时没有被清理
3. 主窗口缺少 `closeEvent` 方法来处理退出时的资源清理

## 优化方案

### 1. 主窗口添加 closeEvent 方法

**文件**: `app/view/main_window.py`

**修改**:
```python
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
```

**作用**: 在窗口关闭时，自动调用所有服务的 cleanup 方法清理线程。

### 2. 数据库服务优化

**文件**: `app/common/database/database_service.py`

#### 2.1 添加线程跟踪

```python
class DatabaseService(QObject):
    def __init__(self, db_path: str = "data/tasks.db"):
        super().__init__()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_workers = []  # 跟踪活动的工作线程
        self._init_database()
```

#### 2.2 改进 AsyncDatabaseWorker

```python
class AsyncDatabaseWorker(QThread):
    def __init__(self, db_service: DatabaseService, method_name: str, *args, **kwargs):
        super().__init__()
        self.db_service = db_service
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self._is_running = True  # 添加运行标志
    
    def run(self):
        """执行数据库操作"""
        try:
            if not self._is_running:
                return
            method = getattr(self.db_service, self.method_name)
            result = method(*self.args, **self.kwargs)
            if self._is_running:
                self.finished.emit(result)
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))
    
    def stop(self):
        """停止工作线程"""
        self._is_running = False
```

#### 2.3 添加 cleanup 方法

```python
def cleanup(self):
    """清理所有活动的工作线程"""
    for worker in self._active_workers[:]:
        if worker and worker.isRunning():
            worker.stop()
            worker.wait(1000)  # 等待最多1秒
            if worker.isRunning():
                worker.terminate()  # 强制终止
        self._active_workers.remove(worker)
    self._active_workers.clear()
```

#### 2.4 改进 sqlRequest 函数

```python
def sqlRequest(service_name: str, method_name: str, callback: Callable, *args, **kwargs):
    if service_name == "taskService":
        db = getDatabaseService()
        # ... 省略方法映射部分 ...
        
        worker = AsyncDatabaseWorker(db, actual_method, *args, **kwargs)
        if callback:
            worker.finished.connect(callback)
        
        # 跟踪工作线程
        db._active_workers.append(worker)
        
        # 完成后从列表中移除
        def on_finished(result):
            if worker in db._active_workers:
                db._active_workers.remove(worker)
        
        def on_error(error):
            if worker in db._active_workers:
                db._active_workers.remove(worker)
        
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        worker.start()
        return worker
```

### 3. 下载服务优化

**文件**: `app/services/downloadservice/base_service.py`

#### 3.1 改进 cancel 方法

```python
def cancel(self, task: Task) -> bool:
    """取消任务"""
    if task.id in self.workers:
        worker = self.workers[task.id]
        worker.cancel()
        worker.wait(3000)  # 等待最多3秒
        if worker.isRunning():
            worker.terminate()  # 强制终止
        del self.workers[task.id]
        
        task.status = TaskStatus.CANCELLED
        self.db.save_task(task)
        return True
    else:
        return False
```

#### 3.2 添加 cleanup 方法

```python
def cleanup(self):
    """清理所有工作线程"""
    for task_id, worker in list(self.workers.items()):
        if worker and worker.isRunning():
            worker.cancel()
            worker.wait(1000)  # 等待最多1秒
            if worker.isRunning():
                worker.terminate()  # 强制终止
    self.workers.clear()
```

### 4. 统一下载服务优化

**文件**: `app/services/downloadservice/download_service.py`

```python
def cleanup(self):
    """清理所有子服务的工作线程"""
    self.bilibili_service.cleanup()
    self.youtube_service.cleanup()
    super().cleanup()
```

## 优化效果

### 优化前
- ❌ 退出时出现线程警告
- ❌ 线程没有正确清理
- ❌ 可能导致资源泄漏

### 优化后
- ✅ 程序退出时自动清理所有线程
- ✅ 线程优雅地停止（先等待，后强制终止）
- ✅ 没有警告信息
- ✅ 资源正确释放

## 线程清理流程

```
窗口关闭
    ↓
closeEvent 触发
    ↓
调用 downloadService.cleanup()
    ├─ bilibili_service.cleanup()
    │   └─ 清理所有下载线程
    └─ youtube_service.cleanup()
        └─ 清理所有下载线程
    ↓
调用 getDatabaseService().cleanup()
    └─ 清理所有数据库查询线程
    ↓
程序正常退出
```

## 线程停止策略

1. **优雅停止** (1-3秒)
   - 设置停止标志
   - 等待线程自然结束

2. **强制终止** (超时后)
   - 如果线程在超时后仍在运行
   - 调用 `terminate()` 强制结束

3. **资源清理**
   - 从跟踪列表中移除
   - 释放相关资源

## 测试验证

### 测试步骤
1. 启动程序
2. 创建一些下载任务
3. 执行数据库查询
4. 关闭窗口
5. 查看控制台输出

### 预期结果
- ✅ 无线程警告
- ✅ 程序正常退出
- ✅ 无内存泄漏

## 注意事项

1. **超时时间**: 根据实际情况调整 `wait()` 的超时时间
2. **强制终止**: 仅在超时后使用 `terminate()`，避免数据损坏
3. **信号连接**: 确保线程完成时从跟踪列表中移除
4. **异常处理**: 添加 try-except 防止清理过程中的错误影响程序退出

## 未来改进

1. ✨ 添加进度指示器，显示线程清理进度
2. ✨ 实现更智能的超时策略
3. ✨ 添加线程状态监控和日志
4. ✨ 考虑使用线程池管理

## 相关文件

- `app/view/main_window.py` - 主窗口，添加 closeEvent
- `app/common/database/database_service.py` - 数据库服务，线程管理
- `app/services/downloadservice/base_service.py` - 下载服务基类
- `app/services/downloadservice/download_service.py` - 统一下载服务

