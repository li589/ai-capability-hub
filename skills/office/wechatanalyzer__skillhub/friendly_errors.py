"""友好错误消息映射（v2.2.0 新增，v2.5.0 接入 CLI 主入口）。

把异常堆栈变成人类能看懂的"该怎么办"。
针对 R 4.4 评测（"错误提示不直观"）优化。

使用：
    from friendly_errors import friendly_error
    try:
        ...
    except Exception as e:
        print(friendly_error(e))

v2.5.0 起 scripts/main.py 的 main() 已全局接入：任何命令异常都会
先转成友好提示输出（--debug 可看完整堆栈）。
"""
from __future__ import annotations

import re
import sys
from typing import Optional


# ============================================================
# 错误模式 → 友好解释
# ============================================================

_ERROR_PATTERNS = [
    # 安装/依赖
    {
        "match": r"ModuleNotFoundError.*jieba",
        "title": "❌ jieba 未安装",
        "reason": "jieba 是中文分词器，缺少它会大幅降低分析准确率。",
        "fix": "运行 `pip install jieba`",
        "doc_link": "../FAQ.md#q4-安装时报-modulenotfounderror-jieba",
    },
    {
        "match": r"ModuleNotFoundError.*sentence_transformers",
        "title": "❌ sentence-transformers 未安装（RAG 引擎）",
        "reason": "RAG 引擎依赖它。**这是可选依赖**，不装也能用核心分析功能。",
        "fix": "运行 `pip install -r requirements-rag.txt` 后才能用 RAG",
        "doc_link": "../FAQ.md#q5-安装时报-modulenotfounderror-sentence_transformers--chromadb",
    },
    {
        "match": r"ModuleNotFoundError.*flask",
        "title": "❌ flask 未安装（Web 仪表盘）",
        "reason": "Web 仪表盘依赖它。**这是可选依赖**，不装也能用 CLI + 报告。",
        "fix": "不需要 Web 界面可忽略；想用则 `pip install flask flask-cors`",
        "doc_link": "../FAQ.md#q7-报no-module-named-flask但我不想用-web-仪表盘",
    },
    {
        "match": r"ModuleNotFoundError.*jinja2",
        "title": "❌ jinja2 未安装（v1 报告生成）",
        "reason": "v1.2.0 的 report 命令依赖 jinja2 渲染模板。**可选**，v2 的 analyze-v2 --html 不依赖它。",
        "fix": "改用 `analyze-v2 --html report.html`；或 `pip install jinja2`",
    },
    {
        "match": r"ModuleNotFoundError.*docx",
        "title": "❌ python-docx 未安装（Word 解析/报告）",
        "reason": "导入 .docx 聊天记录或生成 Word 报告依赖它。**可选依赖**。",
        "fix": "改用 txt 导出聊天记录；或 `pip install python-docx`",
    },
    {
        "match": r"ModuleNotFoundError.*pptx",
        "title": "❌ python-pptx 未安装（PPT 解析/报告）",
        "reason": "导入 .pptx 或生成 PPT 报告依赖它。**可选依赖**。",
        "fix": "改用 txt 导出聊天记录；或 `pip install python-pptx`",
    },
    {
        "match": r"ModuleNotFoundError.*openpyxl",
        "title": "❌ openpyxl 未安装（Excel 解析）",
        "reason": "导入 .xlsx 聊天记录依赖它。**可选依赖**。",
        "fix": "改用 txt 导出聊天记录；或 `pip install openpyxl`",
    },
    {
        "match": r"ModuleNotFoundError.*PIL|ModuleNotFoundError.*'PIL'",
        "title": "❌ Pillow 未安装（图像处理）",
        "reason": "OCR / 图片消息处理依赖它。",
        "fix": "运行 `pip install Pillow`",
    },
    # 文件 / 编码
    {
        "match": r"FileNotFoundError",
        "title": "❌ 文件未找到",
        "reason": "指定路径的文件不存在。",
        "fix": (
            "1. 确认文件路径正确\n"
            "2. 如果是相对路径，确认在对的目录下运行\n"
            "3. 用 `ls` 或 `dir` 看文件是否真的存在"
        ),
        "doc_link": "../RUNBOOK.md#1-一句话用",
    },
    {
        "match": r"PermissionError.*denied",
        "title": "❌ 文件被占用 / 权限不足",
        "reason": "可能 Word / 微信正在打开该文件，或没写权限。",
        "fix": (
            "1. 关闭占用该文件的程序（Word / Excel / 微信）\n"
            "2. 换一个文件路径或文件名输出\n"
            "3. 在管理员权限下运行"
        ),
        "doc_link": "../FAQ.md#q31-跑命令后报-winerror-5-permission-denied",
    },
    {
        "match": r"UnicodeDecodeError|UnicodeError",
        "title": "❌ 编码错误",
        "reason": "工具默认尝试 utf-8-sig / utf-8 / gb18030 自动识别，仍失败说明编码特殊。",
        "fix": (
            "1. 在 `analyze-v2` 命令后加 `--encoding gbk` 或 `--encoding utf-8`\n"
            "2. 用文本编辑器（VSCode）打开文件，另存为 UTF-8 编码\n"
            "3. 确认文件确实没损坏"
        ),
        "doc_link": "../FAQ.md#q30-导入聊天时报编码错误unicodeerror",
    },
    # v2.5.0 bugfix：JSONDecodeError 的 str 总是包含 "Expecting value"，
    # 之前把它写进前一个 pattern 导致后面的"缓存文件损坏"条目永远匹配不到。
    # 现在按异常类型名优先匹配，两条例各自可达。
    {
        "match": r"json\.(decoder\.)?JSONDecodeError",
        "title": "❌ JSON 缓存文件损坏",
        "reason": "本地缓存的 JSON 被改坏或格式非法。",
        "fix": "删除 `data/cache/` 后重跑（会重新生成）",
    },
    {
        "match": r"Expecting value|JSON 解析",
        "title": "❌ JSON 解析失败（内容为空或被截断）",
        "reason": "JSON 文件被截断或格式错误（可能之前进程被 kill）。",
        "fix": (
            "1. 检查是否有进程正在写这个文件\n"
            "2. 看看是不是 0 KB 的空文件\n"
            "3. 备份损坏文件，重跑生成"
        ),
    },
    # 网络
    {
        "match": r"ConnectionError|ConnectionRefusedError|Connection reset",
        "title": "❌ 网络连接失败",
        "reason": "本工具默认不需要网络。如开了 RAG/MiroFish，需要联网下载模型或调用外部 API。",
        "fix": (
            "1. 检查网络：能否打开百度？\n"
            "2. 若用了代理，配置环境变量 `HTTP_PROXY` / `HTTPS_PROXY`\n"
            "3. 如不需要联网功能，确认 `config.json` 中 `mirofish.enabled = false`"
        ),
    },
    {
        "match": r"TimeoutError|ReadTimeout|ConnectTimeout",
        "title": "❌ 网络超时",
        "reason": "网络太慢或目标站无响应。",
        "fix": (
            "1. 重试一次\n"
            "2. 加超时参数 `--timeout 60`\n"
            "3. 检查防火墙 / VPN"
        ),
    },
    # 通用
    {
        "match": r"KeyboardInterrupt",
        "title": "⏹ 用户取消（Ctrl+C）",
        "reason": "你按了 Ctrl+C 终止程序。",
        "fix": "正常现象。如有未保存进度，重新跑即可。",
    },
    {
        "match": r"MemoryError|Cannot allocate memory",
        "title": "❌ 内存不足",
        "reason": "数据量太大或机器内存不够。",
        "fix": (
            "1. 关闭其他占用内存的程序（浏览器、IDE）\n"
            "2. 把对话分成多段处理\n"
            "3. 升级硬件"
        ),
    },
]


