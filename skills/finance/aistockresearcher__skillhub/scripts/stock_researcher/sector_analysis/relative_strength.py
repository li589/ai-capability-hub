#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""板块相对强度分析 (v9.0.0 新增)
================================
相对价格强度 RPS（Relative Price Strength）—— 板块轮动的核心指标。

现 v8.0 板块评分仅基于「当日平均涨跌幅」，无法识别中期强势/弱势板块。
本模块用成分股真实收盘价构造板块代理指数，相对基准（沪深300/恒生/标普500）
计算多周期相对强度 + Mansfield RPS 评级 + RS 趋势，输出 0-100 百分位排名。

设计要点：
  - 纯函数（build_proxy_from_closes / rs_ratio_series / mansfield_rps ...）
    与数据获取分离，全部可离线单测（合成序列）。
  - 真实数据：成分股收盘价来自 MarketData.fetch_history（腾讯前复权日K）。
  - 混合策略：默认用板块代表篮子（real prices, data_mode="proxy"）；
    支持注入 constituents_provider 返回更大成分股清单（data_mode="full"）。
  - 网络失败优雅降级：返回中性结果，绝不抛异常。

用法:
    from stock_researcher.sector_analysis.relative_strength import (
        SectorRelativeStrength, relative_strength, rps_ranking,
    )
    rs = SectorRelativeStrength().relative_strength("新能源", market="cn")
    ranking = rps_ranking(market="cn", lookups=(20, 60))
