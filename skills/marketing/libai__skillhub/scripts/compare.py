#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare before/after transformation with side-by-side detection scores."""

import argparse
import json
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from cli_utils import (
    add_common_args, read_input, validate_text, DETECTION_CATEGORIES,
)
from analyzer import AIDetector
from rewrite import AIRewriter
from utils import write_file


def main():
    parser = argparse.ArgumentParser(
        description="Compare AI detection before/after transformation"
    )
    add_common_args(parser, with_aggressive=True)

    args = parser.parse_args()

    text, _ = read_input(args)
    validate_text(text)

    detector = AIDetector(user_rules_path=args.rules)
    rewriter = AIRewriter(user_rules_path=args.rules)

    before = detector.detect(text)
    transformed, changes = rewriter.rewrite(text, aggressive=args.aggressive)
    after = detector.detect(transformed)

    icons = {"very high": "\U0001f534", "high": "\U0001f7e0",
             "medium": "\U0001f7e1", "low": "\U0001f7e2"}

    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("BEFORE \u2192 AFTER COMPARISON")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"{'Metric':<25} {'Before':<15} {'After':<15} {'Change':<10}")
    lines.append("-" * 60)

    issue_diff = after.total_issues - before.total_issues
    issue_sign = "+" if issue_diff > 0 else ""
    lines.append(
        f"{'Issues':<25} {before.total_issues:<15} "
        f"{after.total_issues:<15} {issue_sign}{issue_diff}"
    )

    prob_before = f"{before.ai_probability:.1f}%"
    prob_after = f"{after.ai_probability:.1f}%"
    lines.append(
        f"{'AI Probability':<25} {icons.get(before.ai_level, '')} "
        f"{before.ai_level} ({prob_before}) \u2192 "
        f"{icons.get(after.ai_level, '')} {after.ai_level} ({prob_after})"
    )
    lines.append(
        f"{'Word Count':<25} {before.word_count:<15} "
        f"{after.word_count:<15} {after.word_count - before.word_count:+}"
    )

    if not args.quiet:
        lines.append("")
        lines.append(
            f"{'Category Changes':<25} {'Before':<15} {'After':<15} {'Change':<10}"
        )
        lines.append("-" * 60)

        for name, attr in DETECTION_CATEGORIES:
            before_val = getattr(before, attr)
            after_val = getattr(after, attr)
            diff = after_val - before_val
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            lines.append(f"{name:<25} {before_val:<15} {after_val:<15} {diff_str}")

    if changes and not args.quiet:
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"TRANSFORMATIONS ({len(changes)})")
        lines.append("=" * 60)
        for c in changes:
            lines.append(f" \u2022 {c}")

    reduction = before.total_issues - after.total_issues
    lines.append("")
    if reduction > 0:
        pct = (reduction / before.total_issues * 100) if before.total_issues else 0
        lines.append(f"\u2713 Reduced {reduction} issues ({pct:.0f}% improvement)")
    elif reduction < 0:
        lines.append(f"\u26a0 Issues increased by {-reduction}")
    else:
        lines.append("\u2014 No change in issue count")

    result = "\n".join(lines)

    if args.output:
        write_file(args.output, result)
        result += f"\n\n\u2192 Saved comparison report to {args.output}"

    print(result)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"[文件未找到] {e}\n→ 建议：请检查文件路径和规则文件路径是否正确。", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[规则解析失败] JSON 格式错误：{e.msg}（位置 {e.pos}）\n→ 建议：请检查规则文件是否为合法 JSON。", file=sys.stderr)
        sys.exit(3)
    except MemoryError:
        print("[内存不足] 输入文本过大，无法一次性处理。\n→ 建议：将文本拆分为多个小文件分批处理。", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"[未知错误] {type(e).__name__}: {e}\n→ 建议：请检查输入文本和规则配置是否有效。", file=sys.stderr)
        sys.exit(99)
