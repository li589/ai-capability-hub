#!/usr/bin/env python3
"""Inspect a WorkBuddy migration package without importing.

Usage:
    python info.py --package <path> [--json]

Reads manifest.json + optional DB + workspace manifest from a migration
package and prints a human-readable summary.  When `--json` is given,
outputs machine-readable JSON.

Inspired by wb-migrate v2.0.3's `info` command.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make scripts.lib importable
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from scripts.lib import manifest as M
from scripts.lib.automap import (
    infer_source_home,
    needs_remapping,
    generate_rules as auto_path_rules,
    get_target_info,
)


# ---------------------------------------------------------------------------
# Unpack
# ---------------------------------------------------------------------------

def _unpack_package(pkg: Path, td: Path) -> Path:
    """Unpack zip/tar.gz or return directory as-is."""
    if pkg.is_dir():
        return pkg
    if pkg.is_file() and pkg.suffix.lower() == ".zip":
        extract_to = td / "unpacked"
        extract_to.mkdir()
        with zipfile.ZipFile(pkg) as zf:
            zf.extractall(extract_to)
        return extract_to
    if pkg.is_file() and pkg.name.lower().endswith(".tar.gz"):
        import tarfile as _tar
        extract_to = td / "unpacked"
        extract_to.mkdir()
        with _tar.open(pkg, "r:gz") as tf:
            tf.extractall(extract_to)
        return extract_to
    raise ValueError(f"Unsupported package: {pkg}")


# ---------------------------------------------------------------------------
# DB stats
# ---------------------------------------------------------------------------

def _db_stats(db_path: Path) -> Dict[str, Any]:
    """Extract statistics from a migration DB file."""
    if not db_path.is_file():
        return {"exists": False}

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        stats: Dict[str, Any] = {"exists": True, "tables": {}}

        # Row counts for key tables
        for table in ["sessions", "automations", "automation_runs",
                       "automation_runtime_state", "workspaces"]:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                stats["tables"][table] = row[0] if row else 0
            except sqlite3.OperationalError:
                stats["tables"][table] = 0

        # Distinct user_ids
        uids = conn.execute(
            "SELECT DISTINCT user_id FROM sessions "
            "WHERE user_id IS NOT NULL AND user_id != ''"
        ).fetchall()
        stats["user_ids"] = [u[0] for u in uids]

        # Estimated DB size
        stats["size_bytes"] = db_path.stat().st_size

        # Schema version (tables present)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        stats["all_tables"] = [t[0] for t in tables]

        conn.close()
        return stats
    except sqlite3.Error as e:
        return {"exists": True, "error": str(e)}


# ---------------------------------------------------------------------------
# Workspace manifest
# ---------------------------------------------------------------------------

def _read_workspace_manifest(ws_zip_path: Optional[Path]) -> Optional[Dict]:
    """Read manifest.json from a workspace bundle zip."""
    if not ws_zip_path or not ws_zip_path.is_file():
        return None
    try:
        with zipfile.ZipFile(ws_zip_path) as zf:
            if "manifest.json" in zf.namelist():
                return json.loads(zf.read("manifest.json"))
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def _fmt_size(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f} GB"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.1f} KB"
    return f"{n} B"


# ---------------------------------------------------------------------------
# Main info command
# ---------------------------------------------------------------------------

def cmd_info(package: Path, output_json: bool = False) -> Dict[str, Any]:
    """Inspect a migration package and return structured info."""

    info: Dict[str, Any] = {
        "package_path": str(package),
        "package_size": package.stat().st_size if package.is_file() else None,
    }

    with tempfile.TemporaryDirectory(prefix="wb-info-") as td:
        pkg_root = _unpack_package(package, Path(td))

        # 1. Manifest
        manifest_path = pkg_root / "manifest.json"
        if not manifest_path.is_file():
            info["error"] = "manifest.json not found in package"
            return info

        try:
            meta = M.Manifest.load(manifest_path)
        except Exception as e:
            info["error"] = f"Failed to parse manifest: {e}"
            return info

        info["manifest"] = {
            "tool_version": meta.tool_version,
            "schema_version": meta.schema_version,
            "export_time": meta.export_time,
            "source_variant": meta.source_variant,
            "source_root": meta.source_root,
            "source_user_id": meta.source_user_id,
            "source_user_ids_all": meta.source_user_ids_all,
            "source_os": meta.source_os or "unknown",
            "source_hostname": meta.source_hostname or "unknown",
            "source_home": meta.source_home or infer_source_home(meta.to_dict()) or "unknown",
            "options": meta.options,
        }

        # 2. DB stats
        db_path = pkg_root / "db" / "workbuddy.db"
        info["database"] = _db_stats(db_path)

        # 3. Asset inventory summary (what's in the manifest)
        assets = meta.asset_inventory.get("file_assets", [])
        info["asset_files"] = [
            {"path": a["path"], "type": a["type"], "description": a.get("description", "")}
            for a in assets
        ]

        # 4. Conversations count
        convo_path = pkg_root / "projects"
        if convo_path.is_dir():
            jsonl_count = len(list(convo_path.rglob("*.jsonl")))
            meta_count = len(list(convo_path.rglob("meta.json")))
            info["conversations"] = {"jsonl_files": jsonl_count, "meta_files": meta_count}
        else:
            info["conversations"] = {"jsonl_files": 0, "meta_files": 0}

        # 5. Skills count
        skills_path = pkg_root / "skills"
        if skills_path.is_dir():
            info["skills"] = sum(1 for _ in skills_path.iterdir() if _.is_dir())
        else:
            info["skills"] = 0

        # 6. Cross-platform advice
        target = get_target_info()
        manifest_dict = meta.to_dict()
        remap = needs_remapping(manifest_dict)
        info["cross_platform"] = {
            "needs_remapping": remap,
            "source_os": meta.source_os or "unknown",
            "target_os": target["os"],
            "source_home": info["manifest"]["source_home"],
            "target_home": target["home"],
            "auto_path_rules": auto_path_rules(manifest_dict) if remap else {},
            "advice": (
                "Use --auto-map for automatic cross-platform path remapping."
                if remap else
                "Same platform detected: no path remapping needed."
            ),
        }

        # 7. Workspace bundle companion
        info["workspaces_package"] = meta.workspaces_package

    return info


def print_human(info: Dict[str, Any]):
    """Print a human-readable info report."""
    if "error" in info:
        print(f"  [error] {info['error']}")
        return

    m = info["manifest"]

    print()
    print("=" * 60)
    print(f"  WorkBuddy 迁移包")
    print("=" * 60)
    print(f"  文件:         {info['package_path']}")
    if info.get("package_size"):
        print(f"  大小:         {_fmt_size(info['package_size'])}")
    print(f"  工具版本:     {m['tool_version']} (schema v{m['schema_version']})")
    print(f"  导出时间:     {m['export_time']}")
    print()

    print(f"  --- 源平台 ---")
    print(f"  变体:         {m['source_variant']} ({m['source_root']})")
    print(f"  OS:           {m['source_os']}")
    print(f"  主机:         {m['source_hostname']}")
    print(f"  Home:         {m['source_home']}")
    print(f"  当前 user_id: {m['source_user_id']}")
    if len(m['source_user_ids_all']) > 1:
        print(f"  所有 user_id: {', '.join(m['source_user_ids_all'])}")
    print()

    db = info["database"]
    if db["exists"] and "tables" in db:
        print(f"  --- 数据库 ---")
        print(f"  大小:         {_fmt_size(db.get('size_bytes', 0))}")
        for table, count in db["tables"].items():
            print(f"  {table:30s} {count:>6} 行")
        if db.get("user_ids"):
            print(f"  不同 user_id: {len(db['user_ids'])}")
        if db.get("all_tables"):
            other = [t for t in db["all_tables"]
                     if t not in db["tables"] and t != "sqlite_sequence"]
            if other:
                print(f"  其他表:       {', '.join(other)}")
    elif not db["exists"]:
        print(f"  --- 数据库 ---")
        print(f"  (包内无 workbuddy.db)")
    else:
        print(f"  --- 数据库 ---")
        print(f"  [error] {db.get('error', 'unknown')}")
    print()

    print(f"  --- 资产概要 ---")
    skills = info.get("skills", 0)
    print(f"  Skills:       {skills} 个")
    conv = info.get("conversations", {})
    print(f"  Conversations: {conv.get('jsonl_files', 0)} jsonl, "
          f"{conv.get('meta_files', 0)} meta.json")
    for asset in info.get("asset_files", []):
        note = ""
        if asset["type"] == "dir-of-dirs":
            note = "(目录)"
        elif asset["type"] == "dir-of-files":
            note = "(文件集)"
        print(f"  {asset['path']:30s} {asset['description']} {note}")
    if info.get("workspaces_package"):
        print(f"  产物包:       {info['workspaces_package']}")
    print()

    cp = info["cross_platform"]
    print(f"  --- 跨平台检测 ---")
    print(f"  源平台:   {cp['source_os']}")
    print(f"  目标平台: {cp['target_os']}")
    if cp["needs_remapping"]:
        print(f"  ⚠  需要路径映射!")
        print(f"  源 Home:  {cp['source_home']}")
        print(f"  目标 Home: {cp['target_home']}")
        if cp["auto_path_rules"]:
            print(f"  建议映射:")
            for src, dst in cp["auto_path_rules"].items():
                print(f"    {src} → {dst}")
    print(f"  建议:     {cp['advice']}")
    print()
    print("=" * 60)
    print(f"  导入命令:")
    if cp["needs_remapping"]:
        print(f"  python scripts/import.py --package {info['package_path']} --auto-map")
    else:
        print(f"  python scripts/import.py --package {info['package_path']}")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Inspect a WorkBuddy migration package."
    )
    ap.add_argument("--package", required=True, help="Migration zip or directory")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = ap.parse_args()

    pkg = Path(args.package).expanduser()
    if not pkg.exists():
        print(f"[error] Package not found: {pkg}", file=sys.stderr)
        return 1

    info = cmd_info(pkg)

    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print_human(info)

    return 0 if "error" not in info else 1


if __name__ == "__main__":
    sys.exit(main())
