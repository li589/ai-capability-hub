#!/usr/bin/env python3
"""一次性初始化本次系统生成工作区；所有分析产物只在调用时创建。"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'scripts'
T=ROOT/'assets'/'templates'
KNOWN={'energy','pointwork','operations','production','quality','equipment','inventory','approval','general','composite'}


def run(script,*args):
    cmd=[sys.executable,str(S/script),*map(str,args)]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.returncode!=0:
        if r.stderr.strip(): print(r.stderr.strip())
        raise RuntimeError(f'{script} 执行失败，退出码 {r.returncode}')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


def write_quality(profile,out):
    lines=['# data-quality-report','',f'- 总体状态：**{profile.get("overall_status","unknown")}**',f'- 文件数：**{profile.get("summary",{}).get("total_files",0)}**',f'- 错误：**{profile.get("summary",{}).get("errors",0)}**',f'- 警告：**{profile.get("summary",{}).get("warnings",0)}**','', '## 文件问题','']
    count=0
    for f in profile.get('files',[]):
        for x in f.get('issues',[]):
            count+=1
            lines += [f'### {count}. `{f.get("path")}` — {x.get("severity","warning")}',f'- 错误码：`{x.get("code")}`',f'- 阶段：{x.get("stage")}',f'- 位置：{x.get("location")}',f'- 原因：{x.get("cause")}',f'- 影响：{x.get("impact")}',f'- 处理：{x.get("action")}',f'- 恢复点：{x.get("resume_point")}','']
    if not count: lines += ['- 未发现文件级阻断或警告。业务字段、公式和审批规则仍需继续比对。','']
    Path(out).write_text('\n'.join(lines),encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description='只读盘点输入并创建本次系统生成工作区。')
    ap.add_argument('source'); ap.add_argument('--output',required=True); ap.add_argument('--profile',default='auto'); ap.add_argument('--system-name',default='待识别本地业务系统'); ap.add_argument('--deployment-mode',choices=['local_or_lan','portable_full'],default='local_or_lan'); ap.add_argument('--network-mode',choices=['auto','offline_core','lan','online_optional'],default='auto'); ap.add_argument('--macos-client',action='store_true'); ap.add_argument('--runtime-strategy',choices=['self_bootstrap_venv','bundled_python','windows_exe','inherit_existing','source_only'],default='self_bootstrap_venv'); ap.add_argument('--package-runtime-dirs',action='store_true')
    a=ap.parse_args(); src=Path(a.source).expanduser(); out=Path(a.output).expanduser()
    if not src.exists(): print('[PB001] 输入路径不存在'); return 1
    if a.profile!='auto' and a.profile not in KNOWN: print(f'[PB001] 不支持的 profile：{a.profile}'); return 1
    # 运行结果不能写回输入目录内部，否则第二个分析步骤会把刚生成的报告误当成业务证据。
    if src.is_dir():
        try:
            out.resolve().relative_to(src.resolve())
            print('[PB001] --output 不能位于输入目录内部；请使用输入目录的同级工作目录，避免生成文件污染业务识别。'); return 1
        except ValueError:
            pass
    out.mkdir(parents=True,exist_ok=True)

    ip=out/'input-profile.json'; bm=out/'business-model.json'; bmr=out/'BUSINESS_MODEL_REPORT.md'; bp=out/'business-profile.json'; br=out/'BUSINESS_RECOGNITION_REPORT.md'
    run('profile_inputs.py',src,'--output',ip)
    run('extract_business_model.py',src,'--output',bm,'--report',bmr)
    run('detect_business_profile.py',src,'--model',bm,'--output',bp,'--report',br)
    input_obj=load(ip); model_obj=load(bm); business_obj=load(bp)
    selected=a.profile if a.profile!='auto' else business_obj.get('recommended_profile','general')
    if a.profile!='auto':
        business_obj['user_forced_profile']=a.profile
        business_obj['recommended_profile']=a.profile
        business_obj['instruction']='用户显式指定 Profile 优先；仍不得覆盖附件中的具体字段、公式、权限与审批事实。'
        save(bp,business_obj)
        with br.open('a',encoding='utf-8') as f: f.write(f'\n## 用户指定\n\n用户显式指定优先 Profile：`{a.profile}`。\n')

    cr=out/'INPUT_COMPLETENESS_REPORT.md'; cj=out/'input-completeness.json'
    run('assess_input_completeness.py',src,'--profile',selected,'--model',bm,'--output',cr,'--json-output',cj)
    completeness=load(cj); cj.unlink(missing_ok=True)

    mapping={'schema_version':'1.1','generated_at':datetime.now(timezone.utc).isoformat(),'source_root':str(src.resolve()),'files':[],'field_mappings':[],'note':'field_mappings 来自深度业务模型；候选唯一键/关系仍需按证据等级确认。'}
    for f in input_obj.get('files',[]):
        mapping['files'].append({'path':f.get('path'),'sha256':f.get('sha256'),'extension':f.get('extension'),'status':f.get('status'),'role':'candidate_evidence'})
    for o in model_obj.get('business_objects',[]):
        for fld in o.get('fields',[]):
            mapping['field_mappings'].append({'object_key':o.get('key'),'object_label':o.get('label'),'field_key':fld.get('key'),'field_label':fld.get('label'),'type':fld.get('type'),'source':fld.get('evidence'),'candidate_unique':fld.get('candidate_unique',False)})
    save(out/'source-file-mapping.json',mapping)
    write_quality(input_obj,out/'data-quality-report.md')

    missing=[x['topic'] for x in completeness.get('topics',[]) if not x.get('evidence_found')]
    missing += [q for q in model_obj.get('open_questions',[]) if q not in missing]
    assumptions=['# ASSUMPTIONS','', '- 初始化阶段不把缺少证据的关键规则自动设为正式业务规则。','']
    if missing:
        assumptions += ['## 待确认主题','']+[f'- {x}' for x in missing]+['']
    else: assumptions += ['- 当前自动证据检查未发现 Profile 主题缺口；仍需对具体字段、公式、权限和流程做业务级核对。','']
    (out/'ASSUMPTIONS.md').write_text('\n'.join(assumptions),encoding='utf-8')
    (out/'BUSINESS_CONFLICTS.md').write_text('# BUSINESS_CONFLICTS\n\n初始化阶段尚未对跨资料的具体业务规则做完逐项语义比对。\n\n- 已发现的文件解析错误/警告见 `data-quality-report.md`。\n- 后续若字段、公式、周期、权限、审批或历史口径互相冲突，必须在此记录来源、影响、采用规则和是否阻断。\n',encoding='utf-8')

    spec=load(T/'system-spec.template.json')
    spec['system']['name']=a.system_name
    spec['system']['deployment_mode']=a.deployment_mode
    spec['system']['network_mode']='offline_core' if a.network_mode=='auto' else a.network_mode
    spec['portable_full']['enabled']=(a.deployment_mode=='portable_full')
    spec['portable_full']['macos_client']=bool(a.macos_client)
    spec['portable_full']['runtime_strategy']=a.runtime_strategy
    spec['portable_full']['package_runtime_dirs']=bool(a.package_runtime_dirs)
    if a.macos_client and 'macOS 13+' not in spec['system']['target_os']: spec['system']['target_os'].append('macOS 13+')
    spec['system']['business_domains']=business_obj.get('strong_domains') or ([selected] if selected not in {'general','composite'} else [selected])
    spec['source_files']=[{'path':x.get('path'),'sha256':x.get('sha256'),'status':x.get('status')} for x in input_obj.get('files',[])]
    spec['business_objects']=model_obj.get('business_objects',[])
    spec['field_mappings']=mapping.get('field_mappings',[])
    spec['calculation_rules']=model_obj.get('calculation_rules',[])
    spec['relationships']=model_obj.get('relationships',[])
    spec['business_model']={'report':'BUSINESS_MODEL_REPORT.md','model_file':'business-model.json',**model_obj.get('summary',{})}
    spec['recognition']['recommended_profile']=selected; spec['recognition']['confidence_score']=business_obj.get('confidence_score')
    spec['input_completeness']['grade']=completeness.get('grade'); spec['input_completeness']['unconfirmed_critical_rules']=missing
    spec['open_questions']=missing[:]
    save(out/'system-spec.json',spec)

    status=load(T/'delivery-status.template.json')
    status['business_domains']=spec['system']['business_domains']; status['deployment_mode']=a.deployment_mode; status['portable_full_requested']=(a.deployment_mode=='portable_full'); status['portable_full_runtime_strategy']=spec.get('portable_full',{}).get('runtime_strategy') if a.deployment_mode=='portable_full' else None; status['business_recognition_report_included']=True; status['input_completeness_report_included']=True
    status['input_completeness_grade']=completeness.get('grade'); status['input_files_total']=input_obj.get('summary',{}).get('total_files',0); status['input_files_error']=input_obj.get('summary',{}).get('errors',0); status['input_files_silently_skipped']=input_obj.get('summary',{}).get('silently_skipped',0)
    save(out/'DELIVERY_STATUS.json',status)

    print(f'[完成] 已初始化工作区：{out.resolve()}')
    print(f'[下一步] 完善 {out/"system-spec.json"} 后生成/升级业务系统。')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as e: print(f'[PB999] 初始化失败：{e}'); sys.exit(1)
