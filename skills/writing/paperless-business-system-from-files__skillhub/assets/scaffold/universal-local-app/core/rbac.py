from __future__ import annotations
from functools import wraps
from flask import session, redirect, url_for, abort
from .db import one, query

def current_user():
    uid=session.get('uid')
    if not uid: return None
    return one('SELECT u.*,r.name role_name FROM users u LEFT JOIN roles r ON r.id=u.role_id WHERE u.id=? AND u.active=1',(uid,))

def current_permissions():
    u=current_user()
    if not u: return set()
    if u['permissions_customized']:
        rows=query('SELECT p.code FROM user_permissions up JOIN permissions p ON p.code=up.permission_code WHERE up.user_id=?',(u['id'],))
    else:
        rows=query('SELECT p.code FROM role_permissions rp JOIN permissions p ON p.code=rp.permission_code WHERE rp.role_id=?',(u['role_id'],))
    return {r['code'] for r in rows}

def login_required(fn):
    @wraps(fn)
    def w(*a,**kw):
        if not current_user(): return redirect(url_for('login'))
        return fn(*a,**kw)
    return w

def permission_required(code):
    def deco(fn):
        @wraps(fn)
        def w(*a,**kw):
            if not current_user(): return redirect(url_for('login'))
            if code not in current_permissions(): abort(403)
            return fn(*a,**kw)
        return w
    return deco
