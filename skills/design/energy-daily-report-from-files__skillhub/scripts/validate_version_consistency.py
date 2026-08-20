#!/usr/bin/env python3
"""Validate the single-source release version contract."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
SCAN_EXTENSIONS = {".md", ".json", ".txt", ".py", ".sh"}
IGNORE_DIRS = {"__pycache__", ".pytest_cache", ".venv", "node_modules"}


def validate_version_consistency(skill_dir: Path) -> dict:
    errors: list[dict[str, str]] = []
    version_path = skill_dir / "VERSION.txt"
    try:
        expected = version_path.read_text(encoding="utf-8-sig").strip()
    except OSError as exc:
        return {"ok": False, "expected_version": None, "errors": [{"code": "VERSION_SOURCE_MISSING", "message": "VERSION.txt 文件缺失或无法读取，请确认技能包已完整解压。"}], "occurrences": []}
    if not SEMVER_RE.fullmatch(expected):
        errors.append({"code": "VERSION_SOURCE_INVALID", "message": "VERSION.txt 必须是 x.y.z 格式。"})

    checks: list[tuple[str, str | None]] = []
    metadata: dict = {}
    try:
        metadata = json.loads((skill_dir / "SKILL_VERSION.json").read_text(encoding="utf-8-sig"))
        checks.append(("SKILL_VERSION.json.version", metadata.get("version")))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append({"code": "VERSION_METADATA_INVALID", "message": "SKILL_VERSION.json 格式有误，请确认技能包完整。"})

    registry_meta: dict = {}
    try:
        registry_meta = json.loads((skill_dir / "_meta.json").read_text(encoding="utf-8-sig"))
        checks.append(("_meta.json.version", registry_meta.get("version")))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append({"code": "VERSION_REGISTRY_METADATA_INVALID", "message": "_meta.json 格式有误，请检查文件完整性。"})
    try:
        state = json.loads((skill_dir / "resources/mapping-templates/build-state.example.json").read_text(encoding="utf-8-sig"))
        checks.append(("build-state.example.json.skill_version", state.get("skill_version")))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append({"code": "VERSION_STATE_INVALID", "message": "构建状态模板文件无效，请确认技能包完整。"})
    for label, value in checks:
        if value != expected:
            errors.append({"code": "VERSION_MISMATCH", "message": f"{label}={value!r}，应为 {expected!r}。"})

    expected_name = str(metadata.get("name", "")).strip()
    expected_display_name = str(metadata.get("display_name", "")).strip()
    registry_slug = str(registry_meta.get("slug", "")).strip()
    if not expected_name:
        errors.append({"code": "IDENTITY_NAME_MISSING", "message": "SKILL_VERSION.json.name 不能为空。"})
    if not expected_display_name:
        errors.append({"code": "IDENTITY_DISPLAY_NAME_MISSING", "message": "SKILL_VERSION.json.display_name 不能为空。"})
    if registry_slug != expected_name:
        errors.append({"code": "IDENTITY_SLUG_MISMATCH", "message": f"_meta.json.slug={registry_slug!r} 与 SKILL_VERSION.json.name={expected_name!r} 不一致。"})
    if skill_dir.name != expected_name:
        errors.append({"code": "IDENTITY_FOLDER_MISMATCH", "message": f"技能根目录名 {skill_dir.name!r} 应与 name {expected_name!r} 一致。"})
    try:
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8-sig")
        frontmatter_block = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_text, re.DOTALL)
        fields = [] if not frontmatter_block else [
            line.split(":", 1)[0].strip()
            for line in frontmatter_block.group(1).splitlines()
            if line.strip() and not line.lstrip().startswith("#") and ":" in line
        ]
        if fields != ["name", "description"]:
            errors.append({"code": "FRONTMATTER_FIELDS_INVALID", "message": "SKILL.md frontmatter 只能按顺序包含 name 和 description。"})
        frontmatter_match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", skill_text)
        frontmatter_name = frontmatter_match.group(1) if frontmatter_match else ""
        if frontmatter_name != expected_name:
            errors.append({"code": "IDENTITY_FRONTMATTER_MISMATCH", "message": f"SKILL.md name={frontmatter_name!r} 与 SKILL_VERSION.json.name={expected_name!r} 不一致。"})
        if expected_display_name and expected_display_name not in skill_text:
            errors.append({"code": "IDENTITY_DISPLAY_NAME_MISMATCH", "message": "SKILL.md 未包含 SKILL_VERSION.json.display_name。"})
    except OSError as exc:
        errors.append({"code": "IDENTITY_SKILL_MISSING", "message": "SKILL.md 文件缺失，请确认技能包已完整解压。"})
    try:
        agent_text = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8-sig")
        for token in [expected_display_name, "short_description:", f"$${expected_name}"]:
            normalized = token.replace("$$", "$")
            if normalized and normalized not in agent_text:
                errors.append({"code": "AGENT_METADATA_INVALID", "message": f"agents/openai.yaml 缺少 {normalized!r}。"})
    except OSError as exc:
        errors.append({"code": "AGENT_METADATA_MISSING", "message": "缺少 agents/openai.yaml，平台入口信息不完整。"})

    standalone_required = [
        "resources/standalone-energy-daily-report/energy_daily_report.py",
        "resources/standalone-energy-daily-report/README_STANDALONE.md",
        "resources/standalone-energy-daily-report/requirements_standalone.txt",
        "resources/standalone-energy-daily-report/build_exe_windows.py",
        "scripts/ensure_energy_daily_standalone.py",
        "references/standalone-energy-daily-report.md",
    ]
    for relative in standalone_required:
        if not (skill_dir / relative).is_file():
            errors.append({"code": "STANDALONE_TEMPLATE_MISSING", "message": f"缺少独立能源日报交付模板：{relative}"})
    standalone_script = skill_dir / "resources/standalone-energy-daily-report/energy_daily_report.py"
    if standalone_script.is_file():
        standalone_text = standalone_script.read_text(encoding="utf-8-sig", errors="replace")
        try:
            ast.parse(standalone_text, filename=str(standalone_script))
        except SyntaxError as exc:
            errors.append({"code": "STANDALONE_TEMPLATE_SYNTAX", "message": "独立能源日报源码有语法错误，请检查 energy_daily_report.py 是否完整且未被损坏"})
        for token in ["class EnergyRepository", "class EnergyDailyApp", "def run_self_test", "--self-test", "build_exe_windows.py"]:
            if token not in standalone_text and token != "build_exe_windows.py":
                errors.append({"code": "STANDALONE_TEMPLATE_INCOMPLETE", "message": f"独立能源日报源码缺少能力标识：{token}"})
        if len(standalone_text.strip()) < 2000:
            errors.append({"code": "STANDALONE_TEMPLATE_INCOMPLETE", "message": "独立能源日报模板内容过少；完整性应同时以能力标识和真实自检判断。"})

    required_tokens = {
        "SECURITY_AUDIT.md": [f"V{expected}"],
        "SKILL.md": [f"V{expected}"],
    }
    for relative, tokens in required_tokens.items():
        path = skill_dir / relative
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            errors.append({"code": "VERSION_DOCUMENT_MISSING", "message": f"{relative} 文件缺失，请确认技能包已完整解压。"})
            continue
        for token in tokens:
            if token not in text:
                errors.append({"code": "VERSION_DOCUMENT_MISMATCH", "message": f"{relative} 缺少当前版本标识 {token}。"})

    occurrences: list[dict[str, object]] = []
    pattern = re.compile(r"(?<![\d.])(\d+\.\d+\.\d+)(?![\d.])")
    allowed_non_release_keys = {"schema_version", "calculation_version", "minimum_python"}
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in SCAN_EXTENSIONS or any(part in IGNORE_DIRS for part in path.parts):
            continue
        relative = path.relative_to(skill_dir).as_posix()
        if relative == "scripts/test_skill_scripts.py":
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if path.name.casefold().startswith("requirements") and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*==[^=\s]+", stripped):
                continue
            for match in pattern.finditer(line):
                value = match.group(1)
                if value == expected:
                    continue
                context = line.strip()
                if any(f'"{key}"' in context for key in allowed_non_release_keys) and "skill_version" not in context:
                    continue
                if "minimum_python" in context:
                    continue
                occurrences.append({"file": relative, "line": line_no, "version": value, "context": context[:180]})
    if occurrences:
        errors.append({"code": "VERSION_STALE_OCCURRENCE", "message": f"发现 {len(occurrences)} 处可能误导评测的旧发布版本标识。"})
    return {"ok": not errors, "expected_version": expected, "errors": errors, "occurrences": occurrences}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查技能包发布版本是否全局一致")
    parser.add_argument("skill_dir", nargs="?", default=".")
    args = parser.parse_args()
    result = validate_version_consistency(Path(args.skill_dir).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
