#!/usr/bin/env python3
"""
日历管理器 - 从聊天记录中提取重要事项并生成日历提醒
"""

import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

from core.data_paths import resolve_db_path


class CalendarManager:
    """日历事件管理器"""

    # 日期时间提取模式
    DATE_PATTERNS = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2024-01-01 或 2024/01/01
        r'(\d{1,2}[-/]\d{1,2})',  # 01-01 或 01/01
        r'下?个?(周一|周二|周三|周四|周五|周六|周日)',
        r'(今天|明天|后天|大后天)',
        r'(\d+)(天|周|个月|年)(之后|以后|后)',
    ]

    # 事件关键词
    EVENT_KEYWORDS = {
        'meeting': ['开会', '会议', 'meeting', '讨论', '评审'],
        'deadline': ['截止', 'deadline', '交付', '完成', '提交', '上线'],
        'appointment': ['约会', '见面', '面试', '看病', '体检', '预约'],
        'reminder': ['记得', '提醒', '别忘了', '注意', '不要忘记'],
        'birthday': ['生日', '纪念日', 'anniversary'],
        'payment': ['付款', '转账', '还钱', '账单', '缴费'],
        'travel': ['出行', '旅游', '出差', '回家', '航班', '火车'],
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = resolve_db_path(config.get('db_path'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for SQLite connections."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """初始化日历数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT,
                    title TEXT,
                    description TEXT,
                    event_date TEXT,
                    event_time TEXT,
                    event_type TEXT,
                    importance TEXT,
                    created_at TEXT,
                    source_message TEXT
                )
            ''')

    def extract_events_from_messages(self, messages: List[Dict[str, Any]], chat_id: str) -> List[Dict[str, Any]]:
        """从聊天记录中提取事件并保存"""
        events = []
        today = datetime.now()

        for msg in messages:
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')

            # 提取日期
            event_date = None
            for pattern in self.DATE_PATTERNS:
                match = re.search(pattern, content)
                if match:
                    event_date = self._parse_date(match.group(1), today)
                    break

            # 提取事件类型和重要性
            event_type = self._detect_event_type(content)
            importance = self._detect_importance(content)

            # 如果发现相关关键词，提取事件
            if event_type or self._has_event_keywords(content):
                title = self._extract_event_title(content, event_type)

                event = {
                    'id': str(uuid.uuid4()),
                    'chat_id': chat_id,
                    'title': title,
                    'description': content[:200],
                    'event_date': event_date.isoformat() if event_date else (today + timedelta(days=7)).isoformat(),
                    'event_time': self._extract_time(content),
                    'event_type': event_type or 'reminder',
                    'importance': importance,
                    'created_at': datetime.now().isoformat(),
                    'source_message': content[:100]
                }

                events.append(event)
                self._save_event(event)

        return events

    def _parse_date(self, date_str: str, reference_date: datetime) -> Optional[datetime]:
        """解析日期字符串"""
        # 处理"今天"、"明天"等
        if '今天' in date_str:
            return reference_date
        if '明天' in date_str:
            return reference_date + timedelta(days=1)
        if '后天' in date_str:
            return reference_date + timedelta(days=2)
        if '大后天' in date_str:
            return reference_date + timedelta(days=3)

        # 处理"下周一"等
        weekday_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
        for day_name, weekday in weekday_map.items():
            if day_name in date_str:
                days_ahead = (weekday - reference_date.weekday() + 7) % 7
                if '下' in date_str:
                    days_ahead += 7
                return reference_date + timedelta(days=days_ahead if days_ahead > 0 else 7)

        # 处理"X天后"
        future_match = re.search(r'(\d+)(天|周|个月|年)(之后|以后|后)', date_str)
        if future_match:
            value = int(future_match.group(1))
            unit = future_match.group(2)
            if '天' in unit:
                return reference_date + timedelta(days=value)
            elif '周' in unit:
                return reference_date + timedelta(weeks=value)
            elif '个月' in unit:
                return reference_date + timedelta(days=value * 30)
            elif '年' in unit:
                return reference_date + timedelta(days=value * 365)

        # 处理标准日期格式（带年份）
        for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # 无年份的月-日（如 "08-20"）：显式补参考年份构造，
        # 避免依赖 strptime 默认年份（Python 3.15 起该行为将变更）
        md = re.fullmatch(r'(\d{1,2})[-/](\d{1,2})', date_str.strip())
        if md:
            try:
                return datetime(reference_date.year, int(md.group(1)), int(md.group(2)))
            except ValueError:
                return None

        return None

    def _extract_time(self, text: str) -> Optional[str]:
        """提取时间"""
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_match:
            return f"{time_match.group(1)}:{time_match.group(2)}"
        return None

    def _detect_event_type(self, text: str) -> Optional[str]:
        """检测事件类型"""
        for event_type, keywords in self.EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return event_type
        return None

    def _detect_importance(self, text: str) -> str:
        """检测重要性"""
        high_keywords = ['紧急', '必须', '重要', '马上', '立刻', '今天必须', 'deadline', '截止今天']
        medium_keywords = ['记得', '提醒', '应该', '最好']

        for kw in high_keywords:
            if kw in text:
                return 'high'
        for kw in medium_keywords:
            if kw in text:
                return 'medium'
        return 'low'

    def _has_event_keywords(self, text: str) -> bool:
        """检查是否包含事件关键词"""
        all_keywords = []
        for keywords in self.EVENT_KEYWORDS.values():
            all_keywords.extend(keywords)
        return any(kw in text for kw in all_keywords)

    def _extract_event_title(self, text: str, event_type: Optional[str]) -> str:
        """提取事件标题"""
        # 去除时间相关的部分作为标题
        title = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', text)
        title = re.sub(r'\d{1,2}:\d{2}', '', title)
        title = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', title)
        title = ' '.join(title.split())

        if len(title) > 30:
            title = title[:30] + '...'

        return title if title else "待确认事项"

    def _save_event(self, event: Dict[str, Any]):
        """保存事件到数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calendar_events (id, chat_id, title, description, event_date, event_time, event_type, importance, created_at, source_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['id'],
                event['chat_id'],
                event['title'],
                event['description'],
                event['event_date'],
                event['event_time'],
                event['event_type'],
                event['importance'],
                event['created_at'],
                event['source_message']
            ))

    def get_events(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                   event_type: Optional[str] = None, importance: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询事件"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = 'SELECT * FROM calendar_events WHERE 1=1'
            params = []

            if start_date:
                query += ' AND event_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND event_date <= ?'
                params.append(end_date)
            if event_type:
                query += ' AND event_type = ?'
                params.append(event_type)
            if importance:
                query += ' AND importance = ?'
                params.append(importance)

            query += ' ORDER BY event_date'

            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = ['id', 'chat_id', 'title', 'description', 'event_date', 'event_time',
                       'event_type', 'importance', 'created_at', 'source_message']

            return [dict(zip(columns, row)) for row in rows]

    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取即将到来的事件"""
        today = datetime.now().date().isoformat()
        end_date = (datetime.now() + timedelta(days=days)).date().isoformat()
        return self.get_events(start_date=today, end_date=end_date)

    def delete_event(self, event_id: str) -> bool:
        """删除事件"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM calendar_events WHERE id = ?', (event_id,))
        return True

    def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """更新事件"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            query = f'UPDATE calendar_events SET {set_clause} WHERE id = ?'
            params = list(updates.values()) + [event_id]
            cursor.execute(query, params)
        return True
