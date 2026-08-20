#!/usr/bin/env python3
"""Remove unused report references and renumber remaining citations."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Dict, List, Sequence, Tuple


REFERENCE_HEADING_RE = re.compile(r"^##\s+(参考资料|References)\s*$", re.IGNORECASE)
REFERENCE_RE = re.compile(
    r"^\s*(\d+)\.\s+\[([^\]]+)\]\((https?://[^)\s]+)\)"
    r"(?:\s*[—-]\s*(.+))?\s*$"
)
CITATION_RE = re.compile(r"(?<!!)\[(\d+)\](?!\()")


class NormalizeError(ValueError):
    """Raised when references cannot be normalized safely."""


Reference = Tuple[str, str, str]


def split_references(lines: Sequence[str]) -> Tuple[List[str], str, List[str]]:
    matches = [index for index, line in enumerate(lines) if REFERENCE_HEADING_RE.match(line)]
    if len(matches) != 1:
        raise NormalizeError("报告必须且只能包含一个“## 参考资料”章节。")
    index = matches[0]
    return list(lines[:index]), lines[index], list(lines[index + 1 :])


def parse_references(lines: Sequence[str]) -> Tuple[List[int], Dict[int, Reference]]:
    order: List[int] = []
    references: Dict[int, Reference] = {}
    for line in lines:
        if not line.strip():
            continue
        match = REFERENCE_RE.match(line)
        if not match:
            raise NormalizeError(f"参考资料格式不正确：{line.strip()}")
        number = int(match.group(1))
        if number in references:
            raise NormalizeError(f"参考资料编号重复：[{number}]")
        order.append(number)
        references[number] = (
            match.group(2).strip(),
            match.group(3).strip(),
            (match.group(4) or "").strip(),
        )
    if not references:
        raise NormalizeError("参考资料章节没有有效来源。")
    return order, references


def normalize(markdown: str) -> Tuple[str, List[int]]:
    if not markdown.strip():
        raise NormalizeError("报告内容为空。")

    body_lines, heading, reference_lines = split_references(markdown.splitlines())
    order, references = parse_references(reference_lines)
    cited = [int(value) for value in CITATION_RE.findall("\n".join(body_lines))]
    if not cited:
        raise NormalizeError("正文没有任何引用。")

    missing = sorted(set(cited) - set(references))
    if missing:
        labels = "、".join(f"[{number}]" for number in missing)
        raise NormalizeError(f"正文引用没有对应的参考资料：{labels}")

    used = set(cited)
    kept = [number for number in order if number in used]
    removed = [number for number in order if number not in used]
    mapping = {old: new for new, old in enumerate(kept, 1)}

    def replace_citation(match: re.Match[str]) -> str:
        old = int(match.group(1))
        return f"[{mapping[old]}]"

    normalized_body = [CITATION_RE.sub(replace_citation, line) for line in body_lines]
    normalized_references: List[str] = []
    for old in kept:
        title, url, details = references[old]
        suffix = f" — {details}" if details else ""
        normalized_references.append(f"{mapping[old]}. [{title}]({url}){suffix}")

    output_lines = normalized_body + [heading, ""] + normalized_references
    return "\n".join(output_lines).rstrip() + "\n", removed


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(content)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input
    try:
        markdown = args.input.read_text(encoding="utf-8")
        normalized, removed = normalize(markdown)
        atomic_write(output, normalized)
    except (OSError, UnicodeError, NormalizeError) as exc:
        print(f"引用整理失败：{exc}", file=sys.stderr)
        return 1

    removed_text = "、".join(f"[{number}]" for number in removed) or "无"
    print(f"引用整理完成；删除未使用来源：{removed_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
