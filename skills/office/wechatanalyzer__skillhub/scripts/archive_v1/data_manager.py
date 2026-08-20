#!/usr/bin/env python3
"""
数据管理器 - 负责聊天记录存储和分析结果管理
"""

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


class DataManager:
    """聊天数据管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/chat_history.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @staticmethod
    @contextmanager
    def _get_connection(db_path: Path):
        """Context manager for SQLite connections. Closes on exit."""
        conn = sqlite3.connect(str(db_path))
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库"""
        with self._get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建聊天记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_records (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    source TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    message_count INTEGER
                )
            ''')

            # 创建消息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    sender TEXT,
                    content TEXT,
                    timestamp TEXT,
                    msg_type TEXT,
                    FOREIGN KEY (chat_id) REFERENCES chat_records(id)
                )
            ''')

            # 创建分析结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    analysis_type TEXT,
                    results_json TEXT,
                    created_at TEXT,
                    FOREIGN KEY (chat_id) REFERENCES chat_records(id)
                )
            ''')

            # 创建定时任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    period TEXT,
                    chat_id TEXT,
                    report_type TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_run TEXT,
                    created_at TEXT
                )
            ''')

    def parse_text_input(self, text: str) -> List[Dict[str, Any]]:
        """
        解析粘贴的聊天记录文本
        支持多种格式：
        - [时间] 发送者: 内容
        - 时间 | 发送者 | 内容
        - 发送者: 内容
        """

        messages = []
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试多种格式
            msg = self._parse_line(line)
            if msg:
                messages.append(msg)

        return messages

    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行聊天记录"""
        # 格式1: [2024-01-01 12:30:00] 张三: 你好
        match = re.match(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*([^:：]+)[:：]\s*(.+)', line)
        if match:
            return {
                'timestamp': match.group(1).strip(),
                'sender': match.group(2).strip(),
                'content': match.group(3).strip()
            }

        # 格式2: 2024-01-01 12:30:00 | 张三 | 你好
        match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*[|｜]\s*([^|：]+)\s*[|｜]\s*(.+)', line)
        if match:
            return {
                'timestamp': match.group(1).strip(),
                'sender': match.group(2).strip(),
                'content': match.group(3).strip()
            }

        # 格式3: 张三: 你好 (无时间)
        match = re.match(r'^([^:：]+)[:：]\s*(.+)', line)
        if match:
            return {
                'timestamp': datetime.now().isoformat(),
                'sender': match.group(1).strip(),
                'content': match.group(2).strip()
            }

        # 格式4: 对方消息模式（假设没有发送者的是自己的消息）
        match = re.match(r'^(.{1,20})$', line)  # 纯文本无标点的短消息
        if match and len(line) < 100:
            return {
                'timestamp': datetime.now().isoformat(),
                'sender': 'other',
                'content': line
            }

        return None

    def save_chat(self, name: str, messages: List[Dict], source: str = 'paste') -> str:
        """保存聊天记录"""
        chat_id = str(uuid.uuid4())

        with self._get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_records (id, name, source, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (chat_id, name, source, datetime.now().isoformat(),
                  datetime.now().isoformat(), len(messages)))

            for msg in messages:
                cursor.execute('''
                    INSERT INTO messages (chat_id, sender, content, timestamp, msg_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (chat_id, msg.get('sender', 'other'), msg.get('content', ''),
                      msg.get('timestamp', datetime.now().isoformat()), msg.get('msg_type', 'text')))

        return chat_id

    def save_analysis(self, results: Dict[str, Any], chat_id: Optional[str] = None) -> str:
        """保存分析结果"""
        if not chat_id:
            chat_id = str(uuid.uuid4())

        # 将chat_id存入结果字典，便于后续查询
        results_with_id = dict(results)
        results_with_id['chat_id'] = chat_id

        with self._get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_results (chat_id, analysis_type, results_json, created_at)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, 'full_analysis', json.dumps(results_with_id, ensure_ascii=False),
                  datetime.now().isoformat()))

        return chat_id

    def _fetch_rows(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a query and return all rows using context manager."""
        with self._get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_analysis(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """获取分析结果"""
        rows = self._fetch_rows(
            'SELECT results_json, chat_id FROM analysis_results WHERE chat_id = ? ORDER BY created_at DESC LIMIT 1',
            (chat_id,)
        )
        if rows:
            result = json.loads(rows[0][0])
            result['chat_id'] = rows[0][1]
            return result
        return None

    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """获取最新的分析结果"""
        rows = self._fetch_rows(
            'SELECT results_json, chat_id FROM analysis_results ORDER BY created_at DESC LIMIT 1'
        )
        if rows:
            result = json.loads(rows[0][0])
            result['chat_id'] = rows[0][1]
            return result
        return None

    def get_chat_list(self) -> List[Dict[str, Any]]:
        """获取聊天记录列表"""
        rows = self._fetch_rows(
            'SELECT id, name, source, created_at, message_count FROM chat_records ORDER BY created_at DESC'
        )
        return [
            {'id': r[0], 'name': r[1], 'source': r[2], 'created_at': r[3], 'message_count': r[4]}
            for r in rows
        ]

    def get_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """获取指定聊天记录的所有消息"""
        rows = self._fetch_rows(
            'SELECT sender, content, timestamp, msg_type FROM messages WHERE chat_id = ? ORDER BY timestamp',
            (chat_id,)
        )
        return [
            {'sender': r[0], 'content': r[1], 'timestamp': r[2], 'msg_type': r[3]}
            for r in rows
        ]
