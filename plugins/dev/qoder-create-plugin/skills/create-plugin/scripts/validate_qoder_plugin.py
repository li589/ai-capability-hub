#!/usr/bin/env python3
"""Offline Qoder plugin package validator.

This script intentionally avoids qodercli. It validates the package structure
that create-plugin should generate before any optional install smoke test.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MANIFEST = ".qoder-plugin/plugin.json"
FORBIDDEN_PARTS = {
    "__MACOSX",
    ".DS_Store",
    "settings.local.json",
}
FORBIDDEN_ROOT_DIRS = {
    ".codex-plugin",
    ".cursor-plugin",
    ".claude-plugin",
}
UPSTREAM_METADATA_DIRS = {
    ".cursor-plugin",
    ".claude-plugin",
}


@dataclass
class Issue:
    level: str
    message: str


class Reporter:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def error(self, message: str) -> None:
        self.issues.append(Issue("error", message))

    def warn(self, message: str) -> None:
        self.issues.append(Issue("warning", message))

    @property
    def has_errors(self) -> bool:
        return any(issue.level == "error" for issue in self.issues)


def load_json(path: Path, reporter: Reporter, label: str) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        reporter.error(f"{label} is missing: {path}")
    except json.JSONDecodeError as exc:
        reporter.error(f"{label} is invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}")
    except OSError as exc:
        reporter.error(f"{label} cannot be read: {path}: {exc}")
    return None


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def normalize_manifest_path(value: str) -> str:
    return value[2:] if value.startswith("./") else value


def validate_manifest_path(value: str, field: str, reporter: Reporter, *, suffix: str | None = None) -> None:
    if is_url(value):
        reporter.warn(f"{field} uses remote URL; prefer copying assets into the plugin: {value}")
        return
    if not value.startswith("./"):
        reporter.error(f"{field} path must start with './': {value}")
    normalized = normalize_manifest_path(value)
    if normalized == "" or normalized.startswith("/") or ".." in normalized.split("/"):
        reporter.error(f"{field} path must stay inside plugin root: {value}")
    if suffix and not normalized.endswith(suffix):
        reporter.error(f"{field} path should end with {suffix}: {value}")


def iter_manifest_paths(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item
    elif isinstance(value, dict):
        source = value.get("source")
        if isinstance(source, str):
            yield source


def path_exists(root: Path, manifest_path: str) -> bool:
    if is_url(manifest_path):
        return True
    return (root / normalize_manifest_path(manifest_path)).exists()


def read_frontmatter(path: Path) -> dict[str, str] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not match:
        return None
    result: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if raw_line.startswith((" ", "\t")) and current_key:
            result[current_key] = (result[current_key] + " " + raw_line.strip()).strip()
            continue
        key, sep, value = raw_line.partition(":")
        if sep:
            current_key = key.strip()
            result[current_key] = value.strip().strip('"').strip("'")
    return result


def collect_skill_files(root: Path, manifest: dict[str, Any], reporter: Reporter) -> list[Path]:
    skill_files: list[Path] = []
    skills_value = manifest.get("skills")
    if skills_value is None:
        reporter.warn("plugin.json does not declare skills")
        return skill_files

    if not isinstance(skills_value, (str, list)):
        reporter.error("plugin.json skills must be a string path or list of string paths")
        return skill_files

    for skill_path in iter_manifest_paths(skills_value):
        validate_manifest_path(skill_path, "skills", reporter)
        if is_url(skill_path):
            reporter.error(f"skills path cannot be a remote URL: {skill_path}")
            continue
        target = root / normalize_manifest_path(skill_path)
        if not target.exists():
            reporter.error(f"declared skills path does not exist: {skill_path}")
            continue
        if target.is_file():
            if target.name != "SKILL.md":
                reporter.error(f"skills file must be named SKILL.md: {skill_path}")
            else:
                skill_files.append(target)
            continue
        direct = target / "SKILL.md"
        if direct.exists():
            skill_files.append(direct)
        else:
            found = sorted(target.glob("*/SKILL.md"))
            if not found:
                reporter.error(f"declared skills directory contains no SKILL.md: {skill_path}")
            skill_files.extend(found)

    return sorted(set(skill_files))


def validate_skill_files(skill_files: list[Path], reporter: Reporter) -> None:
    seen_names: dict[str, Path] = {}
    for skill_file in skill_files:
        frontmatter = read_frontmatter(skill_file)
        if frontmatter is None:
            reporter.error(f"skill is missing YAML frontmatter: {skill_file}")
            continue
        name = frontmatter.get("name", "").strip()
        description = frontmatter.get("description", "").strip()
        if not name:
            reporter.error(f"skill frontmatter missing name: {skill_file}")
        if not description:
            reporter.error(f"skill frontmatter missing description: {skill_file}")
        if name:
            previous = seen_names.get(name)
            if previous:
                reporter.error(f"duplicate skill name '{name}': {previous} and {skill_file}")
            seen_names[name] = skill_file


def validate_commands(root: Path, manifest: dict[str, Any], reporter: Reporter) -> None:
    commands = manifest.get("commands")
    if commands is None:
        return
    command_sources: list[tuple[str, str]] = []
    if isinstance(commands, str):
        validate_manifest_path(commands, "commands", reporter)
        target = root / normalize_manifest_path(commands)
        if not target.exists():
            reporter.error(f"declared commands path does not exist: {commands}")
            return
        if target.is_dir():
            command_sources.extend((path.stem, "./" + str(path.relative_to(root)).replace("\\", "/")) for path in sorted(target.glob("*.md")))
        elif target.name.endswith(".md"):
            command_sources.append((target.stem, commands))
        else:
            reporter.error(f"commands path should be a directory or .md file: {commands}")
            return
    elif isinstance(commands, dict):
        for command_name, command_value in commands.items():
            if isinstance(command_value, str):
                source = command_value
            elif isinstance(command_value, dict):
                source = command_value.get("source")
            else:
                source = None
            if not isinstance(source, str):
                reporter.error(f"command '{command_name}' must declare a string source")
                continue
            command_sources.append((command_name, source))
    else:
        reporter.error("plugin.json commands must be a path string or command object")
        return

    for command_name, source in command_sources:
        validate_manifest_path(source, f"commands.{command_name}.source", reporter, suffix=".md")
        if not path_exists(root, source):
            reporter.error(f"command source does not exist: {command_name}: {source}")


def validate_mcp(root: Path, manifest: dict[str, Any], reporter: Reporter) -> None:
    mcp = manifest.get("mcpServers")
    if mcp is None:
        return
    if not isinstance(mcp, str):
        reporter.error("plugin.json mcpServers must be a string path")
        return
    validate_manifest_path(mcp, "mcpServers", reporter, suffix=".json")
    if is_url(mcp):
        reporter.error("mcpServers must point to a local JSON file")
        return
    mcp_path = root / normalize_manifest_path(mcp)
    data = load_json(mcp_path, reporter, "mcpServers")
    if data is None:
        return
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if servers is None and isinstance(data, dict):
        servers = data
    if not isinstance(servers, dict) or not servers:
        reporter.error(f"mcpServers JSON must contain at least one server: {mcp}")


def validate_other_component_paths(root: Path, manifest: dict[str, Any], reporter: Reporter) -> None:
    for field in ("rules", "agents", "hooks"):
        value = manifest.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            reporter.error(f"plugin.json {field} must be a string path")
            continue
        suffix = ".json" if field == "hooks" else None
        validate_manifest_path(value, field, reporter, suffix=suffix)
        if not path_exists(root, value):
            reporter.error(f"declared {field} path does not exist: {value}")

    logo = manifest.get("logo")
    if isinstance(logo, str):
        validate_manifest_path(logo, "logo", reporter)
        if not path_exists(root, logo):
            reporter.error(f"declared logo path does not exist: {logo}")


def validate_manifest(root: Path, reporter: Reporter) -> dict[str, Any] | None:
    manifest_path = root / MANIFEST
    manifest = load_json(manifest_path, reporter, "plugin manifest")
    if manifest is None:
        return None
    if not isinstance(manifest, dict):
        reporter.error("plugin manifest must be a JSON object")
        return None

    for field in ("name", "version"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            reporter.error(f"plugin.json missing required string field: {field}")

    name = manifest.get("name")
    if isinstance(name, str) and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", name):
        reporter.warn(f"plugin name may not be portable: {name}")

    return manifest


def validate_forbidden_files(root: Path, reporter: Reporter, *, allow_upstream_metadata: bool = False) -> None:
    for item in root.iterdir():
        if item.is_dir() and item.name in FORBIDDEN_ROOT_DIRS:
            if allow_upstream_metadata and item.name in UPSTREAM_METADATA_DIRS:
                continue
            reporter.error(f"non-Qoder plugin manifest directory is not allowed: {item.name}")

    for path in root.rglob("*"):
        parts = set(path.relative_to(root).parts)
        if parts & FORBIDDEN_PARTS:
            reporter.error(f"local or generated state must not be packaged: {path.relative_to(root)}")


def validate_plugin_root(root: Path, reporter: Reporter) -> None:
    if not root.exists():
        reporter.error(f"target does not exist: {root}")
        return
    if not root.is_dir():
        reporter.error(f"target is not a directory: {root}")
        return

    manifest = validate_manifest(root, reporter)
    if manifest is None:
        return
    allow_upstream_metadata = manifest.get("preserveUpstreamMetadata") is True
    validate_forbidden_files(root, reporter, allow_upstream_metadata=allow_upstream_metadata)
    validate_other_component_paths(root, manifest, reporter)
    validate_commands(root, manifest, reporter)
    validate_mcp(root, manifest, reporter)
    skill_files = collect_skill_files(root, manifest, reporter)
    validate_skill_files(skill_files, reporter)


def safe_extract_zip(zip_path: Path, destination: Path, reporter: Reporter) -> Path | None:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            names = [name for name in archive.namelist() if name and not name.endswith("/")]
            for name in names:
                normalized = posixpath.normpath(name)
                if normalized.startswith("../") or normalized.startswith("/"):
                    reporter.error(f"zip contains unsafe path: {name}")
                    return None
            if MANIFEST not in names:
                top_dirs = {name.split("/", 1)[0] for name in names if "/" in name}
                if len(top_dirs) == 1:
                    reporter.error(f"zip root is nested under '{next(iter(top_dirs))}/'; plugin zip must contain {MANIFEST} at the root")
                else:
                    reporter.error(f"zip is missing root {MANIFEST}")
                return None
            archive.extractall(destination)
    except zipfile.BadZipFile:
        reporter.error(f"invalid zip file: {zip_path}")
        return None
    except OSError as exc:
        reporter.error(f"cannot read zip file: {zip_path}: {exc}")
        return None
    return destination


def run(target: Path) -> tuple[Reporter, Path | None]:
    reporter = Reporter()
    if target.is_file() and target.suffix.lower() == ".zip":
        temp_dir = tempfile.TemporaryDirectory(prefix="qoder-plugin-validate-")
        root = safe_extract_zip(target, Path(temp_dir.name), reporter)
        if root is not None:
            validate_plugin_root(root, reporter)
        # Keep cleanup deterministic while still returning a useful label.
        temp_dir.cleanup()
        return reporter, target

    validate_plugin_root(target, reporter)
    return reporter, target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate a Qoder plugin directory or zip without qodercli.")
    parser.add_argument("target", help="Plugin root directory or plugin zip")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    reporter, label = run(target)

    if args.json:
        print(json.dumps({
            "target": str(label or target),
            "ok": not reporter.has_errors,
            "issues": [issue.__dict__ for issue in reporter.issues],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Validating Qoder plugin: {label or target}")
        if reporter.issues:
            for issue in reporter.issues:
                print(f"{issue.level.upper()}: {issue.message}")
        else:
            print("OK: no issues found")

    return 1 if reporter.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
