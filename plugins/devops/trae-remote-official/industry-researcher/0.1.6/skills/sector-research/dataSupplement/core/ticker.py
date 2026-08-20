# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 核心基础设施 · 多市场股票代码标准化
=======================================================

功能概览:
  - normalize: 统一代码格式(A 股纯数字, 港股/美股带后缀)
  - detect_market: 自动识别市场(CN / HK / US)
  - cn_prefix: A 股交易所前缀(sh / sz / bj)
  - to_eastmoney_secid: 东方财富 secid 格式
  - to_tencent_code: 腾讯行情代码格式
  - to_sina_code: 新浪财经代码格式
  - to_yahoo_symbol: Yahoo Finance 代码格式

支持市场:
  - A 股: 上海(60/68/9)、深圳(00/30/12/15)、北交所(8/4)
  - 港股: 五位数字代码
  - 美股: 纯字母代码

零外部依赖 — 仅使用 Python 标准库。
"""

from __future__ import annotations

import re
from typing import Optional

__all__ = [
    "normalize",
    "detect_market",
    "cn_prefix",
    "to_eastmoney_secid",
    "to_tencent_code",
    "to_sina_code",
    "to_yahoo_symbol",
]

# ---------------------------------------------------------------------------
# 正则模式
# ---------------------------------------------------------------------------

# A 股: 6 位纯数字
_RE_CN_CODE = re.compile(r"^(\d{6})$")

# A 股带市场前缀: sh600519, sz000001, bj830799
_RE_CN_PREFIXED = re.compile(r"^(sh|sz|bj)(\d{6})$", re.IGNORECASE)

# 港股: 纯数字 1~5 位, 或带 hk 前缀
_RE_HK_CODE = re.compile(r"^(?:hk)?(\d{1,5})$", re.IGNORECASE)

# 美股: 纯字母 1~5 位(如 AAPL, TSLA)
_RE_US_CODE = re.compile(r"^([A-Za-z]{1,5})$")

# 带后缀格式: 600519.SH, 0700.HK, AAPL.US
_RE_SUFFIXED = re.compile(
    r"^([A-Za-z0-9]+)\.(SH|SZ|BJ|SS|HK|US|NYSE|NASDAQ|N|O)$", re.IGNORECASE
)

# ---------------------------------------------------------------------------
# 市场检测
# ---------------------------------------------------------------------------

# A 股首位 → 交易所映射
_CN_FIRST_DIGIT_MAP = {
    "6": "sh",  # 上证主板 / 科创板(688)
    "9": "sh",  # 上证 B 股
    "5": "sh",  # 上证基金/权证
    "0": "sz",  # 深证主板
    "3": "sz",  # 创业板
    "1": "sz",  # 深证基金/债券
    "2": "sz",  # 深证 B 股
    "8": "bj",  # 北交所
    "4": "bj",  # 北交所(老三板)
}


def detect_market(code: str) -> str:
    """检测股票代码所属市场。

    Args:
        code: 原始股票代码, 支持多种输入格式:
              - 纯数字: "600519" (A 股) / "00700" (港股)
              - 带前缀: "sh600519" / "hk00700" / "us_aapl"
              - 带后缀: "600519.SH" / "0700.HK" / "AAPL.US"
              - 纯字母: "AAPL" (美股)

    Returns:
        市场标识: "CN" / "HK" / "US"

    Raises:
        ValueError: 无法识别的代码格式。

    示例:
        >>> detect_market("600519")
        'CN'
        >>> detect_market("00700")
        'HK'
        >>> detect_market("AAPL")
        'US'
    """
    code = code.strip()

    # 1. 带后缀格式: xxx.SH / xxx.HK / xxx.US
    m = _RE_SUFFIXED.match(code)
    if m:
        suffix = m.group(2).upper()
        if suffix in ("SH", "SZ", "BJ", "SS"):
            return "CN"
        elif suffix == "HK":
            return "HK"
        else:
            return "US"

    # 2. 带前缀格式
    if code.lower().startswith(("sh", "sz", "bj")):
        return "CN"
    if code.lower().startswith(("hk", "r_hk")):
        return "HK"
    if code.lower().startswith(("us", "usr_", "gb_")):
        return "US"

    # 3. A 股带前缀
    if _RE_CN_PREFIXED.match(code):
        return "CN"

    # 4. 6 位纯数字 → A 股
    if _RE_CN_CODE.match(code):
        return "CN"

    # 5. 1~5 位纯数字 → 港股
    if re.match(r"^\d{1,5}$", code):
        return "HK"

    # 6. 纯字母 → 美股
    if _RE_US_CODE.match(code):
        return "US"

    raise ValueError(f"无法识别的股票代码格式: {code!r}")


# ---------------------------------------------------------------------------
# 标准化
# ---------------------------------------------------------------------------


def normalize(code: str) -> str:
    """将股票代码标准化为统一格式。

    规则:
      - A 股: 返回纯 6 位数字, 如 "600519"
      - 港股: 返回 5 位数字(前补零), 如 "00700"
      - 美股: 返回大写字母, 如 "AAPL"

    Args:
        code: 任意格式的股票代码。

    Returns:
        标准化后的代码字符串。

    示例:
        >>> normalize("sh600519")
        '600519'
        >>> normalize("0700.HK")
        '00700'
        >>> normalize("aapl")
        'AAPL'
    """
    code = code.strip()

    # 带后缀
    m = _RE_SUFFIXED.match(code)
    if m:
        raw = m.group(1)
        suffix = m.group(2).upper()
        if suffix in ("SH", "SZ", "BJ", "SS"):
            return raw.zfill(6)
        elif suffix == "HK":
            return raw.zfill(5)
        else:
            return raw.upper()

    # 带前缀: sh/sz/bj
    m = _RE_CN_PREFIXED.match(code)
    if m:
        return m.group(2)

    # 港股前缀
    lower = code.lower()
    if lower.startswith("r_hk"):
        return lower[4:].zfill(5)
    if lower.startswith("hk"):
        return lower[2:].zfill(5)

    # 美股前缀
    if lower.startswith("usr_"):
        return lower[4:].upper()
    if lower.startswith("gb_"):
        return lower[3:].upper()
    if lower.startswith("us"):
        remainder = lower[2:]
        if remainder.isalpha():
            return remainder.upper()

    # 6 位数字 → A 股
    if _RE_CN_CODE.match(code):
        return code

    # 1~5 位纯数字 → 港股
    if re.match(r"^\d{1,5}$", code):
        return code.zfill(5)

    # 纯字母 → 美股
    if _RE_US_CODE.match(code):
        return code.upper()

    # 兜底: 原样返回
    return code


# ---------------------------------------------------------------------------
# A 股交易所前缀
# ---------------------------------------------------------------------------


def cn_prefix(code: str) -> str:
    """获取 A 股代码的交易所前缀。

    Args:
        code: A 股代码(6 位数字或带前缀格式)。

    Returns:
        "sh" / "sz" / "bj"

    Raises:
        ValueError: 非 A 股代码或无法确定交易所。

    规则:
        - 6/9/5 开头 → sh(上海)
        - 0/3/1/2 开头 → sz(深圳)
        - 8/4 开头 → bj(北交所)

    示例:
        >>> cn_prefix("600519")
        'sh'
        >>> cn_prefix("000001")
        'sz'
        >>> cn_prefix("830799")
        'bj'
    """
    normalized = normalize(code)

    # 确保是 A 股代码
    if not re.match(r"^\d{6}$", normalized):
        raise ValueError(f"非 A 股代码, 无法确定交易所前缀: {code!r}")

    first = normalized[0]
    prefix = _CN_FIRST_DIGIT_MAP.get(first)
    if prefix is None:
        raise ValueError(f"无法确定交易所前缀, 首位数字 '{first}' 未在映射中: {code!r}")

    return prefix


# ---------------------------------------------------------------------------
# 东方财富 secid 格式
# ---------------------------------------------------------------------------


def to_eastmoney_secid(code: str) -> str:
    """转换为东方财富 secid 格式。

    格式: "{market_id}.{code}"
      - 上海: "1.600519"
      - 深圳: "0.000001"
      - 北交所: "0.830799"
      - 港股: "116.00700"
      - 美股: "105.AAPL" (纳斯达克) / "106.AAPL" (纽交所, 默认 105)

    Args:
        code: 任意格式的股票代码。

    Returns:
        东方财富 secid 字符串。

    示例:
        >>> to_eastmoney_secid("600519")
        '1.600519'
        >>> to_eastmoney_secid("000001")
        '0.000001'
        >>> to_eastmoney_secid("00700")
        '116.00700'
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        prefix = cn_prefix(normalized)
        if prefix == "sh":
            return f"1.{normalized}"
        else:
            # 深圳和北交所都用 0
            return f"0.{normalized}"
    elif market == "HK":
        return f"116.{normalized}"
    else:
        # 美股默认纳斯达克 105
        return f"105.{normalized}"


