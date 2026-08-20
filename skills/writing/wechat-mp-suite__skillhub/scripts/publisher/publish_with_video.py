#!/usr/bin/env python3
"""
publish_with_video.py - 发布含视频的 Markdown 文章到微信公众号草稿箱（纯 Python）

流程：
1. 解析 Markdown 中的 frontmatter
2. 扫描正文中的 mp4/视频引用
3. 上传每个 mp4 到微信永久素材库，获取 media_id/vid
4. 替换 mp4 引用为微信视频标签
5. 用 typeset 将 Markdown 转为微信公众号 HTML
6. 上传封面图（可选）
7. 创建草稿（draft/add）

用法：
  python publish_with_video.py <markdown-file> [theme] [code_theme]

凭证来源（按优先级）：
  .env / wechat.env 文件 → 系统环境变量 → load_credentials()
"""

import json
import re
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
#  Multipart 上传（视频/图片）
# ═══════════════════════════════════════════════════════════
def _upload_file_multipart(
    url: str,
    file_path: str,
    field_name: str = "media",
    extra_fields: dict | None = None,
    timeout: int = 200,
) -> dict:
    """Multipart 文件上传到微信 API"""
    filename = Path(file_path).name
    with open(file_path, "rb") as f:
        # 自动猜测 MIME 类型
        ext = Path(file_path).suffix.lower()
        mime_map = {
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            ".flv": "video/x-flv",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        mime = mime_map.get(ext, "application/octet-stream")
        files = {field_name: (filename, f, mime)}
        data = extra_fields or {}
        try:
            resp = requests.post(url, files=files, data=data, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise RuntimeError(f"上传超时: {file_path}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"上传失败 ({file_path}): {e}")


# ═══════════════════════════════════════════════════════════
#  封面图上传
# ═══════════════════════════════════════════════════════════
def upload_cover_image(access_token: str, image_path_str: str) -> str:
    """上传封面图片到微信素材库，返回 media_id"""
    img_path = Path(image_path_str)
    if not img_path.exists():
        print(yellow(f"⚠️  封面文件不存在: {image_path_str}，跳过上传"))
        return ""

    print(yellow(f"📤 上传封面: {img_path.name}..."))

    url = f"{WECHAT_MATERIAL_URL}?access_token={access_token}&type=image"
    try:
        data = _upload_file_multipart(url, str(img_path), timeout=30)
    except RuntimeError as e:
        print(red(f"❌ 封面上传错误: {e}"))
        return ""

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
#  视频上传
# ═══════════════════════════════════════════════════════════
def upload_video(access_token: str, video_path: str, title: str = "视频") -> dict:
    """
    上传视频到微信永久素材库
    返回 {media_id, vid, cover_url}
    """
    url = f"{WECHAT_MATERIAL_URL}?access_token={access_token}&type=video"
    description = json.dumps({"title": title, "introduction": title}, ensure_ascii=False)

    data = _upload_file_multipart(
        url,
        video_path,
        field_name="media",
        extra_fields={"description": description},
        timeout=200,
    )

    if "media_id" not in data:
        raise RuntimeError(f"视频上传失败 ({video_path}): {json.dumps(data, ensure_ascii=False)}")

    media_id = data["media_id"]

    # 获取 vid 和 cover_url（通过 batchget_material 查询刚上传的视频）
    list_url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={access_token}"
    try:
        resp = requests.post(list_url, json={"type": "video", "offset": 0, "count": 5}, timeout=15)
        resp.raise_for_status()
        list_data = resp.json()
    except requests.RequestException:
        list_data = {}

    vid = ""
    cover_url = ""
    for item in list_data.get("item", []):
        if item.get("media_id") == media_id:
            vid = item.get("vid", "")
            cover_url = item.get("cover_url", "")
            break

    return {"media_id": media_id, "vid": vid, "cover_url": cover_url}


# ═══════════════════════════════════════════════════════════
#  视频处理
# ═══════════════════════════════════════════════════════════
def find_mp4_refs(content: str, article_dir: str) -> list[dict]:
    """在 Markdown 内容中查找所有 mp4 引用"""
    pattern = re.compile(r'!?\[([^\]]*)\]\(([^)]+\.mp4)\)', re.IGNORECASE)
    refs = []
    for m in pattern.finditer(content):
        alt = m.group(1)
        rel = m.group(2)
        abs_path = os_path_norm(os.path.join(article_dir, rel))
        refs.append({"alt": alt, "rel": rel, "abs_path": abs_path})
    return refs


def os_path_norm(p: str) -> str:
    """跨平台路径规范化"""
    return str(Path(p).resolve())


def is_real_video(file_path: str) -> bool:
    """
    检查文件是否为真实视频（通过读取文件头部 magic bytes 判断）
    纯 Python 实现，不依赖 file 命令
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(12)

        if len(header) < 12:
            return False

        # MP4: ftyp signature at offset 4
        if header[4:8] == b"ftyp":
            return True
        # AVI: RIFF....AVI
        if header[0:4] == b"RIFF" and header[8:11] == b"AVI":
            return True
        # WebM/MKV: 0x1A45DFA3
        if header[0:4] == b"\x1A\x45\xDF\xA3":
            return True
        # FLV: FLV
        if header[0:3] == b"FLV":
            return True

        # 检查是否为文本/HTML（非视频）
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample = f.read(200)
            if re.search(r"<html|<!DOCTYPE|<HTML", sample, re.IGNORECASE):
                return False
        except (UnicodeDecodeError, OSError):
            pass  # 二进制文件，已通过上面检测

        return True  # 给不认识的格式默认通过
    except OSError:
        return False


def build_video_tag(vid: str, cover_url: str = "") -> str:
    """构建微信公众号视频可用的 HTML 标签"""
    if vid:
        # 使用 iframe 方式（推荐，有 vid 时）
        src = (
            f"https://mp.weixin.qq.com/mp/readtemplate"
            f"?t=pages/video_player_tmpl&action=mpvideo&scene=0&vid={vid}"
        )
        cover_attr = f' data-cover="{cover_url}"' if cover_url else ""
        return (
            f'<iframe class="video_iframe rich_pages wxw-img" '
            f'data-src="{src}" '
            f'data-vidtype="2" '
            f'data-mpvid="{vid}"{cover_attr} '
            f'allowfullscreen="" frameborder="0" scrolling="no" '
            f'style="width: 677px; height: 508px;" '
            f'src="{src}"></iframe>'
        )
    else:
        # 无 vid 时使用 mp-video 标签
        return ''

# ═══════════════════════════════════════════════════════════
#  草稿创建
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
#  处理视频并构建 HTML
# ═══════════════════════════════════════════════════════════
def process_videos_and_build_html(
    md_body: str,
    article_dir: str,
    access_token: str,
    theme: str,
    code_theme: str,
) -> str:
    """
    扫描正文中的视频引用，上传视频到微信素材库，
    替换视频引用为 HTML 标签，然后转 Markdown 为 HTML。

    Returns:
        最终的 HTML 字符串
    """
    refs = find_mp4_refs(md_body, article_dir)

    if not refs:
        print(green("✅ 文章中没有视频引用"))
        return md_to_wechat_html(md_body, theme_id=theme, code_theme_id=code_theme)

    print(yellow(f"🎬 发现 {len(refs)} 个视频引用，开始处理..."))

    # 替换映射：先收集所有替换，避免处理过程中修改 md_body 影响正则匹配
    replacements = []

    for ref in refs:
        alt = ref["alt"]
        rel = ref["rel"]
        abs_path = ref["abs_path"]

        if not Path(abs_path).exists():
            print(yellow(f"⚠️  视频文件不存在: {abs_path}，跳过"))
            replacement_text = f"[视频: {alt}（文件不存在）]"
            replacements.append((f"![{alt}]({rel})", replacement_text))
            replacements.append((f"[{alt}]({rel})", replacement_text))
            continue

        if not is_real_video(abs_path):
            print(yellow(f"⚠️  {rel} 不是真实视频文件（可能是 HTML 预览页），替换为文字"))
            replacement_text = f"[视频预览: {alt}]"
            replacements.append((f"![{alt}]({rel})", replacement_text))
            replacements.append((f"[{alt}]({rel})", replacement_text))
            continue

        file_size_mb = Path(abs_path).stat().st_size / 1024 / 1024
        print(f"🎬 上传视频: {rel} ({file_size_mb:.1f} MB)...")

        try:
            result = upload_video(
                access_token, abs_path,
                title=alt or Path(abs_path).stem,
            )
            media_id = result["media_id"]
            vid = result.get("vid", "")
            cover_url = result.get("cover_url", "")

            video_tag = build_video_tag(vid, cover_url)
            if video_tag:
                replacement_html = f"\n{video_tag}\n"
                print(f"   ✅ 上传成功: media_id={media_id[:30]}... vid={vid}")
            else:
                # 没有 vid，用文字提示用户
                replacement_html = f"\n<p>📹 视频已上传（media_id: {media_id}），请在公众号后台添加视频组件</p>\n"
                print(f"   ⚠️  上传成功但未获取到 vid，使用文字提示")

            replacements.append((f"![{alt}]({rel})", replacement_html))
            replacements.append((f"[{alt}]({rel})", replacement_html))
        except RuntimeError as e:
            print(f"   ❌ 上传失败: {e}")
            # fallback：尝试引用同名的 png 截图
            png_ref = rel.replace(".mp4", ".png")
            replace_text = f"![{alt}]({png_ref})" if f"![{alt}]({rel})" in md_body else f"[{alt}]({png_ref})"
            replacements.append((f"![{alt}]({rel})", replace_text))
            replacements.append((f"[{alt}]({rel})", replace_text))

    # 执行替换
    for old, new in replacements:
        md_body = md_body.replace(old, new)

    # Markdown → HTML
    print(yellow(f"🎨 排版（主题: {theme}, 代码高亮: {code_theme}）..."))
    html_content = md_to_wechat_html(md_body, theme_id=theme, code_theme_id=code_theme)
    print(green(f"✅ 排版完成（{len(html_content)} 字符）"))

    return html_content


# ═══════════════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════════════
def publish(file_path: str, theme: str, code_theme: str) -> None:
    """完整的 Markdown → 微信公众号草稿（含视频）发布流程"""

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
    article_dir = str(md_path.parent)

    # ── 3. 解析 Frontmatter ──────────────────────────────
    print(yellow("📋 解析 Frontmatter..."))
    frontmatter, body = parse_frontmatter(md_text)

    title = frontmatter.get("title") or frontmatter.get("name") or md_path.stem
    author = frontmatter.get("author", "")
    cover = frontmatter.get("cover", "")
    digest = frontmatter.get("digest", frontmatter.get("description", ""))
    source_url = frontmatter.get("content_source_url", frontmatter.get("url", ""))

    print(f"  标题:   {cyan(title)}")
    if author:
        print(f"  作者:   {cyan(author)}")
    if digest:
        print(f"  摘要:   {cyan(digest[:60])}{'…' if len(digest) > 60 else ''}")
    if cover:
        print(f"  封面:   {cyan(cover)}")
    if source_url:
        print(f"  原文:   {cyan(source_url)}")

    # ── 4. 获取 access_token ─────────────────────────────
    try:
        access_token = get_access_token(app_id, secret)
    except RuntimeError as e:
        print(red(f"❌ {e}"))
        print(yellow("💡 尝试删除缓存后重试："))
        print(f"     rm {TOKEN_CACHE_PATH}")
        sys.exit(1)

    # ── 5. 处理视频引用并排版 ──────────────────────────
    print(yellow("🔍 扫描视频引用..."))
    html_content = process_videos_and_build_html(
        body, article_dir, access_token, theme, code_theme,
    )

    if not html_content.strip():
        print(red("❌ 排版后内容为空"))
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
        print(green("✅ 发布成功！"))
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
    print(r"""publish_with_video.py - 发布含视频的 Markdown 文章到微信公众号草稿箱

用法:
  python publish_with_video.py <markdown-file> [theme] [code_theme]

示例:
  python publish_with_video.py article.md
  python publish_with_video.py article.md lapis
  python publish_with_video.py article.md lapis solarized-light

可用主题:
  default, lapis, forest, ocean, sunset, noir, phycat

可用代码高亮主题:
  atom-one-dark, atom-one-light, dracula, github-dark, github,
  monokai, solarized-dark, solarized-light, xcode

Frontmatter (文件顶部):
  ---
  title: 文章标题
  author: 作者名
  cover: 封面图片路径
  digest: 文章摘要（可选）
  content_source_url: 原文链接（可选）
  ---

视频引用:
  在 Markdown 正文中使用 ![描述](video.mp4) 或 [描述](video.mp4)
  脚本会自动上传 mp4 到微信永久素材，并在 HTML 中插入视频标签。

凭证（按优先级）:
  1. 项目根目录的 .env 或 wechat.env 文件
  2. 系统环境变量 WECHAT_APP_ID / WECHAT_APP_SECRET""")


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
    try:
        main()
    except (RuntimeError, ValueError) as e:
        print(red(f"❌ 错误: {e}"))
        sys.exit(1)
    except KeyboardInterrupt:
        print(yellow("\n⚠️  用户中断"))
        sys.exit(1)
