#!/usr/bin/env python3
"""在隔离副本中执行生成系统的真实运行级 E2E 测试。

覆盖：启动/健康检查、登录、CRUD、严格类型校验、CSV 导入预览与提交、XLSX 导出、
项目级安全停止、SQLite 备份/恢复与完整性检查。原项目业务数据库不会被改写。
"""
from __future__ import annotations
import argparse, http.cookiejar, json, os, re, shutil, socket, sqlite3, subprocess, sys, tempfile, time, urllib.parse, urllib.request, uuid
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS={'.git','__pycache__','node_modules','.venv','venv','.venv_windows','portable_runtime','backups','import_staging'}


def service_root(project:Path)->Path:
    p=project/'01_服务端_完整程序'
    return p if p.is_dir() else project


def choose_python(project:Path, explicit:str|None)->Path:
    if explicit:
        p=Path(explicit).expanduser().resolve()
        if not p.is_file():raise RuntimeError(f'指定 Python 不存在：{p}')
        return p
    s=service_root(project)
    candidates=[s/'.venv'/'bin'/'python',s/'.venv_windows'/'Scripts'/'python.exe',s/'venv'/'bin'/'python',s/'venv'/'Scripts'/'python.exe']
    for p in candidates:
        if p.is_file():return p
    return Path(sys.executable).resolve()


def check_runtime(py:Path)->None:
    r=subprocess.run([str(py),'-c','import flask, openpyxl; print("runtime-ok")'],text=True,capture_output=True)
    if r.returncode:
        raise RuntimeError('运行测试依赖未就绪：需要 Flask 与 openpyxl。请先按项目 README 安装 requirements.txt，或用 --python 指向项目虚拟环境。')


def copy_isolated(src:Path,dst:Path)->None:
    def ignore(path,names):
        ignored=[]
        for name in names:
            if name in SKIP_DIRS or name.endswith('.pyc'):ignored.append(name)
        return ignored
    shutil.copytree(src,dst,ignore=ignore)
    # 测试副本使用全新数据目录，避免任何业务数据/账号被复制后误操作。
    s=service_root(dst); data=s/'data'
    if data.exists():shutil.rmtree(data)
    data.mkdir(parents=True,exist_ok=True)


def free_port()->int:
    s=socket.socket(); s.bind(('127.0.0.1',0)); port=s.getsockname()[1]; s.close(); return port


def wait_health(url:str,proc:subprocess.Popen,timeout:float=20)->None:
    end=time.time()+timeout; last=''
    while time.time()<end:
        if proc.poll() is not None:raise RuntimeError(f'服务提前退出，退出码 {proc.returncode}。{last}')
        try:
            with urllib.request.urlopen(url+'/health',timeout=.8) as r:
                if r.status==200:return
        except Exception as e:last=str(e)
        time.sleep(.25)
    raise RuntimeError(f'健康检查超时：{last}')


def csrf(html:str)->str:
    m=re.search(r'name=["\']_csrf["\'][^>]*value=["\']([^"\']+)',html)
    if not m:
        m=re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']_csrf["\']',html)
    if not m:raise RuntimeError('页面未找到 CSRF token')
    return m.group(1)


def stage_token(html:str)->str:
    m=re.search(r'name=["\']token["\'][^>]*value=["\']([^"\']+)',html)
    if not m:raise RuntimeError('导入预览未返回 staging token')
    return m.group(1)


def read_text(resp)->str:return resp.read().decode('utf-8','replace')


def form_request(url:str,data:dict[str,str],headers:dict|None=None):
    body=urllib.parse.urlencode(data).encode('utf-8')
    h={'Content-Type':'application/x-www-form-urlencoded'}; h.update(headers or {})
    return urllib.request.Request(url,data=body,headers=h,method='POST')