# ---------------------------------------------------------------------------
# 腾讯行情代码格式
# ---------------------------------------------------------------------------


def to_tencent_code(code: str) -> str:
    """转换为腾讯行情代码格式。

    格式:
      - A 股: "sh600519" / "sz000001"
      - 港股: "r_hk00700"
      - 美股: "usr_aapl"

    Args:
        code: 任意格式的股票代码。

    Returns:
        腾讯格式代码字符串。

    示例:
        >>> to_tencent_code("600519")
        'sh600519'
        >>> to_tencent_code("00700")
        'r_hk00700'
        >>> to_tencent_code("AAPL")
        'usr_aapl'
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        prefix = cn_prefix(normalized)
        return f"{prefix}{normalized}"
    elif market == "HK":
        return f"r_hk{normalized}"
    else:
        return f"usr_{normalized.lower()}"


# ---------------------------------------------------------------------------
# 新浪财经代码格式
# ---------------------------------------------------------------------------


def to_sina_code(code: str) -> str:
    """转换为新浪财经代码格式。

    格式:
      - A 股: "sh600519" / "sz000001"
      - 港股: "hk00700"
      - 美股: "gb_aapl"

    Args:
        code: 任意格式的股票代码。

    Returns:
        新浪格式代码字符串。

    示例:
        >>> to_sina_code("600519")
        'sh600519'
        >>> to_sina_code("00700")
        'hk00700'
        >>> to_sina_code("AAPL")
        'gb_aapl'
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        prefix = cn_prefix(normalized)
        return f"{prefix}{normalized}"
    elif market == "HK":
        return f"hk{normalized}"
    else:
        return f"gb_{normalized.lower()}"


