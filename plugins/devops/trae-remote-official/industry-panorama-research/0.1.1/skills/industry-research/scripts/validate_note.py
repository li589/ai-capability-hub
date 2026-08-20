#!/usr/bin/env python3
"""Validate one industry-research topic note before it enters assembly."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List

from assemble import (
    AssembleError,
    collect_note_errors,
)
from publish import ReportError, looks_like_visual_dsl, render_chart, render_visual


def collect_render_errors(path: Path) -> List[str]:
    """Validate every chart/visual block with the same renderer used for HTML."""

    errors: List[str] = []
    in_fence = False
    language = ""
    block_lines: List[str] = []
    block_number = 0
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```"):
                in_fence = True
                fence_info = stripped[3:].strip()
                language = (
                    fence_info.split(maxsplit=1)[0].lower() if fence_info else ""
                )
                block_lines = []
                if language in {"chart", "visual"}:
                    block_number += 1
            continue

        if stripped.startswith("```"):
            if language in {"chart", "visual"}:
                try:
                    if language == "chart":
                        render_chart(block_lines, block_number)
                    else:
                        render_visual(block_lines)
                except ReportError as exc:
                    errors.append(
                        f"第 {block_number} 个 {language} 数据块无法渲染：{exc}"
                    )
            elif looks_like_visual_dsl(block_lines):
                errors.append(
                    "疑似图表或结构图的数据块缺少 chart/visual 围栏标签，不能作为原始代码交付。"
                )
            in_fence = False
            language = ""
            block_lines = []
            continue

        block_lines.append(line)

    if in_fence:
        errors.append(f"第 {line_number} 行之前打开的代码块没有结束标记。")
    return errors


def validate_note(path: Path) -> None:
    errors = collect_note_errors(path) + collect_render_errors(path)
    if errors:
        details = "\n".join(f"- {path.name}：{error}" for error in errors)
        raise AssembleError(f"共发现 {len(errors)} 项问题：\n{details}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate_note(args.input)
    except (AssembleError, OSError) as exc:
        print(f"专题稿检查失败：{exc}", file=sys.stderr)
        return 1
    print(f"专题稿检查通过：{args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
