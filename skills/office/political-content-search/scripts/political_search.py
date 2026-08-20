#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时政内容检索工具

调用接口对关键词进行时政内容检索，并以 JSON/Markdown 形式展示结果。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

API_URL = "https://api.midu.com/ability/skill/jdt/political/search"
KEY_ENV = "MIDU_APP_SECRET"


class PoliticalSearchError(RuntimeError):
    pass


def load_api_key(explicit_key: Optional[str] = None) -> str:
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    env_key = os.environ.get(KEY_ENV, "").strip()
    if env_key:
        return env_key

    raise PoliticalSearchError(
        "未找到鉴权 token。请前往 https://ai.mdata.net 重新获取 Key，"
        f"然后将其写入环境变量 {KEY_ENV}。"
    )


def _post_json(url: str, body: Dict[str, Any], headers: Dict[str, str], timeout_s: int = 60) -> Dict[str, Any]:
    try:
        r = requests.post(url, json=body, headers=headers, timeout=timeout_s)
    except requests.RequestException as exc:
        raise PoliticalSearchError(f"网络请求失败：{exc}") from exc
    if not r.ok:
        raise PoliticalSearchError(f"接口 HTTP 错误: {r.status_code} {r.text}".strip())
    try:
        return r.json()
    except ValueError as exc:
        raise PoliticalSearchError(f"响应不是合法 JSON：{r.text}") from exc


@dataclass(frozen=True)
class SearchResult:
    keyword: str
    search_type: int
    raw_response: Dict[str, Any]
    formatted_content: Optional[str] = None


def _extract_formatted_content(resp: Dict[str, Any]) -> Optional[str]:
    """从响应中提取 formattedContent 字段。"""
    if not isinstance(resp, dict):
        return None
    # 优先取顶层字段
    if "formattedContent" in resp:
        return str(resp["formattedContent"])
    # 兼容 data.formattedContent
    data = resp.get("data")
    if isinstance(data, dict) and "formattedContent" in data:
        return str(data["formattedContent"])
    return None


def _normalize_line_endings(text: str) -> str:
    """标准化换行符：将 \r\n 统一转换为 \n，确保 Markdown 渲染一致性。
    
    同时处理以下情况：
    1. Windows 换行符 \r\n -> Unix 换行符 \n
    2. 孤立的 \r -> \n
    3. 确保段落之间有适当的空行分隔
    """
    # 第一步：统一换行符
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 第二步：处理连续多个换行符，最多保留两个（保持段落间距）
    while '\n\n\n' in normalized:
        normalized = normalized.replace('\n\n\n', '\n\n')
    
    return normalized


def _format_links(text: str) -> str:
    """将文本中的纯文本 URL 转换为 Markdown 链接形式，支持跳转。
    
    注意：仅处理未被包裹在 Markdown 链接语法中的纯文本 URL，
    避免对已有的 [text](url) 格式进行重复转换。
    
    同时确保换行后的内容能正确渲染为独立段落。
    """
    # 策略：先找出所有已有的 Markdown 链接，用占位符替换
    # 然后转换剩余的纯文本 URL，最后恢复占位符
    
    markdown_links = []
    placeholder_template = "__MD_LINK_{}__"
    
    def save_markdown_link(match: re.Match) -> str:
        """保存 Markdown 链接并返回占位符。"""
        idx = len(markdown_links)
        markdown_links.append(match.group(0))
        return placeholder_template.format(idx)
    
    # 匹配已有的 Markdown 链接格式 [text](url)
    markdown_pattern = re.compile(r'\[[^\]]+\]\([^)]+\)')
    text_with_placeholders = markdown_pattern.sub(save_markdown_link, text)
    
    # 现在转换剩余的纯文本 URL
    # 改进正则：更精确地匹配 URL，排除末尾的标点符号
    url_pattern = re.compile(r'https?://[^\s\)"\'>\]\)]+')
    
    def replace_url(match: re.Match) -> str:
        url = match.group(0)
        # 移除 URL 末尾可能的标点（如逗号、句号）
        trailing_punct = ''
        if url and url[-1] in '，。,;；：:':
            trailing_punct = url[-1]
            url = url[:-1]
        return f"[{url}]({url}){trailing_punct}"
    
    result = url_pattern.sub(replace_url, text_with_placeholders)
    
    # 恢复 Markdown 链接
    for idx, link in enumerate(markdown_links):
        result = result.replace(placeholder_template.format(idx), link)
    
    return result


def call_search_api(
    keyword: str,
    search_type: int = 0,
    api_key: Optional[str] = None,
) -> SearchResult:
    key = load_api_key(api_key)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "X-Skill-Code": "POLITICAL_SEARCH",
        "X-User-Id": os.environ.get("MIDU_USER_ID", ""),
    }
    params: Dict[str, Any] = {
        "keyword": keyword,
        "searchType": search_type,
    }
    resp = _post_json(API_URL, params, headers=headers, timeout_s=60)
    formatted_content = _extract_formatted_content(resp)
    return SearchResult(
        keyword=keyword,
        search_type=search_type,
        raw_response=resp,
        formatted_content=formatted_content,
    )


def search_content(
    keyword: str,
    search_type: int = 0,
    api_key: Optional[str] = None,
) -> SearchResult:
    if not keyword or not keyword.strip():
        raise PoliticalSearchError("keyword 不能为空。")
    return call_search_api(keyword=keyword, search_type=search_type, api_key=api_key)


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="时政内容检索：调用接口并展示结果")
    p.add_argument("--keyword", required=True, help="检索关键词")
    p.add_argument(
        "--search-type",
        dest="search_type",
        type=int,
        default=0,
        help="检索类型（默认 0）",
    )
    p.add_argument("--api-key", dest="api_key", default=None, help="鉴权 token（覆盖环境变量）")
    p.add_argument("--json", action="store_true", help="输出完整 JSON 响应而非格式化内容")
    return p


def main(argv: Optional[Tuple[str, ...]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)

    try:
        result = search_content(
            args.keyword,
            search_type=args.search_type,
            api_key=args.api_key,
        )

        # --json 模式：输出完整原始响应
        if args.json:
            print(json.dumps(result.raw_response, ensure_ascii=False, indent=2))
        # 默认模式：优先展示 formattedContent
        elif result.formatted_content:
            # 标准化换行符并转换 URL 为 Markdown 链接
            normalized_content = _normalize_line_endings(result.formatted_content)
            formatted_output = _format_links(normalized_content)
            print(formatted_output)
        else:
            print(json.dumps(result.raw_response, ensure_ascii=False, indent=2))
        return 0
    except PoliticalSearchError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
