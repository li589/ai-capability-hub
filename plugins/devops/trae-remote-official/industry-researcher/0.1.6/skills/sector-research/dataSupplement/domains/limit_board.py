# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 涨跌停/打板
=============================================

功能概览:
  - zt_pool: 涨停池（连板数/封板资金/首板时间/行业）
  - zb_pool: 炸板池（曾涨停后开板）
  - dt_pool: 跌停池
  - yesterday_zt: 昨日涨停今日表现
  - limit_up_reasons: 涨停原因揭秘（题材/封板成功率/板型）
  - sentiment_score: 打板情绪速算（炸板率/连板梯队/最高连板/晋级率）

数据源:
  - 主源: akshare（stock_zt_pool_em 系列）
  - 备源: 同花顺涨停揭秘接口
  - 计算: 基于涨停池+炸板池联合计算情绪指标
"""

from __future__ import annotations

import sys
import os
from datetime import date as _date, datetime as _datetime
from typing import Optional

# 路径设置: 确保 core/ 和 providers/ 可导入
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.cache import cache_get, cache_set, make_key, TTL_QUOTE, TTL_NEWS
from core.throttle import throttled_get

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _today_str() -> str:
    """返回今日日期字符串，格式 YYYYMMDD。"""
    return _date.today().strftime("%Y%m%d")


def _normalize_date(date: Optional[str]) -> str:
    """标准化日期参数为 YYYYMMDD 格式。
    
    支持输入:
      - None → 今天
      - "2024-01-15" → "20240115"
      - "20240115" → "20240115"
    """
    if date is None:
        return _today_str()
    return date.replace("-", "").replace("/", "")


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数。"""
    if val is None or val == "" or val == "—" or val == "-":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    """安全转换为整数。"""
    if val is None or val == "" or val == "—" or val == "-":
        return None
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# akshare 可用性检测
# ---------------------------------------------------------------------------

_akshare_available = True
try:
    import akshare
except ImportError:
    _akshare_available = False


def _safe_to_list(df) -> list:
    """安全将 DataFrame 转换为字典列表。"""
    if df is None:
        return []
    try:
        if hasattr(df, "to_dict"):
            return df.to_dict("records")
        return list(df) if df is not None else []
    except (TypeError, ValueError, AttributeError):
        return []


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def zt_pool(date: str = None) -> list[dict]:
    """涨停池（连板数/封板资金/首板时间/行业）

    获取指定日期的涨停股票列表，包含连板天数、封板资金、首板时间、
    所属行业等核心打板数据。

    Source: akshare stock_zt_pool_em
    备用: 同花顺涨停揭秘接口

    Args:
        date: 交易日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当天

    Returns:
        涨停股列表，每项包含:
        [{code, name, price, change_pct, first_limit_time, 
          continuous_days, seal_amount, industry, ...}]
    """
    dt = _normalize_date(date)
    
    # 缓存检查
    ck = make_key("zt_pool", dt)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []
    
    # 主源: akshare
    if _akshare_available:
        try:
            df = akshare.stock_zt_pool_em(date=dt)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("代码", item.get("code", ""))).zfill(6),
                    "name": item.get("名称", item.get("name", "")),
                    "price": _safe_float(item.get("最新价", item.get("price"))),
                    "change_pct": _safe_float(item.get("涨跌幅", item.get("change_pct"))),
                    "turnover_rate": _safe_float(item.get("换手率", item.get("turnover_rate"))),
                    "seal_amount": _safe_float(item.get("封板资金", item.get("seal_amount"))),
                    "first_limit_time": item.get("首次封板时间", item.get("first_limit_time", "")),
                    "last_limit_time": item.get("最后封板时间", item.get("last_limit_time", "")),
                    "open_count": _safe_int(item.get("炸板次数", item.get("open_count"))),
                    "continuous_days": _safe_int(item.get("连板数", item.get("continuous_days"))),
                    "industry": item.get("所属行业", item.get("industry", "")),
                })
        except Exception:
            pass

    # 备源: 同花顺涨停揭秘
    if not result:
        try:
            from providers.tonghuashun import limit_up_detail
            ths_date = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}"
            ths_data = limit_up_detail(ths_date)
            for item in ths_data:
                result.append({
                    "code": item.get("code", ""),
                    "name": item.get("name", ""),
                    "price": None,
                    "change_pct": None,
                    "turnover_rate": None,
                    "seal_amount": _safe_float(item.get("seal_amount")),
                    "first_limit_time": item.get("first_limit_time", ""),
                    "last_limit_time": item.get("last_limit_time", ""),
                    "open_count": _safe_int(item.get("open_count")),
                    "continuous_days": None,
                    "industry": item.get("theme", ""),
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_NEWS)
    return result


def zb_pool(date: str = None) -> list[dict]:
    """炸板池（曾涨停后开板）

    获取指定日期曾触及涨停但未能封住的股票列表。

    Source: akshare stock_zt_pool_zbgc_em

    Args:
        date: 交易日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当天

    Returns:
        炸板股列表，每项包含:
        [{code, name, price, change_pct, first_limit_time, 
          open_time, seal_amount_max, ...}]
    """
    dt = _normalize_date(date)

    ck = make_key("zb_pool", dt)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    if _akshare_available:
        try:
            df = akshare.stock_zt_pool_zbgc_em(date=dt)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("代码", item.get("code", ""))).zfill(6),
                    "name": item.get("名称", item.get("name", "")),
                    "price": _safe_float(item.get("最新价", item.get("price"))),
                    "change_pct": _safe_float(item.get("涨跌幅", item.get("change_pct"))),
                    "turnover_rate": _safe_float(item.get("换手率", item.get("turnover_rate"))),
                    "first_limit_time": item.get("首次封板时间", item.get("first_limit_time", "")),
                    "open_time": item.get("炸板时间", item.get("open_time", "")),
                    "seal_amount_max": _safe_float(item.get("最大封板资金", item.get("seal_amount_max"))),
                    "industry": item.get("所属行业", item.get("industry", "")),
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_NEWS)
    return result


