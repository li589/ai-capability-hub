#!/usr/bin/env python3
"""
Markdown 转微信公众号 HTML 转换器（doocs/md 风格）

参考 doocs/md 项目的优秀设计，提供多种专业主题。

使用方法：
    python3 markdown_to_wechat_doocs.py --input article.md --output article.html --theme default
    
支持主题：
    - default: 默认主题（简洁优雅）
    - green: 绿意主题（清新自然）
    - purple: 紫色主题（优雅高贵）
    - orange: 橙心主题（温暖活力）
    - cyan: 青色主题（清爽专业）
"""

import os
import sys
import argparse
import re
import markdown


# doocs/md 风格的主题配置
THEMES = {
    "default": {
        "name": "默认主题",
        "primary": "#3f51b5",
        "text": "#2b2b2b",
        "text_light": "#595959",
        "bg_light": "#f8f9fa",
        "border": "#e0e0e0",
        "code_bg": "#f6f8fa",
        "quote_bg": "#f8f9fa",
        "quote_border": "#3f51b5",
    },
    "green": {
        "name": "绿意主题",
        "primary": "#3eaf7c",
        "text": "#2c3e50",
        "text_light": "#6c757d",
        "bg_light": "#f3f5f7",
        "border": "#eaecef",
        "code_bg": "#f3f5f7",
        "quote_bg": "#f3f5f7",
        "quote_border": "#3eaf7c",
    },
    "purple": {
        "name": "紫色主题",
        "primary": "#8e44ad",
        "text": "#2c3e50",
        "text_light": "#6c757d",
        "bg_light": "#f8f9fa",
        "border": "#e0e0e0",
        "code_bg": "#f8f9fa",
        "quote_bg": "#f8f9fa",
        "quote_border": "#8e44ad",
    },
    "orange": {
        "name": "橙心主题",
        "primary": "#ff6800",
        "text": "#2c3e50",
        "text_light": "#6c757d",
        "bg_light": "#fff8f0",
        "border": "#ffe4cc",
        "code_bg": "#fff8f0",
        "quote_bg": "#fff8f0",
        "quote_border": "#ff6800",
    },
    "cyan": {
        "name": "青色主题",
        "primary": "#00bcd4",
        "text": "#2c3e50",
        "text_light": "#6c757d",
        "bg_light": "#f0f9ff",
        "border": "#d1ecf1",
        "code_bg": "#f0f9ff",
        "quote_bg": "#f0f9ff",
        "quote_border": "#00bcd4",
    }
}


def get_theme(theme_name):
    """获取主题配置"""
    return THEMES.get(theme_name, THEMES["default"])


def markdown_to_html_doocs(markdown_text, theme_name="default"):
    """
    将 Markdown 转换为 doocs/md 风格的 HTML
    使用 markdown 库正确解析所有 Markdown 语法（包括表格）
    """
    theme = get_theme(theme_name)

    # 使用 markdown 库解析，支持表格、代码块、删除线等所有标准语法
    md = markdown.Markdown(
        extensions=[
            'tables',           # 表格支持
            'fenced_code',       # 代码块
            'codehilite',        # 代码高亮
            'nl2br',             # 换行转<br>
            'sane_lists',        # 智能列表
            'def_list',          # 定义列表
            'abbr',              # 缩写
        ]
    )
    html_body = md.convert(markdown_text)

    # 后处理：给生成的 HTML 标签注入微信友好的内联样式
    html_body = apply_wechat_styles(html_body, theme)

    return html_body


