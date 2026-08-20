#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate and materialize the complete LAN energy-daily-report reference system.

The reference archive is treated as a reusable code baseline, never as business truth.
Before any project files are written, the archive is checked for readability, CRC,
unsafe paths, duplicate normalized paths, symlink-like entries and required core files.
Extraction first happens in a temporary staging directory; only a validated staging
copy is then merged into the target project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCE_ARCHIVE = SKILL_DIR / "resources" / "lan-energy-daily-report-reference.zip"
CORE_RELATIVE = [
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
    "01_服务端_完整程序/start_windows.bat",
    "01_服务端_完整程序/stop_windows.bat",
    "一键启动_Windows.bat",
    "一键停止_Windows.bat",
    "一键启动_macOS.command",
    "一键停止_macOS.command",
    "01_服务端_完整程序/templates/index.html",
    "01_服务端_完整程序/static/js/app.js",
    "01_服务端_完整程序/static/css/app.css",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member_path(name: str) -> Path:
    clean = name.replace("\\", "/")
    rel = Path(clean)
    if not clean or rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe archive member: {name}")
    # Drive-letter style paths are unsafe even on POSIX hosts.
    if rel.parts and ":" in rel.parts[0]:
        raise ValueError(f"unsafe archive member: {name}")
    return rel


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return bool(mode and stat.S_ISLNK(mode))


def check_reference() -> dict:
    """Read-only health check for the embedded LAN baseline archive."""
    if not REFERENCE_ARCHIVE.is_file():
        return {
            "ok": False,
            "code": "LAN_REFERENCE_MISSING",
            "message": "技能包缺少完整局域网系统参考基线。请重新获取完整技能 ZIP，不要从其他项目临时拼接模板。",
            "recovery": ["确认 resources/lan-energy-daily-report-reference.zip 存在", "重新校验技能包 FILES_SHA256.txt", "使用完整技能包重新解压后再执行"],
        }

    try:
        archive_hash = sha256(REFERENCE_ARCHIVE)
        with zipfile.ZipFile(REFERENCE_ARCHIVE) as archive:
            normalized: set[str] = set()
            members: list[str] = []
            total_uncompressed = 0
            for info in archive.infolist():
                rel = _safe_member_path(info.filename)
                normalized_name = rel.as_posix().rstrip("/")
                if normalized_name in normalized and normalized_name:
                    return {
                        "ok": False,
                        "code": "LAN_REFERENCE_DUPLICATE_PATH",
                        "message": f"完整局域网基线存在重复规范化路径：{normalized_name}",
                    }
                if normalized_name:
                    normalized.add(normalized_name)
                    members.append(normalized_name)
                if _is_symlink(info):
                    return {
                        "ok": False,
                        "code": "LAN_REFERENCE_SYMLINK_REJECTED",
                        "message": f"完整局域网基线包含符号链接样式成员，已拒绝：{info.filename}",
                    }
                total_uncompressed += max(0, int(info.file_size))

            bad = archive.testzip()
            if bad:
                return {
                    "ok": False,
                    "code": "LAN_REFERENCE_CRC_FAILED",
                    "message": f"完整局域网基线 CRC 校验失败：{bad}",
                    "archive_sha256": archive_hash,
                }

            missing = [rel for rel in CORE_RELATIVE if rel not in normalized]
            if missing:
                return {
                    "ok": False,
                    "code": "LAN_REFERENCE_CORE_MISSING",
                    "message": "完整局域网基线缺少核心源码或启停/前端资源。",
                    "core_missing": missing,
                    "archive_sha256": archive_hash,
                }

            return {
                "ok": True,
                "code": "LAN_REFERENCE_HEALTHY",
                "archive": REFERENCE_ARCHIVE.name,
                "archive_sha256": archive_hash,
                "member_count": len(archive.infolist()),
                "file_member_count": sum(1 for i in archive.infolist() if not i.is_dir()),
                "total_uncompressed_bytes": total_uncompressed,
                "core_file_count": len(CORE_RELATIVE),
                "checks": ["zip_open", "safe_paths", "no_duplicate_paths", "no_symlink_entries", "crc", "core_files"],
            }
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        return {
            "ok": False,
            "code": "LAN_REFERENCE_INVALID",
            "message": f"完整局域网基线无法安全读取：{exc}",
            "recovery": ["重新校验技能包哈希", "重新解压完整技能包", "不要继续向业务项目写入半成品"],
        }


def _extract_to_staging(staging: Path) -> None:
    with zipfile.ZipFile(REFERENCE_ARCHIVE) as archive:
        for info in archive.infolist():
            rel = _safe_member_path(info.filename)
            if _is_symlink(info):
                raise ValueError(f"symlink member rejected: {info.filename}")
            if not rel.parts or "__pycache__" in rel.parts or rel.suffix.lower() in {".pyc", ".pyo"}:
                continue
            dst = staging / rel
            if info.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as src, dst.open("wb") as out:
                shutil.copyfileobj(src, out)


def ensure(project_dir: Path, *, overwrite: bool = False) -> dict:
    health = check_reference()
    if not health.get("ok"):
        return health

    project = project_dir.resolve()
    project.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0

    try:
        with tempfile.TemporaryDirectory(prefix="lan-energy-baseline-staging-") as temp:
            staging = Path(temp)
            _extract_to_staging(staging)
            missing_staging = [rel for rel in CORE_RELATIVE if not (staging / rel).is_file()]
            if missing_staging:
                return {
                    "ok": False,
                    "code": "LAN_REFERENCE_STAGING_INCOMPLETE",
                    "message": "基线临时展开后核心文件不完整，未继续复制到业务项目。",
                    "core_missing": missing_staging,
                    "archive_sha256": health.get("archive_sha256"),
                }

            for src in sorted(staging.rglob("*")):
                rel = src.relative_to(staging)
                dst = project / rel
                if src.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists() and not overwrite:
                    skipped += 1
                    continue
                shutil.copy2(src, dst)
                copied += 1
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        return {
            "ok": False,
            "code": "LAN_REFERENCE_STAGE_FAILED",
            "message": f"完整局域网基线临时展开失败，未把未验证内容继续写入项目：{exc}",
            "archive_sha256": health.get("archive_sha256"),
        }

    missing = [rel for rel in CORE_RELATIVE if not (project / rel).is_file()]
    py_files = sorted(p for p in project.rglob("*.py") if "__pycache__" not in p.parts)
    manifest = {
        "schema_version": "1.1",
        "ok": not missing,
        "reference_baseline": "embedded-complete-lan-system-code-baseline",
        "reference_archive": REFERENCE_ARCHIVE.name,
        "reference_archive_sha256": health.get("archive_sha256"),
        "reference_health_checks": health.get("checks", []),
        "verified_before_copy": True,
        "staging_verified_before_copy": True,
        "copied_files": copied,
        "skipped_files": skipped,
        "python_source_count": len(py_files),
        "core_missing": missing,
        "required_output": "本地部署ZIP必须保留全部Python源码和EXE构建源码",
        "core_sha256": {
            rel: sha256(project / rel)
            for rel in CORE_RELATIVE
            if (project / rel).is_file()
        },
    }
    (project / "FULL_LAN_SOURCE_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="校验或写入完整局域网能源日报系统源码基线")
    parser.add_argument("project_dir", nargs="?", help="目标项目目录；--check-only 时可省略")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check-only", action="store_true", help="只读校验内置完整局域网基线，不写入项目")
    args = parser.parse_args()

    if args.check_only:
        result = check_reference()
    else:
        if not args.project_dir:
            parser.error("未使用 --check-only 时必须提供 project_dir")
        result = ensure(Path(args.project_dir), overwrite=args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
