#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, py_compile, subprocess, sys, tempfile, zipfile
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]; S=ROOT/'scripts'
BASE_SKIP={'__pycache__','.git','node_modules'}; RUNTIME_DIRS={'.venv','venv','.venv_windows','portable_runtime'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def load_spec(root):
    p=root/'system-spec.json'
    try:return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
    except Exception:return {}
def portable(root):
    s=load_spec(root); return (s.get('system') or {}).get('deployment_mode')=='portable_full' or bool((s.get('portable_full') or {}).get('enabled'))
def include_runtime(root):
    if not portable(root): return False
    cfg=load_spec(root).get('portable_full') or {}
    return bool(cfg.get('package_runtime_dirs')) or cfg.get('runtime_strategy')=='bundled_python'
def files(root,runtime=False):
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.suffix=='.pyc' or any(x in BASE_SKIP for x in p.parts): continue
        if not runtime and any(x in RUNTIME_DIRS for x in p.parts): continue
        yield p
def exists_name(root,name): return any(p.is_file() and p.name==name for p in root.rglob('*'))
def run(script,*args):
    r=subprocess.run([sys.executable,str(S/script),*map(str,args)],capture_output=True,text=True,timeout=240)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.returncode!=0:
        if r.stderr.strip(): print(r.stderr.strip())
        raise RuntimeError(f'{script} 未通过')
def refresh(project):
    py=[]
    for p in files(project,False):
        if p.suffix=='.py': py_compile.compile(str(p),doraise=True); py.append({'path':p.relative_to(project).as_posix(),'sha256':sha(p)})
    (project/'PY_SOURCE_MANIFEST.json').write_text(json.dumps({'schema_version':'1.1','generated_at':datetime.now(timezone.utc).isoformat(),'first_party':py},ensure_ascii=False,indent=2),encoding='utf-8')
    sp=project/'DELIVERY_STATUS.json'
    if sp.is_file():
        o=json.loads(sp.read_text(encoding='utf-8')); o['python_source_included']=bool(py); o['exe_build_source_included']=exists_name(project,'build_exe_windows.py') and bool(list(project.rglob('*.spec'))); o['diagnostic_bundle_included']=exists_name(project,'diagnose_local.py'); o['target_pc_acceptance_included']=exists_name(project,'target_pc_acceptance.py')
        if portable(project):
            service=project/'01_服务端_完整程序'; o['portable_full_layout_included']=service.is_dir() and (project/'02_Windows填写客户端').is_dir(); o['windows_client_included']=(project/'02_Windows填写客户端').is_dir(); o['macos_client_included']=(project/'03_macOS填写客户端').is_dir(); o['lan_helpers_included']=exists_name(project,'查看服务器内网地址_Windows.bat'); o['portable_full_runtime_strategy']=(load_spec(project).get('portable_full') or {}).get('runtime_strategy'); o['portable_runtime_included']=any((service/d).exists() for d in ('portable_runtime','.venv_windows'))
        sp.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
    hp=project/'FILES_SHA256.txt'; rows=[]
    for p in files(project,include_runtime(project)):
        if p!=hp: rows.append(f'{sha(p)}  {p.relative_to(project).as_posix()}')
    hp.write_text('\n'.join(rows)+'\n',encoding='utf-8')
def pack(project,out):
    if out.exists():out.unlink()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,strict_timestamps=False) as z:
        for p in files(project,include_runtime(project)):z.write(p,(Path(project.name)/p.relative_to(project)).as_posix())
def validate_all(project):
    run('validate_local_bundle.py',project,'--strict')
    if portable(project):run('validate_portable_full.py',project,'--strict')
    if (project/'delivery-manifest.json').is_file():run('validate_delivery.py',project,'--strict')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('project');ap.add_argument('--output',required=True);a=ap.parse_args();project=Path(a.project).resolve();out=Path(a.output).resolve()
    if not project.is_dir():print('[PB001] 项目目录不存在');return 1
    sp=project/'DELIVERY_STATUS.json';tp=project/'TEST_REPORT.md'
    if not sp.is_file() or not tp.is_file():print('[PB401] 缺少 DELIVERY_STATUS.json 或 TEST_REPORT.md');return 1
    o=json.loads(sp.read_text(encoding='utf-8'));tt=tp.read_text(encoding='utf-8',errors='replace').lower()
    if not o.get('tests_executed') or '状态：未执行' in tt or 'status: not run' in tt or 'not_tested' in tt:print('[PB401] 测试尚未真实执行；先完成测试再打包。');return 1
    refresh(project);validate_all(project);out.parent.mkdir(parents=True,exist_ok=True)
    o=json.loads(sp.read_text(encoding='utf-8'));o['zip_reextract_verified']=False;sp.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8');refresh(project);pack(project,out)
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(out) as z:z.extractall(td)
        validate_all(Path(td)/project.name)
    o=json.loads(sp.read_text(encoding='utf-8'));o['zip_reextract_verified']=True;sp.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8');refresh(project);pack(project,out)
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(out) as z:z.extractall(td)
        validate_all(Path(td)/project.name)
    print(f'[完成] 最终 ZIP：{out}');print(f'[SHA-256] {sha(out)}');return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:print(f'[PB401] 最终交付失败：{e}');raise SystemExit(1)
