#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""市场结构分析 (v9.0.0 新增)
==========================
市场结构（Market Structure）—— 用「高低点序列」客观判定趋势。

均线、RSI 等滞后且易震荡；而「更高的高点 HH + 更高的低点 HL」是趋势最纯粹的定义。
本模块用摆动点（swing pivots）识别结构，避免主观画线。

计算：
  - 摆动高点/低点（枢轴）
  - 趋势结构：HH-HL（上升）/ LH-LL（下降）/ 纠缠（震荡）
  - 关键位：近期枢轴阻力/支撑、ATR、距 MA200/52 周高低
  - 结构破位信号：最近低点被跌破（上升结构转弱）

纯函数离线可测 + 优雅降级。

用法:
    from stock_researcher.index_analysis.market_structure import MarketStructureAnalyzer
    ms = MarketStructureAnalyzer().analyze("sh000001")
    print(ms.trend_structure, ms.support, ms.resistance)
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple
from dataclasses import dataclass, field


@dataclass
class StructureResult:
    """市场结构结果"""
    code: str = ""
    trend_structure: str = "未知"     # 上升/下降/震荡/未知
    structure_strength: float = 0.0   # -100..+100（>0 上升结构强度）
    swing_highs: List[float] = field(default_factory=list)
    swing_lows: List[float] = field(default_factory=list)
    resistance: float = 0.0           # 近期枢轴阻力
    support: float = 0.0              # 近期枢轴支撑
    atr: float = 0.0                  # 14 期 ATR（价格量级）
    distance_to_resistance: float = 0.0   # 距阻力(%)
    distance_to_support: float = 0.0       # 距支撑(%)
    broken_down: bool = False         # 最近低点被跌破（上升结构转弱）
    broken_up: bool = False           # 最近高点被突破（下降结构转强）
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


def find_swing_highs(prices: Sequence[float], k: int = 3) -> List[float]:
    """摆动高点：局部窗口(2k+1)内最高的点。k 为左右各看几期。"""
    s = _clean(prices)
    if len(s) < 2 * k + 1:
        return []
    highs = []
    for i in range(k, len(s) - k):
        window = s[i - k:i + k + 1]
        if s[i] == max(window) and s[i] > s[i - 1] and s[i] > s[i + 1]:
            highs.append(s[i])
    return highs


def find_swing_lows(prices: Sequence[float], k: int = 3) -> List[float]:
    """摆动低点。"""
    s = _clean(prices)
    if len(s) < 2 * k + 1:
        return []
    lows = []
    for i in range(k, len(s) - k):
        window = s[i - k:i + k + 1]
        if s[i] == min(window) and s[i] < s[i - 1] and s[i] < s[i + 1]:
            lows.append(s[i])
    return lows


def trend_structure_from_swings(
    highs: Sequence[float], lows: Sequence[float],
) -> Tuple[str, float]:
    """由最近几个摆动高低点判定结构。

    HH（更高高点）+ HL（更高低点）→ 上升
    LH（更低高点）+ LL（更低低点）→ 下降
    混合/不足 → 震荡
    返回 (结构标签, 强度 -100..+100)。
    """
    h = [float(x) for x in highs if x is not None]
    l = [float(x) for x in lows if x is not None]
    if len(h) < 2 or len(l) < 2:
        return "震荡", 0.0

    # 取最近 N 个比较方向
    hh_count = sum(1 for i in range(1, min(len(h), 4)) if h[-i] > h[-i - 1])   # 高点抬高
    lh_count = sum(1 for i in range(1, min(len(h), 4)) if h[-i] < h[-i - 1])
    hl_count = sum(1 for i in range(1, min(len(l), 4)) if l[-i] > l[-i - 1])   # 低点抬高
    ll_count = sum(1 for i in range(1, min(len(l), 4)) if l[-i] < l[-i - 1])

    bull = hh_count + hl_count
    bear = lh_count + ll_count
    total = bull + bear
    if total == 0:
        return "震荡", 0.0
    score = (bull - bear) / total * 100.0
    if score > 34:
        return "上升", score
    if score < -34:
        return "下降", score
    return "震荡", score


def atr(prices: Sequence[float], n: int = 14) -> float:
    """简化 ATR：用日收益绝对值的 n 期均值近似（无 high/low 时）。

    真 ATR 需 (high-low) 与前收；这里价格序列只有 close，用 |Δclose| 均值近似 True Range。
    """
    s = _clean(prices)
    if len(s) < n + 1 or n <= 0:
        return 0.0
    trs = [abs(s[i] - s[i - 1]) for i in range(len(s) - n, len(s)) if s[i - 1] > 0]
    if not trs:
        return 0.0
    return sum(trs) / len(trs)


