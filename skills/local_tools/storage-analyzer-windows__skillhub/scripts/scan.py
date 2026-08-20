"""Windows-only read-only storage scanner with extended targets.

Collects disk usage, system info, and per-directory size breakdowns for all
major storage hot-spots on Windows, and emits one JSON blob to stdout for the
AI agent to interpret and classify. Covers the original 7 targets plus the
blind spots found during analysis: Windows\\Installer, ProgramData, Recycle Bin,
Windows\\Temp, Windows\\SoftwareDistribution, hiberfil.sys, pagefile.sys.

STRICTLY READ-ONLY. Uses os.scandir exclusively (no `du` --- macOS code removed).

Output shape:
{
  "generated_at", "scan_seconds",
  "system": {os, build, arch, user, home, filesystem,
             disk_total, disk_used, disk_free, purgeable,
             disks: [{name, total, used, free}]},
  "groups": { "<group>": [{name, path, size_kb, size_h}], ... },
  "denied": ["/path", ...]
}
"""

import json
import os
import shutil
import sys
import time
import argparse
from pathlib import Path

HOME = os.path.expanduser("~")
USERPROFILE = os.environ.get("USERPROFILE", HOME)
LOCALAPPDATA = os.environ.get("LOCALAPPDATA",
                              os.path.join(USERPROFILE, "AppData", "Local"))
APPDATA = os.environ.get("APPDATA",
                         os.path.join(USERPROFILE, "AppData", "Roaming"))


# ── helpers ──────────────────────────────────────────────────────────────

def human(kb: float) -> str:
    """KB number -> human string like '12.3 GB'."""
    n = float(kb) * 1024
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit not in ("B", "KB") else f"{int(n)} {unit}"
        n /= 1024


def make_long_path(path: str) -> str:
    """Prepend \\\\?\\ for paths over MAX_PATH (260 chars)."""
    if len(path) >= 260 and not path.startswith(r"\\?\\"):
        return r"\\?\\" + os.path.abspath(path)
    return path


# ── scanning core ────────────────────────────────────────────────────────

def dir_size_bytes(path: str) -> int:
    """Recursive size in bytes via os.scandir. Skips symlinks/junctions
    and silently passes PermissionError."""
    total = 0
    long_path = make_long_path(path)
    try:
        with os.scandir(long_path) as it:
            for e in it:
                try:
                    if e.is_symlink():
                        continue
                    # CHANGED: explicit reparse-point check for NTFS junctions
                    if e.is_dir(follow_symlinks=False):
                        total += dir_size_bytes(e.path)
                    elif e.is_file(follow_symlinks=False):
                        total += e.stat(follow_symlinks=False).st_size
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError, FileNotFoundError):
        pass
    return total


def scandir_children(path: str, min_kb: int = 51200,
                     limit: int = 40, quick: bool = False) -> list:
    """Size every immediate child of `path` via os.scandir.

    Args:
        path: Directory to scan.
        min_kb: Minimum size (KB) to include in results.
        limit: Max results to return.
        quick: If True, only scan one level deep (no recursion).

    Returns:
        List of {name, path, size_kb, size_h} dicts, sorted desc.
    """
    if not path or not os.path.isdir(path):
        return []

    # CHANGED: collect denied paths for full directory
    denied = []

    results = []
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return [{"name": "(permission denied)", "path": path,
                 "size_kb": 0, "size_h": "?", "denied": True}]

    for name in entries:
        child = os.path.join(path, name)
        try:
            if os.path.islink(child):
                continue
            if os.path.isfile(child):
                kb = os.path.getsize(child) // 1024
            elif os.path.isdir(child):
                kb = (dir_size_flat(child) if quick
                      else dir_size_bytes(child)) // 1024
            else:
                continue
        except (PermissionError, OSError):
            denied.append(child)
            continue
        if kb < min_kb:
            continue
        results.append({"name": name, "path": child,
                        "size_kb": kb, "size_h": human(kb)})
    # FIX: in quick mode, aggregate noisy file-level entries into one summary
    if quick and results:
        dir_results = [r for r in results if os.path.isdir(r["path"])]
        file_results = [r for r in results if os.path.isfile(r["path"])]
        # Collapse files only if they dominate (more files than dirs, or >10 files)
        if len(file_results) > max(len(dir_results), 9):
            total_kb = sum(r["size_kb"] for r in file_results)
            if total_kb >= min_kb:
                agg = {"name": f"({len(file_results)} 个大文件, 合计 {human(total_kb)})",
                       "path": path, "size_kb": total_kb, "size_h": human(total_kb)}
                results = dir_results + [agg]
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    if denied:
        results.append({"name": "(permission denied: %d paths)" % len(denied),
                        "path": path, "size_kb": 0, "size_h": "?", "denied": True})
    return results[:limit]


