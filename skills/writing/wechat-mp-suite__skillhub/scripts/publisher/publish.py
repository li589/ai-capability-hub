#!/usr/bin/env python3
""""
wechat-publisher: 发布 Markdown 到微信公众号草稿箱（纯 Python 实现）

直接调用微信公众平台草稿箱 API，不再依赖 wenyan-cli (Node.js)。

用法:
  python publish.py <markdown-file> [theme] [code_theme]

示例:
  python publish.py article.md
  python publish.py article.md lapis
  python publish.py article.md lapis solarized-light
"""

import json
import sys
import time
from pathlib import Path

import requests
import yaml

# ─── 项目路径 ──────────────────────────────────────────────
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
sys.path.insert(0, str(_project_root))

from lib.config_loader import load_credentials, get, get_env
from scripts.typeset.typeset import md_to_wechat_html

# ─── 颜色输出（跨平台） ──────────────────────────────────
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


# ─── 默认配置 ─────────────────────────────────────────────
DEFAULT_THEME = "lapis"
DEFAULT_CODE_THEME = "solarized-light"

TOKEN_CACHE_DIR = Path.home() / ".config" / "wechat-mp-suite"
TOKEN_CACHE_PATH = TOKEN_CACHE_DIR / "token.json"

WECHAT_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
WECHAT_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
WECHAT_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"


