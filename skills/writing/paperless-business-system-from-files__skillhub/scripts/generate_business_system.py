#!/usr/bin/env python3
"""根据 system-spec 自动生成可运行的业务模块，而不只生成空工程骨架。"""
from __future__ import annotations
import argparse, hashlib, json, py_compile, re, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'scripts'


def safe_ident(value:str,prefix:str)->str:
    s=re.sub(r'[^a-zA-Z0-9_]+','_',str(value or '')).strip('_').lower()
    if not s or s[0].isdigit():s=f'{prefix}_{s}' if s else prefix
    return s[:48]


def sqlite_type(field_type:str)->str:
    return {'integer':'INTEGER','boolean':'INTEGER','number':'REAL','date':'TEXT','datetime':'TEXT','text':'TEXT'}.get(str(field_type).lower(),'TEXT')


def ui_control(field_type:str, enum_candidates:list|None=None)->str:
    if enum_candidates:return 'select'
    return {'date':'date','datetime':'datetime-local','boolean':'boolean-select','integer':'number','number':'number'}.get(str(field_type).lower(),'text')


def compile_schema(spec:dict)->dict:
    objects=[]; global_rules=spec.get('calculation_rules') or []
    for oi,src in enumerate(spec.get('business_objects') or [],1):
        okey=safe_ident(src.get('key') or f'obj_{oi:03d}',f'obj_{oi:03d}')
        if not okey.startswith('obj_'): okey=f'obj_{oi:03d}'
        fields=[]; field_map={}
        for fi,f in enumerate(src.get('fields') or [],1):
            fkey=safe_ident(f.get('key') or f'c{fi:02d}',f'c{fi:02d}')
            if not re.fullmatch(r'c\d+',fkey):fkey=f'c{fi:02d}'
            field_map[str(f.get('key') or fkey)]=fkey
            ftype=str(f.get('type') or 'text').lower()
            enums=[str(x) for x in (f.get('enum_candidates') or []) if str(x).strip()][:20]
            required=bool(f.get('required_confirmed') or f.get('required') is True and f.get('evidence_level') in {'formal','user_confirmed'})
            fields.append({
                'key':fkey,'column':fkey,'label':str(f.get('label') or f'字段{fi}'),
                'type':ftype,'required':required,'nullable':bool(f.get('nullable',not required)),
                'candidate_unique':bool(f.get('candidate_unique')),'computed':False,
                'enum_candidates':enums,'ui_control':ui_control(ftype,enums),
                'validation':{'required':required,'type':ftype,'enum':enums},
                'source':f.get('evidence') or f.get('source')
            })
        if not fields:continue
        calculations=[]
        rules=list(src.get('calculation_rules') or [])+[r for r in global_rules if str(r.get('object_key'))==str(src.get('key'))]
        seen=set()
        for r in rules:
            original_target=str(r.get('target_field') or '')
            target=field_map.get(original_target,original_target)
            expr=r.get('expression')
            if not target or not expr or target not in {f['key'] for f in fields}:continue
            # 将原字段 key 映射到生成字段 key。
            for old,new in sorted(field_map.items(),key=lambda x:-len(x[0])):
                expr=re.sub(rf'\b{re.escape(old)}\b',new,str(expr))
            if not re.fullmatch(r'[a-zA-Z0-9_+\-*/()., <>=]+',expr):continue
            sig=(target,expr)
            if sig in seen:continue
            seen.add(sig); calculations.append({'target_field':target,'expression':expr.lower(),'source_formula':r.get('original_formula'),'evidence':r.get('evidence')})
        computed={r['target_field'] for r in calculations}
        for f in fields:
            if f['key'] in computed:f['computed']=True
        confirmed=[]
        for keys in src.get('confirmed_unique_keys') or []:
            mapped=[field_map.get(str(k),str(k)) for k in keys]
            if mapped and all(k in {f['key'] for f in fields} for k in mapped):confirmed.append(mapped)
        objects.append({'key':okey,'label':str(src.get('label') or f'业务对象{oi}'),'table':f'biz_{okey}','fields':fields,'calculations':calculations,'confirmed_unique_keys':confirmed,'source':src.get('source'),'confidence_score':src.get('confidence_score')})
    return {'schema_version':'1.1','system_name':(spec.get('system') or {}).get('name','本地业务系统'),'objects':objects,'relationships':spec.get('relationships') or [],'import_rules':spec.get('import_rules') or {},'generated_capabilities':['crud','search','pagination','typed_forms','strict_type_validation','xlsx_csv_import_preview','row_level_import_validation','xlsx_export','rbac','audit','server_side_calculation','additive_schema_upgrade']}


