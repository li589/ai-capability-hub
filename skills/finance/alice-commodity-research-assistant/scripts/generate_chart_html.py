#!/usr/bin/env python3
"""
generate_chart_html.py - 商品智研助手图表 HTML 报告生成器

扫描指定目录中的期货品种走势图 PNG 文件，使用 base64 内嵌生成一份可独立查看的 HTML 报告。
走势图按命名规则匹配：*_price.png / *_basis.png / *_forward_curve.png / *_sunk_capital.png / *_warehouse_receipt.png 等。

支持两种模式：
  1. 纯图片模式（默认）： -d <图片目录> -o <输出HTML> [-t <标题>]
  2. 文字+图片混排模式： -d <图片目录> -r <报告MD文件> -o <输出HTML> [-t <标题>]

依赖: Pillow (pip install Pillow)
"""

import argparse
import base64
import io
import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# ============================================================
# 走势图文件匹配规则（按后缀）
# ============================================================
CHART_PATTERNS = [
    ("price", "_price.png", "价格走势"),
    ("price", "_price_chart.png", "价格走势"),
    ("basis", "_basis.png", "基差走势"),
    ("basis", "_basis_chart.png", "基差走势"),
    ("forward_curve", "_forward_curve.png", "远期曲线"),
    ("sunk_capital", "_sunk_capital.png", "沉淀资金走势"),
    ("sunk_capital", "_sunk_capital_chart.png", "沉淀资金走势"),
    ("warehouse_receipt", "_warehouse_receipt.png", "注册仓单走势"),
    ("warehouse_receipt", "_warehouse_receipt_chart.png", "注册仓单走势"),
]

OUTPUT_WIDTH = 560
JPEG_QUALITY = 72

# ============================================================
# 图片查找与编码
# ============================================================

# CLI resolveUniqueTargetPath 在同名冲突时会自动加 ' (N)' 后缀（如 'cu_price (1).png'），
# 这会让按后缀的 glob 匹配（*_price.png）漏掉该文件，导致走势图不嵌入 HTML。
# 用它把文件名里的 ' (N)' 还原后再匹配。
_DUP_SUFFIX_RE = re.compile(r' \(\d+\)(?=\.[A-Za-z0-9]+$)')

