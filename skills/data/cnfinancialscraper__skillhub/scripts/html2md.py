# -*- coding: utf-8 -*-
"""
html2md.py v1.0 — HTML → Markdown 转换器（零依赖）
====================================================
基于 stdlib html.parser 自写，支持最小可用标签集：
- 块级: h1-h6, p, blockquote, pre, ul, ol, li, hr, table/thead/tbody/tr/th/td, figure, div
- 行内: a, strong, em, b, i, code, br, img, span
- 自闭合: br, hr, img
- 丢弃: script, style, noscript, link, meta
- iframe → 文本 [iframe: src]

典型用法:
    from html2md import convert
    md = convert('<h1>标题</h1><p>正文 <a href="x">链接</a></p>')
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Dict, Optional, List
from urllib.parse import urljoin


# ============== 主入口 ==============

def convert(html: str, base_url: Optional[str] = None,
            image_map: Optional[Dict[str, str]] = None) -> str:
    """HTML 字符串 → Markdown 字符串。

    Args:
        html: 原始 HTML
        base_url: 用于相对链接/图片转绝对（可选）
        image_map: 把原图 URL 替换成本地路径（可选），如 {"https://x.com/a.png": "./a.png"}

    Returns:
        Markdown 字符串
    """
    if not html:
        return ""
    parser = _HtmlToMarkdown(base_url=base_url, image_map=image_map or {})
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        text = re.sub(r"<[^>]+>", "", html)
        return text.strip()
    md = parser.get_output().strip()
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md


def convert_with_tables(html: str, base_url: Optional[str] = None,
                        image_map: Optional[Dict[str, str]] = None) -> str:
    """convert() 的增强版：先用正则抽取 <table> 块并替换为 GFM 表格，
    再走 HTMLParser 处理其余标签。"""
    if not html:
        return ""
    placeholders: List[str] = []

    def _sub(match):
        gfm = _render_html_table(match.group(0))
        placeholders.append(gfm)
        return f"\n\n@@TABLE_{len(placeholders) - 1}@@\n\n"

    html2 = re.sub(r"<table[^>]*>.*?</table>", _sub, html,
                   flags=re.DOTALL | re.IGNORECASE)
    md = convert(html2, base_url=base_url, image_map=image_map)
    for i, gfm in enumerate(placeholders):
        md = md.replace(f"@@TABLE_{i}@@", gfm.strip())
    return md


# ============== 解析器 ==============

_BLOCK_TAGS = frozenset({
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "blockquote", "pre",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tr",
    "figure", "figcaption", "div", "hr",
    "section", "article", "header", "footer", "main", "aside",
})

_DROP_TAGS = frozenset({"script", "style", "noscript", "link", "meta", "head"})

# 标签栈：每个元素是一个 (tag, attrs, [start_md, end_md]) 配置
_TAG_RENDER = {
    "h1": ("\n\n# ", "\n\n"),
    "h2": ("\n\n## ", "\n\n"),
    "h3": ("\n\n### ", "\n\n"),
    "h4": ("\n\n#### ", "\n\n"),
    "h5": ("\n\n##### ", "\n\n"),
    "h6": ("\n\n###### ", "\n\n"),
    "p": ("\n\n", "\n\n"),
    "blockquote": ("\n\n", "\n\n"),
    "pre": ("\n\n", ""),
    "ul": ("\n\n", "\n\n"),
    "ol": ("\n\n", "\n\n"),
    "div": ("", "\n"),
    "section": ("", "\n"),
    "article": ("\n\n", "\n\n"),
    "header": ("", "\n"),
    "footer": ("", "\n"),
    "main": ("", "\n"),
    "aside": ("", "\n"),
    "figure": ("\n\n", "\n\n"),
    "figcaption": ("\n\n*", "*\n\n"),
}


class _HtmlToMarkdown(HTMLParser):
    def __init__(self, base_url: Optional[str], image_map: Dict[str, str]):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.image_map = image_map
        self.out: List[str] = []
        # 栈：每个元素 (tag, attrs, dropped)
        self.stack: List[tuple] = []
        self._in_pre = False
        self._pre_lang = ""
        self._drop_depth = 0
        self._last_link_href = ""

    # --- output ---

    def _emit(self, s: str) -> None:
        if self._drop_depth > 0:
            return
        self.out.append(s)

    def get_output(self) -> str:
        # 关闭未闭合的标签（容错）
        while self.stack:
            self.stack.pop()
            self._drop_depth = max(0, self._drop_depth - 1)
        return "".join(self.out)

    # --- helpers ---

    def _resolve_url(self, url: str) -> str:
        if not url:
            return ""
        if not self.base_url:
            return url
        if url.startswith(("http://", "https://", "data:", "mailto:", "//")):
            return url
        return urljoin(self.base_url, url)

    def _strip_ws_run(self, s: str) -> str:
        return re.sub(r"[ \t\f\v]+", " ", s)

    # --- element events ---

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        a = dict(attrs)

        if tag in _DROP_TAGS:
            self.stack.append((tag, a, True))
            self._drop_depth += 1
            return

        if tag == "br":
            self._emit("\n")
            return

        if tag == "hr":
            self._emit("\n\n---\n\n")
            return

        if tag == "img":
            src = self._resolve_url(a.get("src") or "")
            src = self.image_map.get(src, src)
            alt = a.get("alt") or ""
            title = a.get("title") or ""
            title_part = f' "{title}"' if title else ""
            self._emit(f"![{alt}]({src}{title_part})")
            return

        if tag == "iframe":
            src = self._resolve_url(a.get("src") or "")
            self._emit(f"[iframe: {src}]")
            return

        # 块级标签：输出起始 markdown
        if tag in _TAG_RENDER:
            start, _ = _TAG_RENDER[tag]
            if tag == "pre":
                self._in_pre = True
            if start:
                self._emit(start)
            self.stack.append((tag, a, False))
            return

        # 表格相关：保守处理
        if tag in ("table", "thead", "tbody", "tr", "th", "td"):
            self.stack.append((tag, a, False))
            return

        # 列表项 - 需要查看父级是 ul 还是 ol（默认 ul）
        if tag == "li":
            ordered = False
            # 检查外层最近未关闭的 ol/ul（在 li 之前）
            for i in range(len(self.stack) - 1, -1, -1):
                parent_tag = self.stack[i][0]
                if parent_tag == "ol":
                    ordered = True
                    break
                if parent_tag == "ul":
                    break
                if parent_tag in _BLOCK_TAGS:
                    break
            marker = "1. " if ordered else "- "
            self._emit(f"\n{marker}")
            self.stack.append((tag, a, False))
            return

        # 行内标签
        if tag in ("strong", "b"):
            self._emit("**")
            self.stack.append((tag, a, False))
            return

        if tag in ("em", "i"):
            self._emit("*")
            self.stack.append((tag, a, False))
            return

        if tag == "code":
            if self._in_pre:
                # pre 内：尝试抽取 language-xxx class
                cls = a.get("class", "") if a else ""
                m = re.search(r"language-(\S+)", cls)
                if m and not self._pre_lang:
                    self._pre_lang = m.group(1)
                self.stack.append((tag, a, False))
            else:
                self._emit("`")
                self.stack.append((tag, a, False))
            return

        if tag == "a":
            href = self._resolve_url(a.get("href") or "")
            self._emit("[")
            self.stack.append((tag, {"href": href}, False))
            self._last_link_href = href
            return

        if tag == "span":
            self.stack.append((tag, a, False))
            return

        # 未知标签：保留 children，当 inline
        self.stack.append((tag, a, False))

    def handle_endtag(self, tag: str):
        # 找到最近的同 tag
        idx = -1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                idx = i
                break
        if idx < 0:
            return  # 容错

        # 弹出（连同其后所有节点）
        dropped = self.stack[idx][2]
        self.stack = self.stack[:idx]

        if dropped:
            self._drop_depth = max(0, self._drop_depth - 1)
            return

        if tag == "pre":
            # 用 _pre_lang（pre 打开时已在内部 code 上设置）
            lang = self._pre_lang
            self._pre_lang = ""
            self._emit(f"```{lang}\n\n")
            self._in_pre = False
            return

        if tag == "code" and self._in_pre:
            # pre > code 内：不需要额外标记
            return

        if tag in _TAG_RENDER:
            _, end = _TAG_RENDER[tag]
            if end:
                self._emit(end)
            return

        if tag in ("table", "thead", "tbody", "tr", "th", "td"):
            return  # 不输出标记，由 _render_table 处理

        if tag == "li":
            # list item 不需要额外结束标记
            return

        if tag in ("strong", "b"):
            self._emit("**")
            return

        if tag in ("em", "i"):
            self._emit("*")
            return

        if tag == "code":
            self._emit("`")
            return

        if tag == "a":
            href = self._last_link_href
            self._emit(f"]({href})")
            return

        if tag == "span":
            return

        # 未知标签闭合 → 不输出
        return

    def handle_data(self, data: str):
        if not data or self._drop_depth > 0:
            return
        if self._in_pre:
            # pre 内保留原样
            self.out.append(data)
            return
        text = self._strip_ws_run(data)
        self._emit(text)

    def handle_entityref(self, name: str):
        if self._drop_depth > 0:
            return
        self._emit(f"&{name};")

    def handle_charref(self, name: str):
        if self._drop_depth > 0:
            return
        self._emit(f"&#{name};")


# ============== 表格渲染（独立） ==============

def _render_html_table(html: str) -> str:
    out: List[str] = []
    for m in re.finditer(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.IGNORECASE):
        body = m.group(1)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.DOTALL | re.IGNORECASE)
        if not rows:
            continue
        parsed: List[List[str]] = []
        for row in rows:
            cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.DOTALL | re.IGNORECASE)
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            cells = [c.replace("|", "\\|").replace("\n", " ") for c in cells]
            parsed.append(cells)
        if not parsed:
            continue
        ncols = max(len(r) for r in parsed)
        for r in parsed:
            while len(r) < ncols:
                r.append("")
        out.append(_gfm_table(parsed))
    return "\n\n".join(out)


def _gfm_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)