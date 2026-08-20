#!/usr/bin/env python3
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
    print('ERROR: Pillow not installed. Run: pip install Pillow', file=sys.stderr)
    sys.exit(1)
CHART_PATTERNS = [('correlation_heatmap', '_correlation_heatmap.png', '资产相关性热力图'), ('efficient_frontier', '_efficient_frontier.png', '有效前沿'), ('risk_contribution', '_risk_contribution.png', '风险贡献分解'), ('weight_pie', '_weight_pie.png', '资产权重分布')]
OUTPUT_WIDTH = 560
JPEG_QUALITY = 72
_DUP_SUFFIX_RE = re.compile(' \\(\\d+\\)(?=\\.[A-Za-z0-9]+$)')

def find_chart_images(directory):
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return {}
    all_pngs = list(dir_path.glob('*.png'))
    found = {}
    for key, suffix, label in CHART_PATTERNS:
        bare_suffix = suffix.lstrip('_')
        candidates = [p for p in all_pngs if _DUP_SUFFIX_RE.sub('', p.name).endswith(suffix) or _DUP_SUFFIX_RE.sub('', p.name).endswith(bare_suffix)]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            found[key] = (label, candidates[0])
    return found

def encode_image(filepath):
    img = Image.open(filepath)
    w, h = img.size
    new_h = int(h * OUTPUT_WIDTH / w)
    img_resized = img.resize((OUTPUT_WIDTH, new_h), Image.LANCZOS)
    if img_resized.mode in ('RGBA', 'P'):
        img_resized = img_resized.convert('RGB')
    buf = io.BytesIO()
    img_resized.save(buf, format='JPEG', quality=JPEG_QUALITY)
    return base64.b64encode(buf.getvalue()).decode()

def inline_format(text):
    text = re.sub('!\\[.*?\\]\\(.*?\\)', '', text)
    text = re.sub('`([^`]+)`', '<code>\\1</code>', text)
    text = re.sub('\\*\\*(.+?)\\*\\*', '<strong>\\1</strong>', text)
    text = re.sub('(?<!\\*)\\*(?!\\*)(.+?)(?<!\\*)\\*(?!\\*)', '<em>\\1</em>', text)
    text = re.sub('\\[([^\\]]+)\\]\\(([^)]+)\\)', '<a href="\\2" target="_blank">\\1</a>', text)
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
        if re.match('^!\\[.*?\\]\\(.+?\\)\\s*$', stripped):
            i += 1
            continue
        if re.match('^---\\s*$', stripped):
            parts.append('<hr>')
            i += 1
            continue
        m_sub = re.match('^(#{1,6})\\s+(.+)$', stripped)
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
        if re.match('^[-*+]\\s+', stripped):
            items = []
            while i < len(lines) and re.match('^[-*+]\\s+', lines[i].strip()):
                item_text = re.sub('^[-*+]\\s+', '', lines[i].strip())
                items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            parts.append(f"<ul>{''.join(items)}</ul>")
            continue
        if re.match('^\\d+[\\.\\、]\\s*', stripped):
            items = []
            while i < len(lines) and re.match('^\\d+[\\.\\、]\\s*', lines[i].strip()):
                item_text = re.sub('^\\d+[\\.\\、]\\s*', '', lines[i].strip())
                items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            parts.append(f"<ol>{''.join(items)}</ol>")
            continue
        para_lines = []
        while i < len(lines) and lines[i].strip() and (not _is_block_start(lines[i].strip())):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            para_text = ' '.join(para_lines)
            parts.append(f'<p>{inline_format(para_text)}</p>')
    return '\n'.join(parts)
_IMG_LINE_RE = re.compile('^!\\[(.*?)\\]\\(([^)]+\\.png)\\)\\s*(?:\\([^)]*\\))?\\s*$')

def _chart_filename_from_url(url):
    fn = re.split('[/\\\\]', url)[-1]
    return _DUP_SUFFIX_RE.sub('', fn)

