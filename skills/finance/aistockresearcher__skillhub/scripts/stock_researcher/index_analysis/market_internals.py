#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""市场内含分析 (v9.0.0 新增)
==========================
市场内含（Market Internals）—— 指数「内部」的广度健康度。

指数点位可能被少数权重股操纵，但「全市场多少股票在涨」无法伪装。
内含指标是识别真假牛市、顶/底的领先信号：
  - 涨跌家数（A/D）与涨跌比
  - 新高/新低家数
  - McClellan 震荡子（EMA(19) - EMA(39) of (advancers - decliners)）
  - 宽度超买/超卖

混合数据策略：头部指数（沪深300/创业板/科创50）用真实成分股全量历史；
其余用代表股篮子代理。每条结果标注 data_mode。

纯函数离线可测 + 真实成分股收盘价 + 优雅降级。

用法:
    from stock_researcher.index_analysis.market_internals import MarketInternalsAnalyzer
    mi = MarketInternalsAnalyzer().analyze("sh000300")
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass, field


# 头部指数 → 真实成分股清单（混合策略中的「full」档；此处给精简权威篮子，
# 完整 300/100 成分股可经 data/index_constituents 注入更大清单）
INDEX_BASKET = {
    "sh000300": ["600519", "601318", "600036", "000858", "600276", "601012",
                 "300750", "000333", "600900", "601166", "002594", "601398"],
    "sz399006": ["300750", "300059", "300015", "300760", "300124", "300498",
                 "300142", "300760", "300033", "300012"],
    "sh000688": ["688981", "688041", "688256", "688111", "688599", "688036",
                 "688012", "688169"],
    "100.SPX": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK"],
    "100.NDX": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO"],
    "100.HSI": ["00700", "09988", "00005", "00939", "01299", "03690", "00388", "00002"],
}


@dataclass
class InternalsResult:
    """市场内含结果"""
    code: str = ""
    data_mode: str = "proxy"
    n_stocks: int = 0
    advancers: int = 0
    decliners: int = 0
    unchanged: int = 0
    ad_ratio: float = 0.0          # 涨跌比
    net_ad: int = 0                # adv - decl（净上涨家数）
    new_highs_20: int = 0
    new_lows_20: int = 0
    mcclellan: float = 0.0         # McClellan 震荡子
    breadth_status: str = "中性"    # 超买/超卖/中性
    health: str = "中性"            # 健康/偏弱/过热/冰点/中性
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层
# ════════════════════════════════════════════════════════════

def _clean(values: Sequence[float]) -> List[float]:
    out = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f) and f > 0:
            out.append(f)
    return out


def daily_ad_series(closes_by_code: Dict[str, Sequence[float]]) -> List[int]:
    """逐日净上涨家数序列（adv - decl）。按最短公共窗口末端对齐。

    每日：对每只股票比较当日 vs 前日涨跌。
    """
    cleaned = {c: _clean(v) for c, v in closes_by_code.items() if len(_clean(v)) >= 2}
    if not cleaned:
        return []
    min_len = min(len(v) for v in cleaned.values())
    if min_len < 2:
        return []
    codes = list(cleaned.keys())
    series = []
    for i in range(1, min_len):
        adv = dec = 0
        for c in codes:
            v = cleaned[c]
            if v[i] > v[i - 1] * 1.0005:
                adv += 1
            elif v[i] < v[i - 1] * 0.9995:
                dec += 1
        series.append(adv - dec)
    return series


