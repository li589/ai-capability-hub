#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""板块宽度分析 (v9.0.0 新增)
============================
市场/板块宽度（Breadth）—— 判断行情健康度的关键内含指标。

「指数在涨但只有少数权重股在涨」是典型的顶背离预警。宽度指标衡量
参与上涨的成分股比例，是识别真假牛市、顶/底的领先信号。

本模块计算：
  - % above MA：成分股现价在 MA20/MA50/MA200 之上的占比
  - 涨跌家数：近 N 期上涨/下跌成分股数
  - 新高/新低：创 N 日新高/新低的成分股数
  - Zweig 宽度推动：>%上穿 0.5 后快速升至 0.615 的强势确认信号
  - 宽度背离：价格创新高但宽度未创新高 → 顶背离预警

设计要点：纯函数离线可测 + 真实成分股收盘价 + 优雅降级。

用法:
    from stock_researcher.sector_analysis.breadth import SectorBreadth, analyze_breadth
    b = SectorBreadth().analyze("电子", market="cn")
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass, field


@dataclass
class BreadthResult:
    """板块宽度结果"""
    sector: str
    data_mode: str = "proxy"
    n_stocks: int = 0

    pct_above_ma20: float = 0.0     # 0-100
    pct_above_ma50: float = 0.0
    pct_above_ma200: float = 0.0

    advancers: int = 0              # 近 lookback 期上涨家数
    decliners: int = 0              # 下跌家数
    ad_ratio: float = 0.0           # 涨跌比（adv/decl，decl=0 时取大数）

    new_highs_20: int = 0           # 创 20 日新高家数
    new_lows_20: int = 0            # 创 20 日新低
    new_highs_60: int = 0
    new_lows_60: int = 0

    breadth_thrust: bool = False    # Zweig 宽度推动触发
    divergence: str = "无"          # 无/顶背离/底背离（需 proxy 配合）
    health: str = "中性"            # 健康/过热/冰点/中性
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


def sma(values: Sequence[float], n: int) -> Optional[float]:
    s = _clean(values)
    if n <= 0 or len(s) < n:
        return None
    return sum(s[-n:]) / n


def pct_above_ma(closes_by_code: Dict[str, Sequence[float]], ma_n: int) -> float:
    """计算成分股现价在 MA(ma_n) 之上的占比（0-100）。

    数据不足（序列短于 ma_n）的股票计入分母但不算「之上」。
    """
    if not closes_by_code:
        return 0.0
    above = 0
    total = 0
    for code, vals in closes_by_code.items():
        s = _clean(vals)
        if len(s) < 2:
            continue
        total += 1
        ma = sma(s, ma_n)
        if ma is not None and s[-1] > ma:
            above += 1
    return (above / total * 100.0) if total else 0.0


def adv_dec_counts(
    closes_by_code: Dict[str, Sequence[float]], lookback: int = 20,
) -> tuple:
    """近 lookback 期上涨/下跌成分股家数。"""
    adv = dec = 0
    for vals in closes_by_code.values():
        s = _clean(vals)
        if len(s) <= lookback or lookback <= 0:
            continue
        ret = s[-1] / s[-1 - lookback] - 1.0
        if ret > 0.0005:    # 忽略近似走平
            adv += 1
        elif ret < -0.0005:
            dec += 1
    return adv, dec


def new_highs_lows(
    closes_by_code: Dict[str, Sequence[float]], window: int = 20,
) -> tuple:
    """创 window 日新高 / 新低 的家数（现价 = window 内最高/最低）。"""
    hi = lo = 0
    for vals in closes_by_code.values():
        s = _clean(vals)
        if len(s) < window or window < 2:
            continue
        win = s[-window:]
        mx, mn = max(win), min(win)
        # 现价贴近极值（容差 1e-6）即计
        if abs(s[-1] - mx) < 1e-6:
            hi += 1
        if abs(s[-1] - mn) < 1e-6:
            lo += 1
    return hi, lo


def zweig_thrust_series(
    closes_by_code: Dict[str, Sequence[float]], ma_n: int = 20,
) -> List[float]:
    """逐日计算 %above_MA(ma_n) 序列（用于检测 Zweig 推动）。

    返回长度 = 公共窗口长度（末端对齐到最短）。计算成本随成分股数线性增长，
    建议仅在 full 模式或小篮子下调用。
    """
    cleaned = {c: _clean(v) for c, v in closes_by_code.items() if len(_clean(v)) >= ma_n + 2}
    if not cleaned:
        return []
    min_len = min(len(v) for v in cleaned.values())
    if min_len < ma_n + 2:
        return []
    codes = list(cleaned.keys())
    series = []
    # 从第 ma_n 个点起算（每个位置回看 ma_n）
    for i in range(ma_n, min_len):
        above = 0
        for c in codes:
            v = cleaned[c]
            ma = sum(v[i - ma_n + 1: i + 1]) / ma_n
            if v[i] > ma:
                above += 1
        series.append(above / len(codes))
    return series


def detect_thrust(pct_series: Sequence[float]) -> bool:
    """Zweig 宽度推动：%above_MA 序列在 10 期内由 ≤0.5 升至 ≥0.615。"""
    s = [float(x) for x in pct_series if x is not None]
    if len(s) < 2:
        return False
    window = s[-10:]
    start = window[0]
    return start <= 0.5 and max(window) >= 0.615


