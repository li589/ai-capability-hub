#!/usr/bin/env python3
"""
workspace_cleaner.py — delete-recovery skill extension v0.1.0

定时清理 workspace 下的临时文件和过期文件，被删除的文件自动备份到 delete_backup/。
支持白名单配置，白名单内的文件/文件夹不会被清理。

功能特性：
- 每 24 小时自动运行一次（时间触发）
- 支持文件扩展名、文件名、文件夹名白名单
- 删除前自动备份到 delete_backup/（复用 delete_recovery.py）
- 支持手动触发清理（python workspace_cleaner.py run）
- 配置通过 workspace_cleaner_whitelist.json 管理

文件结构：
{workspace}/
├── workspace_cleaner_whitelist.json   ← 白名单配置（用户编辑）
├── workspace_cleaner_config.json       ← 运行配置（自动管理）
└── skills/delete-recovery/scripts/
    ├── delete_recovery.py              ← 核心备份恢复脚本
    └── workspace_cleaner.py            ← 本脚本

用法：
    python workspace_cleaner.py run              # 手动触发一次清理
    python workspace_cleaner.py show-whitelist   # 查看当前白名单
    python workspace_cleaner.py add-whitelist <path> [--type file|folder|ext]  # 添加白名单项
    python workspace_cleaner.py remove-whitelist <path>  # 移除白名单项
    python workspace_cleaner.py set-interval <hours>     # 设置清理间隔（小时）
    python workspace_cleaner.py set-expire-days <days>   # 设置过期天数
    python workspace_cleaner.py dry-run                   # 预览哪些文件会被删除（不实际删除）
    python workspace_cleaner.py status                   # 查看定时器状态
"""

import os
import sys
import json
import shutil
import tempfile
import hashlib
import hmac
import base64
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────────────
# Workspace root: scripts/ → skill/ → skills/ → workspace2/
# __file__ = C:\Users\user\.openclaw\workspace2\skills\delete-recovery\scripts\workspace_cleaner.py
#   .parent     = delete-recovery/scripts/
#   .parent     = delete-recovery/          (.parent.parent)
#   .parent     = skills/                           (.parent.parent.parent)
#   .parent     = workspace2/                        (.parent.parent.parent.parent)
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = Path(__file__).parent.resolve()
DELETE_RECOVERY_SCRIPT = SCRIPTS_DIR / "delete_recovery.py"

# All data lives under {workspace}/.delete_recovery/
_DATA_DIR = WORKSPACE_ROOT / ".delete_recovery"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

BACKUP_ROOT = _DATA_DIR / "delete_backup"
_EXTENSION_DIR = _DATA_DIR / "workspace_cleaner"
_EXTENSION_DIR.mkdir(parents=True, exist_ok=True)

WHITELIST_FILE = _EXTENSION_DIR / "workspace_cleaner_whitelist.json"
CONFIG_FILE = _EXTENSION_DIR / "workspace_cleaner_config.json"
TIMER_FILE = _EXTENSION_DIR / "workspace_cleaner_timer.json"

# ─── Default config ───────────────────────────────────────────────────────────
DEFAULT_INTERVAL_HOURS = 24
DEFAULT_EXPIRE_DAYS = 7

# ─── Built-in always-protected paths (hardcoded — cannot be overridden) ─────────
ALWAYS_PROTECTED = {
    "AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md", "USER.md",
    "HEARTBEAT.md", "BOOTSTRAP.md",
    "skills", ".learnings",
    "workspace_cleaner_whitelist.json",
    "workspace_cleaner_config.json",
    "workspace_cleaner_timer.json",
    ".cleanup_timer",
    ".delete_recovery",   # protect the entire data directory
}

# ─── Default whitelist (applied if whitelist file doesn't exist) ────────────────
DEFAULT_WHITELIST = {
    "files":  [],   # exact filenames to protect, e.g. ["good.py", "README.md"]
    "folders": [],  # folder names to protect, e.g. ["log", "temp"]
    "exts":   [],   # extensions to protect, e.g. [".xlsx", ".docx"]
}


