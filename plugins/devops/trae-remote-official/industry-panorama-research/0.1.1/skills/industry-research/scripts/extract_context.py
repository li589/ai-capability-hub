#!/usr/bin/env python3
"""Extract compact, citation-preserving context for later research stages."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Callable, Iterable, List, Sequence


NOTE_FILES = (
    "macro.md",
    "market.md",
    "chain.md",
    "competition.md",
    "companies.md",
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CITATION_RE = re.compile(r"(?<!!)\[(\d+)\]")
REFERENCE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")
MAX_SUPPORTING_LINES = 2
MAX_REPORT_BLOCKS = 2
MAX_REPORT_BLOCK_LINES = 8
MAX_DELIVERY_VISUALS = 3
EDITORIAL_HEADINGS = (
    "核心结论",
    "市场规模",
    "产业链与关键瓶颈",
    "竞争格局",
    "重点企业",
    "宏观与政策环境",
    "趋势、机会与风险",
    "结论与展望",
)
DELIVERY_HEADINGS = (
    "核心结论",
    "行业概览",
    "市场规模",
    "产业链与关键瓶颈",
    "竞争格局",
    "重点企业",
    "宏观与政策环境",
    "趋势、机会与风险",
    "结论与展望",
)


def extract_section(
    lines: Sequence[str], predicate: Callable[[str], bool]
) -> List[str]:
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match or not predicate(match.group(2).strip()):
            continue
        level = len(match.group(1))
        end = len(lines)
        for cursor in range(index + 1, len(lines)):
            next_match = HEADING_RE.match(lines[cursor])
            if next_match and len(next_match.group(1)) <= level:
                end = cursor
                break
        return trim_blank_lines(lines[index + 1 : end])
    return []


def trim_blank_lines(lines: Iterable[str]) -> List[str]:
    result = list(lines)
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()
    return result


def extract_references(lines: Sequence[str], numbers: set[int]) -> List[str]:
    references = extract_section(
        lines, lambda title: title.lower() in {"参考资料", "references"}
    )
    selected: List[str] = []
    for line in references:
        match = REFERENCE_RE.match(line)
        if match and int(match.group(1)) in numbers:
            selected.append(line)
    return selected


def extract_supporting_lines(
    lines: Sequence[str], excluded_lines: Sequence[str]
) -> List[str]:
    """Return a few cited body lines when the core judgment has no citations."""

    excluded = {line.strip() for line in excluded_lines if line.strip()}
    selected: List[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = HEADING_RE.match(line)
        if heading and heading.group(2).strip().lower() in {"参考资料", "references"}:
            break
        if (
            not stripped
            or heading
            or stripped in excluded
            or stripped.startswith("|")
            or not CITATION_RE.search(stripped)
        ):
            continue
        selected.append(stripped)
        if len(selected) == MAX_SUPPORTING_LINES:
            break
    return selected


def note_title(lines: Sequence[str], fallback: str) -> str:
    for line in lines:
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()
    return fallback


def compact_note(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    first_nonempty = next((line.strip() for line in lines if line.strip()), "")
    title = note_title(lines, path.stem)
    output = [f"# {title}（{path.name}）"]
    if first_nonempty.upper().startswith("INSUFFICIENT:") or first_nonempty.startswith(
        "INSUFFICIENT："
    ):
        output.extend(["", first_nonempty])
        return "\n".join(output)

    core = extract_section(lines, lambda heading: "核心判断" in heading)
    limits = extract_section(
        lines,
        lambda heading: any(
            keyword in heading
            for keyword in ("资料限制", "研究限制", "证据边界", "数据缺口", "局限")
        ),
    )
    core_numbers = {int(number) for number in CITATION_RE.findall("\n".join(core))}
    evidence = [] if core_numbers else extract_supporting_lines(lines, core + limits)
    cited_numbers = {
        int(number)
        for number in CITATION_RE.findall("\n".join(core + evidence + limits))
    }
    references = extract_references(lines, cited_numbers)

    output.extend(["", "## 核心判断"])
    output.extend(core or ["未找到“核心判断”段落。"])
    if evidence:
        output.extend(["", "## 关键证据"])
        output.extend(evidence)
    output.extend(["", "## 资料限制"])
    output.extend(limits or ["专题稿未单列资料限制。"])
    output.extend(["", "## 上述段落引用的参考资料"])
    output.extend(references or ["上述段落没有可提取的参考资料。"])
    return "\n".join(output)


def build_context(work_dir: Path) -> str:
    notes_dir = work_dir / "notes"
    available = [notes_dir / name for name in NOTE_FILES if (notes_dir / name).is_file()]
    if not available:
        raise FileNotFoundError("没有可提取的前序专题稿")
    return "\n\n".join(compact_note(path) for path in available)


def split_h2_sections(lines: Sequence[str]) -> tuple[List[str], dict[str, List[str]]]:
    """Return report prelude and second-level sections without expanding content."""

    indexes: List[tuple[str, int]] = []
    in_fence = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) == 2:
            indexes.append((match.group(2).strip(), index))

    if not indexes:
        raise ValueError("报告中没有可提取的二级章节")

    prelude = trim_blank_lines(lines[: indexes[0][1]])
    sections: dict[str, List[str]] = {}
    for position, (title, start) in enumerate(indexes):
        end = indexes[position + 1][1] if position + 1 < len(indexes) else len(lines)
        sections[title] = trim_blank_lines(lines[start + 1 : end])
    return prelude, sections


def compact_block(lines: Sequence[str]) -> List[str]:
    """Keep one complete Markdown block small without cutting prose mid-line."""

    if len(lines) <= MAX_REPORT_BLOCK_LINES:
        return list(lines)
    return list(lines[:MAX_REPORT_BLOCK_LINES])


def first_report_blocks(lines: Sequence[str]) -> List[str]:
    """Select the first substantive prose or table blocks, excluding visual payloads."""

    blocks: List[List[str]] = []
    current: List[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if current:
                blocks.append(compact_block(current))
                current = []
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            if current:
                blocks.append(compact_block(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(compact_block(current))

    selected: List[str] = []
    for block in blocks[:MAX_REPORT_BLOCKS]:
        if selected:
            selected.append("")
        selected.extend(block)
    return selected


def extract_visual_blocks(lines: Sequence[str]) -> List[str]:
    """Keep a few already-published visual payloads for the final response."""

    blocks: List[str] = []
    current: List[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if not collecting and stripped in {"```chart", "```visual"}:
            collecting = True
            current = [line]
            continue
        if not collecting:
            continue
        current.append(line)
        if stripped == "```":
            blocks.append("\n".join(current))
            collecting = False
            current = []
            if len(blocks) == MAX_DELIVERY_VISUALS:
                break
    return blocks


def format_prelude(lines: Sequence[str]) -> List[str]:
    output: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) == 1:
            output.append(f"- 报告标题：{match.group(2).strip()}")
        else:
            output.append(stripped)
    return output


def build_report_context(
    work_dir: Path,
    mode: str,
    source_path: Path | None = None,
    html_path: Path | None = None,
) -> str:
    source_name = "draft.md" if mode == "editorial" else "report.md"
    source = source_path if source_path is not None else work_dir / source_name
    if not source.is_file():
        raise FileNotFoundError(f"缺少上下文来源文件：{source.name}")

    lines = source.read_text(encoding="utf-8").splitlines()
    prelude, sections = split_h2_sections(lines)
    headings = EDITORIAL_HEADINGS if mode == "editorial" else DELIVERY_HEADINGS
    title = "报告编辑上下文" if mode == "editorial" else "最终交付上下文"
    output = [
        f"# {title}",
        "",
        "> 仅使用下列已组装或已核查内容，不回读完整报告，不新增事实、计算或来源。",
        "",
        "## 报告元信息",
    ]
    output.extend(format_prelude(prelude) or ["未提取到报告元信息。"])
    if mode == "delivery":
        delivered_html = html_path if html_path is not None else source.with_suffix(".html")
        output.extend(
            [
                f"- Markdown 文件：{source.name}",
                f"- HTML 文件：{delivered_html.name}",
            ]
        )

    selected_text: List[str] = []
    for heading in headings:
        body = sections.get(heading)
        if not body:
            continue
        compact = first_report_blocks(body)
        if not compact:
            continue
        output.extend(["", f"## {heading}", *compact])
        selected_text.extend(compact)

    visuals: List[str] = []
    if mode == "delivery":
        visuals = extract_visual_blocks(lines)
        if visuals:
            output.extend(["", "## 可复用视觉数据"])
            for block in visuals:
                output.extend(["", block])

    cited_numbers = {
        int(number)
        for number in CITATION_RE.findall(
            "\n".join(selected_text + visuals)
        )
    }
    references = extract_references(lines, cited_numbers)
    output.extend(["", "## 上述内容引用的参考资料"])
    output.extend(references or ["上述内容没有可提取的参考资料。"])
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument(
        "--mode",
        choices=("trend", "editorial", "delivery"),
        default="trend",
        help="Context target. Defaults to trend.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the compact context to this file instead of stdout.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Delivery mode source Markdown. Defaults to report.md for compatibility.",
    )
    args = parser.parse_args()
    try:
        context = (
            build_context(args.work_dir)
            if args.mode == "trend"
            else build_report_context(args.work_dir, args.mode, source_path=args.input)
        )
        if args.output:
            args.output.write_text(context.rstrip() + "\n", encoding="utf-8")
            print(f"紧凑上下文已生成：{args.output}")
        else:
            print(context)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"紧凑上下文提取失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
