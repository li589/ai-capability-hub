# -*- coding: utf-8 -*-
"""
clean.py — 交付前清理脚本（v7.0.0 补齐）

上传系统拒绝二进制文件（.pyc/.pdf/.png 等），交付 skill 包前必须清干净。

用法：
  python clean.py --dry-run    # 只列出将删除的内容（推荐先跑）
  python clean.py --full       # 删除 __pycache__/pytest_cache + 运行时产物目录
  python clean.py --binary     # 只删已知二进制文件（pdf/png/jpg/zip/docx 等）

注意：
  - 清理之后不要再执行任何 import 项目代码的命令（会重新生成 .pyc）；
    必要验证请加 PYTHONDONTWRITEBYTECODE=1
  - 测试请走 runtests.py（自带前后清理），不要直跑 python -m pytest
"""
import argparse
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent

# 运行时产物目录（整目录删除；macros/ 是用户宏资产，不删）
RUNTIME_DIRS = [
    "data/exports", "data/reports", "data/generated_reports", "data/charts",
    "data/packages", "data/archives", "data/scheduler_logs",
    "data/sentiment_exports", "data/sentiment_snapshots",
    "data/backtest_conflicts", "data/overseas_cache", "data/scrape_cache",
    "data/browser_cache", "data/browser_state", "data/screenshots",
    "data/downloads", "data/selector_cache", "data/temp_packages",
]

# 已知二进制扩展名
BINARY_EXTS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".docx", ".xlsx",
    ".pptx", ".exe", ".bin", ".onnx", ".pyc", ".pyo", ".pyd", ".7z", ".rar",
}


def _scan_binary() -> list:
    hits = []
    for f in SKILL_DIR.rglob("*"):
        if f.is_file() and f.suffix.lower() in BINARY_EXTS:
            hits.append(f)
    return hits


def _scan_pycache() -> list:
    return [d for d in SKILL_DIR.rglob("__pycache__") if d.is_dir()]


def _scan_pytest_cache() -> list:
    return [d for d in SKILL_DIR.rglob(".pytest_cache") if d.is_dir()]


def dry_run():
    print("== 二进制文件 ==")
    for f in _scan_binary():
        print(f"  {f.relative_to(SKILL_DIR)} ({f.stat().st_size} B)")
    print("== __pycache__ 目录 ==")
    for d in _scan_pycache():
        print(f"  {d.relative_to(SKILL_DIR)}/")
    print("== .pytest_cache 目录 ==")
    for d in _scan_pytest_cache():
        print(f"  {d.relative_to(SKILL_DIR)}/")


def full():
    n = 0
    for f in _scan_binary():
        try:
            f.unlink()
            n += 1
        except OSError:
            pass
    for d in _scan_pycache() + _scan_pytest_cache():
        try:
            shutil.rmtree(d, ignore_errors=True)
            n += 1
        except OSError:
            pass
    for rel in RUNTIME_DIRS:
        d = SKILL_DIR / rel
        if d.exists() and d.is_dir():
            try:
                shutil.rmtree(d, ignore_errors=True)
                n += 1
            except OSError:
                pass
    print(f"清理完成：{n} 项")
    dry_run()


def binary_only():
    n = 0
    for f in _scan_binary():
        try:
            f.unlink()
            n += 1
        except OSError:
            pass
    print(f"删除二进制文件 {n} 个")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="交付前二进制清理")
    ap.add_argument("--dry-run", action="store_true", help="只列出不删除")
    ap.add_argument("--full", action="store_true", help="全量清理（推荐）")
    ap.add_argument("--binary", action="store_true", help="只删二进制文件")
    args = ap.parse_args()
    if args.dry_run:
        dry_run()
    elif args.binary:
        binary_only()
    else:
        full()
