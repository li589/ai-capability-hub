#!/usr/bin/env python3
"""
微信公众号文章下载器 — URL → Markdown + 图片

用法:
    python download.py <URL> [--output 目录] [--no-image] [--help]

功能:
    - 提取标题、作者、时间、正文
    - 下载图片到 images/ 子目录
    - 输出 Markdown（含 YAML frontmatter） + HTML + metadata.json
    - 3 次重试 + 进度显示
"""

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# 确保能导入项目根目录的 lib/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from lib.config_loader import get, get_env, load_credentials

# ── User-Agent 随机池（20 个，与 fetcher.py 一致）───────────
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/123.0.0.0 Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/122.0.0.0 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Mi 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
]

def get_random_user_agent() -> str:
    """从 20 个 UA 池中随机返回一个"""
    return random.choice(USER_AGENTS)

HEADERS = {
    'User-Agent': get_random_user_agent(),
    'Referer': 'https://mp.weixin.qq.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
# 从 config.yaml 读取重试参数（默认 3 次，指数退避 [1, 3, 5]）
MAX_RETRIES = get('spider.max_image_retries', 3) or 3
RETRY_DELAYS = [1, 3, 5]  # 秒 (指数退避)

BAR_WIDTH = 20


# ── 工具函数 ─────────────────────────────────────────────────

def sanitize_filename(name: str, max_len: int = 100) -> str:
    """去除文件名中的非法字符，限制长度"""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:max_len]


def get_ext_from_url(url: str) -> str:
    """从图片 URL 推断扩展名"""
    try:
        parsed = urlparse(url)
        # check query param wx_fmt
        query = parsed.query
        match = re.search(r'wx_fmt=(\w+)', query)
        if match:
            ext = match.group(1)
            if ext:
                return '.' + ext.lstrip('.')
        # path extension
        _, ext = os.path.splitext(parsed.path)
        if ext and len(ext) <= 5:
            return ext
    except Exception:
        pass
    return '.jpg'


def fetch_url(url: str, timeout: int = 30) -> requests.Response:
    """带重试的 HTTP GET 请求"""
    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                status_part = f"HTTP {e.response.status_code}" if hasattr(e, 'response') and e.response is not None else str(e)
                print(f"  ⚠️  请求失败（第{attempt}次/共{MAX_RETRIES}次）: {status_part}，{delay}s 后重试...")
                time.sleep(delay)
    raise last_exception  # type: ignore[misc]


def download_file(url: str, file_path: str) -> bool:
    """下载文件到本地路径，带重试"""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Referer': 'https://mp.weixin.qq.com/',
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=30, stream=True)
            resp.raise_for_status()
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                print(f"\r  ⚠️  下载失败（第{attempt}次/共{MAX_RETRIES}次）: {str(e)[:60]}，{delay}s 后重试...")
                time.sleep(delay)
    return False


