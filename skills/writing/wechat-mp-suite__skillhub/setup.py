#!/usr/bin/env python3
"""
wechat-mp-suite 一键初始化向导

检测环境 + 安装依赖 + 配置凭证 → 就绪

用法:
    python setup.py              # 交互式向导
    python setup.py --check-only # 仅检测，不安装
    python setup.py --skip-deps  # 跳过 pip install
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Windows GBK 终端兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
ENV_FILE = PROJECT_ROOT / ".env"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"

# ── 预生成 .env.example ──
ENV_EXAMPLE_CONTENT = """# wechat-mp-suite 凭证配置
# 复制此文件重命名为 .env 后填写

# 微信公众号凭证（发布功能需要）
# 获取: 微信公众平台 → 设置与开发 → 基本配置
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...

# 搜狗微信搜索 Cookie（搜索功能需要）
# 获取: 浏览器打开 weixin.sogou.com → F12 → Network → 复制 Cookie
SOGOU_COOKIE=

# 远程 MCP 发布服务器（可选）
MCP_SERVER_URL=

# 网络代理（可选）
SEARCH_PROXY=
"""

CREDENTIAL_TEMPLATE = {
    "WECHAT_APP_ID":         {"desc": "公众号 AppID",        "required_for": "发布",   "sensitive": False},
    "WECHAT_APP_SECRET":     {"desc": "公众号 AppSecret",    "required_for": "发布",   "sensitive": True},
    "SOGOU_COOKIE":          {"desc": "搜狗 Cookie",         "required_for": "搜索",   "sensitive": True},
    "MCP_SERVER_URL":        {"desc": "远程 MCP 服务器 URL",  "required_for": "远程发布 (可选)", "sensitive": False},
    "SEARCH_PROXY":          {"desc": "网络代理地址",         "required_for": "搜索 (可选)",     "sensitive": False},
}


def header(text: str, width: int = 46):
    print(f"\n{'─' * width}")
    print(f"  {text}")
    print(f"{'─' * width}")


def success(msg: str):
    print(f"  ✅ {msg}")


def warn(msg: str):
    print(f"  ⚠️  {msg}")


def fail(msg: str):
    print(f"  ❌ {msg}")


def ask(prompt: str, default: str = "") -> str:
    """交互式提问，按回车跳过"""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    try:
        val = input(display).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default


def check_python() -> bool:
    print("  🔍 Python 版本 ...", end=" ")
    v = sys.version_info
    if v >= (3, 12):
        print(f"✅ {v.major}.{v.minor}.{v.micro}")
        return True
    elif v >= (3, 9):
        print(f"⚠️  {v.major}.{v.minor}.{v.micro} (建议 ≥3.12)")
        return True
    else:
        print(f"❌ {v.major}.{v.minor}.{v.micro} (需要 ≥3.9)")
        return False


def install_deps() -> bool:
    """pip install -r requirements.txt"""
    if not REQUIREMENTS.exists():
        fail("requirements.txt 不存在")
        return False

    print("  📦 安装 Python 依赖 ...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            success("依赖安装完成")
            return True
        else:
            fail(f"安装失败: {result.stderr.splitlines()[-1] if result.stderr else ''}")
            return False
    except subprocess.TimeoutExpired:
        fail("安装超时，请检查网络后重试")
        return False


def ensure_env_example():
    if not ENV_EXAMPLE.exists():
        ENV_EXAMPLE.write_text(ENV_EXAMPLE_CONTENT, encoding="utf-8")
        success(".env.example 已创建")


def configure_credentials():
    """交互式引导用户填写凭证"""
    if not ENV_EXAMPLE.exists():
        ensure_env_example()

    print(f"\n  📝 当前 .env 状态: {'存在' if ENV_FILE.exists() else '尚未创建'}")

    existing = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            existing[k.strip()] = v.strip().strip('"').strip("'")

    while True:
        print(f"\n  ┌─ 选择要配置的凭证 ─────────────")
        print(f"  │ 1. 公众号凭证 (AppID + Secret)")
        print(f"  │ 2. 搜狗 Cookie")
        print(f"  │ 3. 远程 MCP URL / 代理")
        print(f"  │ 4. 全部配置")
        print(f"  │ 5. 跳过，保持现有 .env")
        print(f"  └{'─' * 32}")

        choice = ask("  选项", "5")
        if choice == "5":
            break

        keys_to_ask = []
        if choice == "1":
            keys_to_ask = ["WECHAT_APP_ID", "WECHAT_APP_SECRET"]
        elif choice == "2":
            keys_to_ask = ["SOGOU_COOKIE"]
        elif choice == "3":
            keys_to_ask = ["MCP_SERVER_URL", "SEARCH_PROXY"]
        elif choice == "4":
            keys_to_ask = list(CREDENTIAL_TEMPLATE.keys())
        else:
            continue

        for key in keys_to_ask:
            info = CREDENTIAL_TEMPLATE[key]
            current = existing.get(key, "")
            display = ""
            if current:
                if info["sensitive"]:
                    display = f"****{current[-4:]}" if len(current) > 4 else "****"
                else:
                    display = current
            hint = f" ({info['required_for']}, 当前: {display})" if display else f" ({info['required_for']})"
            val = ask(f"  {info['desc']}{hint}", current)
            if val:
                existing[key] = val
            elif not current:
                existing.pop(key, None)

        if ENV_FILE.exists():
            print(f"\n  已更新，再选 5 保存退出，或继续配置其他凭证")
        else:
            print(f"  按回车继续，选 5 保存退出")

    # 写入
    lines = []
    for k, v in existing.items():
        lines.append(f"{k}={v}")

    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print()
    if existing:
        filled = [k for k, v in existing.items() if v and v not in ("wx...", "")]
        success(f".env 已保存 ({len(filled)}/{len(existing)} 项已填写)")
    else:
        warn(".env 已创建，但尚未填写任何凭证")


def show_next_steps():
    print(f"\n{'═' * 46}")
    print(f"  🎉 初始化完成！")

    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

    spider_ok = True
    search_ok = "SOGOU_COOKIE" in env and env["SOGOU_COOKIE"]
    publish_ok = "WECHAT_APP_ID" in env and "WECHAT_APP_SECRET" in env

    modules = []
    modules.append("🐛 爬虫 / 排版 (无凭证, 开箱即用)")
    if search_ok:
        modules.append("🔍 搜索 (Cookie 已配置)")
    else:
        modules.append("🔍 搜索 (需配置 SOGOU_COOKIE)")
    if publish_ok:
        modules.append("📤 发布 (凭证已配置)")
    else:
        modules.append("📤 发布 (需配置 WECHAT_APP_ID + SECRET)")

    print(f"{'─' * 46}")
    for m in modules:
        print(f"  {m}")

    print(f"{'─' * 46}")
    print(f"\n  快速上手:")
    print(f"    python scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx")
    print(f"    python check.py                                查看环境状态")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="wechat-mp-suite 一键初始化")
    parser.add_argument("--check-only", action="store_true", help="仅检测，不安装/配置")
    parser.add_argument("--skip-deps", action="store_true", help="跳过 pip install")
    args = parser.parse_args()

    print("\n🚀 wechat-mp-suite 初始化向导")
    print(f"   项目: {PROJECT_ROOT}")

    # ── 步骤 1: Python 检测 ──
    header("步骤 1/4 — Python 环境")
    if not check_python():
        print("\n  请先安装 Python 3.12+ (https://python.org)")
        sys.exit(1)

    if not args.check_only and not args.skip_deps:
        install_deps()
    elif args.skip_deps:
        print("  ⏭️  跳过依赖安装 (--skip-deps)")

    # ── 步骤 2: 配置文件 ──
    header("步骤 2/4 — 配置文件")
    if (PROJECT_ROOT / "config.yaml").exists():
        success("config.yaml 存在")
    else:
        fail("config.yaml 缺失")
    ensure_env_example()

    # ── 步骤 3: 运行 check.py ──
    header("步骤 3/4 — 环境检测")
    import check
    checker = check.Checker()
    checker.check_python()
    checker.check_pip_packages()
    checker.check_config_yaml()
    checker.check_network()
    checker.check_output_dir()
    checker.check_module_files()

    # ── 步骤 4: 凭证配置 ──
    if not args.check_only:
        header("步骤 4/4 — 凭证配置")
        configure_credentials()
    else:
        header("步骤 4/4 — 跳过 (--check-only)")

    show_next_steps()


if __name__ == "__main__":
    main()
