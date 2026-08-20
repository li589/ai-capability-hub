# -*- coding: utf-8 -*-
"""
代码高亮主题（与文章主题独立，常见 IDE 风格）
用于语法高亮颜色 + 代码块背景、边框、语言标签颜色
"""

CODE_THEMES = [
    {
        'id': 'solarized-light',
        'name': 'Solarized Light',
        'colors': {
            'keyword': '#859900',
            'string': '#2aa198',
            'number': '#d33682',
            'comment': '#93a1a1',
            'function': '#268bd2',
            'regex': '#dc322f',
            'attr': '#b58900',
            'tag': '#268bd2',
            'param': '#657b83',
            'default': '#586e75',
        },
        'block': {
            'bg': '#fdf6e3',
            'border': '#eee8d5',
            'labelColor': '#93a1a1',
        },
    },
    {
        'id': 'vscode-dark',
        'name': 'VS Code Dark+',
        'colors': {
            'keyword': '#569cd6',
            'string': '#ce9178',
            'number': '#b5cea8',
            'comment': '#6a9955',
            'function': '#dcdcaa',
            'regex': '#d16969',
            'attr': '#9cdcfe',
            'tag': '#569cd6',
            'param': '#9cdcfe',
            'default': '#d4d4d4',
        },
        'block': {
            'bg': '#282c34',
            'border': '#3e4451',
            'labelColor': '#abb2bf',
        },
    },
    {
        'id': 'github',
        'name': 'GitHub',
        'colors': {
            'keyword': '#d73a49',
            'string': '#032f62',
            'number': '#005cc5',
            'comment': '#6a737d',
            'function': '#6f42c1',
            'regex': '#032f62',
            'attr': '#22863a',
            'tag': '#22863a',
            'param': '#005cc5',
            'default': '#24292e',
        },
        'block': {
            'bg': '#f6f8fa',
            'border': '#e1e4e8',
            'labelColor': '#6a737d',
        },
    },
    {
        'id': 'monokai',
        'name': 'Monokai',
        'colors': {
            'keyword': '#f92672',
            'string': '#e6db74',
            'number': '#ae81ff',
            'comment': '#75715e',
            'function': '#a6e22e',
            'regex': '#e6db74',
            'attr': '#a6e22e',
            'tag': '#f92672',
            'param': '#fd971f',
            'default': '#f8f8f2',
        },
        'block': {
            'bg': '#272822',
            'border': '#49483e',
            'labelColor': '#75715e',
        },
    },
    {
        'id': 'one-dark',
        'name': 'One Dark',
        'colors': {
            'keyword': '#c678dd',
            'string': '#98c379',
            'number': '#d19a66',
            'comment': '#5c6370',
            'function': '#61afef',
            'regex': '#56b6c2',
            'attr': '#e06c75',
            'tag': '#e06c75',
            'param': '#61afef',
            'default': '#abb2bf',
        },
        'block': {
            'bg': '#282c34',
            'border': '#3e4451',
            'labelColor': '#5c6370',
        },
    },
]


def get_code_theme(theme_id: str = 'solarized-light') -> dict:
    """获取代码主题配置，找不到则返回 solarized-light"""
    for t in CODE_THEMES:
        if t['id'] == theme_id:
            return t
    return CODE_THEMES[0]


def list_code_themes() -> list:
    """列出所有代码主题"""
    return [{'id': t['id'], 'name': t['name']} for t in CODE_THEMES]
