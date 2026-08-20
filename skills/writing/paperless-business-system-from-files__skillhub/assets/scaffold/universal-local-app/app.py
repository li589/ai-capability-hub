from __future__ import annotations
import os, signal, threading
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from core.config import SYSTEM_NAME, APP_ID
from core.migrations import migrate
from core.bootstrap import ensure_secret, seed_core
from core.db import one, execute
from core.security import verify_password, hash_password
from core.rbac import login_required, permission_required, current_user, current_permissions
from core.audit import audit
from core.lifecycle import save_state, clear_state, new_shutdown_token
from core.csrf import token as csrf_token, validate_request as validate_csrf
from core.config import CREDENTIAL_FILE

app=Flask(__name__); app.secret_key=ensure_secret(); app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
app.jinja_env.globals['csrf_token']=csrf_token
app.before_request(validate_csrf)
migrate(); seed_core()
try:
    from business.runtime_generated import bp as business_bp, ensure_business_permissions, load_schema
    ensure_business_permissions(); app.register_blueprint(business_bp)
except Exception:
    business_bp=None
    def load_schema(): return {'objects':[]}
shutdown_token=new_shutdown_token()

@app.get('/health')
def health(): return jsonify(ok=True,app_id=APP_ID,system=SYSTEM_NAME)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=one('SELECT * FROM users WHERE username=? AND active=1',(request.form.get('username','').strip(),))
        if u and verify_password(request.form.get('password',''),u['password_hash']):
            session.clear(); session['uid']=u['id']; audit(u['id'],'登录'); return redirect(url_for('index'))
        return render_template('login.html',error='账号或密码错误')
    return render_template('login.html',error=None)

@app.post('/logout')
def logout():
    u=current_user(); audit(u['id'],'退出') if u else None; session.clear(); return redirect(url_for('login'))

@app.get('/')
@login_required
def index(): return render_template('dashboard.html',user=current_user(),permissions=sorted(current_permissions()),business_objects=load_schema().get('objects',[]))

@app.route('/change-password',methods=['GET','POST'])
@login_required
def change_password():
    u=current_user(); error=None
    if request.method=='POST':
        if not verify_password(request.form.get('old_password',''),u['password_hash']): error='原密码错误'
        elif len(request.form.get('new_password',''))<8: error='新密码至少 8 位'
        else:
            execute('UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?',(hash_password(request.form['new_password']),u['id']))
            audit(u['id'],'修改密码')
            try: CREDENTIAL_FILE.unlink()
            except FileNotFoundError: pass
            return redirect(url_for('index'))
    return render_template('change_password.html',error=error)

@app.post('/internal/shutdown')
def shutdown():
    if request.headers.get('X-Shutdown-Token')!=shutdown_token: abort(403)
    def stop(): os.kill(os.getpid(),signal.SIGTERM)
    threading.Timer(.2,stop).start(); return jsonify(ok=True)

def run():
    host=os.environ.get('APP_HOST','{{DEFAULT_BIND_HOST}}'); port=int(os.environ.get('APP_PORT','5200'))
    save_state({'app_id':APP_ID,'pid':os.getpid(),'port':port,'url':f'http://127.0.0.1:{port}','shutdown_token':shutdown_token})
    try:
        try:
            from waitress import serve; serve(app,host=host,port=port,threads=8)
        except ImportError: app.run(host=host,port=port,debug=False,use_reloader=False)
    finally: clear_state()
if __name__=='__main__': run()