def find_chart_images(directory):
    """扫描目录，按命名规则匹配走势图 PNG 文件，返回 dict: {key: (label, filepath)}

    兼容同名冲突自动加的 ' (N)' 后缀：'cu_price (1).png' 仍按 'cu_price.png' 匹配 _price.png 规则；
    多个同名副本（含/不含后缀）按修改时间取最新。
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return {}

    all_pngs = list(dir_path.glob("*.png"))
    found = {}
    for key, suffix, label in CHART_PATTERNS:
        candidates = [
            p for p in all_pngs
            if _DUP_SUFFIX_RE.sub('', p.name).endswith(suffix)
        ]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            found[key] = (label, candidates[0])
    return found


def encode_image(filepath):
    """读取 PNG，缩放到指定宽度，转为 JPEG base64"""
    img = Image.open(filepath)
    w, h = img.size
    new_h = int(h * OUTPUT_WIDTH / w)
    img_resized = img.resize((OUTPUT_WIDTH, new_h), Image.LANCZOS)
    if img_resized.mode in ("RGBA", "P"):
        img_resized = img_resized.convert("RGB")

    buf = io.BytesIO()
    img_resized.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buf.getvalue()).decode()


# ============================================================
# Markdown → HTML 转换
# ============================================================

def inline_format(text):
    """处理行内格式：**加粗**、*斜体*、`行内代码`、链接、删除 markdown 图片引用"""
    # 删除 ![...](...) 图片引用（后面会用 base64 内嵌替换）
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # 行内代码（放在最前面，防干扰）
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 加粗
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体（不匹配已处理的加粗）
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # 链接
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    return text


def markdown_sections_to_html(preamble_lines, sections):
    """
    将序言行 + section 列表转为 HTML。

    sections: [(section_header, content_lines), ...]
      其中第一个元素可能是 ('', preamble) 表示序言部分

    返回 HTML 字符串。
    """
    html_parts = []

    for header, content in sections:
        if not header:
            # 序言/非 ## 部分
            html_parts.append(_render_block(content, heading_rendered=False))
        else:
            # Section header（去掉开头的 ## ）
            clean_header = re.sub(r'^#{2,}\s*', '', header)
            html_parts.append(f'<h2 class="section-title">{inline_format(clean_header)}</h2>')
            html_parts.append(_render_block(content, heading_rendered=True))

    return '\n'.join(html_parts)


def _render_block(lines, charts=None):
    """将一组行渲染为 HTML。charts 参数用于原地替换 `![...](/project/*.png)` 引用。"""
    if charts is None:
        charts = {}
    parts = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # 空行
        if not line.strip():
            i += 1
            continue

        stripped = line.strip()

        # 🔴 图片引用行（原地替换为 base64 图表，保持精确位置）
        img_block = _try_render_chart_line(stripped, charts)
        if img_block:
            parts.append(img_block)
            i += 1
            continue
        # 若为 ![...](...) 引用但无匹配图表，则跳过该行（避免无限循环）
        if re.match(r'^!\[.*?\]\(.+?\)\s*$', stripped):
            i += 1
            continue

        # --- 分割线
        if re.match(r'^---\s*$', stripped):
            parts.append('<hr>')
            i += 1
            continue

        # # / ## / ### / #### 标题（H1–H6）
        m_sub = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m_sub:
            level = min(len(m_sub.group(1)), 6)
            parts.append(f'<h{level}>{inline_format(m_sub.group(2))}</h{level}>')
            i += 1
            continue

        # 引用块
        if stripped.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            quote_text = ' '.join(quote_lines)
            parts.append(f'<blockquote>{inline_format(quote_text)}</blockquote>')
            continue

        # 无序列表
        if re.match(r'^[-*+]\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^[-*+]\s+', lines[i].strip()):
                item_text = re.sub(r'^[-*+]\s+', '', lines[i].strip())
                items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            parts.append(f'<ul>{"".join(items)}</ul>')
            continue

        # 有序列表
        if re.match(r'^\d+[\.\、]\s*', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+[\.\、]\s*', lines[i].strip()):
                item_text = re.sub(r'^\d+[\.\、]\s*', '', lines[i].strip())
                items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            parts.append(f'<ol>{"".join(items)}</ol>')
            continue

        # 段落：收集连续的非特殊行
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1

        if para_lines:
            para_text = ' '.join(para_lines)
            parts.append(f'<p>{inline_format(para_text)}</p>')

    return '\n'.join(parts)


# 图片引用行正则：兼容三种形式（取 URL 末尾文件名按 CHART_PATTERNS 匹配）
#   ![alt](/project/xxx.png)              服务端原始引用
#   ![alt](file:///.../xxx.png) (路径)   CLI sanitize 内联后的引用（含可选尾随 (绝对路径)）
#   ![alt](xxx.png)                       裸相对引用
_IMG_LINE_RE = re.compile(r'^!\[(.*?)\]\(([^)]+\.png)\)\s*(?:\([^)]*\))?\s*$')


def _chart_filename_from_url(url):
    """从图片 URL（/project/x.png、file:///.../x.png、x.png 均可）取末尾文件名，去掉 ' (N)' 后缀。"""
    fn = re.split(r'[/\\]', url)[-1]
    return _DUP_SUFFIX_RE.sub('', fn)


def _try_render_chart_line(line, charts):
    """如果是图片引用行（/project/、file:///、裸路径三种形式皆可），返回对应的 base64 图表 HTML；否则返回 None。"""
    m = _IMG_LINE_RE.match(line.strip())
    if not m:
        return None

    alt_text = m.group(1)
    filename = _chart_filename_from_url(m.group(2))  # e.g., "cu_price.png"
    # 匹配 CHART_PATTERNS 中的 key
    for key, suffix, label in CHART_PATTERNS:
        if filename.endswith(suffix) and key in charts:
            _, filepath = charts[key]
            b64 = encode_image(filepath)
            cap = alt_text or label
            return (
                f'<div class="chart-container">\n'
                f'  <img src="data:image/jpeg;base64,{b64}" alt="{cap}">\n'
                f'  <div class="caption">{cap}</div>\n'
                f'</div>'
            )
    # 未匹配到走势图（如本地无对应文件）：静默跳过
    return None


def _is_block_start(line):
    """判断一行是否为新块的起始。"""
    return (
        line.startswith('#')
        or line.startswith('>')
        or line.startswith('---')
        or line.startswith('![')     # 图片引用行（原地替换为图表）
        or re.match(r'^[-*+]\s+', line)
        or re.match(r'^\d+[\.\、]\s*', line)
    )


def parse_sections(text):
    """
    按 ## 标题拆分为 section 列表。

    返回: [(section_header, content_lines), ...]
      第一个元素可能是 ('', preamble_lines) 表示序言（第一个 ## 之前的内容）
    """
    sections = []
    lines = text.split('\n')
    current_header = None
    current_content = []
    preamble_lines = []

    for line in lines:
        if line.strip().startswith('## '):
            # 保存上一个 section
            if current_header is not None:
                sections.append((current_header, current_content))
            elif preamble_lines:
                sections.append(('', preamble_lines))
                preamble_lines = []

            current_header = line.strip()
            current_content = []
        elif current_header is not None:
            current_content.append(line)
        else:
            preamble_lines.append(line)

    # 保存最后一个 section
    if current_header is not None:
        sections.append((current_header, current_content))
    elif preamble_lines:
        sections.append(('', preamble_lines))

    return sections


