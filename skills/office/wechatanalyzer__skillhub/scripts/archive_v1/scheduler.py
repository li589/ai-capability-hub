#!/usr/bin/env python3
"""
定时任务调度器 - 支持每日/周/月/季/半年/年自动生成报告
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3
from pathlib import Path


class SchedulerManager:
    """定时任务管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/chat_history.db'))
        self.scheduler = None
        self._init_scheduler()

    def _init_scheduler(self):
        """初始化调度器"""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers import cron, interval
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
        except ImportError:
            print("警告: APScheduler未安装，定时任务功能不可用")
            print("请使用: pip install apscheduler")

    def add_job(self, name: str, period: str, chat_id: Optional[str] = None,
                report_type: str = 'html') -> bool:
        """添加定时任务"""
        if not self.scheduler:
            return False

        task_id = str(uuid.uuid4())

        # 保存到数据库
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO scheduled_tasks (id, name, period, chat_id, report_type, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (task_id, name, period, chat_id, report_type, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # 添加到调度器
        trigger = self._get_trigger(period)
        if trigger:
            self.scheduler.add_job(
                self._run_task,
                trigger,
                id=task_id,
                name=name,
                args=[task_id, chat_id, report_type]
            )

        return True

    def remove_job(self, name: str) -> bool:
        """删除定时任务"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM scheduled_tasks WHERE name = ?', (name,))
        row = cursor.fetchone()

        if row:
            task_id = row[0]
            cursor.execute('DELETE FROM scheduled_tasks WHERE name = ?', (name,))
            conn.commit()
            conn.close()

            if self.scheduler:
                self.scheduler.remove_job(task_id)
            return True

        conn.close()
        return False

    def enable_job(self, name: str) -> bool:
        """启用定时任务"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM scheduled_tasks WHERE name = ?', (name,))
        row = cursor.fetchone()

        if row and self.scheduler:
            task_id = row[0]
            cursor.execute('UPDATE scheduled_tasks SET enabled = 1 WHERE name = ?', (name,))
            conn.commit()
            conn.close()

            self.scheduler.resume_job(task_id)
            return True

        conn.close()
        return False

    def disable_job(self, name: str) -> bool:
        """禁用定时任务"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM scheduled_tasks WHERE name = ?', (name,))
        row = cursor.fetchone()

        if row and self.scheduler:
            task_id = row[0]
            cursor.execute('UPDATE scheduled_tasks SET enabled = 0 WHERE name = ?', (name,))
            conn.commit()
            conn.close()

            self.scheduler.pause_job(task_id)
            return True

        conn.close()
        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有定时任务"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, period, chat_id, report_type, enabled FROM scheduled_tasks')

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row[0],
                'name': row[1],
                'period': row[2],
                'chat_id': row[3],
                'report_type': row[4],
                'enabled': bool(row[5])
            }
            for row in rows
        ]

    def _get_trigger(self, period: str):
        """获取定时器触发器"""
        from apscheduler.triggers import cron, interval

        triggers = {
            'daily': interval(days=1),
            'weekly': interval(weeks=1),
            'monthly': interval(days=30),
            'quarterly': interval(days=90),
            'semi-annually': interval(days=180),
            'annually': interval(days=365)
        }

        return triggers.get(period)

    def _run_task(self, task_id: str, chat_id: Optional[str], report_type: str):
        """执行定时任务"""
        from .report_generator import ReportGenerator
        from .data_manager import DataManager

        print(f"[{datetime.now()}] 执行定时任务: {task_id}")

        dm = DataManager(self.config)

        if chat_id:
            results = dm.get_analysis(chat_id)
        else:
            results = dm.get_latest_analysis()

        if results:
            generator = ReportGenerator(self.config)
            generator.generate(results, report_type=report_type)
            print(f"[{datetime.now()}] 报告已生成")

            # 更新最后运行时间
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('UPDATE scheduled_tasks SET last_run = ? WHERE id = ?',
                          (datetime.now().isoformat(), task_id))
            conn.commit()
            conn.close()
        else:
            print(f"[{datetime.now()}] 无分析结果可生成报告")
