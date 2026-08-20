from __future__ import annotations
import secrets
from flask import session, request, abort

def token():
    if not session.get('_csrf'): session['_csrf']=secrets.token_urlsafe(24)
    return session['_csrf']

def validate_request():
    if request.method not in {'POST','PUT','PATCH','DELETE'}: return
    if request.path=='/internal/shutdown': return
    supplied=request.form.get('_csrf') or request.headers.get('X-CSRF-Token')
    if not supplied or not secrets.compare_digest(str(supplied),str(session.get('_csrf',''))): abort(400,'CSRF 校验失败')
