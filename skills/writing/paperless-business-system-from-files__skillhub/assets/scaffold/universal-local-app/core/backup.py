from __future__ import annotations
import sqlite3, datetime as dt
from pathlib import Path
from .config import DB_PATH, BACKUP_DIR

def create_backup(prefix='manual')->Path:
    BACKUP_DIR.mkdir(parents=True,exist_ok=True)
    target=BACKUP_DIR/f'{prefix}_{dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    src=sqlite3.connect(str(DB_PATH)); dst=sqlite3.connect(str(target))
    try: src.backup(dst); dst.execute('PRAGMA integrity_check').fetchone()
    finally: dst.close(); src.close()
    return target

def integrity_ok(path:Path)->bool:
    c=sqlite3.connect(str(path))
    try: return c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    finally: c.close()
