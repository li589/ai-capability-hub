#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate full LAN delivery: complete source, responsive Web UI, backup tool and EXE build source."""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

CORE = [
    "01_服务端_完整程序/server.py",
    "01_服务端_完整程序/backend_core.py",
    "01_服务端_完整程序/energy_excel_import.py",
    "01_服务端_完整程序/backup_restore.py",
    "01_服务端_完整程序/port_config.py",
    "01_服务端_完整程序/launcher.py",
    "01_服务端_完整程序/stop_server.py",
    "01_服务端_完整程序/app.py",
    "01_服务端_完整程序/wsgi.py",
    "01_服务端_完整程序/exe_entry.py",
    "01_服务端_完整程序/build_exe_windows.py",
    "01_服务端_完整程序/energy_daily_report_exe.spec",
    "01_服务端_完整程序/requirements.txt",
    "01_服务端_完整程序/templates/index.html",
    "01_服务端_完整程序/templates/login.html",
    "01_服务端_完整程序/static/js/app.js",
    "01_服务端_完整程序/static/css/app.css",
    "01_服务端_完整程序/vendor/flask/__init__.py",
    "01_服务端_完整程序/vendor/xlsxwriter/__init__.py",
]
FIRST_PARTY = [
    "server.py", "backend_core.py", "energy_excel_import.py", "backup_restore.py", "port_config.py",
    "launcher.py", "stop_server.py", "app.py", "wsgi.py", "exe_entry.py", "build_exe_windows.py",
]

LAUNCH_STOP_PAIRS = [
    ("一键启动_Windows.bat", "一键停止_Windows.bat"),
    ("一键启动_macOS.command", "一键停止_macOS.command"),
    ("01_服务端_完整程序/start_windows.bat", "01_服务端_完整程序/stop_windows.bat"),
]


def validate(project: Path, *, run_backup_self_test: bool = True) -> dict:
    project = project.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, object] = {}
    missing = [rel for rel in CORE if not (project / rel).is_file()]
    if missing:
        errors.extend(f"缺少强制交付文件：{rel}" for rel in missing)

    for start_rel, stop_rel in LAUNCH_STOP_PAIRS:
        start_exists = (project / start_rel).is_file()
        stop_exists = (project / stop_rel).is_file()
        if start_exists != stop_exists:
            errors.append(f"一键启动/停止脚本必须成对交付：{start_rel} + {stop_rel}")
        elif not start_exists:
            errors.append(f"缺少一键启动/停止脚本对：{start_rel} + {stop_rel}")
    checks["launch_stop_pairs"] = "passed" if not any("一键启动/停止" in e for e in errors) else "failed"

    server_dir = project / "01_服务端_完整程序"
    for name in FIRST_PARTY:
        path = server_dir / name
        if not path.is_file():
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8-sig", errors="strict"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"Python 源码无法解析：{name}: {exc}")

    all_py = [p for p in server_dir.rglob("*.py") if "__pycache__" not in p.parts]
    first_party_py = [p for p in all_py if "vendor" not in p.relative_to(server_dir).parts]
    vendor_py = [p for p in all_py if "vendor" in p.relative_to(server_dir).parts]
    if len(first_party_py) < 10:
        errors.append("第一方完整服务端 Python 源码数量异常，疑似只交付了启动壳或简化版代码。")

    forbidden = [p for p in project.rglob("*") if p.is_file() and (p.suffix.lower() == ".pyc" or "__pycache__" in p.parts)]
    if forbidden:
        errors.append("交付包不应包含 pyc/__pycache__：" + ", ".join(str(p.relative_to(project)) for p in forbidden[:8]))

    build = server_dir / "build_exe_windows.py"
    if build.is_file():
        text = build.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["PyInstaller", "exe_entry.py", "templates", "static", "vendor", "--onefile", "--onedir"]:
            if token not in text:
                errors.append(f"EXE 构建脚本缺少关键能力：{token}")

    exe_entry = server_dir / "exe_entry.py"
    if exe_entry.is_file():
        text = exe_entry.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["ENERGY_DAILY_DATA_DIR", "from server import app", "webbrowser.open", "app.run"]:
            if token not in text:
                errors.append(f"EXE 专用入口缺少关键能力：{token}")

    index = server_dir / "templates/index.html"
    login = server_dir / "templates/login.html"
    css = server_dir / "static/css/app.css"
    if index.is_file():
        itext = index.read_text(encoding="utf-8-sig", errors="replace").lower()
        if 'name="viewport"' not in itext and "name='viewport'" not in itext:
            errors.append("Web 主界面缺少 viewport，移动端/小屏响应式体验无法验收。")
    if login.is_file():
        ltext = login.read_text(encoding="utf-8-sig", errors="replace").lower()
        if 'name="viewport"' not in ltext and "name='viewport'" not in ltext:
            errors.append("登录页缺少 viewport。")
    if css.is_file():
        ctext = css.read_text(encoding="utf-8-sig", errors="replace").lower()
        if "@media" not in ctext:
            errors.append("Web 样式缺少响应式 @media 规则。")
    checks["primary_ui"] = "responsive_web" if not any("viewport" in e or "@media" in e for e in errors) else "web_ui_check_failed"

    backup = server_dir / "backup_restore.py"
    backup_self_test = "not_run"
    if backup.is_file():
        btext = backup.read_text(encoding="utf-8-sig", errors="replace")
        for token in ["sqlite3", ".backup(", "integrity_check", "confirm_server_stopped", "pre_restore_rollback"]:
            if token not in btext:
                errors.append(f"备份恢复工具缺少安全能力标识：{token}")
        if run_backup_self_test:
            try:
                proc = subprocess.run(
                    [sys.executable, str(backup), "self-test"],
                    cwd=server_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                    check=False,
                )
                payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
                if proc.returncode != 0 or not payload.get("ok"):
                    errors.append("备份恢复自检失败。")
                    backup_self_test = "failed"
                else:
                    backup_self_test = "passed"
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                errors.append(f"备份恢复自检无法完成：{exc}")
                backup_self_test = "failed"
    checks["backup_restore_self_test"] = backup_self_test

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "python_source_count": len(all_py),
        "first_party_python_source_count": len(first_party_py),
        "third_party_vendor_python_source_count": len(vendor_py),
        "core_file_count": len(CORE) - len(missing),
        "core_required_count": len(CORE),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验完整局域网能源日报系统交付")
    parser.add_argument("project_dir")
    parser.add_argument("--skip-backup-self-test", action="store_true")
    args = parser.parse_args()
    result = validate(Path(args.project_dir), run_backup_self_test=not args.skip_backup_self_test)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
