#!/usr/bin/env python3
"""
setup_config.py - 网络安全威胁情报日报 · 配置向导
首次运行时引导用户完成邮箱配置，支持 AgentMail 和 SMTP 两种发送方式
同时提供 RSS 数据源的新增 / 删除 / 列出管理功能
"""

import json
import os
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 配置文件路径（存储在技能目录下，避免覆盖用户全局配置）
# ──────────────────────────────────────────────────────────────
SKILL_CONFIG_DIR = Path(os.path.expanduser("~/.workbuddy/skills/cyber-threat-intel-daily-shared"))
CONFIG_FILE = SKILL_CONFIG_DIR / "config.json"

# ──────────────────────────────────────────────────────────────
# 内置默认 RSS 源（13 个）
# ──────────────────────────────────────────────────────────────
DEFAULT_RSS_SOURCES = {
    "安全圈": "https://wechat2rss.xlab.app/feed/d568d6fca93d750898111f09cc3c551e7a62f7ab.xml",
    "看雪论坛": "https://wechat2rss.xlab.app/feed/0e026637254d450ae84c59f87d4e4fb4616651ca.xml",
    "FreeBuf": "https://www.freebuf.com/feed",
    "嗅学安全": "https://wechat2rss.xlab.app/feed/b15a925f83a4b108b957f8dd0e8030b6caa7da5e.xml",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "Threatpost": "https://threatpost.com/feed/",
    "Dark Reading": "https://www.darkreading.com/rss_simple.asp",
    "Schneier on Security": "https://www.schneier.com/feed/atom/",
    "CISA": "https://www.cisa.gov/news-events/cybersecurity-advisories/rss",
    "Ars Technica Security": "https://arstechnica.com/security/feed/",
    "The Register": "https://www.theregister.com/security/headlines.atom",
    "Wired Security": "https://www.wired.com/feed/category/security/latest/rss",
    "Microsoft Security": "https://www.microsoft.com/en-us/security/blog/feed/",
}


def load_config() -> dict:
    """读取配置文件，不存在则返回空配置骨架"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "email_method": None,          # "agentmail" | "smtp"
        "agentmail": {},               # agentmail 配置
        "smtp": {},                    # smtp 配置
        "recipient_email": "",         # 收件人邮箱
        "custom_rss_sources": {},      # 用户自定义增加的 RSS 源
        "disabled_rss_sources": [],    # 用户禁用的默认 RSS 源（名称列表）
    }


def save_config(cfg: dict) -> None:
    """保存配置到文件"""
    SKILL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 配置已保存至: {CONFIG_FILE}")


def is_configured(cfg: dict) -> bool:
    """检查是否已完成基本配置"""
    method = cfg.get("email_method")
    if not method:
        return False
    if method == "agentmail":
        return bool(cfg.get("agentmail", {}).get("api_key")) and bool(cfg.get("agentmail", {}).get("inbox_id"))
    if method == "smtp":
        return bool(cfg.get("smtp", {}).get("host")) and bool(cfg.get("smtp", {}).get("username"))
    return False


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       🔴  网络安全威胁情报日报  · 配置向导                        ║
║       Cyber Threat Intel Daily — Setup Wizard               ║
╚══════════════════════════════════════════════════════════════╝
""")


def setup_agentmail(cfg: dict) -> dict:
    """配置 AgentMail 发送方式"""
    print("\n📧 AgentMail 配置")
    print("  AgentMail 是为 AI Agent 设计的轻量邮件服务。")
    print("  官网 / 注册：https://agentmail.to")
    print()

    api_key = input("  请输入 AgentMail API Key: ").strip()
    inbox_id = input("  请输入 Inbox ID（即发件邮箱地址，如 foo@agentmail.to）: ").strip()

    cfg["email_method"] = "agentmail"
    cfg["agentmail"] = {
        "api_key": api_key,
        "inbox_id": inbox_id,
    }
    return cfg


def setup_smtp(cfg: dict) -> dict:
    """配置 SMTP 发送方式"""
    print("\n📧 SMTP 配置")
    print("  支持 Gmail、Outlook、企业邮箱等任何标准 SMTP 服务。")
    print()

    host = input("  SMTP 服务器地址（如 smtp.gmail.com）: ").strip()
    port_str = input("  SMTP 端口（TLS 推荐 587，SSL 推荐 465）[默认 587]: ").strip()
    port = int(port_str) if port_str.isdigit() else 587
    use_tls = input("  使用 TLS 加密？[Y/n]: ").strip().lower() != "n"
    username = input("  发件人邮箱地址: ").strip()
    password = input("  邮箱密码（授权码）: ").strip()
    sender_name = input("  发件人显示名称（如 CTI 情报中心）[可留空]: ").strip()

    cfg["email_method"] = "smtp"
    cfg["smtp"] = {
        "host": host,
        "port": port,
        "use_tls": use_tls,
        "username": username,
        "password": password,
        "sender_name": sender_name or "CTI 情报中心",
    }
    return cfg


