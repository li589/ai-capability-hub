# -*- coding: utf-8 -*-
"""
文章主题定义 — 5 种预设主题
每个主题定义标题、引用、代码块、链接、分割线、段落间距等样式
所有样式均为内联 inline style（公众号不支持外部 CSS）
"""

THEMES = {
    'lapis': {
        'name': '青金石 (Lapis)',
        'desc': '沉稳蓝调，商务清新',
        'colors': {
            'accent': '#2b6cb0',
            'accentLight': '#90cdf4',
            'text': '#1a202c',
            'textSecondary': '#4a5568',
            'quoteBg': '#ebf8ff',
            'tableBorder': '#bee3f8',
            'tableThBg': '#2b6cb0',
        },
        'h1': 'font-size:24px;font-weight:700;margin:28px 0 14px;color:#1a202c;text-align:center;',
        'h2': 'font-size:20px;font-weight:700;margin:24px 0 12px;color:#1a202c;border-bottom:2px solid #90cdf4;padding-bottom:6px;',
        'h3': 'font-size:18px;font-weight:700;margin:22px 0 10px;color:#2b6cb0;',
        'h4': 'font-size:16px;font-weight:600;margin:18px 0 8px;color:#2b6cb0;',
        'h5': 'font-size:15px;font-weight:600;margin:16px 0 6px;color:#4a5568;',
        'h6': 'font-size:14px;font-weight:600;margin:14px 0 6px;color:#718096;',
        'blockquote': 'margin:18px 0;padding:14px 18px;background:#ebf8ff;border-left:4px solid #2b6cb0;color:#4a5568;border-radius:0 8px 8px 0;',
        'codeBlock': 'margin:16px 0;padding:14px 18px;background:#f7fafc;border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;font-size:14px;line-height:1.6;border:1px solid #e2e8f0;white-space:pre-wrap;word-break:break-word;color:#2d3748;',
        'u': 'text-decoration:underline;text-underline-offset:3px;color:#2b6cb0;',
        'link': 'color:#2b6cb0;text-decoration:underline;',
        'hr': 'border:none;height:1px;background:#e2e8f0;margin:24px 0;',
        'strong': 'font-weight:700;color:#2b6cb0;',
        'p': 'margin:0;padding:8px 0;color:#1a202c;font-size:15px;line-height:1.8;',
        'section': 'margin:0;padding:12px 10px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:15px;color:#1a202c;line-height:1.8;word-break:break-word;',
        'table': {
            'wrap': 'margin:16px 0;width:100%;border-collapse:collapse;border:1px solid #bee3f8;border-radius:8px;overflow:hidden;',
            'th': 'padding:10px 12px;background:#2b6cb0;color:#fff;font-weight:bold;text-align:left;border:1px solid #bee3f8;',
            'td': 'padding:10px 12px;border:1px solid #bee3f8;background:#fff;color:#1a202c;',
        },
        'image': {
            'default': 'max-width:100%;height:auto;display:block;margin:14px auto;',
            'rounded': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;',
            'shadow': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;box-shadow:0 4px 12px rgba(43,108,176,0.15);',
            'border': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;border:3px solid #2b6cb0;',
        },
        'imageCaption': 'display:block;margin:-6px 0 14px;font-size:13px;color:#4a5568;text-align:center;line-height:1.5;',
    },
    'forest': {
        'name': '森林 (Forest)',
        'desc': '自然绿意，清新舒爽',
        'colors': {
            'accent': '#276749',
            'accentLight': '#9ae6b4',
            'text': '#1a202c',
            'textSecondary': '#4a5568',
            'quoteBg': '#f0fff4',
            'tableBorder': '#c6f6d5',
            'tableThBg': '#276749',
        },
        'h1': 'font-size:24px;font-weight:700;margin:28px 0 14px;color:#22543d;text-align:center;',
        'h2': 'font-size:20px;font-weight:700;margin:24px 0 12px;color:#22543d;border-bottom:2px solid #9ae6b4;padding-bottom:6px;',
        'h3': 'font-size:18px;font-weight:700;margin:22px 0 10px;color:#276749;',
        'h4': 'font-size:16px;font-weight:600;margin:18px 0 8px;color:#276749;',
        'h5': 'font-size:15px;font-weight:600;margin:16px 0 6px;color:#4a5568;',
        'h6': 'font-size:14px;font-weight:600;margin:14px 0 6px;color:#718096;',
        'blockquote': 'margin:18px 0;padding:14px 18px;background:#f0fff4;border-left:4px solid #276749;color:#4a5568;border-radius:0 8px 8px 0;',
        'codeBlock': 'margin:16px 0;padding:14px 18px;background:#f0fff4;border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;font-size:14px;line-height:1.6;border:1px solid #c6f6d5;white-space:pre-wrap;word-break:break-word;color:#22543d;',
        'u': 'text-decoration:underline;text-underline-offset:3px;color:#276749;',
        'link': 'color:#276749;text-decoration:underline;',
        'hr': 'border:none;height:1px;background:#c6f6d5;margin:24px 0;',
        'strong': 'font-weight:700;color:#276749;',
        'p': 'margin:0;padding:8px 0;color:#1a202c;font-size:15px;line-height:1.8;',
        'section': 'margin:0;padding:12px 10px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:15px;color:#1a202c;line-height:1.8;word-break:break-word;',
        'table': {
            'wrap': 'margin:16px 0;width:100%;border-collapse:collapse;border:1px solid #c6f6d5;border-radius:8px;overflow:hidden;',
            'th': 'padding:10px 12px;background:#276749;color:#fff;font-weight:bold;text-align:left;border:1px solid #c6f6d5;',
            'td': 'padding:10px 12px;border:1px solid #c6f6d5;background:#fff;color:#1a202c;',
        },
        'image': {
            'default': 'max-width:100%;height:auto;display:block;margin:14px auto;',
            'rounded': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;',
            'shadow': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;box-shadow:0 4px 12px rgba(39,103,73,0.15);',
            'border': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;border:3px solid #276749;',
        },
        'imageCaption': 'display:block;margin:-6px 0 14px;font-size:13px;color:#4a5568;text-align:center;line-height:1.5;',
    },
    'ocean': {
        'name': '海洋 (Ocean)',
        'desc': '深邃海洋，专业沉稳',
        'colors': {
            'accent': '#1a365d',
            'accentLight': '#63b3ed',
            'text': '#1a202c',
            'textSecondary': '#4a5568',
            'quoteBg': '#ebf4ff',
            'tableBorder': '#bee3f8',
            'tableThBg': '#1a365d',
        },
        'h1': 'font-size:24px;font-weight:700;margin:28px 0 14px;color:#1a365d;text-align:center;',
        'h2': 'font-size:20px;font-weight:700;margin:24px 0 12px;color:#1a365d;border-bottom:2px solid #63b3ed;padding-bottom:6px;',
        'h3': 'font-size:18px;font-weight:700;margin:22px 0 10px;color:#2b6cb0;',
        'h4': 'font-size:16px;font-weight:600;margin:18px 0 8px;color:#2b6cb0;',
        'h5': 'font-size:15px;font-weight:600;margin:16px 0 6px;color:#4a5568;',
        'h6': 'font-size:14px;font-weight:600;margin:14px 0 6px;color:#718096;',
        'blockquote': 'margin:18px 0;padding:14px 18px;background:#ebf4ff;border-left:4px solid #1a365d;color:#4a5568;border-radius:0 8px 8px 0;',
        'codeBlock': 'margin:16px 0;padding:14px 18px;background:#f7fafc;border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;font-size:14px;line-height:1.6;border:1px solid #e2e8f0;white-space:pre-wrap;word-break:break-word;color:#2d3748;',
        'u': 'text-decoration:underline;text-underline-offset:3px;color:#1a365d;',
        'link': 'color:#2b6cb0;text-decoration:underline;',
        'hr': 'border:none;height:1px;background:#e2e8f0;margin:24px 0;',
        'strong': 'font-weight:700;color:#1a365d;',
        'p': 'margin:0;padding:8px 0;color:#1a202c;font-size:15px;line-height:1.8;',
        'section': 'margin:0;padding:12px 10px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:15px;color:#1a202c;line-height:1.8;word-break:break-word;',
        'table': {
            'wrap': 'margin:16px 0;width:100%;border-collapse:collapse;border:1px solid #bee3f8;border-radius:8px;overflow:hidden;',
            'th': 'padding:10px 12px;background:#1a365d;color:#fff;font-weight:bold;text-align:left;border:1px solid #bee3f8;',
            'td': 'padding:10px 12px;border:1px solid #bee3f8;background:#fff;color:#1a202c;',
        },
        'image': {
            'default': 'max-width:100%;height:auto;display:block;margin:14px auto;',
            'rounded': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;',
            'shadow': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;box-shadow:0 4px 12px rgba(26,54,93,0.15);',
            'border': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;border:3px solid #1a365d;',
        },
        'imageCaption': 'display:block;margin:-6px 0 14px;font-size:13px;color:#4a5568;text-align:center;line-height:1.5;',
    },
    'sunset': {
        'name': '日落 (Sunset)',
        'desc': '暖橙色调，温馨活力',
        'colors': {
            'accent': '#c05621',
            'accentLight': '#fbd38d',
            'text': '#1a202c',
            'textSecondary': '#4a5568',
            'quoteBg': '#fffaf0',
            'tableBorder': '#feebc8',
            'tableThBg': '#c05621',
        },
        'h1': 'font-size:24px;font-weight:700;margin:28px 0 14px;color:#7b341e;text-align:center;',
        'h2': 'font-size:20px;font-weight:700;margin:24px 0 12px;color:#7b341e;border-bottom:2px solid #fbd38d;padding-bottom:6px;',
        'h3': 'font-size:18px;font-weight:700;margin:22px 0 10px;color:#c05621;',
        'h4': 'font-size:16px;font-weight:600;margin:18px 0 8px;color:#c05621;',
        'h5': 'font-size:15px;font-weight:600;margin:16px 0 6px;color:#4a5568;',
        'h6': 'font-size:14px;font-weight:600;margin:14px 0 6px;color:#718096;',
        'blockquote': 'margin:18px 0;padding:14px 18px;background:#fffaf0;border-left:4px solid #c05621;color:#4a5568;border-radius:0 8px 8px 0;',
        'codeBlock': 'margin:16px 0;padding:14px 18px;background:#fffaf0;border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;font-size:14px;line-height:1.6;border:1px solid #feebc8;white-space:pre-wrap;word-break:break-word;color:#7b341e;',
        'u': 'text-decoration:underline;text-underline-offset:3px;color:#c05621;',
        'link': 'color:#c05621;text-decoration:underline;',
        'hr': 'border:none;height:1px;background:#feebc8;margin:24px 0;',
        'strong': 'font-weight:700;color:#c05621;',
        'p': 'margin:0;padding:8px 0;color:#1a202c;font-size:15px;line-height:1.8;',
        'section': 'margin:0;padding:12px 10px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:15px;color:#1a202c;line-height:1.8;word-break:break-word;',
        'table': {
            'wrap': 'margin:16px 0;width:100%;border-collapse:collapse;border:1px solid #feebc8;border-radius:8px;overflow:hidden;',
            'th': 'padding:10px 12px;background:#c05621;color:#fff;font-weight:bold;text-align:left;border:1px solid #feebc8;',
            'td': 'padding:10px 12px;border:1px solid #feebc8;background:#fff;color:#1a202c;',
        },
        'image': {
            'default': 'max-width:100%;height:auto;display:block;margin:14px auto;',
            'rounded': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;',
            'shadow': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;box-shadow:0 4px 12px rgba(192,86,33,0.15);',
            'border': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;border:3px solid #c05621;',
        },
        'imageCaption': 'display:block;margin:-6px 0 14px;font-size:13px;color:#4a5568;text-align:center;line-height:1.5;',
    },
    'noir': {
        'name': '暗夜 (Noir)',
        'desc': '深色背景，护眼夜读',
        'colors': {
            'accent': '#38bdf8',
            'accentLight': '#7dd3fc',
            'text': '#e2e8f0',
            'textSecondary': '#94a3b8',
            'quoteBg': 'rgba(56,189,248,0.12)',
            'tableBorder': '#475569',
            'tableThBg': '#334155',
        },
        'h1': 'font-size:24px;font-weight:700;margin:28px 0 14px;color:#e2e8f0;text-align:center;',
        'h2': 'font-size:20px;font-weight:700;margin:24px 0 12px;color:#7dd3fc;border-bottom:2px solid #475569;padding-bottom:6px;',
        'h3': 'font-size:18px;font-weight:700;margin:22px 0 10px;color:#94a3b8;',
        'h4': 'font-size:16px;font-weight:600;margin:18px 0 8px;color:#94a3b8;',
        'h5': 'font-size:15px;font-weight:600;margin:16px 0 6px;color:#718096;',
        'h6': 'font-size:14px;font-weight:600;margin:14px 0 6px;color:#64748b;',
        'blockquote': 'margin:18px 0;padding:14px 18px;background:rgba(56,189,248,0.12);border-left:4px solid #38bdf8;color:#94a3b8;border-radius:0 8px 8px 0;',
        'codeBlock': 'margin:16px 0;padding:14px 18px;background:#1e293b;border-radius:8px;overflow:auto;font-family:Consolas,Monaco,monospace;font-size:14px;line-height:1.6;border:1px solid #334155;white-space:pre-wrap;word-break:break-word;color:#e2e8f0;',
        'u': 'text-decoration:underline;text-underline-offset:3px;color:#38bdf8;',
        'link': 'color:#38bdf8;text-decoration:underline;',
        'hr': 'border:none;height:1px;background:#475569;margin:24px 0;',
        'strong': 'font-weight:700;color:#e2e8f0;',
        'p': 'margin:0;padding:8px 0;color:#e2e8f0;font-size:15px;line-height:1.8;',
        'section': 'margin:0;padding:16px 14px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:15px;color:#e2e8f0;line-height:1.8;word-break:break-word;background:#0f172a;border-radius:12px;',
        'table': {
            'wrap': 'margin:16px 0;width:100%;border-collapse:collapse;border:1px solid #475569;border-radius:8px;overflow:hidden;background:#1e293b;',
            'th': 'padding:10px 12px;background:#334155;color:#f1f5f9;font-weight:bold;text-align:left;border:1px solid #475569;',
            'td': 'padding:10px 12px;border:1px solid #334155;background:#1e293b;color:#cbd5e1;',
        },
        'image': {
            'default': 'max-width:100%;height:auto;display:block;margin:14px auto;',
            'rounded': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;',
            'shadow': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.4);',
            'border': 'max-width:100%;height:auto;display:block;margin:14px auto;border-radius:8px;border:2px solid #475569;',
        },
        'imageCaption': 'display:block;margin:-6px 0 14px;font-size:13px;color:#94a3b8;text-align:center;line-height:1.5;',
    },
}

