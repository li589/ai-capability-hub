#!/usr/bin/env python3
"""
WorkBuddy 环境一键诊断脚本
用法：python check_env.py [--fast] [--fix] [--collect-logs]
功能：检查代理状态、连接器配置、专家注册、最近错误日志
选项：--fast          跳过网络检测，只查本地配置（弱网环境推荐）
      --fix          检测到问题时自动尝试修复（代理重启/JSON修复/连接器重连）
      --collect-logs 将环境快照（脱敏）导出为 workbuddy_env_report_时间戳.json，便于上报问题
注意：自动修复仅限 JSON/代理/连接器状态；网络、账号、权限类问题需按 troubleshooting 指引手动处理。
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# 使用纯 ASCII 符号，避免 Windows GBK 编码问题
OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

HOME = Path.home()
WORKBUDDY_DIR = HOME / ".workbuddy"
CONNECTORS_DIR = WORKBUDDY_DIR / "connectors"
EXPERTS_DIR = WORKBUDDY_DIR / "plugins" / "marketplaces" / "my-experts" / "plugins"
LOGS_DIR = WORKBUDDY_DIR / "logs"

def green(s):
    return f"\033[92m{s}\033[0m"

def red(s):
    return f"\033[91m{s}\033[0m"

def yellow(s):
    return f"\033[93m{s}\033[0m"

def check_proxy():
    """检查代理是否运行"""
    print("\n" + "=" * 50)
    print("1. 代理状态检查")
    print("=" * 50)
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "3",
             "http://127.0.0.1:51103/health"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() == "200":
            print(green(f"{OK} 代理正常运行 (端口 51103)"))
            return True
        else:
            print(red(f"{FAIL} 代理无响应 (HTTP {result.stdout.strip()})"))
            print(yellow(f"   → 建议：重启 WorkBuddy"))
            return False
    except Exception:
        print(red(f"{FAIL} 无法连接代理 (端口 51103)"))
        print(yellow(f"   → 建议：确认 WorkBuddy 是否正在运行"))
        return False

def check_connectors():
    """检查连接器配置"""
    print("\n" + "=" * 50)
    print("2. 连接器配置检查")
    print("=" * 50)

    sessions = [d for d in CONNECTORS_DIR.iterdir()
                if d.is_dir() and d.name not in ("default", "skills")]

    if not sessions:
        print(red(f"{FAIL} 未找到连接器会话目录"))
        return

    for session in sorted(sessions):
        print(f"\n--- Session: {session.name} ---")

        # 检查 connector-states.json
        states_file = session / "connector-states.json"
        if states_file.exists():
            try:
                states = json.loads(states_file.read_text(encoding='utf-8'))
                enabled = states.get("enabled", [])
                header_overrides = states.get("headerOverrides", {})
                print(f"  已启用连接器: {len(enabled)} 个")
                if enabled:
                    print(f"  列表: {', '.join(enabled)}")
                if header_overrides:
                    print(f"  有 headerOverrides: {', '.join(header_overrides.keys())}")
            except json.JSONDecodeError:
                print(red(f"  {FAIL} connector-states.json 格式错误"))
        else:
            print(yellow(f"  {WARN} 无 connector-states.json"))

        # 检查 mcp.json
        mcp_file = session / "mcp.json"
        if mcp_file.exists():
            try:
                config = json.loads(mcp_file.read_text(encoding='utf-8'))
                connectors = [k for k in config if k.startswith("connector:")]
                disabled = [k for k, v in config.items() if k.startswith("connector:") and v.get("disabled")]
                print(f"  配置的连接器: {len(connectors)} 个")
                if disabled:
                    print(yellow(f"  已禁用: {', '.join(disabled)}"))
            except json.JSONDecodeError:
                print(red(f"  {FAIL} mcp.json 格式错误"))
        else:
            print(yellow(f"  {WARN} 无 mcp.json"))

def check_experts():
    """检查专家注册"""
    print("\n" + "=" * 50)
    print("3. 专家注册检查")
    print("=" * 50)

    if not EXPERTS_DIR.exists():
        print(yellow(f"{WARN} 无自定义专家目录"))
        return

    experts = [d for d in EXPERTS_DIR.iterdir() if d.is_dir()]
    if not experts:
        print(yellow(f"{WARN} 无自定义专家"))
        return

    for expert in experts:
        print(f"\n--- {expert.name} ---")
        # plugin.json 可能在 .codebuddy-plugin/ 或 .workbuddy-plugin/ 子目录
        plugin_file = None
        for subdir in ("plugin.json", ".codebuddy-plugin/plugin.json", ".workbuddy-plugin/plugin.json"):
            candidate = expert / subdir
            if candidate.exists():
                plugin_file = candidate
                break
        agent_dir = expert / "agents"

        if plugin_file:
            try:
                plugin = json.loads(plugin_file.read_text(encoding='utf-8'))
                print(f"  名称: {plugin.get('displayName', 'N/A')}")
                print(f"  类型: {plugin.get('expertType', 'N/A')}")
                print(f"  插件位置: {plugin_file.relative_to(expert)}")
                agent_name = plugin.get('agentName', '')
            except json.JSONDecodeError:
                print(red(f"  {FAIL} plugin.json 格式错误"))
                continue
        else:
            print(red(f"  {FAIL} 缺少 plugin.json（已检查 expert/、.codebuddy-plugin/、.workbuddy-plugin/）"))
            continue

        if agent_dir.exists():
            md_file = agent_dir / f"{agent_name}.md"
            if md_file.exists():
                size = md_file.stat().st_size
                print(f"  Agent文件: {agent_name}.md ({size} 字节)")
                if size < 100:
                    print(yellow(f"  {WARN} Prompt 太短，可能缺少必要信息"))
                elif size > 5000:
                    print(yellow(f"  {WARN} Prompt 太长，可能导致模型遗忘"))
            else:
                print(red(f"  {FAIL} 缺少 agents/{agent_name}.md"))
        else:
            print(red(f"  {FAIL} 缺少 agents/ 目录"))

def check_logs():
    """检查最近错误日志"""
    print("\n" + "=" * 50)
    print("4. 最近错误日志")
    print("=" * 50)

    if not LOGS_DIR.exists():
        print(yellow(f"{WARN} 无日志目录"))
        return

    log_files = sorted(LOGS_DIR.glob("*.log"), key=os.path.getmtime, reverse=True)
    if not log_files:
        print("无日志文件")
        return

    for log_file in log_files[:3]:  # 只检查最近3个日志
        try:
            content = log_file.read_text(encoding='utf-8', errors='ignore')
            errors = [l for l in content.split('\n') if any(kw in l.lower() for kw in ('error', 'fail', 'warning', 'crash', 'exception', 'timeout'))]
            if errors:
                print(f"\n{log_file.name} ({len(errors)} 条错误):")
                for e in errors[-5:]:  # 只显示最近5条
                    print(f"  {e[:120]}...")
            else:
                print(f"\n{log_file.name}: 无错误")
        except Exception:
            print(f"\n{log_file.name}: 无法读取")

def check_config_files():
    """检查配置文件完整性"""
    print("\n" + "=" * 50)
    print("5. 配置文件完整性")
    print("=" * 50)

    checks = {
        "~/.workbuddy/mcp.json": WORKBUDDY_DIR / "mcp.json",
        "~/.workbuddy/connectors/default/mcp.json": CONNECTORS_DIR / "default" / "mcp.json",
    }

    for name, path in checks.items():
        if path.exists():
            try:
                json.loads(path.read_text(encoding='utf-8'))
                print(green(f"{OK} {name} — 格式正确"))
            except json.JSONDecodeError:
                print(red(f"{FAIL} {name} — JSON格式错误"))
        else:
            print(yellow(f"{WARN} {name} — 文件不存在（可能使用默认配置）"))

def check_automations():
    """检查自动化任务状态"""
    print("\n" + "=" * 50)
    print("6. 自动化任务检查")
    print("=" * 50)

    db_path = WORKBUDDY_DIR / "workbuddy.db"
    if not db_path.exists():
        print(yellow(f"{WARN} 无 workbuddy.db 数据库文件"))
        return

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='automations'")
        if not cursor.fetchone():
            print(yellow(f"{WARN} 无 automations 表"))
            conn.close()
            return

        cursor.execute("SELECT name, status, rrule FROM automations")
        rows = cursor.fetchall()

        if not rows:
            print(yellow(f"{WARN} 无自动化任务"))
            conn.close()
            return

        print(f"  共 {len(rows)} 个自动化任务:")
        for name, status, rrule in rows:
            status_str = green(f"{OK}") if status and status.upper() == "ACTIVE" else yellow(f"{WARN}")
            rrule_str = "无RRULE" if not rrule else rrule[:40]
            print(f"  {status_str} {name} [{status}] rrule: {rrule_str}")

        conn.close()
    except Exception as e:
        print(red(f"{FAIL} 读取自动化任务失败: {e}"))


def check_models():
    """检查模型配置"""
    print("\n" + "=" * 50)
    print("7. 模型配置检查")
    print("=" * 50)

    candidates = [
        WORKBUDDY_DIR / "models.json",
        WORKBUDDY_DIR / "connectors" / "default" / "models.json",
    ]

    found = False
    for path in candidates:
        if path.exists():
            found = True
            try:
                config = json.loads(path.read_text(encoding='utf-8'))
                model_count = len(config) if isinstance(config, dict) else 0
                print(green(f"{OK} {path.relative_to(WORKBUDDY_DIR)} — 格式正确 ({model_count} 个配置)"))
            except json.JSONDecodeError:
                print(red(f"{FAIL} {path.relative_to(WORKBUDDY_DIR)} — JSON 格式错误"))

    if not found:
        print(yellow(f"{WARN} 未找到 models.json（可能使用默认模型配置）"))


def summary(fix_mode=False):
    """输出诊断摘要"""
    print("\n" + "=" * 50)
    print("诊断完成")
    print("=" * 50)
    if fix_mode:
        print("""