def health_label(pct_above_ma20: float, pct_above_ma50: float) -> str:
    """宽度健康度标签。"""
    avg = (pct_above_ma20 + pct_above_ma50) / 2.0
    if pct_above_ma20 >= 80:
        return "过热"      # 几乎全线在均线之上 → 短期过热
    if avg <= 20:
        return "冰点"      # 极度超卖，常伴底部
    if avg >= 60:
        return "健康"
    if avg <= 35:
        return "偏弱"
    return "中性"


def detect_divergence(
    proxy_closes: Sequence[float], pct_series: Sequence[float],
) -> str:
    """价格 vs 宽度背离检测（需 proxy 与 %above 序列末端对齐）。

    价格创新高但宽度未创新高 → 顶背离；价格创新低但宽度未创新低 → 底背离。
    """
    p = _clean(proxy_closes)
    b = [float(x) for x in pct_series if x is not None]
    if len(p) < 20 or len(b) < 20:
        return "无"
    m = min(len(p), len(b))
    p, b = p[-m:], b[-m:]
    half = m // 2
    price_new_hi = p[-1] >= max(p[:half]) * 0.999
    price_new_lo = p[-1] <= min(p[:half]) * 1.001
    breadth_new_hi = b[-1] >= max(b[:half]) * 0.999
    breadth_new_lo = b[-1] <= min(b[:half]) * 1.001
    if price_new_hi and not breadth_new_hi:
        return "顶背离"
    if price_new_lo and not breadth_new_lo:
        return "底背离"
    return "无"


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class SectorBreadth:
    """板块宽度分析器。"""

    def __init__(self, constituents_provider=None):
        self._provider = constituents_provider

    def _resolve(self, sector: str, market: str):
        if self._provider:
            try:
                codes = list(self._provider(sector, market) or [])
                if codes:
                    return codes, "full"
            except Exception:
                pass
        try:
            from stock_researcher.sector_analysis.sectors import SectorAnalyzer
            return list(SectorAnalyzer.ALL_SECTOR_MAPS.get(market, {}).get(sector, [])), "proxy"
        except Exception:
            return [], "proxy"

    def _fetch_closes(self, codes, days=220):
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

    def analyze(
        self, sector: str, market: str = "cn", days: int = 220,
    ) -> BreadthResult:
        """分析板块宽度。days 默认 220（覆盖 MA200 + 余量）。"""
        codes, data_mode = self._resolve(sector, market)
        if not codes:
            return BreadthResult(sector=sector, note="无成分股数据")

        closes = self._fetch_closes(codes, days)
        if not closes:
            return BreadthResult(sector=sector, data_mode=data_mode, note="行情获取失败")

        p20 = pct_above_ma(closes, 20)
        p50 = pct_above_ma(closes, 50)
        p200 = pct_above_ma(closes, 200)
        adv, dec = adv_dec_counts(closes, lookback=20)
        hi20, lo20 = new_highs_lows(closes, 20)
        hi60, lo60 = new_highs_lows(closes, 60)

        # Zweig 推动（仅 full/小篮子下计算以控制成本）
        pct_series = []
        thrust = False
        try:
            pct_series = zweig_thrust_series(closes, 20)
            thrust = detect_thrust(pct_series)
        except Exception:
            pass

        # 背离需 proxy：用等权代理近似
        div = "无"
        try:
            from stock_researcher.sector_analysis.relative_strength import align_and_rebase
            proxy, _ = align_and_rebase(closes)
            if proxy and pct_series:
                div = detect_divergence(proxy, pct_series)
        except Exception:
            pass

        ad_ratio = (adv / dec) if dec > 0 else float(adv)

        return BreadthResult(
            sector=sector, data_mode=data_mode, n_stocks=len(closes),
            pct_above_ma20=round(p20, 1),
            pct_above_ma50=round(p50, 1),
            pct_above_ma200=round(p200, 1),
            advancers=adv, decliners=dec,
            ad_ratio=round(ad_ratio, 2),
            new_highs_20=hi20, new_lows_20=lo20,
            new_highs_60=hi60, new_lows_60=lo60,
            breadth_thrust=thrust,
            divergence=div,
            health=health_label(p20, p50),
            note=f"基于{len(closes)}只成分股",
        )

    @staticmethod
    def format(b: BreadthResult) -> str:
        return (
            f"[{b.sector}] 宽度: MA20↑{b.pct_above_ma20:.0f}% "
            f"MA50↑{b.pct_above_ma50:.0f}% | 涨跌 {b.advancers}/{b.decliners} "
            f"| 新高/低20日 {b.new_highs_20}/{b.new_lows_20} | "
            f"{'宽度推动🔥' if b.breadth_thrust else ''}"
            f"{'⚠'+b.divergence if b.divergence != '无' else ''} "
            f"健康度:{b.health} ({b.data_mode})"
        )


def analyze_breadth(sector: str, market: str = "cn") -> BreadthResult:
    """便捷函数：板块宽度。"""
    return SectorBreadth().analyze(sector, market=market)