def dt_pool(date: str = None) -> list[dict]:
    """跌停池

    获取指定日期跌停股票列表。

    Source: akshare stock_zt_pool_dtgc_em

    Args:
        date: 交易日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当天

    Returns:
        跌停股列表，每项包含:
        [{code, name, price, change_pct, turnover_rate, 
          seal_amount, first_limit_time, continuous_days, ...}]
    """
    dt = _normalize_date(date)

    ck = make_key("dt_pool", dt)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    if _akshare_available:
        try:
            df = akshare.stock_zt_pool_dtgc_em(date=dt)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("代码", item.get("code", ""))).zfill(6),
                    "name": item.get("名称", item.get("name", "")),
                    "price": _safe_float(item.get("最新价", item.get("price"))),
                    "change_pct": _safe_float(item.get("涨跌幅", item.get("change_pct"))),
                    "turnover_rate": _safe_float(item.get("换手率", item.get("turnover_rate"))),
                    "seal_amount": _safe_float(item.get("封板资金", item.get("seal_amount"))),
                    "first_limit_time": item.get("首次封板时间", item.get("first_limit_time", "")),
                    "continuous_days": _safe_int(item.get("连板数", item.get("continuous_days"))),
                    "industry": item.get("所属行业", item.get("industry", "")),
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_NEWS)
    return result


def yesterday_zt(date: str = None) -> list[dict]:
    """昨日涨停今日表现

    获取前一交易日涨停的股票在今天的表现（是否连板/开盘情况等）。

    Source: akshare stock_zt_pool_previous_em

    Args:
        date: 交易日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当天

    Returns:
        昨日涨停股今日表现列表:
        [{code, name, price, change_pct, open_pct, 
          is_limit_up_again, seal_amount, ...}]
    """
    dt = _normalize_date(date)

    ck = make_key("yesterday_zt", dt)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    if _akshare_available:
        try:
            df = akshare.stock_zt_pool_previous_em(date=dt)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("代码", item.get("code", ""))).zfill(6),
                    "name": item.get("名称", item.get("name", "")),
                    "price": _safe_float(item.get("最新价", item.get("price"))),
                    "change_pct": _safe_float(item.get("涨跌幅", item.get("change_pct"))),
                    "open_pct": _safe_float(item.get("开盘涨幅", item.get("open_pct"))),
                    "turnover_rate": _safe_float(item.get("换手率", item.get("turnover_rate"))),
                    "is_limit_up_again": item.get("是否再次涨停", item.get("is_limit_up_again", False)),
                    "seal_amount": _safe_float(item.get("封板资金", item.get("seal_amount"))),
                    "industry": item.get("所属行业", item.get("industry", "")),
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_NEWS)
    return result


