#!/usr/bin/env python3
"""统一命令入口。仅路由到现有脚本，不替换既有脚本职责。"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def call(script: str, args: list[str]) -> int:
    cmd=[sys.executable, str(ROOT/script), *args]
    print('[运行]', ' '.join(cmd))
    p=subprocess.run(cmd)
    return p.returncode

def main() -> int:
    ap=argparse.ArgumentParser(description='纸质表单电子化系统生成器统一入口')
    sub=ap.add_subparsers(dest='command', required=True)

    a=sub.add_parser('analyze', help='只读分析资料并创建工作区')
    a.add_argument('source')
    a.add_argument('--output', required=True)
    a.add_argument('--profile', default='auto')
    a.add_argument('--system-name', default='待识别本地业务系统')
    a.add_argument('--deployment-mode', choices=['local_or_lan','portable_full'], default='local_or_lan')
    a.add_argument('--network-mode', choices=['auto','offline_core','lan','online_optional'], default='auto')
    a.add_argument('--macos-client', action='store_true')
    a.add_argument('--runtime-strategy', choices=['self_bootstrap_venv','bundled_python','windows_exe','inherit_existing','source_only'], default='self_bootstrap_venv')
    a.add_argument('--package-runtime-dirs', action='store_true')

    a=sub.add_parser('scaffold', help='根据已确认 system-spec 生成工程骨架')
    a.add_argument('--spec', required=True); a.add_argument('--output', required=True); a.add_argument('--force', action='store_true')

    a=sub.add_parser('generate', help='根据 system-spec 自动生成完整业务模块')
    a.add_argument('--spec', required=True); a.add_argument('--output', required=True); a.add_argument('--force', action='store_true')

    a=sub.add_parser('validate', help='严格验收本地交付包')
    a.add_argument('--project', required=True); a.add_argument('--strict', action='store_true'); a.add_argument('--json-report')

    a=sub.add_parser('diagnose', help='统一诊断材料和项目')
    a.add_argument('--source'); a.add_argument('--project'); a.add_argument('--strict', action='store_true'); a.add_argument('--json-report')

    a=sub.add_parser('package', help='测试/验收通过后最终打包')
    a.add_argument('--project', required=True); a.add_argument('--output', required=True)

    a=sub.add_parser('test', help='在隔离副本中执行真实运行级 E2E 测试')
    a.add_argument('--project', required=True); a.add_argument('--python', dest='python_bin')

    a=sub.add_parser('upgrade', help='对既有生成系统做差异分析并创建安全升级副本')
    a.add_argument('--project', required=True); a.add_argument('--spec', required=True); a.add_argument('--output', required=True)
    a.add_argument('--plan-only', action='store_true'); a.add_argument('--allow-breaking', action='store_true'); a.add_argument('--force', action='store_true')

    a=sub.add_parser('version', help='检查技能版本一致性')
    sub.add_parser('self-test', help='运行技能包自身冒烟测试，不访问网络、不修改用户项目')

    ns=ap.parse_args()
    if ns.command=='analyze':
        args=[ns.source,'--output',ns.output,'--profile',ns.profile,'--system-name',ns.system_name,'--deployment-mode',ns.deployment_mode,'--network-mode',ns.network_mode,'--runtime-strategy',ns.runtime_strategy]
        if ns.macos_client: args.append('--macos-client')
        if ns.package_runtime_dirs: args.append('--package-runtime-dirs')
        return call('bootstrap_generation.py',args)
    if ns.command=='scaffold':
        args=['--spec',ns.spec,'--output',ns.output]
        if ns.force: args.append('--force')
        return call('create_project_scaffold.py',args)
    if ns.command=='generate':
        args=['--spec',ns.spec,'--output',ns.output]
        if ns.force: args.append('--force')
        return call('generate_business_system.py',args)
    if ns.command=='validate':
        args=[ns.project]
        if ns.strict: args.append('--strict')
        if ns.json_report: args += ['--json-report',ns.json_report]
        return call('validate_local_bundle.py',args)
    if ns.command=='diagnose':
        args=[]
        if ns.source: args += ['--source',ns.source]
        if ns.project: args += ['--project',ns.project]
        if ns.strict: args.append('--strict')
        if ns.json_report: args += ['--json-report',ns.json_report]
        if not args: print('[PB001] diagnose 至少需要 --source 或 --project'); return 1
        return call('diagnose.py',args)
    if ns.command=='package':
        return call('finalize_delivery.py',[ns.project,'--output',ns.output])
    if ns.command=='test':
        args=['--project',ns.project]
        if ns.python_bin: args += ['--python',ns.python_bin]
        return call('runtime_e2e_test.py',args)
    if ns.command=='upgrade':
        args=['--project',ns.project,'--spec',ns.spec,'--output',ns.output]
        if ns.plan_only: args.append('--plan-only')
        if ns.allow_breaking: args.append('--allow-breaking')
        if ns.force: args.append('--force')
        return call('upgrade_system.py',args)
    if ns.command=='version':
        return call('check_version.py',[])
    if ns.command=='self-test':
        return call('self_test.py',[])
    return 1

if __name__=='__main__':
    raise SystemExit(main())
