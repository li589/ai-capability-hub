#!/usr/bin/env python3
"""
wechat-analyzer 缓存清理脚本（v2.6.0）

场景：跑测试 / 导入模块 / 运行分析后会在根目录、scripts/、tests/、core/、analyzers/、
      data/ 等位置留 `__pycache__/`、`.pyc`、`.db` 等文件，导致上传/打包时被拒。

用法：
    python clean.py             # 清理 .pyc + __pycache__ + .pytest_cache + .db
    python clean.py --keep-pyc  # 不删除 .pyc（调试时用）
    python clean.py --keep-db   # 不删除 .db（保留聊天历史时用）
    python clean.py --deep      # 额外清理 .cache / .coverage / htmlcov
    python clean.py --check     # 只检查残留（不删除；退出码 1=有残留，上传前必跑）
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def clean_pyc(verbose: bool = True) -> tuple:
    """清理 .pyc 缓存文件和 __pycache__ 目录"""
    removed_files = 0
    removed_dirs = 0

    # 1. 删除 .pyc 文件
    for pyc in PROJECT_ROOT.rglob("*.pyc"):
        try:
            pyc.unlink()
            removed_files += 1
            if verbose:
                print(f"  [文件] {pyc.relative_to(PROJECT_ROOT)}")
        except OSError as e:
            print(f"  [失败] {pyc}: {e}", file=sys.stderr)

    # 2. 删除空的 __pycache__ 目录
    for cache_dir in sorted(PROJECT_ROOT.rglob("__pycache__"), reverse=True):
        try:
            # 只删空目录
            if cache_dir.is_dir() and not any(cache_dir.iterdir()):
                cache_dir.rmdir()
                removed_dirs += 1
                if verbose:
                    print(f"  [目录] {cache_dir.relative_to(PROJECT_ROOT)}")
        except OSError as e:
            print(f"  [失败] {cache_dir}: {e}", file=sys.stderr)

    # 3. 类似 pyo / pyd
    for ext in ("*.pyo", "*.pyd"):
        for f in PROJECT_ROOT.rglob(ext):
            try:
                f.unlink()
                removed_files += 1
            except OSError:
                pass

    return removed_files, removed_dirs


def clean_pytest(verbose: bool = True) -> int:
    """清理 .pytest_cache 目录"""
    count = 0
    for pytest_dir in PROJECT_ROOT.rglob(".pytest_cache"):
        try:
            shutil.rmtree(pytest_dir)
            count += 1
            if verbose:
                print(f"  [pytest 缓存] {pytest_dir.relative_to(PROJECT_ROOT)}")
        except OSError as e:
            print(f"  [失败] {pytest_dir}: {e}", file=sys.stderr)
    return count


def clean_deep(verbose: bool = True) -> int:
    """深度清理：测试覆盖率、HTML 覆盖报告"""
    count = 0
    for pattern in (".cache", ".coverage", "htmlcov"):
        for path in PROJECT_ROOT.rglob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                count += 1
                if verbose:
                    print(f"  [深度清理] {path.relative_to(PROJECT_ROOT)}")
            except OSError as e:
                print(f"  [失败] {path}: {e}", file=sys.stderr)
    return count


def clean_db(verbose: bool = True) -> int:
    """清理 SQLite 数据库及 WAL/SHM 残留（运行时生成，二进制，上传被拒）。

    注意：默认数据库已改到系统 tempdir（见 core/data_paths.py），
    此函数兜底清理任何残留在 skill 包内的 .db 文件。
    """
    patterns = ("*.db", "*.db-wal", "*.db-shm", "*.sqlite", "*.sqlite3")
    count = 0
    for pattern in patterns:
        for f in PROJECT_ROOT.rglob(pattern):
            try:
                f.unlink()
                count += 1
                if verbose:
                    print(f"  [数据库] {f.relative_to(PROJECT_ROOT)}")
            except OSError as e:
                print(f"  [失败] {f}: {e}", file=sys.stderr)
    return count


def find_leftovers() -> list:
    """扫描会被上传平台拒绝的二进制残留（.pyc/.pyo/.pyd/__pycache__/.pytest_cache/.db）"""
    leftovers = []
    for pattern in ("*.pyc", "*.pyo", "*.pyd",
                    "*.db", "*.db-wal", "*.db-shm", "*.sqlite", "*.sqlite3"):
        leftovers.extend(f for f in PROJECT_ROOT.rglob(pattern) if f.is_file())
    leftovers.extend(d for d in PROJECT_ROOT.rglob("__pycache__") if d.is_dir())
    leftovers.extend(d for d in PROJECT_ROOT.rglob(".pytest_cache") if d.is_dir())
    return sorted(set(leftovers))


def main():
    parser = argparse.ArgumentParser(description="wechat-analyzer 缓存清理")
    parser.add_argument("--keep-pyc", action="store_true", help="保留 .pyc 文件")
    parser.add_argument("--keep-db", action="store_true", help="保留 .db 数据库文件")
    parser.add_argument("--deep", action="store_true", help="深度清理（覆盖率等）")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    parser.add_argument("--check", action="store_true",
                        help="只检查是否有二进制残留（不删除），退出码 1=有残留")
    args = parser.parse_args()

    if args.check:
        leftovers = find_leftovers()
        for f in leftovers:
            print(f.relative_to(PROJECT_ROOT))
        if leftovers:
            print(f"\n⚠️ 发现 {len(leftovers)} 项二进制残留，上传前请先运行 python clean.py")
            sys.exit(1)
        print("✅ 无二进制残留，可上传")
        sys.exit(0)

    verbose = not args.quiet

    if verbose:
        print("=" * 60)
        print(" wechat-analyzer 缓存清理")
        print("=" * 60)

    if not args.keep_pyc:
        files, dirs = clean_pyc(verbose=verbose)
        if verbose:
            print(f"\n[.pyc / __pycache__] 删除 {files} 文件, {dirs} 目录")
    else:
        if verbose:
            print("\n[跳过] --keep-pyc 已指定, 保留 .pyc")

    pytest_count = clean_pytest(verbose=verbose)
    if verbose:
        print(f"\n[.pytest_cache] 删除 {pytest_count} 目录")

    if not args.keep_db:
        db_count = clean_db(verbose=verbose)
        if verbose:
            print(f"\n[.db / .sqlite] 删除 {db_count} 文件")
    else:
        if verbose:
            print("\n[跳过] --keep-db 已指定, 保留 .db")

    if args.deep:
        deep_count = clean_deep(verbose=verbose)
        if verbose:
            print(f"\n[深度清理] 处理 {deep_count} 项")

    if verbose:
        print("\n" + "=" * 60)
        print(" ✅ 清理完成")
        print("=" * 60)
        print()
        print("💡 提示：跑测试时设置环境变量可避免生成 .pyc:")
        print("   Windows: set PYTHONDONTWRITEBYTECODE=1")
        print("   Linux:   export PYTHONDONTWRITEBYTECODE=1")
        print()


if __name__ == "__main__":
    main()
