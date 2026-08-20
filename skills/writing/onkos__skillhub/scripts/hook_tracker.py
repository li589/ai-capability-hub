#!/usr/bin/env python3
"""
伏笔追踪器 - 基于 SQLite 的伏笔/悬念管理
数据存储在 novel_memory.db 的 hooks 表中
支持: 种埋、收线、遗忘预警、超期统计
"""

import os
import json
import sqlite3
import argparse
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class HookTracker:
    """伏笔追踪器 - SQLite 存储"""

    def __init__(self, db_path: str):
        """
        初始化伏笔追踪器

        Args:
            db_path: SQLite 数据库路径（与 MemoryEngine 共享 novel_memory.db）
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_tables()

    def _ensure_tables(self):
        """确保所需表存在（支持独立使用，无需依赖 MemoryEngine 先建表）"""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hooks (
                id TEXT PRIMARY KEY,
                desc TEXT NOT NULL,
                planted_chapter INTEGER NOT NULL,
                expected_resolve INTEGER,
                resolved_chapter INTEGER,
                resolution TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                tags TEXT DEFAULT '[]',
                related_characters TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hooks_status ON hooks(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hooks_priority ON hooks(priority)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hooks_planted ON hooks(planted_chapter)")
        self.conn.commit()

    def plant(self, desc: str, planted_chapter: int,
              expected_resolve: int = None, priority: str = "normal",
              tags: List[str] = None, related_characters: List[str] = None,
              hook_id: str = None) -> str:
        """
        种埋伏笔（自动检测重复：同描述的open伏笔已存在时返回已有ID）

        Args:
            desc: 伏笔描述
            planted_chapter: 种埋章节
            expected_resolve: 预期收线章节
            priority: 优先级（critical / normal / minor）
            tags: 标签列表
            related_characters: 关联角色列表
            hook_id: 自定义ID

        Returns:
            伏笔ID
        """
        # 重复检测：同描述的open伏笔已存在时直接返回
        existing = self.conn.execute(
            "SELECT id FROM hooks WHERE desc = ? AND status = 'open'", (desc,)
        ).fetchone()
        if existing:
            return existing["id"]

        if not hook_id:
            hook_id = f"hook_{uuid.uuid4().hex[:8]}"

        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        chars_json = json.dumps(related_characters or [], ensure_ascii=False)

        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO hooks (id, desc, planted_chapter, expected_resolve,
                resolved_chapter, resolution, status, priority, tags,
                related_characters, created_at, updated_at)
            VALUES (?, ?, ?, ?, NULL, NULL, 'open', ?, ?, ?, ?, ?)
        """, (hook_id, desc, planted_chapter, expected_resolve, priority,
              tags_json, chars_json, now, now))
        self.conn.commit()
        return hook_id

    def resolve(self, hook_id: str, resolved_chapter: int, resolution: str = "") -> bool:
        """
        收线伏笔

        Args:
            hook_id: 伏笔ID
            resolved_chapter: 收线章节
            resolution: 收线描述
        """
        # 不允许重复resolve已resolved的伏笔
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM hooks WHERE id=?", (hook_id,))
        row = cur.fetchone()
        if not row:
            return False
        if row['status'] == 'resolved':
            return False  # 已回收，不覆盖

        now = datetime.now().isoformat()
        cur.execute("""
            UPDATE hooks
            SET resolved_chapter = ?, resolution = ?, status = 'resolved',
                updated_at = ?
            WHERE id = ? AND status != 'resolved'
        """, (resolved_chapter, resolution, now, hook_id))
        self.conn.commit()
        return cur.rowcount > 0

    def abandon(self, hook_id: str, reason: str = "") -> bool:
        """放弃伏笔"""
        now = datetime.now().isoformat()
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE hooks
            SET status = 'abandoned', resolution = ?, updated_at = ?
            WHERE id = ?
        """, (reason, now, hook_id))
        self.conn.commit()
        return cur.rowcount > 0

    def abandon_chapter_hooks(self, chapter: int, reason: str = "章节修订") -> int:
        """
        放弃指定章节种埋的open伏笔（用于修订章节时清理旧伏笔）

        Args:
            chapter: 种埋章节
            reason: 放弃原因

        Returns:
            放弃的伏笔数量
        """
        now = datetime.now().isoformat()
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE hooks
            SET status = 'abandoned', resolution = ?, updated_at = ?
            WHERE planted_chapter = ? AND status = 'open'
        """, (reason, now, chapter))
        count = cur.rowcount
        self.conn.commit()
        return count

    def get_open_hooks(self, current_chapter: int = None,
                       priority: str = None) -> List[Dict[str, Any]]:
        """获取未收线的伏笔"""
        cur = self.conn.cursor()
        sql = "SELECT * FROM hooks WHERE status = 'open'"
        params = []

        if priority:
            sql += " AND priority = ?"
            params.append(priority)

        if current_chapter is not None:
            # 优先显示即将到期和已超期的
            sql += " ORDER BY CASE WHEN expected_resolve IS NOT NULL AND expected_resolve < ? THEN 0 ELSE 1 END, priority, planted_chapter"
            params.append(current_chapter)
        else:
            sql += " ORDER BY priority, planted_chapter"

        cur.execute(sql, params)
        results = []
        for row in cur.fetchall():
            r = dict(row)
            r["tags"] = json.loads(r.get("tags", "[]"))
            r["related_characters"] = json.loads(r.get("related_characters", "[]"))
            results.append(r)
        return results

    def get_overdue_hooks(self, current_chapter: int) -> List[Dict[str, Any]]:
        """获取超期未收的伏笔"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM hooks
            WHERE status = 'open'
            AND expected_resolve IS NOT NULL
            AND expected_resolve < ?
            ORDER BY expected_resolve
        """, (current_chapter,))
        results = []
        for row in cur.fetchall():
            r = dict(row)
            r["tags"] = json.loads(r.get("tags", "[]"))
            r["related_characters"] = json.loads(r.get("related_characters", "[]"))
            results.append(r)
        return results

    def get_forgotten_hooks(self, current_chapter: int, threshold: int = 100) -> List[Dict[str, Any]]:
        """获取可能被遗忘的伏笔（种埋很久但未收线且近期未提及）"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM hooks
            WHERE status = 'open'
            AND planted_chapter < ?
            ORDER BY planted_chapter
        """, (max(1, current_chapter - threshold),))
        results = []
        for row in cur.fetchall():
            r = dict(row)
            r["tags"] = json.loads(r.get("tags", "[]"))
            r["related_characters"] = json.loads(r.get("related_characters", "[]"))
            results.append(r)
        return results

    def get_hook(self, hook_id: str) -> Optional[Dict[str, Any]]:
        """获取单个伏笔"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM hooks WHERE id = ?", (hook_id,))
        row = cur.fetchone()
        if not row:
            return None
        r = dict(row)
        r["tags"] = json.loads(r.get("tags", "[]"))
        r["related_characters"] = json.loads(r.get("related_characters", "[]"))
        return r

    def list_all(self, status: str = None) -> List[Dict[str, Any]]:
        """列出所有伏笔"""
        cur = self.conn.cursor()
        if status:
            cur.execute("SELECT * FROM hooks WHERE status = ? ORDER BY planted_chapter", (status,))
        else:
            cur.execute("SELECT * FROM hooks ORDER BY planted_chapter")
        results = []
        for row in cur.fetchall():
            r = dict(row)
            r["tags"] = json.loads(r.get("tags", "[]"))
            r["related_characters"] = json.loads(r.get("related_characters", "[]"))
            results.append(r)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取伏笔统计"""
        cur = self.conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM hooks GROUP BY status")
        status_counts = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT priority, COUNT(*) FROM hooks WHERE status = 'open' GROUP BY priority")
        priority_counts = {row[0]: row[1] for row in cur.fetchall()}
        return {
            "status_counts": status_counts,
            "open_priority_counts": priority_counts,
            "total": sum(status_counts.values())
        }

    def execute_action(self, action: str, params: dict) -> dict:
        """统一调度入口"""
        if action == "plant":
            desc = params.get("description") or params.get("desc")
            planted_chapter = params.get("planted_chapter") or params.get("chapter")
            if not desc or planted_chapter is None:
                raise ValueError("plant需要description/desc和planted_chapter")
            tags = params.get("tags", "").split(",") if params.get("tags") else []
            chars = params.get("characters", "").split(",") if params.get("characters") else []
            hid = self.plant(desc, int(planted_chapter),
                             params.get("expected_resolve"),
                             params.get("priority"), tags, chars,
                             params.get("hook_id"))
            return {"hook_id": hid}

        elif action == "resolve":
            hook_id = params.get("hook_id")
            resolved_chapter = params.get("resolved_chapter")
            if not hook_id or resolved_chapter is None:
                raise ValueError("resolve需要hook_id和resolved_chapter")
            resolution = params.get("how") or params.get("resolution", "")
            success = self.resolve(hook_id, int(resolved_chapter), resolution)
            return {"success": success}

        elif action == "abandon":
            hook_id = params.get("hook_id")
            if not hook_id:
                raise ValueError("abandon需要hook_id")
            success = self.abandon(hook_id, params.get("reason", ""))
            return {"success": success}

        elif action == "abandon-chapter":
            chapter = params.get("planted_chapter") or params.get("chapter")
            if chapter is None:
                raise ValueError("abandon-chapter需要chapter")
            count = self.abandon_chapter_hooks(int(chapter), params.get("reason", "章节修订"))
            return {"abandoned_count": count, "chapter": int(chapter)}

        elif action == "list-open":
            return {"hooks": self.get_open_hooks(params.get("current_chapter"),
                                                   params.get("priority"))}

        elif action == "overdue":
            current_chapter = params.get("current_chapter")
            if current_chapter is None:
                raise ValueError("overdue需要current_chapter")
            return {"hooks": self.get_overdue_hooks(int(current_chapter))}

        elif action == "forgotten":
            current_chapter = params.get("current_chapter")
            if current_chapter is None:
                raise ValueError("forgotten需要current_chapter")
            return {"hooks": self.get_forgotten_hooks(int(current_chapter))}

        elif action == "stats":
            return self.get_stats()

        else:
            raise ValueError(f"未知操作: {action}")

    def close(self):
        """关闭连接"""
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='伏笔追踪器')
    parser.add_argument('--db-path', required=True, help='数据库路径')
    parser.add_argument('--action', required=True,
                       choices=['plant', 'resolve', 'abandon', 'abandon-chapter',
                               'get', 'list-open', 'list-all', 'overdue',
                               'forgotten', 'stats'],
                       help='操作类型')
    parser.add_argument('--hook-id', help='伏笔ID')
    parser.add_argument('--desc', help='伏笔描述')
    parser.add_argument('--planted-chapter', type=int, help='种埋章节')
    parser.add_argument('--expected-resolve', type=int, help='预期收线章节')
    parser.add_argument('--resolved-chapter', type=int, help='收线章节')
    parser.add_argument('--resolution', help='收线描述')
    parser.add_argument('--reason', help='放弃原因')
    parser.add_argument('--priority', choices=['critical', 'normal', 'minor'],
                       default=None, help='优先级(默认不限)')
    parser.add_argument('--tags', help='标签(逗号分隔)')
    parser.add_argument('--characters', help='关联角色(逗号分隔)')
    parser.add_argument('--current-chapter', type=int, help='当前章节')
    parser.add_argument('--status', choices=['open', 'resolved', 'abandoned'],
                       help='状态过滤')
    parser.add_argument('--output', choices=['text', 'json'], default='json')

    args = parser.parse_args()
    tracker = HookTracker(args.db_path)
    try:
        skip_keys = {"db_path", "action", "output"}
        params = {k: v for k, v in vars(args).items()
                  if v is not None and k not in skip_keys and not k.startswith('_')}
        result = tracker.execute_action(args.action, params)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        tracker.close()

if __name__ == '__main__':
    main()
if __name__ == '__main__':
    main()
