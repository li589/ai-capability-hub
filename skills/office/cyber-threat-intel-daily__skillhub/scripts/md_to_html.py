#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_to_html.py — 将威胁情报日报 Markdown 转换为精美独立 HTML 文件

用法：
  python3 md_to_html.py <input.md> --output <output.html>

特性：
  - 完全独立的单文件 HTML（CSS内联，无外部依赖）
  - 自动解析 Markdown 结构（标题、表格、列表、代码块）
  - 高亮 CVE 编号、威胁等级标签
  - 支持中文字体优先
"""

import argparse
import re
import sys
import os
from datetime import datetime


# ─── Markdown 解析器（轻量级，无需第三方库）─────────────────────────────────

def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def render_inline(text: str) -> str:
    """处理行内 Markdown 语法（粗体、斜体、代码、链接）"""
    # 代码（先处理，防止其他规则干扰）
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 粗体
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
    # 链接
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    # CVE 高亮
    text = re.sub(r'\b(CVE-\d{4}-\d{4,})\b', r'<span class="cve-badge">\1</span>', text)
    # 威胁等级 emoji 标签
    text = re.sub(r'🔴\s*(高|Critical|HIGH)', r'<span class="badge badge-critical">🔴 高危</span>', text)
    text = re.sub(r'🟠\s*(中高|High|HIGH)', r'<span class="badge badge-high">🟠 中高</span>', text)
    text = re.sub(r'🟡\s*(中|Medium|MEDIUM)', r'<span class="badge badge-medium">🟡 中危</span>', text)
    text = re.sub(r'🟢\s*(低|Low|LOW)', r'<span class="badge badge-low">🟢 低危</span>', text)
    return text


def parse_table(lines: list) -> str:
    """解析 Markdown 表格"""
    html = '<div class="table-wrapper"><table>\n'
    header_done = False
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            break
        # 分隔行（全是 - 和 |）
        if re.match(r'^\|[\s\-|:]+\|$', line):
            if not header_done:
                html += '</tr></thead>\n<tbody>\n'
                header_done = True
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        tag = 'th' if not header_done else 'td'
        row = '  <tr>\n'
        for cell in cells:
            row += f'    <{tag}>{render_inline(escape_html(cell))}</{tag}>\n'
        row += '  </tr>\n'
        if not header_done:
            html += '<thead>\n  <tr>\n'
            for cell in cells:
                html += f'    <th>{render_inline(escape_html(cell))}</th>\n'
            html += '  </tr>\n'
            header_done = True
            # 跳过这一行（已经手动写了）
            # 重置：下面统一走循环
            html = html  # noop
            break
    # 重新解析
    html = '<div class="table-wrapper"><table>\n'
    thead_cells = None
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            break
        if re.match(r'^\|[\s\-|:]+\|$', line):
            continue
        cells = [render_inline(escape_html(c.strip())) for c in line.split('|')[1:-1]]
        rows.append(cells)

    if rows:
        # 第一行为表头
        html += '<thead><tr>'
        for cell in rows[0]:
            html += f'<th>{cell}</th>'
        html += '</tr></thead>\n<tbody>\n'
        for row in rows[1:]:
            html += '<tr>'
            for cell in row:
                html += f'<td>{cell}</td>'
            html += '</tr>\n'
        html += '</tbody>\n'
    html += '</table></div>\n'
    return html


def md_to_html_body(md_text: str) -> tuple:
    """
    将 Markdown 正文转为 HTML body 内容
    返回 (html_body, report_title, report_date)
    """
    lines = md_text.split('\n')
    html_parts = []
    report_title = '网络安全威胁情报日报'
    report_date = datetime.now().strftime('%Y年%m月%d日')

    i = 0
    in_code_block = False
    code_lang = ''
    code_lines = []
    in_list = False
    list_type = None  # 'ul' or 'ol'
    list_items = []
    in_blockquote = False
    blockquote_lines = []

    def flush_list():
        nonlocal in_list, list_type, list_items
        if not in_list:
            return ''
        tag = list_type
        result = f'<{tag} class="md-list">\n'
        for item in list_items:
            result += f'  <li>{render_inline(escape_html(item))}</li>\n'
        result += f'</{tag}>\n'
        in_list = False
        list_type = None
        list_items = []
        return result

    def flush_blockquote():
        nonlocal in_blockquote, blockquote_lines
        if not in_blockquote:
            return ''
        content = '<br>'.join(render_inline(escape_html(l)) for l in blockquote_lines)
        result = f'<blockquote>{content}</blockquote>\n'
        in_blockquote = False
        blockquote_lines = []
        return result

    while i < len(lines):
        line = lines[i]

        # ── 代码块 ──
        if line.strip().startswith('```'):
            if in_list:
                html_parts.append(flush_list())
            if in_blockquote:
                html_parts.append(flush_blockquote())
            if in_code_block:
                code_content = escape_html('\n'.join(code_lines))
                lang_class = f' class="language-{code_lang}"' if code_lang else ''
                html_parts.append(f'<pre><code{lang_class}>{code_content}</code></pre>\n')
                in_code_block = False
                code_lines = []
                code_lang = ''
            else:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # ── 水平分割线 ──
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            if in_list:
                html_parts.append(flush_list())
            if in_blockquote:
                html_parts.append(flush_blockquote())
            html_parts.append('<hr>\n')
            i += 1
            continue

        # ── 表格 ──
        if line.strip().startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s\-|:]+\|$', lines[i+1].strip()):
            if in_list:
                html_parts.append(flush_list())
            if in_blockquote:
                html_parts.append(flush_blockquote())
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            html_parts.append(parse_table(table_lines))
            continue

        # ── 标题 ──
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            if in_list:
                html_parts.append(flush_list())
            if in_blockquote:
                html_parts.append(flush_blockquote())
            level = len(heading_match.group(1))
            title_text = heading_match.group(2).strip()
            clean_title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title_text).strip()
            # 提取报告标题和日期
            if level == 1:
                report_title = re.sub(r'[🔴🟠🟡🟢⚠️🔐🛡️]', '', title_text).strip()
            if level == 2 and re.search(r'\d{4}年\d{1,2}月\d{1,2}日', title_text):
                m = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', title_text)
                if m:
                    report_date = m.group(1)
            anchor = re.sub(r'\s+', '-', clean_title.lower())
            rendered = render_inline(escape_html(title_text))
            html_parts.append(f'<h{level} id="{anchor}">{rendered}</h{level}>\n')
            i += 1
            continue

        # ── 引用块 ──
        if line.startswith('>'):
            if in_list:
                html_parts.append(flush_list())
            in_blockquote = True
            blockquote_lines.append(line[1:].strip())
            i += 1
            continue
        elif in_blockquote and line.strip() == '':
            html_parts.append(flush_blockquote())
            i += 1
            continue
        elif in_blockquote:
            html_parts.append(flush_blockquote())

        # ── 无序列表 ──
        ul_match = re.match(r'^(\s*)[-*+]\s+(.*)', line)
        if ul_match:
            if in_list and list_type == 'ol':
                html_parts.append(flush_list())
            in_list = True
            list_type = 'ul'
            list_items.append(ul_match.group(2).strip())
            i += 1
            continue

        # ── 有序列表 ──
        ol_match = re.match(r'^(\s*)\d+\.\s+(.*)', line)
        if ol_match:
            if in_list and list_type == 'ul':
                html_parts.append(flush_list())
            in_list = True
            list_type = 'ol'
            list_items.append(ol_match.group(2).strip())
            i += 1
            continue

        # ── 空行 / 段落分隔 ──
        if line.strip() == '':
            if in_list:
                html_parts.append(flush_list())
            if in_blockquote:
                html_parts.append(flush_blockquote())
            html_parts.append('<br>\n')
            i += 1
            continue

        # ── 普通段落 ──
        if in_list:
            html_parts.append(flush_list())
        if in_blockquote:
            html_parts.append(flush_blockquote())
        html_parts.append(f'<p>{render_inline(escape_html(line.strip()))}</p>\n')
        i += 1

    # 收尾
    if in_list:
        html_parts.append(flush_list())
    if in_blockquote:
        html_parts.append(flush_blockquote())
    if in_code_block and code_lines:
        html_parts.append(f'<pre><code>{escape_html(chr(10).join(code_lines))}</code></pre>\n')

    return ''.join(html_parts), report_title, report_date


# ─── HTML 页面模板 ──────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei',
               'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
  line-height: 1.7;
  padding: 20px;
  font-size: 15px;
}
.page-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

/* ── 页头 ── */
.report-header {
  background: linear-gradient(135deg, #c0392b 0%, #8e1a12 100%);
  color: white;
  border-radius: 14px;
  padding: 30px 36px 28px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(192,57,43,0.35);
  position: relative;
  overflow: hidden;
}
.report-header::before {
  content: '';
  position: absolute;
  top: -30px; right: -30px;
  width: 200px; height: 200px;
  background: rgba(255,255,255,0.06);
  border-radius: 50%;
}
.report-header h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 8px;
  position: relative;
}
.report-header .meta {
  font-size: 13px;
  opacity: 0.85;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.tlp-badge {
  display: inline-block;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.4);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
}

/* ── 目录 ── */
.toc-card {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.07);
  border-left: 4px solid #c0392b;
}
.toc-card h2 { font-size: 15px; color: #666; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; border: none; }
.toc-list { list-style: none; }
.toc-list li { padding: 4px 0; }
.toc-list a { color: #c0392b; text-decoration: none; font-size: 14px; }
.toc-list a:hover { text-decoration: underline; }

/* ── 内容卡片 ── */
.content-card {
  background: white;
  border-radius: 12px;
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.07);
}

/* ── 标题层级 ── */
h1 { font-size: 22px; color: #1a1a2e; margin: 20px 0 12px; }
h2 {
  font-size: 18px; color: #1a1a2e;
  border-bottom: 2px solid #f0f2f5;
  padding-bottom: 10px;
  margin: 20px 0 14px;
  display: flex; align-items: center; gap: 8px;
}
h3 { font-size: 15px; color: #374151; margin: 16px 0 10px; }
h4 { font-size: 14px; color: #4b5563; margin: 12px 0 8px; }
h5, h6 { font-size: 13px; color: #6b7280; margin: 10px 0 6px; }

/* ── 段落与内联 ── */
p { margin-bottom: 10px; color: #374151; }
strong { color: #1a1a2e; }
em { color: #6b7280; }
a { color: #c0392b; text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  background: #f3f4f6;
  color: #dc2626;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'JetBrains Mono', Consolas, monospace;
  font-size: 13px;
}
pre {
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 16px 20px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.6;
}
pre code { background: none; color: inherit; padding: 0; }

/* ── 列表 ── */
.md-list {
  padding-left: 22px;
  margin: 8px 0 12px;
  color: #374151;
}
.md-list li {
  margin-bottom: 6px;
  line-height: 1.65;
}

/* ── 表格 ── */
.table-wrapper { overflow-x: auto; margin: 12px 0 16px; border-radius: 8px; border: 1px solid #e5e7eb; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead { background: #fef2f2; }
th {
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  color: #991b1b;
  border-bottom: 2px solid #fecaca;
  white-space: nowrap;
}
td {
  padding: 9px 14px;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fafafa; }

/* ── 分隔线 ── */
hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 20px 0;
}

/* ── 引用块 ── */
blockquote {
  border-left: 4px solid #fca5a5;
  background: #fef2f2;
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  margin: 12px 0;
  color: #6b7280;
  font-size: 14px;
}

/* ── 徽章 ── */
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.badge-critical { background: #fee2e2; color: #991b1b; }
.badge-high     { background: #ffedd5; color: #9a3412; }
.badge-medium   { background: #fef9c3; color: #854d0e; }
.badge-low      { background: #dcfce7; color: #166534; }
.cve-badge {
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  font-family: monospace;
  border: 1px solid #fde68a;
}

/* ── 页脚 ── */
.report-footer {
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
  padding: 20px 0 10px;
}
.report-footer a { color: #9ca3af; }

/* ── 打印 ── */
@media print {
  body { background: white; padding: 0; }
  .content-card { box-shadow: none; border: 1px solid #e5e7eb; }
  .report-header { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""


def build_toc(html_body: str) -> str:
    """从 h2 标题构建目录"""
    headings = re.findall(r'<h2[^>]*id="([^"]*)"[^>]*>(.*?)</h2>', html_body)
    if not headings:
        return ''
    items = ''
    for anchor, text in headings:
        clean = re.sub(r'<[^>]+>', '', text)
        items += f'<li><a href="#{anchor}">{clean}</a></li>\n'
    return f'''<div class="toc-card">
  <h2>📋 目录</h2>
  <ul class="toc-list">
    {items}
  </ul>
</div>
'''


def build_full_html(md_text: str, source_file: str = '') -> str:
    """构建完整 HTML 页面"""
    body_html, title, report_date = md_to_html_body(md_text)
    toc = build_toc(body_html)
    gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(title)} — {report_date}</title>
  <style>
{CSS}
  </style>
</head>
<body>
<div class="page-wrapper">

  <div class="report-header">
    <h1>🔴 {escape_html(title)}</h1>
    <div class="meta">
      <span>📅 {report_date}</span>
      <span class="tlp-badge">TLP: WHITE</span>
      <span>⏱ 生成时间：{gen_time}</span>
    </div>
  </div>

  {toc}

  <div class="content-card">
    {body_html}
  </div>

  <div class="report-footer">
    <p>TLP: WHITE — 本报告可自由分享 &nbsp;|&nbsp; 数据来源：自动化抓取 + AI 分析整合</p>
    <p>报告生成时间：{gen_time}</p>
  </div>

</div>
</body>
</html>
"""


# ─── 入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='将威胁情报日报 Markdown 转为 HTML')
    parser.add_argument('input', help='输入的 .md 文件路径')
    parser.add_argument('--output', '-o', help='输出 HTML 文件路径（默认与输入同名）')
    args = parser.parse_args()

    input_path = os.path.expanduser(args.input)
    if not os.path.exists(input_path):
        print(f'[ERROR] 输入文件不存在：{input_path}', file=sys.stderr)
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    html = build_full_html(md_text, source_file=input_path)

    if args.output:
        output_path = os.path.expanduser(args.output)
    else:
        output_path = re.sub(r'\.md$', '.html', input_path)
        if output_path == input_path:
            output_path = input_path + '.html'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'[OK] HTML 报告已生成：{output_path}')
    print(f'[INFO] 文件大小：{os.path.getsize(output_path):,} bytes')
    return output_path


if __name__ == '__main__':
    main()
