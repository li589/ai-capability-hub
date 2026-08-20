#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from portable_full_support import SERVICE_DIR,WIN_CLIENT_DIR,MAC_CLIENT_DIR,REF_DIR,TEMPLATE_DIR,DOC_DIR

def any_name(root:Path,names): return any(p.is_file() and p.name in names for p in root.rglob('*'))
def main():
    ap=argparse.ArgumentParser(description='验证 V1.5.11 级 portable_full 完整部署包装。'); ap.add_argument('project'); ap.add_argument('--strict',action='store_true'); a=ap.parse_args()
    root=Path(a.project); errors=[]; warnings=[]
    if not root.is_dir(): print('[PB001] 项目目录不存在'); return 1
    specp=root/'system-spec.json'; statusp=root/'DELIVERY_STATUS.json'
    try: spec=json.loads(specp.read_text(encoding='utf-8'))
    except Exception as e: print(f'[PB451] system-spec.json 无法读取：{e}'); return 1
    cfg=spec.get('portable_full') or {}
    if (spec.get('system') or {}).get('deployment_mode')!='portable_full' and not cfg.get('enabled'): errors.append('system-spec 未声明 portable_full')
    for d in (SERVICE_DIR,WIN_CLIENT_DIR,REF_DIR,TEMPLATE_DIR,DOC_DIR):
        if not (root/d).is_dir(): errors.append(f'缺少完整部署目录：{d}')
    service=root/SERVICE_DIR
    if service.is_dir():
        checks={'服务端主入口':['app.py','server.py','main.py'],'服务端启动':['start_windows.bat'],'服务端停止':['stop_windows.bat'],'运行说明':['README_运行说明.md'],'备份恢复':['backup_restore.py'],'EXE构建':['build_exe_windows.py'],'诊断':['diagnose_local.py'],'目标机验收':['target_pc_acceptance.py']}
        for label,names in checks.items():
            if not any_name(service,names): errors.append(f'缺少{label}：{names}')
        for d in ('templates','static','data','logs'):
            if not (service/d).exists(): errors.append(f'服务端缺少 {d}/')
        if cfg.get('lan_helpers',True):
            for n in ('查看服务器内网地址_Windows.bat','开放当前端口_Windows.bat','当前服务器地址.txt','当前服务端口.txt'):
                if not (service/n).is_file(): errors.append(f'局域网辅助缺少：{n}')
    for n in ('一键启动_Windows.bat','一键停止_Windows.bat'):
        if not (root/n).is_file(): errors.append(f'根目录缺少 {n}')
    wc=root/WIN_CLIENT_DIR
    for n in ('server_url.txt','Windows客户端使用说明.txt','打开系统_Windows.vbs','设置服务器地址_Windows.vbs','测试服务器连接_Windows.vbs'):
        if not (wc/n).is_file(): errors.append(f'Windows 填写客户端缺少：{n}')
    cur=root/DOC_DIR/'00_当前版本'
    for n in ('VERSION.txt','更新摘要.txt'):
        if not (cur/n).is_file(): errors.append(f'版本区缺少：{n}')
    if cfg.get('macos_client'):
        mc=root/MAC_CLIENT_DIR
        for n in ('server_url.txt','macOS客户端使用说明.txt','打开系统_macOS.command','设置服务器地址_macOS.command','测试服务器连接_macOS.command'):
            if not (mc/n).is_file(): errors.append(f'macOS 填写客户端缺少：{n}')
    strategy=str(cfg.get('runtime_strategy') or '')
    if strategy not in {'self_bootstrap_venv','bundled_python','windows_exe','inherit_existing','source_only'}: errors.append(f'portable_full.runtime_strategy 非法或缺失：{strategy!r}')
    if strategy=='source_only': errors.append('runtime_strategy=source_only 不能作为 portable_full 完整运行交付')
    if strategy=='self_bootstrap_venv' and service.is_dir():
        if not (service/'launcher.py').is_file() or not (service/'requirements.txt').is_file(): errors.append('self_bootstrap_venv 缺少 launcher.py/requirements.txt')
    if strategy=='bundled_python' and not (service/'portable_runtime'/'python.exe').is_file(): errors.append('bundled_python 缺少 01_服务端_完整程序/portable_runtime/python.exe')
    if strategy=='windows_exe' and not list(service.rglob('*.exe')): errors.append('windows_exe 模式未发现已构建 EXE')
    try: status=json.loads(statusp.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'DELIVERY_STATUS.json 无法解析：{e}'); status={}
    if status:
        for k in ('portable_full_requested','portable_full_layout_included','windows_client_included'):
            if status.get(k) is not True: errors.append(f'DELIVERY_STATUS 未确认 {k}')
        if status.get('no_python_required_verified') is True:
            binary=bool(status.get('exe_binary_included') and status.get('windows_exe_runtime_verified'))
            portable=bool(status.get('portable_runtime_included') and status.get('portable_runtime_verified'))
            if not (binary or portable): errors.append('声明免 Python，但没有已验证 EXE 或便携 Python 运行时证据')
        if status.get('offline_install_ready_verified') is True:
            evidence=bool(status.get('exe_binary_included') or status.get('portable_runtime_included') or (service/'wheelhouse').is_dir())
            if not evidence: errors.append('声明首次安装完全离线，但未发现 EXE/便携运行时/wheelhouse 证据')
    su=wc/'server_url.txt'
    if su.is_file() and re.search(r'http://192\.168\.',su.read_text(encoding='utf-8',errors='ignore')): warnings.append('Windows 客户端默认地址写死为 192.168.*，建议改成 127.0.0.1 或交付时配置')
    if errors:
        print(f'[PB451] portable_full 验收失败，共 {len(errors)} 项'); [print('-',x) for x in errors]; [print('[警告]',x) for x in warnings]; return 1
    print('[通过] portable_full V1.5.11 级完整部署包装检查通过。'); [print('[警告]',x) for x in warnings]; return 0
if __name__=='__main__': raise SystemExit(main())
