from __future__ import annotations
from .db import connect

MIGRATIONS=[
('0001_core', r"""
CREATE TABLE IF NOT EXISTS schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS roles(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,description TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS permissions(code TEXT PRIMARY KEY,name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS role_permissions(role_id INTEGER NOT NULL,permission_code TEXT NOT NULL,PRIMARY KEY(role_id,permission_code),FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,FOREIGN KEY(permission_code) REFERENCES permissions(code) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,role_id INTEGER,active INTEGER NOT NULL DEFAULT 1,must_change_password INTEGER NOT NULL DEFAULT 1,permissions_customized INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(role_id) REFERENCES roles(id));
CREATE TABLE IF NOT EXISTS user_permissions(user_id INTEGER NOT NULL,permission_code TEXT NOT NULL,PRIMARY KEY(user_id,permission_code),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(permission_code) REFERENCES permissions(code) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,action TEXT NOT NULL,detail TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
""")]

try:
    from business.generated_migrations import MIGRATIONS as BUSINESS_MIGRATIONS, ensure_business_schema
except Exception:
    BUSINESS_MIGRATIONS=[]
    def ensure_business_schema(conn): return None
MIGRATIONS.extend(BUSINESS_MIGRATIONS)

def migrate():
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        for mid,sql in MIGRATIONS:
            if c.execute('SELECT 1 FROM schema_migrations WHERE id=?',(mid,)).fetchone(): continue
            c.executescript(sql); c.execute('INSERT INTO schema_migrations(id) VALUES(?)',(mid,))
        # 即使旧版 migration id 已执行，也检查新增字段并做非破坏式补齐。
        ensure_business_schema(c)
