from __future__ import annotations
import importlib.util, json, subprocess, sys, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    results=[]
    missing=[m for m in ('flask','waitress','openpyxl') if importlib.util.find_spec(m) is None]
    if missing:
        results.append({'id':'environment','ok':False,'evidence':'缺少依赖：'+', '.join(missing)+'；请先 pip install -r requirements.txt'})
        obj={'schema_version':'1.0','steps':results,'overall_status':'failed'}
        (ROOT/'RUNTIME_ACCEPTANCE.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(obj,ensure_ascii=False,indent=2)); return 1
    results.append({'id':'environment','ok':True,'evidence':'运行依赖已发现'})
    r=subprocess.run([sys.executable,str(ROOT/'launcher.py')],cwd=ROOT,text=True,capture_output=True,timeout=20); results.append({'id':'start','ok':r.returncode==0,'evidence':r.stdout[-500:]+r.stderr[-500:]})
    state_file=ROOT/'data'/'runtime'/'runtime.json'; state=json.loads(state_file.read_text(encoding='utf-8')) if state_file.exists() else {}
    url=state.get('url')
    if url:
        try:
            body=urllib.request.urlopen(url.rstrip('/')+'/health',timeout=2).read().decode(); ok='"ok":true' in body.replace(' ','').lower()
        except Exception as e: ok=False; body=str(e)
    else: ok=False; body='启动失败或未生成运行状态，跳过健康接口请求。'
    results.append({'id':'health','ok':ok,'evidence':body[:500]})
    s=subprocess.run([sys.executable,str(ROOT/'stop_server.py')],cwd=ROOT,text=True,capture_output=True,timeout=15); results.append({'id':'safe_stop','ok':s.returncode==0,'evidence':s.stdout[-500:]+s.stderr[-500:]})
    obj={'schema_version':'1.0','steps':results,'overall_status':'passed' if all(x['ok'] for x in results) else 'failed'}
    (ROOT/'RUNTIME_ACCEPTANCE.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(obj,ensure_ascii=False,indent=2)); return 0 if obj['overall_status']=='passed' else 1
if __name__=='__main__': raise SystemExit(main())