def format_progress(done: int, total: int, bar_width: int = BAR_WIDTH) -> str:
    """生成进度条文本，如 |████████░░░░░░|  60%"""
    if total == 0:
        return "|" + "█" * bar_width + "| 100%"
    filled = int(bar_width * done / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    pct = int(100 * done / total)
    return f"|{bar}| {pct:3d}%"


# ── HTML → Markdown 转换 ─────────────────────────────────────

def html_to_markdown(html: str) -> str:
    """将 HTML 正文转换为 Markdown 文本"""
    md = html
    # 移除 script / style
    md = re.sub(r'<script[\s\S]*?</script>', '', md, flags=re.IGNORECASE)
    md = re.sub(r'<style[\s\S]*?</style>', '', md, flags=re.IGNORECASE)

    # 标题
    md = re.sub(r'<h1[^>]*>([\s\S]*?)</h1>', r'# \1\n\n', md, flags=re.IGNORECASE)
    md = re.sub(r'<h2[^>]*>([\s\S]*?)</h2>', r'## \1\n\n', md, flags=re.IGNORECASE)
    md = re.sub(r'<h3[^>]*>([\s\S]*?)</h3>', r'### \1\n\n', md, flags=re.IGNORECASE)
    md = re.sub(r'<h4[^>]*>([\s\S]*?)</h4>', r'#### \1\n\n', md, flags=re.IGNORECASE)

    # 加粗 / 斜体
    md = re.sub(r'<(?:strong|b)[^>]*>([\s\S]*?)</(?:strong|b)>', r'**\1**', md, flags=re.IGNORECASE)
    md = re.sub(r'<(?:em|i)[^>]*>([\s\S]*?)</(?:em|i)>', r'*\1*', md, flags=re.IGNORECASE)

    # 图片 — 保留原始 URL，后续会被替换为本地路径
    md = re.sub(
        r'<img[^>]*?(?:data-src|src)="([^"]*)"[^>]*>',
        r'\n![image](\1)\n',
        md,
        flags=re.IGNORECASE,
    )

    # 链接
    md = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>',
        r'[\2](\1)',
        md,
        flags=re.IGNORECASE,
    )

    # 换行 / 段落
    md = re.sub(r'<br\s*/?>', '\n', md, flags=re.IGNORECASE)
    md = re.sub(r'</p>', '\n\n', md, flags=re.IGNORECASE)
    md = re.sub(r'<p[^>]*>', '', md, flags=re.IGNORECASE)
    md = re.sub(r'</div>', '\n', md, flags=re.IGNORECASE)
    md = re.sub(r'<div[^>]*>', '', md, flags=re.IGNORECASE)

    # 列表
    md = re.sub(r'<li[^>]*>([\s\S]*?)</li>', r'- \1\n', md, flags=re.IGNORECASE)
    md = re.sub(r'</?[uo]l[^>]*>', '\n', md, flags=re.IGNORECASE)

    # 引用
    def _blockquote_replacer(match: re.Match) -> str:
        content = match.group(1)
        lines = content.split('\n')
        quoted = '\n'.join('> ' + l for l in lines)
        return quoted + '\n\n'

    md = re.sub(
        r'<blockquote[^>]*>([\s\S]*?)</blockquote>',
        _blockquote_replacer,
        md,
        flags=re.IGNORECASE,
    )

    # 代码
    md = re.sub(r'<code[^>]*>([\s\S]*?)</code>', r'`\1`', md, flags=re.IGNORECASE)
    md = re.sub(r'<pre[^>]*>([\s\S]*?)</pre>', r'```\n\1\n```\n\n', md, flags=re.IGNORECASE)

    # 水平线
    md = re.sub(r'<hr[^>]*>', '\n---\n\n', md, flags=re.IGNORECASE)

    # 移除剩余标签
    md = re.sub(r'<[^>]+>', '', md)

    # HTML 实体
    md = md.replace('&nbsp;', ' ')
    md = md.replace('&amp;', '&')
    md = md.replace('&lt;', '<')
    md = md.replace('&gt;', '>')
    md = md.replace('&quot;', '"')
    md = md.replace('&#39;', "'")

    # 合并多余换行
    md = re.sub(r'\n{3,}', '\n\n', md)

    return md.strip()


# ── 文章提取 ─────────────────────────────────────────────────

def fetch_article(url: str) -> str:
    """抓取文章页面 HTML"""
    print("📡 正在请求文章页面...")
    resp = fetch_url(url)
    resp.encoding = resp.apparent_encoding
    return resp.text


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """提取文章元数据"""
    # 标题
    title = ''
    for sel in ['#activity-name', '.rich_media_title']:
        tag = soup.select_one(sel)
        if tag:
            t = tag.get_text(strip=True)
            if t:
                title = t
                break
    if not title:
        meta = soup.find('meta', property='og:title')
        if meta:
            title = meta.get('content', '')
    if not title:
        title = soup.title.get_text(strip=True) if soup.title else '未命名文章'

    # 作者
    author = ''
    for sel in ['#js_name', '.rich_media_meta_nickname']:
        tag = soup.select_one(sel)
        if tag:
            a = tag.get_text(strip=True)
            if a:
                author = a
                break

    # 发布时间
    publish_time = ''
    for sel in ['#publish_time', '.rich_media_meta_date']:
        tag = soup.select_one(sel)
        if tag:
            t = tag.get_text(strip=True)
            if t:
                publish_time = t
                break

    # 摘要
    digest = ''
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        digest = meta_desc.get('content', '')

    return {
        'title': title,
        'author': author,
        'publish_time': publish_time,
        'digest': digest,
    }