def nearest_levels(
    prices: Sequence[float],
    swing_highs: Sequence[float],
    swing_lows: Sequence[float],
) -> Tuple[float, float]:
    """最近的上方阻力（≤现价的最高摆动高 / 否则 52w 高）与下方支撑。"""
    s = _clean(prices)
    if not s:
        return 0.0, 0.0
    last = s[-1]
    highs_below = [h for h in swing_highs if h >= last]
    lows_below = [l for l in swing_lows if l <= last]
    resistance = min(highs_below) if highs_below else max(s)
    support = max(lows_below) if lows_below else min(s)
    return resistance, support


def break_signals(
    prices: Sequence[float],
    swing_highs: Sequence[float],
    swing_lows: Sequence[float],
) -> Tuple[bool, bool]:
    """最近摆动低点被跌破(broken_down)；最近摆动高点被突破(broken_up)。"""
    s = _clean(prices)
    if not s:
        return False, False
    last = s[-1]
    broken_down = bool(swing_lows) and last < swing_lows[-1] * 0.995
    broken_up = bool(swing_highs) and last > swing_highs[-1] * 1.005
    return broken_down, broken_up


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class MarketStructureAnalyzer:
    """市场结构分析器。"""

    def analyze(self, code: str, days: int = 160) -> StructureResult:
        prices = self._fetch_prices(code, days)
        if not prices or len(prices) < 30:
            return StructureResult(code=code, note="行情数据不足")
        return self.analyze_from_prices(code, prices)

    def analyze_from_prices(self, code: str, prices: Sequence[float]) -> StructureResult:
        s = _clean(prices)
        sh = find_swing_highs(s, k=3)
        sl = find_swing_lows(s, k=3)
        structure, strength = trend_structure_from_swings(sh, sl)
        res, sup = nearest_levels(s, sh, sl)
        a = atr(s, 14)
        last = s[-1]
        bdown, bup = break_signals(s, sh, sl)

        dist_res = (last / res - 1.0) * 100 if res > 0 else 0.0
        dist_sup = (last / sup - 1.0) * 100 if sup > 0 else 0.0

        return StructureResult(
            code=code,
            trend_structure=structure,
            structure_strength=round(strength, 1),
            swing_highs=[round(x, 2) for x in sh[-6:]],
            swing_lows=[round(x, 2) for x in sl[-6:]],
            resistance=round(res, 2),
            support=round(sup, 2),
            atr=round(a, 4),
            distance_to_resistance=round(dist_res, 2),
            distance_to_support=round(dist_sup, 2),
            broken_down=bdown,
            broken_up=bup,
            note=f"基于{len(s)}日摆动点(k=3)",
        )

    def _fetch_prices(self, code: str, days: int) -> List[float]:
        try:
            c = str(code).lower()
            if c.startswith(("100.", "idx:")):
                from stock_researcher.data.global_market import fetch_global_kline
                kl = fetch_global_kline(f"idx:{code}", days=days) or []
                return [float(k.get("close", 0)) for k in kl
                        if isinstance(k, dict) and k.get("close")]
            from stock_researcher.data.market import MarketData
            md = MarketData()
            if c.startswith("sh") or c.startswith("sz"):
                k = md.fetch_history(c[2:], days=days, prefix=c[:2]) or {}
            else:
                k = md.fetch_history(code, days=days) or {}
            return [float(p) for p in k.get("closes", []) if p is not None]
        except Exception:
            return []

    @staticmethod
    def format(ms: StructureResult) -> str:
        brk = []
        if ms.broken_down:
            brk.append("⚠低点破位")
        if ms.broken_up:
            brk.append("高点突破")
        brk_s = (" ".join(brk)) if brk else "无破位"
        return (
            f"市场结构: {ms.trend_structure}(强度{ms.structure_strength:+.0f}) | "
            f"阻力{ms.resistance}({ms.distance_to_resistance:+.1f}%) "
            f"支撑{ms.support}({ms.distance_to_support:+.1f}%) ATR{ms.atr:.2f} | {brk_s}"
        )


def analyze_market_structure(code: str) -> StructureResult:
    """便捷函数：市场结构。"""
    return MarketStructureAnalyzer().analyze(code)
