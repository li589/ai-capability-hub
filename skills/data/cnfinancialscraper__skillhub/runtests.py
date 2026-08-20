#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cn-financial-scraper 测试启动包装。

用法（在技能根目录）：
    python runtests.py                  # 跑全部测试
    python runtests.py tests/test_backtester.py    # 跑指定文件
    python runtests.py -k backtest      # 关键字过滤

为什么需要这个包装：
  Python 在 import conftest.py 时会先编译源码再执行，
  因此 conftest.py 内部即使设置了 sys.dont_write_bytecode = True
  也晚于自身字节码的写入，会留下 __pycache__/conftest.cpython-*.pyc。
  本包装：
    1. 在 Python 启动前通过 PYTHONDONTWRITEBYTECODE=1 抑制字节码写入
    2. 跑测试前后自动清理已生成的 __pycache__（彻底保证交付包干净）
"""
import os
import shutil
import sys
from pathlib import Path

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None


def _cleanup_pycache():
    """清理项目内所有 __pycache__ 与 .pyc 文件。

    这是本项目的「防上传二进制文件」关键防线：
    由于 Python 字节码生成是 import 时的固行为，无法仅靠 env 变量
    完全阻止（conftest.py 自身的 pyc 在加载时即生成）。
    所以采用「跑完测试立刻清理」兜底方案。
    """
    root = Path(__file__).resolve().parent
    cleaned = 0
    # 1) 删除所有 __pycache__ 目录
    for cache_dir in root.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            cleaned += 1
        except OSError:
            pass
    # 2) 兜底删除散落的 .pyc 文件
    for pyc in root.rglob("*.pyc"):
        try:
            pyc.unlink()
            cleaned += 1
        except OSError:
            pass
    if cleaned:
        print(f"🧹 清理 {cleaned} 个字节码缓存项")


def main() -> int:
    # 1) 必须在 Python 启动早期设置，子进程继承
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True

    # 2) 跑测试前先清理（兜底之前可能残留的）
    _cleanup_pycache()

    # 3) 组装 pytest 参数
    args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/"]
    if pytest is None:
        print("pytest 未安装，请先安装 pytest 后运行。")
        return 2

    # 4) 同一进程内运行，避免 Windows 上子进程启动后 stdout flush 报 OSError
    print(f"🧪 pytest {' '.join(args)}")
    rc = pytest.main(args)

    # 5) 跑完测试立刻清理（防御性）
    _cleanup_pycache()
    return rc


if __name__ == "__main__":
    sys.exit(main())
