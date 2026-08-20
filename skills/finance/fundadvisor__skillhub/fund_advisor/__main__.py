"""
fund-advisor.__main__
===================

任意 agent 拿到这个 skill 都可以这样启动：

    python -m fund_advisor check    # 自检（依赖 + 数据 + 配置）
    python -m fund_advisor install  # 一键安装缺失依赖
    python -m fund_advisor test     # 跑 pytest
    python -m fund_advisor mcp      # MCP Server（stdio 协议）
    python -m fund_advisor version  # 显示版本

零配置：data/ 目录已含 4,270 位经理档案 + 164 家公司 + 全市场经理现任基金十大重仓（季度更新），开箱即用。
"""
from __future__ import annotations

import argparse
import os
import sys
sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
PKG_PARENT = Path(__file__).resolve().parent.parent  # fund-advisor/

# 路径准备：让 scripts/ 和 fund_advisor/ 都能 import
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PKG_PARENT))


def cmd_mcp(args):
    """启动 MCP Server（stdio 协议）"""
    from mcp_server import main
    main()


def cmd_test(args):
    """跑 pytest"""
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    try:
        import pytest
    except ImportError:
        import subprocess
        r = subprocess.run(
            [sys.executable, '-m', 'pytest', str(ROOT / 'tests'), '-v', '--tb=short'],
            cwd=str(ROOT),
        )
        sys.exit(r.returncode)
    sys.exit(pytest.main([str(ROOT / 'tests'), '-v', '--tb=short', '-p', 'no:cacheprovider']))


def cmd_check(args):
    """自检：依赖 + 数据 + 配置"""
    from .fund_advisor_bootstrap import run_check
    sys.exit(0 if run_check(verbose=True) else 1)


def _get_version() -> str:
    """从 _meta.json 动态读取版本号"""
    try:
        import json
        meta_path = ROOT / "_meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            return meta.get("version", "unknown")
    except Exception:
        pass
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        prog='fund-advisor',
        description='基金投资智能顾问 — 启动入口',
    )
    sub = parser.add_subparsers(dest='cmd', help='子命令')

    # mcp
    p = sub.add_parser('mcp', help='启动 MCP Server（stdio）')
    p.set_defaults(func=cmd_mcp)

    # test
    p = sub.add_parser('test', help='跑测试')
    p.set_defaults(func=cmd_test)

    # check
    p = sub.add_parser('check', help='自检依赖/数据/配置')
    p.set_defaults(func=cmd_check)

    # version
    p = sub.add_parser('version', help='显示版本')
    p.set_defaults(func=lambda a: print(f"fund-advisor v{_get_version()}"))

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