def limit_up_reasons(date: str = None) -> list[dict]:
    """涨停原因揭秘（题材/封板成功率/板型）

    获取涨停板的原因归因分析，包含涨停驱动题材、封板成功率、
    涨停类型（首板/连板等）。

    Source: 同花顺 limit_up_detail

    Args:
        date: 交易日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当天

    Returns:
        涨停原因列表:
        [{code, name, reason, theme, first_limit_time, 
          limit_up_type, seal_amount, seal_rate, ...}]
    """
    dt = _normalize_date(date)

    ck = make_key("limit_up_reasons", dt)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    # 主源: 同花顺涨停揭秘
    try:
        from providers.tonghuashun import limit_up_detail
        ths_date = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}"
        ths_data = limit_up_detail(ths_date)
        if ths_data:
            result = ths_data
    except Exception:
        pass

    # 备源: akshare 涨停池 + 行业信息补充
    if not result and _akshare_available:
        try:
            df = akshare.stock_zt_pool_em(date=dt)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("代码", item.get("code", ""))).zfill(6),
                    "name": item.get("名称", item.get("name", "")),
                    "reason": item.get("涨停原因", item.get("所属行业", "")),
                    "theme": item.get("所属行业", ""),
                    "first_limit_time": item.get("首次封板时间", ""),
                    "last_limit_time": item.get("最后封板时间", ""),
                    "open_count": _safe_int(item.get("炸板次数")),
                    "limit_up_type": f"{item.get('连板数', 1)}板",
                    "seal_amount": _safe_float(item.get("封板资金")),
                    "seal_rate": None,
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_NEWS)
    return result


def sentiment_score(date: str = None) -> dict:
    """打板情绪速算（炸板率/连板梯队/最高连板/晋级率）

    基于涨停池和炸板池数据综合计算市场短线情绪指标:
    - 炸板率: 炸板数 / (涨停数 + 炸板数)
    - 连板梯队: 各连板层级的股票数量分布
    - 最高连板: 当日最高连板天数
    - 晋级率: 二板及以上数量 / 前日涨停总数

    Computed from: zt_pool + zb_pool data

    Args:
        date: 交易日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当天

    Returns:
        情绪评分字典:
        {zb_rate, max_continuous, ladder: {1板: N, 2板: N, ...}, 
         promotion_rate, zt_count, zb_count, dt_count}
    """
    dt = _normalize_date(date)

    ck = make_key("sentiment_score", dt)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    # 获取涨停池和炸板池数据
    zt_data = zt_pool(dt)
    zb_data = zb_pool(dt)
    dt_data = dt_pool(dt)

    zt_count = len(zt_data)
    zb_count = len(zb_data)
    dt_count = len(dt_data)

    # 炸板率
    total_attempted = zt_count + zb_count
    zb_rate = round(zb_count / total_attempted * 100, 2) if total_attempted > 0 else 0.0

    # 连板梯队统计
    ladder = {}
    max_continuous = 0
    for item in zt_data:
        days = item.get("continuous_days")
        if days is not None and isinstance(days, (int, float)):
            days = int(days)
            key = f"{days}板"
            ladder[key] = ladder.get(key, 0) + 1
            if days > max_continuous:
                max_continuous = days
        else:
            # 默认首板
            ladder["1板"] = ladder.get("1板", 0) + 1

    # 晋级率 = 二板及以上数量 / 总涨停数
    advanced_count = sum(v for k, v in ladder.items() if k != "1板")
    promotion_rate = round(advanced_count / zt_count * 100, 2) if zt_count > 0 else 0.0

    result = {
        "date": dt,
        "zt_count": zt_count,
        "zb_count": zb_count,
        "dt_count": dt_count,
        "zb_rate": zb_rate,
        "max_continuous": max_continuous,
        "ladder": ladder,
        "promotion_rate": promotion_rate,
        "total_attempted": total_attempted,
    }

    cache_set(ck, result, ttl=TTL_NEWS)
    return result
