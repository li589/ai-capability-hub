#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""板块离散度分析 (v9.0.0 新增)
==============================
横截面离散度（Cross-sectional Dispersion）—— 判断板块内部一致性。

- 高离散 + 齐涨：趋势确立，龙头领涨
- 低离散 / 分化：见顶/见底信号（齐涨后开始分道扬镳）
- 集中度过高：少数龙头撑场，行情根基不稳

本模块计算：
  - 横截面标准差：成分股区间收益的离散度（年化可比）
  - 龙头-落后差：头部五分位均收益 - 尾部五分位均收益
  - 集中度：涨幅最大成分股对板块平均的贡献占比
  - 一致性标签：齐涨/齐跌/分化/中性

纯函数离线可测 + 真实成分股收盘价 + 优雅降级。

用法:
    from stock_researcher.sector_analysis.dispersion import SectorDispersion, analyze_dispersion
    d = SectorDispersion().analyze("计算机", market="cn")
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass, field


@dataclass
class DispersionResult:
    """板块离散度结果"""
    sector: str
    data_mode: str = "proxy"
    n_stocks: int = 0
    lookback: int = 20

    mean_return: float = 0.0       # 成分股区间均收益(%)
    median_return: float = 0.0
    stdev_return: float = 0.0      # 横截面标准差(%)
    leader_return: float = 0.0     # 头部五分位均收益(%)
    lagger_return: float = 0.0     # 尾部五分位均收益(%)
    leader_lagger_gap: float = 0.0 # 龙头-落后差(%)
    top1_contrib: float = 0.0      # 涨幅最大者相对均值的贡献占比(0-1+)
    skew: float = 0.0              # 偏度：>0 龙头拉动少数大涨
    cohesion: str = "中性"         # 齐涨/齐跌/分化/中性
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层
# ════════════════════════════════════════════════════════════

def period_returns(closes_by_code: Dict[str, Sequence[float]], lookback: int) -> List[float]:
    """计算各成分股最近 lookback 期收益率（小数，如 0.05=5%）。

    数据不足的股票跳过。返回有序列表（按输入顺序）。
    """
    rets = []
    if lookback <= 0:
        return rets
    for vals in closes_by_code.values():
        s = [float(v) for v in vals if _is_pos(v)]
        if len(s) <= lookback or s[-1 - lookback] <= 0:
            continue
        rets.append(s[-1] / s[-1 - lookback] - 1.0)
    return rets


def _is_pos(v) -> bool:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f) and f > 0


def mean(values: Sequence[float]) -> float:
    v = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    return sum(v) / len(v) if v else 0.0


def median(values: Sequence[float]) -> float:
    v = sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    n = len(v)
    if n == 0:
        return 0.0
    mid = n // 2
    return v[mid] if n % 2 == 1 else (v[mid - 1] + v[mid]) / 2.0


def stdev(values: Sequence[float]) -> float:
    """样本标准差（n-1）。"""
    v = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    n = len(v)
    if n < 2:
        return 0.0
    m = sum(v) / n
    var = sum((x - m) ** 2 for x in v) / (n - 1)
    return math.sqrt(var)


def skewness(values: Sequence[float]) -> float:
    """偏度（Fisher-Pearson，样本）。需 ≥3 个点，否则 0。"""
    v = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    n = len(v)
    if n < 3:
        return 0.0
    m = sum(v) / n
    s = stdev(v)
    if s == 0:
        return 0.0
    return (sum((x - m) ** 3 for x in v) / n) / (s ** 3)