# 图片样式预设
IMAGE_STYLE_OPTIONS = [
    {'id': 'default', 'name': '默认'},
    {'id': 'rounded', 'name': '圆角'},
    {'id': 'shadow', 'name': '阴影'},
    {'id': 'border', 'name': '描边'},
]


def get_resolved_theme(theme_id: str = 'lapis') -> dict:
    """获取解析后的完整主题配置

    Args:
        theme_id: 主题 ID (lapis/forest/ocean/sunset/noir)

    Returns:
        主题配置字典
    """
    theme = THEMES.get(theme_id)
    if theme is None:
        theme = THEMES['lapis']
    return theme


def get_image_style(theme_id: str, image_style_id: str = 'default') -> str:
    """获取指定主题的图片样式字符串

    Args:
        theme_id: 主题 ID
        image_style_id: 图片样式 ID (default/rounded/shadow/border)

    Returns:
        CSS inline style 字符串
    """
    theme = get_resolved_theme(theme_id)
    images = theme.get('image', {})
    style = images.get(image_style_id)
    if style is None:
        style = images.get('default', 'max-width:100%;height:auto;display:block;margin:14px auto;')
    return style


def list_themes() -> list:
    """列出所有可用主题"""
    return [{'id': tid, 'name': t['name'], 'desc': t['desc']}
            for tid, t in THEMES.items()]


def list_image_styles() -> list:
    """列出所有可用图片样式"""
    return [{'id': s['id'], 'name': s['name']} for s in IMAGE_STYLE_OPTIONS]
