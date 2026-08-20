#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared CLI utilities for content-deai scripts.

Provides unified argument parsing, input reading, error handling,
and shared constants to eliminate duplication across detect.py,
transform.py, and compare.py.
"""

import sys
from typing import Tuple, Optional

from utils import read_file


# ---------- 统一的检测类别列表 ----------
# 用于 detect.py / compare.py 展示；与 DetectionReport 字段对齐
DETECTION_CATEGORIES = [
    ("AI Jargon",           "ai_jargon_count"),
    ("Puffery (夸大)",      "puffery_count"),
    ("Marketing Speak",     "marketing_count"),
    ("Vague Attributions",  "vague_count"),
    ("Hedging",             "hedging_count"),
    ("Chatbot Artifacts",   "chatbot_count"),
    ("Citation Bugs",       "citation_count"),
    ("Knowledge Cutoff",    "cutoff_count"),
    ("Markdown",            "markdown_count"),
    ("Negative Parallelisms","negative_parallel_count"),
    ("Superficial Verbs",   "superficial_verb_count"),
    ("Filler Phrases",      "filler_count"),
    ("Rule of Three",       "rule_of_three_count"),
    ("Sentence Starters",   "sentence_starter_count"),
    ("Rhetorical Patterns", "rhetorical_count"),
    ("List Markers",        "list_marker_count"),
]

PUNCTUATION_ITEMS = [
    ("Em dashes (——)",      "em_dash_count"),
    ("Curly quotes",        "curly_quote_count"),
    ("Exclamation marks",   "exclamation_count"),
    ("Question marks",      "question_count"),
]


# ---------- 公共 CLI 参数 ----------
def add_common_args(parser, *, with_output: bool = True,
                    with_aggressive: bool = False,
                    with_quiet: bool = True) -> None:
    """向 argparse.ArgumentParser 添加公共参数。

    :param parser: argparse.ArgumentParser 实例
    :param with_output: 是否添加 -o/--output 参数
    :param with_aggressive: 是否添加 -a/--aggressive 参数
    :param with_quiet: 是否添加 -q/--quiet 参数
    """
    parser.add_argument(
        "input", nargs="?",
        help="Input file path (reads from stdin if omitted)"
    )
    parser.add_argument(
        "-r", "--rules",
        help="Path to user-defined rules JSON file"
    )
    if with_output:
        parser.add_argument(
            "-o", "--output",
            help="Write result to file (default: stdout)"
        )
    if with_aggressive:
        parser.add_argument(
            "-a", "--aggressive", action="store_true",
            help="Enable aggressive rewriting mode"
        )
    if with_quiet:
        parser.add_argument(
            "-q", "--quiet", action="store_true",
            help="Suppress detailed / change-log output"
        )


# ---------- 统一输入读取 ----------
def read_input(args) -> Tuple[str, Optional[str]]:
    """从命令行参数读取输入文本。

    优先读取 -r/--rules 指定的文件，否则从 stdin 读取。

    :returns: (text, input_path_or_None)
    """
    if args.input:
        try:
            text = read_file(args.input)
            return text, args.input
        except FileNotFoundError:
            print(
                "[文件未找到] 无法读取输入文件：{}。\n"
                "→ 建议：请检查文件路径是否正确，确认文件存在且未被占用。".format(args.input),
                file=sys.stderr
            )
            sys.exit(1)
        except PermissionError:
            print(
                "[权限不足] 没有读取权限：{}。\n"
                "→ 建议：请检查文件权限设置，或尝试以管理员身份运行。".format(args.input),
                file=sys.stderr
            )
            sys.exit(1)
        except UnicodeDecodeError:
            print(
                "[编码错误] 文件编码不兼容：{}。\n"
                "→ 建议：请确认文件为 UTF-8 编码，或将文本粘贴到标准输入。".format(args.input),
                file=sys.stderr
            )
            sys.exit(1)
    else:
        text = sys.stdin.read()
        return text, None


def validate_text(text: str) -> None:
    """验证输入文本非空；为空则输出错误并退出。"""
    if not text:
        print(
            "[输入为空] 没有收到任何文本内容。\n"
            "→ 建议：请提供待检测/改写的文本，或指定文件路径（如 `python detect.py mytext.txt`），"
            "也可通过管道输入（`echo 文本 | python detect.py`）。",
            file=sys.stderr
        )
        sys.exit(1)
