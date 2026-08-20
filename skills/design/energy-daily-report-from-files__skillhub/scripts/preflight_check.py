#!/usr/bin/env python3
"""Run a read-only Chinese preflight check for a generated paperless system."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import socket
import sqlite3
import sys
from pathlib import Path

REQUIRED_PATHS = [
    "app.py", "src", "templates", "static", "data/paperless_business.db",
    "config/business-system-blueprint.json", "requirements.txt", "README_运行说明.md", "VERSION",
]
REQUIRED_IMPORTS = ["flask", "jinja2", "waitress"]


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_available_port(host: str = "127.0.0.1", start: int = 5000, attempts: int = 20) -> int | None:
    if not 1 <= start <= 65535:
        return None
    for port in range(start, min(start + max(attempts, 0), 65536)):
        if port_available(host, port):
            return port
    return None


def run_preflight(project: Path, *, check_dependencies: bool = True) -> dict:
    checks: list[dict] = []
    errors: list[dict] = []
    warnings: list[dict] = []

    def check(name: str, passed: bool, detail: str, code: str, suggestion: str, *, warning: bool = False) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            (warnings if warning else errors).append({"code": code, "message": detail, "suggestion": suggestion})

    check("python_version", sys.version_info >= (3, 10), f"Python {platform.python_version()}", "PREFLIGHT_PYTHON_VERSION", "安装 Python 3.10 或更高版本。")
    check("project_path", project.is_dir(), f"项目目录：{project}", "PREFLIGHT_PROJECT_MISSING", "确认已完整解压系统 ZIP。")
    for relative in REQUIRED_PATHS:
        exists = (project / relative).exists()
        check(f"path:{relative}", exists, f"{'存在' if exists else '缺少'}：{relative}", "PREFLIGHT_PATH_MISSING", "重新解压完整系统 ZIP，不能只复制部分文件。")

    blueprint = project / "config/business-system-blueprint.json"
    if blueprint.is_file():
        try:
            from validate_business_blueprint import validate_business_blueprint
            payload = json.loads(blueprint.read_text(encoding="utf-8-sig"))
            result = validate_business_blueprint(payload)
            detail = "业务蓝图校验通过" if result["ok"] else "业务蓝图错误：" + "；".join(item["message"] for item in result["errors"][:3])
            check("business_blueprint", result["ok"], detail, "PREFLIGHT_BLUEPRINT_INVALID", "运行业务蓝图校验器并修正错误。")
            warnings.extend(result["warnings"])
        except Exception as exc:
            check("business_blueprint", False, "业务蓝图无法校验，请检查 config/business-system-blueprint.json 是否存在且格式正确", "PREFLIGHT_BLUEPRINT_INVALID", "检查 JSON 和蓝图校验脚本。")

    db = project / "data/paperless_business.db"
    if db.is_file():
        try:
            con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
            integrity = con.execute("PRAGMA integrity_check").fetchone()
            foreign_keys = con.execute("PRAGMA foreign_key_check").fetchall()
            con.close()
            check("database_integrity", bool(integrity and integrity[0] == "ok" and not foreign_keys), "数据库完整性和外键正常" if integrity and integrity[0] == "ok" and not foreign_keys else "数据库完整性或外键检查失败", "PREFLIGHT_DATABASE_INTEGRITY", "停止启动并从最近备份恢复。")
        except Exception as exc:
            check("database_integrity", False, "无法读取数据库文件，可能文件已损坏或被占用，请检查 data/paperless_business.db", "PREFLIGHT_DATABASE_OPEN", "确认文件未损坏且有读取权限。")

    if check_dependencies:
        missing = [name for name in REQUIRED_IMPORTS if importlib.util.find_spec(name) is None]
        check("dependencies", not missing, "依赖已就绪" if not missing else "缺少依赖：" + ", ".join(missing), "PREFLIGHT_DEPENDENCIES", "使用统一依赖助手；离线环境使用已验证 wheels。")

    try:
        start_port = int(os.environ.get("PAPERLESS_PORT", "5000"))
        if not 1 <= start_port <= 65535:
            raise ValueError("端口必须在 1 到 65535 之间")
    except ValueError as exc:
        start_port = 5000
        warnings.append({"code": "PREFLIGHT_PORT_INVALID", "message": "PAPERLESS_PORT 环境变量值无效，已回退从 5000 开始探测。", "suggestion": "设置有效的端口号（1-65535）。"})
    selected_port = find_available_port(start=start_port)
    check("available_port", selected_port is not None, f"发现候选端口：{selected_port}" if selected_port else "暂无候选端口", "PREFLIGHT_PORT_UNAVAILABLE", "启动时重新绑定，或设置 PAPERLESS_PORT。", warning=True)
    return {"ok": not errors, "summary": "启动前自检通过" if not errors else "启动前自检未通过", "environment": {"python": platform.python_version(), "os": platform.platform()}, "selected_port": selected_port, "checks": checks, "errors": errors, "warnings": warnings}


def render_text(result: dict) -> str:
    lines = [f"[{'通过' if result['ok'] else '未通过'}] {result['summary']}"]
    lines.extend(f"- [{'通过' if item['passed'] else '失败'}] {item['name']}：{item['detail']}" for item in result["checks"])
    lines.extend(f"- [{item['code']}] {item['message']}；解决步骤：{item['suggestion']}" for item in result["errors"] + result["warnings"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="无纸化业务系统启动前中文自检")
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--skip-dependencies", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_preflight(Path(args.project_dir).resolve(), check_dependencies=not args.skip_dependencies)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
