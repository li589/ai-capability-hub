from __future__ import annotations
import importlib.util, os, subprocess, sys, time, urllib.request, venv
from pathlib import Path
from core.lifecycle import load_state, choose_port, STOPPING
from core.config import ROOT

REQUIRED=('flask','waitress','openpyxl')
VENV_DIR=ROOT/('.venv_windows' if sys.platform=='win32' else '.venv')

def healthy(url):
    try:
        with urllib.request.urlopen(url.rstrip('/')+'/health',timeout=.7) as r: return r.status==200
    except Exception: return False

def deps_ok(): return all(importlib.util.find_spec(x) is not None for x in REQUIRED)
def venv_python(): return VENV_DIR/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')

def ensure_project_runtime():
    if deps_ok(): return Path(sys.executable)
    py=venv_python()
    if py.is_file(): return py
    print('未发现项目运行环境，正在创建项目专属虚拟环境...')
    try:
        venv.EnvBuilder(with_pip=True,clear=False).create(VENV_DIR)
        py=venv_python()
        subprocess.check_call([str(py),'-m','pip','install','-r',str(ROOT/'requirements.txt')])
        return py
    except Exception as e:
        print('运行环境准备失败：',e)
        print('如目标电脑无法联网，请交付已验证 EXE、便携 Python 或本地 wheelhouse。')
        raise

def main():
    state=load_state(); url=state.get('url')
    if url and healthy(url): print('系统已在运行：',url); return 0
    runtime=ensure_project_runtime()
    if runtime.resolve()!=Path(sys.executable).resolve():
        return subprocess.call([str(runtime),str(Path(__file__).resolve())])
    deadline=time.time()+12
    while STOPPING.exists() and time.time()<deadline: time.sleep(.25)
    bind_host=os.environ.get('APP_HOST','{{DEFAULT_BIND_HOST}}')
    port=choose_port(bind_host=bind_host)
    env=os.environ.copy(); env['APP_PORT']=str(port); env.setdefault('APP_HOST',bind_host)
    log=(ROOT/'data'/'server.log').open('a',encoding='utf-8')
    subprocess.Popen([sys.executable,str(ROOT/'app.py')],cwd=str(ROOT),env=env,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
    local_url=f'http://127.0.0.1:{port}'
    for _ in range(50):
        if healthy(local_url):
            print('启动成功：',local_url)
            if bind_host=='0.0.0.0': print('局域网访问：请使用本机内网 IPv4 + 端口，例如 http://192.168.x.x:%s' % port)
            return 0
        time.sleep(.25)
    print('启动未通过健康检查，请运行诊断_一键诊断.bat'); return 1
if __name__=='__main__': raise SystemExit(main())