# ============================================================
# HTML 生成：纯图片模式（向后兼容）
# ============================================================

def generate_html_images_only(charts, title):
    """纯图片模式：只输出走势图，不包含文字"""
    html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #ffffff;
    color: #1a1a2e;
    line-height: 1.8;
    padding: 32px 20px;
    max-width: 900px;
    margin: 0 auto;
  }}
  h1 {{
    font-size: 26px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
  }}
  .date {{
    text-align: center;
    color: #888;
    font-size: 13px;
    margin-bottom: 28px;
  }}
  .chart-container {{
    margin: 20px 0;
    text-align: center;
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
  }}
  .chart-container img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
  }}
  .chart-container .caption {{
    font-size: 13px;
    color: #888;
    margin-top: 8px;
  }}
  .footer {{
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
    text-align: center;
    color: #aaa;
    font-size: 12px;
  }}
</style>
</head>
<body>

<h1>{title}</h1>
<div class="date">走势图总览</div>
"""]

    for key, (label, filepath) in charts.items():
        b64 = encode_image(filepath)
        html_parts.append(f"""
<div class="chart-container">
  <img src="data:image/jpeg;base64,{b64}" alt="{label}">
  <div class="caption">{label}</div>
</div>
""")

    html_parts.append("""
<div class="footer">商品智研助手生成</div>

</body>
</html>
""")
    return '\n'.join(html_parts)


# ============================================================
# HTML 生成：文字+图片混排模式
# ============================================================

def generate_html_with_report(report_text, charts, title):
    """文字+图片混排模式：按章节渲染，`![...](/project/*.png)` 引用原地替换为 base64 走势图"""

    sections = parse_sections(report_text)

    # 生成 HTML
    style = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #ffffff;
    color: #1a1a2e;
    line-height: 1.9;
    padding: 32px 20px 48px;
    max-width: 900px;
    margin: 0 auto;
  }
  h1 {
    font-size: 28px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 6px;
    color: #b22222;
  }
  h2.section-title {
    font-size: 20px;
    font-weight: 700;
    margin: 32px 0 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e8e8e8;
    color: #222;
  }
  h3 { font-size: 17px; font-weight: 700; margin: 20px 0 10px; color: #333; }
  h4 { font-size: 15px; font-weight: 600; margin: 16px 0 8px; color: #444; }
  h5, h6 { font-size: 14px; font-weight: 600; margin: 14px 0 6px; color: #555; }
  p { margin: 10px 0; font-size: 15px; text-align: justify; }
  strong { color: #b22222; }
  em { color: #555; }
  code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 13px;
    font-family: "SF Mono", "Cascadia Code", Consolas, monospace;
    color: #c7254e;
  }
  blockquote {
    margin: 12px 0;
    padding: 12px 18px;
    background: #fff8e1;
    border-left: 4px solid #ffc107;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
    color: #795548;
  }
  ul, ol { margin: 10px 0 10px 24px; font-size: 15px; }
  li { margin: 4px 0; }
  hr { border: none; border-top: 1px solid #eee; margin: 20px 0; }
  a { color: #1976d2; text-decoration: none; }
  a:hover { text-decoration: underline; }

  .chart-container {
    margin: 20px 0 28px;
    text-align: center;
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
  }
  .chart-container img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
  }
  .chart-container .caption {
    font-size: 13px;
    color: #999;
    margin-top: 8px;
  }
  .footer {
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
    text-align: center;
    color: #aaa;
    font-size: 12px;
  }
</style>
</head>
<body>
"""

    html_parts = [style.replace("__TITLE__", title)]

    # 逐 section 渲染（图片在 _render_block 中原地替换）
    for header, content in sections:
        if not header:
            # 序言：标题 + 一句话总结 + 声明
            _render_preamble(html_parts, content, title, charts)
        else:
            clean_header = re.sub(r'^#{2,}\s*', '', header)
            html_parts.append(f'<h2 class="section-title">{inline_format(clean_header)}</h2>')
            html_parts.append(_render_block(content, charts))

    html_parts.append("""
<div class="footer">商品智研助手生成 · 仅供参考，不构成投资建议</div>

</body>
</html>
""")
    return '\n'.join(html_parts)


