# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 指数行情
==========================================

功能概览:
  - major_indices: 主要指数快照（上证/深证/创业板/科创50/北证50/
                   中证500/中证1000/恒生/纳斯达克）

数据源:
  - 主源: 腾讯批量行情 qt.gtimg.cn（覆盖A股/港股/美股指数）
  - 备源: 新浪行情 hq.sinajs.cn
"""

from __future__ import annotations

import sys
import os
import re
from typing import Optional

# 路径设置: 确保 core/ 和 providers/ 可导入
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get
from core.cache import cache_get, cache_set, make_key, TTL_QUOTE
from core.throttle import throttled_get

# ---------------------------------------------------------------------------
# 指数代码映射
# ---------------------------------------------------------------------------

# 腾讯行情格式的主要指数代码
_MAJOR_INDEX_CODES = {
    # A股指数
    "sh000001": {"name": "上证指数", "market": "CN"},
    "sz399001": {"name": "深证成指", "market": "CN"},
    "sz399006": {"name": "创业板指", "market": "CN"},
    "sh000688": {"name": "科创50", "market": "CN"},
    "bj899050": {"name": "北证50", "market": "CN"},
    "sh000905": {"name": "中证500", "market": "CN"},
    "sh000852": {"name": "中证1000", "market": "CN"},
    "sh000300": {"name": "沪深300", "market": "CN"},
    # 港股指数
    "r_hkHSI": {"name": "恒生指数", "market": "HK"},
    "r_hkHSCEI": {"name": "恒生国企指数", "market": "HK"},
    # 美股指数
    "usr_ixic": {"name": "纳斯达克", "market": "US"},
    "usr_dji": {"name": "道琼斯", "market": "US"},
    "usr_inx": {"name": "标普500", "market": "US"},
}

# 新浪格式备用
_SINA_INDEX_CODES = {
    "s_sh000001": "上证指数",
    "s_sz399001": "深证成指",
    "s_sz399006": "创业板指",
    "s_sh000688": "科创50",
    "s_sh000905": "中证500",
    "s_sh000852": "中证1000",
    "s_sh000300": "沪深300",
    "int_hangseng": "恒生指数",
    "int_nasdaq": "纳斯达克",
    "int_dji": "道琼斯",
    "int_sp500": "标普500",
}

_TENCENT_URL = "http://qt.gtimg.cn/q="
_SINA_URL = "http://hq.sinajs.cn/list="

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.qq.com/",
}


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数。"""
    if val is None or val == "" or val == "—" or val == "-":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


def _parse_tencent_index_line(line: str, expected_name: str = None) -> Optional[dict]:
    """解析腾讯行情指数数据行。

    腾讯指数数据格式与个股略有不同，统一采用 ~ 分隔。

    Args:
        line: 原始数据行
        expected_name: 预期的指数名称（用于标记）

    Returns:
        解析后的字典，失败返回 None
    """
    if "=" not in line:
        return None

    try:
        raw = line.split('"')[1]
    except IndexError:
        return None

    if not raw or raw.strip() == "":
        return None

    fields = raw.split("~")
    if len(fields) < 35:
        return None

    def _float(idx: int) -> Optional[float]:
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    code = fields[2].strip() if len(fields) > 2 else ""
    name = fields[1].strip() if len(fields) > 1 else (expected_name or "")
    price = _float(3)
    prev_close = _float(4)

    change = _float(31)
    change_pct = _float(32)

    # 如果字段不够或为空，尝试计算
    if change is None and price is not None and prev_close is not None and prev_close != 0:
        change = round(price - prev_close, 2)
        change_pct = round(change / prev_close * 100, 2)

    return {
        "code": code,
        "name": name,
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "open": _float(5),
        "high": _float(33),
        "low": _float(34),
        "prev_close": prev_close,
        "volume": _float(6),
        "amount": _float(36),
    }


def _fetch_via_tencent() -> list[dict]:
    """通过腾讯批量行情获取主要指数数据。"""
    codes_str = ",".join(_MAJOR_INDEX_CODES.keys())
    url = f"{_TENCENT_URL}{codes_str}"

    try:
        resp = http_get(url, encoding="gbk", headers=_HEADERS)
        text = resp.text if hasattr(resp, "text") else str(resp)
    except Exception:
        return []

    if not text:
        return []

    results = []
    lines = text.strip().split("\n")
    code_list = list(_MAJOR_INDEX_CODES.keys())

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 匹配对应的代码信息
        code_key = code_list[i] if i < len(code_list) else None
        meta = _MAJOR_INDEX_CODES.get(code_key, {}) if code_key else {}
        expected_name = meta.get("name", "")

        parsed = _parse_tencent_index_line(line, expected_name)
        if parsed:
            parsed["market"] = meta.get("market", "")
            if not parsed["name"] and expected_name:
                parsed["name"] = expected_name
            results.append(parsed)

    return results


def _fetch_via_sina() -> list[dict]:
    """通过新浪行情获取主要指数数据（备用）。"""
    codes_str = ",".join(_SINA_INDEX_CODES.keys())
    url = f"{_SINA_URL}{codes_str}"

    try:
        resp = http_get(url, encoding="gbk", headers={
            "User-Agent": _HEADERS["User-Agent"],
            "Referer": "https://finance.sina.com.cn/",
        })
        text = resp.text if hasattr(resp, "text") else str(resp)
    except Exception:
        return []

    if not text:
        return []

    results = []
    code_list = list(_SINA_INDEX_CODES.keys())
    name_list = list(_SINA_INDEX_CODES.values())

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "=" not in line:
            continue

        # 提取变量名确定是哪个指数
        var_part = line.split("=")[0]
        matched_name = ""
        for sina_code, idx_name in _SINA_INDEX_CODES.items():
            if sina_code in var_part:
                matched_name = idx_name
                break

        # 提取引号内数据
        match = re.search(r'"([^"]*)"', line)
        if not match:
            continue

        data_str = match.group(1)
        fields = data_str.split(",")

        if len(fields) >= 6:
            # 简化格式: 名称,当前点数,涨跌点数,涨跌幅,成交量,成交额
            results.append({
                "code": "",
                "name": matched_name or fields[0].strip(),
                "price": _safe_float(fields[1]),
                "change": _safe_float(fields[2]),
                "change_pct": _safe_float(fields[3]),
                "volume": _safe_float(fields[4]),
                "amount": _safe_float(fields[5]),
                "open": None,
                "high": None,
                "low": None,
                "prev_close": None,
                "market": "",
            })

    return results


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def major_indices() -> list[dict]:
    """主要指数快照

    获取全球主要指数的实时行情快照，覆盖A股、港股、美股主要指数。

    涵盖指数:
      - A股: 上证指数、深证成指、创业板指、科创50、北证50、
             沪深300、中证500、中证1000
      - 港股: 恒生指数、恒生国企指数
      - 美股: 纳斯达克、道琼斯、标普500

    Source: 腾讯批量行情
    备用: 新浪行情

    Returns:
        指数行情列表:
        [{code, name, price, change, change_pct, volume, amount, 
          open, high, low, prev_close, market}]
    """
    ck = make_key("major_indices")
    cached = cache_get(ck)
    if cached is not None:
        return cached

    # 主源: 腾讯行情
    result = _fetch_via_tencent()

    # 备源: 新浪行情
    if not result:
        result = _fetch_via_sina()

    if result:
        cache_set(ck, result, ttl=TTL_QUOTE)
    return result