def apply_wechat_styles(html, theme):
    """
    给 HTML 标签注入微信内联样式（替换手写正则的逐行解析）
    """
    primary   = theme["primary"]
    text      = theme["text"]
    text_light= theme["text_light"]
    bg_light  = theme["bg_light"]
    border    = theme["border"]
    code_bg   = theme["code_bg"]
    quote_bg  = theme["quote_bg"]
    quote_border = theme["quote_border"]

    # ── 标题 ──────────────────────────────────────────────
    html = re.sub(r'<h1>', f'<h1 style="margin: 30px 8px 20px; padding:0; font-size:22px; font-weight:700; line-height:1.4; color:{text}; text-align:center;">', html)
    html = re.sub(r'<h2>', f'<h2 style="margin: 28px 8px 16px; padding:0 0 8px; font-size:20px; font-weight:600; line-height:1.4; color:{text}; border-bottom:2px solid {primary};">', html)
    html = re.sub(r'<h3>', f'<h3 style="margin: 24px 8px 12px; padding:0 0 0 12px; font-size:18px; font-weight:600; line-height:1.4; color:{text}; border-left:4px solid {primary};">', html)
    html = re.sub(r'<h4>', f'<h4 style="margin:20px 8px 10px; padding:0; font-size:16px; font-weight:600; line-height:1.4; color:{text};">', html)
    html = re.sub(r'<h5>', f'<h5 style="margin:18px 8px 8px; padding:0; font-size:15px; font-weight:600; line-height:1.4; color:{text};">', html)
    html = re.sub(r'<h6>', f'<h6 style="margin:16px 8px 8px; padding:0; font-size:14px; font-weight:600; line-height:1.4; color:{text_light};">', html)

    # ── 段落 ──────────────────────────────────────────────
    html = re.sub(r'<p>', f'<p style="margin: 12px 8px; font-size:15px; line-height:1.8; color:{text}; text-align:justify; word-wrap:break-word;">', html)

    # ── 强调 ──────────────────────────────────────────────
    # <strong> 橙色强调（和老罗风格一致）
    html = re.sub(r'<strong>', f'<strong style="color:{primary}; font-weight:600;">', html)
    # <em> 斜体
    html = re.sub(r'<em>', f'<em style="font-style:italic;">', html)
    # <del> 删除线
    html = re.sub(r'<del>', f'<del style="text-decoration:line-through; color:{text_light};">', html)

    # ── 行内代码 ──────────────────────────────────────────
    html = re.sub(r'<code>', f'<code style="padding:2px 6px; background:{code_bg}; border-radius:3px; color:{primary}; font-family:Consolas,Monaco,monospace; font-size:14px;">', html)

    # ── 代码块（pre）──────────────────────────────────────
    def wrap_pre(m):
        lang = ""
        code = m.group(1)
        # 提取语言
        lm = re.search(r'class="language-(\w+)"', code)
        if lm:
            lang = lm.group(1)
            code = re.sub(r'<span class="[^"]*">([^<]*)</span>', r'\1', code)  # 去掉高亮span
        return (
            f'<section style="margin:16px 8px; padding:16px; background:{code_bg}; '
            f'border-radius:6px; border:1px solid {border}; overflow-x:auto; '
            f'font-family:Consolas,Monaco,"Courier New",monospace;">'
            f'<code style="font-size:14px; line-height:1.7; color:{text};">{code}</code>'
            f'</section>'
        )
    html = re.sub(r'<pre><code[^>]*>(.*?)</code></pre>', wrap_pre, html, flags=re.DOTALL)

    # ── 引用 ──────────────────────────────────────────────
    def wrap_blockquote(m):
        inner = m.group(1)
        return (
            f'<blockquote style="margin:16px 8px; padding:12px 16px; '
            f'background:{quote_bg}; border-left:4px solid {quote_border}; '
            f'border-radius:0 4px 4px 0;">'
            f'{inner}'
            f'</blockquote>'
        )
    html = re.sub(r'<blockquote>(.*?)</blockquote>', wrap_blockquote, html, flags=re.DOTALL)

    # ── 无序列表 ──────────────────────────────────────────
    def wrap_ul(m):
        return (f'<ul style="margin:12px 8px; padding-left:28px; list-style-type:disc; '
                f'color:{text}; font-size:15px; line-height:1.8;">{m.group(1)}</ul>')
    html = re.sub(r'<ul>(.*?)</ul>', wrap_ul, html, flags=re.DOTALL)

    # ── 有序列表 ─────────────────────────────────────────
    def wrap_ol(m):
        return (f'<ol style="margin:12px 8px; padding-left:28px; list-style-type:decimal; '
                f'color:{text}; font-size:15px; line-height:1.8;">{m.group(1)}</ol>')
    html = re.sub(r'<ol>(.*?)</ol>', wrap_ol, html, flags=re.DOTALL)

    # ── 列表项 ────────────────────────────────────────────
    def wrap_li(m):
        return (f'<li style="margin:6px 0 6px 20px;">'
                f'<span style="color:{text}; font-size:15px; line-height:1.8;">'
                f'{m.group(1)}</span></li>')
    html = re.sub(r'<li>(.*?)</li>', wrap_li, html, flags=re.DOTALL)

    # ── 水平线 ───────────────────────────────────────────
    html = re.sub(r'<hr />', f'<hr style="margin:24px 8px; border:none; border-top:1px solid {border};" />', html)

    # ── 图片 ─────────────────────────────────────────────
    def wrap_img(m):
        src  = m.group(1)
        alt  = m.group(2)
        cap  = f'<p style="margin:10px 0 0; font-size:13px; line-height:1.6; color:{text_light}; font-style:italic; text-align:center;">▲ {alt}</p>' if alt else ''
        return (
            f'<section style="margin:24px 8px; text-align:center;">'
            f'<img src="{src}" alt="{alt}" style="max-width:100%; height:auto; border-radius:6px; display:inline-block;" />'
            f'{cap}'
            f'</section>'
        )
    html = re.sub(r'<img src="([^"]+)" alt="([^"]*)" />', wrap_img, html)

    # ── 链接 ─────────────────────────────────────────────
    def wrap_a(m):
        txt  = m.group(1)
        href = m.group(2)
        return f'<a href="{href}" style="color:{primary}; text-decoration:none; border-bottom:1px solid {primary};">{txt}</a>'
    html = re.sub(r'<a href="([^"]+)">([^<]+)</a>', wrap_a, html)

    # ── 表格（重点！之前手写正则完全缺失的功能）───────────
    def wrap_table(m):
        inner = m.group(1)
        header_row = re.search(r'<thead>(.*?)</thead>', inner, re.DOTALL)
        body_rows  = re.findall(r'<tbody>(.*?)</tbody>', inner, re.DOTALL)
        rows_html  = ""

        # 表头行
        if header_row:
            header_html = re.sub(r'<th>', f'<th style="padding:10px 12px; background:{primary}; color:#fff; font-size:14px; font-weight:600; border-bottom:2px solid {primary}; text-align:center;">', header_row.group(1))
            header_html = re.sub(r'</th>', '</th>', header_html)
            rows_html  += f'<thead style="background:{primary};"><tr>{header_html}</tr></thead>'

        # 表体行
        body_html = '\n'.join(body_rows)
        # 交替行背景色
        def stripe_row(match):
            cells = match.group(1)
            cells = re.sub(r'<td>', f'<td style="padding:10px 12px; font-size:14px; line-height:1.6; color:{text}; border-bottom:1px solid {border};">', cells)
            return f'<tr style="background:#fff;">{cells}</tr>'
        def stripe_row_alt(match):
            cells = match.group(1)
            cells = re.sub(r'<td>', f'<td style="padding:10px 12px; font-size:14px; line-height:1.6; color:{text}; border-bottom:1px solid {border};">', cells)
            return f'<tr style="background:{bg_light};">{cells}</tr>'

        body_rows_list = re.findall(r'<tr>(.*?)</tr>', body_html, re.DOTALL)
        striped_body = ""
        for idx, row in enumerate(body_rows_list):
            row_td = re.sub(r'<td>', f'<td style="padding:10px 12px; font-size:14px; line-height:1.6; color:{text}; border-bottom:1px solid {border};">', row)
            bg = bg_light if idx % 2 == 1 else "#fff"
            striped_body += f'<tr style="background:{bg};">{row_td}</tr>\n'

        rows_html += f'<tbody>{striped_body}</tbody>'

        return (
            f'<div style="margin:20px 8px; overflow-x:auto; border-radius:6px; '
            f'border:1px solid {border}; box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
            f'<table style="width:100%; border-collapse:collapse; font-size:14px;">'
            f'{rows_html}'
            f'</table></div>'
        )

    html = re.sub(r'<table>(.*?)</table>', wrap_table, html, flags=re.DOTALL)

    # ── 微信段落行距修复 ──────────────────────────────────
    html = html.replace('</li>\n<li', '</li><li')
    html = html.replace('</p>\n<p', '</p><p')

    return html


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="Markdown 转微信公众号 HTML 转换器（doocs/md 风格）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持主题：
  default  - 默认主题（简洁优雅）
  green    - 绿意主题（清新自然）
  purple   - 紫色主题（优雅高贵）
  orange   - 橙心主题（温暖活力）
  cyan     - 青色主题（清爽专业）
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入 Markdown 文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出 HTML 文件路径"
    )
    
    parser.add_argument(
        "--theme", "-t",
        choices=["default", "green", "purple", "orange", "cyan"],
        default="default",
        help="主题选择"
    )

    parser.add_argument(
        "--no-footer",
        action="store_true",
        help="禁用自动追加 footer（默认禁用，推荐手动复制footer内容到文章末尾）"
    )

    parser.add_argument(
        "--footer-simple",
        action="store_true",
        help="追加简化版 footer（纯微信标签，编辑不失效）"
    )

    args = parser.parse_args()

    try:
        # 读取 Markdown 文件
        with open(args.input, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        # footer 处理（默认禁用，推荐手动复制粘贴）
        footer_path = None
        if args.footer_simple:
            footer_path = os.path.join(os.path.dirname(__file__), '..', 'footer-simple.md')
        elif not args.no_footer:
            footer_path = os.path.join(os.path.dirname(__file__), '..', 'footer.md')

        if footer_path and os.path.exists(footer_path):
            with open(footer_path, 'r', encoding='utf-8') as f:
                footer_content = f.read()
            # 去掉 frontmatter (---...---)
            footer_content = re.sub(r'^---\n.*?\n---\n', '', footer_content, flags=re.DOTALL)
            if footer_content:
                markdown_text = markdown_text.rstrip() + '\n\n' + footer_content

        # 转换为 HTML
        html_content = markdown_to_html_doocs(markdown_text, args.theme)
        
        # 获取主题信息
        theme = get_theme(args.theme)
        
        # 包装在 section 中
        final_html = f'''<section style="padding: 16px; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;">
{html_content}
</section>'''
        
        # 写入 HTML 文件
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        # 打印结果
        footer_note = ""
        if args.footer_simple:
            footer_note = "（含简化版footer）"
        elif args.no_footer:
            footer_note = "（无footer，建议手动复制 footer-simple.md 到文章末尾）"
        else:
            footer_note = "（含原始footer）"

        print(f"✅ 转换成功！")
        print(f"   输入: {args.input}")
        print(f"   输出: {args.output}")
        print(f"   主题: {theme['name']}")
        print(f"   风格: doocs/md {footer_note}")
        if not args.footer_simple and not args.no_footer:
            print(f"   💡 提示: 推荐使用 --footer-simple 参数生成兼容微信编辑器的footer")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)




if __name__ == "__main__":
    main()
