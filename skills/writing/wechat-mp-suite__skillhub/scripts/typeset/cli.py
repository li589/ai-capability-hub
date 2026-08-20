#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 入口 — Markdown 转微信公众号 HTML 排版

用法:
    python cli.py input.md [--theme THEME] [--code-theme CODE_THEME] [-o OUTPUT]
    echo "markdown..." | python cli.py [--theme THEME] [-o OUTPUT]

选项:
    --theme, -t         主题 ID (lapis/forest/ocean/sunset/noir)，默认 lapis
    --code-theme, -c    代码高亮主题 (solarized-light/vscode-dark/github/monokai/one-dark)
    --output, -o        输出文件路径（默认 stdout）
    --list-themes, -L   列出所有可用主题
    --list-code-themes  列出所有代码主题
    --help, -h          显示帮助

环境变量:
    WECHAT_TYPESET_THEME        默认主题
    WECHAT_TYPESET_CODE_THEME   默认代码主题
"""

import argparse
import sys
import os
from pathlib import Path

try:
    from .typeset import md_to_wechat_html, get_full_html
    from .themes import list_themes, list_image_styles
    from .code_themes import list_code_themes
except ImportError:
    # 直接运行时修正 path
    _script_dir = Path(__file__).resolve().parent
    if str(_script_dir) not in sys.path:
        sys.path.insert(0, str(_script_dir))
    from typeset import md_to_wechat_html, get_full_html
    from themes import list_themes, list_image_styles
    from code_themes import list_code_themes


def resolve_theme_id(cli_theme: str = None) -> str:
    """优先级: CLI > 环境变量 > 默认值"""
    return cli_theme or os.environ.get('WECHAT_TYPESET_THEME', 'lapis')


def resolve_code_theme_id(cli_code_theme: str = None) -> str:
    """优先级: CLI > 环境变量 > 默认值"""
    return cli_code_theme or os.environ.get('WECHAT_TYPESET_CODE_THEME', 'solarized-light')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Markdown 转微信公众号 HTML 排版引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python -m scripts.typeset.cli article.md -o article.html\n'
            '  echo "# Hello" | python -m scripts.typeset.cli --theme ocean\n'
            '  python -m scripts.typeset.cli --list-themes\n'
        ),
    )
    parser.add_argument('input', nargs='?', metavar='FILE',
                        help='输入的 Markdown 文件路径（省略则从 stdin 读取）')
    parser.add_argument('--theme', '-t', metavar='THEME',
                        help='主题 ID (lapis/forest/ocean/sunset/noir)')
    parser.add_argument('--code-theme', '-c', metavar='CODE_THEME',
                        help='代码高亮主题 (solarized-light/vscode-dark/github/monokai/one-dark)')
    parser.add_argument('--output', '-o', metavar='FILE',
                        help='输出文件路径（默认输出到 stdout）')
    parser.add_argument('--full-html', '-f', action='store_true',
                        help='输出完整 HTML（含 section 包装，默认只输出 body）')
    parser.add_argument('--list-themes', '-L', action='store_true',
                        help='列出所有可用主题')
    parser.add_argument('--list-code-themes', action='store_true',
                        help='列出所有代码主题')
    return parser


def main(argv: list = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # 列出主题
    if args.list_themes:
        print('可用主题:')
        for t in list_themes():
            print(f'  {t["id"]:15s} — {t["name"]} ({t["desc"]})')
        return 0

    # 列出代码主题
    if args.list_code_themes:
        print('可用代码主题:')
        for t in list_code_themes():
            print(f'  {t["id"]:25s} — {t["name"]}')
        return 0

    # 读取输入
    content = ''
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f'错误: 文件不存在: {input_path}', file=sys.stderr)
            return 1
        try:
            content = input_path.read_text('utf-8')
        except Exception as e:
            print(f'错误: 读取文件失败: {e}', file=sys.stderr)
            return 1
    else:
        # 从 stdin 读取
        if sys.stdin.isatty():
            # 交互式终端，等待输入
            print('请粘贴 Markdown 内容（按 Ctrl+D 结束）:', file=sys.stderr)
        try:
            content = sys.stdin.read()
        except KeyboardInterrupt:
            print('\n已取消', file=sys.stderr)
            return 1

    if not content or not content.strip():
        print('错误: 无输入内容', file=sys.stderr)
        return 1

    # 解析选项
    theme_id = resolve_theme_id(args.theme)
    code_theme_id = resolve_code_theme_id(args.code_theme)

    try:
        if args.full_html:
            html = get_full_html(content, theme_id=theme_id, code_theme_id=code_theme_id)
        else:
            html = md_to_wechat_html(content, theme_id=theme_id, code_theme_id=code_theme_id)
    except Exception as e:
        print(f'错误: 排版失败: {e}', file=sys.stderr)
        return 1

    # 输出
    if args.output:
        try:
            output_path = Path(args.output)
            output_path.write_text(html, 'utf-8')
            print(f'✅ 排版完成: {output_path.resolve()}', file=sys.stderr)
        except Exception as e:
            print(f'错误: 写入文件失败: {e}', file=sys.stderr)
            return 1
    else:
        sys.stdout.write(html)
        if not html.endswith('\n'):
            sys.stdout.write('\n')

    return 0


if __name__ == '__main__':
    sys.exit(main())