def migration_source(schema:dict)->str:
    parts=[]; field_defs={}; unique_defs={}
    for idx,o in enumerate(schema.get('objects',[]),1):
        cols=[]; field_defs[o['table']]={}
        for f in o['fields']:
            typ=sqlite_type(f['type'])
            cols.append(f"{f['column']} {typ}")
            field_defs[o['table']][f['column']]=typ
        uniques=[f"UNIQUE ({','.join(keys)})" for keys in o.get('confirmed_unique_keys',[]) if keys]
        extra=(','+'\n'+','.join(uniques)) if uniques else ''
        sql=(f"CREATE TABLE IF NOT EXISTS {o['table']}(\n"
             "id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
             + ',\n'.join(cols)
             + ",\ncreated_by INTEGER,\nupdated_by INTEGER,\n"
             "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
             "updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
             + extra + "\n);")
        parts.append((f'1000_business_{idx:03d}',sql))
        unique_defs[o['table']]=o.get('confirmed_unique_keys',[])
    lines=[
        '# 自动生成；支持对既有 SQLite 数据库进行非破坏式“新增表/新增字段”迁移。',
        '# 删除字段、改类型等破坏性变更必须经过 upgrade diff 人工确认。',
        'MIGRATIONS='+repr(parts),
        'FIELD_DEFS='+repr(field_defs),
        'UNIQUE_DEFS='+repr(unique_defs),
        '',
        'def _q(name):',
        "    return '\"'+str(name).replace('\\\"','\\\"\\\"')+'\\\"'",
        '',
        'def ensure_business_schema(conn):',
        '    for table, fields in FIELD_DEFS.items():',
        '        existing={r[1] for r in conn.execute(f"PRAGMA table_info({_q(table)})").fetchall()}',
        '        if not existing:',
        '            continue',
        '        for col, typ in fields.items():',
        '            if col not in existing:',
        '                conn.execute(f"ALTER TABLE {_q(table)} ADD COLUMN {_q(col)} {typ}")',
        '        for n, keys in enumerate(UNIQUE_DEFS.get(table,[]),1):',
        '            if not keys: continue',
        "            idx='ux_'+table+'_'+str(n)",
        "            cols=','.join(_q(k) for k in keys)",
        '            conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {_q(idx)} ON {_q(table)} ({cols})")',
        ''
    ]
    return '\n'.join(lines)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def refresh_generated_metadata(project:Path)->None:
    py=[]
    for p in sorted(project.rglob('*.py')):
        if any(x in p.parts for x in ('.venv','venv','.venv_windows','vendor','__pycache__')):continue
        py_compile.compile(str(p),doraise=True)
        py.append({'path':p.relative_to(project).as_posix(),'sha256':sha256_file(p)})
    (project/'PY_SOURCE_MANIFEST.json').write_text(json.dumps({'schema_version':'1.1','first_party':py},ensure_ascii=False,indent=2),encoding='utf-8')
    status=project/'DELIVERY_STATUS.json'
    if status.is_file():
        obj=json.loads(status.read_text(encoding='utf-8'))
        obj.update({'python_source_included':bool(py),'exe_build_source_included':any(p.name=='build_exe_windows.py' for p in project.rglob('*.py')) and bool(list(project.rglob('*.spec'))),'diagnostic_bundle_included':any(p.name=='diagnose_local.py' for p in project.rglob('*.py')),'target_pc_acceptance_included':any(p.name=='target_pc_acceptance.py' for p in project.rglob('*.py')),'schema_migrations_included':True})
        status.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    hp=project/'FILES_SHA256.txt'; rows=[]
    for f in sorted(project.rglob('*')):
        if not f.is_file() or f==hp or f.suffix=='.pyc' or any(x in f.parts for x in ('.venv','venv','.venv_windows','vendor','__pycache__')):continue
        rows.append(f'{sha256_file(f)}  {f.relative_to(project).as_posix()}')
    hp.write_text('\n'.join(rows)+'\n',encoding='utf-8')

