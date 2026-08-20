#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line interface for AI text detection."""

import argparse
import json
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from cli_utils import (
    add_common_args, read_input, validate_text,
    DETECTION_CATEGORIES, PUNCTUATION_ITEMS,
)
from analyzer import AIDetector
from utils import write_file


def print_report(report):
    """Print formatted detection report."""
    icons = {"very high": "\U0001f534", "high": "\U0001f7e0",
             "medium": "\U0001f7e1", "low": "\U0001f7e2"}

    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("AI DETECTION REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Word Count: {report.word_count}")
    lines.append(f"Character Count: {report.char_count}")
    lines.append(f"Total Issues: {report.total_issues}")
    lines.append(
        f"AI Probability: {icons.get(report.ai_level, '')} "
        f"{report.ai_probability:.1f}% (Level: {report.ai_level.upper()})"
    )

    lines.append("")
    lines.append("-" * 60)
    lines.append("Category Breakdown:")
    lines.append("-" * 60)

    for name, attr in DETECTION_CATEGORIES:
        count = getattr(report, attr)
        if count > 0:
            lines.append(f"  {name:<25} {count}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("Punctuation:")
    lines.append("-" * 60)
    for name, attr in PUNCTUATION_ITEMS:
        count = getattr(report, attr)
        if count > 0:
            lines.append(f"  {name:<25} {count}")

    if report.sentence_reports:
        high_risk = [s for s in report.sentence_reports if s.score > 0]
        if high_risk:
            lines.append("")
            lines.append("=" * 60)
            lines.append("Suspicious Sentences (with issues):")
            lines.append("=" * 60)
            for i, s in enumerate(high_risk[:10], 1):
                lines.append("")
                lines.append(f"{i}. [Score: {s.score}] {s.sentence[:100]}...")
                if s.reasons:
                    lines.append(f"   Reasons: {', '.join(s.reasons[:3])}")
            if len(high_risk) > 10:
                lines.append(
                    f"\n... and {len(high_risk) - 10} more suspicious sentences."
                )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Detect AI patterns in text (no rewriting)"
    )
    add_common_args(parser, with_aggressive=False)
    parser.add_argument("-j", "--json", action="store_true",
                        help="Output results in JSON format")
    parser.add_argument("-s", "--score-only", action="store_true",
                        help="Print only score and probability")
    parser.add_argument("--no-sentences", action="store_true",
                        help="Skip displaying suspicious sentences")

    args = parser.parse_args()

    text, _ = read_input(args)
    validate_text(text)

    detector = AIDetector(user_rules_path=args.rules)
    report = detector.detect(text)

    if args.json:
        output = {
            "word_count": report.word_count,
            "char_count": report.char_count,
            "total_issues": report.total_issues,
            "ai_probability": report.ai_probability,
            "ai_level": report.ai_level,
            "categories": {attr: getattr(report, attr) for _, attr in DETECTION_CATEGORIES},
            "punctuation": {attr: getattr(report, attr) for _, attr in PUNCTUATION_ITEMS},
        }
        result = json.dumps(output, ensure_ascii=False, indent=2)
    elif args.score_only:
        result = (
            f"Issues: {report.total_issues} | "
            f"Words: {report.word_count} | "
            f"AI: {report.ai_probability:.1f}% ({report.ai_level})"
        )
    else:
        result = print_report(report)

    if args.output:
        write_file(args.output, result)
        if not args.quiet:
            print(f"\u2192 Saved to {args.output}", file=sys.stderr)
    else:
        print(result)


    # 差异化退出码：便于 CI/CD 流水线根据 AI 概率做出自动化决策
    level_map = {"low": 0, "medium": 1, "high": 2, "very_high": 3}
    sys.exit(level_map.get(report.ai_level, 0))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"[文件未找到] {e}\n→ 建议：请检查文件路径是否正确，确认规则文件存在。", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[规则解析失败] JSON 格式错误：{e.msg}（位置 {e.pos}）\n→ 建议：请检查规则文件是否为合法 JSON，可使用 jsonlint 验证。", file=sys.stderr)
        sys.exit(3)
    except MemoryError:
        print("[内存不足] 输入文本过大，无法一次性处理。\n→ 建议：将文本拆分为多个小文件分批处理。", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"[未知错误] {type(e).__name__}: {e}\n→ 建议：请检查输入文本是否有效，或尝试使用 --rules 指定规则文件路径。", file=sys.stderr)
        sys.exit(99)
