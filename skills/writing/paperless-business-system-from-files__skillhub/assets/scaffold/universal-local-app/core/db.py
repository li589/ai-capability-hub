from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

@contextmanager
def connect():
    conn=sqlite3.connect(str(DB_PATH),timeout=20)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def query(sql,params=()):
    with connect() as c: return c.execute(sql,params).fetchall()

def one(sql,params=()):
    with connect() as c: return c.execute(sql,params).fetchone()

def execute(sql,params=()):
    with connect() as c: return c.execute(sql,params).lastrowid
