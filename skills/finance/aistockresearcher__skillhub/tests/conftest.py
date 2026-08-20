"""pytest conftest — 屏蔽重型三方库，确保零依赖测试可运行。

v7.1 强化：
  - 第一时间禁用 Python 字节码生成（设置 sys.dont_write_bytecode = True）
  - 通过 PYTHONDONTWRITEBYTECODE=1 让 pytest 内部 import 链也不写 .pyc
  - 防止 tests/__pycache__/conftest.cpython-311-pytest-*.pyc 反写到磁盘
"""
import sys
import types
import os
from pathlib import Path

# 阻止字节码生成（conftest.py 被 import 时，Python 已先编译，但通过环境变量可抑制）
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# === 屏蔽重型三方库（确保零依赖测试不引入 pip 包）===
class HeavyLibBlocker:
    BLOCKED = (
        "numpy", "pandas", "sklearn", "scipy", "arch", "statsmodels",
        "lightgbm", "matplotlib", "empyrical", "openpyxl", "docx",
        "requests", "ollama", "mootdx", "mcp", "langchain", "langgraph",
        "akshare",  # v8.0: akshare 内部依赖 pandas，测试环境需离线确定性
    )

    def find_module(self, name, path=None):
        for b in self.BLOCKED:
            if name == b or name.startswith(b + ".") or name.startswith(b + "_"):
                return self
        return None

    def load_module(self, name):
        raise ImportError("blocked " + name)


sys.meta_path.insert(0, HeavyLibBlocker())


# === stub crawl_utils 防止 fund_analyzer/market 因 requests 被屏蔽而导入失败 ===
_crawl_stub = types.ModuleType("crawl_utils")
_crawl_stub.safe_request = lambda *a, **k: None
_crawl_stub.fetch_json = lambda *a, **k: None
_crawl_stub.today_str = lambda fmt="%Y-%m-%d": "2026-07-26"
_crawl_stub.read_json = lambda p, d=None: d
_crawl_stub.write_json = lambda p, d, indent=2: True
_crawl_stub.detect_encoding = lambda r, d="utf-8": d
sys.modules["crawl_utils"] = _crawl_stub


def pytest_configure(config):
    """pytest 启动时再次确认字节码关闭。"""
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def pytest_load_initial_conftests(early_config, parser, args):
    """在加载其他 conftest 之前强制设置。"""
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
