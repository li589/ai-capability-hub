#!/usr/bin/env python3
import argparse
import base64
import io
import re
import sys
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)
CHART_PATTERNS = [
    ("sentiment", "_sentiment.png", "情绪走势"),
    ("sentiment", "_sentiment_chart.png", "情绪走势"),
    ("view_distribution", "_view_distribution.png", "多空观点分布"),
    ("view_distribution", "_view_distribution_chart.png", "多空观点分布"),
    ("wind_score", "_wind_score.png", "Wind 评分走势"),
    ("wind_score", "_wind_score_chart.png", "Wind 评分走势"),
    ("price", "_price.png", "价格走势"),
    ("price", "_price_chart.png", "价格走势"),
    ("sentiment_trend", "_sentiment_trend.png", "情绪与价格走势对比"),
    ("sentiment_trend", "_sentiment_trend_chart.png", "情绪与价格走势对比"),
    ("quantity_stats", "_quantity_stats.png", "数量统计"),
]
OUTPUT_WIDTH = 560
JPEG_QUALITY = 72
_DUP_SUFFIX_RE = re.compile(r' \(\d+\)(?=\.[A-Za-z0-9]+$)')
_CSS = '*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#ffffff;color:#1a1a2e;line-height:1.9;padding:32px 20px 48px;max-width:900px;margin:0 auto}h1{font-size:28px;font-weight:700;text-align:center;margin-bottom:6px;color:#b22222}h2.section-title{font-size:20px;font-weight:700;margin:32px 0 14px;padding-bottom:8px;border-bottom:2px solid #e8e8e8;color:#222}h3{font-size:17px;font-weight:700;margin:20px 0 10px;color:#333}h4{font-size:15px;font-weight:600;margin:16px 0 8px;color:#444}h5,h6{font-size:14px;font-weight:600;margin:14px 0 6px;color:#555}p{margin:10px 0;font-size:15px;text-align:justify}strong{color:#b22222}em{color:#555}code{background:#f5f5f5;padding:2px 6px;border-radius:3px;font-size:13px;font-family:"SF Mono","Cascadia Code",Consolas,monospace;color:#c7254e}blockquote{margin:12px 0;padding:12px 18px;background:#fff8e1;border-left:4px solid #ffc107;border-radius:0 8px 8px 0;font-size:14px;color:#795548}ul,ol{margin:10px 0 10px 24px;font-size:15px}li{margin:4px 0}hr{border:none;border-top:1px solid #eee;margin:20px 0}a{color:#1976d2;text-decoration:none}a:hover{text-decoration:underline}.chart-container{margin:20px 0 28px;text-align:center;background:#fafafa;border:1px solid #e0e0e0;border-radius:12px;padding:16px}.chart-container img{max-width:100%;height:auto;border-radius:8px}.chart-container .caption{font-size:13px;color:#999;margin-top:8px}.footer{margin-top:48px;padding-top:16px;border-top:1px solid #e0e0e0;text-align:center;color:#aaa;font-size:12px}'
def find_chart_images(directory):
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return {}
    all_pngs = list(dir_path.glob("*.png"))
    found = {}
    for key, suffix, label in CHART_PATTERNS:
        bare_suffix = suffix.lstrip("_")
        candidates = [
            p for p in all_pngs
            if _DUP_SUFFIX_RE.sub('', p.name).endswith(suffix)
            or _DUP_SUFFIX_RE.sub('', p.name).endswith(bare_suffix)
        ]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            found[key] = (label, candidates[0])
    return found
def encode_image(filepath):
    img = Image.open(filepath)
    w, h = img.size
    new_h = int(h * OUTPUT_WIDTH / w)
    img_resized = img.resize((OUTPUT_WIDTH, new_h), Image.LANCZOS)
    if img_resized.mode in ("RGBA", "P"):
        img_resized = img_resized.convert("RGB")
    buf = io.BytesIO()
    img_resized.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buf.getvalue()).decode()
