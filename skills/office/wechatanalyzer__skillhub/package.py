#!/usr/bin/env python3
"""
wechat-analyzer 上传友好打包脚本（v2.2.0）

用途：把 wechat-analyzer 目录打包成 .zip 供上传/分享用，
      自动排除以下禁止/不需要的文件：
      - .pyc / __pycache__ / .pytest_cache
      - .gitignore / LICENSE(.md/.txt) / .env / *.local
      - .docx / .doc / .pdf / .pptx / .xlsx / .xls (测试导出)
      - .bat / .cmd / .ps1 / .exe (启动脚本)
      - .log / .tmp / .bak
      - data/ 下的运行时数据（uploads / reports / sessions / scrape_cache）
      - .claude/ 本地配置
      - *.sqlite 数据库

用法：
    python package.py                     # 打包到 dist/wechat-analyzer.zip
    python package.py --output my.zip     # 自定义输出
    python package.py --include-gitignore # 包含 .gitignore（默认排除）
    python package.py --include-data      # 包含 data/ 运行时数据
    python package.py --list              # 只列出将要打包的文件，不实际打包
"""

import os
import sys
import zipfile
import argparse
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_ROOT / "dist" / "wechat-analyzer.zip"


# ============== 排除规则 ==============
EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".cache",
    ".git",
    ".claude",
    ".vscode",
    ".idea",
    "venv",
    ".venv",
    "env",
    "htmlcov",
    "dist",
    "build",
    "*.egg-info",
    # 运行时数据（包含用户聊天记录，不应打包）
    "uploads",
    "reports",
    "sessions",
    "scrape_cache",
    "sentiment_snapshots",
    "sentiment_exports",
    "vector_store",
    "models",  # embedding 模型
    "screenshots",
    "charts",
    "generated_reports",
}

EXCLUDED_FILES = {
    ".gitignore",
    ".env",
    ".env.local",
    ".env.*.local",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "api_keys.json",
    "config.json.bak",
}

EXCLUDED_PATTERNS = [
    "*.pyc", "*.pyo", "*.pyd",
    "*.py[cod]",
    "*.docx", "*.doc", "*.pdf", "*.pptx", "*.ppt", "*.xlsx", "*.xls",
    "*.bat", "*.cmd", "*.ps1", "*.exe", "*.sh",
    "*.log", "*.tmp", "*.bak", "*.swp", "*.swo",
    "*.sqlite", "*.db", "*.sqlite3",
    "Thumbs.db", "desktop.ini", ".DS_Store",
    "*.egg", "*.egg-info",
    "*.png", "*.jpg", "*.jpeg", "*.gif",  # 排除图片（聊天截图等）
]


# ============== 辅助 ==============
def _should_exclude(path: Path, include_gitignore: bool, include_data: bool) -> tuple:
    """判断路径是否应排除，返回 (是否排除, 原因)"""
    rel = path.relative_to(PROJECT_ROOT)
    parts = rel.parts

    # 1. 目录排除
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True, f"目录 {part}"
        if part.startswith(".") and part not in (".",):
            # 隐藏目录（除了根的 . 之外）
            if part != "." and part != "..":
                return True, f"隐藏目录 {part}"

    # 2. data/ 子目录特殊处理
    if include_data is False and parts and parts[0] == "data":
        # 默认排除 data/ 整个目录
        return True, "运行时数据 data/"

    # 3. 文件排除
    name = path.name

    # 3.1 .gitignore（已重命名为 gitignore_rules.txt，但仍需排除）
    if name in (".gitignore", "gitignore_rules.txt") and not include_gitignore:
        return True, "gitignore"

    # 3.2 黑名单
    if name in EXCLUDED_FILES:
        return True, name

    # 3.3 通配符
    import fnmatch
    for pattern in EXCLUDED_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return True, pattern

    return False, ""


def collect_files(include_gitignore: bool, include_data: bool):
    """遍历目录，收集要打包的文件路径（带排除原因）"""
    files = []
    excluded_count = 0
    excluded_summary: dict = {}

    for path in sorted(PROJECT_ROOT.rglob("*")):
        if path == PROJECT_ROOT:
            continue
        # 跳过 dist/ 自身
        if "dist" in path.parts:
            continue
        if path.is_dir():
            continue

        excluded, reason = _should_exclude(path, include_gitignore, include_data)
        if excluded:
            excluded_count += 1
            excluded_summary[reason] = excluded_summary.get(reason, 0) + 1
            continue

        rel = path.relative_to(PROJECT_ROOT)
        files.append((path, rel))

    return files, excluded_count, excluded_summary


# ============== 入口 ==============
def main():
    parser = argparse.ArgumentParser(description="wechat-analyzer 上传友好打包")
    parser.add_argument("--output", "-o", type=str, help=f"输出 zip 路径（默认 {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)}）")
    parser.add_argument("--include-gitignore", action="store_true", help="包含 .gitignore（默认排除）")
    parser.add_argument("--include-data", action="store_true", help="包含 data/ 运行时数据（默认排除）")
    parser.add_argument("--list", "-l", action="store_true", help="只列出将要打包的文件，不实际打包")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    print("=" * 70)
    print(" wechat-analyzer 上传友好打包")
    print("=" * 70)
    print(f"项目根: {PROJECT_ROOT}")
    print(f"输出:   {output_path}")
    print(f"包含 .gitignore: {args.include_gitignore}")
    print(f"包含 data/:      {args.include_data}")
    print()

    files, excluded_count, excluded_summary = collect_files(
        args.include_gitignore, args.include_data
    )

    # 打印将要打包的文件
    print(f"[收集] {len(files)} 个文件（已排除 {excluded_count} 个）")
    print()
    print("── 将要打包 ──")
    for _, rel in files:
        print(f"  + {rel}")
    print()

    print("── 已排除的类别 ──")
    for reason, count in sorted(excluded_summary.items(), key=lambda x: -x[1]):
        print(f"  - {reason:30s} ×{count}")
    print()

    if args.list:
        print("💡 --list 模式：未实际打包")
        return 0

    # 实际打包
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for abs_path, rel_path in files:
            zf.write(abs_path, rel_path)

    # 二次校验
    with zipfile.ZipFile(output_path, "r") as zf:
        bad_files = []
        for name in zf.namelist():
            low = name.lower()
            if low.endswith((".pyc", ".pyo", ".docx", ".doc", ".pdf",
                             ".pptx", ".xlsx", ".xls", ".exe", ".bat", ".ps1")):
                bad_files.append(name)
            if ".gitignore" in name or "gitignore_rules" in name or "license" in low.split("/")[-1]:
                if not args.include_gitignore:
                    bad_files.append(name)

    size_mb = output_path.stat().st_size / 1024 / 1024

    print("=" * 70)
    print(f" ✅ 打包完成: {output_path}")
    print(f"    文件数: {len(files)}")
    print(f"    大小:   {size_mb:.2f} MB")
    if bad_files:
        print(f"    ⚠️  警告：zip 内仍有 {len(bad_files)} 个可疑文件:")
        for f in bad_files[:10]:
            print(f"        - {f}")
    else:
        print(f"    ✅ 二次校验通过：不含 .pyc / .docx / .gitignore 等")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
