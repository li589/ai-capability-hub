#!/usr/bin/env python3
"""Plan deterministic, verified offline dependency installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

WHEEL_PATTERN = re.compile(
    r"^(?P<name>.+?)-(?P<version>[^-]+?)(?:-(?P<build>\d[^-]*))?-(?P<python>[^-]+)-(?P<abi>[^-]+)-(?P<platform>[^-]+)\.whl$",
    re.IGNORECASE,
)


def normalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).casefold()


def requirement_names(requirements: Path) -> set[str]:
    names: set[str] = set()
    for raw in requirements.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("-r", "--requirement")):
            continue
        if line.startswith(("http://", "https://", "git+", "-e ")) or " @ " in line:
            raise ValueError(f"离线模式不支持直接 URL、VCS 或可编辑依赖：{line}")
        match = re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*", line)
        if match:
            names.add(normalize_name(match.group(0)))
    return names


def unpinned_requirements(requirements: Path) -> list[str]:
    unpinned: list[str] = []
    for raw in requirements.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r", "--requirement")):
            unpinned.append(line)
            continue
        if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*==[^=\s]+$", line):
            unpinned.append(line)
    return unpinned


def wheel_projects(wheels_dir: Path) -> set[str]:
    projects: set[str] = set()
    for wheel in wheels_dir.glob("*.whl"):
        match = WHEEL_PATTERN.match(wheel.name)
        if match:
            projects.add(normalize_name(match.group("name")))
    return projects


def verify_manifest(wheels_dir: Path, requirements_sha256: str) -> tuple[bool, list[str]]:
    manifest_path = wheels_dir / "OFFLINE_MANIFEST.json"
    if not manifest_path.is_file():
        return False, ["缺少 OFFLINE_MANIFEST.json"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, ["离线依赖清单格式有误或已损坏，请重新运行 prepare_offline_dependencies.py"]
    problems: list[str] = []
    if manifest.get("requirements_sha256") != requirements_sha256:
        problems.append("requirements.txt 已变化，离线依赖包需要重新生成")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        problems.append("离线清单没有 wheel 文件记录")
        return False, problems
    for item in files:
        if not isinstance(item, dict) or not item.get("file") or not item.get("sha256"):
            problems.append("离线清单存在无效文件记录")
            continue
        name = str(item["file"])
        if Path(name).name != name or not name.casefold().endswith(".whl"):
            problems.append(f"离线清单包含不安全文件名：{name}")
            continue
        wheel = wheels_dir / name
        if not wheel.is_file():
            problems.append(f"离线文件缺失：{name}")
        elif file_sha256(wheel) != item["sha256"]:
            problems.append(f"离线文件哈希不匹配：{name}")
    return not problems, problems


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def plan_dependencies(project: Path) -> dict:
    requirements = project / "requirements.txt"
    wheels_dir = project / "wheels"
    result = {
        "ok": False,
        "code": "DEPENDENCY_PLAN_UNAVAILABLE",
        "mode": "unavailable",
        "requirements_sha256": None,
        "required_projects": [],
        "wheel_projects": [],
        "missing_wheels": [],
        "install_args": [],
        "message": "",
        "suggestion": "",
    }
    if not requirements.is_file():
        result.update(code="REQUIREMENTS_MISSING", message="找不到 requirements.txt", suggestion="确认系统 ZIP 已完整解压后重试。")
        return result
    try:
        required = sorted(requirement_names(requirements))
    except ValueError as exc:
        result.update(message=str(exc), suggestion="把依赖改为受信任软件源中的固定包名与版本，并重新准备离线包。")
        return result
    result["requirements_sha256"] = file_sha256(requirements)
    result["required_projects"] = required
    if wheels_dir.is_dir():
        available = sorted(wheel_projects(wheels_dir))
        missing = sorted(set(required) - set(available))
        manifest_ok, manifest_problems = verify_manifest(wheels_dir, result["requirements_sha256"])
        result["wheel_projects"] = available
        result["missing_wheels"] = missing
        result["manifest_problems"] = manifest_problems
        if not missing and required and manifest_ok:
            result.update(
                ok=True,
                mode="offline",
                install_args=["--no-index", "--find-links", str(wheels_dir), "-r", str(requirements)],
                message="离线依赖包完整且哈希校验通过，启动时不访问软件源。",
                suggestion="保持 wheels 与 requirements.txt 同版本发布。",
            )
            return result
    result.update(
        ok=False,
        code="OFFLINE_DEPENDENCIES_UNAVAILABLE",
        mode="blocked",
        install_args=[],
        message="未发现完整且通过哈希校验的离线依赖包。",
        suggestion="由 IT 将匹配当前 Python 和操作系统的 wheels 放入 wheels 目录，再运行 prepare_offline_dependencies.py 生成清单。",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="无纸化业务系统依赖安装方案检查")
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    result = plan_dependencies(Path(args.project_dir).resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[{result['mode']}] {result['message']}")
        if result["missing_wheels"]:
            print("缺少离线 wheel：" + ", ".join(result["missing_wheels"]))
        print("处理建议：" + result["suggestion"])
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