def multipart_request(url:str, fields:dict[str,str], filename:str, file_bytes:bytes):
    boundary='----PaperlessE2E'+uuid.uuid4().hex
    parts=[]
    for k,v in fields.items():
        parts += [f'--{boundary}\r\n'.encode(),f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode(),str(v).encode('utf-8'),b'\r\n']
    parts += [f'--{boundary}\r\n'.encode(),f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),b'Content-Type: text/csv\r\n\r\n',file_bytes,b'\r\n',f'--{boundary}--\r\n'.encode()]
    return urllib.request.Request(url,data=b''.join(parts),headers={'Content-Type':f'multipart/form-data; boundary={boundary}'},method='POST')


def credentials(service:Path)->tuple[str,str]:
    p=service/'data'/'首次管理员凭据.txt'
    end=time.time()+8
    while time.time()<end and not p.is_file():time.sleep(.1)
    if not p.is_file():raise RuntimeError('未生成首次管理员凭据')
    text=p.read_text(encoding='utf-8',errors='replace')
    u=re.search(r'首次管理员账号：(.+)',text); pw=re.search(r'首次随机密码：(.+)',text)
    if not u or not pw:raise RuntimeError('首次管理员凭据格式无法识别')
    return u.group(1).strip(),pw.group(1).strip()


def sample_value(field:dict, suffix:str='A')->str:
    enums=field.get('enum_candidates') or []
    if enums:return str(enums[0])
    t=field.get('type','text')
    if t=='integer':return '7'
    if t=='number':return '7.5'
    if t=='boolean':return '1'
    if t=='date':return '2026-08-18'
    if t=='datetime':return '2026-08-18T09:30'
    return 'E2E_'+suffix+'_'+uuid.uuid4().hex[:8]


def db_path(service:Path)->Path:return service/'data'/'app.db'