# ---------------------------------------------------------------------------
# Yahoo Finance 代码格式
# ---------------------------------------------------------------------------


def to_yahoo_symbol(code: str) -> str:
    """转换为 Yahoo Finance 代码格式。

    格式:
      - A 股上海: "600519.SS"
      - A 股深圳: "000001.SZ"
      - 港股: "0700.HK"
      - 美股: "AAPL" (无后缀)

    Args:
        code: 任意格式的股票代码。

    Returns:
        Yahoo Finance 格式代码字符串。

    示例:
        >>> to_yahoo_symbol("600519")
        '600519.SS'
        >>> to_yahoo_symbol("000001")
        '000001.SZ'
        >>> to_yahoo_symbol("00700")
        '0700.HK'
        >>> to_yahoo_symbol("AAPL")
        'AAPL'
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        prefix = cn_prefix(normalized)
        if prefix == "sh":
            return f"{normalized}.SS"
        elif prefix == "sz":
            return f"{normalized}.SZ"
        else:
            # 北交所在 Yahoo 上用 .BJ
            return f"{normalized}.BJ"
    elif market == "HK":
        # Yahoo 港股去掉前导零, 如 "0700.HK"
        stripped = normalized.lstrip("0") or "0"
        return f"{stripped}.HK"
    else:
        # 美股无后缀
        return normalized
