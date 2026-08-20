#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自上而下整合分析 (v9.0.0 新增)
==============================
把三大支柱（宏观体制 / 深度板块 / 深度指数 / 体制感知预测）串成一条
经典自上而下的投研链路：

  宏观体制 + 轮动周期阶段
      ↓
  受益板块（RPS 相对强度 + 宽度 筛选）
      ↓
  指数健康度（体制 / 波动率 / 结构 / 内含 / 估值）
      ↓
  综合研判：仓位倾向 + 板块倾斜 + 风险提示

这是 v9.0 的「总览报告」——一次性给出市场全景，避免用户在多个分析器间
手动拼接。每个环节失败均优雅降级，不阻断整体输出。

用法:
    from stock_researcher.analysis.top_down import TopDownReport
    rep = TopDownReport().build(market="cn")
    print(rep.summary)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dataclasses import dataclass, field


# 各市场基准指数（用于体制/指数健康判定）
BENCHMARK_INDEX = {
    "cn": "sh000001",
    "hk": "100.HSI",
    "us": "100.SPX",
}


@dataclass
class TopDownResult:
    """自上而下分析结果"""
    market: str = "cn"
    benchmark: str = ""

    # 宏观层
    regime: Optional[str] = None              # 牛市/熊市/震荡
    regime_score: float = 0.0
    cycle_stage: Optional[str] = None         # 早/中/晚周期/衰退
    cycle_favored: List[str] = field(default_factory=list)

    # 板块层
    top_sectors: List[Dict] = field(default_factory=list)   # RPS 靠前的板块
    weak_sectors: List[str] = field(default_factory=list)

    # 指数层
    index_health: Dict = field(default_factory=dict)        # 体制/波动/结构/估值摘要
    valuation_label: str = ""

    # 综合
    position_tilt: str = "中性"               # 进攻/中性/防御
    favored_themes: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    summary: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


