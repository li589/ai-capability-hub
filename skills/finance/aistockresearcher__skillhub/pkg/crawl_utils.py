#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用爬虫工具模块（零依赖，纯 Python 标准库）
提供 HTTP 请求、JSON 读写、编码检测等基础设施函数。
适配任意 Agent 环境，无需 pip install。
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any, Optional

# ── 常量 ────────────────────────────────────────────────────
DEFAULT_TIMEOUT = 10
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,application/xhtml+xml,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ── HTTP 请求（stdlib urllib，零依赖）────────────────────────
def safe_request(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[dict] = None,
    retries: int = 2,
) -> Optional[bytes]:
    """安全的 HTTP GET 请求，返回原始字节或 None。

    Args:
        url: 请求地址
        timeout: 超时秒数
        headers: 自定义请求头
        retries: 失败重试次数

    Returns:
        响应内容 bytes，失败返回 None
    """
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    return None


def fetch_json(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[dict] = None,
) -> Optional[dict]:
    """获取 JSON 并解析为字典。

    Args:
        url: JSON 接口地址
        timeout: 超时秒数
        headers: 自定义请求头

    Returns:
        解析后的 dict，失败返回 None
    """
    raw = safe_request(url, timeout=timeout, headers=headers, retries=2)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ── 日期工具 ────────────────────────────────────────────────
def today_str(fmt: str = "%Y-%m-%d") -> str:
    """返回今天的日期字符串，默认格式 YYYY-MM-DD。"""
    return date.today().strftime(fmt)


# ── JSON 读写 ───────────────────────────────────────────────
def read_json(path: str, default: Any = None) -> Any:
    """从文件读取 JSON，文件不存在或损坏时返回 default。"""
    p = Path(path)
    if not p.exists():
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: str, data: Any, indent: int = 2) -> bool:
    """将数据写入 JSON 文件，自动创建父目录。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except OSError:
        return False


# ── 编码检测 ────────────────────────────────────────────────
def detect_encoding(raw: bytes, default: str = "utf-8") -> str:
    """检测字节数据的编码，优先 BOM，其次尝试常见中文编码。"""
    if raw is None:
        return default
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    if raw[:2] == b"\xff\xfe":
        return "utf-16-le"
    if raw[:2] == b"\xfe\xff":
        return "utf-16-be"
    for enc in ["utf-8", "gbk", "gb2312", "gb18030"]:
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return default


# ── 导出 ────────────────────────────────────────────────────
__all__ = [
    "safe_request",
    "fetch_json",
    "today_str",
    "read_json",
    "write_json",
    "detect_encoding",
]
