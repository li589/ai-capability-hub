"""订单存储 (SQLite)"""
import json
import sqlite3
import os
from typing import Optional

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
                    query_text TEXT,
                    method TEXT,
                    numbers TEXT,
                    status TEXT DEFAULT 'INIT',
                    result TEXT,
                    transaction_id TEXT,
                    refund_reason TEXT,
                    user_id TEXT,
                    created_at INTEGER,
                    fulfilled_at INTEGER
                )
            """)

    def save(self, order: dict):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO orders
                (out_trade_no, payment_code, amount, description, query_text, method, numbers,
                 status, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order['out_trade_no'], order.get('payment_code'),
                order['amount'], order.get('description'),
                order.get('query'), order.get('method'),
                json.dumps(order.get('numbers')) if order.get('numbers') else None,
                order.get('status', 'INIT'), order.get('user_id'),
                order.get('created_at'),
            ))

    def get(self, out_trade_no: str) -> Optional[dict]:
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

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
