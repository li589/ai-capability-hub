from __future__ import annotations
import json, urllib.request, urllib.error, time
from core.lifecycle import load_state, mark_stopping, clear_state

def main():
    s=load_state(); url=s.get('url'); token=s.get('shutdown_token')
    if not url or not token: clear_state(); print('未发现本项目运行状态。'); return 0
    mark_stopping()
    req=urllib.request.Request(url.rstrip('/')+'/internal/shutdown',data=b'',method='POST',headers={'X-Shutdown-Token':token})
    try: urllib.request.urlopen(req,timeout=2).read()
    except Exception as e: print('停止请求结果：',e)
    for _ in range(32):
        try: urllib.request.urlopen(url.rstrip('/')+'/health',timeout=.25); time.sleep(.25)
        except Exception: clear_state(); print('已停止。'); return 0
    print('服务未在预期时间退出，请运行一键诊断。'); return 1
if __name__=='__main__': raise SystemExit(main())
