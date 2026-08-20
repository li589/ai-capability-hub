# -*- coding: utf-8 -*-
"""
cn-financial-scraper 一键舆情爬取工具 v4.3

用法：
  方式1（交互式）: python run_sentiment.py
  方式2（命令行）: python run_sentiment.py "贵州茅台最近7天的舆情"
"""
import sys
import os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


def check_env():
    issues = []
    if sys.version_info < (3, 8):
        issues.append(f"Python 版本过低: {sys.version}，需要 3.8+")
    missing = []
    for mod, desc in [
        ("http_utils", "HTTP 基础"),
        ("scraper", "基础爬虫"),
        ("sentiment_crawler", "舆情爬虫引擎"),
        ("sentiment_chat", "对话入口"),
    ]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(desc)
    if missing:
        mod_names = ", ".join(missing)
        issues.append(f"缺少核心模块: {mod_names}")
        issues.append("请先运行: python setup_env.py")
    if issues:
        print("=" * 50)
        print(" 环境检测发现问题:")
        for i in issues:
            print(f"   {i}")
        print("=" * 50)
        return False
    return True


def show_banner():
    print()
    print("  cn-financial-scraper 中国金融舆情爬虫 v5.0.0")
    print("  " + "-" * 46)
    print()


def run_interactive():
    show_banner()
    print("请输入你想爬取的内容，例如：")
    print('  "贵州茅台最近7天的舆情"')
    print('  "工银瑞信基金最近3天的负面新闻"')
    print('  "哪些媒体可用？"')
    print('  "帮助" 查看完整指南')
    print('  输入 quit 退出')
    print()

    from sentiment_chat import chat_handle

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q", "退出"):
            print("再见！")
            break

        print()
        result = chat_handle(user_input)
        print(result.get("reply", "无法处理该请求"))
        print()


def main():
    if not check_env():
        ans = input("是否现在运行 setup_env.py 安装依赖? (y/n): ").strip().lower()
        if ans in ("y", "yes"):
            setup_path = Path(__file__).resolve().parent / "setup_env.py"
            if setup_path.exists():
                os.system(f'"{sys.executable}" "{setup_path}"')
                print()
                print("安装完成，请重新运行本脚本。")
            else:
                print("未找到 setup_env.py")
        sys.exit(1)

    from sentiment_chat import chat_handle

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        text_clean = text.replace("--export", "").strip()
        show_banner()
        print(f"正在处理: {text_clean}")
        print()
        result = chat_handle(text_clean)
        print(result.get("reply", "无法处理该请求"))

        if "--export" in text and result.get("output"):
            from sentiment_exporter import export as export_sentiment
            export_sentiment(result["output"], fmt="all")
        return

    run_interactive()


if __name__ == "__main__":
    main()
