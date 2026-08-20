# -*- coding: utf-8 -*-
"""
核心排版引擎 — Markdown 转微信公众号 HTML
纯 Python 实现，所有样式内联（公众号不支持外部 CSS）

支持：
- h1-h6, 粗体/斜体/删除线/下划线/标记/上下标
- 代码块 (```), 行内代码 (`)
- 表格, 引用 (>), 有序/无序列表, 嵌套列表
- 图片, 链接, 脚注, 分割线 (---/***), 段落
- 任务列表 (checkbox)
- GitHub 风格警告框: > [!TIP/NOTE/IMPORTANT/WARNING/CAUTION]
- 代码块 class="language-xxx" 保留
"""

import re
import sys
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    from .themes import get_resolved_theme, get_image_style
    from .syntax_highlight import highlight as syntax_highlight
    from .code_themes import get_code_theme
except ImportError:
    # 直接运行时修正 path
    _script_dir = Path(__file__).resolve().parent
    if str(_script_dir) not in sys.path:
        sys.path.insert(0, str(_script_dir))
    from themes import get_resolved_theme, get_image_style
    from syntax_highlight import highlight as syntax_highlight
    from code_themes import get_code_theme


def _escape_html(s: str) -> str:
    """HTML 转义"""
    if not s:
        return ''
    return (s.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _allow_u(escaped: str, theme: dict) -> str:
    """在转义后允许 <u></u> 以真实标签渲染（带主题样式）"""
    if not escaped:
        return ''
    u_style = theme.get('u', 'text-decoration:underline;')
    return (escaped
            .replace('&lt;u&gt;', f'<u style="{u_style}">')
            .replace('&lt;/u&gt;', '</u>'))


def _parse_table(lines: list, start_idx: int) -> Tuple[List[List[str]], int]:
    """解析 Markdown 表格

    Returns:
        (rows, next_idx)
    """
    rows = []
    i = start_idx
    while i < len(lines):
        line = lines[i]
        if not re.match(r'^\|.+\|$', line.strip()):
            break
        cells = [c.strip() for c in line.split('|')]
        # Remove first and last empty cells from leading/trailing |
        if len(cells) >= 2:
            cells = cells[1:-1]
        if cells:
            rows.append(cells)
        i += 1
    return rows, i


def md_to_wechat_html(md_text: str, theme_id: str = 'lapis',
                      code_theme_id: str = 'solarized-light') -> str:
    """将 Markdown 转换为微信公众号兼容的 HTML（所有样式内联）

    Args:
        md_text: Markdown 源文本
        theme_id: 主题 ID (lapis/forest/ocean/sunset/noir)
        code_theme_id: 代码高亮主题 ID

    Returns:
        带内联样式的 HTML 字符串
    """
    if not md_text:
        return ''

    theme = get_resolved_theme(theme_id)
    img_style = get_image_style(theme_id)

    lines = md_text.split('\n')

    # 收集引用定义、脚注定义、缩写
    refs: Dict[str, Dict[str, str]] = {}
    abbrevs: Dict[str, str] = {}
    footnote_defs: Dict[str, str] = {}
    footnote_order: List[str] = []
    skip_line_idx: set = set()

    for idx, ln in enumerate(lines):
        # 引用定义: [id]: url "title"
        ref_m = re.match(r'^\s*\[([^\]]+)\]:\s*(\S+)(?:\s+["\']([^"\']*)["\'])?\s*$', ln)
        if ref_m:
            ref_id = ref_m.group(1).lower().replace(r'\s+', ' ')
            ref_url = ref_m.group(2).replace('<', '').replace('>', '')
            ref_title = ref_m.group(3) or ''
            refs[ref_id] = {'url': ref_url, 'title': ref_title}
            continue

        # 缩写: *[ABBR]: 解释
        abbr_m = re.match(r'^\s*\*\[([^\]]+)\]:\s*(.+)\s*$', ln)
        if abbr_m:
            abbrevs[abbr_m.group(1)] = abbr_m.group(2).strip()

        # 脚注定义: [^id]: content
        fn_m = re.match(r'^\s*\[\^([^\]]+)\]:\s*(.*)\s*$', ln)
        if fn_m:
            fn_id = fn_m.group(1)
            if fn_id not in footnote_defs:
                fn_content = fn_m.group(2)
                j = idx + 1
                skip_line_idx.add(idx)
                while j < len(lines) and lines[j].startswith('    '):
                    fn_content += '\n' + lines[j][4:]
                    skip_line_idx.add(j)
                    j += 1
                footnote_defs[fn_id] = fn_content
                footnote_order.append(fn_id)

    html_parts: List[str] = []
    in_blockquote = False
    in_list = False
    list_type = ''  # 'ul' or 'ol'
    list_nest_depth = 0
    in_def_list = False

    # 脚注编号映射
    fn_num_map = {fn_id: idx + 1 for idx, fn_id in enumerate(footnote_order)}
    fn_ref_count: Dict[str, int] = {}

    def _close_list():
        nonlocal in_list, list_type, list_nest_depth
        tag = 'ol' if list_type == 'ol' else 'ul'
        while list_nest_depth > 0:
            html_parts.append(f'</{tag}></li>')
            list_nest_depth -= 1
        if in_list:
            html_parts.append(f'</{"ol" if list_type == "ol" else "ul"}>\n')
            in_list = False

    def _apply_abbrevs(s: str) -> str:
        if not abbrevs:
            return s
        # Sort by length descending so longer ones match first
        for k in sorted(abbrevs.keys(), key=lambda x: -len(x)):
            pattern = re.compile(
                r'(?<![a-zA-Z0-9])' + re.escape(k) + r'(?![a-zA-Z0-9])'
            )
            s = pattern.sub(
                lambda m: f'<abbr title="{_escape_html(abbrevs[k])}">{m.group(0)}</abbr>',
                s,
            )
        return s

    def _process_inline(s: str) -> str:
        """处理行内标记：粗体、斜体、删除线、代码、链接、图片、脚注引用等"""
        # 先转义 HTML
        escaped = _escape_html(s)

        # 粗体 **text**
        escaped = re.sub(
            r'\*\*(.+?)\*\*',
            lambda m: f'<strong style="{theme.get("strong", "font-weight:700")}">{_escape_html(m.group(1))}</strong>',
            escaped,
        )
        # 粗体 __text__
        escaped = re.sub(
            r'__(.+?)__',
            lambda m: f'<strong style="{theme.get("strong", "font-weight:700")}">{_escape_html(m.group(1))}</strong>',
            escaped,
        )
        # 斜体 *text*
        escaped = re.sub(r'\*(.+?)\*', lambda m: f'<em>{_escape_html(m.group(1))}</em>', escaped)
        # 斜体 _text_
        escaped = re.sub(r'_(.+?)_', lambda m: f'<em>{_escape_html(m.group(1))}</em>', escaped)
        # 删除线 ~~text~~
        escaped = re.sub(r'~~(.+?)~~', lambda m: f'<s>{_escape_html(m.group(1))}</s>', escaped)
        # 下划线 ++text++
        escaped = re.sub(r'\+\+(.+?)\+\+', lambda m: f'<ins>{_escape_html(m.group(1))}</ins>', escaped)
        # 标记 ==text==
        escaped = re.sub(r'==(.+?)==', lambda m: f'<mark>{_escape_html(m.group(1))}</mark>', escaped)
        # 上标 ^text^
        escaped = re.sub(r'\^(.+?)\^', lambda m: f'<sup>{_escape_html(m.group(1))}</sup>', escaped)
        # 下标 ~text~
        escaped = re.sub(r'~(.+?)~', lambda m: f'<sub>{_escape_html(m.group(1))}</sub>', escaped)

        # 行内代码 `code`
        escaped = re.sub(
            r'`(.+?)`',
            lambda m: f'<code style="background:#f5f5f5;padding:2px 6px;border-radius:4px;font-size:14px">{_escape_html(m.group(1))}</code>',
            escaped,
        )

        # 脚注引用 [^id]
        def _fn_ref_replace(m):
            fn_id = m.group(1)
            num = fn_num_map.get(fn_id)
            if num is None:
                return m.group(0)
            cnt = fn_ref_count.get(fn_id, 0) + 1
            fn_ref_count[fn_id] = cnt
            ref_id = f'fnref{num}' if cnt == 1 else f'fnref{num}:{cnt - 1}'
            return f'<sup class="footnote-ref"><a href="#fn{num}" id="{ref_id}" style="font-size:12px;color:#1890ff;text-decoration:none">[{num}]</a></sup>'

        escaped = re.sub(r'\[\^([^\]]+)\]', _fn_ref_replace, escaped)

        # 图片引用式 ![alt][id]
        def _img_ref_replace(m):
            alt = m.group(1)
            ref_id = m.group(2)
            key = (ref_id or alt or '').lower().replace(r'\s+', ' ')
            r = refs.get(key)
            if r is None:
                return m.group(0)
            img_url = _escape_html(r['url'])
            img_alt = _escape_html(alt or '')
            title_attr = f' title="{_escape_html(r["title"])}"' if r.get('title') else ''
            caption = ''
            if img_alt and theme.get('imageCaption'):
                caption = f'<span style="{theme["imageCaption"]}">{img_alt}</span>'
            return f'<img src="{img_url}" alt="{img_alt}"{title_attr} style="{img_style}">{caption}'

        escaped = re.sub(r'!\[([^\]]*)\]\[([^\]]*)\]', _img_ref_replace, escaped)

        # 图片直接 ![alt](url)
        def _img_direct_replace(m):
            alt = m.group(1)
            src_part = m.group(2).strip()
            parts = src_part.split()
            img_src = parts[0].strip() if parts else ''
            img_title = parts[1].replace('"', '').replace("'", '') if len(parts) > 1 else ''
            img_url = _escape_html(img_src)
            img_alt = _escape_html(alt or '')
            title_attr = f' title="{_escape_html(img_title)}"' if img_title else ''
            caption = ''
            if img_alt and theme.get('imageCaption'):
                caption = f'<span style="{theme["imageCaption"]}">{img_alt}</span>'
            return f'<img src="{img_url}" alt="{img_alt}"{title_attr} style="{img_style}">{caption}'

        escaped = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _img_direct_replace, escaped)

        # 链接引用式 [text][id]
        def _link_ref_replace(m):
            text = m.group(1)
            ref_id = m.group(2)
            key = (ref_id or text or '').lower().replace(r'\s+', ' ')
            r = refs.get(key)
            if r is None:
                return m.group(0)
            link_url = _escape_html(r['url'])
            link_text = _escape_html(text or r['url'])
            title_attr = f' title="{_escape_html(r["title"])}"' if r.get('title') else ''
            return f'<a href="{link_url}"{title_attr} style="{theme.get("link", "color:#1890ff;text-decoration:underline")}" target="_blank" rel="noopener">{link_text}</a>'

        escaped = re.sub(r'\[([^\]]*)\]\[([^\]]*)\]', _link_ref_replace, escaped)

        # 链接直接 [text](url "title")
        def _link_direct_replace(m):
            text = m.group(1)
            href_part = m.group(2).strip()
            parts = href_part.split()
            link_href = parts[0].strip() if parts else ''
            link_title = parts[1].replace('"', '').replace("'", '') if len(parts) > 1 else ''
            link_url = _escape_html(link_href)
            link_text = _escape_html(text or link_url)
            title_attr = f' title="{_escape_html(link_title)}"' if link_title else ''
            return f'<a href="{link_url}"{title_attr} style="{theme.get("link", "color:#1890ff;text-decoration:underline")}" target="_blank" rel="noopener">{link_text}</a>'

        escaped = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', _link_direct_replace, escaped)

        return _apply_abbrevs(escaped)

    def _render_task_or_list_item(raw: str) -> str:
        """渲染任务列表项或普通列表项"""
        task_match = re.match(r'^(\[[ xX]\])\s+(.*)$', raw)
        if task_match:
            checked = task_match.group(1).lower() == '[x]'
            text = task_match.group(2)
            box = '☑' if checked else '☐'
            box_color = '#52c41a' if checked else '#bfbfbf'
            inner = _process_inline(text)
            return f'<span style="margin-right:6px;color:{box_color}" role="img" aria-label="{"已完成" if checked else "未完成"}">{box}</span>{inner}'
        return _process_inline(raw)

    i = 0
    while i < len(lines):
        line = lines[i]

        # 跳过已处理的行
        if i in skip_line_idx:
            i += 1
            continue

        # 跳过引用定义行
        if re.match(r'^\s*\[([^\]]+)\]:\s*\S+', line):
            i += 1
            continue
        if re.match(r'^\s*\*\[([^\]]+)\]:\s*', line):
            i += 1
            continue

        # 分割线
        if line.strip() == '---' or line.strip() == '***' or re.match(r'^___+$', line.strip()):
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            _close_list()
            html_parts.append(f'<hr style="{theme.get("hr", "border:none;height:1px;background:#e5e5e5;margin:24px 0")}">\n')
            i += 1
            continue

        # 代码块
        if line.strip().startswith('```'):
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            _close_list()

            lang_match = re.match(r'^```(\w*)', line.strip())
            lang = lang_match.group(1) if lang_match and lang_match.group(1) else ''

            code_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != '```':
                code_lines.append(lines[j])
                j += 1

            code_content = '\n'.join(code_lines)
            ct = get_code_theme(code_theme_id)
            code_block_style = theme.get(
                'codeBlock',
                f'margin:16px 0;padding:14px 18px;background:{ct["block"]["bg"]};'
                f'border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;'
                f'font-size:14px;line-height:1.5;border:1px solid {ct["block"]["border"]};'
                f'white-space:pre-wrap;word-break:break-word;color:{ct["colors"]["default"]}',
            )
            lang_label = ''
            if lang:
                lang_label = f'<div style="font-size:12px;color:{ct["block"]["labelColor"]};margin-bottom:8px;font-family:Consolas,monospace">{_escape_html(lang)}</div>'
            highlighted = syntax_highlight(code_content, lang, code_theme_id)
            data_lang = f' data-lang="{_escape_html(lang)}"' if lang else ''
            html_parts.append(
                f'<pre style="{code_block_style}"{data_lang}>{lang_label}'
                f'<code style="background:transparent;padding:0;font-size:inherit">{highlighted}</code></pre>\n'
            )
            i = j + 1
            continue

        # 缩进代码块 (4 spaces or tab)
        indent_code_match = re.match(r'^(    |\t)', line)
        if indent_code_match and line.strip() != '':
            trimmed = line[4:] if line.startswith('    ') else line[1:]
            # Check if it's a list continuation
            if re.match(r'^[-*+]\s', trimmed) or re.match(r'^\d+\.\s', trimmed):
                pass  # handle as list below
            else:
                if in_blockquote:
                    html_parts.append('</blockquote>\n')
                    in_blockquote = False
                _close_list()
                code_lines = []
                j = i
                while j < len(lines):
                    if re.match(r'^(    |\t)', lines[j]):
                        t = lines[j][4:] if lines[j].startswith('    ') else lines[j][1:]
                        if re.match(r'^[-*+]\s', t) or re.match(r'^\d+\.\s', t):
                            break
                        code_lines.append(t)
                        j += 1
                    else:
                        break
                code_content = '\n'.join(code_lines)
                ct = get_code_theme(code_theme_id)
                code_block_style = theme.get(
                    'codeBlock',
                    f'margin:16px 0;padding:14px 18px;background:{ct["block"]["bg"]};'
                    f'border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;'
                    f'font-size:14px;line-height:1.5;border:1px solid {ct["block"]["border"]};'
                    f'white-space:pre-wrap;word-break:break-word;color:{ct["colors"]["default"]}',
                )
                highlighted = syntax_highlight(code_content, '', code_theme_id)
                html_parts.append(
                    f'<pre style="{code_block_style}" data-lang="">'
                    f'<code style="background:transparent;padding:0;font-size:inherit">{highlighted}</code></pre>\n'
                )
                i = j
                continue

        # 标题 h1-h6
        h_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if h_match:
            level = len(h_match.group(1))
            content = h_match.group(2)
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            _close_list()

            processed = _process_inline(content)

            if level == 1:
                html_parts.append(f'<h1 style="{theme["h1"]}">{processed}</h1>\n')
            elif level == 2:
                html_parts.append(f'<h2 style="{theme["h2"]}">{processed}</h2>\n')
            elif level == 3:
                html_parts.append(f'<h3 style="{theme["h3"]}">{processed}</h3>\n')
            elif level == 4:
                style = theme.get('h4', theme.get('h3', 'font-size:16px;font-weight:600;'))
                html_parts.append(f'<h4 style="{style}">{processed}</h4>\n')
            elif level == 5:
                style = theme.get('h5', theme.get('h3', 'font-size:15px;font-weight:600;'))
                html_parts.append(f'<h5 style="{style}">{processed}</h5>\n')
            elif level == 6:
                style = theme.get('h6', theme.get('h3', 'font-size:14px;font-weight:600;'))
                html_parts.append(f'<h6 style="{style}">{processed}</h6>\n')
            i += 1
            continue

        # 表格
        if re.match(r'^\|.+\|$', line.strip()) and '|' in line:
            rows, next_idx = _parse_table(lines, i)
            i = next_idx
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            _close_list()

            if rows:
                # 找分隔行
                sep_idx = -1
                for ri, row in enumerate(rows):
                    if all(re.match(r'^[-:]+$', cell) for cell in row):
                        sep_idx = ri
                        break

                header_row = rows[0] if sep_idx >= 0 else None
                body_rows = rows[sep_idx + 1:] if sep_idx >= 0 else rows
                body_rows = [r for r in body_rows if not all(re.match(r'^[-:]+$', cell) for cell in r)]

                t = theme.get('table', {})
                html_parts.append(f'<table style="{t.get("wrap", "margin:16px 0;width:100%;border-collapse:collapse;border:1px solid #ddd;")}">')
                if header_row:
                    html_parts.append('<thead><tr>')
                    for cell in header_row:
                        html_parts.append(f'<th style="{t.get("th", "padding:10px 12px;background:#f5f5f5;font-weight:bold;text-align:left;border:1px solid #ddd;")}">{_process_inline(cell)}</th>')
                    html_parts.append('</tr></thead>')
                html_parts.append('<tbody>')
                for row in body_rows:
                    html_parts.append('<tr>')
                    for cell in row:
                        html_parts.append(f'<td style="{t.get("td", "padding:10px 12px;border:1px solid #ddd;")}">{_process_inline(cell)}</td>')
                    html_parts.append('</tr>')
                html_parts.append('</tbody></table>\n')
            continue

        # GitHub 风格警告框
        alert_match = re.match(r'^>\s*\[!(TIP|NOTE|IMPORTANT|WARNING|CAUTION)\]\s*$', line, re.IGNORECASE)
        if alert_match:
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            _close_list()

            kind = alert_match.group(1).upper()
            labels = {'TIP': '建议', 'NOTE': '提醒', 'IMPORTANT': '重要', 'WARNING': '警告', 'CAUTION': '注意'}
            label = labels.get(kind, kind)

            # Theme-based alert box colors
            alert_palette = {
                'TIP': {'emoji': '💡', 'border': '#10b981', 'bg': '#ecfdf5', 'color': '#065f46'},
                'NOTE': {'emoji': '📌', 'border': '#3b82f6', 'bg': '#eff6ff', 'color': '#1e40af'},
                'IMPORTANT': {'emoji': '⭐', 'border': '#8b5cf6', 'bg': '#f5f3ff', 'color': '#5b21b6'},
                'WARNING': {'emoji': '⚠️', 'border': '#f59e0b', 'bg': '#fffbeb', 'color': '#92400e'},
                'CAUTION': {'emoji': '🔴', 'border': '#ef4444', 'bg': '#fef2f2', 'color': '#991b1b'},
            }
            cfg = alert_palette.get(kind, alert_palette['NOTE'])

            body_lines = []
            j = i + 1
            while j < len(lines) and re.match(r'^>\s?', lines[j]):
                body_lines.append(re.sub(r'^>\s?', '', lines[j]))
                j += 1
            i = j - 1

            body = '<br>'.join(_process_inline(ln) for ln in body_lines if ln.strip())
            body_html = f'<p style="margin:0;padding:4px 0 0 0;line-height:1.6">{body}</p>' if body else ''

            alert_style = f'margin:16px 0;padding:12px 16px;border-radius:8px;border-left:4px solid {cfg["border"]};background:{cfg["bg"]};color:{cfg["color"]};'
            html_parts.append(
                f'<table style="width:100%;border-collapse:collapse;border:none">'
                f'<tr><td style="{alert_style}">'
                f'<span style="margin-right:6px" role="img" aria-hidden="true">{cfg["emoji"]}</span>'
                f'<strong style="font-weight:600">{_escape_html(label)}</strong>{body_html}'
                f'</td></tr></table>\n'
            )
            i += 1
            continue

        # 引用
        bq_match = re.match(r'^(>+)\s?(.*)$', line)
        if bq_match:
            level = len(bq_match.group(1))
            inner = bq_match.group(2) or ''
            if not in_blockquote:
                html_parts.append(f'<blockquote style="{theme["blockquote"]}">')
                in_blockquote = True
            if level > 1:
                html_parts.append(
                    '<blockquote style="margin:8px 0;padding-left:12px;border-left:3px solid rgba(0,0,0,0.1)">' * (level - 1)
                )
            html_parts.append(_process_inline(inner))
            if level > 1:
                html_parts.append('</blockquote>' * (level - 1))
            html_parts.append('<br>\n')
            i += 1
            continue

        if in_blockquote:
            html_parts.append('</blockquote>\n')
            in_blockquote = False

        # 无序列表
        ul_match = re.match(r'^(\s*)[-*+]\s+(.*)$', line)
        if ul_match:
            indent_str = ul_match.group(1) or ''
            indent_len = indent_str.count('\t') * 2 + len(indent_str.replace('\t', ''))
            level = indent_len // 2
            content = ul_match.group(2)

            if not in_list or list_type != 'ul':
                if in_list:
                    while list_nest_depth > 0:
                        html_parts.append(f'</{"ol" if list_type == "ol" else "ul"}></li>\n')
                        list_nest_depth -= 1
                    html_parts.append(f'</{"ol" if list_type == "ol" else "ul"}>\n')
                html_parts.append('<ul style="padding-left:24px;margin:16px 0">\n')
                in_list = True
                list_type = 'ul'

            while list_nest_depth > level:
                html_parts.append('</ul></li>\n')
                list_nest_depth -= 1
            for _ in range(list_nest_depth, level):
                html_parts.append('<ul style="padding-left:24px;margin:8px 0">\n')
                list_nest_depth += 1

            html_parts.append(f'<li style="margin:8px 0;">{_render_task_or_list_item(content)}</li>\n')
            i += 1
            continue

        # 有序列表
        ol_match = re.match(r'^(\s*)(\d+)\.\s+(.*)$', line)
        if ol_match:
            indent_str = ol_match.group(1) or ''
            indent_len = indent_str.count('\t') * 2 + len(indent_str.replace('\t', ''))
            level = indent_len // 2
            num = int(ol_match.group(2))
            rest = ol_match.group(3)

            if not in_list or list_type != 'ol':
                if in_list:
                    while list_nest_depth > 0:
                        html_parts.append(f'</{"ol" if list_type == "ol" else "ul"}></li>\n')
                        list_nest_depth -= 1
                    html_parts.append(f'</{"ol" if list_type == "ol" else "ul"}>\n')
                start_attr = f' start="{num}"' if num != 1 else ''
                html_parts.append(f'<ol style="padding-left:24px;margin:16px 0"{start_attr}>\n')
                in_list = True
                list_type = 'ol'

            while list_nest_depth > level:
                html_parts.append('</ol></li>\n')
                list_nest_depth -= 1
            for _ in range(list_nest_depth, level):
                html_parts.append('<ol style="padding-left:24px;margin:8px 0">\n')
                list_nest_depth += 1

            html_parts.append(f'<li style="margin:8px 0;">{_process_inline(rest)}</li>\n')
            i += 1
            continue

        # 关闭列表（如果进入了列表模式但当前行不是列表项）
        _close_list()

        # 定义列表: 项
        # 先检查下一行是否是 : 开头
        next_is_def = i + 1 < len(lines) and re.match(r'^[ \t]*:', lines[i + 1])
        if next_is_def and line.strip() and not re.match(r'^[#>\-*+]', line) and not re.match(r'^\s*\d+\.', line) and not re.match(r'^\s*\|', line):
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            if not in_def_list:
                html_parts.append('<dl style="margin:16px 0">\n')
                in_def_list = True
            html_parts.append(f'<dt style="font-weight:600;margin:8px 0">{_process_inline(line)}</dt>\n')
            i += 1
            continue

        # 定义列表: 定义 : 内容
        def_colon = re.match(r'^:\s+(.*)$', line)
        if def_colon:
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            if not in_def_list:
                html_parts.append('<dl style="margin:16px 0">\n')
                in_def_list = True
            def_content = def_colon.group(1)
            html_parts.append(f'<dd style="margin:4px 0 16px 24px"><p style="margin:4px 0">{_process_inline(def_content)}</p></dd>\n')
            i += 1
            continue

        if in_def_list:
            html_parts.append('</dl>\n')
            in_def_list = False

        # 独立图片行
        img_only_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line.strip())
        if img_only_match:
            raw_url = img_only_match.group(2).strip().split()[0].strip()
            img_url = _escape_html(raw_url)
            img_alt = _escape_html(img_only_match.group(1) or '')
            caption = ''
            if img_alt and theme.get('imageCaption'):
                caption = f'<span style="{theme["imageCaption"]}">{img_alt}</span>'
            html_parts.append(
                f'<p style="{theme.get("p", "margin:0;padding:8px 0;font-size:15px;line-height:1.8;")}">'
                f'<img src="{img_url}" alt="{img_alt}" style="{img_style}">{caption}</p>\n'
            )
            i += 1
            continue

        # 段落（普通文本）
        if line.strip() != '':
            processed = _process_inline(line)
            html_parts.append(
                f'<p style="{theme.get("p", "margin:0;padding:8px 0;font-size:15px;line-height:1.8;color:#333;")}">{processed}</p>\n'
            )

        i += 1

    # 关闭所有打开的标签
    if in_blockquote:
        html_parts.append('</blockquote>\n')
    _close_list()
    if in_def_list:
        html_parts.append('</dl>\n')

    # 脚注
    if footnote_order:
        html_parts.append(
            '<hr class="footnotes-sep" style="border:none;border-top:1px solid #e5e5e5;margin:24px 0">\n'
        )
        html_parts.append(
            '<section class="footnotes" style="font-size:14px;color:#666">\n'
            '<ol class="footnotes-list" style="padding-left:24px">\n'
        )
        for fn_idx, fn_id in enumerate(footnote_order):
            num = fn_idx + 1
            raw = footnote_defs[fn_id]
            paras = raw.split('\n\n')
            cnt = fn_ref_count.get(fn_id, 1)
            backrefs = []
            for r in range(cnt):
                ref_id = f'fnref{num}' if r == 0 else f'fnref{num}:{r}'
                backrefs.append(
                    f'<a href="#{ref_id}" class="footnote-backref" style="font-size:12px;color:#1890ff;text-decoration:none">↩︎</a>'
                )
            backref = ' '.join(backrefs)

            body_parts = []
            for pi, p in enumerate(paras):
                content = _process_inline(p.strip())
                suffix = f' {backref}' if pi == len(paras) - 1 else ''
                body_parts.append(f'<p style="margin:4px 0">{content}{suffix}</p>')
            body = ''.join(body_parts)
            html_parts.append(
                f'<li id="fn{num}" class="footnote-item" style="margin:8px 0">{body}</li>\n'
            )
        html_parts.append('</ol></section>\n')

    return ''.join(html_parts)


def get_full_html(md_text: str, theme_id: str = 'lapis',
                  code_theme_id: str = 'solarized-light') -> str:
    """生成完整的微信公众号文章 HTML（包含 section 包装）

    Args:
        md_text: Markdown 源文本
        theme_id: 主题 ID
        code_theme_id: 代码高亮主题 ID

    Returns:
        完整的公众号文章 HTML
    """
    theme = get_resolved_theme(theme_id)
    body = md_to_wechat_html(md_text, theme_id, code_theme_id)
    section_style = theme.get(
        'section',
        'margin:0;padding:12px 10px;font-family:-apple-system,BlinkMacSystemFont,'
        '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;'
        'font-size:15px;color:#1a202c;line-height:1.8;word-break:break-word;'
    )
    return (
        f'<section data-tool="公众号排版" style="{section_style}">\n'
        f'{body}\n'
        f'</section>'
    )