# ─── Config helpers ────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {
            "workspace": str(WORKSPACE_ROOT),
            "interval_hours": DEFAULT_INTERVAL_HOURS,
            "expire_days": DEFAULT_EXPIRE_DAYS,
            "auto_backup": True,
            "last_cleanup": None,
        }
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "workspace": str(WORKSPACE_ROOT),
            "interval_hours": DEFAULT_INTERVAL_HOURS,
            "expire_days": DEFAULT_EXPIRE_DAYS,
            "auto_backup": True,
            "last_cleanup": None,
        }


def _save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def _atomic_write(file_path: Path, content: str) -> None:
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(file_path.parent), prefix=".tmp_", suffix=".atomic")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, file_path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _load_whitelist() -> dict:
    """Load whitelist from JSON file, return DEFAULT_WHITELIST if missing."""
    if not WHITELIST_FILE.exists():
        return dict(DEFAULT_WHITELIST)
    try:
        w = json.loads(WHITELIST_FILE.read_text(encoding="utf-8"))
        return {
            "files":   list(w.get("files",   DEFAULT_WHITELIST["files"])),
            "folders": list(w.get("folders", DEFAULT_WHITELIST["folders"])),
            "exts":    list(w.get("exts",    DEFAULT_WHITELIST["exts"])),
        }
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_WHITELIST)


def _save_whitelist(wl: dict) -> None:
    content = json.dumps(wl, ensure_ascii=False, indent=2)
    _atomic_write(WHITELIST_FILE, content)


