"""订单存储 (SQLite)"""
import json
import sqlite3
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'orders.db')


class OrderStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    out_trade_no TEXT PRIMARY KEY,
                    payment_code TEXT,
                    amount INTEGER,
                    description TEXT,
                    video_url TEXT,
                    status TEXT DEFAULT 'INIT',
                    task_status TEXT DEFAULT 'pending',
                    result TEXT,
                    error TEXT,
                    transaction_id TEXT,
                    refund_reason TEXT,
                    user_id TEXT,
                    progress TEXT,
                    stock_code TEXT,
                    company_name TEXT,
                    created_at INTEGER,
                    fulfilled_at INTEGER,
                    completed_at INTEGER
                )
            """)

    def save(self, order: dict):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO orders
                (out_trade_no, payment_code, amount, description, video_url,
                 status, task_status, user_id, stock_code, company_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.get('out_trade_no'),
                order.get('payment_code'),
                order.get('amount'),
                order.get('description'),
                order.get('video_url'),
                order.get('status', 'INIT'),
                order.get('task_status', 'pending'),
                order.get('user_id'),
                order.get('stock_code'),
                order.get('company_name'),
                order.get('created_at'),
            ))

    def get(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE out_trade_no = ?", (out_trade_no,)
            ).fetchone()
            return dict(row) if row else None

    def update_status(self, out_trade_no: str, status: str, **kwargs):
        sets = ["status = ?"]
        vals = [status]
        for k, v in kwargs.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(out_trade_no)
        with self._conn() as conn:
            conn.execute(
                f"UPDATE orders SET {', '.join(sets)} WHERE out_trade_no = ?", vals
            )

    def update_progress(self, out_trade_no: str, dim_id: str, message: str):
        """更新分析进度"""
        order = self.get(out_trade_no)
        if not order:
            return
        
        progress = json.loads(order.get('progress') or '{}')
        progress[dim_id] = message
        
        with self._conn() as conn:
            conn.execute(
                "UPDATE orders SET progress = ? WHERE out_trade_no = ?",
                (json.dumps(progress, ensure_ascii=False), out_trade_no)
            )

    def get_progress(self, out_trade_no: str) -> Dict[str, str]:
        """获取分析进度"""
        order = self.get(out_trade_no)
        if not order:
            return {}
        return json.loads(order.get('progress') or '{}')

    def save_result(self, out_trade_no: str, result: Dict[str, Any]):
        """保存分析结果"""
        with self._conn() as conn:
            conn.execute(
                "UPDATE orders SET result = ?, completed_at = ? WHERE out_trade_no = ?",
                (json.dumps(result, ensure_ascii=False), int(__import__('time').time()), out_trade_no)
            )

    def get_result(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        """获取分析结果"""
        order = self.get(out_trade_no)
        if not order or not order.get('result'):
            return None
        return json.loads(order['result'])

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