class TopDownReport:
    """自上而下整合分析器。"""

    def build(self, market: str = "cn", top_n: int = 5) -> TopDownResult:
        bench = BENCHMARK_INDEX.get(market, BENCHMARK_INDEX["cn"])
        res = TopDownResult(market=market, benchmark=bench)

        # 1) 宏观体制
        self._fill_regime(res, bench)
        # 2) 轮动周期
        self._fill_cycle(res, market)
        # 3) 板块强度
        self._fill_sectors(res, market, top_n)
        # 4) 指数健康
        self._fill_index_health(res, bench, market)
        # 5) 综合
        self._synthesize(res)

        return res

    # ── 宏观体制 ──
    def _fill_regime(self, res: TopDownResult, bench: str):
        try:
            from stock_researcher.index_analysis.market_regime import MarketRegimeClassifier
            reg = MarketRegimeClassifier().classify(bench)
            res.regime = reg.regime
            res.regime_score = reg.regime_score
        except Exception:
            res.regime = None

    # ── 轮动周期 ──
    def _fill_cycle(self, res: TopDownResult, market: str):
        try:
            from stock_researcher.sector_analysis.rotation_cycle import RotationCycleDetector
            cyc = RotationCycleDetector().detect(market=market)
            res.cycle_stage = cyc.stage
            res.cycle_favored = list(cyc.favored_sectors)
        except Exception:
            pass

    # ── 板块强度（RPS 排名 + 宽度） ──
    def _fill_sectors(self, res: TopDownResult, market: str, top_n: int):
        try:
            from stock_researcher.sector_analysis.relative_strength import (
                SectorRelativeStrength,
            )
            ranking = SectorRelativeStrength().rps_ranking(
                market=market, lookups=(20, 60), top_n=top_n,
            )
            res.top_sectors = [
                {"sector": r.sector, "rps": r.rps_score,
                 "percentile": r.rps_percentile, "trend": r.rs_trend,
                 "data_mode": r.data_mode}
                for r in ranking if r.series_len > 0
            ]
            res.weak_sectors = [r.sector for r in ranking[-3:]
                                if r.rps_score < 0]
        except Exception:
            pass

    # ── 指数健康度 ──
    def _fill_index_health(self, res: TopDownResult, bench: str, market: str):
        health: Dict = {}
        try:
            from stock_researcher.index_analysis.volatility_regime import (
                VolatilityRegimeAnalyzer,
            )
            v = VolatilityRegimeAnalyzer().analyze(bench)
            health["vol_regime"] = v.regime
            health["vol_20d"] = v.realized_vol_20d
            health["bull_friendly"] = v.bull_friendly
        except Exception:
            pass
        try:
            from stock_researcher.index_analysis.market_structure import (
                MarketStructureAnalyzer,
            )
            ms = MarketStructureAnalyzer().analyze(bench)
            health["trend_structure"] = ms.trend_structure
        except Exception:
            pass
        try:
            from stock_researcher.index_analysis.index_valuation import IndexValuation
            iv = IndexValuation().classify(bench, market=market)
            health["valuation"] = iv.valuation_label
            health["pe_percentile"] = iv.pe_percentile
            res.valuation_label = iv.valuation_label
        except Exception:
            pass
        res.index_health = health

    # ── 综合研判 ──
    def _synthesize(self, res: TopDownResult):
        # 仓位倾向
        if res.regime == "牛市" and res.regime_score > 30:
            res.position_tilt = "进攻"
        elif res.regime == "熊市" or res.regime_score < -30:
            res.position_tilt = "防御"
        else:
            res.position_tilt = "中性"

        # 受益主题：取周期阶段受益板块 ∩ RPS 强势板块（若有交集）
        strong = {s["sector"] for s in res.top_sectors[:5]}
        favored = set(res.cycle_favored) & strong
        res.favored_themes = sorted(favored) if favored else list(res.cycle_favored)[:3]

        # 风险提示
        risks = []
        if res.regime == "熊市":
            risks.append("市场处于熊市体制，控制仓位")
        ih = res.index_health
        if ih.get("vol_regime") in ("高波动", "扩张"):
            risks.append(f"波动率{ih.get('vol_regime')}，注意风险")
        if "高估" in str(ih.get("valuation", "")):
            risks.append("指数估值偏高")
        if ih.get("trend_structure") == "下降":
            risks.append("指数趋势结构走弱")
        res.risk_factors = risks[:4]

        # 文字摘要
        parts = [
            f"{res.market.upper()}市场自上而下：体制={res.regime or '未知'}"
            f"(分{res.regime_score:+.0f})",
            f"周期阶段={res.cycle_stage or '未知'}",
            f"仓位倾向={res.position_tilt}",
        ]
        if res.top_sectors:
            parts.append("强势板块=" + ",".join(s["sector"] for s in res.top_sectors[:3]))
        if res.risk_factors:
            parts.append("风险=" + ";".join(res.risk_factors))
        res.summary = " | ".join(parts)

    @staticmethod
    def format(r: TopDownResult) -> str:
        lines = [
            f"\n{'=' * 70}",
            f"  🎯 {r.market.upper()} 自上而下市场全景 v9.0  基准={r.benchmark}",
            f"{'=' * 70}",
            f"  ▎宏观体制: {r.regime or '未知'} (分{r.regime_score:+.0f}) | "
            f"周期: {r.cycle_stage or '未知'} | 仓位倾向: {r.position_tilt}",
        ]
        if r.cycle_favored:
            lines.append(f"  ▎周期受益板块: {', '.join(r.cycle_favored[:6])}")
        if r.top_sectors:
            lines.append(f"  ▎RPS 强势板块:")
            for s in r.top_sectors:
                lines.append(
                    f"     · {s['sector']:<10} RPS{s['rps']:+5.0f} "
                    f"({s['percentile']:.0f}%) {s['trend']} [{s['data_mode']}]"
                )
        ih = r.index_health
        if ih:
            lines.append(
                f"  ▎指数健康: 结构={ih.get('trend_structure','?')} "
                f"波动={ih.get('vol_regime','?')}({ih.get('vol_20d',0):.1f}%) "
                f"估值={ih.get('valuation','?')}"
            )
        if r.favored_themes:
            lines.append(f"  ▎综合推荐方向: {', '.join(r.favored_themes)}")
        if r.risk_factors:
            lines.append(f"  ⚠ 风险提示: {' | '.join(r.risk_factors)}")
        lines.append(f"{'=' * 70}")
        return "\n".join(lines)


def build_topdown(market: str = "cn") -> TopDownResult:
    """便捷函数：自上而下市场全景。"""
    return TopDownReport().build(market=market)
