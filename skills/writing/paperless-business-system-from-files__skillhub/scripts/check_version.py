#!/usr/bin/env python3
"""校验技能说明、脚手架及可选平台元数据中的基线版本。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SEMVER = r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?"
SKILL_RE = re.compile(rf"当前技能基线\s*[：:]\s*\*\*({SEMVER})\*\*")
SCAFFOLD_RE = re.compile(rf"^SKILL_VERSION\s*=\s*['\"]({SEMVER})['\"]", re.MULTILINE)


def read_required(path: Path, pattern: re.Pattern[str], label: str) -> str:
    if not path.is_file():
        raise ValueError(f"缺少{label}：{path.name}")
    match = pattern.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{label}中未找到语义版本")
    return match.group(1)


def collect_versions(root: Path) -> dict[str, str]:
    versions = {
        "SKILL.md": read_required(root / "SKILL.md", SKILL_RE, "技能说明"),
        "create_project_scaffold.py": read_required(
            root / "scripts" / "create_project_scaffold.py", SCAFFOLD_RE, "脚手架脚本"
        ),
    }

    version_file = root / "VERSION"
    if version_file.is_file():
        versions["VERSION"] = version_file.read_text(encoding="utf-8").strip()

    meta_file = root / "_meta.json"
    if meta_file.is_file():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        versions["_meta.json"] = str(meta.get("version", "")).strip()
    return versions


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        versions = collect_versions(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[PB501] 技能基线检查失败：{exc}")
        print("处理：修复缺失或无法读取的版本来源后重新运行本命令。")
        print("恢复点：发布检查。")
        return 1

    invalid = {name: value for name, value in versions.items() if not re.fullmatch(SEMVER, value)}
    if invalid or len(set(versions.values())) != 1:
        detail = "；".join(f"{name}={value or '缺失'}" for name, value in versions.items())
        print(f"[PB501] 技能基线不一致：{detail}")
        print("处理：同步 SKILL.md、脚手架常量及存在的平台版本文件，不要只改其中一处。")
        print("恢复点：发布检查。")
        return 1

    version = next(iter(versions.values()))
    print(f"[通过] 技能基线一致：{version}（核对 {len(versions)} 个来源）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
