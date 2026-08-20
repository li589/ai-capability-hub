from __future__ import annotations
import secrets
from .db import connect
from .security import hash_password, random_password
from .config import SECRET_FILE, CREDENTIAL_FILE

PERMISSIONS=[('dashboard_view','查看首页'),('change_password','修改本人密码'),('user_manage','用户管理'),('permission_manage','权限管理'),('backup_manage','备份恢复')]

def ensure_secret():
    if not SECRET_FILE.exists(): SECRET_FILE.write_text(secrets.token_hex(32),encoding='utf-8')
    return SECRET_FILE.read_text(encoding='utf-8').strip()

def seed_core():
    with connect() as c:
        for code,name in PERMISSIONS: c.execute('INSERT OR IGNORE INTO permissions(code,name) VALUES(?,?)',(code,name))
        c.execute("INSERT OR IGNORE INTO roles(name,description) VALUES('管理员','拥有全部系统功能')")
        role=c.execute("SELECT id FROM roles WHERE name='管理员'").fetchone()['id']
        for code,_ in PERMISSIONS: c.execute('INSERT OR IGNORE INTO role_permissions(role_id,permission_code) VALUES(?,?)',(role,code))
        if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            password=random_password()
            c.execute('INSERT INTO users(username,password_hash,role_id,must_change_password) VALUES(?,?,?,1)',('管理员',hash_password(password),role))
            CREDENTIAL_FILE.write_text('首次管理员账号：管理员\n首次随机密码：'+password+'\n登录后请立即修改密码。\n',encoding='utf-8')
