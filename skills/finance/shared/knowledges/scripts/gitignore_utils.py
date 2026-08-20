#!/usr/bin/env python3
"""Helpers for making knowledge scans respect Git ignore rules."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Optional, Union


def _decode_git_path(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def _run_git(project_root: Path, args: list[str], input_data: Optional[bytes] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(project_root), *args],
        input=input_data,
        check=False,
        capture_output=True,
    )


def find_git_root(path: Path) -> Optional[Path]:
    result = _run_git(path, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return None

    git_root = _decode_git_path(result.stdout).strip()
    return Path(git_root).resolve() if git_root else None


def normalize_git_rel_path(path: Union[str, Path]) -> str:
    return Path(str(path).replace("\\", "/")).as_posix().lstrip("./")


def check_ignored_paths(project_root: Path, rel_paths: Iterable[str]) -> set[str]:
    paths = [normalize_git_rel_path(path) for path in rel_paths if normalize_git_rel_path(path)]
    if not paths:
        return set()

    ignored: set[str] = set()
    chunk_size = 512
    for index in range(0, len(paths), chunk_size):
        chunk = paths[index:index + chunk_size]
        input_data = ("\0".join(chunk) + "\0").encode("utf-8", errors="surrogateescape")
        result = _run_git(project_root, ["check-ignore", "--stdin", "-z", "--no-index"], input_data)
        if result.returncode not in (0, 1):
            continue

        ignored.update(
            normalize_git_rel_path(_decode_git_path(part))
            for part in result.stdout.split(b"\0")
            if part
        )

    return ignored


class GitIgnoreMatcher:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.enabled = find_git_root(self.project_root) is not None
        self._cache: dict[str, bool] = {}

    def is_ignored(self, rel_path: Union[str, Path]) -> bool:
        if not self.enabled:
            return False

        normalized = normalize_git_rel_path(rel_path)
        if not normalized or normalized.startswith("../"):
            return False

        cached = self._cache.get(normalized)
        if cached is not None:
            return cached

        ignored = normalized in check_ignored_paths(self.project_root, [normalized])
        self._cache[normalized] = ignored
        return ignored


def build_git_visible_file_index(project_root: Path) -> Optional[tuple[set[str], set[str]]]:
    """Return files and parent dirs visible to scans, excluding Git-ignored paths.

    The file set includes tracked files and untracked, non-ignored files. Tracked files that
    match ignore rules are filtered with `git check-ignore --no-index` so generated artifacts
    remain out of knowledge scans even if they were previously committed.
    """

    project_root = project_root.resolve()
    if find_git_root(project_root) is None:
        return None

    result = _run_git(project_root, ["ls-files", "-co", "--exclude-standard", "-z"])
    if result.returncode != 0:
        return None

    files = {
        normalize_git_rel_path(_decode_git_path(part))
        for part in result.stdout.split(b"\0")
        if part
    }
    files.difference_update(check_ignored_paths(project_root, files))

    dirs = {"."}
    for rel_file in files:
        parent = Path(rel_file).parent
        while parent.as_posix() not in ("", "."):
            dirs.add(parent.as_posix())
            parent = parent.parent

    return files, dirs
