"""Build a privacy-preserving structural manifest for SkillPay planning.

The manifest deliberately excludes paths, filenames, titles, note bodies,
frontmatter values, tags, links, timestamps, file hashes, and exact byte sizes.
Only aggregate buckets that are useful to the deterministic planner leave the
local machine after a separate user-confirmed upload step.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PRIVACY_MODE = "structure-only"
EXCLUDED_DIRECTORIES = {
    ".ai-workbench",
    ".git",
    ".obsidian",
    ".trash",
    ".Trash",
    "__pycache__",
    "AI-Dashboard",
    "AI-Knowledge",
}


def _canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _file_category(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".md":
        return "markdown"
    if suffix in {".doc", ".docx", ".odt", ".pdf", ".rtf", ".txt"}:
        return "document"
    if suffix in {".csv", ".ods", ".xls", ".xlsx"}:
        return "spreadsheet"
    if suffix in {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}:
        return "image"
    if suffix in {".c", ".cpp", ".css", ".go", ".html", ".java", ".js", ".json", ".py", ".rs", ".ts", ".yaml", ".yml"}:
        return "code"
    return "other"


def _size_bucket(size: int) -> str:
    if size == 0:
        return "empty"
    if size < 64 * 1024:
        return "small"
    if size < 1024 * 1024:
        return "medium"
    return "large"


def _total_size_bucket(size: int) -> str:
    if size < 1024 * 1024:
        return "under-1mb"
    if size < 10 * 1024 * 1024:
        return "1mb-to-10mb"
    if size < 100 * 1024 * 1024:
        return "10mb-to-100mb"
    return "over-100mb"


def _depth_bucket(depth: int) -> str:
    return str(depth) if depth < 3 else "3-plus"


def build_structure_manifest(source: Path) -> dict[str, Any]:
    """Return a deterministic aggregate manifest without source identifiers."""

    source = source.expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError("The selected source must be a directory.")

    categories: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    depths: Counter[str] = Counter()
    file_count = 0
    directory_count = 0
    total_bytes = 0
    max_depth = 0
    symlinks_skipped = 0
    obsidian_detected = (source / ".obsidian").is_dir()

    for current_root, directory_names, file_names in os.walk(source, followlinks=False):
        current = Path(current_root)
        relative_current = current.relative_to(source)
        current_depth = len(relative_current.parts)
        kept_directories: list[str] = []
        for directory_name in directory_names:
            candidate = current / directory_name
            if candidate.is_symlink():
                symlinks_skipped += 1
                continue
            if directory_name in EXCLUDED_DIRECTORIES:
                continue
            kept_directories.append(directory_name)
            directory_count += 1
            max_depth = max(max_depth, current_depth + 1)
        directory_names[:] = kept_directories

        for file_name in file_names:
            path = current / file_name
            if path.is_symlink():
                symlinks_skipped += 1
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            depth = current_depth
            file_count += 1
            total_bytes += stat.st_size
            max_depth = max(max_depth, depth)
            categories[_file_category(path)] += 1
            sizes[_size_bucket(stat.st_size)] += 1
            depths[_depth_bucket(depth)] += 1

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "privacy_mode": PRIVACY_MODE,
        "consent_scope": "aggregate-structure-only",
        "counts": {
            "directories": directory_count,
            "files": file_count,
        },
        "file_categories": dict(sorted(categories.items())),
        "file_size_buckets": dict(sorted(sizes.items())),
        "depth_buckets": dict(sorted(depths.items())),
        "features": {
            "max_depth_bucket": _depth_bucket(max_depth),
            "obsidian_detected": obsidian_detected,
            "symlinks_skipped": symlinks_skipped,
            "total_size_bucket": _total_size_bucket(total_bytes),
        },
    }
    return {**body, "manifest_digest": _digest(body)}


def validate_structure_manifest(manifest: object) -> list[str]:
    """Validate the exact privacy contract accepted by the paid service."""

    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]
    errors: list[str] = []
    expected = {
        "schema_version",
        "privacy_mode",
        "consent_scope",
        "counts",
        "file_categories",
        "file_size_buckets",
        "depth_buckets",
        "features",
        "manifest_digest",
    }
    if set(manifest) != expected:
        errors.append("manifest fields do not match the structure-only contract")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported manifest schema version")
    if manifest.get("privacy_mode") != PRIVACY_MODE:
        errors.append("manifest privacy mode must be structure-only")
    if manifest.get("consent_scope") != "aggregate-structure-only":
        errors.append("manifest consent scope is invalid")

    counts = manifest.get("counts")
    if not isinstance(counts, dict) or set(counts) != {"directories", "files"}:
        errors.append("manifest counts are invalid")
    elif any(not isinstance(value, int) or value < 0 for value in counts.values()):
        errors.append("manifest counts must be non-negative integers")

    allowed_categories = {"markdown", "document", "spreadsheet", "image", "code", "other"}
    categories = manifest.get("file_categories")
    if not isinstance(categories, dict) or not set(categories).issubset(allowed_categories):
        errors.append("manifest file categories are invalid")
    elif any(not isinstance(value, int) or value < 0 for value in categories.values()):
        errors.append("manifest file category counts must be non-negative integers")

    allowed_size_buckets = {"empty", "small", "medium", "large"}
    size_buckets = manifest.get("file_size_buckets")
    if not isinstance(size_buckets, dict) or not set(size_buckets).issubset(allowed_size_buckets):
        errors.append("manifest size buckets are invalid")

    allowed_depth_buckets = {"0", "1", "2", "3-plus"}
    depth_buckets = manifest.get("depth_buckets")
    if not isinstance(depth_buckets, dict) or not set(depth_buckets).issubset(allowed_depth_buckets):
        errors.append("manifest depth buckets are invalid")

    features = manifest.get("features")
    if not isinstance(features, dict) or set(features) != {
        "max_depth_bucket",
        "obsidian_detected",
        "symlinks_skipped",
        "total_size_bucket",
    }:
        errors.append("manifest feature summary is invalid")
    else:
        if features.get("max_depth_bucket") not in allowed_depth_buckets:
            errors.append("manifest maximum depth bucket is invalid")
        if not isinstance(features.get("obsidian_detected"), bool):
            errors.append("manifest obsidian flag must be boolean")
        if not isinstance(features.get("symlinks_skipped"), int) or features.get("symlinks_skipped", -1) < 0:
            errors.append("manifest skipped symlink count is invalid")
        if features.get("total_size_bucket") not in {
            "under-1mb",
            "1mb-to-10mb",
            "10mb-to-100mb",
            "over-100mb",
        }:
            errors.append("manifest total size bucket is invalid")

    if not errors:
        digest_source = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        if manifest.get("manifest_digest") != _digest(digest_source):
            errors.append("manifest digest does not match its aggregate fields")
    return errors