def setup_email(cfg: dict) -> dict:
    """邮箱配置主流程"""
    print_banner()
    print("首次使用前，请完成以下配置。\n")
    print("【选择邮件发送方式】")
    print("  1. AgentMail（推荐，专为 AI Agent 设计，注册简单）")
    print("  2. SMTP（支持 Gmail / Outlook / 企业邮箱等）")
    print()

    choice = ""
    while choice not in ("1", "2"):
        choice = input("  请输入选项编号 [1/2]: ").strip()

    if choice == "1":
        cfg = setup_agentmail(cfg)
    else:
        cfg = setup_smtp(cfg)

    print()
    recipient = input("📬 收件人邮箱地址（接收日报的邮箱）: ").strip()
    cfg["recipient_email"] = recipient

    print("\n✅ 邮件配置完成！")
    return cfg


def list_rss_sources(cfg: dict) -> None:
    """列出当前全部 RSS 数据源（内置 + 自定义）"""
    disabled = set(cfg.get("disabled_rss_sources", []))
    custom = cfg.get("custom_rss_sources", {})

    print("\n📡 当前 RSS 数据源列表")
    print("─" * 60)
    print("\n【内置源】")
    for i, (name, url) in enumerate(DEFAULT_RSS_SOURCES.items(), 1):
        status = "❌ 已禁用" if name in disabled else "✅ 已启用"
        print(f"  {i:2}. [{status}] {name}")
        print(f"       {url}")

    print(f"\n【自定义源】（共 {len(custom)} 个）")
    if custom:
        for i, (name, url) in enumerate(custom.items(), 1):
            print(f"  {i:2}. ✅ {name}")
            print(f"       {url}")
    else:
        print("  （尚未添加自定义源）")

    total_active = len([n for n in DEFAULT_RSS_SOURCES if n not in disabled]) + len(custom)
    print(f"\n  共 {total_active} 个活跃数据源\n")


def add_rss_source(cfg: dict) -> dict:
    """新增自定义 RSS 源"""
    print("\n➕ 新增 RSS 数据源")
    print()
    name = input("  数据源名称（如 安全牛、SecurityWeek 等）: ").strip()
    if not name:
        print("  ❌ 名称不能为空")
        return cfg

    if name in DEFAULT_RSS_SOURCES:
        print(f"  ⚠️  '{name}' 是内置数据源名称，建议使用不同名称以避免混淆")
        confirm = input("  是否继续？[y/N]: ").strip().lower()
        if confirm != "y":
            return cfg

    url = input("  RSS Feed URL: ").strip()
    if not url.startswith("http"):
        print("  ❌ URL 格式不正确，请以 http:// 或 https:// 开头")
        return cfg

    if "custom_rss_sources" not in cfg:
        cfg["custom_rss_sources"] = {}

    cfg["custom_rss_sources"][name] = url
    print(f"\n  ✅ 已添加: {name}")
    print(f"     {url}")
    return cfg


def remove_rss_source(cfg: dict) -> dict:
    """删除自定义 RSS 源，或禁用内置源"""
    print("\n➖ 删除 / 禁用数据源")
    print("\n  1. 删除自定义源")
    print("  2. 禁用内置源")
    print("  3. 重新启用已禁用的内置源")
    print()
    choice = input("  请输入选项 [1/2/3]: ").strip()

    if choice == "1":
        custom = cfg.get("custom_rss_sources", {})
        if not custom:
            print("  （没有自定义源可删除）")
            return cfg
        print("\n  当前自定义源：")
        names = list(custom.keys())
        for i, name in enumerate(names, 1):
            print(f"  {i}. {name}")
        sel = input("  请输入要删除的序号: ").strip()
        try:
            idx = int(sel) - 1
            name = names[idx]
            del cfg["custom_rss_sources"][name]
            print(f"  ✅ 已删除: {name}")
        except (ValueError, IndexError):
            print("  ❌ 无效选项")

    elif choice == "2":
        print("\n  内置源：")
        disabled = set(cfg.get("disabled_rss_sources", []))
        active = [n for n in DEFAULT_RSS_SOURCES if n not in disabled]
        for i, name in enumerate(active, 1):
            print(f"  {i}. {name}")
        sel = input("  请输入要禁用的序号: ").strip()
        try:
            idx = int(sel) - 1
            name = active[idx]
            if "disabled_rss_sources" not in cfg:
                cfg["disabled_rss_sources"] = []
            cfg["disabled_rss_sources"].append(name)
            print(f"  ✅ 已禁用: {name}（可随时重新启用）")
        except (ValueError, IndexError):
            print("  ❌ 无效选项")

    elif choice == "3":
        disabled = cfg.get("disabled_rss_sources", [])
        if not disabled:
            print("  （没有已禁用的内置源）")
            return cfg
        print("\n  已禁用的内置源：")
        for i, name in enumerate(disabled, 1):
            print(f"  {i}. {name}")
        sel = input("  请输入要重新启用的序号: ").strip()
        try:
            idx = int(sel) - 1
            name = disabled[idx]
            cfg["disabled_rss_sources"].remove(name)
            print(f"  ✅ 已重新启用: {name}")
        except (ValueError, IndexError):
            print("  ❌ 无效选项")

    return cfg


