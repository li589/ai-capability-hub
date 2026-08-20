#!/usr/bin/env python3
"""一键诊断技能包、输入材料和系统交付；优先给可执行修复信息。"""
from __future__ import annotations
import argparse,json,re,subprocess,sys,tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Any
S=Path(__file__).resolve().parent; TZ=timezone(timedelta(hours=8)); CODE_RE=re.compile(r'\[(PB\d{3})\]')

def run_step(name,cmd):
    try: r=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
    except subprocess.TimeoutExpired: return {'name':name,'passed':False,'return_code':124,'error_code':'PB401','stdout':'','stderr':'步骤超过 300 秒','action':'缩小材料范围或检查卡住的文件','resume_point':name}
    combined='\n'.join(x for x in (r.stdout.strip(),r.stderr.strip()) if x); m=CODE_RE.search(combined)
    return {'name':name,'passed':r.returncode==0,'return_code':r.returncode,'error_code':m.group(1) if m else ('PB999' if r.returncode else ''),'stdout':r.stdout.strip(),'stderr':r.stderr.strip(),'action':'按该步骤输出修复后重跑','resume_point':name}

def args():
    p=argparse.ArgumentParser(); p.add_argument('--source'); p.add_argument('--project'); p.add_argument('--strict',action='store_true'); p.add_argument('--json-report'); p.add_argument('--max-issues',type=int,default=20); return p.parse_args()

def main():
    a=args(); results=[]; file_issues=[]
    ok=sys.version_info>=(3,9); results.append({'name':'Python 运行环境','passed':ok,'return_code':0 if ok else 1,'error_code':'' if ok else 'PB201','stdout':f'Python {sys.version.split()[0]}','stderr':'' if ok else '需要 Python 3.9+','action':'安装匹配运行时','resume_point':'安装验证'})
    results.append(run_step('技能包版本',[sys.executable,str(S/'check_version.py')]))
    with tempfile.TemporaryDirectory(prefix='pbs-diagnose-') as td:
        if a.source:
            report_path=Path(td)/'input-profile.json'; cmd=[sys.executable,str(S/'profile_inputs.py'),str(Path(a.source).expanduser()),'--output',str(report_path),'--strict']
            step=run_step('输入文件画像',cmd); results.append(step)
            if report_path.is_file():
                try:
                    prof=json.loads(report_path.read_text(encoding='utf-8'))
                    for f in prof.get('files',[]):
                        for x in f.get('issues',[]): file_issues.append({'file':f.get('path',''),**x})
                except Exception as e: file_issues.append({'file':'input-profile.json','code':'PB999','severity':'error','stage':'诊断报告读取','location':'file','cause':repr(e),'impact':'无法汇总文件级问题','action':'直接查看 input-profile.json','resume_point':'输入文件画像'})
        if a.project:
            cmd=[sys.executable,str(S/'validate_delivery.py'),str(Path(a.project).expanduser())];
            if a.strict: cmd.append('--strict')
            results.append(run_step('系统交付静态验收',cmd))
            cmd2=[sys.executable,str(S/'validate_local_bundle.py'),str(Path(a.project).expanduser())];
            if a.strict: cmd2.append('--strict')
            results.append(run_step('本地部署契约',cmd2))
    passed=all(x['passed'] for x in results); failed=[x for x in results if not x['passed']]
    primary=next((x.get('code') for x in file_issues if x.get('severity')=='error' and x.get('code')),None) or next((x.get('error_code') for x in failed if x.get('error_code')),('' if passed else 'PB999'))
    last=next((x['name'] for x in reversed(results) if x['passed']),'无'); resume=(file_issues[0].get('resume_point') if file_issues else (failed[0].get('resume_point') if failed else '完成'))
    report={'schema_version':'1.2','generated_at':datetime.now(TZ).isoformat(),'timezone':'Asia/Shanghai','network_used':False,'passed':passed,'primary_error_code':primary,'last_passed_step':last,'recommended_resume_point':resume,'file_issues':file_issues,'steps':results}
    if a.json_report:
        out=Path(a.json_report).expanduser(); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for x in results:
        print(f'[{"通过" if x["passed"] else "失败"}] {x["name"]}')
        if x.get('stdout'): print('\n'.join('  '+line for line in x['stdout'].splitlines()[:40]))
        if x.get('stderr'): print('  '+x['stderr'])
    if file_issues:
        print('\n=== 文件级定位 ===')
        for x in file_issues[:max(a.max_issues,1)]:
            print(f'[{x.get("code","PB999")}] 文件：{x.get("file")}; 位置：{x.get("location")}; 阶段：{x.get("stage")}')
            print(f'  原因：{x.get("cause")}\n  影响：{x.get("impact")}\n  处理：{x.get("action")}\n  恢复点：{x.get("resume_point")}')
    if passed: print('[完成] 未发现阻断项；诊断未使用网络。'); return 0
    print(f'[{primary}] 诊断发现阻断项。\n处理：优先修复上方首个明确定位的问题，不必重新处理已通过步骤。\n恢复点：{resume}；最近通过：{last}。'); return 1
if __name__=='__main__': sys.exit(main())