def _try_render_chart_line(line, charts):
    m = _IMG_LINE_RE.match(line.strip())
    if not m:
        return None
    alt_text = m.group(1)
    filename = _chart_filename_from_url(m.group(2))
    for key, suffix, label in CHART_PATTERNS:
        bare_suffix = suffix.lstrip('_')
        if (filename.endswith(suffix) or filename.endswith(bare_suffix)) and key in charts:
            _, filepath = charts[key]
            b64 = encode_image(filepath)
            cap = alt_text or label
            return f'<div class="chart-container">\n  <img src="data:image/jpeg;base64,{b64}" alt="{cap}">\n  <div class="caption">{cap}</div>\n</div>'
    return None

def _is_block_start(line):
    return line.startswith('#') or line.startswith('>') or line.startswith('---') or line.startswith('![') or re.match('^[-*+]\\s+', line) or re.match('^\\d+[\\.\\、]\\s*', line)

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
    html_parts = [f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{title}</title>\n<style>\n  * {{ margin: 0; padding: 0; box-sizing: border-box; }}\n  body {{\n    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;\n    background: #ffffff;\n    color: #1a1a2e;\n    line-height: 1.8;\n    padding: 32px 20px;\n    max-width: 900px;\n    margin: 0 auto;\n  }}\n  h1 {{\n    font-size: 26px;\n    font-weight: 700;\n    text-align: center;\n    margin-bottom: 8px;\n  }}\n  .date {{\n    text-align: center;\n    color: #888;\n    font-size: 13px;\n    margin-bottom: 28px;\n  }}\n  .chart-container {{\n    margin: 20px 0;\n    text-align: center;\n    background: #fafafa;\n    border: 1px solid #e0e0e0;\n    border-radius: 12px;\n    padding: 16px;\n  }}\n  .chart-container img {{\n    max-width: 100%;\n    height: auto;\n    border-radius: 8px;\n  }}\n  .chart-container .caption {{\n    font-size: 13px;\n    color: #888;\n    margin-top: 8px;\n  }}\n  .footer {{\n    margin-top: 40px;\n    padding-top: 16px;\n    border-top: 1px solid #e0e0e0;\n    text-align: center;\n    color: #aaa;\n    font-size: 12px;\n  }}\n</style>\n</head>\n<body>\n\n<h1>{title}</h1>\n<div class="date">图表总览</div>\n']
    for key, (label, filepath) in charts.items():
        b64 = encode_image(filepath)
        html_parts.append(f'\n<div class="chart-container">\n  <img src="data:image/jpeg;base64,{b64}" alt="{label}">\n  <div class="caption">{label}</div>\n</div>\n')
    html_parts.append('\n<div class="footer">战略资产配置生成</div>\n\n</body>\n</html>\n')
    return '\n'.join(html_parts)

def generate_html_with_report(report_text, charts, title):
    sections = parse_sections(report_text)
    style = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>__TITLE__</title>\n<style>\n  * { margin: 0; padding: 0; box-sizing: border-box; }\n  body {\n    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;\n    background: #ffffff;\n    color: #1a1a2e;\n    line-height: 1.9;\n    padding: 32px 20px 48px;\n    max-width: 900px;\n    margin: 0 auto;\n  }\n  h1 {\n    font-size: 28px;\n    font-weight: 700;\n    text-align: center;\n    margin-bottom: 6px;\n    color: #b22222;\n  }\n  h2.section-title {\n    font-size: 20px;\n    font-weight: 700;\n    margin: 32px 0 14px;\n    padding-bottom: 8px;\n    border-bottom: 2px solid #e8e8e8;\n    color: #222;\n  }\n  h3 { font-size: 17px; font-weight: 700; margin: 20px 0 10px; color: #333; }\n  h4 { font-size: 15px; font-weight: 600; margin: 16px 0 8px; color: #444; }\n  h5, h6 { font-size: 14px; font-weight: 600; margin: 14px 0 6px; color: #555; }\n  p { margin: 10px 0; font-size: 15px; text-align: justify; }\n  strong { color: #b22222; }\n  em { color: #555; }\n  code {\n    background: #f5f5f5;\n    padding: 2px 6px;\n    border-radius: 3px;\n    font-size: 13px;\n    font-family: "SF Mono", "Cascadia Code", Consolas, monospace;\n    color: #c7254e;\n  }\n  blockquote {\n    margin: 12px 0;\n    padding: 12px 18px;\n    background: #fff8e1;\n    border-left: 4px solid #ffc107;\n    border-radius: 0 8px 8px 0;\n    font-size: 14px;\n    color: #795548;\n  }\n  ul, ol { margin: 10px 0 10px 24px; font-size: 15px; }\n  li { margin: 4px 0; }\n  hr { border: none; border-top: 1px solid #eee; margin: 20px 0; }\n  a { color: #1976d2; text-decoration: none; }\n  a:hover { text-decoration: underline; }\n\n  .chart-container {\n    margin: 20px 0 28px;\n    text-align: center;\n    background: #fafafa;\n    border: 1px solid #e0e0e0;\n    border-radius: 12px;\n    padding: 16px;\n  }\n  .chart-container img {\n    max-width: 100%;\n    height: auto;\n    border-radius: 8px;\n  }\n  .chart-container .caption {\n    font-size: 13px;\n    color: #999;\n    margin-top: 8px;\n  }\n  .footer {\n    margin-top: 48px;\n    padding-top: 16px;\n    border-top: 1px solid #e0e0e0;\n    text-align: center;\n    color: #aaa;\n    font-size: 12px;\n  }\n</style>\n</head>\n<body>\n'
    html_parts = [style.replace('__TITLE__', title)]
    for header, content in sections:
        if not header:
            _render_preamble(html_parts, content, title, charts)
        else:
            clean_header = re.sub('^#{2,}\\s*', '', header)
            html_parts.append(f'<h2 class="section-title">{inline_format(clean_header)}</h2>')
            html_parts.append(_render_block(content, charts))
    html_parts.append('\n<div class="footer">战略资产配置生成 · 仅供参考，不构成投资建议</div>\n\n</body>\n</html>\n')
    return '\n'.join(html_parts)

def _render_preamble(html_parts, lines, title, charts):
    for line in lines:
        m = re.match('^#\\s+(.+)$', line.strip())
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
            html_parts.append(f'<blockquote>{inline_format(stripped[1:].strip())}</blockquote>')
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
            print(f'[fix-refs] {filename} -> {matched_path}', file=sys.stderr)
        else:
            print(f'[fix-refs] {filename} 本地无文件，已删除该引用', file=sys.stderr)
    return '\n'.join(fixed_lines)

def main():
    parser = argparse.ArgumentParser(description='战略资产配置 (SAA) 图表 HTML 报告生成器')
    parser.add_argument('-d', '--dir', required=True, help='图片所在目录')
    parser.add_argument('-o', '--output', required=True, help='输出 HTML 文件路径')
    parser.add_argument('-t', '--title', default='战略资产配置图表', help='报告标题 (默认: 战略资产配置图表)')
    parser.add_argument('-r', '--report-text', default=None, help='报告 Markdown 文本文件路径（可选；提供后生成文字+图片混排 HTML）')
    parser.add_argument('--text-output', default=None, help='修复 /project/ 引用后的纯文本输出路径（可选；与 -r 配合使用，将 agentResult.value 中的图片引用替换为本地 file:/// 路径）')
    args = parser.parse_args()
    charts = find_chart_images(args.dir)
    if not charts:
        print(f'WARNING: No chart images found in {args.dir}', file=sys.stderr)
        sys.exit(2)
    print(f'[图表HTML] 找到 {len(charts)} 张图表: {[c[0] for c in charts.values()]}')
    if args.report_text:
        report_path = Path(args.report_text)
        if not report_path.is_file():
            print(f'ERROR: Report text file not found: {report_path}', file=sys.stderr)
            sys.exit(3)
        report_text = report_path.read_text(encoding='utf-8')
        html = generate_html_with_report(report_text, charts, args.title)
        print(f'[图表HTML] 文字+图片混排模式，已按 {len(charts)} 张图表内嵌到对应章节')
        if args.text_output:
            fixed_text = fix_project_refs(report_text, charts)
            text_out_path = Path(args.text_output)
            text_out_path.parent.mkdir(parents=True, exist_ok=True)
            text_out_path.write_text(fixed_text, encoding='utf-8')
            print(f'[fix-refs] 修复后纯文本已生成: {text_out_path} ({len(fixed_text)} chars)')
    else:
        html = generate_html_images_only(charts, args.title)
        print(f'[图表HTML] 纯图片模式')
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    print(f'[图表HTML] 报告已生成: {output_path} ({len(html)} bytes)')
    sys.exit(0)
if __name__ == '__main__':
    main()