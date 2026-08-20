# install_deps.py: 运行时依赖脚本（技能运行调用）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install_deps.py — 律师助手按需依赖安装器（v4.4.2 新增，v4.10.0 授权加固）

用法：
  python scripts/install_deps.py --auto     # 智能检测：缺什么装什么（推荐，用户侧回复“安装”即触发）
  python scripts/install_deps.py --word     # Word导出
  python scripts/install_deps.py --pdf      # PDF解析
  python scripts/install_deps.py --ocr      # 图片OCR
  python scripts/install_deps.py --audio    # 语音转写
  python scripts/install_deps.py --office   # Office全家桶
  python scripts/install_deps.py --all      # 一键全装
  python scripts/install_deps.py --yes      # 跳过交互确认（须已获用户明确同意；agent 调用前必须先征得同意）

安全约束（v4.10.0 起）：
  1. 包名白名单：仅允许安装 PACKAGES 中声明的固定版本包，任何命令行传入/白名单外的包名直接拒绝；
  2. 版本锁定：每个包锁定固定版本（==），保证复测环境可复现；
  3. 安装前确认：默认逐组打印将安装的包名与版本并要求 y/N 确认；--yes 仅用于已获用户同意的自动场景；
  4. 审计日志：每次安装写入 ~/.workbuddy/logs/install_audit.log（时间/分组/包名/版本/结果），可追溯；
  5. 失败提示回滚：安装失败时给出回滚建议（pip uninstall 已装部分）。

退出码：
  0 = 全部安装成功或已安装
  1 = 部分安装失败 / 用户取消 / 白名单拒绝