"""

from __future__ import annotations

import math
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from dataclasses import dataclass, field


# ── 各市场相对强度基准 ──────────────────────────────
# 板块强度必须相对「宽基基准指数」衡量才有意义
BENCHMARK = {
    "cn": {"code": "000300", "name": "沪深300", "prefix": "sh"},
    "hk": {"code": "100.HSI", "name": "恒生指数"},
    "us": {"code": "100.SPX", "name": "标普500"},
}


@dataclass
class RelativeStrengthResult:
    """板块相对强度结果"""
    sector: str
    benchmark: str = ""
    data_mode: str = "proxy"        # proxy(代表篮子) | full(全成分股) | index(官方行业指数)
    n_stocks: int = 0               # 实际纳入的成分股数
    series_len: int = 0             # 代理序列长度（交易日）

    rs_ratio: float = 1.0           # 最新 RS 比率（proxy/benchmark）
    rs_lookups: Dict[str, float] = field(default_factory=dict)  # {"5d":..,"20d":..} RS 区间收益
    rps_score: float = 0.0          # Mansfield RPS 原始分（0=与基准持平，>0 强于基准）
    rps_percentile: float = 50.0    # 0-100 横截面百分位（仅 ranking 时有意义）
    rps_rank: int = 0               # 横截面排名（1=最强，仅 ranking 时填）
    rs_trend: str = "中性"          # 上升/下降/中性（RS vs RS均线 + 斜率）
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层（无副作用，可离线单测）
# ════════════════════════════════════════════════════════════

def _clean(values: Sequence[float]) -> List[float]:
    """过滤 None/非正数，返回 float 列表（价格须 > 0）。"""
    out = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f) and f > 0:
            out.append(f)
    return out


def align_and_rebase(
    closes_by_code: Dict[str, Sequence[float]],
    weights: str = "equal",
) -> Tuple[List[float], int]:
    """把多只成分股收盘价对齐→重定基准 100→加权合成板块代理指数。

    Args:
        closes_by_code: {code: [closes]}；长度可不一致（按最短公共窗口从末端对齐）
        weights: "equal" 等权（默认）；"cap" 暂降级为等权（需市值，留扩展）

    Returns:
        (proxy_closes, n_stocks)；输入无效时返回 ([], 0)
    """
    cleaned = {c: _clean(v) for c, v in closes_by_code.items()}
    cleaned = {c: v for c, v in cleaned.items() if len(v) >= 2}
    if not cleaned:
        return [], 0

    min_len = min(len(v) for v in cleaned.values())
    if min_len < 2:
        return [], 0

    # 末端对齐：各序列取最后 min_len 个点
    series = {c: v[-min_len:] for c, v in cleaned.items()}
    n = len(series)

    # 重定基准：每只股票首点归一为 100
    rebased = {}
    for c, v in series.items():
        base = v[0]
        rebased[c] = [p / base * 100.0 for p in v]

    # 等权平均（cap 权重暂降级为等权）
    proxy = []
    for i in range(min_len):
        s = sum(rebased[c][i] for c in rebased)
        proxy.append(s / n)
    return proxy, n


def rs_ratio_series(proxy: Sequence[float], benchmark: Sequence[float]) -> List[float]:
    """逐点计算 RS = proxy / benchmark（按最短长度末端对齐）。"""
    p, b = _clean(proxy), _clean(benchmark)
    if not p or not b:
        return []
    m = min(len(p), len(b))
    p, b = p[-m:], b[-m:]
    return [p[i] / b[i] for i in range(m)]


def pct_change_over(series: Sequence[float], n: int) -> Optional[float]:
    """序列最后 n 期的收益率（series[-1]/series[-1-n] - 1）。数据不足返回 None。"""
    s = _clean(series)
    if n <= 0 or len(s) <= n or s[-1 - n] <= 0:
        return None
    return s[-1] / s[-1 - n] - 1.0


def sma(series: Sequence[float], n: int) -> Optional[float]:
    """最后 n 期算术均线。不足返回 None。"""
    s = _clean(series)
    if n <= 0 or len(s) < n:
        return None
    return sum(s[-n:]) / n


def slope_sign(series: Sequence[float], n: int = 10) -> float:
    """末段 n 期线性回归斜率符号与量级（>0 上升）。用最小二乘，纯 stdlib。

    n 自动收敛到 min(n, 序列长度)，序列不足 2 点返回 0。
    """
    s = _clean(series)
    if len(s) < 2:
        return 0.0
    n = min(n, len(s))
    if n < 2:
        return 0.0
    y = s[-n:]
    x = list(range(n))
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den = sum((x[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return num / den  # 原始斜率（价格量级）


def mansfield_rps(rs_series: Sequence[float], n: int = 126) -> Optional[float]:
    """Mansfield 相对强度评级：(RS[-1] / mean(RS[-n:]) - 1) * 100。

    > 0 表示强于基准（过去约半年均值之上），越大越强。数据不足返回 None。
    n 默认 126（约半年交易日）。
    """
    s = _clean(rs_series)
    if len(s) < max(n, 20) or n <= 0:
        # 数据不足时退用全部可用长度的均值
        if len(s) < 10:
            return None
        window = s
    else:
        window = s[-n:]
    mean_rs = sum(window) / len(window)
    if mean_rs <= 0:
        return None
    return (s[-1] / mean_rs - 1.0) * 100.0


def percentile_rank(value: float, population: Sequence[float]) -> float:
    """value 在 population 中的百分位（0-100，越高越强）。

    采用「竞争百分位」：最小值→0、最大值→100、中位→50，便于排名解读。
    相等值（并列）取其平均位次。空集返回 50（中性）。
    """
    pop = [float(v) for v in population if v is not None and math.isfinite(float(v))]
    n = len(pop)
    if n == 0:
        return 50.0
    if n == 1:
        return 50.0
    less = sum(1 for v in pop if v < value)
    equal = sum(1 for v in pop if v == value)
    avg_pos = less + (equal - 1) / 2.0   # 0 基平均位次
    return avg_pos / (n - 1) * 100.0


def rs_trend_label(rs_series: Sequence[float], ma_n: int = 20) -> str:
    """RS 趋势标签：RS 位于其均线上方且斜率向上 →「上升」，反之为「下降」，否则「中性」。"""
    s = _clean(rs_series)
    if len(s) < ma_n + 2:
        return "数据不足"
    ma = sma(s, ma_n)
    if ma is None:
        return "数据不足"
    slope = slope_sign(s, ma_n)
    above = s[-1] > ma
    below = s[-1] < ma
    if above and slope > 0:
        return "上升"
    if below and slope < 0:
        return "下降"
    return "中性"


# ════════════════════════════════════════════════════════════
# 数据接线层（联网，全部 try/except 降级）
# ════════════════════════════════════════════════════════════

class SectorRelativeStrength:
    """板块相对强度分析器。

    Args:
        constituents_provider: 可选回调 (sector, market) -> List[code]，
            返回该板块的成分股清单（用于 full 模式）。不传则用代表篮子。
    """

    LOOKUPS = (5, 20, 60, 120)

    def __init__(self, constituents_provider: Optional[Callable] = None):
        self._provider = constituents_provider

    # ── 成分股清单解析 ──
    def _resolve_constituents(self, sector: str, market: str) -> Tuple[List[str], str]:
        """返回 (codes, data_mode)。优先 provider → 代表篮子。"""
        if self._provider:
            try:
                codes = list(self._provider(sector, market) or [])
                if codes:
                    return codes, "full"
            except Exception:
                pass
        # 回退到既有代表篮子映射
        reps = self._representatives(sector, market)
        return reps, "proxy"

    @staticmethod
    def _representatives(sector: str, market: str) -> List[str]:
        """复用 sector_forecast / sectors 的代表股映射（real prices）。"""
        try:
            from stock_researcher.sector_analysis.sector_forecast import (
                SECTOR_REPRESENTATIVES,
            )
            return list(SECTOR_REPRESENTATIVES.get(market, {}).get(sector, []))
        except Exception:
            pass
        try:
            from stock_researcher.sector_analysis.sectors import SectorAnalyzer
            return list(SectorAnalyzer.ALL_SECTOR_MAPS.get(market, {}).get(sector, []))
        except Exception:
            return []

    # ── 数据获取 ──
    def _fetch_closes(self, codes: List[str], days: int) -> Dict[str, List[float]]:
        """并发拉取成分股前复权日K收盘价（失败代码剔除）。"""
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

    def _fetch_benchmark_closes(self, market: str, days: int) -> List[float]:
        """拉取基准指数收盘价。cn→沪深300(腾讯日K)；hk/us→全球指数。"""
        try:
            if market == "cn":
                from stock_researcher.data.market import MarketData
                k = MarketData().fetch_history("000300", days=days, prefix="sh") or {}
                return [float(p) for p in k.get("closes", []) if p is not None]
            # hk / us / 其它：走全球指数 kline
            from stock_researcher.data.global_market import fetch_global_kline
            code = BENCHMARK.get(market, BENCHMARK["us"])["code"]
            kl = fetch_global_kline(f"idx:{code}", days=days) or []
            return [float(k.get("close", 0)) for k in kl
                    if isinstance(k, dict) and k.get("close")]
        except Exception:
            return []

    # ── 主分析 ──
    def relative_strength(
        self,
        sector: str,
        market: str = "cn",
        lookups: Sequence[int] = None,
        days: int = 130,
    ) -> RelativeStrengthResult:
        """计算单个板块相对基准的多周期相对强度。

        Args:
            sector: 板块名
            market: cn/hk/us
            lookups: RS 收益计算周期（交易日），默认 (5,20,60,120)
            days: 拉取历史天数（需 > max(lookups)，默认 130）
        """
        lookups = list(lookups) if lookups else list(self.LOOKUPS)
        max_lookup = max(lookups) if lookups else 20
        days = max(days, max_lookup + 30)

        codes, data_mode = self._resolve_constituents(sector, market)
        bench_cfg = BENCHMARK.get(market, BENCHMARK["us"])

        if not codes:
            return RelativeStrengthResult(
                sector=sector, benchmark=bench_cfg["name"],
                note="无成分股数据",
            )

        closes = self._fetch_closes(codes, days)
        bench = self._fetch_benchmark_closes(market, days)

        if not closes or len(bench) < 2:
            return RelativeStrengthResult(
                sector=sector, benchmark=bench_cfg["name"],
                n_stocks=len(closes), data_mode=data_mode,
                note="行情数据获取失败",
            )

        proxy, n_used = align_and_rebase(closes)
        rs = rs_ratio_series(proxy, bench)
        if len(rs) < 10:
            return RelativeStrengthResult(
                sector=sector, benchmark=bench_cfg["name"],
                data_mode=data_mode, n_stocks=n_used, series_len=len(rs),
                note="对齐后序列过短",
            )

        # 多周期 RS 收益
        rs_lookups = {}
        for lk in lookups:
            r = pct_change_over(rs, lk)
            if r is not None:
                rs_lookups[f"{lk}d"] = round(r * 100, 2)

        rps = mansfield_rps(rs)
        rps_val = rps if rps is not None else 0.0

        return RelativeStrengthResult(
            sector=sector,
            benchmark=bench_cfg["name"],
            data_mode=data_mode,
            n_stocks=n_used,
            series_len=len(rs),
            rs_ratio=round(rs[-1], 4),
            rs_lookups=rs_lookups,
            rps_score=round(rps_val, 2),
            rs_trend=rs_trend_label(rs),
            note=f"基于{n_used}只成分股/{len(rs)}日 vs {bench_cfg['name']}",
        )

    def rps_ranking(
        self,
        market: str = "cn",
        lookups: Sequence[int] = (20, 60),
        top_n: Optional[int] = None,
    ) -> List[RelativeStrengthResult]:
        """全市场板块 RPS 排名（按 Mansfield RPS 降序，附横截面百分位）。

        Args:
            market: cn/hk/us
            lookups: 传给 relative_strength 的周期
            top_n: 仅返回前 N（None=全部）
        """
        sectors = self._all_sector_names(market)
        results = []
        for name in sectors:
            try:
                r = self.relative_strength(name, market=market, lookups=lookups)
                results.append(r)
            except Exception:
                continue
            time.sleep(0.1)

        # 横截面百分位 + 排名
        pop = [r.rps_score for r in results]
        for r in results:
            r.rps_percentile = round(percentile_rank(r.rps_score, pop), 1)

        results.sort(key=lambda x: x.rps_score, reverse=True)
        for i, r in enumerate(results, 1):
            r.rps_rank = i

        return results[:top_n] if top_n else results

    @staticmethod
    def _all_sector_names(market: str) -> List[str]:
        try:
            from stock_researcher.sector_analysis.sector_forecast import (
                SECTOR_REPRESENTATIVES,
            )
            return list(SECTOR_REPRESENTATIVES.get(market, {}).keys())
        except Exception:
            pass
        try:
            from stock_researcher.sector_analysis.sectors import SectorAnalyzer
            return list(SectorAnalyzer.ALL_SECTOR_MAPS.get(market, {}).keys())
        except Exception:
            return []

    # ── 报告 ──
    @staticmethod
    def format_ranking(results: List[RelativeStrengthResult], market: str = "cn") -> str:
        labels = {"cn": "A股", "hk": "港股", "us": "美股"}
        lines = [
            f"\n{'=' * 78}",
            f"  📈 {labels.get(market, market)}板块相对强度(RPS)排名 v9.0",
            f"  {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'=' * 78}",
            f"  {'排名':<4}{'板块':<10}{'RPS':>7}{'百分位':>8}"
            f"{'20d':>8}{'60d':>8}  {'趋势':<6}{'数据'}",
            f"  {'-' * 72}",
        ]
        for r in results:
            d20 = r.rs_lookups.get("20d", 0)
            d60 = r.rs_lookups.get("60d", 0)
            lines.append(
                f"  {r.rps_rank:<4}{r.sector:<10}{r.rps_score:>+6.1f}"
                f"{r.rps_percentile:>7.0f}%{d20:>+7.1f}%{d60:>+7.1f}%  "
                f"{r.rs_trend:<6}{r.data_mode}"
            )
        lines.append(f"{'=' * 78}")
        return "\n".join(lines)


# ── 便捷函数 ──

def relative_strength(sector: str, market: str = "cn") -> RelativeStrengthResult:
    """便捷函数：单板块相对强度。"""
    return SectorRelativeStrength().relative_strength(sector, market=market)


def rps_ranking(market: str = "cn", top_n: Optional[int] = None) -> List[RelativeStrengthResult]:
    """便捷函数：全市场 RPS 排名。"""
    return SectorRelativeStrength().rps_ranking(market=market, top_n=top_n)
