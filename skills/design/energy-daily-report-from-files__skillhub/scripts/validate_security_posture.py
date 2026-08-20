#!/usr/bin/env python3
"""Fail a release when runtime helpers can download, elevate, or execute unsafely."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

LAUNCHER_FORBIDDEN = {
    "Invoke-WebRequest", "Start-Process", "-Verb RunAs",
    "ExecutionPolicy Bypass", "Set-ExecutionPolicy", "/usr/bin/curl",
    "/usr/bin/osascript", "/usr/sbin/installer", "sudo -S",
    "NOPASSWD", "spctl --master-disable",
}
DEPENDENCY_FORBIDDEN = {
    "--index-url", "--extra-index-url", "--allow-online",
    "--allow-network", "pip download", "requests.get(",
    "urllib.request.urlopen(",
}
RUNTIME_PYTHON = [
    "scripts/dependency_plan.py",
    "scripts/install_dependencies.py",
    "scripts/prepare_offline_dependencies.py",
    "resources/standalone-energy-daily-report/build_exe_windows.py",
    "resources/standalone-energy-daily-report/energy_daily_report.py",
]


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        value = func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def _scan_python(path: Path, relative: str, errors: list[dict[str, object]]) -> None:
    try:
        source = path.read_text(encoding="utf-8-sig", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        errors.append({"code": "SECURITY_PYTHON_UNREADABLE", "file": relative, "message": "运行脚本无法安全解析。"})
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name in {"eval", "exec", "os.system"}:
            errors.append({"code": "SECURITY_DYNAMIC_EXECUTION", "file": relative, "line": node.lineno, "message": f"禁止动态执行：{name}"})
        if name in {"subprocess.run", "subprocess.call", "subprocess.Popen", "subprocess.check_call", "subprocess.check_output"}:
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    errors.append({"code": "SECURITY_SHELL_EXECUTION", "file": relative, "line": node.lineno, "message": "禁止 shell=True。"})


def _is_pinned_requirement(line: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*==[^=\s]+", line))


def validate_security_posture(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    errors: list[dict[str, object]] = []

    for path in skill_dir.rglob("*"):
        if any(part in {"__pycache__", ".pytest_cache", ".venv", "dist", "build"} for part in path.parts):
            continue
        relative = path.relative_to(skill_dir).as_posix()
        if any(ord(character) > 127 for character in relative):
            errors.append({"code": "SECURITY_NON_ASCII_ARCHIVE_PATH", "file": relative, "message": "归档文件名必须使用 ASCII，避免上传平台 MIME 解析失败。"})

    launcher_dir = skill_dir / "resources/launcher-templates"
    if launcher_dir.is_dir():
        for path in launcher_dir.iterdir():
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for token in sorted(LAUNCHER_FORBIDDEN):
                if token in text:
                    errors.append({"code": "SECURITY_LAUNCHER_FORBIDDEN", "file": path.relative_to(skill_dir).as_posix(), "message": f"启动模板包含禁止能力：{token}"})

    for relative in RUNTIME_PYTHON:
        path = skill_dir / relative
        if not path.is_file():
            errors.append({"code": "SECURITY_RUNTIME_FILE_MISSING", "file": relative, "message": "安全检查所需运行文件缺失。"})
            continue
        _scan_python(path, relative, errors)

    for relative in ["scripts/install_dependencies.py", "scripts/prepare_offline_dependencies.py"]:
        path = skill_dir / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for token in sorted(DEPENDENCY_FORBIDDEN):
            if token in text:
                errors.append({"code": "SECURITY_DEPENDENCY_NETWORK_PATH", "file": relative, "message": f"离线依赖脚本包含联网入口：{token}"})

    for path in skill_dir.rglob("requirements*.txt"):
        relative = path.relative_to(skill_dir).as_posix()
        for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
            line = raw.strip()
            if line and not line.startswith("#") and not _is_pinned_requirement(line):
                errors.append({"code": "SECURITY_REQUIREMENT_UNPINNED", "file": relative, "line": line_no, "message": f"依赖未精确锁定：{line}"})

    runtime_path = skill_dir / "resources/config-templates/python-runtime.example.json"
    try:
        runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))
        policy = runtime.get("policy", {})
        if runtime.get("mode") != "verify-only" or any(policy.get(key) is not False for key in ["allow_network_download", "allow_process_launch", "allow_admin_install"]):
            errors.append({"code": "SECURITY_RUNTIME_POLICY", "file": runtime_path.relative_to(skill_dir).as_posix(), "message": "Python 运行时必须保持只验证、无下载、无启动、无提权。"})
    except (OSError, json.JSONDecodeError):
        errors.append({"code": "SECURITY_RUNTIME_POLICY_UNREADABLE", "file": "resources/config-templates/python-runtime.example.json", "message": "Python 安全策略配置缺失或损坏。"})

    return {
        "ok": not errors,
        "policy": "verify-only/offline-only/no-elevation",
        "checked_runtime_files": len(RUNTIME_PYTHON),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查技能包是否存在联网下载、自动安装、提权或不安全执行入口")
    parser.add_argument("skill_dir", nargs="?", default=".")
    args = parser.parse_args()
    result = validate_security_posture(Path(args.skill_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