# ═══════════════════════════════════════════════════════════
#  Frontmatter 解析
# ═══════════════════════════════════════════════════════════
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 Markdown 文件中的 YAML frontmatter

    Frontmatter 由文件顶部 --- ... --- 包裹。

    Returns:
        (frontmatter_dict, body_text)
    """
    text = text.lstrip("\ufeff")  # 去除 BOM

    if not text.startswith("---"):
        return {}, text

    # 找闭合 ---
    end_idx = text.find("---", 3)
    if end_idx == -1:
        return {}, text

    yaml_str = text[3:end_idx].strip()
    body = text[end_idx + 3 :].strip()

    try:
        fm = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError as e:
        print(yellow(f"⚠️  Frontmatter 解析警告: {e}"))
        fm = {}

    if not isinstance(fm, dict):
        print(yellow("⚠️  Frontmatter 不是字典格式，跳过"))
        return {}, body

    return fm, body


# ═══════════════════════════════════════════════════════════
#  Access Token 管理（带缓存）
# ═══════════════════════════════════════════════════════════
def _load_cached_token() -> dict | None:
    """从本地缓存加载 access_token"""
    if not TOKEN_CACHE_PATH.exists():
        return None
    try:
        return json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save_token_cache(token_data: dict) -> None:
    """保存 access_token 到本地缓存"""
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    token_data["cached_at"] = time.time()
    TOKEN_CACHE_PATH.write_text(
        json.dumps(token_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_access_token(app_id: str, secret: str) -> str:
    """获取微信公众号 access_token（优先使用缓存）

    缓存文件: ~/.config/wechat-mp-suite/token.json
    提前 5 分钟过期，避免使用过期 token。
    """
    cached = _load_cached_token()
    if cached:
        token = cached.get("access_token", "")
        expires_in = cached.get("expires_in", 7200)
        cached_at = cached.get("cached_at", 0)
        remaining = expires_in - (time.time() - cached_at)
        if token and remaining > 300:  # 提前 5 分钟过期
            print(yellow(f"🔑 使用缓存的 access_token（剩余 {int(remaining)} 秒）"))
            return token

    print(yellow("🔄 请求新的 access_token..."))
    try:
        resp = requests.get(
            WECHAT_TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": app_id,
                "secret": secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}")

    data = resp.json()

    if "access_token" not in data:
        err_msg = data.get("errmsg", "未知错误")
        err_code = data.get("errcode", -1)
        raise RuntimeError(f"获取 access_token 失败 (errcode={err_code}): {err_msg}")

    _save_token_cache(data)
    print(green(f"✅ 获取成功（有效期 {data['expires_in']} 秒）"))
    return data["access_token"]


# ═══════════════════════════════════════════════════════════
#  封面图上传
# ═══════════════════════════════════════════════════════════
def upload_cover_image(access_token: str, image_path_str: str) -> str:
    """上传封面图片到微信素材库，返回 media_id

    封面要求:
      - 格式: JPG / PNG
      - 尺寸: 建议 1080×864 像素
      - 大小: 不超过 10MB
    """
    img_path = Path(image_path_str)
    if not img_path.exists():
        print(yellow(f"⚠️  封面文件不存在: {image_path_str}，跳过上传"))
        return ""

    print(yellow(f"📤 上传封面: {img_path.name}..."))

    try:
        with open(img_path, "rb") as f:
            resp = requests.post(
                WECHAT_MATERIAL_URL,
                params={"access_token": access_token, "type": "image"},
                files={"media": (img_path.name, f, "image/png")},
                timeout=30,
            )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(red(f"❌ 封面上传网络错误: {e}"))
        return ""

    data = resp.json()

    if "media_id" not in data:
        err_msg = data.get("errmsg", "未知错误")
        err_code = data.get("errcode", -1)
        hints = {
            40007: "文件格式不支持或损坏",
            40009: "图片尺寸或大小不符合要求",
            41005: "缺少 media 数据",
        }
        hint = hints.get(err_code, "")
        detail = f" — {hint}" if hint else ""
        print(red(f"❌ 封面上传失败 (errcode={err_code}): {err_msg}{detail}"))
        return ""

    print(green(f"✅ 封面上传成功 → media_id: {data['media_id']}"))
    return data["media_id"]


# ═══════════════════════════════════════════════════════════
#  创建草稿
# ═══════════════════════════════════════════════════════════
def create_draft(
    access_token: str,
    title: str,
    author: str,
    content: str,
    thumb_media_id: str = "",
    digest: str = "",
    source_url: str = "",
) -> str:
    """创建微信公众号草稿，返回 draft media_id"""
    article = {
        "title": title,
        "author": author,
        "content": content,
        "digest": digest,
        "content_source_url": source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }

    body = {"articles": [article]}

    print(yellow("📝 创建草稿..."))
    try:
        resp = requests.post(
            WECHAT_DRAFT_URL,
            params={"access_token": access_token},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}")

    data = resp.json()

    if "media_id" not in data:
        err_msg = data.get("errmsg", "未知错误")
        err_code = data.get("errcode", -1)
        raise RuntimeError(f"创建草稿失败 (errcode={err_code}): {err_msg}")

    print(green(f"✅ 草稿创建成功 → media_id: {data['media_id']}"))
    return data["media_id"]


# ═══════════════════════════════════════════════════════════
#  发布主流程
# ═══════════════════════════════════════════════════════════
def publish(file_path: str, theme: str, code_theme: str) -> None:
    """完整的 Markdown → 微信公众号草稿发布流程"""

    # ── 1. 加载凭证 ──────────────────────────────────────
    print(green("🔐 加载微信公众号凭证..."))
    creds = load_credentials()
    app_id = creds.get("WECHAT_APP_ID", "") or get_env("WECHAT_APP_ID", "")
    secret = creds.get("WECHAT_APP_SECRET", "") or get_env("WECHAT_APP_SECRET", "")

    if not app_id or not secret:
        print(red("❌ 未找到微信公众号凭证 (WECHAT_APP_ID / WECHAT_APP_SECRET)！"))
        print(yellow("请通过以下任一方式配置："))
        print()
        print("  1. 在项目根目录创建 .env 文件：")
        print("     WECHAT_APP_ID=your_app_id")
        print("     WECHAT_APP_SECRET=your_app_secret")
        print()
        print("  2. 设置系统环境变量")
        sys.exit(1)

    print(f"  APP ID: {cyan(app_id[:6] + '******')}")

    # ── 2. 读取 Markdown 文件 ────────────────────────────
    md_path = Path(file_path)
    if not md_path.exists():
        print(red(f"❌ 文件不存在: {file_path}"))
        sys.exit(1)

    print(green(f"📖 读取文件: {md_path.resolve()}"))
    md_text = md_path.read_text(encoding="utf-8")

    # ── 3. 解析 Frontmatter ──────────────────────────────
    print(yellow("📋 解析 Frontmatter..."))
    frontmatter, body = parse_frontmatter(md_text)

    title = frontmatter.get("title") or frontmatter.get("name") or md_path.stem
    author = frontmatter.get("author", "")
    cover = frontmatter.get("cover", "")
    digest = frontmatter.get("digest", frontmatter.get("description", ""))
    source_url = frontmatter.get(
        "content_source_url", frontmatter.get("url", "")
    )

    print(f"  标题:   {cyan(title)}")
    if author:
        print(f"  作者:   {cyan(author)}")
    if digest:
        print(f"  摘要:   {cyan(digest[:60])}{'…' if len(digest) > 60 else ''}")
    if cover:
        print(f"  封面:   {cyan(cover)}")
    if source_url:
        print(f"  原文:   {cyan(source_url)}")

    # ── 4. Markdown → WeChat HTML ────────────────────────
    print(yellow(f"🎨 排版（主题: {theme}, 代码高亮: {code_theme}）..."))
    html_content = md_to_wechat_html(body, theme_id=theme, code_theme_id=code_theme)

    if not html_content.strip():
        print(red("❌ 排版后内容为空"))
        sys.exit(1)

    print(green(f"✅ 排版完成（{len(html_content)} 字符）"))

    # ── 5. 获取 access_token ─────────────────────────────
    try:
        access_token = get_access_token(app_id, secret)
    except RuntimeError as e:
        print(red(f"❌ {e}"))
        print(yellow("💡 尝试删除缓存后重试："))
        print(f"     rm {TOKEN_CACHE_PATH}")
        sys.exit(1)

    # ── 6. 上传封面图（可选） ────────────────────────────
    thumb_media_id = ""
    if cover:
        cover_path = Path(cover)
        if not cover_path.is_absolute():
            cover_path = md_path.parent / cover
        thumb_media_id = upload_cover_image(access_token, str(cover_path))

    # ── 7. 创建草稿 ──────────────────────────────────────
    print(green("📤 发布到微信公众号草稿箱..."))
    try:
        draft_media_id = create_draft(
            access_token=access_token,
            title=title,
            author=author,
            content=html_content,
            thumb_media_id=thumb_media_id,
            digest=digest,
            source_url=source_url,
        )
        print()
        print(green(f"✅ 发布成功！"))
        print(yellow("📱 请前往微信公众号后台草稿箱查看："))
        print("  https://mp.weixin.qq.com/")
        print(f"  草稿 media_id: {draft_media_id}")
    except RuntimeError as e:
        print()
        print(red(f"❌ 发布失败: {e}"))
        print(yellow("💡 常见问题："))
        print("  1. IP 未在白名单 → 到公众号后台添加本机 IP")
        print("  2. access_token 过期 → 删除缓存后重试")
        print(f"     缓存文件: {TOKEN_CACHE_PATH}")
        print("  3. API 凭证错误 → 检查 .env 中的凭证")
        print("  4. 封面尺寸/格式错误 → 需要 1080×864 像素 JPG/PNG")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════
#  帮助信息
# ═══════════════════════════════════════════════════════════
def show_help() -> None:
    print("""Usage: python publish.py <markdown-file> [theme] [code_theme]

Examples:
  python publish.py article.md
  python publish.py article.md lapis
  python publish.py article.md lapis solarized-light

Available themes:
  default, lapis, forest, ocean, sunset, noir, phycat

Available code themes:
  atom-one-dark, atom-one-light, dracula, github-dark, github,
  monokai, solarized-dark, solarized-light, xcode

Frontmatter (文件顶部):
  ---
  title: 文章标题
  author: 作者名
  cover: 封面图片路径
  digest: 文章摘要（可选）
  content_source_url: 原文链接（可选）
  ---""")


# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════
def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        show_help()
        sys.exit(0)

    file_path = args[0]
    theme = args[1] if len(args) > 1 else DEFAULT_THEME
    code_theme = args[2] if len(args) > 2 else DEFAULT_CODE_THEME

    publish(file_path, theme, code_theme)


if __name__ == "__main__":
    main()