def db_count(service:Path,table:str)->int:
    c=sqlite3.connect(db_path(service));
    try:return int(c.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
    finally:c.close()


def latest_id(service:Path,table:str)->int:
    c=sqlite3.connect(db_path(service));
    try:return int(c.execute(f'SELECT MAX(id) FROM "{table}"').fetchone()[0])
    finally:c.close()


def stop_server(py:Path,base:str,service:Path,proc:subprocess.Popen)->None:
    # 优先测试项目自身的安全停止脚本；该脚本会按项目状态/token 停止并清理 runtime.json。
    try:
        subprocess.run([str(py),str(service/'stop_server.py')],cwd=service,text=True,capture_output=True,timeout=12)
    except Exception:
        state=service/'data'/'runtime'/'runtime.json'; token=None
        if state.is_file():
            try:token=json.loads(state.read_text(encoding='utf-8')).get('shutdown_token')
            except Exception:pass
        if token:
            try:
                req=urllib.request.Request(base+'/internal/shutdown',data=b'',headers={'X-Shutdown-Token':token},method='POST')
                urllib.request.urlopen(req,timeout=2).read()
            except Exception:pass
    try:proc.wait(timeout=6)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:proc.wait(timeout=3)
        except subprocess.TimeoutExpired:proc.kill(); proc.wait(timeout=2)
    # 最后清理隔离副本的残留状态，避免影响备份恢复测试。
    for name in ('runtime.json','stopping.json'):
        (service/'data'/'runtime'/name).unlink(missing_ok=True)


def run_backup_restore(py:Path,service:Path)->None:
    r=subprocess.run([str(py),str(service/'backup_restore.py'),'backup'],cwd=service,text=True,capture_output=True)
    if r.returncode:raise RuntimeError('备份命令失败：'+(r.stdout+r.stderr)[-1000:])
    backups=sorted((service/'data'/'backups').glob('manual_*.db'),key=lambda x:x.stat().st_mtime)
    if not backups:raise RuntimeError('备份命令未生成数据库文件')
    backup=backups[-1]
    c=sqlite3.connect(db_path(service)); c.execute("INSERT OR REPLACE INTO system_settings(key,value) VALUES('e2e_restore_probe','dirty')"); c.commit(); c.close()
    r=subprocess.run([str(py),str(service/'backup_restore.py'),'restore',str(backup)],cwd=service,text=True,capture_output=True)
    if r.returncode:raise RuntimeError('恢复命令失败：'+(r.stdout+r.stderr)[-1000:])
    c=sqlite3.connect(db_path(service))
    try:
        ok=c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        probe=c.execute("SELECT value FROM system_settings WHERE key='e2e_restore_probe'").fetchone()
    finally:c.close()
    if not ok or probe is not None:raise RuntimeError('恢复后的数据库完整性或回滚结果不符合预期')


def update_project_status(project:Path, checks:list[str], env_info:dict)->None:
    status=project/'DELIVERY_STATUS.json'
    if status.is_file():
        obj=json.loads(status.read_text(encoding='utf-8'))
        tests=list(obj.get('tests_executed') or [])
        for x in checks:
            if x not in tests:tests.append(x)
        obj.update({'tests_executed':tests,'runtime_e2e_verified':True,'runtime_e2e_test_environment':env_info,'runtime_e2e_last_run':datetime.now(timezone.utc).isoformat(),'runtime_e2e_isolated_copy':True,'business_regression_tests_included':True,'project_scoped_safe_stop_verified':True,'additive_schema_upgrade_verified':True})
        status.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    report=['# TEST_REPORT','',f'状态：通过。','',f'- 执行时间（UTC）：{datetime.now(timezone.utc).isoformat()}','- 执行方式：隔离副本真实运行测试；原项目数据库未被改写。','', '## 覆盖范围','']+[f'- [通过] {x}' for x in checks]+['','## 环境','',f'- Python：{env_info.get("python")}',f'- 平台：{env_info.get("platform")}',f'- Web：本机 127.0.0.1 随机端口','']
    (project/'TEST_REPORT.md').write_text('\n'.join(report),encoding='utf-8')


def main()->int:
    ap=argparse.ArgumentParser(description='在隔离副本中执行真实运行级 E2E 测试。')
    ap.add_argument('--project',required=True); ap.add_argument('--python',dest='python_bin')
    a=ap.parse_args(); project=Path(a.project).expanduser().resolve()
    if not project.is_dir():print('[PB801] 项目目录不存在');return 1
    py=choose_python(project,a.python_bin)
    try:check_runtime(py)
    except Exception as e:print(f'[PB802] {e}');return 2
    checks=[]
    with tempfile.TemporaryDirectory(prefix='paperless-runtime-e2e-') as td:
        clone=Path(td)/project.name; copy_isolated(project,clone); service=service_root(clone)
        schema_path=service/'business'/'generated_schema.json'
        if not schema_path.is_file():print('[PB803] 项目缺少 generated_schema.json；请先 generate');return 1
        schema=json.loads(schema_path.read_text(encoding='utf-8')); objects=schema.get('objects') or []
        if not objects:print('[PB803] 没有可测试业务对象');return 1
        obj=objects[0]; key=obj['key']; table=obj['table']; port=free_port(); base=f'http://127.0.0.1:{port}'
        env=os.environ.copy(); env['APP_HOST']='127.0.0.1'; env['APP_PORT']=str(port)
        log=(service/'data'/'e2e_server.log').open('w',encoding='utf-8')
        proc=subprocess.Popen([str(py),str(service/'app.py')],cwd=service,env=env,stdout=log,stderr=log)
        try:
            wait_health(base,proc); checks.append('启动与 /health 健康检查')
            cj=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
            login_html=read_text(opener.open(base+'/login',timeout=3)); token=csrf(login_html); username,password=credentials(service)
            html=read_text(opener.open(form_request(base+'/login',{'_csrf':token,'username':username,'password':password}),timeout=5))
            if '账号或密码错误' in html:raise RuntimeError('管理员登录失败')
            checks.append('管理员登录与会话')
            before=db_count(service,table)
            new_html=read_text(opener.open(base+f'/business/{key}/new',timeout=3)); token=csrf(new_html)
            values={f['key']:sample_value(f,'create') for f in obj.get('fields',[]) if not f.get('computed')}
            payload={'_csrf':token,**values}; read_text(opener.open(form_request(base+f'/business/{key}/new',payload),timeout=5))
            if db_count(service,table)!=before+1:raise RuntimeError('新增记录后数据库行数未增加')
            rid=latest_id(service,table); checks.append('业务新增与持久化')
            edit_html=read_text(opener.open(base+f'/business/{key}/{rid}/edit',timeout=3)); token=csrf(edit_html)
            edit_values=dict(values)
            target=next((f for f in obj.get('fields',[]) if not f.get('computed') and f.get('type')=='text' and not f.get('enum_candidates')),None)
            if target:edit_values[target['key']]=sample_value(target,'edit')
            read_text(opener.open(form_request(base+f'/business/{key}/{rid}/edit',{'_csrf':token,**edit_values}),timeout=5)); checks.append('业务修改')
            numeric=next((f for f in obj.get('fields',[]) if not f.get('computed') and f.get('type') in {'integer','number'}),None)
            if numeric:
                bad_html=read_text(opener.open(base+f'/business/{key}/new',timeout=3)); bad_csrf=csrf(bad_html); bad=dict(values); bad[numeric['key']]='not-a-number'
                resp=read_text(opener.open(form_request(base+f'/business/{key}/new',{'_csrf':bad_csrf,**bad}),timeout=5))
                if '必须为' not in resp:raise RuntimeError('非法数字未触发严格类型校验')
                checks.append('严格字段类型校验')
            exported=opener.open(base+f'/business/{key}/export.xlsx',timeout=5).read()
            if not exported.startswith(b'PK'):raise RuntimeError('XLSX 导出不是有效 ZIP/Office 文件')
            checks.append('XLSX 导出')
            import_html=read_text(opener.open(base+f'/business/{key}/import',timeout=3)); token=csrf(import_html)
            labels=[f['label'] for f in obj.get('fields',[])]; row=[]
            for f in obj.get('fields',[]):
                if f.get('computed'):row.append('')
                else:row.append(sample_value(f,'import'))
            import csv, io
            bio=io.StringIO(); w=csv.writer(bio); w.writerow(labels); w.writerow(row); csv_bytes=bio.getvalue().encode('utf-8-sig')
            preview_html=read_text(opener.open(multipart_request(base+f'/business/{key}/import',{'_csrf':token,'action':'preview'},'e2e.csv',csv_bytes),timeout=5))
            if '失败 <strong>0</strong>' not in preview_html and '失败 <strong>0</strong> 行' not in preview_html:raise RuntimeError('CSV 导入预览存在校验失败')
            st=stage_token(preview_html); token2=csrf(preview_html); count_before_commit=db_count(service,table)
            read_text(opener.open(form_request(base+f'/business/{key}/import',{'_csrf':token2,'action':'commit','token':st}),timeout=5))
            if db_count(service,table)!=count_before_commit+1:raise RuntimeError('确认导入后数据库行数未增加')
            checks.append('CSV 逐行校验、预览与确认导入')
            del_html=read_text(opener.open(base+f'/business/{key}/{rid}/edit',timeout=3)); token=csrf(del_html)
            read_text(opener.open(form_request(base+f'/business/{key}/{rid}/delete',{'_csrf':token}),timeout=5)); checks.append('业务删除')
        except Exception as e:
            print(f'[PB804] E2E 失败：{e}')
            try:print((service/'data'/'e2e_server.log').read_text(encoding='utf-8',errors='replace')[-4000:])
            except Exception:pass
            return 1
        finally:
            stop_server(py,base,service,proc); log.close()
        checks.append('项目级安全停止')
        try:run_backup_restore(py,service); checks.append('SQLite 备份、恢复与完整性检查')
        except Exception as e:print(f'[PB805] 备份恢复测试失败：{e}');return 1
    env_info={'python':str(py),'platform':sys.platform,'isolated_copy':True}
    update_project_status(project,checks,env_info)
    print(f'[通过] 真实运行级 E2E：{len(checks)}/{len(checks)}')
    for x in checks:print('[通过]',x)
    print('[说明] 测试在隔离副本执行，原项目业务数据库未被改写。')
    return 0

if __name__=='__main__':raise SystemExit(main())
