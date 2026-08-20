#!/usr/bin/env python3
"""静态验证完整本地部署系统契约；不执行用户项目代码。"""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path

def exists_any(root,names): return any(p.is_file() and p.name in names for p in root.rglob('*'))
def read_any(root,names):
    for p in root.rglob('*'):
        if p.is_file() and p.name in names:
            try: return p,p.read_text(encoding='utf-8',errors='replace')
            except OSError: pass
    return None,''
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--strict',action='store_true'); ap.add_argument('--json-report'); a=ap.parse_args(); root=Path(a.project); errors=[]; warnings=[]; notes=[]
    if not root.is_dir(): print('[PB001] 项目目录不存在'); return 1
    py=[p for p in root.rglob('*.py') if '.venv' not in p.parts and 'vendor' not in p.parts]
    if not py: errors.append('缺少第一方 Python 源码')
    else: notes.append(f'第一方 Python 源码：{len(py)} 个')
    req={'主入口':['app.py','server.py','main.py'],'EXE入口':['exe_entry.py'],'EXE构建脚本':['build_exe_windows.py'],'备份恢复':['backup_restore.py'],'Windows启动':['start_windows.bat','start-windows.bat'],'Windows停止':['stop_windows.bat','stop-windows.bat'],'一键诊断':['诊断_一键诊断.bat','diagnose_windows.bat'],'目标电脑验收':['验收_目标电脑.bat','target_pc_acceptance.py'],'运行说明':['README_运行说明.md','使用说明.md'],'依赖清单':['requirements.txt']}
    for label,names in req.items():
        if not exists_any(root,names): (errors if a.strict or label not in {'一键诊断','目标电脑验收','依赖清单'} else warnings).append(f'缺少{label}：{names}')
    starts=[p for p in root.rglob('*') if p.is_file() and p.name in {'start_windows.bat','start-windows.bat'}]; stops=[p for p in root.rglob('*') if p.is_file() and p.name in {'stop_windows.bat','stop-windows.bat'}]
    if starts and stops and not any(s.parent==t.parent for s in starts for t in stops): errors.append('Windows 启动与停止脚本未成对放在同一目录')
    for p in stops:
        txt=p.read_text(encoding='utf-8',errors='replace').lower()
        bad=[r'taskkill\s+[^\r\n]*/im\s+python(?:w)?\.exe',r'killall\s+python',r'pkill\s+[^\r\n]*python']
        if any(re.search(x,txt) for x in bad): errors.append(f'{p.relative_to(root)} 使用全局结束 Python 进程的危险停止方式')
        if a.strict and not any(k in txt for k in ('pid','process_id','server.pid','app.pid')): warnings.append(f'{p.relative_to(root)} 未发现 PID/唯一实例标识字样，请人工确认只停止本项目')
    if not list(root.rglob('*.spec')): errors.append('缺少 PyInstaller .spec')
    for f in ['DELIVERY_STATUS.json','PY_SOURCE_MANIFEST.json','FILES_SHA256.txt','TEST_REPORT.md']:
        if not (root/f).is_file(): errors.append(f'缺少 {f}')
    status=root/'DELIVERY_STATUS.json'
    if status.is_file():
        try:
            obj=json.loads(status.read_text(encoding='utf-8'))
            if obj.get('windows_exe_runtime_verified') is True and not obj.get('exe_binary_included'): errors.append('windows_exe_runtime_verified=true 但 exe_binary_included 不是 true')
            for k in ('exe_build_source_included','python_source_included'):
                if obj.get(k) is not True: errors.append(f'DELIVERY_STATUS 未确认 {k}')
            for k in ('diagnostic_bundle_included','target_pc_acceptance_included','target_pc_smoke_verified','input_files_silently_skipped','runtime_e2e_verified'):
                if k not in obj: (errors if a.strict else warnings).append(f'DELIVERY_STATUS 缺少 {k}')
            if obj.get('input_files_silently_skipped',0)!=0: errors.append('input_files_silently_skipped 必须为 0')
            if obj.get('target_pc_smoke_verified') is True and not obj.get('target_pc_test_environment'): errors.append('目标电脑标记已验证但未记录测试环境')
            if a.strict:
                if not obj.get('tests_executed'): errors.append('严格验收要求 tests_executed 非空；请先执行 run_skill.py test')
                if obj.get('runtime_e2e_verified') is not True: errors.append('严格验收要求 runtime_e2e_verified=true；静态检查不能替代真实运行测试')
                if obj.get('runtime_e2e_verified') is True and not obj.get('runtime_e2e_test_environment'): errors.append('runtime_e2e_verified=true 但未记录运行测试环境')
        except Exception as e: errors.append(f'DELIVERY_STATUS.json 无法解析：{e}')
    test_report=root/'TEST_REPORT.md'
    if test_report.is_file():
        tt=test_report.read_text(encoding='utf-8',errors='replace').lower()
        if a.strict and ('状态：未执行' in tt or 'status: not run' in tt or 'not_tested' in tt): errors.append('TEST_REPORT 仍标记为未执行；严格验收不通过')
    readme_p,readme=read_any(root,['README_运行说明.md','使用说明.md'])
    if readme:
        for word in ('启动','停止','诊断','验收'):
            if word not in readme: (errors if a.strict else warnings).append(f'{readme_p.relative_to(root)} 未说明“{word}”')
    report={'schema_version':'1.0','project':str(root.resolve()),'strict':bool(a.strict),'passed':not errors,'notes':notes,'warnings':warnings,'errors':errors}
    if a.json_report:
        out=Path(a.json_report).expanduser(); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for n in notes: print('[通过]',n)
    for w in warnings: print('[警告]',w)
    if errors:
        print(f'[PB401] 本地部署契约验收失败，共 {len(errors)} 项'); [print('-',e) for e in errors]; return 1
    print('[通过] 完整本地部署契约静态检查通过。' + (' 严格模式。' if a.strict else '')); return 0
if __name__=='__main__': sys.exit(main())