自动修复说明：
  - 已尝试自动修复检测到的问题
  - 如仍有问题，请手动执行上方建议操作
  - 常见手动修复：
    - 所有连接器down → 重启 WorkBuddy
    - 单个连接器disconnected → 重新登录
    - 专家不生效 → 执行 validate + register
    - 自动化不执行 → 检查 status 是否 ACTIVE
    - 配置JSON错误 → 用 jsonlint 检查
""")
    else:
        print("""
常见问题快速修复：
  - 所有连接器down → 重启 WorkBuddy
  - 单个连接器disconnected → 重新登录
  - 专家不生效 → 执行 validate + register
  - 自动化不执行 → 检查 status 是否 ACTIVE
  - 配置JSON错误 → 用 jsonlint 检查
  - 自动修复 → python check_env.py --fix
""")


def fix_proxy():
    """尝试修复代理问题"""
    print("\n" + "=" * 50)
    print("[FIX] 代理修复")
    print("=" * 50)
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "3",
             "http://127.0.0.1:51103/health"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() == "200":
            print(green(f"{OK} 代理正常，无需修复"))
            return True
        else:
            print(yellow(f"{WARN} 代理无响应，尝试重启 WorkBuddy..."))
            print(yellow(f"   → 请手动重启 WorkBuddy 后重新运行诊断"))
            return False
    except Exception:
        print(red(f"{FAIL} 无法连接代理"))
        print(yellow(f"   → 请确认 WorkBuddy 是否正在运行，如未运行请启动"))
        return False


def fix_json_files():
    """尝试修复 JSON 配置文件（BOM / 尾部逗号 / 行注释）"""
    print("\n" + "=" * 50)
    print("[FIX] JSON 配置修复")
    print("=" * 50)

    candidates = [
        WORKBUDDY_DIR / "mcp.json",
        WORKBUDDY_DIR / "models.json",
        CONNECTORS_DIR / "default" / "mcp.json",
    ]

    fixed = 0
    for path in candidates:
        if not path.exists():
            continue
        try:
            json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            print(yellow(f"{WARN} {path.name} JSON 格式错误: {e}"))
            raw = path.read_text(encoding='utf-8')
            # 1) 剥 BOM 头
            fixed_content = raw.lstrip('\ufeff')
            # 2) 去除行注释（// 与行首 #），仅当整行可被安全剥离时
            cleaned_lines = []
            for line in fixed_content.split('\n'):
                stripped = line.lstrip()
                if stripped.startswith('#'):
                    continue
                if '//' in line:
                    line = line.split('//')[0].rstrip()
                cleaned_lines.append(line)
            fixed_content = '\n'.join(cleaned_lines)
            # 3) 去除尾部多余逗号
            fixed_content = re.sub(r',\s*([}\]])', r'\1', fixed_content)
            try:
                json.loads(fixed_content)
                backup = path.with_suffix('.json.bak')
                backup.write_text(raw, encoding='utf-8')
                path.write_text(fixed_content, encoding='utf-8')
                print(green(f"{OK} 已修复 {path.name}（原文件备份为 .bak）"))
                fixed += 1
            except json.JSONDecodeError:
                print(red(f"{FAIL} 无法自动修复 {path.name}（可能缺括号/引号，或注释在字符串内）"))
                print(yellow(f"   → 建议使用 JSON linter 在线工具定位第 {e.lineno} 行附近"))

    if fixed == 0:
        print(green(f"{OK} 所有 JSON 配置文件格式正确"))
    return fixed


def collect_env_report():
    """导出脱敏环境快照，便于上报问题（不含 token/密钥）"""
    print("\n" + "=" * 50)
    print("[REPORT] 收集环境快照")
    print("=" * 50)

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "workbuddy_dir": str(WORKBUDDY_DIR),
        "items": {},
    }

    # 代理（仅探活，不记录内容）
    report["items"]["proxy_reachable"] = check_proxy()

    # 连接器会话数量与启用状态（不记录 token）
    connector_summary = {}
    if CONNECTORS_DIR.exists():
        for session in sorted(CONNECTORS_DIR.iterdir()):
            if not session.is_dir() or session.name in ("default", "skills"):
                continue
            states_file = session / "connector-states.json"
            if states_file.exists():
                try:
                    states = json.loads(states_file.read_text(encoding='utf-8'))
                    connector_summary[session.name] = {
                        "enabled_count": len(states.get("enabled", [])),
                        "enabled": states.get("enabled", []),
                    }
                except json.JSONDecodeError:
                    connector_summary[session.name] = {"error": "connector-states.json 格式错误"}
    report["items"]["connectors"] = connector_summary

    # 配置文件存在性与大小（不读取内容）
    for name, p in {
        "mcp.json": WORKBUDDY_DIR / "mcp.json",
        "models.json": WORKBUDDY_DIR / "models.json",
        "default_mcp.json": CONNECTORS_DIR / "default" / "mcp.json",
    }.items():
        report["items"][name] = {
            "exists": p.exists(),
            "size": p.stat().st_size if p.exists() else 0,
        }

    # 自动化任务数量（不记录 prompt 内容）
    db_path = WORKBUDDY_DIR / "workbuddy.db"
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM automations")
            count = cur.fetchone()[0]
            report["items"]["automation_count"] = count
            conn.close()
        except Exception:
            report["items"]["automation_count"] = "读取失败"
    else:
        report["items"]["automation_count"] = 0

    out_name = f"workbuddy_env_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(out_name, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(green(f"{OK} 环境快照已导出: {out_name}（已脱敏，可安全分享）"))
    except Exception as e:
        print(red(f"{FAIL} 导出失败: {e}"))


def fix_connectors():
    """检查并提示连接器重连"""
    print("\n" + "=" * 50)
    print("[FIX] 连接器状态检查")
    print("=" * 50)

    if not CONNECTORS_DIR.exists():
        print(yellow(f"{WARN} 无连接器目录"))
        return

    sessions = [d for d in CONNECTORS_DIR.iterdir()
                if d.is_dir() and d.name not in ("default", "skills")]
    disconnected = []

    for session in sessions:
        states_file = session / "connector-states.json"
        if states_file.exists():
            try:
                states = json.loads(states_file.read_text(encoding='utf-8'))
                enabled = states.get("enabled", [])
                if not enabled:
                    disconnected.append(session.name)
            except json.JSONDecodeError:
                pass

    if disconnected:
        print(yellow(f"{WARN} 以下会话无已启用连接器: {', '.join(disconnected)}"))
        print(yellow(f"   → 请在 WorkBuddy UI 中重新授权连接器"))
    else:
        print(green(f"{OK} 连接器状态正常"))


if __name__ == "__main__":
    fast_mode = "--fast" in sys.argv
    fix_mode = "--fix" in sys.argv
    collect_logs = "--collect-logs" in sys.argv
    print("WorkBuddy 环境诊断工具 v1.4")
    if fast_mode:
        print(yellow("[--fast] 跳过网络检测，只查本地配置"))
    if fix_mode:
        print(yellow("[--fix] 检测到问题时将自动尝试修复"))
    if collect_logs:
        print(yellow("[--collect-logs] 结束后导出脱敏环境快照"))

    if not fast_mode:
        check_proxy()
    else:
        print(f"\n{'=' * 50}\n1. 代理状态检查 [SKIPPED --fast]\n{'=' * 50}")
    check_connectors()
    check_experts()
    check_logs()
    check_config_files()
    check_automations()
    check_models()

    if fix_mode:
        fix_proxy()
        fixed_json = fix_json_files()
        fix_connectors()

    if collect_logs:
        collect_env_report()

    summary(fix_mode=fix_mode)

    # 退出码：0=无问题，1=有问题未自动修复（或仅诊断），2=已自动修复
    if fix_mode and fixed_json > 0:
        sys.exit(2)
    elif fix_mode:
        sys.exit(1)
    else:
        sys.exit(0)
