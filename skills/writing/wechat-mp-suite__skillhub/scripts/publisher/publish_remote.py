#!/usr/bin/env python3
"""
publish_remote.py - 远程发布 Markdown 文章到微信公众号草稿箱（MCP 模式）

通过 HTTP 将文章上传到远程 MCP 服务，由远程服务执行发布流程。

用法:
  python publish_remote.py <path/to/article.md> [theme_id]

环境变量:
  WECHAT_APP_ID         微信公众号 AppID
  WECHAT_APP_SECRET     微信公众号 AppSecret
  MCP_SERVER_URL        MCP 服务地址（可选，默认: http://localhost:3000/api/mcp）

配置文件:
  wechat.env / .env    从项目目录或脚本目录自动加载
"""

import json
import os
import sys
import re
from pathlib import Path

import requests

# ─── sys.path 引导，确保可以导入 lib/ ──────────────────────────
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
sys.path.insert(0, str(_project_root))

from lib.config_loader import load_credentials, get, get_env

# ─── 颜色输出 ─────────────────────────────────────────────────
_SUPPORTS_COLOR = sys.stdout.isatty()


def _color(code: str, s: str) -> str:
    if _SUPPORTS_COLOR:
        return f"{code}{s}\x1b[0m"
    return s


def red(s: str) -> str:
    return _color("\x1b[31m", s)


def green(s: str) -> str:
    return _color("\x1b[32m", s)


def yellow(s: str) -> str:
    return _color("\x1b[33m", s)


def cyan(s: str) -> str:
    return _color("\x1b[36m", s)


# ─── MCP 服务配置 ─────────────────────────────────────────────
def get_mcp_url() -> str:
    """获取 MCP 服务地址"""
    url = get_env("MCP_SERVER_URL").strip()
    if not url:
        url = "http://localhost:3000/api/mcp"
    return url.rstrip("/")


# ─── 上传文件 ─────────────────────────────────────────────────
def upload_file(mcp_url: str, file_path: str) -> str:
    """上传文件到 MCP 服务，返回 file_id"""
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"   文件: {filename}")
    print(f"   大小: {len(content)} 字符")

    payload = {
        "content": content,
        "filename": filename,
    }

    proxies = _build_proxies()

    try:
        resp = requests.post(
            f"{mcp_url}/upload_file",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=(30, 120),
            proxies=proxies,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.Timeout:
        print(red("❌ 上传请求超时"))
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(red(f"❌ 上传请求失败: {e}"))
        sys.exit(1)

    file_id = result.get("file_id")
    error_msg = result.get("error")

    if error_msg:
        print(red(f"❌ 上传失败: {error_msg}"))
        sys.exit(1)

    if not file_id or file_id == "null":
        print(red("❌ 上传失败: 无法从响应中解析 file_id"))
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        sys.exit(1)

    return file_id


# ─── 发布文章 ─────────────────────────────────────────────────
def publish_article(mcp_url: str, file_id: str, theme_id: str,
                    app_id: str, app_secret: str) -> str:
    """调用 MCP 发布文章，返回 media_id"""
    payload = {
        "file_id": file_id,
        "theme_id": theme_id,
        "wechat_app_id": app_id,
        "wechat_app_secret": app_secret,
    }

    proxies = _build_proxies()

    try:
        resp = requests.post(
            f"{mcp_url}/publish_article",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=(30, 180),
            proxies=proxies,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.Timeout:
        print(red("❌ 发布请求超时（180秒）"))
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(red(f"❌ 发布请求失败: {e}"))
        sys.exit(1)

    media_id = result.get("media_id")
    publish_error = result.get("error")

    if publish_error:
        print(red(f"❌ 发布失败: {publish_error}"))
        print(yellow("💡 提示: 检查远程服务器 IP 是否已在微信公众号后台添加白名单"))
        sys.exit(1)

    if not media_id or media_id == "null":
        print(red("❌ 发布失败: 未知响应"))
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        sys.exit(1)

    return media_id


# ─── 代理 ────────────────────────────────────────────────────
def _build_proxies() -> dict[str, str] | None:
    """构建 requests 代理配置"""
    proxies = {}
    http_proxy = get_env("HTTP_PROXY")
    https_proxy = get_env("HTTPS_PROXY")
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy
    return proxies if proxies else None


# ─── 帮助 ────────────────────────────────────────────────────
def show_help() -> None:
    print(f"""用法: python publish_remote.py <path/to/article.md> [theme_id]
示例: python publish_remote.py ./my-post.md lapis

可用主题（theme_id）: default, lapis, phycat, ...

环境变量:
  WECHAT_APP_ID         微信公众号 AppID
  WECHAT_APP_SECRET     微信公众号 AppSecret
  MCP_SERVER_URL        MCP 服务地址（可选）""")


# ─── 主函数 ──────────────────────────────────────────────────
def main() -> None:
    args = sys.argv[1:]

    # 用法
    if not args or args[0] in ("-h", "--help"):
        show_help()
        sys.exit(0)

    file_path = args[0]
    theme_id = args[1] if len(args) > 1 else "default"

    # 检查文件
    if not os.path.exists(file_path):
        print(red(f"❌ 错误: 文件不存在: {file_path}"))
        sys.exit(1)

    # 加载凭证
    creds = load_credentials()
    app_id = creds.get("WECHAT_APP_ID", "")
    app_secret = creds.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        print(red("❌ 错误: WECHAT_APP_ID 或 WECHAT_APP_SECRET 未设置"))
        print(yellow("请在项目目录创建 .env 或 wechat.env 文件："))
        print("  WECHAT_APP_ID=your_app_id")
        print("  WECHAT_APP_SECRET=your_app_secret")
        print("")
        print(yellow("或参考 .env.example 配置。"))
        sys.exit(1)

    # MCP 服务地址
    mcp_url = get_mcp_url()
    print(cyan(f"🌐 MCP 服务: {mcp_url}"))

    # 上传文件
    print(green("🚀 上传文章到 MCP 服务..."))
    file_id = upload_file(mcp_url, file_path)
    print(green(f"✅ 文件上传成功！ID: {file_id}"))

    # 发布
    print(green("⏳ 正在发布到微信公众号草稿箱..."))
    media_id = publish_article(mcp_url, file_id, theme_id, app_id, app_secret)
    print(green(f"🎉 发布成功！Media ID: {media_id}"))
    print(yellow("📱 请前往微信公众号后台草稿箱查看："))
    print("   https://mp.weixin.qq.com/")
    print("")
    print(yellow("💡 常见问题："))
    print("  1. IP 未在白名单 → 添加到公众号后台")
    print("  2. Frontmatter 缺失 → 文件顶部添加 title + cover")
    print("  3. API 凭证错误 → 检查 .env 中的凭证")
    print("  4. 封面尺寸错误 → 需要 1080×864 像素")


if __name__ == "__main__":
    main()
