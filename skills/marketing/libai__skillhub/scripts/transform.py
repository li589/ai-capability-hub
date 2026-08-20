#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line interface for AI text rewriting."""

import argparse
import json
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from cli_utils import add_common_args, read_input, validate_text
from rewrite import AIRewriter
from utils import write_file


def main():
    parser = argparse.ArgumentParser(
        description="Rewrite AI-generated text to sound more natural."
    )
    add_common_args(parser, with_aggressive=True)
    
    args = parser.parse_args()
    
    text, _ = read_input(args)
    validate_text(text)
    
    rewriter = AIRewriter(user_rules_path=args.rules)
    rewritten, changes = rewriter.rewrite(text, aggressive=args.aggressive)
    
    if not args.quiet and changes:
        print(f"Changes ({len(changes)}):", file=sys.stderr)
        for c in changes:
            print(f" • {c}", file=sys.stderr)
    
    if args.output:
        write_file(args.output, rewritten)
        if not args.quiet:
            print(f"→ Saved to {args.output}", file=sys.stderr)
    else:
        print(rewritten)


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
        print(f"[未知错误] {type(e).__name__}: {e}\n→ 建议：请检查输入文本是否有效，或尝试使用 -a 开启激进模式重试。", file=sys.stderr)
        sys.exit(99)
