"""Automatic cross-platform path and user_id mapping for WorkBuddy migration.

Inspired by wb-migrate v2.0.3's --auto-map feature.

Reads source metadata (OS, username, home) from the migration package manifest,
detects the target platform, and automatically derives path-map rules.
Applies them to DB columns, JSON fields, and project directory names.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import pathmap as PM


# --- Platform detection --------------------------------------------------------

OS_HOME_PATTERNS = {
    "Darwin":  "/Users/{username}",
    "Windows": "{drive}:\\Users\\{username}",
    "Linux":   "/home/{username}",
}


def get_target_info() -> Dict[str, str]:
    """Gather target machine platform info."""
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "username": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "hostname": platform.node(),
        "home": str(Path.home()),
    }


def infer_source_home(manifest: dict) -> Optional[str]:
    """Derive the source machine's home directory from manifest metadata."""
    src_os = manifest.get("source_os", "")
    src_user = manifest.get("source_username", "")
    src_home = manifest.get("source_home", "")
    src_root = manifest.get("source_root", "")

    if src_home:
        return src_home

    # Fallback: reconstruct from source_root (typically ~/.workbuddy)
    if src_root:
        if src_root.endswith("/.workbuddy"):
            return src_root[:-len("/.workbuddy")]
        if src_root.endswith("\\.workbuddy"):
            return src_root[:-len("\\.workbuddy")]

    # Last fallback: use OS patterns
    if src_os == "Darwin":
        return f"/Users/{src_user}" if src_user else None
    elif src_os == "Windows":
        return f"C:\\Users\\{src_user}" if src_user else None
    elif src_os == "Linux":
        return f"/home/{src_user}" if src_user else None

    return None


def needs_remapping(manifest: dict) -> bool:
    """Check whether cross-platform or different-user mapping is needed."""
    src_os = manifest.get("source_os", "")
    target = get_target_info()
    # Different OS → definitely needs remapping
    if src_os and src_os != target["os"]:
        return True
    # Same OS but different home path → user might have changed
    src_home = infer_source_home(manifest)
    if src_home and Path(src_home) != Path(target["home"]):
        return True
    return False


def generate_rules(manifest: dict) -> Dict[str, str]:
    """Auto-generate path-map rules from manifest metadata.

    Returns dict of {source_prefix: target_prefix} for PathMapper.
    """
    src_home = infer_source_home(manifest)
    target = get_target_info()
    rules: Dict[str, str] = {}

    if not src_home:
        return rules

    target_home = target["home"]
    src_os = manifest.get("source_os", "")

    # Primary rule: source_home → target_home
    if src_home != target_home:
        rules[src_home] = target_home

    # Additional: if usernames differ, add username-only remapping
    src_user = manifest.get("source_username", "")
    tgt_user = target.get("username", "")
    if src_user and tgt_user and src_user != tgt_user:
        if src_os == "Darwin" or src_os == "Linux":
            rules[f"/Users/{src_user}"] = target_home
            rules[f"/home/{src_user}"] = target_home
        elif src_os == "Windows":
            rules[f"C:\\Users\\{src_user}"] = target_home

    return rules


# --- User ID auto-mapping -------------------------------------------------------

@dataclass
class UIDMapping:
    source_uids: List[str] = field(default_factory=list)
    target_uid: str = ""
    mapping: Dict[str, str] = field(default_factory=dict)


