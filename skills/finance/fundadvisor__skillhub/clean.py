#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean.py — 上传前清理脚本（零依赖）
====================================
上传平台拒绝二进制文件，本脚本删除运行产生的二进制/缓存/临时产物：

  1. __pycache__/ 与 *.pyc、*.pyo        （Python 字节码缓存）
  2. data/nav_cache.db                    （净值 SQLite 缓存，可重建）
  3. data/reports/                        （运行期生成的报告 JSON）
  4. data/clients/ data/uploads/          （空运行目录）
  5. *.log / *.tmp / nul                  （日志与临时文件）

用法:
  python clean.py          # 清理并打印清单
  python clean.py --check  # 只检查是否有残留（退出码 1=有残留）

提示：日常开发建议设置 PYTHONDONTWRITEBYTECODE=1 防止生成 pyc。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# 需要删除的目录（存在即整体删除）
CLEAN_DIRS = ["__pycache__"]
# 需要清空的运行期目录（保留目录本身）
RUNTIME_DIRS = [DATA / "reports", DATA / "clients", DATA / "uploads"]
# 需要删除的文件 glob（相对 ROOT 或 DATA）
CLEAN_GLOBS = ["**/*.pyc", "**/*.pyo", "**/*.pyc.gz"]
DATA_FILE_GLOBS = ["nav_cache.db*", "*.log", "*.tmp"]
ROOT_FILE_GLOBS = ["*.log", "*.tmp", "nul"]


def _find_targets() -> list:
    targets = []
    for d in CLEAN_DIRS:
        for p in ROOT.rglob(d):
            if p.is_dir():
                targets.append(("dir", p))
    for g in CLEAN_GLOBS:
        for p in ROOT.rglob(g):
            if p.is_file():
                targets.append(("file", p))
    for g in DATA_FILE_GLOBS:
        for p in DATA.glob(g):
            if p.is_file():
                targets.append(("file", p))
    for g in ROOT_FILE_GLOBS:
        for p in ROOT.glob(g):
            if p.is_file():
                targets.append(("file", p))
    for d in RUNTIME_DIRS:
        if d.is_dir():
            for p in d.iterdir():
                if p.is_file():
                    targets.append(("file", p))
            targets.append(("dir", d))
    # 去重（同一路径可能被多个规则命中）
    seen, unique = set(), []
    for kind, p in targets:
        key = str(p)
        if key not in seen:
            seen.add(key)
            unique.append((kind, p))
    return unique


def run(verbose: bool = True) -> int:
    targets = _find_targets()
    # 先删文件、后删目录（目录删除后其内文件会失效）
    targets.sort(key=lambda t: 0 if t[0] == "file" else 1)
    removed = 0
    for kind, p in targets:
        try:
            if kind == "dir":
                _rmtree(p)
            else:
                p.unlink()
            removed += 1
            if verbose:
                rel = p.relative_to(ROOT)
                print(f"  已删除: {rel}")
        except Exception as e:
            if verbose:
                print(f"  跳过: {p.relative_to(ROOT)} ({e})")
    if verbose:
        print(f"\n清理完成: 删除 {removed} 项")
        leftover = _find_targets()
        if leftover:
            print(f"⚠️ 仍有 {len(leftover)} 项残留（可能被占用）:")
            for _, p in leftover[:10]:
                print(f"    {p.relative_to(ROOT)}")
            return 1
        print("✅ 目录干净，可上传")
    return 0


def _rmtree(p: Path) -> None:
    import shutil
    shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        leftover = _find_targets()
        for _, p in leftover:
            print(p.relative_to(ROOT))
        sys.exit(1 if leftover else 0)
    sys.exit(run())
