"""版本号单一来源（v2.5.0 新增）。

此前版本号散落在 SKILL.md / config.json / main.py / 报告生成器等
十余处，升级时经常漏改（v2.4.0 时 config.json 仍显示 2.3.0）。
CLI 输出、JSON 导出、HTML 报告统一从这里读取。

用法：
    from core.version import __version__
"""

__version__ = "2.8.0"
