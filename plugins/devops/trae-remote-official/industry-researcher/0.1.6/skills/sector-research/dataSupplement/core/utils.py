# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 核心基础设施 · 公共工具函数
=================================================

功能概览:
  - safe_float: 安全数值转换（处理逗号/百分号/空值/NaN）
  - safe_int: 安全整数转换
  - strip_html: 移除 HTML 标签
  - ts_to_str: Unix 时间戳转格式化字符串

所有 domain/provider 模块应从此处导入工具函数，避免重复定义。

零外部依赖 — 仅使用 Python 标准库。
"""

from __future__ import annotations

import math
import re
from datetime import datetime as _datetime
from typing import Optional, Union

__all__ = [
    "safe_float",
    "safe_int",
    "strip_html",
    "ts_to_str",
]


def safe_float(val, default: Optional[float] = None) -> Optional[float]:
    """安全转换为浮点数。

    处理常见的非标准格式:
      - 逗号分隔（如 "1,234.56"）
      - 百分号（如 "12.5%"）
      - 中文横线/破折号（如 "—" "-"）
      - 空字符串和 None
      - NaN/Inf

    Args:
        val: 输入值
        default: 转换失败时的默认返回值（默认 None）

    Returns:
        浮点数或 default
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return default
        return float(val)
    s = str(val).strip()
    if not s or s in ("", "—", "-", "--", "N/A", "n/a", "null", "None"):
        return default
    # 移除逗号和百分号
    s = s.replace(",", "").replace("%", "").replace("％", "")
    try:
        result = float(s)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def safe_int(val, default: Optional[int] = None) -> Optional[int]:
    """安全转换为整数。

    Args:
        val: 输入值
        default: 转换失败时的默认返回值（默认 None）

    Returns:
        整数或 default
    """
    if val is None:
        return default
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return default
        return int(val)
    s = str(val).strip()
    if not s or s in ("", "—", "-", "--", "N/A", "n/a", "null", "None"):
        return default
    s = s.replace(",", "")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


def strip_html(text: str) -> str:
    """移除 HTML 标签。

    Args:
        text: 可能含有 HTML 标签的字符串

    Returns:
        纯文本字符串
    """
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def ts_to_str(ts, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Unix 时间戳转为格式化时间字符串。

    支持秒级和毫秒级时间戳（自动识别）。

    Args:
        ts: 时间戳（int/float/str），可以是秒级或毫秒级
        fmt: 输出格式，默认 "YYYY-MM-DD HH:MM:SS"

    Returns:
        格式化时间字符串，无法转换时返回原始值的字符串表示
    """
    if not ts:
        return ""
    try:
        ts_num = int(ts)
        # 毫秒级时间戳（13位）自动转为秒级
        if ts_num > 1e12:
            ts_num = ts_num // 1000
        return _datetime.fromtimestamp(ts_num).strftime(fmt)
    except (ValueError, OSError, TypeError, OverflowError):
        return str(ts)
