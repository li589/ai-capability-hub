#!/usr/bin/env python3
"""Copy the required standalone energy daily-report application into a generated project."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent / "resources" / "standalone-energy-daily-report"
FILES = ["energy_daily_report.py", "README_STANDALONE.md", "requirements_standalone.txt", "build_exe_windows.py"]
RETRY_MAX = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure(project_dir: Path, *, overwrite: bool = False) -> dict:
    project = project_dir.resolve()
    target = project / "standalone"
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    skipped = []
    for name in FILES:
        source = SOURCE_DIR / name
        destination = target / name
        if not source.is_file():
            return {"ok": False, "code": "STANDALONE_TEMPLATE_MISSING", "message": f"技能包缺少独立程序模板文件：{source.name}，请确认技能包已完整解压。"}
        if destination.exists() and not overwrite:
            skipped.append(destination.relative_to(project).as_posix())
            continue
        for attempt in range(RETRY_MAX + 1):
            try:
                shutil.copy2(source, destination)
                break
            except OSError:
                if attempt == RETRY_MAX:
                    return {"ok": False, "code": "STANDALONE_COPY_FAILED", "message": f"无法复制 {name} 到 standalone 目录，请检查磁盘空间和目录权限。"}
                time.sleep(0.5)
        copied.append({"path": destination.relative_to(project).as_posix(), "sha256": sha256(destination)})
    manifest = {
        "schema_version": "1.0",
        "required_entry": "standalone/energy_daily_report.py",
        "copied": copied,
        "skipped": skipped,
        "run": "python standalone/energy_daily_report.py",
        "self_test": "python standalone/energy_daily_report.py --self-test",
        "build_exe": "python standalone/build_exe_windows.py",
    }
    (target / "standalone-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="向生成项目写入独立 PY 能源日报")
    parser.add_argument("project_dir")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(json.dumps(ensure(Path(args.project_dir), overwrite=args.overwrite), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