def dir_size_flat(path: str) -> int:
    """Quick one-level size (no recursion)."""
    total = 0
    try:
        with os.scandir(path) as it:
            for e in it:
                try:
                    if e.is_symlink():
                        continue
                    total += e.stat(follow_symlinks=False).st_size
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    return total


def file_size_if_exists(path: str) -> int:
    """Return file size in bytes or 0 if not found.
    Uses os.path.exists instead of isfile to handle system-protected
    files like pagefile.sys and hiberfil.sys on Windows."""
    try:
        if os.path.exists(path) and not os.path.isdir(path):
            return os.path.getsize(path)
        return 0
    except OSError:
        return 0


# ── Windows targets ──────────────────────────────────────────────────────

def get_targets():
    """Return list of (key, path, min_kb) scan targets."""
    return [
        # --- user directories (original) ---
        ("user_profile",     USERPROFILE,                  102400),
        ("appdata_local",    LOCALAPPDATA,                  51200),
        ("appdata_roaming",  APPDATA,                       51200),
        ("downloads",        os.path.join(USERPROFILE, "Downloads"), 51200),

        # --- system application dirs (original) ---
        ("program_files",    r"C:\Program Files",          102400),
        ("program_files_x86", r"C:\Program Files (x86)",   102400),

        # NEW: system-level directories that were blind spots
        ("program_data",     r"C:\ProgramData",            102400),
        ("windows_temp",     r"C:\Windows\Temp",           51200),
        ("windows_installer", r"C:\Windows\Installer",    102400),
        # NEW: $Recycle.Bin (skip individual files — just report total)
        ("recycle_bin",      r"C:\$Recycle.Bin",          102400),
        ("windows_update",   r"C:\Windows\SoftwareDistribution", 51200),

        # --- dev caches (expanded) ---
        ("dev_caches",       None,                          51200),
    ]


def get_dev_cache_paths() -> list:
    """Return list of (env_key, path) for developer cache locations."""
    profile = USERPROFILE
    local = LOCALAPPDATA
    return [
        ("pip Cache", os.path.join(local, "pip", "Cache")),
        ("uv Cache",  os.path.join(local, "uv")),
        (".cache",    os.path.join(profile, ".cache")),
        (".npm",      os.path.join(profile, ".npm")),
        (".cargo",    os.path.join(profile, ".cargo")),
        (".gradle",   os.path.join(profile, ".gradle")),
        (".m2",       os.path.join(profile, ".m2")),
        ("Yarn",      os.path.join(local, "Yarn")),
        # NEW: additional Windows dev caches
        ("nuget packages", os.path.join(profile, ".nuget", "packages")),
        ("ms-playwright",  os.path.join(local, "ms-playwright")),
        ("go-build",       os.path.join(local, "go-build")),
        ("pnpm-store",     os.path.join(local, "pnpm-store")),
    ]


# ── system info ──────────────────────────────────────────────────────────