def quintile_gap(values: Sequence[float]) -> tuple:
    """头部五分位均值 - 尾部五分位均值。返回 (leader, lagger, gap)。"""
    v = sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    n = len(v)
    if n < 5:
        # 数据少时用最大/最小作近似
        if not v:
            return 0.0, 0.0, 0.0
        return v[-1], v[0], v[-1] - v[0]
    k = max(1, n // 5)
    top = v[-k:]
    bot = v[:k]
    leader = sum(top) / len(top)
    lagger = sum(bot) / len(bot)
    return leader, lagger, leader - lagger


def top1_contribution(returns: Sequence[float]) -> float:
    """涨幅最大者相对均值的贡献占比。

    定义：max(r) / mean(r)（均值 ≤0 时返回 0，无意义）。
    >1 表示头部贡献超过平均 → 行情集中。
    """
    r = [float(x) for x in returns if x is not None and math.isfinite(float(x))]
    if not r:
        return 0.0
    m = sum(r) / len(r)
    if m <= 0:
        return 0.0
    return max(r) / m


def cohesion_label(
    mean_ret: float, stdev_ret: float, n: int,
    pos_ratio: float, neg_ratio: float,
) -> str:
    """板块一致性标签。

    - 齐涨：均收益明显为正且大多数(≥70%)上涨、离散适中
    - 齐跌：均收益明显为负且大多数(≥70%)下跌
    - 分化：涨跌各半（pos/neg 都在 30%-70%）或离散极高
    - 中性：其余
    """
    if n < 3:
        return "数据不足"
    high_disp = stdev_ret > abs(mean_ret) * 1.5 and stdev_ret > 0.03
    if mean_ret > 0.01 and pos_ratio >= 0.70 and not high_disp:
        return "齐涨"
    if mean_ret < -0.01 and neg_ratio >= 0.70 and not high_disp:
        return "齐跌"
    if 0.30 <= pos_ratio <= 0.70 or high_disp:
        return "分化"
    return "中性"


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class SectorDispersion:
    """板块离散度分析器。"""

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

    def _fetch_closes(self, codes, days=90):
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
        self, sector: str, market: str = "cn", lookback: int = 20, days: int = 90,
    ) -> DispersionResult:
        """分析板块离散度。lookback 默认 20（近一月）。"""
        codes, data_mode = self._resolve(sector, market)
        if not codes:
            return DispersionResult(sector=sector, note="无成分股数据")

        closes = self._fetch_closes(codes, days)
        if not closes:
            return DispersionResult(
                sector=sector, data_mode=data_mode, lookback=lookback, note="行情获取失败")

        rets = period_returns(closes, lookback)
        if len(rets) < 2:
            return DispersionResult(
                sector=sector, data_mode=data_mode, n_stocks=len(closes),
                lookback=lookback, note="区间收益数据不足")

        m = mean(rets)
        md_ = median(rets)
        sd = stdev(rets)
        leader, lagger, gap = quintile_gap(rets)
        contrib = top1_contribution(rets)
        sk = skewness(rets)
        pos_ratio = sum(1 for r in rets if r > 0) / len(rets)
        neg_ratio = sum(1 for r in rets if r < 0) / len(rets)

        return DispersionResult(
            sector=sector, data_mode=data_mode, n_stocks=len(rets),
            lookback=lookback,
            mean_return=round(m * 100, 2),
            median_return=round(md_ * 100, 2),
            stdev_return=round(sd * 100, 2),
            leader_return=round(leader * 100, 2),
            lagger_return=round(lagger * 100, 2),
            leader_lagger_gap=round(gap * 100, 2),
            top1_contrib=round(contrib, 2),
            skew=round(sk, 2),
            cohesion=cohesion_label(m, sd, len(rets), pos_ratio, neg_ratio),
            note=f"基于{len(rets)}只成分股/{lookback}日",
        )

    @staticmethod
    def format(d: DispersionResult) -> str:
        return (
            f"[{d.sector}] 离散度: 均值{d.mean_return:+.1f}% "
            f"σ{d.stdev_return:.1f}% 龙头-落后{d.leader_lagger_gap:+.1f}% "
            f"集中度{d.top1_contrib:.2f} 偏度{d.skew:+.2f} → {d.cohesion} ({d.data_mode})"
        )


def analyze_dispersion(sector: str, market: str = "cn", lookback: int = 20) -> DispersionResult:
    """便捷函数：板块离散度。"""
    return SectorDispersion().analyze(sector, market=market, lookback=lookback)
