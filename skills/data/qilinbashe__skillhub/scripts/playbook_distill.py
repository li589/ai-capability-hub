# playbook_distill.py: 运行时依赖脚本（技能运行调用）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""playbook_distill.py — 方法论飞轮沉淀脚本（v4.5.1 交付；v4.21.0 随 update_memory 支持
容量上限 FIFO 淘汰与 fuzzify 数字模糊化）

把本次办案中可复用的步骤、追问、路由决策、踩坑和律师纠偏写入 MEMORY.md。
只记方法，不记案情；写入前后执行 PII / 案情标识硬校验；数字模糊化与容量
上限机制复用 update_memory.py（fuzzify / MAX_ENTRIES=500 FIFO）。

用法：
  python scripts/playbook_distill.py --check
  python scripts/playbook_distill.py --entry "可复用方法：..."
  python scripts/playbook_distill.py --entry "..." --dry-run
"""

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_memory import append_entry, check_memory  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="律师助手方法论飞轮沉淀")
    ap.add_argument("--check", action="store_true", help="校验 MEMORY.md")
    ap.add_argument("--entry", help="可复用方法条目")
    ap.add_argument("--dry-run", action="store_true", help="仅预览")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if check_memory() else 1)
    if not args.entry:
        ap.print_help()
        sys.exit(2)
    ok = append_entry("方法论", args.entry, args.dry_run)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
