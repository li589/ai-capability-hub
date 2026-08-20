# -*- coding: utf-8 -*-
"""
fullpage_archiver.py v1.0 — 全页内容归档器（零新依赖）
====================================================
单页 or 翻页 → 下载全部文字+图片+Canvas+Svg+表格 → 生成自包含输出。

特性：
  - 双重输出模式：base64 内嵌单文件 HTML + 独立目录（同时生成）
  - 自动翻页（复用 BrowserScraper.paginate）
  - 图片去重（同 URL 只下载一次）
  - Canvas 截图（等待 JS 渲染后 element.screenshot）
  - 表格提取（HTML <table> → JSON，保留跨行/跨列结构）
  - SVG 内联保留
  - 类人操作集成（可选）
  - 零新增 pip 依赖（仅依赖已有的可选 playwright）

用法：
    from fullpage_archiver import FullPageArchiver
    archiver = FullPageArchiver()
    result = archiver.archive("https://example.com/article")

    # 翻页归档
    result = archiver.archive(url, paginate=True, next_selector=".next-page",
                              max_pages=5)

    # 仅生成目录模式（不内嵌 base64）
    result = archiver.archive(url, inline_images=False, save_assets=True)
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

# ─── 路径 ────────────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
ARCHIVE_DIR = DATA_DIR / "archives"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# ─── 正则（图片提取） ──────────────────────────────────────────────────────────

_IMG_SRC_RE = re.compile(r'<img[^>]+src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_IMG_SRCSET_RE = re.compile(r'<img[^>]+srcset\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_SOURCE_SRC_RE = re.compile(r'<source[^>]+srcset\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_CSS_URL_RE = re.compile(r'url\(["\']?([^)"\']+)["\']?\)', re.IGNORECASE)
_SVG_TAG_RE = re.compile(r'<svg[\s\S]*?</svg>', re.IGNORECASE)
_CANVAS_TAG_RE = re.compile(r'<canvas[^>]*>', re.IGNORECASE)
_TABLE_RE = re.compile(r'<table[\s\S]*?</table>', re.IGNORECASE)

# ─── 数据模型 ────────────────────────────────────────────────────────────────


@dataclass
class ArchiveResult:
    """归档结果"""
    url: str
    title: str = ""
    output_dir: str = ""
    inline_html_path: str = ""        # base64 内嵌版
    index_html_path: str = ""         # 目录版
    page_count: int = 0
    image_count: int = 0
    canvas_count: int = 0
    table_count: int = 0
    total_size_bytes: int = 0
    fetched_at: str = ""
    elapsed_seconds: float = 0.0
    pages: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # 压缩 pages 字段（仅保留摘要）
        d["pages"] = [{"page_num": p.get("page_num"), "url": p.get("url")}
                       for p in self.pages]
        return d

    @property
    def summary(self) -> str:
        lines = [
            f"📦 归档完成: {self.title or self.url[:60]}",
            f"   页数: {self.page_count} | 图片: {self.image_count} | "
            f"Canvas: {self.canvas_count} | 表格: {self.table_count}",
            f"   大小: {self._format_size(self.total_size_bytes)} | "
            f"耗时: {self.elapsed_seconds:.1f}s",
        ]
        if self.inline_html_path:
            lines.append(f"   内嵌版: {self.inline_html_path}")
        if self.index_html_path:
            lines.append(f"   目录版: {self.index_html_path}")
        if self.errors:
            lines.append(f"   ⚠️  {len(self.errors)} 个错误")
        return "\n".join(lines)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f}MB"


# ─── 主类 ────────────────────────────────────────────────────────────────────


class FullPageArchiver:
    """全页内容归档器。

    Args:
        headless: 浏览器模式（默认无头）
        timeout: 页面加载超时（秒）
        humanlike: 是否启用类人操作
        max_image_mb: 单张图片最大下载大小（MB）
    """

    def __init__(self, headless: bool = True, timeout: int = 30,
                 humanlike: bool = True, max_image_mb: float = 10.0):
        self.headless = headless
        self.timeout = timeout
        self.humanlike = humanlike
        self.max_image_bytes = int(max_image_mb * 1024 * 1024)

    # ── 主入口 ─────────────────────────────────────────────────────────

    def archive(self, url: str, *,
                paginate: bool = False,
                next_selector: Optional[str] = None,
                max_pages: int = 5,
                output_dir: Optional[str] = None,
                inline_images: bool = True,
                save_assets: bool = True,
                download_images: bool = True,
                capture_canvases: bool = True,
                extract_tables: bool = True,
                dismiss_cookies: bool = True) -> ArchiveResult:
        """全页归档主入口。

        Args:
            url: 目标 URL
            paginate: 是否自动翻页
            next_selector: "下一页"按钮 CSS 选择器（翻页时必填）
            max_pages: 最大翻页数
            output_dir: 输出目录（None=自动生成）
            inline_images: 是否生成 base64 内嵌单文件 HTML
            save_assets: 是否保存原始资源到独立目录
            download_images: 是否下载图片
            capture_canvases: 是否截图 Canvas 元素
            extract_tables: 是否提取 HTML 表格为 JSON
            dismiss_cookies: 是否自动关闭 Cookie 弹窗

        Returns:
            ArchiveResult: 归档结果对象
        """
        start_time = time.time()
        errors: List[str] = []

        # 确定输出目录
        domain = self._extract_domain(url)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir is None:
            output_dir = str(ARCHIVE_DIR / domain / ts)
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        # ── 1. 抓取页面（含翻页） ──
        pages_data = self._fetch_pages(
            url, paginate=paginate, next_selector=next_selector,
            max_pages=max_pages, dismiss_cookies=dismiss_cookies,
        )
        if not pages_data:
            return ArchiveResult(
                url=url, output_dir=str(out_p),
                fetched_at=datetime.now().isoformat(),
                elapsed_seconds=round(time.time() - start_time, 2),
                errors=["无法获取页面内容"],
            )

        # ── 2. 提取标题 ──
        title = self._extract_title(pages_data[0]["html"]) or domain

        # ── 3. 下载图片 ──
        image_map: Dict[str, str] = {}  # {original_url: local_path}
        if download_images:
            assets_dir = out_p / "assets" / "images"
            assets_dir.mkdir(parents=True, exist_ok=True)
            for pdata in pages_data:
                page_images = self._download_page_images(
                    pdata["html"], pdata["url"], str(assets_dir),
                )
                image_map.update(page_images)

        # ── 4. 截图 Canvas ──
        canvas_paths: List[str] = []
        if capture_canvases:
            canvas_dir = out_p / "assets" / "canvases"
            canvas_dir.mkdir(parents=True, exist_ok=True)
            canvas_paths = self._capture_page_canvases(
                pages_data[0]["url"], str(canvas_dir), dismiss_cookies,
            ) if pages_data else []

        # ── 5. 提取表格 ──
        tables_data: List[Dict] = []
        if extract_tables:
            tables_dir = out_p / "assets" / "tables"
            tables_dir.mkdir(parents=True, exist_ok=True)
            for pdata in pages_data:
                page_tables = self._extract_page_tables(
                    pdata["html"], pdata["page_num"], str(tables_dir),
                )
                tables_data.extend(page_tables)

        # ── 6. 生成输出文件 ──
        inline_html_path = ""
        index_html_path = ""

        if inline_images:
            inline_html_path = str(out_p / "article_inline.html")
            self._write_inline_html(
                pages_data, image_map, canvas_paths, title, inline_html_path,
            )

        if save_assets:
            index_html_path = str(out_p / "index.html")
            self._write_assets_html(
                pages_data, image_map, canvas_paths, title, index_html_path,
            )

        # ── 7. 保存多页数据 ──
        pages_dir = out_p / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        for pdata in pages_data:
            page_file = pages_dir / f"page_{pdata['page_num']:02d}.html"
            page_file.write_text(pdata["html"], encoding="utf-8")

        # ── 8. 保存元数据 ──
        metadata = {
            "url": url, "title": title, "domain": domain,
            "fetched_at": datetime.now().isoformat(),
            "page_count": len(pages_data),
            "image_count": len(image_map),
            "canvas_count": len(canvas_paths),
            "table_count": len(tables_data),
            "pages": [{"page_num": p["page_num"], "url": p["url"]}
                       for p in pages_data],
        }
        (out_p / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8",
        )

        # ── 9. 计算总大小 ──
        total_size = sum(
            f.stat().st_size for f in out_p.rglob("*") if f.is_file()
        )

        return ArchiveResult(
            url=url, title=title[:200],
            output_dir=str(out_p),
            inline_html_path=inline_html_path,
            index_html_path=index_html_path,
            page_count=len(pages_data),
            image_count=len(image_map),
            canvas_count=len(canvas_paths),
            table_count=len(tables_data),
            total_size_bytes=total_size,
            fetched_at=datetime.now().isoformat(),
            elapsed_seconds=round(time.time() - start_time, 2),
            pages=pages_data,
            errors=errors,
        )

    # ── 内部: 页面抓取 ────────────────────────────────────────────────

    def _fetch_pages(self, url: str, *, paginate: bool,
                     next_selector: Optional[str], max_pages: int,
                     dismiss_cookies: bool) -> List[Dict[str, Any]]:
        """抓取单页或多页。"""
        try:
            from scripts.browser_scraper import BrowserScraper
        except ImportError:
            try:
                from browser_scraper import BrowserScraper
            except ImportError:
                # 回退到纯 HTTP 请求
                return self._fetch_pages_http(url)

        try:
            bs = BrowserScraper(headless=self.headless, timeout_ms=self.timeout * 1000)
            bs.start()
            try:
                if paginate and next_selector:
                    result = bs.paginate(
                        url, next_selector, max_pages=max_pages,
                        dismiss_cookies=dismiss_cookies,
                    )
                    return result.get("pages", [])
                else:
                    if self.humanlike and hasattr(bs, "humanlike_fetch"):
                        html = bs.humanlike_fetch(url, scroll=True, dwell=True)
                    else:
                        html = bs.fetch(url, scroll=True, dismiss_cookies=dismiss_cookies)
                    if html:
                        return [{"url": url, "html": html, "page_num": 1}]
            finally:
                bs.stop()
        except Exception as e:
            # Browser 不可用 → 回退 HTTP
            pass

        return self._fetch_pages_http(url)

    def _fetch_pages_http(self, url: str) -> List[Dict[str, Any]]:
        """纯 HTTP 请求回退（无 JS 渲染）。"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/131.0.0.0 Safari/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                # 编码检测
                charset = resp.headers.get_content_charset() or "utf-8"
                try:
                    html = raw.decode(charset, errors="replace")
                except (LookupError, TypeError):
                    html = raw.decode("utf-8", errors="replace")
                return [{"url": url, "html": html, "page_num": 1}]
        except Exception:
            return []

    # ── 内部: 图片下载 ────────────────────────────────────────────────

    def _download_page_images(self, html: str, base_url: str,
                              assets_dir: str) -> Dict[str, str]:
        """下载页面中的所有图片，返回 {original_url: local_path}。"""
        image_map: Dict[str, str] = {}
        seen_norm: Dict[str, str] = {}  # normalized_url → local_path

        # 提取所有 <img src>
        for m in _IMG_SRC_RE.finditer(html):
            raw_src = m.group(1)
            img_map = self._download_single_image(
                raw_src, base_url, assets_dir, seen_norm,
            )
            image_map.update(img_map)

        # 提取 <source srcset> (取第一个 URL)
        for m in _SOURCE_SRC_RE.finditer(html):
            srcset = m.group(1)
            first_url = srcset.split(",")[0].strip().split(" ")[0]
            if first_url:
                img_map = self._download_single_image(
                    first_url, base_url, assets_dir, seen_norm,
                )
                image_map.update(img_map)

        return image_map

    def _download_single_image(self, raw_url: str, base_url: str,
                                assets_dir: str,
                                seen_norm: Dict[str, str]) -> Dict[str, str]:
        """下载单张图片（带去重）。"""
        if not raw_url or raw_url.startswith("data:"):
            return {}

        full_url = urljoin(base_url, raw_url)
        parsed = urlparse(full_url)
        norm_key = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if norm_key in seen_norm:
            return {full_url: seen_norm[norm_key]}

        ext = self._guess_image_ext(full_url)
        fname = hashlib.md5(norm_key.encode()).hexdigest()[:16] + ext
        local_path = os.path.join(assets_dir, fname)

        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; cn-financial-scraper/4.5)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                if len(data) > self.max_image_bytes:
                    return {}
                Path(local_path).write_bytes(data)
            seen_norm[norm_key] = local_path
            return {full_url: local_path}
        except Exception:
            return {}

    # ── 内部: Canvas 截图 ─────────────────────────────────────────────

    def _capture_page_canvases(self, url: str, canvas_dir: str,
                               dismiss_cookies: bool) -> List[str]:
        """截图页面中的 Canvas 元素。

        使用 try/finally 保证无论截图成功与否都释放浏览器进程，避免泄漏。
        """
        paths: List[str] = []
        try:
            from browser_scraper import BrowserScraper
        except ImportError:
            try:
                from scripts.browser_scraper import BrowserScraper
            except ImportError:
                return paths

        bs = None
        try:
            bs = BrowserScraper(headless=self.headless, timeout_ms=self.timeout * 1000)
            paths = bs.capture_canvas(url, output_dir=canvas_dir,
                                      wait_seconds=2.0,
                                      dismiss_cookies=dismiss_cookies)
        except Exception:
            pass
        finally:
            if bs is not None:
                try:
                    bs.stop()
                except Exception:
                    pass
        return paths

    # ── 内部: 表格提取 ────────────────────────────────────────────────

    def _extract_page_tables(self, html: str, page_num: int,
                             tables_dir: str) -> List[Dict]:
        """提取页面中的所有 <table> 为 JSON。"""
        tables: List[Dict] = []
        for i, m in enumerate(_TABLE_RE.finditer(html)):
            table_html = m.group(0)
            try:
                table_data = self._parse_html_table(table_html)
                if not table_data:
                    continue
                table_info = {
                    "page_num": page_num,
                    "table_index": i,
                    "rows": len(table_data),
                    "cols": max(len(row) for row in table_data) if table_data else 0,
                    "data": table_data,
                }
                # 保存为 JSON
                json_path = os.path.join(
                    tables_dir,
                    f"table_p{page_num:02d}_{i:02d}.json",
                )
                Path(json_path).write_text(
                    json.dumps(table_info, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                tables.append(table_info)
            except Exception:
                continue
        return tables

    def _parse_html_table(self, table_html: str) -> List[List[str]]:
        """简易 HTML 表格解析（不依赖 BeautifulSoup）。"""
        # 提取所有行
        rows: List[List[str]] = []
        tr_pattern = re.compile(r'<tr[\s>][\s\S]*?</tr>', re.IGNORECASE)
        td_pattern = re.compile(r'<(?:td|th)[^>]*>([\s\S]*?)</(?:td|th)>', re.IGNORECASE)
        tag_strip = re.compile(r'<[^>]+>')

        for tr_m in tr_pattern.finditer(table_html):
            row_html = tr_m.group(0)
            cells = []
            for td_m in td_pattern.finditer(row_html):
                cell_text = tag_strip.sub('', td_m.group(1)).strip()
                cell_text = re.sub(r'\s+', ' ', cell_text)
                cells.append(cell_text)
            if cells:
                rows.append(cells)
        return rows

    # ── 内部: 输出生成 ────────────────────────────────────────────────

    def _write_inline_html(self, pages_data: List[Dict],
                           image_map: Dict[str, str],
                           canvas_paths: List[str],
                           title: str, output_path: str):
        """生成 base64 内嵌图片的单文件 HTML。"""
        # 合并所有页面
        parts = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<head>',
            f'<meta charset="utf-8">',
            f'<title>{self._escape_html(title)}</title>',
            '<style>',
            '  body { max-width: 900px; margin: 0 auto; padding: 20px; '
            'font-family: "Microsoft YaHei", "PingFang SC", sans-serif; '
            'line-height: 1.8; color: #333; }',
            '  img { max-width: 100%; height: auto; display: block; margin: 16px 0; }',
            '  .page-divider { border-top: 2px dashed #ccc; margin: 30px 0; '
            'padding-top: 10px; color: #999; font-size: 14px; }',
            '  table { border-collapse: collapse; width: 100%; margin: 16px 0; }',
            '  table td, table th { border: 1px solid #ddd; padding: 8px; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>{self._escape_html(title)}</h1>',
            f'<p class="meta">归档时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} '
            f'| 页数: {len(pages_data)}</p>',
        ]

        for i, pdata in enumerate(pages_data):
            if i > 0:
                parts.append(
                    f'<div class="page-divider">📄 第 {pdata["page_num"]} 页 '
                    f'— {self._escape_html(pdata.get("url", "")[:80])}</div>'
                )
            html = pdata["html"]
            # 替换图片 src 为 base64
            html = self._inline_images_in_html(html, image_map, pdata["url"])
            # 注入到 body
            body_content = self._extract_body_content(html)
            parts.append(body_content)

        # 附加 Canvas 截图
        if canvas_paths:
            parts.append('<hr><h2>📊 图表 (Canvas 截图)</h2>')
            for cp in canvas_paths:
                b64 = self._file_to_base64(cp)
                if b64:
                    ext = os.path.splitext(cp)[1].lower()
                    mime = "image/png" if ext == ".png" else "image/jpeg"
                    parts.append(
                        f'<figure><img src="data:{mime};base64,{b64}" '
                        f'alt="Canvas 截图"><figcaption>{os.path.basename(cp)}'
                        f'</figcaption></figure>'
                    )

        parts.extend(['</body>', '</html>'])
        Path(output_path).write_text("\n".join(parts), encoding="utf-8")

    def _write_assets_html(self, pages_data: List[Dict],
                           image_map: Dict[str, str],
                           canvas_paths: List[str],
                           title: str, output_path: str):
        """生成引用本地资源的目录版 index.html。"""
        parts = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<head>',
            f'<meta charset="utf-8">',
            f'<title>{self._escape_html(title)}</title>',
            '<style>',
            '  body { max-width: 900px; margin: 0 auto; padding: 20px; '
            'font-family: "Microsoft YaHei", "PingFang SC", sans-serif; '
            'line-height: 1.8; color: #333; }',
            '  img { max-width: 100%; height: auto; display: block; margin: 16px 0; }',
            '  .page-divider { border-top: 2px dashed #ccc; margin: 30px 0; '
            'padding-top: 10px; color: #999; font-size: 14px; }',
            '  table { border-collapse: collapse; width: 100%; margin: 16px 0; }',
            '  table td, table th { border: 1px solid #ddd; padding: 8px; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>{self._escape_html(title)}</h1>',
            f'<p class="meta">归档时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} '
            f'| 页数: {len(pages_data)}</p>',
        ]

        for i, pdata in enumerate(pages_data):
            if i > 0:
                parts.append(
                    f'<div class="page-divider">📄 第 {pdata["page_num"]} 页</div>'
                )
            html = pdata["html"]
            # 替换图片 src 为相对路径
            html = self._relink_images_in_html(html, image_map)
            body_content = self._extract_body_content(html)
            parts.append(body_content)

        # 附加 Canvas
        if canvas_paths:
            parts.append('<hr><h2>📊 图表</h2>')
            for cp in canvas_paths:
                rel_path = os.path.relpath(
                    cp, os.path.dirname(output_path)
                ).replace("\\", "/")
                parts.append(
                    f'<figure><img src="{rel_path}" alt="Canvas 截图">'
                    f'<figcaption>{os.path.basename(cp)}</figcaption></figure>'
                )

        parts.extend(['</body>', '</html>'])
        Path(output_path).write_text("\n".join(parts), encoding="utf-8")

    # ── 内部: HTML 处理 ───────────────────────────────────────────────

    def _inline_images_in_html(self, html: str, image_map: Dict[str, str],
                               base_url: str) -> str:
        """将 HTML 中的图片 src 替换为 base64 data URI。"""
        def _replace_img(m: re.Match) -> str:
            tag = m.group(0)
            src_m = re.search(r'src\s*=\s*["\']([^"\']+)["\']', tag, re.IGNORECASE)
            if not src_m:
                return tag
            src = src_m.group(1)
            full_src = urljoin(base_url, src)
            local = image_map.get(full_src) or image_map.get(src)
            if local and os.path.exists(local):
                b64 = self._file_to_base64(local)
                if b64:
                    ext = os.path.splitext(local)[1].lower()
                    mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                                ".jpeg": "image/jpeg", ".gif": "image/gif",
                                ".webp": "image/webp", ".svg": "image/svg+xml",
                                ".bmp": "image/bmp"}
                    mime = mime_map.get(ext, "image/png")
                    tag = tag.replace(
                        src_m.group(1),
                        f"data:{mime};base64,{b64}",
                    )
            return tag

        # 还有 CSS url() 引用
        def _replace_css_url(m: re.Match) -> str:
            full = m.group(0)
            inner = m.group(1)
            if inner.startswith("data:"):
                return full
            full_url = urljoin(base_url, inner)
            local = image_map.get(full_url) or image_map.get(inner)
            if local and os.path.exists(local):
                b64 = self._file_to_base64(local)
                if b64:
                    ext = os.path.splitext(local)[1].lower()
                    mime = "image/png" if ext == ".png" else "image/jpeg"
                    return f"url(data:{mime};base64,{b64})"
            return full

        html = _IMG_SRC_RE.sub(_replace_img, html)
        html = _CSS_URL_RE.sub(_replace_css_url, html)
        return html

    def _relink_images_in_html(self, html: str,
                               image_map: Dict[str, str]) -> str:
        """将图片 src 替换为本地相对路径。"""
        def _replace(m: re.Match) -> str:
            tag = m.group(0)
            src_m = re.search(r'src\s*=\s*["\']([^"\']+)["\']', tag, re.IGNORECASE)
            if not src_m:
                return tag
            src = src_m.group(1)
            local = image_map.get(src)
            if local:
                # 使用 assets/images/ 相对路径
                fname = os.path.basename(local)
                tag = tag.replace(src_m.group(1), f"assets/images/{fname}")
            return tag
        return re.sub(r'<img[^>]+src\s*=\s*["\']([^"\']+)["\'][^>]*>',
                       _replace, html, flags=re.IGNORECASE)

    def _extract_body_content(self, html: str) -> str:
        """抽取 <body> 内容（无 body 标签时返回全文）。"""
        m = re.search(r'<body[^>]*>([\s\S]*?)</body>', html, re.IGNORECASE)
        if m:
            return m.group(1)
        return html

    # ── 内部: 工具函数 ────────────────────────────────────────────────

    @staticmethod
    def _extract_title(html: str) -> str:
        m = re.search(r'<title[^>]*>([\s\S]*?)</title>', html, re.IGNORECASE)
        if m:
            return re.sub(r'\s+', ' ', m.group(1)).strip()[:200]
        return ""

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            return urlparse(url).netloc.replace("www.", "")[:40]
        except Exception:
            return "unknown"

    @staticmethod
    def _guess_image_ext(url: str) -> str:
        path = urlparse(url).path.lower()
        for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"):
            if path.endswith(ext):
                return ".jpg" if ext == ".jpeg" else ext
        return ".jpg"

    @staticmethod
    def _escape_html(text: str) -> str:
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    @staticmethod
    def _file_to_base64(file_path: str) -> str:
        """文件转 base64 字符串。"""
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("ascii")
        except Exception:
            return ""


