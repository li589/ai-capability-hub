#!/usr/bin/env python3
"""技能包自身冒烟测试：覆盖业务理解、自动生成、验收闭环与非破坏式升级。"""
from __future__ import annotations
import importlib.util, json, sqlite3, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; S=ROOT/'scripts'

def run(cmd):
    p=subprocess.run([sys.executable,*cmd],cwd=ROOT,text=True,capture_output=True)
    return p.returncode,p.stdout,p.stderr

def write_csvs(src:Path):
    (src/'员工.csv').write_text('工号,姓名,部门\nE001,张三,生产\nE002,李四,质量\nE003,王五,生产\n',encoding='utf-8-sig')
    (src/'能耗记录.csv').write_text('员工编号,日期,用电量,产量\nE001,2026-08-16,100,50\nE001,2026-08-17,120,60\nE002,2026-08-18,90,45\n',encoding='utf-8-sig')

def import_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def main():
    checks=[]
    rc,out,err=run([str(S/'check_version.py')]); checks.append(('版本一致性',rc==0,out or err))
    rc,out,err=run([str(S/'run_skill.py'),'--help']); checks.append(('统一入口包含 test/upgrade',rc==0 and 'test' in out and 'upgrade' in out and 'generate' in out,out or err))
    with tempfile.TemporaryDirectory(prefix='paperless-skill-smoke-') as td:
        t=Path(td); src=t/'input'; work=t/'work'; project=t/'project'; upgraded=t/'upgraded'; src.mkdir(); write_csvs(src)
        rc,out,err=run([str(S/'run_skill.py'),'analyze',str(src),'--output',str(work),'--system-name','技能自测系统'])
        model=json.loads((work/'business-model.json').read_text(encoding='utf-8')) if (work/'business-model.json').is_file() else {}
        rels=model.get('relationships') or []
        relation_ok=any(r.get('sample_overlap_count',0)>=2 and r.get('confidence_score',0)>=80 for r in rels)
        checks.append(('业务关系增强推断',rc==0 and model.get('summary',{}).get('structured_objects',0)>=2 and relation_ok,out or err))
        rc,out,err=run([str(S/'run_skill.py'),'generate','--spec',str(work/'system-spec.json'),'--output',str(project)])
        service=project/'01_服务端_完整程序' if (project/'01_服务端_完整程序').is_dir() else project
        schema=json.loads((service/'business'/'generated_schema.json').read_text(encoding='utf-8')) if (service/'business'/'generated_schema.json').is_file() else {}
        fields=[f for o in schema.get('objects',[]) for f in o.get('fields',[])]
        gm=(service/'business'/'generated_migrations.py').read_text(encoding='utf-8') if (service/'business'/'generated_migrations.py').is_file() else ''
        checks.append(('智能表单/严格校验/增量迁移生成',rc==0 and fields and all('ui_control' in f and 'validation' in f for f in fields) and 'ensure_business_schema' in gm and 'strict_type_validation' in schema.get('generated_capabilities',[]),out or err))
        # 未运行 E2E 时，strict 必须拒绝，证明“静态通过 != 已测试”的旧漏洞已关闭。
        rc,out,err=run([str(S/'run_skill.py'),'validate','--project',str(project),'--strict'])
        checks.append(('严格验收阻止未测试项目',rc!=0 and ('runtime_e2e_verified' in out or 'tests_executed' in out or 'TEST_REPORT' in out),out or err))
        # 构造旧数据库，再给新规格增加一个字段，验证 upgrade 与 additive schema 补齐。
        old_schema=schema; first=old_schema['objects'][0]; db=service/'data'/'app.db'; db.parent.mkdir(parents=True,exist_ok=True)
        c=sqlite3.connect(db); cols=','.join(f'"{f["column"]}" TEXT' for f in first['fields']); c.execute(f'CREATE TABLE "{first["table"]}"(id INTEGER PRIMARY KEY AUTOINCREMENT,{cols},created_by INTEGER,updated_by INTEGER,created_at TEXT,updated_at TEXT)'); c.execute('CREATE TABLE preserve_probe(k TEXT PRIMARY KEY,v TEXT)'); c.execute("INSERT INTO preserve_probe VALUES('keep','yes')"); c.commit(); c.close()
        new_spec=json.loads((work/'system-spec.json').read_text(encoding='utf-8')); new_spec['business_objects'][0]['fields'].append({'key':'c99','label':'升级新增字段','type':'text','nullable':True,'candidate_unique':False,'examples':['A']})
        new_spec_path=t/'new-system-spec.json'; new_spec_path.write_text(json.dumps(new_spec,ensure_ascii=False,indent=2),encoding='utf-8')
        rc,out,err=run([str(S/'run_skill.py'),'upgrade','--project',str(project),'--spec',str(new_spec_path),'--output',str(upgraded)])
        up_service=upgraded/'01_服务端_完整程序' if (upgraded/'01_服务端_完整程序').is_dir() else upgraded
        up_db=up_service/'data'/'app.db'; additive_ok=False
        if rc==0 and up_db.is_file():
            gm_mod=import_module(up_service/'business'/'generated_migrations.py','generated_migrations_smoke')
            c=sqlite3.connect(up_db); gm_mod.ensure_business_schema(c); c.commit(); cols2={r[1] for r in c.execute(f'PRAGMA table_info("{first["table"]}")').fetchall()}; probe=c.execute("SELECT v FROM preserve_probe WHERE k='keep'").fetchone(); c.close(); additive_ok=('c99' in cols2 and probe and probe[0]=='yes')
        diff=json.loads((upgraded/'upgrade-diff.json').read_text(encoding='utf-8')) if (upgraded/'upgrade-diff.json').is_file() else {}
        checks.append(('非破坏式升级与数据保留',rc==0 and additive_ok and diff.get('summary',{}).get('safe_additive',0)>=1,out or err))
        rc,out,err=run([str(S/'runtime_e2e_test.py'),'--help']); checks.append(('真实运行 E2E 测试器可调用',rc==0 and '隔离副本' in out,out or err))
    failed=[x for x in checks if not x[1]]
    for name,ok,msg in checks: print(f"[{'通过' if ok else '失败'}] {name}")
    if failed:
        for name,_,msg in failed: print(f'--- {name} ---\n{msg}')
        return 1
    print(f'[通过] 技能冒烟测试完成：{len(checks)}/{len(checks)}')
    print('[说明] runtime E2E 的真实启动测试需项目运行环境已安装 Flask/openpyxl；self-test 只验证测试器本身与验收闭环。')
    return 0

if __name__=='__main__': raise SystemExit(main())