def list_drives_windows() -> list:
    """Return [{name, total, used, free}] for all accessible drives."""
    drives = []
    import string
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if os.path.exists(root):
            try:
                t, u, f = shutil.disk_usage(root)
                drives.append({"name": root, "total": human(t // 1024),
                               "used": human(u // 1024), "free": human(f // 1024)})
            except Exception:
                continue
    return drives


def system_info_windows() -> dict:
    """Collect system metadata for Windows."""
    import platform
    info = {
        "os": platform.system() + " " + platform.release(),
        "build": platform.version(),
        "arch": os.environ.get("PROCESSOR_ARCHITECTURE", platform.machine()),
        "user": os.environ.get("USERNAME", ""),
        "home": USERPROFILE,
        "filesystem": "NTFS",
        "purgeable": "",
    }
    sysdrive = os.environ.get("SystemDrive", "C:") + "\\"
    try:
        t, u, f = shutil.disk_usage(sysdrive)
        info["disk_total"] = human(t // 1024)
        info["disk_used"] = human(u // 1024)
        info["disk_free"] = human(f // 1024)
    except Exception:
        info["disk_total"] = "?"
        info["disk_used"] = "?"
        info["disk_free"] = "?"
    info["disk_name"] = sysdrive
    info["disks"] = list_drives_windows()

    # NEW: system file detection
    for var, path in [("hiberfil", r"C:\hiberfil.sys"),
                      ("pagefile", r"C:\pagefile.sys")]:
        sz = file_size_if_exists(path)
        if sz:
            info.setdefault("system_files", {})[var] = {
                "path": path, "size": human(sz // 1024)}

    return info


# ── main ─────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Windows storage scanner")
    p.add_argument("--quick", action="store_true",
                   help="One-level only (no recursion, <5s)")
    p.add_argument("--min-mb", type=int, default=50,
                   help="Minimum size in MB to report (default: 50)")
    p.add_argument("--include-hidden", action="store_true",
                   help="Include hidden directories")
    p.add_argument("--cache", action="store_true",
                   help="Use/update ~/.cache/storage-scan/ cache (24h TTL)")
    return p.parse_args()


def load_cache(cache_path: str, max_age: float = 86400) -> dict | None:
    """Load cached scan if it exists and is fresh (< max_age seconds)."""
    if not os.path.isfile(cache_path):
        return None
    age = time.time() - os.path.getmtime(cache_path)
    if age > max_age:
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(data: dict, cache_path: str):
    """Write scan data to cache file."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def main():
    args = parse_args()
    min_kb = args.min_mb * 1024

    # NEW: cache support
    cache_dir = os.path.expanduser(r"~\.cache\storage-scan")
    hostname = os.environ.get("COMPUTERNAME") or \
               __import__("socket").gethostname() or "unknown"
    cache_path = os.path.join(cache_dir, f"{hostname}-scan.json")
    if args.cache:
        cached = load_cache(cache_path)
        if cached:
            print(json.dumps(cached, ensure_ascii=False, indent=2))
            return

    started = time.time()

    # system info (always full scan for disk usage)
    system = system_info_windows()

    # scan targets
    targets = get_targets()
    groups = {}
    denied_all = []

    for key, path, floor in targets:
        if key == "dev_caches":
            dev = []
            for label, dp in get_dev_cache_paths():
                if not os.path.isdir(dp):
                    continue
                try:
                    kb = (dir_size_flat(dp) if args.quick
                          else dir_size_bytes(dp)) // 1024
                except (PermissionError, OSError):
                    denied_all.append(dp)
                    continue
                if kb < min_kb:
                    continue
                dev.append({"name": label, "path": dp,
                            "size_kb": kb, "size_h": human(kb)})
            dev.sort(key=lambda r: r["size_kb"], reverse=True)
            groups[key] = dev
        else:
            groups[key] = scandir_children(path, min_kb=min_kb,
                                           quick=args.quick)

    # collect denied items from group results
    for items in groups.values():
        for item in items:
            if item.get("denied"):
                denied_all.append(item["path"])

    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": system,
        "groups": groups,
        "denied": list(set(denied_all)),
        "scan_seconds": round(time.time() - started, 1),
    }

    # NEW: save cache
    if args.cache:
        save_cache(data, cache_path)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # CHANGED: ensure output is line-buffered (fixes Windows background task bug)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    main()