def extract_content_html(soup: BeautifulSoup) -> str:
    """提取文章正文 HTML"""
    content_div = soup.select_one('#js_content') or soup.select_one('.rich_media_content')
    if content_div:
        return str(content_div)
    return ''


def extract_image_urls(content_html: str) -> list:
    """从正文 HTML 中提取所有图片 URL"""
    soup = BeautifulSoup(content_html, 'lxml')
    urls = []
    for img in soup.find_all('img'):
        src = img.get('data-src') or img.get('src') or ''
        if src and not src.startswith('data:') and 'icon' not in src and 'loading' not in src:
            urls.append(src)
    return urls


# ── 主流程 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog='download.py',
        description='微信公众号文章下载器 — URL → Markdown + 图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python download.py "https://mp.weixin.qq.com/s/xxxxx"\n'
            '  python download.py "https://mp.weixin.qq.com/s/xxxxx" --output ./articles\n'
            '  python download.py "https://mp.weixin.qq.com/s/xxxxx" --no-image\n'
        ),
    )
    parser.add_argument('url', help='微信公众号文章 URL（以 http 开头）')
    parser.add_argument(
        '--output', '-o',
        default='',
        help='输出目录（默认: ./output/<文章标题>/）',
    )
    parser.add_argument(
        '--no-image',
        action='store_true',
        help='跳过图片下载',
    )
    args = parser.parse_args()

    url = args.url
    if not url.startswith('http'):
        print('❌ 请提供以 http 开头的有效 URL')
        sys.exit(1)

    print('🐱 微信公众号文章下载器')
    print(f'📎 URL: {url}\n')

    # ── 1. 抓取页面 ──
    try:
        html = fetch_article(url)
    except Exception as e:
        print(f'❌ 页面抓取失败: {e}')
        sys.exit(1)

    soup = BeautifulSoup(html, 'lxml')

    # ── 2. 提取元数据 ──
    print('📋 提取文章信息...')
    meta = extract_metadata(soup, url)
    print(f'  📰 标题: {meta["title"]}')
    print(f'  ✍️  作者: {meta["author"]}')
    print(f'  📅 时间: {meta["publish_time"]}')

    if not meta['title'] or meta['title'] == '未命名文章':
        print('⚠️  未能提取到有效标题，文章可能已删除或需要登录')

    # ── 3. 提取正文 ──
    content_html = extract_content_html(soup)
    if not content_html:
        print('❌ 未找到文章正文（#js_content / .rich_media_content），文章可能已删除或需要登录')
        # 仍保存元数据
    else:
        print(f'  📄 正文长度: {len(content_html)} 字符')

    # ── 4. 创建输出目录 ──
    safe_title = sanitize_filename(meta['title'])
    if args.output:
        article_dir = Path(args.output) / safe_title
    else:
        article_dir = Path('output') / safe_title

    images_dir = article_dir / 'images'
    article_dir.mkdir(parents=True, exist_ok=True)

    # ── 5. 下载图片 ──
    url_to_local = {}  # 原始 URL → 本地相对路径

    if not args.no_image and content_html:
        print('\n🖼️  下载配图...')
        image_urls = extract_image_urls(content_html)
        # 去重且保留首次出现顺序
        seen = set()
        unique_urls = []
        for img_url in image_urls:
            if img_url not in seen:
                seen.add(img_url)
                unique_urls.append(img_url)

        total = len(unique_urls)
        print(f'  发现 {total} 张图片（去重后）')

        for idx, img_url in enumerate(unique_urls, 1):
            full_url = img_url
            if full_url.startswith('//'):
                full_url = 'https:' + full_url

            ext = get_ext_from_url(full_url)
            filename = f'{idx}{ext}'
            file_path = images_dir / filename
            relative_path = f'images/{filename}'

            # 进度
            progress = format_progress(idx - 1, total)
            print(f'  ⬇️  {progress} [{idx}/{total}] {filename}...', end='', flush=True)

            ok = download_file(full_url, str(file_path))
            if ok:
                url_to_local[full_url] = relative_path
                print(' ✅')
            else:
                print(' ❌')
    elif args.no_image:
        print('\n🖼️  跳过图片下载 (--no-image)')
    else:
        print('\n🖼️  无正文内容，跳过图片下载')

    # ── 6. 生成 Markdown ──
    print('\n📝 生成 Markdown...')

    # 构建 frontmatter
    frontmatter = {
        'title': meta['title'],
        'author': meta['author'],
        'publish_time': meta['publish_time'],
        'url': url,
        'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    if meta['digest']:
        frontmatter['digest'] = meta['digest']

    yaml_lines = ['---']
    for k, v in frontmatter.items():
        yaml_lines.append(f'{k}: {v}')
    yaml_lines.append('---')
    yaml_lines.append('')

    # 正文
    body = f'# {meta["title"]}\n\n'
    body += f'> **作者**: {meta["author"]}  \n'
    body += f'> **时间**: {meta["publish_time"]}  \n'
    if meta['digest']:
        body += f'> **摘要**: {meta["digest"]}  \n'
    body += f'> **原文**: [{url}]({url})\n'
    body += '\n---\n\n'

    if content_html:
        md_content = html_to_markdown(content_html)

        # 替换图片 URL 为本地路径
        for orig_url, local_path in url_to_local.items():
            # 处理 data-src 和 src 两种引用
            md_content = md_content.replace(f'({orig_url})', f'({local_path})')
            # 也处理 protocol-relative URL
            if orig_url.startswith('https:'):
                rel_url = orig_url.replace('https:', '')
                md_content = md_content.replace(f'({rel_url})', f'({local_path})')

        body += md_content

    markdown = '\n'.join(yaml_lines) + '\n' + body

    md_path = article_dir / 'article.md'
    md_path.write_text(markdown, encoding='utf-8')
    md_size = round(md_path.stat().st_size / 1024, 1)
    print(f'  📄 article.md ({md_size} KB)')

    # ── 7. 保存 HTML ──
    html_template = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{meta["title"]}</title>
<style>
  body {{ max-width: 800px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.8; color: #333; }}
  img {{ max-width: 100%; height: auto; }}
  .meta {{ color: #999; margin-bottom: 20px; font-size: 14px; }}
</style>
</head>
<body>
<h1>{meta["title"]}</h1>
<div class="meta">{meta["author"]} · {meta["publish_time"]}</div>
{content_html}
</body>
</html>'''

    html_path = article_dir / 'article.html'
    html_path.write_text(html_template, encoding='utf-8')
    html_size = round(html_path.stat().st_size / 1024, 1)
    print(f'  📄 article.html ({html_size} KB)')

    # ── 8. 保存 metadata.json ──
    meta_path = article_dir / 'metadata.json'
    meta_json = {
        **meta,
        'url': url,
        'downloaded_at': datetime.now().isoformat(),
        'images_count': len(url_to_local),
    }
    meta_path.write_text(json.dumps(meta_json, ensure_ascii=False, indent=2), encoding='utf-8')

    # ── 结果 ──
    image_files = list(images_dir.glob('*')) if images_dir.exists() else []
    print(f'\n✅ 下载完成！')
    print(f'📂 输出目录: {article_dir.resolve()}')
    print(f'  📄 article.md     ({md_size} KB)')
    print(f'  📄 article.html   ({html_size} KB)')
    print(f'  📄 metadata.json')
    print(f'  🖼️   {len(image_files)} 张图片')

    # 返回路径供外部调用
    print(f'\nMEDIA:{md_path.resolve()}')
    print(f'MEDIA:{html_path.resolve()}')


if __name__ == '__main__':
    main()