def detect_source_uids(db_path: Path) -> List[str]:
    """Extract all distinct user_ids from a migration DB."""
    import sqlite3
    if not db_path.is_file():
        return []
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        rows = conn.execute(
            "SELECT DISTINCT user_id FROM sessions WHERE user_id IS NOT NULL AND user_id != ''"
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except sqlite3.Error:
        return []


def detect_target_uid(db_path: Path) -> Optional[str]:
    """Detect target machine's current user_id from DB."""
    import sqlite3
    if not db_path.is_file():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT user_id FROM sessions WHERE user_id IS NOT NULL AND user_id != '' "
            "ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def generate_uid_map(source_uids: List[str], target_uid: str) -> Dict[str, str]:
    """Map all source user_ids to target_uid."""
    if not target_uid or not source_uids:
        return {}
    return {uid: target_uid for uid in source_uids}


# --- Apply auto-mapping ---------------------------------------------------------

@dataclass
class AutoMapPlan:
    needs_remap: bool
    source_os: str
    target_os: str
    source_home: str
    target_home: str
    path_rules: Dict[str, str]
    uid_map: Dict[str, str]
    notes: List[str] = field(default_factory=list)


def plan(manifest: dict, target_db_path: Optional[Path] = None) -> AutoMapPlan:
    """Generate an auto-mapping plan without applying anything.

    Returns AutoMapPlan with all detected rules and mapping suggestions.
    """
    src_os = manifest.get("source_os", "unknown")
    target = get_target_info()
    tgt_os = target["os"]
    src_home = infer_source_home(manifest) or "unknown"
    tgt_home = target["home"]
    path_rules = generate_rules(manifest)

    # UID detection
    uid_map: Dict[str, str] = {}
    src_uids = manifest.get("user_ids", [])
    tgt_uid = None
    if target_db_path:
        tgt_uid = detect_target_uid(target_db_path)
    if src_uids and tgt_uid:
        uid_map = generate_uid_map(src_uids, tgt_uid)

    plan_obj = AutoMapPlan(
        needs_remap=needs_remapping(manifest),
        source_os=src_os,
        target_os=tgt_os,
        source_home=src_home,
        target_home=tgt_home,
        path_rules=path_rules,
        uid_map=uid_map,
    )

    if not plan_obj.needs_remap:
        plan_obj.notes.append("Same platform and home directory, no remapping needed.")
    if path_rules:
        plan_obj.notes.append(
            f"Auto-detected {len(path_rules)} path mapping rule(s)."
        )
    if uid_map:
        plan_obj.notes.append(
            f"Mapping {len(uid_map)} source uid(s) → target uid {tgt_uid}."
        )
    if not uid_map and src_uids:
        plan_obj.notes.append(
            "Target user_id not found. Use --target-user-id to specify."
        )

    return plan_obj


def apply_path_remapping(
    db_path: Path,
    path_rules: Dict[str, str],
    src_os: str = "unknown",
    dst_os: str = "",
) -> int:
    """Apply path remapping to target DB in-place.

    Returns count of rows remapped.
    """
    import sqlite3

    if not path_rules:
        return 0

    mapper = PM.PathMapper(
        rules=[(src, dst) for src, dst in path_rules.items()],
        src_os=src_os,
        dst_os=dst_os or platform.system().lower(),
    ) if hasattr(PM, 'PathMapper') else None

    if not mapper:
        return 0

    total = 0
    conn = sqlite3.connect(str(db_path))

    # sessions.cwd
    for row in conn.execute("SELECT id, cwd FROM sessions WHERE cwd IS NOT NULL").fetchall():
        result = mapper.rewrite(row[1])
        if result and result.new_path != row[1]:
            conn.execute("UPDATE sessions SET cwd = ? WHERE id = ?", (result.new_path, row[0]))
            total += 1

    # workspaces.path
    for row in conn.execute("SELECT path FROM workspaces").fetchall():
        result = mapper.rewrite(row[0])
        if result and result.new_path != row[0]:
            conn.execute("UPDATE workspaces SET path = ? WHERE path = ?", (result.new_path, row[0]))
            total += 1

    # automations.cwds (JSON array)
    for row in conn.execute("SELECT id, cwds FROM automations WHERE cwds IS NOT NULL").fetchall():
        try:
            cwds = json.loads(row[1])
            if isinstance(cwds, list):
                new_cwds = []
                changed = False
                for c in cwds:
                    r = mapper.rewrite(c) if isinstance(c, str) else None
                    if r and r.new_path != c:
                        new_cwds.append(r.new_path)
                        changed = True
                    else:
                        new_cwds.append(c)
                if changed:
                    conn.execute("UPDATE automations SET cwds = ? WHERE id = ?",
                                 (json.dumps(new_cwds), row[0]))
                    total += 1
        except (json.JSONDecodeError, TypeError):
            pass

    # automation_runs.source_cwd
    for row in conn.execute("SELECT id, source_cwd FROM automation_runs WHERE source_cwd IS NOT NULL").fetchall():
        result = mapper.rewrite(row[1])
        if result and result.new_path != row[1]:
            conn.execute("UPDATE automation_runs SET source_cwd = ? WHERE id = ?",
                         (result.new_path, row[0]))
            total += 1

    conn.commit()
    conn.close()
    return total


def apply_uid_remapping(
    db_path: Path,
    uid_map: Dict[str, str],
    projects_dir: Optional[Path] = None,
    memory_dir: Optional[Path] = None,
    connectors_dir: Optional[Path] = None,
) -> Dict[str, int]:
    """Rewrite user_id in DB and rename associated files/dirs.

    Returns counts: {db_sessions, memory_files, connectors_dirs, projects}
    """
    import sqlite3

    counts = {"db_sessions": 0, "memory_files": 0, "connectors_dirs": 0, "projects": 0}
    if not uid_map:
        return counts

    # DB: update sessions.user_id
    conn = sqlite3.connect(str(db_path))
    for src_uid, dst_uid in uid_map.items():
        c = conn.execute(
            "UPDATE sessions SET user_id = ? WHERE user_id = ?",
            (dst_uid, src_uid),
        ).rowcount
        counts["db_sessions"] += c
    conn.commit()
    conn.close()

    # Rename memory files
    if memory_dir and memory_dir.is_dir():
        for src_uid, dst_uid in uid_map.items():
            src_file = memory_dir / f"{src_uid}_memory.md"
            dst_file = memory_dir / f"{dst_uid}_memory.md"
            if src_file.exists() and not dst_file.exists():
                shutil.move(str(src_file), str(dst_file))
                counts["memory_files"] += 1

    # Rename connectors subdirs
    if connectors_dir and connectors_dir.is_dir():
        for src_uid, dst_uid in uid_map.items():
            src_sub = connectors_dir / src_uid
            dst_sub = connectors_dir / dst_uid
            if src_sub.is_dir() and not dst_sub.is_dir():
                shutil.move(str(src_sub), str(dst_sub))
                counts["connectors_dirs"] += 1

    return counts
