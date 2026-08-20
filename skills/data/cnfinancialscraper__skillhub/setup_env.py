#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cn-financial-scraper 环境安装脚本

一键搭建环境：
    python setup_env.py

功能：
    1. 创建虚拟环境 .venv（可选）
    2. pip install 依赖
    3. 验证核心模块可导入

【环境强制】运行时禁止生成 .pyc，避免污染仓库（项目根 .gitignore 已同步屏蔽二进制）
"""

import sys
sys.dont_write_bytecode = True

# 关闭 .pyc 生成（全局 -B 标志同等效果）
import os
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
REQUIREMENTS = PROJECT_DIR / "requirements.txt"


def print_header(text: str):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_step(text: str):
    print(f"\n>>> {text}")


def print_ok(text: str):
    print(f"  ✅ {text}")


def print_warn(text: str):
    print(f"  ⚠️  {text}")


def print_fail(text: str):
    print(f"  ❌ {text}")


# ─── 1. Python 版本检查 ────────────────────────────────────────────────────

def check_python_version() -> bool:
    print_step("检查 Python 版本")
    v = sys.version_info
    print(f"  当前: Python {v.major}.{v.minor}.{v.micro}")
    if v < (3, 8):
        print_fail(f"需要 Python 3.8+，当前为 {v.major}.{v.minor}")
        return False
    print_ok(f"Python {v.major}.{v.minor} 满足要求")
    return True


# ─── 2. 安装依赖 ────────────────────────────────────────────────────────────

TIER_PACKAGES = {
    "core": [],  # 纯标准库，无需 pip 安装
    "recommended": ["beautifulsoup4", "lxml", "python-docx", "openpyxl"],
    "full": None,  # None = 安装 requirements.txt 全部
}

def install_dependencies(tier: str = "core") -> bool:
    if tier == "core":
        print_step("核心模式 - 零外部依赖")
        print("  cn-financial-scraper 的核心舆情功能使用 Python 标准库")
        print("  无需安装任何 pip 包，可直接使用:")
        print("    python run_sentiment.py")
        print()
        print("  如需增强功能:")
        print("    python setup_env.py --recommended   (HTML解析 + Word/Excel导出)")
        print("    python setup_env.py --full          (全部功能)")
        return True

    if not REQUIREMENTS.exists():
        print_fail(f"未找到 {REQUIREMENTS}")
        return False

    mirrors = [
        ("https://pypi.tuna.tsinghua.edu.cn/simple", "pypi.tuna.tsinghua.edu.cn"),
        ("https://mirrors.aliyun.com/pypi/simple", "mirrors.aliyun.com"),
    ]

    if tier == "recommended":
        print_step(f"推荐模式 - 安装核心增强包")
        packages = TIER_PACKAGES["recommended"]
    else:
        print_step(f"全功能模式 - 安装全部依赖")
        packages = None  # 用 requirements.txt

    for mirror_url, host in mirrors:
        if packages:
            cmd = [sys.executable, "-m", "pip", "install"] + packages
        else:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
        cmd_full = cmd + ["-i", mirror_url, "--trusted-host", host]
        print(f"  执行: pip install {' '.join(packages) if packages else 'requirements.txt'}")
        try:
            result = subprocess.run(cmd_full, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print_ok(f"依赖安装成功 (镜像: {host})")
                return True
            else:
                print_warn(f"镜像 {host} 安装失败，尝试下一个...")
        except subprocess.TimeoutExpired:
            print_warn(f"镜像 {host} 超时")
        except Exception as e:
            print_warn(f"镜像 {host} 异常: {e}")
    print_fail("所有镜像安装失败")
    return False


# ─── 3. 核心模块导入验证 ─────────────────────────────────────────────────────

def check_core_modules() -> bool:
    print_step("验证核心模块导入")
    sys.path.insert(0, str(PROJECT_DIR / "scripts"))

    modules = [
        ("http_utils", "HTTP 基础设施"),
        ("scraper", "页面爬取器"),
        ("web_parser", "网页解析器"),
        ("institution_scraper", "机构爬虫"),
        ("scrapable_registry", "机构注册表"),
        ("news_scraper", "新闻爬虫"),
        ("announcement_scraper", "公告爬虫"),
        ("research_report_scraper", "券商研报"),
        ("comprehensive_report_scraper", "综合报告"),
        ("document_parser", "文档解析"),
        ("document_analyzer", "文档分析"),
        ("report_exporter", "报告导出"),
        ("batch_institution_crawler", "批量爬虫"),
        ("sina_scraper", "新浪财经"),
        ("cls_scraper", "财联社"),
        ("jisilu_scraper", "集思录"),
        ("exchange_scraper", "交易所"),
        ("report_stdlib_fallbacks", "标准库文档生成"),
        # v4.0 新增模块
        ("enhanced_parser", "增强文件解析"),
        ("content_compressor", "内容智能压缩"),
        ("crawl_scheduler", "定时爬取调度"),
        ("crawl_packager", "批量打包ZIP"),
        ("report_templates", "报告模板库"),
        ("financial_writer", "金融写作引擎"),
        ("research_report_generator", "研究报告生成"),
        # v4.1 新增模块
        ("overseas_scraper", "海外金融机构爬取"),
        ("translate_utils", "金融术语翻译"),
        # v4.2 新增模块
        ("browser_scraper", "浏览器自动化爬虫"),
        # v4.3 新增模块
        ("sentiment_crawler", "全网舆情爬虫"),
        ("sentiment_exporter", "舆情导出器"),
        ("sentiment_chat", "对话式NLU入口"),
        ("sentiment_keywords", "舆情关键词库"),
        # v4.4 新增数据源
        ("eastmoney_scraper", "东方财富数据爬虫"),
        ("cninfo_scraper", "巨潮资讯公告爬虫"),
        ("regulatory_scraper", "金融监管机构爬虫"),
        # v4.5 新增模块
        ("fullpage_archiver", "全页内容归档器"),
        ("search_engine", "多搜索引擎聚合"),
        ("crawl_backtester", "数据回测工具"),
        # v4.7 新增模块
        ("market_data_scraper", "市场数据爬虫"),
    ]

    all_ok = True
    for mod, desc in modules:
        try:
            __import__(mod)
            print_ok(f"{desc} ({mod})")
        except SyntaxError as e:
            print_fail(f"{desc}: SyntaxError {e}")
            all_ok = False
        except ImportError as e:
            print_warn(f"{desc}: ImportError - {e}")
        except Exception as e:
            print_warn(f"{desc}: {type(e).__name__} - {e}")

    return all_ok


# ─── 4. 可选增强检查 ────────────────────────────────────────────────────────

def check_optional():
    print_step("可选增强功能")
    for pkg, desc in [("scrapling", "动态 JS 渲染"), ("playwright", "浏览器自动化")]:
        try:
            __import__(pkg.split(".")[0])
            print_ok(f"{pkg} 已安装（{desc}可用）")
        except ImportError:
            print_warn(f"{pkg} 未安装（{desc}不可用，不影响核心功能）")


# ─── 主函数 ────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="cn-financial-scraper 环境安装")
    ap.add_argument("--recommended", action="store_true", help="安装推荐包 (HTML解析+导出)")
    ap.add_argument("--full", action="store_true", help="安装全部依赖")
    args, _ = ap.parse_known_args()

    tier = "full" if args.full else ("recommended" if args.recommended else "core")
    tier_label = {"core": "核心（零依赖）", "recommended": "推荐", "full": "全功能"}[tier]

    print_header(f"cn-financial-scraper 环境安装向导 v5.0.0 - {tier_label}")
    print(f"\n  版本: 5.0.0")
    print(f"  模式: {tier_label}")
    print(f"  目录: {PROJECT_DIR}")

    results = {}

    results["Python 版本"] = check_python_version()
    if not results["Python 版本"]:
        print_fail("Python 版本不满足要求，继续验证（结果仅供参考）")

    results["依赖安装"] = install_dependencies(tier)
    results["核心模块"] = check_core_modules()
    check_optional()

    print_header("验证结果汇总")
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {'通过' if ok else '失败'}")

    print("\n" + "=" * 60)
    all_ok = all(isinstance(v, bool) and v for v in results.values())
    if all_ok:
        print("  🎉 所有检查通过！skill 已就绪。")
        print("\n  快速开始:")
        print("    python -c \"from scripts import search_institution; print(search_institution('华夏基金'))\"")
        print("\n  MCP Server 模式:")
        print("    python mcp_server.py")
    else:
        print("  ⚠️  部分检查失败，请检查上述错误。")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
