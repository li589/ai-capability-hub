from __future__ import annotations
import json, socket, secrets, time
from pathlib import Path
from .config import APP_ID, RUNTIME_DIR
STATE=RUNTIME_DIR/'runtime.json'; STOPPING=RUNTIME_DIR/'stopping.json'

def load_state():
    try: return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception: return {}

def save_state(obj): STATE.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def clear_state():
    for p in (STATE,STOPPING):
        try: p.unlink()
        except FileNotFoundError: pass

def choose_port(start=5200,end=5299,bind_host="127.0.0.1"):
    for port in range(start,end+1):
        s=socket.socket(); s.settimeout(.15)
        try: s.bind((bind_host,port)); return port
        except OSError: pass
        finally: s.close()
    raise RuntimeError('没有可用本地端口')

def new_shutdown_token(): return secrets.token_urlsafe(32)

def mark_stopping(): STOPPING.write_text(json.dumps({'at':time.time()}),encoding='utf-8')
