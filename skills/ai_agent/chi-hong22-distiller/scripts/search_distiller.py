#!/usr/bin/env python3
"""
Input: keywords/tags + search directory path
Output: list of matching distilled documents with title, tags, date, confidence
Pos: Primary search method for Phase 3.2 (create/append decision). If Python is
     unavailable, SKILL.md defines a Grep-based fallback that covers the same logic.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


def load_search_index(distiller_dir: Path) -> List[Dict]:
    """Load entries from .distiller/search-index.jsonl if it exists."""
    index_path = distiller_dir / "search-index.jsonl"
    entries = []
    if index_path.exists():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def parse_frontmatter(file_path: Path) -> Optional[Dict]:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None

    frontmatter = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")
        elif line.strip().startswith("- ") and frontmatter:
            last_key = list(frontmatter.keys())[-1]
            if not isinstance(frontmatter[last_key], list):
                frontmatter[last_key] = [] if frontmatter[last_key] == "" else [frontmatter[last_key]]
            frontmatter[last_key].append(line.strip()[2:].strip().strip('"').strip("'"))

    return frontmatter


def scan_markdown_files(search_dir: Path) -> List[Dict]:
    """Scan directory for .md files and extract frontmatter metadata."""
    results = []
    if not search_dir.exists():
        return results

    for md_file in search_dir.rglob("*.md"):
        fm = parse_frontmatter(md_file)
        if fm and "distilled" in str(fm.get("tags", "")):
            results.append({
                "file": str(md_file),
                "title": fm.get("title", md_file.stem),
                "tags": fm.get("tags", []),
                "date": fm.get("date", ""),
                "scene": fm.get("scene", ""),
                "confidence_summary": fm.get("confidence_summary", ""),
            })
    return results


def search(keywords: List[str], entries: List[Dict]) -> List[Dict]:
    """Score and rank entries by keyword match against title, tags, keywords fields."""
    scored = []
    keyword_lower = [k.lower() for k in keywords]

    for entry in entries:
        score = 0
        searchable = " ".join([
            str(entry.get("title", "")),
            " ".join(entry.get("tags", [])) if isinstance(entry.get("tags"), list) else str(entry.get("tags", "")),
            " ".join(entry.get("keywords", [])) if isinstance(entry.get("keywords"), list) else "",
        ]).lower()

        for kw in keyword_lower:
            if kw in searchable:
                score += 1

        if score > 0:
            entry["_score"] = score
            scored.append(entry)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


def main():
    parser = argparse.ArgumentParser(description="Search existing distilled documents by keyword or tag.")
    parser.add_argument("keywords", nargs="+", help="Keywords or tags to search for")
    parser.add_argument("--dir", required=True, help="Directory to search for .md files")
    parser.add_argument("--distiller-dir", default=".distiller", help="Path to .distiller/ memory directory")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results to return")
    args = parser.parse_args()

    search_dir = Path(args.dir).resolve()
    distiller_dir = Path(args.distiller_dir).resolve()

    index_entries = load_search_index(distiller_dir)
    file_entries = scan_markdown_files(search_dir)

    seen_files = {e.get("file") for e in index_entries}
    for fe in file_entries:
        if fe["file"] not in seen_files:
            index_entries.append(fe)

    results = search(args.keywords, index_entries)

    if not results:
        print(json.dumps({"matches": [], "suggestion": "create_new"}, indent=2))
        sys.exit(0)

    output = {
        "matches": results[:args.limit],
        "suggestion": "append_to_existing" if results[0].get("_score", 0) >= 2 else "create_new",
    }

    for match in output["matches"]:
        match.pop("_score", None)

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