def main()->int:
    ap=argparse.ArgumentParser(description='根据 system-spec 生成完整业务系统（骨架 + 业务模块）。')
    ap.add_argument('--spec',required=True); ap.add_argument('--output',required=True); ap.add_argument('--force',action='store_true')
    a=ap.parse_args(); spec_path=Path(a.spec).expanduser(); out=Path(a.output).expanduser()
    if not spec_path.is_file():print('[PB701] system-spec.json 不存在');return 1
    try:spec=json.loads(spec_path.read_text(encoding='utf-8'))
    except Exception as e:print(f'[PB702] system-spec.json 无法读取：{e}');return 1
    schema=compile_schema(spec)
    if not schema['objects']:
        print('[PB703] system-spec 中没有可生成的 business_objects。请先运行 analyze，让深度业务模型提取字段；或手工补充业务对象。');return 1
    cmd=[sys.executable,str(S/'create_project_scaffold.py'),'--spec',str(spec_path),'--output',str(out)]
    if a.force:cmd.append('--force')
    r=subprocess.run(cmd)
    if r.returncode:return r.returncode
    # portable_full 的服务端代码位于 01_服务端_完整程序，否则就在根目录。
    service=out/'01_服务端_完整程序' if (out/'01_服务端_完整程序').is_dir() else out
    business=service/'business'; business.mkdir(parents=True,exist_ok=True)
    (business/'generated_schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
    (business/'generated_migrations.py').write_text(migration_source(schema),encoding='utf-8')
    report=['# AUTO_GENERATION_REPORT','',f'- 已生成业务对象：**{len(schema["objects"])}**',f'- 已生成字段：**{sum(len(o["fields"]) for o in schema["objects"])}**',f'- 可自动执行公式：**{sum(len(o["calculations"]) for o in schema["objects"])}**','','## 已生成能力','']+[f'- {x}' for x in schema['generated_capabilities']]+['','## 约束','- 候选唯一键不会自动升级为数据库 UNIQUE；只有 `confirmed_unique_keys` 才会建立正式唯一约束。','- 无法安全转换的 Excel 公式只保留在业务模型证据中，不会静默计算错误结果。','- 审批链、字段级权限和正式统计口径如果没有证据，仍保持待确认。','- 已支持新增表/新增字段的非破坏式 SQLite 升级；删除字段、改类型等破坏性变化必须经 upgrade diff 确认。','']
    (out/'AUTO_GENERATION_REPORT.md').write_text('\n'.join(report),encoding='utf-8')
    baseline=out/'GENERATION_BASELINE.json'
    if baseline.is_file():
        obj=json.loads(baseline.read_text(encoding='utf-8')); obj.update({'business_modules_generated':True,'generated_business_objects':len(schema['objects']),'generated_business_fields':sum(len(o['fields']) for o in schema['objects']),'auto_generation_report':'AUTO_GENERATION_REPORT.md'}); baseline.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    refresh_generated_metadata(out)
    print(f'[完成] 已自动生成业务系统：{out.resolve()}')
    print(f'[生成] 业务对象 {len(schema["objects"])} 个，字段 {sum(len(o["fields"]) for o in schema["objects"])} 个，公式 {sum(len(o["calculations"]) for o in schema["objects"])} 条。')
    return 0

if __name__=='__main__':raise SystemExit(main())