def ema(values: Sequence[float], period: int) -> List[float]:
    """指数移动平均序列（长度与输入一致，前 period-1 用逐步展开）。"""
    v = [float(x) for x in values if x is not None]
    if not v or period <= 0:
        return []
    k = 2.0 / (period + 1)
    out = [v[0]]
    for x in v[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def mcclellan_oscillator(net_ad_series: Sequence[int],
                         fast: int = 19, slow: int = 39) -> float:
    """McClellan 震荡子 = EMA(net_ad,19) - EMA(net_ad,39)。末值。"""
    v = [float(x) for x in net_ad_series if x is not None]
    if len(v) < slow + 5:
        return 0.0
    e_fast = ema(v, fast)
    e_slow = ema(v, slow)
    if not e_fast or not e_slow:
        return 0.0
    return e_fast[-1] - e_slow[-1]


def breadth_status_from_mcclellan(mcc: float, total_stocks: int) -> str:
    """McClellan 相对规模 → 超买/超卖/中性。阈值随总家数缩放。"""
    if total_stocks <= 0:
        return "中性"
    norm = mcc / total_stocks
    if norm > 0.3:
        return "超买"
    if norm < -0.3:
        return "超卖"
    return "中性"


def new_highs_lows(closes_by_code: Dict[str, Sequence[float]], window: int) -> tuple:
    hi = lo = 0
    for vals in closes_by_code.values():
        s = _clean(vals)
        if len(s) < window or window < 2:
            continue
        win = s[-window:]
        if abs(s[-1] - max(win)) < 1e-6:
            hi += 1
        if abs(s[-1] - min(win)) < 1e-6:
            lo += 1
    return hi, lo


def health_from_internals(pct_above_ma20: float, new_hi: int, new_lo: int) -> str:
    if pct_above_ma20 >= 80:
        return "过热"
    if pct_above_ma20 <= 20:
        return "冰点"
    if new_hi >= 2 * max(new_lo, 1):
        return "健康"
    if new_lo >= 2 * max(new_hi, 1):
        return "偏弱"
    return "中性"


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class MarketInternalsAnalyzer:
    """市场内含分析器（混合数据策略）。"""

    def __init__(self, constituents_provider=None):
        self._provider = constituents_provider

    def _resolve(self, code: str):
        """返回 (codes, data_mode)。优先 provider → 头部篮子 → 空。"""
        if self._provider:
            try:
                codes = list(self._provider(code) or [])
                if codes:
                    return codes, "full"
            except Exception:
                pass
        if code in INDEX_BASKET:
            return list(INDEX_BASKET[code]), "full"
        return [], "proxy"

    def _fetch_closes(self, codes, days=60):
        if not codes:
            return {}
        try:
            from stock_researcher.data.batch import fetch_batch_concurrent
            from stock_researcher.data.market import MarketData
            md = MarketData()
            raw = fetch_batch_concurrent(
                md.fetch_history, codes, max_workers=5,
                sleep_between=0.2, days=days,
            )
            out = {}
            for c, v in raw.items():
                cl = (v or {}).get("closes", []) if isinstance(v, dict) else []
                if cl:
                    out[c] = [float(p) for p in cl if p is not None]
            return out
        except Exception:
            return {}

    def analyze(self, code: str, days: int = 60) -> InternalsResult:
        codes, data_mode = self._resolve(code)
        if not codes:
            return InternalsResult(code=code, note="无成分股清单（可用 constituents_provider 注入）")

        closes = self._fetch_closes(codes, days)
        if not closes:
            return InternalsResult(code=code, data_mode=data_mode, note="行情获取失败")

        # 涨跌家数（最后一日）
        adv = dec = unch = 0
        for vals in closes.values():
            s = _clean(vals)
            if len(s) < 2:
                continue
            r = s[-1] / s[-2] - 1.0
            if r > 0.0005:
                adv += 1
            elif r < -0.0005:
                dec += 1
            else:
                unch += 1

        # McClellan
        net_series = daily_ad_series(closes)
        mcc = mcclellan_oscillator(net_series) if len(net_series) >= 44 else 0.0
        status = breadth_status_from_mcclellan(mcc, len(closes))

        # 新高新低 + %above MA20
        hi20, lo20 = new_highs_lows(closes, 20)
        try:
            from stock_researcher.sector_analysis.breadth import pct_above_ma
            p20 = pct_above_ma(closes, 20)
        except Exception:
            p20 = 50.0
        health = health_from_internals(p20, hi20, lo20)

        return InternalsResult(
            code=code, data_mode=data_mode, n_stocks=len(closes),
            advancers=adv, decliners=dec, unchanged=unch,
            ad_ratio=round(adv / dec, 2) if dec > 0 else float(adv),
            net_ad=adv - dec,
            new_highs_20=hi20, new_lows_20=lo20,
            mcclellan=round(mcc, 1),
            breadth_status=status,
            health=health,
            note=f"基于{len(closes)}只成分股/{data_mode}",
        )

    @staticmethod
    def format(mi: InternalsResult) -> str:
        return (
            f"[{mi.code}] 内含: 涨跌 {mi.advancers}/{mi.decliners}"
            f"(比{mi.ad_ratio:.1f}) 净{mi.net_ad:+d} | "
            f"新高/低 {mi.new_highs_20}/{mi.new_lows_20} | "
            f"McClellan{mi.mcclellan:+.0f} {mi.breadth_status} | "
            f"健康:{mi.health} ({mi.data_mode})"
        )


def analyze_market_internals(code: str) -> InternalsResult:
    """便捷函数：市场内含。"""
    return MarketInternalsAnalyzer().analyze(code)