def inline_format(text):
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    return text
def _render_block(lines, charts=None):
    if charts is None:
        charts = {}
    parts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        stripped = line.strip()
        img_block = _try_render_chart_line(stripped, charts)
        if img_block:
            parts.append(img_block)
            i += 1
            continue
        if re.match(r'^!\[.*?\]\(.+?\)\s*$', stripped):
            i += 1
            continue
        if re.match(r'^---\s*$', stripped):
            parts.append('<hr>')
            i += 1
            continue
        m_sub = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m_sub:
            level = min(len(m_sub.group(1)), 6)
            parts.append(f'<h{level}>{inline_format(m_sub.group(2))}</h{level}>')
            i += 1
            continue
        if stripped.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            quote_text = ' '.join(quote_lines)
            parts.append(f'<blockquote>{inline_format(quote_text)}</blockquote>')
            continue
        if re.match(r'^[-*+]\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^[-*+]\s+', lines[i].strip()):
                item_text = re.sub(r'^[-*+]\s+', '', lines[i].strip())
                items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            parts.append(f'<ul>{"".join(items)}</ul>')
            continue
        if re.match(r'^\d+[\.\、]\s*', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+[\.\、]\s*', lines[i].strip()):
                item_text = re.sub(r'^\d+[\.\、]\s*', '', lines[i].strip())
                items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            parts.append(f'<ol>{"".join(items)}</ol>')
            continue
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            para_text = ' '.join(para_lines)
            parts.append(f'<p>{inline_format(para_text)}</p>')
    return '\n'.join(parts)
_IMG_LINE_RE = re.compile(r'^!\[(.*?)\]\(([^)]+\.png)\)\s*(?:\([^)]*\))?\s*$')
def _chart_filename_from_url(url):
    fn = re.split(r'[/\\]', url)[-1]
    return _DUP_SUFFIX_RE.sub('', fn)
def _try_render_chart_line(line, charts):
    m = _IMG_LINE_RE.match(line.strip())
    if not m:
        return None
    alt_text = m.group(1)
    filename = _chart_filename_from_url(m.group(2))
    for key, suffix, label in CHART_PATTERNS:
        bare_suffix = suffix.lstrip("_")
        if (filename.endswith(suffix) or filename.endswith(bare_suffix)) and key in charts:
            _, filepath = charts[key]
            b64 = encode_image(filepath)
            cap = alt_text or label
            return (
                f'<div class="chart-container">\n'
                f'  <img src="data:image/jpeg;base64,{b64}" alt="{cap}">\n'
                f'  <div class="caption">{cap}</div>\n'
                f'</div>'
            )
    return None
def _is_block_start(line):
    return (
        line.startswith('#')
        or line.startswith('>')
        or line.startswith('---')
        or line.startswith('![')
        or re.match(r'^[-*+]\s+', line)
        or re.match(r'^\d+[\.\、]\s*', line)
    )
def parse_sections(text):
    sections = []
    lines = text.split('\n')
    current_header = None
    current_content = []
    preamble_lines = []
    for line in lines:
        if line.strip().startswith('## '):
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
    if current_header is not None:
        sections.append((current_header, current_content))
    elif preamble_lines:
        sections.append(('', preamble_lines))
    return sections
def generate_html_images_only(charts, title):
    html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{_CSS}
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
<div class="footer">期货研报观点生成</div>

</body>
</html>
""")
    return '\n'.join(html_parts)
def generate_html_with_report(report_text, charts, title):
    sections = parse_sections(report_text)
    style = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<style>
__CSS__
</style>
</head>
<body>
"""
    html_parts = [style.replace("__TITLE__", title).replace("__CSS__", _CSS)]
    for header, content in sections:
        if not header:
            _render_preamble(html_parts, content, title, charts)
        else:
            clean_header = re.sub(r'^#{2,}\s*', '', header)
            html_parts.append(f'<h2 class="section-title">{inline_format(clean_header)}</h2>')
            html_parts.append(_render_block(content, charts))
    html_parts.append("""
<div class="footer">期货研报观点生成 · 仅供参考，不构成投资建议</div>

</body>
</html>
""")
    return '\n'.join(html_parts)
def _render_preamble(html_parts, lines, title, charts):
    for line in lines:
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m:
            html_parts.append(f'<h1>{inline_format(m.group(1))}</h1>')
            break
    else:
        html_parts.append(f'<h1>{title}</h1>')
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('# '):
            continue
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
def fix_project_refs(text, charts):
    lines = text.split('\n')
    fixed_lines = []
    for line in lines:
        m = _IMG_LINE_RE.match(line.strip())
        if not m:
            fixed_lines.append(line)
            continue
        alt_text = m.group(1)
        filename = _chart_filename_from_url(m.group(2))
        matched_path = None
        for key, suffix, label in CHART_PATTERNS:
            if filename.endswith(suffix) and key in charts:
                _, filepath = charts[key]
                if filepath.is_file():
                    matched_path = filepath
                    break
        if matched_path:
            abspath = str(matched_path).replace('\\', '/')
            fixed_lines.append(f'[{alt_text}](file:///{abspath}) ({matched_path})')
            print(f"[fix-refs] {filename} -> {matched_path}", file=sys.stderr)
        else:
            print(f"[fix-refs] {filename} 本地无文件，已删除该引用", file=sys.stderr)
    return '\n'.join(fixed_lines)
def main():
    parser = argparse.ArgumentParser(description="期货研报观点图表 HTML 报告生成器")
    parser.add_argument("-d", "--dir", required=True, help="图片所在目录")
    parser.add_argument("-o", "--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("-t", "--title", default="期货研报观点走势图",
                        help="报告标题 (默认: 期货研报观点走势图)")
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
    if args.report_text:
        report_path = Path(args.report_text)
        if not report_path.is_file():
            print(f"ERROR: Report text file not found: {report_path}", file=sys.stderr)
            sys.exit(3)
        report_text = report_path.read_text(encoding="utf-8")
        html = generate_html_with_report(report_text, charts, args.title)
        print(f"[图表HTML] 文字+图片混排模式，已按 {len(charts)} 张走势图内嵌到对应章节")
        if args.text_output:
            fixed_text = fix_project_refs(report_text, charts)
            text_out_path = Path(args.text_output)
            text_out_path.parent.mkdir(parents=True, exist_ok=True)
            text_out_path.write_text(fixed_text, encoding="utf-8")
            print(f"[fix-refs] 修复后纯文本已生成: {text_out_path} ({len(fixed_text)} chars)")
    else:
        html = generate_html_images_only(charts, args.title)
        print(f"[图表HTML] 纯图片模式")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"[图表HTML] 报告已生成: {output_path} ({len(html)} bytes)")
    sys.exit(0)
if __name__ == "__main__":
    main()
