#!/usr/bin/env python3
"""根据新 system-spec 对既有生成系统做差异分析，并创建非破坏式升级副本。"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; S=ROOT/'scripts'
SKIP_COPY={'__pycache__','.git','node_modules','.venv','venv','.venv_windows','portable_runtime'}


def load(path:Path)->dict:return json.loads(path.read_text(encoding='utf-8'))

def keyed(items):return {str(x.get('key')):x for x in (items or []) if x.get('key')}

def field_map(obj):return {str(x.get('key')):x for x in (obj.get('fields') or []) if x.get('key')}


def calc_signatures(obj):
    out=set()
    for r in obj.get('calculation_rules') or []:
        out.add((str(r.get('target_field')),str(r.get('expression') or r.get('original_formula') or '')))
    return out


def compare(old:dict,new:dict)->dict:
    safe=[]; review=[]; breaking=[]
    oo=keyed(old.get('business_objects')); nn=keyed(new.get('business_objects'))
    for k in sorted(nn.keys()-oo.keys()):safe.append({'kind':'object_added','object':k,'label':nn[k].get('label')})
    for k in sorted(oo.keys()-nn.keys()):breaking.append({'kind':'object_removed','object':k,'label':oo[k].get('label')})
    for k in sorted(oo.keys()&nn.keys()):
        a,b=oo[k],nn[k]; af,bf=field_map(a),field_map(b)
        if a.get('label')!=b.get('label'):review.append({'kind':'object_label_changed','object':k,'from':a.get('label'),'to':b.get('label')})
        for f in sorted(bf.keys()-af.keys()):safe.append({'kind':'field_added','object':k,'field':f,'label':bf[f].get('label'),'type':bf[f].get('type')})
        for f in sorted(af.keys()-bf.keys()):breaking.append({'kind':'field_removed','object':k,'field':f,'label':af[f].get('label')})
        for f in sorted(af.keys()&bf.keys()):
            x,y=af[f],bf[f]
            if str(x.get('type') or 'text')!=str(y.get('type') or 'text'):
                breaking.append({'kind':'field_type_changed','object':k,'field':f,'label':y.get('label'),'from':x.get('type'),'to':y.get('type')})
            if x.get('label')!=y.get('label'):review.append({'kind':'field_label_changed','object':k,'field':f,'from':x.get('label'),'to':y.get('label')})
            if bool(x.get('required'))!=bool(y.get('required')):review.append({'kind':'required_rule_changed','object':k,'field':f,'from':bool(x.get('required')),'to':bool(y.get('required'))})
        if (a.get('confirmed_unique_keys') or [])!=(b.get('confirmed_unique_keys') or []):review.append({'kind':'unique_constraint_changed','object':k,'from':a.get('confirmed_unique_keys') or [],'to':b.get('confirmed_unique_keys') or []})
        if calc_signatures(a)!=calc_signatures(b):review.append({'kind':'calculation_rules_changed','object':k})
    for topic in ('workflows','roles','permissions','relationships'):
        if (old.get(topic) or [])!=(new.get(topic) or []):review.append({'kind':topic+'_changed'})
    return {'schema_version':'1.0','generated_at':datetime.now(timezone.utc).isoformat(),'safe_additive':safe,'review_required':review,'breaking':breaking,'summary':{'safe_additive':len(safe),'review_required':len(review),'breaking':len(breaking),'can_auto_apply':not breaking}}


def render(diff:dict)->str:
    s=diff['summary']; lines=['# UPGRADE_DIFF_REPORT','',f'- 可安全新增：**{s["safe_additive"]}**',f'- 需业务复核：**{s["review_required"]}**',f'- 破坏性变化：**{s["breaking"]}**',f'- 可自动创建升级副本：**{"是" if s["can_auto_apply"] else "否"}**','','## 可安全新增','']
    lines += [f'- `{x.get("kind")}`：{json.dumps(x,ensure_ascii=False)}' for x in diff['safe_additive']] or ['- 无']
    lines += ['','## 需业务复核','']
    lines += [f'- `{x.get("kind")}`：{json.dumps(x,ensure_ascii=False)}' for x in diff['review_required']] or ['- 无']
    lines += ['','## 破坏性变化','']
    lines += [f'- `{x.get("kind")}`：{json.dumps(x,ensure_ascii=False)}' for x in diff['breaking']] or ['- 无']
    lines += ['','> 自动升级默认只接受新增表/新增字段等非破坏性变化。删除字段、删除对象、字段改类型必须显式 `--allow-breaking`，且仍建议先人工迁移演练。','']
    return '\n'.join(lines)


def copy_project(src:Path,dst:Path):
    def ignore(path,names):return [n for n in names if n in SKIP_COPY or n.endswith('.pyc')]
    shutil.copytree(src,dst,ignore=ignore)
    # 运行状态不能继承到升级副本。
    for p in dst.rglob('runtime.json'):p.unlink(missing_ok=True)
    for p in dst.rglob('stopping.json'):p.unlink(missing_ok=True)


def overlay(src:Path,dst:Path):
    for p in src.rglob('*'):
        rel=p.relative_to(src)
        if any(x in SKIP_COPY for x in rel.parts):continue
        if 'data' in rel.parts:continue
        target=dst/rel
        if p.is_dir():target.mkdir(parents=True,exist_ok=True)
        elif p.is_file():target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)


def main()->int:
    ap=argparse.ArgumentParser(description='对既有生成系统做差异分析并创建安全升级副本。')
    ap.add_argument('--project',required=True); ap.add_argument('--spec',required=True); ap.add_argument('--output',required=True)
    ap.add_argument('--plan-only',action='store_true'); ap.add_argument('--allow-breaking',action='store_true'); ap.add_argument('--force',action='store_true')
    a=ap.parse_args(); project=Path(a.project).expanduser().resolve(); spec_path=Path(a.spec).expanduser().resolve(); out=Path(a.output).expanduser().resolve()
    old_spec_path=project/'system-spec.json'
    if not project.is_dir() or not old_spec_path.is_file():print('[PB901] 既有项目缺少 system-spec.json');return 1
    if not spec_path.is_file():print('[PB902] 新 system-spec.json 不存在');return 1
    old,new=load(old_spec_path),load(spec_path); diff=compare(old,new)
    if out.exists():
        if not a.force:print('[PB903] 输出目录已存在；确认覆盖请加 --force');return 1
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out/'upgrade-diff.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'UPGRADE_DIFF_REPORT.md').write_text(render(diff),encoding='utf-8')
    if a.plan_only:
        print(f'[完成] 升级差异报告：{out.resolve()}');return 0
    if diff['breaking'] and not a.allow_breaking:
        print(f'[PB904] 检测到 {len(diff["breaking"])} 项破坏性变化，已停止自动升级。报告位于：{out}');return 1
    # 报告先放临时目录，正式输出需替换为项目副本。
    report_json=(out/'upgrade-diff.json').read_bytes(); report_md=(out/'UPGRADE_DIFF_REPORT.md').read_bytes(); shutil.rmtree(out)
    copy_project(project,out)
    (out/'system-spec.before-upgrade.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='paperless-upgrade-generate-') as td:
        fresh=Path(td)/'fresh'
        r=subprocess.run([sys.executable,str(S/'generate_business_system.py'),'--spec',str(spec_path),'--output',str(fresh)],text=True)
        if r.returncode:
            shutil.rmtree(out,ignore_errors=True);print('[PB905] 新规格生成失败，未留下半成品升级目录');return r.returncode
        overlay(fresh,out)
    (out/'system-spec.json').write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'upgrade-diff.json').write_bytes(report_json); (out/'UPGRADE_DIFF_REPORT.md').write_bytes(report_md)
    status=out/'DELIVERY_STATUS.json'
    if status.is_file():
        obj=load(status); obj.update({'tests_executed':[],'runtime_e2e_verified':False,'runtime_e2e_last_run':None,'runtime_e2e_test_environment':None,'upgrade_diff_report_included':True,'additive_schema_upgrade_verified':False,'zip_reextract_verified':False}); status.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'TEST_REPORT.md').write_text('# TEST_REPORT\n\n状态：未执行。升级副本必须重新运行 `run_skill.py test --project ...` 后再打包。\n',encoding='utf-8')
    print(f'[完成] 已创建升级副本：{out}')
    print(f'[差异] 安全新增 {diff["summary"]["safe_additive"]}，需复核 {diff["summary"]["review_required"]}，破坏性 {diff["summary"]["breaking"]}。')
    print('[下一步] 对升级副本执行 test，再执行 validate --strict。')
    return 0

if __name__=='__main__':raise SystemExit(main())
