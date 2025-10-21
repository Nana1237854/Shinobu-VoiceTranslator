# coding:utf-8
import json
import sqlite3
from pathlib import Path
from typing import List, Callable, Any, Optional, Dict
from datetime import datetime
from PySide6.QtCore import QObject, QThread, Signal

from .entity.task import Task, TaskStatus, TaskType


class DatabaseService(QObject):
    """数据库服务 - 管理任务数据持久化"""
    
    taskSaved = Signal(Task)        # 任务保存信号
    taskDeleted = Signal(str)       # 任务删除信号（任务ID）
    
    def __init__(self, db_path: str = "data/tasks.db"):
        super().__init__()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_workers = []  # 跟踪活动的工作线程
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                name TEXT,
                fileName TEXT,
                description TEXT,
                url TEXT,
                inputPath TEXT,
                outputPath TEXT,
                outputPaths TEXT,
                logFile TEXT,
                progress REAL DEFAULT 0,
                speed TEXT,
                eta TEXT,
                currentStep TEXT,
                totalSteps INTEGER DEFAULT 1,
                currentStepIndex INTEGER DEFAULT 0,
                fileSize INTEGER DEFAULT 0,
                duration REAL DEFAULT 0,
                createTime TEXT,
                startTime TEXT,
                endTime TEXT,
                updateTime TEXT,
                errorMsg TEXT,
                errorCode TEXT,
                retryCount INTEGER DEFAULT 0,
                maxRetry INTEGER DEFAULT 3,
                config TEXT,
                metadata TEXT,
                tags TEXT,
                category TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_type ON tasks(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_createTime ON tasks(createTime)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_priority ON tasks(priority)')
        
        # 创建统计视图
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS task_statistics AS
            SELECT 
                type,
                status,
                COUNT(*) as count,
                AVG(progress) as avg_progress
            FROM tasks
            GROUP BY type, status
        ''')
        
        conn.commit()
        conn.close()
    
    def save_task(self, task: Task) -> bool:
        """保存任务"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            task.updateTime = datetime.now()
            task_dict = task.toDict()
            
            # 构建SQL语句
            columns = ', '.join(task_dict.keys())
            placeholders = ', '.join(['?' for _ in task_dict])
            
            cursor.execute(f'''
                INSERT OR REPLACE INTO tasks ({columns}) VALUES ({placeholders})
            ''', tuple(task_dict.values()))
            
            conn.commit()
            conn.close()
            
            self.taskSaved.emit(task)
            return True
            
        except Exception as e:
            print(f"保存任务失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """根据ID获取单个任务"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return self._row_to_task(row, cursor.description)
            
        except Exception as e:
            print(f"获取任务失败: {e}")
            return None
    
    def list_all_tasks(self, orderBy: str = "createTime", asc: bool = False) -> List[Task]:
        """获取所有任务"""
        return self.list_tasks_by(orderBy=orderBy, asc=asc)
    
    def list_tasks_by(
        self, 
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        category: Optional[str] = None,
        orderBy: str = "createTime", 
        asc: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """按条件查询任务列表"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            query = 'SELECT * FROM tasks WHERE 1=1'
            params = []
            
            # 添加过滤条件
            if status:
                query += ' AND status = ?'
                params.append(status.value if isinstance(status, TaskStatus) else status)
            
            if task_type:
                query += ' AND type = ?'
                params.append(task_type.value if isinstance(task_type, TaskType) else task_type)
            
            if category:
                query += ' AND category = ?'
                params.append(category)
            
            # 排序
            order = 'ASC' if asc else 'DESC'
            query += f' ORDER BY {orderBy} {order}'
            
            # 分页
            if limit:
                query += f' LIMIT {limit} OFFSET {offset}'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            description = cursor.description
            conn.close()
            
            return [self._row_to_task(row, description) for row in rows]
            
        except Exception as e:
            print(f"查询任务列表失败: {e}")
            return []
    
    def search_tasks(
        self,
        keyword: str,
        search_fields: List[str] = None,
        **filters
    ) -> List[Task]:
        """搜索任务"""
        if search_fields is None:
            search_fields = ['name', 'fileName', 'description', 'url']
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 构建搜索条件
            search_conditions = ' OR '.join([f"{field} LIKE ?" for field in search_fields])
            query = f'SELECT * FROM tasks WHERE ({search_conditions})'
            params = [f'%{keyword}%' for _ in search_fields]
            
            # 添加额外过滤条件
            for key, value in filters.items():
                if value is not None:
                    query += f' AND {key} = ?'
                    params.append(value.value if hasattr(value, 'value') else value)
            
            query += ' ORDER BY createTime DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            description = cursor.description
            conn.close()
            
            return [self._row_to_task(row, description) for row in rows]
            
        except Exception as e:
            print(f"搜索任务失败: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected > 0:
                self.taskDeleted.emit(task_id)
                return True
            return False
            
        except Exception as e:
            print(f"删除任务失败: {e}")
            return False
    
    def delete_tasks_by_status(self, status: TaskStatus) -> int:
        """批量删除指定状态的任务"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE status = ?', (status.value,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected
            
        except Exception as e:
            print(f"批量删除任务失败: {e}")
            return 0
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            update_time = datetime.now().isoformat()
            cursor.execute(
                'UPDATE tasks SET status = ?, updateTime = ? WHERE id = ?',
                (status.value, update_time, task_id)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"更新任务状态失败: {e}")
            return False
    
    def update_task_progress(self, task_id: str, progress: float, speed: str = "", eta: str = "") -> bool:
        """更新任务进度"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            update_time = datetime.now().isoformat()
            cursor.execute(
                'UPDATE tasks SET progress = ?, speed = ?, eta = ?, updateTime = ? WHERE id = ?',
                (progress, speed, eta, update_time, task_id)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"更新任务进度失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 总任务数
            cursor.execute('SELECT COUNT(*) FROM tasks')
            total = cursor.fetchone()[0]
            
            # 按状态统计
            cursor.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
            status_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按类型统计
            cursor.execute('SELECT type, COUNT(*) FROM tasks GROUP BY type')
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 今日任务数
            today = datetime.now().date().isoformat()
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE DATE(createTime) = ?', (today,))
            today_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'by_status': status_stats,
                'by_type': type_stats,
                'today': today_count
            }
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}
    
    def cleanup_old_tasks(self, days: int = 30, keep_successful: bool = True) -> int:
        """清理旧任务"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
            cutoff_str = datetime.fromtimestamp(cutoff_date).isoformat()
            
            if keep_successful:
                cursor.execute(
                    'DELETE FROM tasks WHERE createTime < ? AND status != ?',
                    (cutoff_str, TaskStatus.SUCCESS.value)
                )
            else:
                cursor.execute('DELETE FROM tasks WHERE createTime < ?', (cutoff_str,))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected
            
        except Exception as e:
            print(f"清理旧任务失败: {e}")
            return 0
    
    def _row_to_task(self, row, description) -> Task:
        """将数据库行转换为Task对象"""
        # 创建列名到值的映射
        columns = [col[0] for col in description]
        data = dict(zip(columns, row))
        
        # 处理JSON字段
        for json_field in ['outputPaths', 'config', 'metadata', 'tags']:
            if data.get(json_field):
                try:
                    data[json_field] = json.loads(data[json_field])
                except:
                    data[json_field] = [] if json_field in ['outputPaths', 'tags'] else {}
            else:
                data[json_field] = [] if json_field in ['outputPaths', 'tags'] else {}
        
        # 创建Task对象
        return Task(**data)
    
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


class AsyncDatabaseWorker(QThread):
    """异步数据库工作线程"""
    finished = Signal(object)  # 完成信号，返回结果
    error = Signal(str)        # 错误信号
    
    def __init__(self, db_service: DatabaseService, method_name: str, *args, **kwargs):
        super().__init__()
        self.db_service = db_service
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self._is_running = True
    
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


# 全局数据库实例
_db_service = None


def getDatabaseService(db_path: str = "data/tasks.db") -> DatabaseService:
    """获取数据库服务单例"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(db_path)
    return _db_service


def getTaskService() -> DatabaseService:
    """获取任务数据库服务（别名）"""
    return getDatabaseService()


def sqlRequest(service_name: str, method_name: str, callback: Callable, *args, **kwargs):
    """异步数据库请求
    
    Args:
        service_name: 服务名称（如 "taskService"）
        method_name: 方法名（如 "listBy", "save_task"）
        callback: 回调函数
        *args, **kwargs: 方法参数
    """
    if service_name == "taskService":
        db = getDatabaseService()
        # 修正方法名映射
        method_map = {
            'listBy': 'list_tasks_by',
            'getTask': 'get_task',
            'saveTask': 'save_task',
            'deleteTask': 'delete_task',
        }
        actual_method = method_map.get(method_name, method_name)
        
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
    
    return None