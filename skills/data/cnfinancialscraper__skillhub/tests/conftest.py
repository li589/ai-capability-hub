# -*- coding: utf-8 -*-
"""cn-financial-scraper 测试根 conftest.

设计要点：
  1. 第一时间禁用 Python 字节码生成（设置 sys.dont_write_bytecode = True），
     同时通过环境变量 PYTHONDONTWRITEBYTECODE=1 让子进程继承，
     防止 tests/__pycache__/conftest.cpython-311-pytest-*.pyc 这类文件被
     pytest 加载 conftest 时反写到磁盘。
  2. 把 scripts/ 加入 sys.path，方便 `import sentiment_crawler` 等绝对导入。
"""
import os
import sys
from pathlib import Path

# ---- 1) 阻止字节码生成 ----
# 这行虽然在被 pytest import 时已经晚于 conftest.py 自身的字节码写入，
# 但可通过 -p no:cacheprovider 等机制抑制；同时强制设置环境变量，
# 让子进程与 pytest 内部 import 链都不写 pyc。
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

# ---- 2) 确保 scripts/ 可导入 ----
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def pytest_configure(config):
    """pytest 启动时再次确认字节码关闭。"""
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def pytest_load_initial_conftests(early_config, parser, args):
    """在加载其他 conftest 之前强制设置（无需 pytest hook 装饰器）。"""
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"