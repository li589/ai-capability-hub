#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宏观时间序列 (v9.0.0 新增)
============================
v8.0 的 MacroData.fetch_macro_indicator 只返回最新单点（items[0]），
无法做趋势判断（PMI 连续回升 vs 回落，是体制分类的重要输入）。

本模块补齐「宏观指标时间序列」：拉取近 N 期（月频约 60 期=5 年），
计算趋势方向/斜率/动量，供体制分类与自上而下报告复用。
不改动既有单点 API（独立新模块）。

用法:
    from stock_researcher.data.macro_series import MacroSeries
    s = MacroSeries().fetch_series("pmi", periods=24)
    print(s.trend, s.values[-1])
"""

from __future__ import annotations

import json
import math
import time
import urllib.request
from typing import Dict, List, Optional

try:
    from crawl_utils import safe_request
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False

# 指标 → (reportName, 过滤名)：与 MacroData.MACRO_REPORT 一致
MACRO_REPORT = {
    "gdp": ("RPT_ECONOMIC_GDP", "GDP同比"),
    "cpi": ("RPT_ECONOMIC_CPI", "CPI同比"),
    "ppi": ("RPT_ECONOMIC_PPI", "PPI同比"),
    "pmi": ("RPT_ECONOMIC_PMI", "PMI"),
    "m2": ("RPT_ECONOMIC_GJZB", "M2同比"),
    "lpr": ("RPT_LPR", ""),
}


class MacroSeriesResult:
    """宏观时间序列结果（轻量类，避免 dataclass 依赖）"""

    def __init__(self, indicator: str = "", values: Optional[List[float]] = None,
                 dates: Optional[List[str]] = None, trend: str = "未知",
                 slope: float = 0.0, momentum_3: float = 0.0,
                 latest: Optional[float] = None, note: str = ""):
        self.indicator = indicator
        self.values = list(values or [])
        self.dates = list(dates or [])
        self.trend = trend            # 回升/回落/走平/未知
        self.slope = slope            # 线性回归斜率（每期变化）
        self.momentum_3 = momentum_3  # 近3期环比动量（末值-3期前值）
        self.latest = latest
        self.note = note

    def get(self, key, default=None):
        return getattr(self, key, default)


def _slope_of(values: List[float]) -> float:
    """末段线性回归斜率（每期）。"""
    n = len(values)
    if n < 3:
        return 0.0
    y = values
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(y) / n
    num = sum((xs[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    return num / den if den else 0.0


def trend_label(slope: float, values: List[float], recent_n: int = 3) -> str:
    """趋势标签：结合整体斜率与近期动量。"""
    if len(values) < 4:
        return "数据不足"
    recent = values[-recent_n:]
    momentum = recent[-1] - recent[0]
    if slope > 0 and momentum > 0:
        return "回升"
    if slope < 0 and momentum < 0:
        return "回落"
    return "走平"


def build_result(indicator: str, values: List[float], dates: List[str],
                 note: str = "") -> MacroSeriesResult:
    """从数值序列构建结果（纯逻辑，离线可测）。"""
    slope = _slope_of(values)
    momentum_3 = (values[-1] - values[-3]) if len(values) >= 3 else 0.0
    return MacroSeriesResult(
        indicator=indicator, values=values, dates=dates,
        trend=trend_label(slope, values),
        slope=round(slope, 3),
        momentum_3=round(momentum_3, 3),
        latest=values[-1] if values else None,
        note=note,
    )


class MacroSeries:
    """宏观指标时间序列获取器。"""

    def fetch_series(self, indicator: str, periods: int = 24) -> MacroSeriesResult:
        """拉取指标最近 periods 期（月频）。失败返回空结果。"""
        report_cfg = MACRO_REPORT.get(indicator)
        if not report_cfg:
            return MacroSeriesResult(indicator=indicator, note=f"未知指标:{indicator}")
        report_name, cn_name = report_cfg
        filter_part = f"filter=(INDICATOR_NAME%3D%22{cn_name}%22)" if cn_name else ""
        url = (
            f"https://datacenter-web.eastmoney.com/api/data/v1/get?"
            f"reportName={report_name}&columns=ALL&{filter_part}"
            f"pageSize={max(periods, 12)}&pageIndex=1"
            f"&sortColumns=REPORT_DATE&sortTypes=1"   # 升序
        )
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, headers=headers, timeout=8)
                if isinstance(raw, tuple):
                    raw = raw[0]
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            data = json.loads(raw)
            rows = (data.get("result") or {}).get("data") or []
            values: List[float] = []
            dates: List[str] = []
            for r in rows:
                # 取值字段：VALUE（东财通用）或 INDICATOR_VALUE
                v = r.get("VALUE", r.get("INDICATOR_VALUE"))
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if math.isnan(fv):
                    continue
                values.append(fv)
                dates.append(str(r.get("REPORT_DATE", r.get("TIME", "")))[:10])
            if not values:
                return MacroSeriesResult(indicator=indicator, note="接口无数据")
            return build_result(indicator, values[-periods:], dates[-periods:],
                                note=f"东财{report_name}")
        except Exception as e:
            return MacroSeriesResult(indicator=indicator, note=f"获取失败: {e}")

    def fetch_all(self, indicators: Optional[List[str]] = None,
                  periods: int = 24) -> Dict[str, MacroSeriesResult]:
        """批量拉取多个指标序列。"""
        inds = indicators or ["pmi", "cpi", "ppi", "m2"]
        out: Dict[str, MacroSeriesResult] = {}
        for ind in inds:
            try:
                out[ind] = self.fetch_series(ind, periods)
            except Exception:
                out[ind] = MacroSeriesResult(indicator=ind, note="获取失败")
            time.sleep(0.3)
        return out


def fetch_macro_series(indicator: str, periods: int = 24) -> MacroSeriesResult:
    """便捷函数：宏观时间序列。"""
    return MacroSeries().fetch_series(indicator, periods)