"""

import argparse
import importlib.util
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

# 包名白名单 + 版本锁定（固定版本，禁止裸包名；升级须人工评估后同步更新本表与法源抽样核验台账）
PACKAGES = {
    "word":   ["python-docx==1.1.2"],
    "pdf":    ["pymupdf==1.24.9", "pdfplumber==0.11.4"],
    "ocr":    ["easyocr==1.7.2", "Pillow==10.4.0"],
    "audio":  ["websocket-client==1.8.0"],
    "office": ["python-pptx==1.0.2", "openpyxl==3.1.5", "xlrd==2.0.1"],
    "ai":     ["openai==1.40.0"],
}

# 白名单集合（install_group 断言用）：仅允许上表声明的 "包名==版本"
ALLOWED = set()
for _pkgs in PACKAGES.values():
    ALLOWED.update(_pkgs)

# 各分组检测探针：import 名 -> 分组
PROBES = {
    "word":   "docx",
    "pdf":    "fitz",
    "ocr":    "easyocr",
    "audio":  "websocket",
    "office": "pptx",
    "ai":     "openai",
}

# 审计日志位置（技能包外，避免污染提交包体）
AUDIT_LOG = os.path.join(os.path.expanduser("~"), ".workbuddy", "logs", "install_audit.log")


def audit(entry):
    """写入审计日志（时间/动作/包/结果），失败不阻断安装主流程"""
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), entry))
    except Exception as e:
        print("  ⚠️ 审计日志写入失败: %s" % e)


def check_installed(name):
    """探测指定分组是否已就绪"""
    mod = PROBES.get(name)
    if not mod:
        return False
    return importlib.util.find_spec(mod) is not None


def install_group(name, pkgs, yes=False):
    """安装单个依赖组：白名单断言 → 版本锁定 → （确认）→ 执行 → 审计"""
    # 白名单断言：命令行/配置无法引入白名单外的包
    for p in pkgs:
        if p not in ALLOWED:
            print("❌ 拒绝安装白名单外依赖: %s（仅允许 %d 个锁定包）" % (p, len(ALLOWED)))
            audit("REJECT %s (白名单外)" % p)
            return False

    print("\n📦 安装 %s 依赖: %s" % (name, " ".join(pkgs)))

    # 安装前确认（默认交互；--yes 表示已获用户同意）
    if not yes:
        try:
            ans = input("  将安装以上 %d 个锁定版本包，是否继续？[y/N]: " % len(pkgs)).strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("  ⏭️ 已取消（未安装任何包）。如需自动安装，请确认后使用 --yes。")
            audit("CANCEL %s (用户未确认)" % name)
            return False

    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + pkgs,
            capture_output=False,
            text=True,
            encoding="utf-8", errors="replace",
            timeout=300,
        )
        if r.returncode == 0:
            print("✅ %s 安装完成" % name)
            audit("OK %s %s" % (name, " ".join(pkgs)))
            return True
        print("❌ %s 安装失败 (exit %d)" % (name, r.returncode))
        audit("FAIL %s %s (exit %d)" % (name, " ".join(pkgs), r.returncode))
        print("  💡 回滚建议：pip uninstall %s（如部分已装）后重试；或换替代方式（转PDF/截图/粘贴文字）。"
              % " ".join(p.split("==")[0] for p in pkgs))
        return False
    except Exception as e:
        print("❌ %s 安装异常: %s" % (name, e))
        audit("EXC %s %s (%s)" % (name, " ".join(pkgs), e))
        return False


def main():
    ap = argparse.ArgumentParser(description="律师助手按需依赖安装器")
    ap.add_argument("--auto", action="store_true", help="智能检测：缺什么装什么（推荐）")
    ap.add_argument("--word", action="store_true", help="Word 导出依赖 (python-docx)")
    ap.add_argument("--pdf", action="store_true", help="PDF 解析依赖 (pymupdf, pdfplumber)")
    ap.add_argument("--ocr", action="store_true", help="图片 OCR 依赖 (easyocr, Pillow)")
    ap.add_argument("--audio", action="store_true", help="语音转写依赖 (websocket-client)")
    ap.add_argument("--office", action="store_true", help="Office 文档依赖 (python-pptx, openpyxl, xlrd)")
    ap.add_argument("--ai", action="store_true", help="AI 接口依赖 (openai)")
    ap.add_argument("--all", action="store_true", help="一键安装全部依赖")
    ap.add_argument("--yes", action="store_true", help="跳过交互确认（须已获用户明确同意）")
    args = ap.parse_args()

    if args.auto:
        missing = [k for k in PACKAGES if not check_installed(k)]
        if not missing:
            print("✅ 检测完成：所有功能组件均已就绪，无需安装。")
            sys.exit(0)
        print("🔍 检测到未就绪组件：%s，开始按需安装……" % "、".join(missing))
        groups = missing
    elif args.all:
        groups = list(PACKAGES.keys())
    else:
        groups = [k for k in PACKAGES if getattr(args, k, False)]

    if not groups:
        print("💡 用法示例：")
        print("  python scripts/install_deps.py --auto     # 智能检测：缺什么装什么（推荐）")
        print("  python scripts/install_deps.py --word     # Word导出")
        print("  python scripts/install_deps.py --pdf      # PDF解析")
        print("  python scripts/install_deps.py --ocr      # 图片OCR")
        print("  python scripts/install_deps.py --audio    # 语音转写")
        print("  python scripts/install_deps.py --office   # Office全家桶")
        print("  python scripts/install_deps.py --all      # 一键全装")
        print("  python scripts/install_deps.py --yes      # 跳过确认（已获用户同意）")
        print("\n💡 跑 python scripts/doctor.py --quick 看看当前缺什么。")
        sys.exit(0)

    print("=" * 50)
    print("律师助手 · 按需依赖安装（白名单 %d 个锁定包）" % len(ALLOWED))
    print("=" * 50)

    all_ok = True
    for g in groups:
        ok = install_group(g, PACKAGES[g], yes=args.yes)
        all_ok = all_ok and ok

    print()
    if all_ok:
        print("✅ 全部依赖安装完成。跑 python scripts/doctor.py --full 确认。")
        sys.exit(0)
    print("⚠️ 部分依赖未安装成功。可用替代方式（转PDF/截图/粘贴文字/导出Markdown）继续，不影响文字咨询。")
    sys.exit(1)


if __name__ == "__main__":
    main()
