#!/usr/bin/env python3
"""Install only locally verified wheels; this module has no network mode."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from dependency_plan import plan_dependencies


def marker_path(project: Path) -> Path:
    return Path(sys.prefix) / ".requirements-ready.json"


def marker_matches(project: Path, requirements_sha256: str) -> bool:
    marker = marker_path(project)
    if not marker.is_file():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return data.get("requirements_sha256") == requirements_sha256 and data.get("mode") == "offline-verified"


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def run_pip(args: list[str], project: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PIP_NO_INDEX"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pip"] + args,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
        timeout=600,
    )


def install(project: Path) -> dict:
    plan = plan_dependencies(project)
    if not plan["ok"] or plan["mode"] != "offline":
        return {
            "ok": False,
            "code": plan.get("code", "OFFLINE_DEPENDENCIES_UNAVAILABLE"),
            "mode": "offline-only",
            "attempts": 0,
            "message": plan.get("message", "离线依赖不可用。"),
            "suggestion": plan.get("suggestion", "请由 IT 补齐并校验 wheels。"),
        }
    if marker_matches(project, plan["requirements_sha256"]):
        checked = run_pip(["check"], project)
        if checked.returncode == 0:
            return {"ok": True, "code": "DEPENDENCIES_READY", "mode": "cached", "attempts": 0, "message": "离线依赖版本未变化且完整性检查通过。"}
    try:
        installed = run_pip(plan["install_args"], project)
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "code": "OFFLINE_INSTALL_TIMEOUT",
            "mode": "offline-only",
            "attempts": 1,
            "message": "离线依赖安装超时，已安全停止。",
            "suggestion": "检查磁盘、杀毒软件和 wheel 是否匹配当前 Python。",
        }
    if installed.returncode != 0:
        return {
            "ok": False,
            "code": "OFFLINE_INSTALL_FAILED",
            "mode": "offline-only",
            "attempts": 1,
            "message": "离线依赖安装失败，数据库未被修改。",
            "suggestion": "确认 wheel 与当前 Python、系统架构匹配，并重新生成哈希清单。",
            "output_tail": f"{installed.stdout}\n{installed.stderr}"[-2000:],
        }
    checked = run_pip(["check"], project)
    if checked.returncode != 0:
        return {
            "ok": False,
            "code": "OFFLINE_DEPENDENCY_CHECK_FAILED",
            "mode": "offline-only",
            "attempts": 1,
            "message": "依赖安装完成，但一致性检查未通过。",
            "suggestion": "不要启动系统；由 IT 修复离线依赖集合。",
            "output_tail": f"{checked.stdout}\n{checked.stderr}"[-2000:],
        }
    atomic_write_json(marker_path(project), {
        "requirements_sha256": plan["requirements_sha256"],
        "mode": "offline-verified",
        "python": sys.version.split()[0],
    })
    return {"ok": True, "code": "DEPENDENCIES_INSTALLED", "mode": "offline", "attempts": 1, "message": "已从本地校验通过的 wheels 安装并复核依赖。"}


def main() -> int:
    parser = argparse.ArgumentParser(description="仅使用本地校验 wheels 安装依赖")
    parser.add_argument("project_dir", nargs="?", default=".")
    args = parser.parse_args()
    result = install(Path(args.project_dir).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