def _render_preamble(html_parts, lines, title, charts):
    """渲染序言（标题 + 一句话总结 + 声明等），支持图表原地替换"""
    # 提取主标题（第一个 # 开头）
    for line in lines:
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m:
            html_parts.append(f'<h1>{inline_format(m.group(1))}</h1>')
            break
    else:
        html_parts.append(f'<h1>{title}</h1>')

    # 渲染其余序言行
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('# '):
            continue

        # 图片引用行
        img_block = _try_render_chart_line(stripped, charts)
        if img_block:
            html_parts.append(img_block)
            continue

        if stripped.startswith('#### '):
            html_parts.append(f'<h4>{inline_format(stripped[5:])}</h4>')
        elif stripped.startswith('>'):
            html_parts.append(
                f'<blockquote>{inline_format(stripped[1:].strip())}</blockquote>'
            )
        elif stripped == '---':
            html_parts.append('<hr>')
        else:
            html_parts.append(f'<p>{inline_format(stripped)}</p>')


# ============================================================
# 主入口
# ============================================================

def fix_project_refs(text, charts):
    """将 agentResult.value 中的 /project/xxx.png 引用替换为本地 file:/// 路径。
    匹配规则：![...](project/xxx.png) → [filename](file:///path) + 保留 alt 文字。
    若本地文件不存在则删除整行（避免展示破图引用）。
    """
    lines = text.split('\n')
    fixed_lines = []

    for line in lines:
        m = _IMG_LINE_RE.match(line.strip())
        if not m:
            fixed_lines.append(line)
            continue

        alt_text = m.group(1)
        filename = _chart_filename_from_url(m.group(2))

        # 按 CHART_PATTERNS 匹配本地文件
        matched_path = None
        for key, suffix, label in CHART_PATTERNS:
            if filename.endswith(suffix) and key in charts:
                _, filepath = charts[key]
                if filepath.is_file():
                    matched_path = filepath
                    break

        if matched_path:
            # 替换为 markdown 链接格式（可点击）
            abspath = str(matched_path).replace('\\', '/')
            fixed_lines.append(f'[{alt_text}](file:///{abspath}) ({matched_path})')
            print(f"[fix-refs] {filename} -> {matched_path}", file=sys.stderr)
        else:
            # 本地没有对应文件，删除该行（静默跳过）
            print(f"[fix-refs] {filename} 本地无文件，已删除该引用", file=sys.stderr)

    return '\n'.join(fixed_lines)


def main():
    parser = argparse.ArgumentParser(description="商品智研助手图表 HTML 报告生成器")
    parser.add_argument("-d", "--dir", required=True, help="图片所在目录")
    parser.add_argument("-o", "--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("-t", "--title", default="期货品种走势图",
                        help="报告标题 (默认: 期货品种走势图)")
    parser.add_argument("-r", "--report-text", default=None,
                        help="报告 Markdown 文本文件路径（可选；提供后生成文字+图片混排 HTML）")
    parser.add_argument("--text-output", default=None,
                        help="修复 /project/ 引用后的纯文本输出路径（可选；与 -r 配合使用，将 agentResult.value 中的图片引用替换为本地 file:/// 路径）")
    args = parser.parse_args()

    charts = find_chart_images(args.dir)
    if not charts:
        print(f"WARNING: No chart images found in {args.dir}", file=sys.stderr)
        sys.exit(2)

    print(f"[图表HTML] 找到 {len(charts)} 张走势图: {[c[0] for c in charts.values()]}")

    # 文字+图片混排模式
    if args.report_text:
        report_path = Path(args.report_text)
        if not report_path.is_file():
            print(f"ERROR: Report text file not found: {report_path}", file=sys.stderr)
            sys.exit(3)

        report_text = report_path.read_text(encoding="utf-8")
        html = generate_html_with_report(report_text, charts, args.title)
        print(f"[图表HTML] 文字+图片混排模式，已按 {len(charts)} 张走势图内嵌到对应章节")

        # 🔴 生成修复 /project/ 引用后的纯文本（供 Agent 交付正文用）
        if args.text_output:
            fixed_text = fix_project_refs(report_text, charts)
            text_out_path = Path(args.text_output)
            text_out_path.parent.mkdir(parents=True, exist_ok=True)
            text_out_path.write_text(fixed_text, encoding="utf-8")
            print(f"[fix-refs] 修复后纯文本已生成: {text_out_path} ({len(fixed_text)} chars)")
    else:
        # 纯图片模式（向后兼容）
        html = generate_html_images_only(charts, args.title)
        print(f"[图表HTML] 纯图片模式")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"[图表HTML] 报告已生成: {output_path} ({len(html)} bytes)")
    sys.exit(0)


if __name__ == "__main__":
    main()
