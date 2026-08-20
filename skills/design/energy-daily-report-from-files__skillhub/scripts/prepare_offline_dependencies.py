#!/usr/bin/env python3
"""Create and verify a manifest for wheel files already provided by IT."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dependency_plan import file_sha256, plan_dependencies, unpinned_requirements


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare(project: Path) -> dict:
    requirements = project / "requirements.txt"
    wheels = project / "wheels"
    if not requirements.is_file():
        return {"ok": False, "code": "OFFLINE_REQUIREMENTS_MISSING", "message": "找不到 requirements.txt", "suggestion": "确认项目完整后重试。"}
    unpinned = unpinned_requirements(requirements)
    if unpinned:
        return {
            "ok": False,
            "code": "REQUIREMENTS_NOT_PINNED",
            "message": "生成离线清单前必须精确锁定全部依赖版本。",
            "suggestion": "把依赖写成 package==version。",
            "unpinned": unpinned,
        }
    files_on_disk = sorted(wheels.glob("*.whl")) if wheels.is_dir() else []
    if not files_on_disk:
        return {
            "ok": False,
            "code": "WHEELS_NOT_PROVIDED",
            "message": "wheels 目录中没有 wheel 文件。",
            "suggestion": "请由 IT 在受控环境获取匹配文件，并复制到 wheels 目录；本脚本不联网下载。",
        }
    files = [{"file": path.name, "size": path.stat().st_size, "sha256": sha256(path)} for path in files_on_disk]
    manifest = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "requirements_sha256": file_sha256(requirements),
        "files": files,
        "network_used": False,
    }
    (wheels / "OFFLINE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    verified = plan_dependencies(project)
    if verified["mode"] != "offline":
        return {
            "ok": False,
            "code": "OFFLINE_MANIFEST_VERIFY_FAILED",
            "message": "离线清单写入后复核失败。",
            "suggestion": "不要交付该 wheels；按 manifest_problems 补齐文件。",
            "manifest_problems": verified.get("manifest_problems", []),
        }
    return {"ok": True, "code": "OFFLINE_READY", "wheel_count": len(files), "manifest": "wheels/OFFLINE_MANIFEST.json"}


def main() -> int:
    parser = argparse.ArgumentParser(description="为 IT 已提供的 wheels 生成并验证离线清单")
    parser.add_argument("project_dir", nargs="?", default=".")
    args = parser.parse_args()
    result = prepare(Path(args.project_dir).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
