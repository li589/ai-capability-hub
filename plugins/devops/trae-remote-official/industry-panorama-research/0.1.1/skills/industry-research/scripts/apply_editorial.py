#!/usr/bin/env python3
"""Merge the small editorial layer into an assembled research draft."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TARGET_HEADINGS = ("核心结论", "行业概览", "结论与展望")
REQUIRED_HEADINGS = ("核心结论", "结论与展望")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
H1_RE = re.compile(r"^#\s+")
URL_RE = re.compile(r"https?://", re.IGNORECASE)
CITATION_RE = re.compile(r"(?<!!)\[(\d+)\]")
REFERENCE_RE = re.compile(r"^\s*(\d+)\.\s+", re.MULTILINE)


class EditorialError(ValueError):
    """Raised when an editorial file cannot be merged safely."""


def _headings(lines: list[str]) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    in_fence = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = H2_RE.match(line)
        if match:
            found.append((match.group(1).strip(), index))
    return found


def _ranges(lines: list[str]) -> tuple[list[tuple[str, int, int]], dict[str, tuple[int, int]]]:
    headings = _headings(lines)
    ranges: list[tuple[str, int, int]] = []
    by_title: dict[str, tuple[int, int]] = {}
    for position, (title, start) in enumerate(headings):
        end = headings[position + 1][1] if position + 1 < len(headings) else len(lines)
        ranges.append((title, start, end))
        if title in by_title:
            raise EditorialError(f"二级标题重复：{title}")
        by_title[title] = (start, end)
    return ranges, by_title


def merge_editorial(draft_text: str, editorial_text: str) -> str:
    """Return a draft with only the permitted editorial sections replaced."""
    if URL_RE.search(editorial_text):
        raise EditorialError("editorial.md 不得增加 URL")

    editorial_lines = editorial_text.splitlines()
    if any(H1_RE.match(line) for line in editorial_lines):
        raise EditorialError("editorial.md 不得包含一级标题")

    draft_lines = draft_text.splitlines()
    draft_ranges, draft_by_title = _ranges(draft_lines)
    editorial_ranges, editorial_by_title = _ranges(editorial_lines)

    for required in REQUIRED_HEADINGS:
        if required not in draft_by_title:
            raise EditorialError(f"draft.md 缺少必要章节：{required}")

    expected = [title for title in TARGET_HEADINGS if title in draft_by_title]
    actual = [title for title, _, _ in editorial_ranges]
    if actual != expected:
        raise EditorialError(
            "editorial.md 只能按草稿顺序包含：" + "、".join(expected)
        )

    unexpected = [title for title in actual if title not in TARGET_HEADINGS]
    if unexpected:
        raise EditorialError("editorial.md 含有不允许的章节：" + "、".join(unexpected))

    for title, (start, end) in editorial_by_title.items():
        body = "\n".join(editorial_lines[start + 1 : end]).strip()
        if not body:
            raise EditorialError(f"editorial.md 章节为空：{title}")

    if "参考资料" not in draft_by_title:
        raise EditorialError("draft.md 缺少参考资料章节")
    ref_start, ref_end = draft_by_title["参考资料"]
    reference_numbers = set(
        REFERENCE_RE.findall("\n".join(draft_lines[ref_start + 1 : ref_end]))
    )
    editorial_citations = set(CITATION_RE.findall(editorial_text))
    unknown = sorted(editorial_citations - reference_numbers, key=int)
    if unknown:
        raise EditorialError("editorial.md 使用了不存在的引用：" + "、".join(unknown))

    replacements = {
        title: editorial_lines[start:end]
        for title, (start, end) in editorial_by_title.items()
    }
    output: list[str] = []
    cursor = 0
    for title, start, end in draft_ranges:
        if title not in replacements:
            continue
        output.extend(draft_lines[cursor:start])
        output.extend(replacements[title])
        cursor = end
    output.extend(draft_lines[cursor:])
    return "\n".join(output).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将 editorial.md 中允许的章节合并到 assemble.py 生成的 draft.md"
    )
    parser.add_argument("--draft", required=True, help="待更新的 draft.md")
    parser.add_argument("--editorial", required=True, help="局部编辑文件 editorial.md")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    editorial_path = Path(args.editorial)
    try:
        merged = merge_editorial(
            draft_path.read_text(encoding="utf-8"),
            editorial_path.read_text(encoding="utf-8"),
        )
        draft_path.write_text(merged, encoding="utf-8")
    except (OSError, EditorialError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {draft_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
