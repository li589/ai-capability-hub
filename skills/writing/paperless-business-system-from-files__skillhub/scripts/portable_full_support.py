from __future__ import annotations
import re
from pathlib import Path

SERVICE_DIR='01_服务端_完整程序'
WIN_CLIENT_DIR='02_Windows填写客户端'
MAC_CLIENT_DIR='03_macOS填写客户端'
REF_DIR='04_业务原始资料参考'
TEMPLATE_DIR='05_电子档模板'
DOC_DIR='06_说明与版本记录'


def _safe_name(name:str)->str:
    name=re.sub(r'[\\/:*?"<>|]+','_',name).strip().strip('.')
    return name or '本地业务系统'


def write_utf16(path:Path,text:str):
    path.write_text(text,encoding='utf-16')


def portable_enabled(spec:dict)->bool:
    return (spec.get('system') or {}).get('deployment_mode')=='portable_full' or bool((spec.get('portable_full') or {}).get('enabled'))


def materialize_portable_layout(root:Path, service:Path, spec:dict, skill_version:str):
    cfg=spec.get('portable_full') or {}
    system=spec.get('system') or {}
    name=_safe_name(str(system.get('name') or '本地业务系统'))
    network=str(system.get('network_mode') or 'offline_core')
    default_url='http://127.0.0.1:5200'

    # Root wrappers
    (root/'一键启动_Windows.bat').write_text('@echo off\r\ncd /d "%~dp0\\01_服务端_完整程序"\r\ncall start_windows.bat\r\n',encoding='utf-8-sig')
    (root/'一键停止_Windows.bat').write_text('@echo off\r\ncd /d "%~dp0\\01_服务端_完整程序"\r\ncall stop_windows.bat\r\n',encoding='utf-8-sig')
    write_utf16(root/'一键启动_Windows.vbs','Set sh=CreateObject("WScript.Shell")\r\nSet fso=CreateObject("Scripting.FileSystemObject")\r\nbase=fso.GetParentFolderName(WScript.ScriptFullName)\r\nsh.Run Chr(34)&base&"\\一键启动_Windows.bat"&Chr(34),0,False\r\n')
    write_utf16(root/'一键停止_Windows.vbs','Set sh=CreateObject("WScript.Shell")\r\nSet fso=CreateObject("Scripting.FileSystemObject")\r\nbase=fso.GetParentFolderName(WScript.ScriptFullName)\r\nsh.Run Chr(34)&base&"\\一键停止_Windows.bat"&Chr(34),0,False\r\n')

    # Windows client
    wc=root/WIN_CLIENT_DIR; wc.mkdir(parents=True,exist_ok=True)
    (wc/'server_url.txt').write_text(default_url+'\n',encoding='utf-8')
    (wc/'Windows客户端使用说明.txt').write_text(
        f'{name} Windows 填写客户端\n\n'
        '1. 管理员先在服务端电脑启动系统。\n'
        '2. 双击“设置服务器地址_Windows.vbs”，填写管理员提供的完整地址，例如 http://192.168.1.100:5200。\n'
        '3. 双击“测试服务器连接_Windows.vbs”确认可访问。\n'
        '4. 双击“打开系统_Windows.vbs”进入系统。\n'
        '5. 客户端不会静默开放防火墙或修改服务端端口。\n',encoding='utf-8')
    vbs_common='''Function BaseDir()\r
 Dim fso:Set fso=CreateObject("Scripting.FileSystemObject"):BaseDir=fso.GetParentFolderName(WScript.ScriptFullName)\r
End Function\r
Function ConfigPath()\r
 Dim sh,fso,d:Set sh=CreateObject("WScript.Shell"):Set fso=CreateObject("Scripting.FileSystemObject")\r
 d=sh.ExpandEnvironmentStrings("%APPDATA%\\UniversalLocalDeploymentClient")\r
 If Not fso.FolderExists(d) Then fso.CreateFolder(d)\r
 ConfigPath=fso.BuildPath(d,"server_url.txt")\r
End Function\r
Function ReadUrl()\r
 Dim fso,p,d:Set fso=CreateObject("Scripting.FileSystemObject"):p=ConfigPath()\r
 If fso.FileExists(p) Then ReadUrl=Trim(fso.OpenTextFile(p,1,False,-1).ReadAll):Exit Function\r
 d=fso.BuildPath(BaseDir(),"server_url.txt")\r
 If fso.FileExists(d) Then ReadUrl=Trim(fso.OpenTextFile(d,1,False,-1).ReadAll) Else ReadUrl="http://127.0.0.1:5200"\r
End Function\r
'''
    write_utf16(wc/'打开系统_Windows.vbs','Option Explicit\r\n'+vbs_common+'Dim sh,url:Set sh=CreateObject("WScript.Shell"):url=ReadUrl():sh.Run url,1,False\r\n')
    write_utf16(wc/'设置服务器地址_Windows.vbs','Option Explicit\r\n'+vbs_common+'Dim fso,p,u,fh:Set fso=CreateObject("Scripting.FileSystemObject"):p=ConfigPath():u=InputBox("请输入完整服务器地址，例如 http://192.168.1.100:5200","设置服务器地址",ReadUrl())\r\nIf Trim(u)="" Then WScript.Quit\r\nIf LCase(Left(Trim(u),7))<>"http://" And LCase(Left(Trim(u),8))<>"https://" Then MsgBox "地址必须以 http:// 或 https:// 开头",16,"地址无效":WScript.Quit\r\nSet fh=fso.CreateTextFile(p,True,True):fh.Write Trim(u):fh.Close:MsgBox "服务器地址已保存："&vbCrLf&Trim(u),64,"完成"\r\n')
    write_utf16(wc/'测试服务器连接_Windows.vbs','Option Explicit\r\n'+vbs_common+'Dim h,u:u=ReadUrl():On Error Resume Next:Set h=CreateObject("WinHttp.WinHttpRequest.5.1"):h.SetTimeouts 3000,3000,3000,3000:h.Open "GET",u&"/health",False:h.Send\r\nIf Err.Number=0 And h.Status=200 Then MsgBox "连接成功："&vbCrLf&u,64,"测试服务器连接" Else MsgBox "连接失败："&vbCrLf&u&vbCrLf&"请确认服务端已启动、地址正确且网络可达。",16,"测试服务器连接"\r\nOn Error GoTo 0\r\n')

    # Reference/template areas - do not silently copy private input.
    rd=root/REF_DIR; rd.mkdir(parents=True,exist_ok=True)
    (rd/'README_资料放置说明.txt').write_text('此目录用于随系统交付经用户明确允许的原始业务资料参考。默认不自动复制用户敏感附件、数据库、密码或日志。\n',encoding='utf-8')
    td=root/TEMPLATE_DIR; td.mkdir(parents=True,exist_ok=True)
    (td/'README_电子模板说明.txt').write_text('此目录用于本业务已验证的 Excel/CSV/申请单/导入模板。只有附件或现有源码有证据时才生成正式模板，禁止凭空伪造字段和公式。\n',encoding='utf-8')

    # Version archive
    current=root/DOC_DIR/'00_当前版本'; current.mkdir(parents=True,exist_ok=True)
    version=str(system.get('version') or '1.0.0')
    (current/'VERSION.txt').write_text(version+'\n',encoding='utf-8')
    (current/f'00_当前版本_V{version}.txt').write_text(f'{name}\n版本：{version}\n生成技能：纸质表单电子化系统生成器 {skill_version}\n部署模式：portable_full\n',encoding='utf-8')
    (current/'更新摘要.txt').write_text('当前包按 portable_full V1.5.11 级交付结构生成。具体业务功能、迁移和修复内容以本次 TEST_REPORT、system-spec 与版本说明为准。\n',encoding='utf-8')
    (current/'完整部署能力说明.md').write_text(
        f'# {name} 完整部署能力\n\n'
        f'- 服务端：`{SERVICE_DIR}/`\n'
        f'- Windows 填写客户端：`{WIN_CLIENT_DIR}/`\n'
        f'- 局域网模式：{network}\n'
        f'- 运行时策略：{cfg.get("runtime_strategy","self_bootstrap_venv")}\n'
        '- “免 Python/首次安装完全离线”必须以 `DELIVERY_STATUS.json` 的真实验证状态为准。\n',encoding='utf-8')
    hist=root/DOC_DIR/'04_历史资料'; hist.mkdir(parents=True,exist_ok=True)
    (hist/'README_历史版本归档规则.txt').write_text('后续升级时把旧版更新说明、迁移说明和回归证据归档到此目录；不要把真实密码、secret key、会话或无关日志归档进交付包。\n',encoding='utf-8')

    logs=service/'logs'; logs.mkdir(parents=True,exist_ok=True)
    (logs/'README.txt').write_text('运行日志目录。交付新建系统时不要预置含敏感信息的真实运行日志。\n',encoding='utf-8')

    # LAN helpers
    if cfg.get('lan_helpers',True):
        (service/'当前服务器地址.txt').write_text('首次启动后由启动器/管理员确认实际地址；不要把某台机器的 192.168.x.x 固定写死为所有用户地址。\n',encoding='utf-8')
        (service/'当前服务端口.txt').write_text('5200\n',encoding='utf-8')
        (service/'查看服务器内网地址_Windows.bat').write_text('@echo off\r\nipconfig | findstr /i "IPv4"\r\necho.\r\necho 请将可用 IPv4 地址与当前服务端口组合为 http://IP:PORT\r\npause\r\n',encoding='utf-8-sig')
        (service/'开放当前端口_Windows.bat').write_text('@echo off\r\nset PORT=5200\r\necho 将为本项目端口 %PORT% 添加 Windows 防火墙入站规则，需要管理员权限。\r\nchoice /M "是否继续"\r\nif errorlevel 2 exit /b 1\r\nnetsh advfirewall firewall add rule name="'+name+' LAN %PORT%" dir=in action=allow protocol=TCP localport=%PORT%\r\npause\r\n',encoding='utf-8-sig')

    # Optional macOS client
    if cfg.get('macos_client'):
        mc=root/MAC_CLIENT_DIR; mc.mkdir(parents=True,exist_ok=True)
        (mc/'server_url.txt').write_text(default_url+'\n',encoding='utf-8')
        (mc/'macOS客户端使用说明.txt').write_text(f'{name} macOS 客户端：先修改 server_url.txt 为服务端地址，再双击/执行打开系统_macOS.command。\n',encoding='utf-8')
        commands={
            '打开系统_macOS.command':'#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\nURL="$(cat "$DIR/server_url.txt" | tr -d "\\r\\n")"\nopen "$URL"\n',
            '测试服务器连接_macOS.command':'#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\nURL="$(cat "$DIR/server_url.txt" | tr -d "\\r\\n")"\n/usr/bin/curl -fsS --max-time 5 "$URL/health" && echo "连接成功" || { echo "连接失败"; exit 1; }\nread -n 1\n',
            '设置服务器地址_macOS.command':'#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\nread -p "请输入完整服务器地址: " URL\ncase "$URL" in http://*|https://*) printf "%s\\n" "$URL" > "$DIR/server_url.txt";; *) echo "地址必须以 http:// 或 https:// 开头"; exit 1;; esac\n'
        }
        for fn,body in commands.items():
            fp=mc/fn; fp.write_text(body,encoding='utf-8'); fp.chmod(0o755)
        for fn,body in {
            '一键启动_macOS.command':'#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\ncd "$DIR/01_服务端_完整程序"\npython3 launcher.py\n',
            '一键停止_macOS.command':'#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\ncd "$DIR/01_服务端_完整程序"\npython3 stop_server.py\n'
        }.items():
            fp=root/fn; fp.write_text(body,encoding='utf-8'); fp.chmod(0o755)

    return {'service_dir':SERVICE_DIR,'windows_client_dir':WIN_CLIENT_DIR,'macos_client_dir':MAC_CLIENT_DIR if cfg.get('macos_client') else None,'runtime_strategy':cfg.get('runtime_strategy','self_bootstrap_venv')}