def _load_timer() -> dict:
    if not TIMER_FILE.exists():
        return {"last_run": None}
    try:
        return json.loads(TIMER_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_run": None}


def _save_timer(data: dict) -> None:
    _atomic_write(TIMER_FILE, json.dumps(data, ensure_ascii=False, indent=2))


def _should_run() -> bool:
    """Check if enough time has passed since last cleanup."""
    cfg = _load_config()
    timer = _load_timer()
    last = timer.get("last_run")
    if last is None:
        return True
    try:
        last_time = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
        elapsed = datetime.now() - last_time
        return elapsed >= timedelta(hours=cfg.get("interval_hours", DEFAULT_INTERVAL_HOURS))
    except (ValueError, TypeError):
        return True


# ─── Whitelist matching ───────────────────────────────────────────────────────

def _is_whitelisted(rel_path: str, wl: dict) -> bool:
    """
    Returns True if rel_path is protected by the whitelist.
    rel_path: relative path from workspace root (e.g. "log/test.txt" or "temp/")
    """
    name = Path(rel_path).name
    parent = str(Path(rel_path).parent)

    # 1. Exact filename match
    if name in wl.get("files", []):
        return True
    # 2. Folder name match (if path refers to a directory or parent dir matches)
    for folder in wl.get("folders", []):
        if folder in parent.split(os.sep) or folder in rel_path.split(os.sep):
            return True
    # 3. Extension match
    for ext in wl.get("exts", []):
        if name.endswith(ext):
            return True
    return False


def _is_always_protected(name: str) -> bool:
    """Check against hardcoded always-protected list."""
    return name in ALWAYS_PROTECTED


def _is_temp_file(name: str) -> bool:
    """Check if filename looks like a common temp file pattern."""
    temp_patterns = [
        ".tmp", ".temp", ".bak", ".backup",
        "~", ".swp", ".swo", ".cache",
        "__pycache__",
        ".pyc", ".pyo",
        ".DS_Store", "Thumbs.db",
        "._", ".goutputstream",
    ]
    name_lower = name.lower()
    for p in temp_patterns:
        if name_lower == p.lower() or name_lower.endswith(p.lower()):
            return True
    return False


def _is_temp_dir(name: str) -> bool:
    """Check if directory name looks like a temp/cache directory."""
    temp_dir_names = [
        "__pycache__", ".pytest_cache", ".mypy_cache",
        ".tox", ".nox", ".egg-info",
        ".git", ".svn", ".hg",  # version control — usually not temp
        "node_modules", ".cache", ".temp", ".tmp",
    ]
    name_lower = name.lower()
    # Only treat __pycache__, .pytest_cache, etc. as temp dirs
    # (exclude .git, node_modules — those are versioned, not temp)
    temp_only = ["__pycache__", ".pytest_cache", ".mypy_cache", ".nox"]
    for d in temp_only:
        if name_lower == d.lower():
            return True
    # Also treat dirs ending in .pyc (some tools create them)
    if name_lower.endswith(".pyc") or name_lower.endswith(".pyo"):
        return True
    return False


# ─── Backup via delete_recovery.py ───────────────────────────────────────────

def _backup_file_using_delete_recovery(file_path: Path, original_path_str: str) -> bool:
    """
    Use the existing delete_recovery.py to back up a file before deletion.
    Returns True if backup succeeded, False otherwise.
    """
    if not DELETE_RECOVERY_SCRIPT.exists():
        return False
    try:
        # Encode path for CLI: replace \ with / for safety
        encoded = str(file_path).replace("\\", "/")
        original = original_path_str.replace("\\", "/")
        result = subprocess.run(
            [sys.executable, str(DELETE_RECOVERY_SCRIPT),
             "backup", encoded, original, "workspace_cleaner"],
            capture_output=True, text=True, timeout=60,
            cwd=str(WORKSPACE_ROOT),
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


# ─── Core cleanup logic ───────────────────────────────────────────────────────

def _scan_workspace(workspace: Path, wl: dict, expire_days: int) -> dict:
    """
    Scan workspace and return files eligible for cleanup.
    Returns {"files": [(rel_path, mtime_ts), ...], "skipped": [reasons...]}
    """
    cutoff = datetime.now() - timedelta(days=expire_days)
    candidates = []
    skipped_reasons = {"protected": [], "whitelisted": [], "recent": [], "errors": []}

    try:
        for root, dirs, files in os.walk(workspace):
            root_path = Path(root)
            rel_root = root_path.relative_to(workspace)

            # Check if this directory itself is protected
            rel_str = str(rel_root).replace("\\", "/")
            if rel_root.name and (_is_always_protected(rel_root.name) or _is_whitelisted(rel_str, wl)):
                # Don't descend into protected folders
                dirs[:] = []
                skipped_reasons["protected"].append(str(rel_root))
                continue

            for d in dirs[:]:
                # Skip protected subdirectories
                if _is_always_protected(d) or _is_whitelisted(f"{rel_str}/{d}", wl):
                    dirs.remove(d)
                    skipped_reasons["protected"].append(f"{rel_str}/{d}")
                    continue
                # Temp directories (__pycache__, .pyc dirs, etc.) → mark as cleanup candidate if expired
                if _is_temp_dir(d):
                    try:
                        dir_path = root_path / d
                        mtime = datetime.fromtimestamp(dir_path.stat().st_mtime)
                        if mtime < cutoff:
                            candidates.append((f"{rel_str}/{d}", dir_path.stat().st_mtime))
                            dirs.remove(d)  # don't descend into it
                        else:
                            skipped_reasons["recent"].append(f"{rel_str}/{d}")
                            dirs.remove(d)
                    except OSError:
                        dirs.remove(d)
                    continue

            for fname in files:
                file_path = root_path / fname
                rel_path_obj = file_path.relative_to(workspace)
                rel_str = str(rel_path_obj).replace("\\", "/")

                # Always-protected check
                if _is_always_protected(fname):
                    skipped_reasons["protected"].append(rel_str)
                    continue

                # Whitelist check
                if _is_whitelisted(rel_str, wl):
                    skipped_reasons["whitelisted"].append(rel_str)
                    continue

                # Temp file pattern check
                if _is_temp_file(fname):
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff:
                            candidates.append((rel_str, file_path.stat().st_mtime))
                        else:
                            skipped_reasons["recent"].append(rel_str)
                    except OSError:
                        pass
                    continue

                # Non-temp, non-whitelisted: check age
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        candidates.append((rel_str, file_path.stat().st_mtime))
                    else:
                        skipped_reasons["recent"].append(rel_str)
                except OSError:
                    skipped_reasons["errors"].append(rel_str)
    except PermissionError as e:
        skipped_reasons["errors"].append(f"PermissionError: {e}")

    return {"files": candidates, "skipped": skipped_reasons}


def run_cleanup(dry_run: bool = False, force: bool = False) -> dict:
    """
    Main cleanup entrypoint.

    dry_run: if True, scan and return what would be deleted without deleting
    force:   if True, ignore the 24-hour timer and run immediately

    Returns dict with stats.
    """
    cfg = _load_config()
    wl = _load_whitelist()
    workspace = Path(cfg.get("workspace", str(WORKSPACE_ROOT)))

    if not force and not _should_run():
        timer = _load_timer()
        return {
            "ok": False,
            "reason": "timer_not_due",
            "message": "清理尚未到时间间隔，上次运行: "
                       f"{timer.get('last_run', '从未')}",
            "interval_hours": cfg.get("interval_hours", DEFAULT_INTERVAL_HOURS),
        }

    expire_days = cfg.get("expire_days", DEFAULT_EXPIRE_DAYS)
    result = _scan_workspace(workspace, wl, expire_days)
    candidates = result["files"]
    skipped = result["skipped"]

    deleted = []
    errors = []
    backed_up = []

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "candidates": sorted(candidates, key=lambda x: x[1]),
            "skipped": skipped,
            "candidate_count": len(candidates),
            "expire_days": expire_days,
            "workspace": str(workspace),
        }

    for rel_str, mtime in candidates:
        file_path = workspace / rel_str
        # Double-check still exists and not protected
        if not file_path.exists():
            continue
        if _is_always_protected(file_path.name):
            continue
        if _is_whitelisted(rel_str, wl):
            skipped["whitelisted"].append(rel_str)
            continue

        original_path_str = str(file_path.resolve())

        # Backup before delete (auto_backup config)
        if cfg.get("auto_backup", True):
            backup_ok = _backup_file_using_delete_recovery(file_path, original_path_str)
            if backup_ok:
                backed_up.append(rel_str)
            else:
                # Try manual backup to delete_backup directly
                _manual_backup(file_path, rel_str)

        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            deleted.append(rel_str)
        except OSError as e:
            errors.append({"file": rel_str, "error": str(e)})

    # Update timer
    _save_timer({"last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    return {
        "ok": True,
        "dry_run": False,
        "deleted": deleted,
        "backed_up": backed_up,
        "errors": errors,
        "skipped": skipped,
        "deleted_count": len(deleted),
        "backed_up_count": len(backed_up),
        "expire_days": expire_days,
        "workspace": str(workspace),
        "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _manual_backup(src: Path, rel_str: str) -> bool:
    """
    Fallback: manually copy file to delete_backup/timestamp/ when
    delete_recovery.py is unavailable. Mirrors the backup format.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = BACKUP_ROOT / timestamp
        backup_dir.mkdir(exist_ok=True)
        safe_name = rel_str.replace("/", "__").replace("\\", "__").replace(":", "")
        dest = backup_dir / safe_name
        shutil.copy2(src, dest)

        # Write .path file
        path_file = backup_dir / (safe_name + ".path")
        path_file.write_text(str(src.resolve()), encoding="utf-8")

        # Write .sha256 file (basic, no safe_path dependency)
        import hashlib
        h = hashlib.sha256()
        with open(src, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        sha256_file = backup_dir / (safe_name + ".sha256")
        sha256_file.write_text(f"SHA256:{h.hexdigest()}\nPATH:{src.resolve()}\n", encoding="utf-8")
        return True
    except Exception:
        return False


# ─── Whitelist management ─────────────────────────────────────────────────────

def show_whitelist() -> dict:
    wl = _load_whitelist()
    return {
        "ok": True,
        "whitelist": wl,
        "protected_always": sorted(ALWAYS_PROTECTED),
        "whitelist_file": str(WHITELIST_FILE),
        "config_file": str(CONFIG_FILE),
        "timer_file": str(TIMER_FILE),
        "extension_dir": str(_EXTENSION_DIR),
    }


def add_whitelist_entry(path: str, entry_type: str = "file") -> dict:
    """
    Add a path to the whitelist.
    entry_type: "file", "folder", or "ext"
    """
    wl = _load_whitelist()
    if entry_type == "file":
        if path not in wl["files"]:
            wl["files"].append(path)
    elif entry_type == "folder":
        if path not in wl["folders"]:
            wl["folders"].append(path)
    elif entry_type == "ext":
        if not path.startswith("."):
            path = "." + path
        if path not in wl["exts"]:
            wl["exts"].append(path)
    else:
        return {"ok": False, "error": f"Unknown entry_type: {entry_type}"}
    _save_whitelist(wl)
    return {"ok": True, "whitelist": wl}


def remove_whitelist_entry(path: str) -> dict:
    """Remove a path from the whitelist (matches any list)."""
    wl = _load_whitelist()
    removed = False
    if path in wl["files"]:
        wl["files"].remove(path)
        removed = True
    if path in wl["folders"]:
        wl["folders"].remove(path)
        removed = True
    if not path.startswith("."):
        alt = "." + path
    else:
        alt = path
    if alt in wl["exts"]:
        wl["exts"].remove(alt)
        removed = True
    if not removed:
        return {"ok": False, "error": f"'{path}' not found in whitelist"}
    _save_whitelist(wl)
    return {"ok": True, "whitelist": wl}


def set_interval(hours: int) -> dict:
    cfg = _load_config()
    cfg["interval_hours"] = max(1, hours)
    _save_config(cfg)
    return {"ok": True, "interval_hours": cfg["interval_hours"]}


def set_expire_days(days: int) -> dict:
    cfg = _load_config()
    cfg["expire_days"] = max(0, days)
    _save_config(cfg)
    return {"ok": True, "expire_days": cfg["expire_days"]}


def show_status() -> dict:
    cfg = _load_config()
    timer = _load_timer()
    wl = _load_whitelist()
    return {
        "ok": True,
        "workspace": str(WORKSPACE_ROOT),
        "extension_dir": str(_EXTENSION_DIR),
        "interval_hours": cfg.get("interval_hours", DEFAULT_INTERVAL_HOURS),
        "expire_days": cfg.get("expire_days", DEFAULT_EXPIRE_DAYS),
        "auto_backup": cfg.get("auto_backup", True),
        "last_run": timer.get("last_run"),
        "timer_due": _should_run(),
        "whitelist": wl,
        "always_protected_count": len(ALWAYS_PROTECTED),
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing action argument. Try: run, dry-run, status, show-whitelist, add-whitelist, remove-whitelist, set-interval, set-expire-days"}))
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "run":
            result = run_cleanup(dry_run=False, force=False)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "dry-run":
            result = run_cleanup(dry_run=True, force=True)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "status":
            result = show_status()
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "show-whitelist":
            result = show_whitelist()
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "add-whitelist":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing path argument"}))
                sys.exit(1)
            path = sys.argv[2]
            entry_type = "file"
            if len(sys.argv) > 3:
                if sys.argv[3] == "--type" and len(sys.argv) > 4:
                    entry_type = sys.argv[4]
            result = add_whitelist_entry(path, entry_type)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "remove-whitelist":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing path argument"}))
                sys.exit(1)
            result = remove_whitelist_entry(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "set-interval":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing hours argument"}))
                sys.exit(1)
            try:
                hours = int(sys.argv[2])
            except ValueError:
                print(json.dumps({"error": "Hours must be an integer"}))
                sys.exit(1)
            result = set_interval(hours)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "set-expire-days":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing days argument"}))
                sys.exit(1)
            try:
                days = int(sys.argv[2])
            except ValueError:
                print(json.dumps({"error": "Days must be an integer"}))
                sys.exit(1)
            result = set_expire_days(days)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        else:
            print(json.dumps({"error": f"Unknown action: {action}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
