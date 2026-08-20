# -*- coding: utf-8 -*-
"""
轻量级代码语法高亮（纯 Python 无依赖，输出 inline 样式）
支持: python, javascript, json, html, css, shell/bash
若 pygments 已安装则使用 pygments 以获得更好效果。
"""

import re
import sys
from pathlib import Path

try:
    from .code_themes import get_code_theme
except ImportError:
    # 直接运行时修正 path
    _script_dir = Path(__file__).resolve().parent
    if str(_script_dir) not in sys.path:
        sys.path.insert(0, str(_script_dir))
    from code_themes import get_code_theme


def _escape_html(s: str) -> str:
    if not s:
        return ''
    return (s.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _span(style_color: str, text: str) -> str:
    return f'<span style="color:{style_color}">{text}</span>'


def _highlight_py(code: str, colors: dict) -> str:
    """Python 语法高亮"""
    tokens = []
    # (triple-quoted strings) | (single-line comments) | (numbers) | (keywords)
    pattern = re.compile(
        r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
        r'|(#[^\n]*)'
        r'|(\b(?:0x[\da-fA-F]+|0o[0-7]+|0b[01]+|\d+\.?\d*(?:e[+-]?\d+)?[jJ]?)\b)'
        r'|(\b(?:def|class|if|elif|else|for|while|try|except|finally|with|'
        r'import|from|as|return|yield|pass|break|continue|and|or|not|in|is|'
        r'None|True|False|lambda|async|await|raise|global|nonlocal|del|print)\b)',
        re.MULTILINE,
    )
    last_idx = 0
    for m in pattern.finditer(code):
        if m.start() > last_idx:
            tokens.append(('d', code[last_idx:m.start()]))
        if m.group(1):
            tokens.append(('s', m.group(1)))
        elif m.group(2):
            tokens.append(('c', m.group(2)))
        elif m.group(3):
            tokens.append(('n', m.group(3)))
        elif m.group(4):
            tokens.append(('k', m.group(4)))
        last_idx = m.end()
    if last_idx < len(code):
        tokens.append(('d', code[last_idx:]))

    parts = []
    for ttype, val in tokens:
        if ttype == 's':
            parts.append(_span(colors.get('string', colors['default']), _escape_html(val)))
        elif ttype == 'c':
            parts.append(_span(colors.get('comment', colors['default']), _escape_html(val)))
        elif ttype == 'n':
            parts.append(_span(colors.get('number', colors['default']), _escape_html(val)))
        elif ttype == 'k':
            parts.append(_span(colors.get('keyword', colors['default']), _escape_html(val)))
        else:
            parts.append(_span(colors['default'], _escape_html(val)))
    return ''.join(parts)


def _highlight_js(code: str, colors: dict) -> str:
    """JavaScript/TypeScript 语法高亮"""
    tokens = []
    pattern = re.compile(
        r'(//[^\n]*|/\*[\s\S]*?\*/)'  # (1) comment
        r'|("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|`(?:[^`\\]|\\.)*`)'  # (2) string
        r'|(/(?:[^/\\]|\\.)+/[gimsuy]*)'  # (3) regex
        r'|(\b(?:0x[\da-fA-F]+|0o[0-7]+|0b[01]+|\d+\.?\d*(?:e[+-]?\d+)?)\b)'  # (4) number
        r'|(\b(?:const|let|var|function|return|if|else|for|while|do|switch|case|break|'
        r'continue|try|catch|finally|throw|new|class|extends|import|export|default|from|'
        r'async|await|typeof|instanceof|in|of|true|false|null|undefined|this|super|'
        r'delete|void|yield)\b)'  # (5) keyword
        r'|(\b([a-zA-Z_$][\w$]*)\s*(?=\())',  # (6) function call
        re.MULTILINE,
    )
    last_idx = 0
    for m in pattern.finditer(code):
        if m.start() > last_idx:
            tokens.append(('d', code[last_idx:m.start()]))
        if m.group(1):
            tokens.append(('c', m.group(1)))
        elif m.group(2):
            tokens.append(('s', m.group(2)))
        elif m.group(3):
            tokens.append(('r', m.group(3)))
        elif m.group(4):
            tokens.append(('n', m.group(4)))
        elif m.group(5):
            tokens.append(('k', m.group(5)))
        elif m.group(6):
            tokens.append(('f', m.group(6)))
        last_idx = m.end()
    if last_idx < len(code):
        tokens.append(('d', code[last_idx:]))

    parts = []
    for ttype, val in tokens:
        if ttype == 'c':
            parts.append(_span(colors.get('comment', colors['default']), _escape_html(val)))
        elif ttype == 's':
            parts.append(_span(colors.get('string', colors['default']), _escape_html(val)))
        elif ttype == 'r':
            parts.append(_span(colors.get('regex', colors['default']), _escape_html(val)))
        elif ttype == 'n':
            parts.append(_span(colors.get('number', colors['default']), _escape_html(val)))
        elif ttype == 'k':
            parts.append(_span(colors.get('keyword', colors['default']), _escape_html(val)))
        elif ttype == 'f':
            parts.append(_span(colors.get('function', colors['default']), _escape_html(val)))
        else:
            parts.append(_span(colors['default'], _escape_html(val)))
    return ''.join(parts)


def _highlight_json(code: str, colors: dict) -> str:
    """JSON 语法高亮"""
    parts = []
    pattern = re.compile(
        r'("(?:[^"\\]|\\.)*")(\s*:)?'  # string key/value + optional colon
        r'|(-?\d+\.?\d*(?:e[+-]?\d+)?)'  # number
        r'|\b(true|false|null)\b',  # keyword
        re.MULTILINE,
    )
    last_idx = 0
    for m in pattern.finditer(code):
        if m.start() > last_idx:
            parts.append(_span(colors['default'], _escape_html(code[last_idx:m.start()])))
        if m.group(1):
            # If followed by ':', it's a key (attr), otherwise a string value
            if m.group(2) and m.group(2).strip() == ':':
                parts.append(_span(colors.get('attr', colors['default']), _escape_html(m.group(1))))
                parts.append(_span(colors['default'], _escape_html(m.group(2))))
            else:
                parts.append(_span(colors.get('string', colors['default']), _escape_html(m.group(1))))
        elif m.group(3):
            parts.append(_span(colors.get('number', colors['default']), _escape_html(m.group(3))))
        elif m.group(4):
            parts.append(_span(colors.get('keyword', colors['default']), _escape_html(m.group(4))))
        last_idx = m.end()
    if last_idx < len(code):
        parts.append(_span(colors['default'], _escape_html(code[last_idx:])))
    return ''.join(parts)


def _highlight_html(code: str, colors: dict) -> str:
    """HTML/XML 语法高亮"""
    parts = []
    pattern = re.compile(
        r'(<!--[\s\S]*?-->)'  # (1) comment
        r'|(</?[a-zA-Z][a-zA-Z0-9]*\b)'  # (2) tag
        r'|([a-zA-Z-]+)=|("[^"]*"|\'[^\']*\')',  # (3) attr name + (4) attr value
        re.MULTILINE,
    )
    last_idx = 0
    for m in pattern.finditer(code):
        if m.start() > last_idx:
            parts.append(_span(colors['default'], _escape_html(code[last_idx:m.start()])))
        if m.group(1):
            parts.append(_span(colors.get('comment', colors['default']), _escape_html(m.group(1))))
        elif m.group(2):
            parts.append(_span(colors.get('tag', colors['default']), _escape_html(m.group(2))))
        elif m.group(3):
            parts.append(_span(colors.get('attr', colors['default']), _escape_html(m.group(3) + '=')))
        elif m.group(4):
            parts.append(_span(colors.get('string', colors['default']), _escape_html(m.group(4))))
        last_idx = m.end()
    if last_idx < len(code):
        parts.append(_span(colors['default'], _escape_html(code[last_idx:])))
    return ''.join(parts)


def _highlight_css(code: str, colors: dict) -> str:
    """CSS 语法高亮"""
    parts = []
    pattern = re.compile(
        r'(/\*[\s\S]*?\*/)'  # (1) comment
        r'|("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'  # (2) string
        r'|([.#]?[a-zA-Z_-][a-zA-Z0-9_-]*)\s*\{'  # (3) selector
        r'|([a-zA-Z-]+)\s*:'  # (4) property
        r'|(#[a-fA-F0-9]{3,8}|rgba?\([^)]+\)|\d+\.?\d*(?:px|%|em|rem|pt|vh|vw|s)?)',  # (5) value
        re.MULTILINE,
    )
    last_idx = 0
    for m in pattern.finditer(code):
        if m.start() > last_idx:
            parts.append(_span(colors['default'], _escape_html(code[last_idx:m.start()])))
        if m.group(1):
            parts.append(_span(colors.get('comment', colors['default']), _escape_html(m.group(1))))
        elif m.group(2):
            parts.append(_span(colors.get('string', colors['default']), _escape_html(m.group(2))))
        elif m.group(3):
            parts.append(_span(colors.get('tag', colors['default']), _escape_html(m.group(3))))
            parts.append(_span(colors['default'], ' {'))
        elif m.group(4):
            parts.append(_span(colors.get('attr', colors['default']), _escape_html(m.group(4))))
            parts.append(_span(colors['default'], ': '))
        elif m.group(5):
            parts.append(_span(colors.get('number', colors['default']), _escape_html(m.group(5))))
        last_idx = m.end()
    if last_idx < len(code):
        parts.append(_span(colors['default'], _escape_html(code[last_idx:])))
    return ''.join(parts)


def _highlight_bash(code: str, colors: dict) -> str:
    """Bash/Shell 语法高亮"""
    parts = []
    pattern = re.compile(
        r'(^#![^\n]*|#[^\n]*)'  # (1) shebang/comment
        r'|("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'  # (2) string
        r'|(\b(?:if|then|else|elif|fi|for|do|done|while|until|case|esac|'
        r'function|return|export|source|break|continue|in|select|time|'
        r'read|echo|exit|set|unset|declare|typeset|local)\b)'  # (3) keyword
        r'|(\$[a-zA-Z_][a-zA-Z0-9_]*|\$\{[^}]+\})',  # (4) variable
        re.MULTILINE,
    )
    last_idx = 0
    for m in pattern.finditer(code):
        if m.start() > last_idx:
            parts.append(_span(colors['default'], _escape_html(code[last_idx:m.start()])))
        if m.group(1):
            parts.append(_span(colors.get('comment', colors['default']), _escape_html(m.group(1))))
        elif m.group(2):
            parts.append(_span(colors.get('string', colors['default']), _escape_html(m.group(2))))
        elif m.group(3):
            parts.append(_span(colors.get('keyword', colors['default']), _escape_html(m.group(3))))
        elif m.group(4):
            parts.append(_span(colors.get('param', colors['default']), _escape_html(m.group(4))))
        last_idx = m.end()
    if last_idx < len(code):
        parts.append(_span(colors['default'], _escape_html(code[last_idx:])))
    return ''.join(parts)


# Lang -> highlighter function mapping
_HIGHLIGHTERS = {
    'python': _highlight_py,
    'py': _highlight_py,
    'javascript': _highlight_js,
    'js': _highlight_js,
    'typescript': _highlight_js,
    'ts': _highlight_js,
    'json': _highlight_json,
    'html': _highlight_html,
    'xml': _highlight_html,
    'css': _highlight_css,
    'bash': _highlight_bash,
    'shell': _highlight_bash,
    'sh': _highlight_bash,
    'java': _highlight_js,
    'go': _highlight_js,
    'sql': _highlight_js,
    'php': _highlight_js,
}

# Try to use pygments if available for better highlighting
_USE_PYGMENTS = False
_PYGMENTS_AVAILABLE = False
try:
    import pygments
    import pygments.lexers
    import pygments.formatters
    _PYGMENTS_AVAILABLE = True
    _USE_PYGMENTS = True
except ImportError:
    pass


def _pygments_highlight(code: str, lang: str, colors: dict, theme: dict) -> str:
    """使用 pygments 进行高亮，用自定义内联样式"""
    try:
        from pygments.lexers import get_lexer_by_name
        from pygments.token import Token
    except ImportError:
        return None

    try:
        lexer = get_lexer_by_name(lang, stripall=False)
    except Exception:
        return None

    # Map pygments token types to our theme color keys
    token_color_map = {
        Token.Keyword: 'keyword',
        Token.Keyword.Type: 'keyword',
        Token.Keyword.Constant: 'keyword',
        Token.Keyword.Declaration: 'keyword',
        Token.Keyword.Namespace: 'keyword',
        Token.Keyword.Reserved: 'keyword',
        Token.Name.Builtin: 'keyword',
        Token.Name.Function: 'function',
        Token.Name.Class: 'function',
        Token.Name.Decorator: 'function',
        Token.Name.Tag: 'tag',
        Token.Name.Attribute: 'attr',
        Token.String: 'string',
        Token.String.Doc: 'string',
        Token.String.Single: 'string',
        Token.String.Double: 'string',
        Token.Number: 'number',
        Token.Number.Integer: 'number',
        Token.Number.Float: 'number',
        Token.Number.Hex: 'number',
        Token.Comment: 'comment',
        Token.Comment.Single: 'comment',
        Token.Comment.Multiline: 'comment',
        Token.Comment.Special: 'comment',
    }

    default_color = colors.get('default', '#d4d4d4')

    def get_color(ttype) -> str:
        for tok_type, color_key in token_color_map.items():
            if ttype in tok_type:
                return colors.get(color_key, default_color)
        return default_color

    parts = []
    try:
        tokens = list(lexer.get_tokens(code))
        for ttype, value in tokens:
            color = get_color(ttype)
            if ttype in Token.Comment or value == '\n':
                pass  # use color
            ev = _escape_html(value)
            if color != default_color:
                parts.append(_span(color, ev))
            else:
                parts.append(_span(default_color, ev))
    except Exception:
        return None

    return ''.join(parts)


def highlight(code: str, lang: str = '', code_theme_id: str = 'solarized-light') -> str:
    """语法高亮主函数

    Args:
        code: 源代码文本
        lang: 语言名称
        code_theme_id: 代码主题 ID

    Returns:
        带 inline style 的 HTML span 标签序列
    """
    if not code:
        return ''

    theme = get_code_theme(code_theme_id)
    colors = theme['colors']

    if _USE_PYGMENTS and _PYGMENTS_AVAILABLE:
        result = _pygments_highlight(code, lang, colors, theme)
        if result is not None:
            return result

    normal_lang = lang.lower().replace('lang', '', 1).lstrip('-').strip() if lang else ''
    fn = _HIGHLIGHTERS.get(normal_lang)
    if fn:
        return fn(code, colors)

    # Fallback: just escape
    return _escape_html(code)