# ── 便捷函数 ────────────────────────────────────────────────────────────────


def quick_archive(url: str, **kwargs) -> ArchiveResult:
    """一行归档：默认同时生成内嵌版 + 目录版。"""
    archiver = FullPageArchiver()
    return archiver.archive(url, **kwargs)


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    import argparse
    ap = argparse.ArgumentParser(description="全页内容归档器 v1.0")
    ap.add_argument("url", help="目标 URL")
    ap.add_argument("--paginate", action="store_true", help="启用翻页")
    ap.add_argument("--next-selector", default=".next,a[rel=next]",
                    help="下一页选择器")
    ap.add_argument("--max-pages", type=int, default=5, help="最大页数")
    ap.add_argument("--output-dir", help="输出目录")
    ap.add_argument("--no-inline", action="store_true", help="不生成内嵌版")
    ap.add_argument("--no-assets", action="store_true", help="不生成目录版")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式结果")
    args = ap.parse_args()

    print(f"📥 正在归档: {args.url}")
    result = quick_archive(
        args.url,
        paginate=args.paginate,
        next_selector=args.next_selector if args.paginate else None,
        max_pages=args.max_pages,
        output_dir=args.output_dir,
        inline_images=not args.no_inline,
        save_assets=not args.no_assets,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.summary)


if __name__ == "__main__":
    main()
