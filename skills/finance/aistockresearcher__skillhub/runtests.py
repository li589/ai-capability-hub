#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-researcher 测试启动包装。

用法（在技能根目录）：
    python runtests.py                  # 跑全部测试
    python runtests.py tests/test_v71_analysis.py    # 跑指定文件
    python runtests.py -k reliability    # 关键字过滤

为什么需要这个包装：
  Python 在 import conftest.py 时会先编译源码再执行，
  因此 conftest.py 内部即使设置了 sys.dont_write_bytecode = True
  也晚于自身字节码的写入，会留下 __pycache__/conftest.cpython-*.pyc。
  本包装在 Python 启动前通过 PYTHONDONTWRITEBYTECODE=1 抑制字节码写入，
  彻底防止 conftest.pyc 被反写到磁盘（保证交付包干净）。
"""
import os
import sys

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None


def main() -> int:
    # 1) 必须在 Python 启动早期设置，子进程继承
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True

    # 2) 组装 pytest 参数
    args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/"]
    if pytest is None:
        print("pytest 未安装，请先安装 pytest 后运行。")
        return 2

    # 3) 同一进程内运行，避免 Windows 上子进程启动后 stdout flush 报 OSError
    print(f"🧪 pytest {' '.join(args)}")
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main())
