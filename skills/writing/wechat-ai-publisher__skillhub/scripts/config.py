#!/usr/bin/env python3
"""
配置管理工具

自动读取 .env 文件中的配置信息。
支持的主题与 scripts/markdown_to_wechat_doocs.py 的 THEMES 完全一致：
default / green / purple / orange / cyan（5 种，确保主题不会静默回退）。
"""

import os
from pathlib import Path


def load_config():
    """加载 .env 配置（skill 目录下）"""
    config = {}

    skill_dir = Path(__file__).parent.parent
    env_file = skill_dir / '.env'

    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()

    return config


def get_wechat_config():
    """获取微信公众号配置"""
    config = load_config()
    return {
        'app_id': config.get('WECHAT_APP_ID', ''),
        'app_secret': config.get('WECHAT_APP_SECRET', '')
    }


def get_markdown_config():
    """获取 Markdown 排版配置"""
    config = load_config()
    return {
        'converter': config.get('MARKDOWN_CONVERTER', 'doocs'),
        'theme': config.get('MARKDOWN_THEME', None)  # None 表示由 Agent 动态选择
    }


# 与 markdown_to_wechat_doocs.py 的 THEMES 严格对齐，避免选到不支持的主题被静默回退
SUPPORTED_THEMES = ('default', 'green', 'purple', 'orange', 'cyan')


def select_theme_by_content(title: str = "", content: str = "") -> str:
    """
    根据文章内容自动选择合适的主题（只返回转换器支持的 5 种之一）。

    Args:
        title: 文章标题
        content: 文章内容

    Returns:
        str: 主题名称（default / green / purple / orange / cyan）
    """
    text = (title + " " + content).lower()

    # 科技/商务/职场/AI/旅行/文艺 → cyan（清爽专业）
    if any(k in text for k in ['科技', 'ai', '人工智能', '商务', '职场', '管理',
                                '效率', '旅行', '旅游', '游记', '文艺', '清新']):
        return 'cyan'

    # 健康/养生/环保/自然/运动/饮食 → green
    if any(k in text for k in ['健康', '养生', '环保', '自然', '运动', '饮食']):
        return 'green'

    # 情感/浪漫/爱情/品牌/高端/艺术 → purple
    if any(k in text for k in ['爱情', '恋爱', '浪漫', '情感', '甜蜜',
                                '品牌', '奢侈', '高端', '优雅', '艺术']):
        return 'purple'

    # 励志/成长/女性/独立/搞钱/改变/蜕变/节日活动 → orange（温暖活力）
    if any(k in text for k in ['励志', '成长', '女人', '女性', '独立', '搞钱',
                                '改变', '蜕变', '节日', '春节', '新年', '活动', '庆祝']):
        return 'orange'

    # 默认：通用简洁
    return 'default'


if __name__ == '__main__':
    wechat = get_wechat_config()
    markdown = get_markdown_config()

    print("微信公众号配置:")
    print(f"  AppID: {wechat['app_id'] or '(未配置)'}")
    print(f"  AppSecret: {wechat['app_secret'][:10] + '...' if wechat['app_secret'] else '(未配置)'}")
    print(f"\nMarkdown 排版配置:")
    print(f"  转换器: {markdown['converter']}")
    print(f"  主题: {markdown['theme'] or '动态选择'}")

    print(f"\n主题选择测试（仅输出支持的 5 种主题）:")
    test_cases = [
        ("当女人一门心思搞钱，她就开始长脑子", "励志 女性 独立"),
        ("2024年AI技术发展趋势分析", "科技 人工智能 商务"),
        ("春天来了，去这10个地方旅行吧", "旅行 清新 文艺"),
        ("如何保持健康的生活方式", "健康 养生 运动"),
        ("爱情里最重要的是什么", "爱情 情感 浪漫"),
        ("一篇普通的产品使用说明", "常规内容"),
    ]
    for title, content in test_cases:
        theme = select_theme_by_content(title, content)
        assert theme in SUPPORTED_THEMES, f"主题越界: {theme}"
        print(f"  '{title}' → {theme}")
