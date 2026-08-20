"""输出后处理：将 ContentBlock 列表转换为 Markdown。

此模块复用了 mineru-vl-utils 的 post_process.json2md 函数。
"""
from __future__ import annotations

import re
from typing import Optional

# upstream MinerU content_list caption 字段名（运行时导入避免循环依赖）
_IMAGE_CAPTION_KEY = "image_caption"
_TABLE_CAPTION_KEY = "table_caption"
_CHART_CAPTION_KEY = "chart_caption"

from loguru import logger

SENTENCE_END_PATTERN = re.compile(r"[。.!！?？…」』）)]\s*$")


def blocks_to_markdown(blocks: list) -> str:
    """将 ContentBlock 列表转换为 Markdown 字符串。

    优先使用 mineru-vl-utils 提供的 json2md；若不可用则使用内置简版。

    Parameters
    ----------
    blocks : ContentBlock 列表

    Returns
    -------
    str: Markdown 格式字符串
    """
    try:
        from mineru_vl_utils.post_process import json2md
        return json2md(blocks)
    except ImportError:
        logger.warning("mineru-vl-utils 未安装，使用内置简版 Markdown 转换")
        return _simple_blocks_to_markdown(blocks)
    except Exception as e:
        logger.warning("json2md 调用失败: {}，使用内置简版", e)
        return _simple_blocks_to_markdown(blocks)


_BLOCK_TYPE_HANDLERS: dict[str, callable] = {}


def _register_block_handler(btype: str):
    """装饰器：注册块类型处理器。"""
    def decorator(func: callable) -> callable:
        _BLOCK_TYPE_HANDLERS[btype] = func
        return func
    return decorator


@_register_block_handler("text")
def _handle_text(block: dict) -> str:
    """处理文本块。"""
    return block.get("content") or ""


@_register_block_handler("title")
def _handle_title(block: dict) -> str:
    """处理标题块。"""
    text = (block.get("content") or "").strip().replace("\n", " ")
    return f"## {text}" if text else ""


@_register_block_handler("table")
def _handle_table(block: dict) -> str:
    """处理表格块。"""
    content = block.get("content") or ""
    caption = block.get(_TABLE_CAPTION_KEY) or ""
    if caption:
        return f"{caption}\n\n{content}" if content else caption
    return content


@_register_block_handler("equation")
def _handle_equation(block: dict) -> str:
    """处理公式块。"""
    content = block.get("content") or ""
    return f"$$\n{content}\n$$"


@_register_block_handler("image")
def _handle_image(block: dict) -> str:
    """处理图片块。"""
    caption = block.get(_IMAGE_CAPTION_KEY) or block.get("content") or ""
    return f"**[图片]** {caption}" if caption else "**[图片]**"


@_register_block_handler("chart")
def _handle_chart(block: dict) -> str:
    """处理图表块。"""
    caption = block.get(_CHART_CAPTION_KEY) or block.get("content") or ""
    return f"**[图表]** {caption}" if caption else "**[图表]**"


@_register_block_handler("caption")
def _handle_caption(block: dict) -> str:
    """处理独立 caption 块。"""
    return block.get("content") or ""


@_register_block_handler("code")
def _handle_code(block: dict) -> str:
    """处理代码块。"""
    content = block.get("content") or ""
    return f"```\n{content}\n```"


@_register_block_handler("footer")
def _handle_footer(block: dict) -> str:
    """处理页脚块。"""
    content = block.get("content") or ""
    return f"*{content}*"


@_register_block_handler("header")
def _handle_header(block: dict) -> str:
    """处理页眉块。"""
    content = block.get("content") or ""
    return f"*{content}*"


@_register_block_handler("reference")
def _handle_reference(block: dict) -> str:
    """处理参考文献块。"""
    content = block.get("content") or ""
    return f"*{content}*"


def _simple_blocks_to_markdown(blocks: list) -> str:
    """内置简版 Markdown 转换（不依赖 mineru-vl-utils）。"""
    lines = []
    for block in blocks:
        btype = block.get("type", "")
        handler = _BLOCK_TYPE_HANDLERS.get(btype)

        if handler:
            content = handler(block)
        else:
            content = block.get("content") or ""

        if content:
            lines.append(content)
            lines.append("")

    return "\n".join(lines).strip()


def merge_pages(
    page_results: list[tuple[str, int, list]],
    merge_paragraphs: bool = True,
) -> str:
    """合并多页结果为完整文档的 Markdown。"""
    md_parts: list[str] = []
    merge_with_prev: list[bool] = []   # 记录每页是否应与上一页无分隔地合并

    prev_text_tail: Optional[str] = None

    for source, page_idx, blocks in page_results:
        page_md = blocks_to_markdown(blocks)

        # 只有上一页以未结束的句子结尾、且当前页不以标题开头，才合并
        should_merge = (
            merge_paragraphs
            and prev_text_tail is not None
            and bool(page_md)
            and not _is_page_start(page_md)
        )

        md_parts.append(page_md)
        merge_with_prev.append(should_merge)
        prev_text_tail = _get_last_text_fragment(blocks) if merge_paragraphs else None

    # 按合并标志拼接：需要合并的页面用空格连接（不插入 --- 分隔符）
    result_segments: list[str] = []
    for page_md, should_merge in zip(md_parts, merge_with_prev):
        if not page_md.strip():
            continue
        if should_merge and result_segments:
            # 跨页续接：直接拼到上一段末尾，不插入分隔符
            result_segments[-1] = result_segments[-1].rstrip() + " " + page_md.lstrip()
        else:
            result_segments.append(page_md)

    full_md = "\n\n---\n\n".join(result_segments)
    return full_md


def _is_page_start(text: str) -> bool:
    """判断 Markdown 内容是否以标题开始（不应合并）。"""
    return bool(text.strip().startswith("#"))


def _get_last_text_fragment(blocks: list) -> Optional[str]:
    """返回最后一个文本块的内容（若末尾无句终符则视为可合并）。"""
    for block in reversed(blocks):
        if block.get("type") == "text" and block.get("content"):
            content = block["content"].strip()
            if content and not _ends_with_sentence_end(content):
                return content
    return None


def _ends_with_sentence_end(text: str) -> bool:
    """判断文本是否以句终符结尾。"""
    return bool(SENTENCE_END_PATTERN.search(text))