def reconfigure_email(cfg: dict) -> dict:
    """重新配置邮箱"""
    print("\n⚙️  重新配置邮件发送")
    return setup_email(cfg)


def show_current_config(cfg: dict) -> None:
    """显示当前配置摘要（脱敏）"""
    print("\n📋 当前配置摘要")
    print("─" * 50)
    method = cfg.get("email_method")
    if not method:
        print("  邮件配置: ❌ 尚未配置")
    elif method == "agentmail":
        am = cfg.get("agentmail", {})
        key = am.get("api_key", "")
        masked_key = key[:6] + "****" + key[-4:] if len(key) > 10 else "****"
        print(f"  发送方式: AgentMail")
        print(f"  API Key : {masked_key}")
        print(f"  发件箱  : {am.get('inbox_id', '(未设置)')}")
    elif method == "smtp":
        sm = cfg.get("smtp", {})
        print(f"  发送方式: SMTP")
        print(f"  服务器  : {sm.get('host', '(未设置)')}:{sm.get('port', 587)}")
        print(f"  发件人  : {sm.get('username', '(未设置)')}")

    print(f"  收件人  : {cfg.get('recipient_email', '(未设置)')}")
    custom = cfg.get("custom_rss_sources", {})
    disabled = cfg.get("disabled_rss_sources", [])
    total_active = len([n for n in DEFAULT_RSS_SOURCES if n not in disabled]) + len(custom)
    print(f"  RSS 源  : {total_active} 个活跃（其中 {len(custom)} 个自定义，{len(disabled)} 个已禁用）")
    print()


def interactive_menu():
    """交互式配置菜单（当直接运行时使用）"""
    cfg = load_config()

    if not is_configured(cfg):
        print_banner()
        print("⚠️  检测到尚未完成配置，请先完成以下设置：\n")
        cfg = setup_email(cfg)
        save_config(cfg)

    while True:
        print("\n" + "─" * 50)
        print("🛠️  配置管理菜单")
        print("─" * 50)
        show_current_config(cfg)
        print("  1. 查看 RSS 数据源列表")
        print("  2. 新增自定义 RSS 源")
        print("  3. 删除 / 禁用数据源")
        print("  4. 重新配置邮箱")
        print("  5. 保存并退出")
        print("  6. 退出（不保存）")
        print()
        choice = input("请输入选项: ").strip()

        if choice == "1":
            list_rss_sources(cfg)
        elif choice == "2":
            cfg = add_rss_source(cfg)
        elif choice == "3":
            cfg = remove_rss_source(cfg)
        elif choice == "4":
            cfg = reconfigure_email(cfg)
        elif choice == "5":
            save_config(cfg)
            print("👋 配置已保存，退出。")
            break
        elif choice == "6":
            print("👋 退出（未保存更改）")
            break
        else:
            print("  ❌ 无效选项，请重试")


# ──────────────────────────────────────────────────────────────
# 供其他脚本调用的 API
# ──────────────────────────────────────────────────────────────

def get_active_rss_sources() -> dict:
    """返回当前有效的 RSS 源字典（内置 + 自定义，去除已禁用）"""
    cfg = load_config()
    disabled = set(cfg.get("disabled_rss_sources", []))
    custom = cfg.get("custom_rss_sources", {})

    sources = {}
    for name, url in DEFAULT_RSS_SOURCES.items():
        if name not in disabled:
            sources[name] = url
    sources.update(custom)
    return sources


def get_email_config() -> dict:
    """返回邮件配置（含完整凭据），供发送脚本使用"""
    cfg = load_config()
    return cfg


def check_and_prompt_setup() -> bool:
    """
    检查配置是否完整。
    若不完整，打印提示信息（而非强制交互），返回 False。
    调用方可据此决定是否中止。
    """
    cfg = load_config()
    if is_configured(cfg):
        return True

    print("""
╔══════════════════════════════════════════════════════════════╗
║  ⚠️   首次使用：请先完成邮箱配置                                  ║
╚══════════════════════════════════════════════════════════════╝

在生成和发送情报日报之前，需要配置一次发件邮箱。

请运行以下命令完成配置：

    python3 ~/.workbuddy/skills/cyber-threat-intel-daily-shared/scripts/setup_config.py

支持以下两种发送方式：
  ① AgentMail（推荐）— 专为 AI Agent 设计，注册简单
     注册地址：https://agentmail.to
  ② SMTP — 支持 Gmail / Outlook / 企业邮箱等标准邮件服务

配置完成后，重新执行日报生成即可。
""")
    return False


if __name__ == "__main__":
    interactive_menu()
