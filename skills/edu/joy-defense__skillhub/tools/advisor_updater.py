#!/usr/bin/env python3
"""
Advisor Updater: auto-distillation of advisor review transcripts into advisor files.

Usage:
  python advisor_updater.py --advisor <code> --input <transcript_file> --base-dir ../advisors/

This script reads the existing advisor files (judgment.md, management.md, persona.md, meta.json),
extracts new review patterns and persona phrases from the transcript, and appends them to the
files. A timestamped backup is created in versions/ before applying changes.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def extract_review_patterns(text: str) -> List[str]:
    # Simple heuristic extraction of new review criteria/points from transcript
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    patterns: List[str] = []
    keywords = ["评审", "要点", "重点", "关注", "标准", "规则", "审查"]
    for ln in lines:
        if any(k in ln for k in keywords):
            patterns.append(ln)
    # Fallback: capture sentences mentioning keywords
    if not patterns:
        for ln in lines:
            if any(w in ln for w in ["要点", "关注点", "关注"]):
                patterns.append(ln)
    # Deduplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for p in patterns:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def extract_persona_phrases(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    phrases: List[str] = []
    keywords = ["语气", "口吻", "风格", "用语", "称呼"]
    for ln in lines:
        if any(k in ln for k in keywords):
            phrases.append(ln)
    if not phrases:
        for ln in lines:
            if len(ln) < 120:
                phrases.append(ln)
    # Deduplicate
    seen = set()
    uniq: List[str] = []
    for p in phrases:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def merge_updates(existing_content: str, new_items: List[str]) -> str:
    if not new_items:
        return existing_content
    # Normalize existing by a simple sentinel for existing items
    existing_lines = set(line.strip() for line in existing_content.splitlines())
    additions = [f"- {it}" for it in new_items if it not in existing_lines]
    if not additions:
        return existing_content
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    footer = f"\n\n# Updated on {timestamp}\n"  # marker for updates
    return existing_content.rstrip() + "\n" + "\n".join(additions) + footer


def backup_version(advisor_dir: Path) -> Path:
    versions_dir = advisor_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = versions_dir / ts
    shutil.copytree(advisor_dir, backup_dir, ignore=shutil.ignore_patterns("versions"))
    return backup_dir


def update_advisor(advisor_code: str, new_text: str, base_dir: Path) -> dict:
    advisors_root = base_dir / "advisors"
    advisor_dir = advisors_root / advisor_code
    if not advisor_dir.exists():
        raise FileNotFoundError(f"Advisor directory not found: {advisor_dir}")

    judgment_path = advisor_dir / "judgment.md"
    management_path = advisor_dir / "management.md"
    persona_path = advisor_dir / "persona.md"
    meta_path = advisor_dir / "meta.json"

    # Read existing content (create if missing)
    judgment = read_text(judgment_path) if judgment_path.exists() else "# Judgment
"
    management = read_text(management_path) if management_path.exists() else "# Management
"
    persona = read_text(persona_path) if persona_path.exists() else "# Persona
"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    else:
        meta = {}

    # Parse transcript
    new_patterns = extract_review_patterns(new_text)
    new_persona = extract_persona_phrases(new_text)

    # Merge into files
    judgment_updated = merge_updates(judgment, new_patterns)
    management_updated = merge_updates(management, [p for p in new_patterns if isinstance(p, str) and len(p) > 0])
    persona_updated = merge_updates(persona, new_persona)

    # Update meta.json: focus_areas and priority_questions
    focus_areas = set(meta.get("focus_areas", []))
    for pat in new_patterns:
        if isinstance(pat, str) and ("关注" in pat or "focus" in pat.lower()):
            focus_areas.add(pat)
    priority_questions = set(meta.get("priority_questions", []))
    for p in new_persona:
        priority_questions.add(p)
    meta.update({
        "focus_areas": sorted(list(focus_areas)),
        "priority_questions": sorted(list(priority_questions)),
        "last_updated": datetime.utcnow().isoformat() + "Z",
    })

    # Backup current version
    backup_version(advisor_dir)

    # Write updates
    advisor_dir.mkdir(parents=True, exist_ok=True)
    judgment_path.write_text(judgment_updated, encoding="utf-8")
    management_path.write_text(management_updated, encoding="utf-8")
    persona_path.write_text(persona_updated, encoding="utf-8")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "updated": {
            "judgment.md": bool(new_patterns),
            "management.md": bool(new_patterns),
            "persona.md": bool(new_persona),
            "meta.json": True,
        },
        "summary": {
            "patterns_added": len(new_patterns),
            "persona_phrases_added": len(new_persona),
            "backup": str(backup_version(advisor_dir)),
        },
        "advisor": advisor_code,
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Auto-distill advisor transcript into advisor files.")
    ap.add_argument("--advisor", required=True, help="Advisor code (e.g., zhang)")
    ap.add_argument("--input", required=True, help="Path to transcript input file (txt/json)")
    ap.add_argument("--base-dir", default="/Users/eimei/Desktop/答辩-skill/", help="Base directory of the skill")
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input transcript not found: {input_path}", file=sys.stderr)
        return 1
    new_text = input_path.read_text(encoding="utf-8").strip()
    if not new_text:
        print("Empty transcript provided.", file=sys.stderr)
        return 1

    base_dir = Path(args.base_dir).expanduser().resolve()
    try:
        result = update_advisor(args.advisor, new_text, base_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"Error updating advisor: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