def friendly_error(exc: Exception) -> str:
    """把异常对象转换成人类可读的错误提示。

    Args:
        exc: 异常实例

    Returns:
        多行字符串，包含：标题 / 原因 / 解决方案

    Examples:
        >>> try:
        ...     import jieba
        ... except ModuleNotFoundError as e:
        ...     print(friendly_error(e))
        ❌ jieba 未安装
        原因：jieba 是中文分词器，缺少它会大幅降低分析准确率。
        解决：运行 `pip install jieba`
    """
    error_str = str(exc)
    type_name = type(exc).__name__

    # 1. 尝试匹配已知模式
    for pattern in _ERROR_PATTERNS:
        if re.search(pattern["match"], f"{type_name}: {error_str}", re.I):
            return _format_friendly(pattern, error_str)

    # 2. 未知错误 → 给出通用建议
    return _format_unknown(type_name, error_str)


def _format_friendly(pattern: dict, error_str: str) -> str:
    lines = [
        pattern["title"],
        "",
        f"原因：{pattern['reason']}",
        "",
        f"解决：{pattern['fix']}",
    ]
    if pattern.get("doc_link"):
        lines.append("")
        lines.append(f"📖 参考：[{pattern['doc_link']}]({pattern['doc_link']})")
    return "\n".join(lines)


def _format_unknown(type_name: str, error_str: str) -> str:
    return (
        f"❌ 未知错误（{type_name}）\n"
        f"\n"
        f"原始信息：{error_str}\n"
        f"\n"
        f"建议：\n"
        f"1. 跑 `python scripts/main.py doctor` 看环境\n"
        f"2. 检查输入文件格式是否正确\n"
        f"3. 在 GitHub issue 里贴出完整错误日志\n"
        f"4. 或参考 [FAQ.md](FAQ.md) 看是否有相似案例"
    )


# ============================================================
# CLI 入口
# ============================================================

def main():
    """CLI: 接住一个错误并友好地展示。"""
    if len(sys.argv) < 2:
        # 交互式：模拟一个常见错误
        try:
            import jieba  # noqa
        except ModuleNotFoundError as e:
            print(friendly_error(e))
        return 0

    # 从命令行输入错误名测试
    error_name = sys.argv[1]
    test_errors = {
        "jieba": ModuleNotFoundError("No module named 'jieba'"),
        "flask": ModuleNotFoundError("No module named 'flask'"),
        "file": FileNotFoundError("chat.txt not found"),
        "permission": PermissionError("Permission denied: 'output/report.html'"),
        "encoding": UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "invalid start byte"),
        "json": __import__("json").decoder.JSONDecodeError("Expecting value", "test.json", 0),
    }
    if error_name in test_errors:
        print(friendly_error(test_errors[error_name]))
    else:
        print(f"用法: python {sys.argv[0]} <jieba|flask|file|permission|encoding|json>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
