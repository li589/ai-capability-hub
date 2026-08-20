#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投资推荐引擎 (v4.0.0 新增)

基于融合多周期预测，输出 短(1-5日)/中(1月)/长(1季) 三档
板块 + 个股推荐，每项带排名分、方向、具体理由(引用信号来源)、风险提示。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from stock_researcher.fusion.multi_horizon_forecaster import (
    MultiHorizonForecaster, ForecastResult, MultiHorizonForecast,
)

# 申万板块 → 代表股列表（与 sector_forecast 一致）
SECTOR_CODES = {
    "银行": ["600036","601318","600016","601166"],
    "非银金融": ["601601","600837","601628","601688"],
    "食品饮料": ["600519","000858","600887","603288"],
    "医药生物": ["000538","600276","603259","000661"],
    "电子": ["002475","603986","000725","600183"],
    "计算机": ["000977","002410","300033","600570"],
    "通信": ["000063","600050","601728","002281"],
    "传媒": ["300059","002027","603444","300413"],
    "军工": ["600893","002013","000733","601985"],
    "新能源": ["300750","002594","600900","601012"],
    "汽车": ["002594","000625","601127","600741"],
    "房地产": ["000002","600048","600383","001979"],
    "有色金属": ["601899","600111","000630","002460"],
    "基础化工": ["600309","002601","600486","000301"],
    "电力设备": ["600900","601012","002459","601615"],
}

# 各周期桶映射
HORIZON_BUCKETS = {
    "short": {"horizons": ["1d", "3d", "5d"], "label": "短期(1-5日)", "merge_key": "5d"},
    "mid":   {"horizons": ["1M"], "label": "中期(1个月)", "merge_key": "1M"},
    "long":  {"horizons": ["1Q"], "label": "长期(1个季度)", "merge_key": "1Q"},
}


@dataclass
class Recommendation:
    target_type: str       # "sector"|"stock"
    code: str              # 板块名或股票代码
    name: str
    horizon_bucket: str    # "short"/"mid"/"long"
    direction: str
    predicted_pct: float
    score: float           # 排名分(-100~+100,越高越推荐)
    confidence: float
    top_reasons: List[str] # 具体理由列表
    risk_notes: List[str]


class RecommendationEngine:
    """投资推荐引擎"""

    def __init__(self, seed: int = None):
        self._forecaster = MultiHorizonForecaster(seed=seed)
        self._sector_cache: Dict[str, MultiHorizonForecast] = {}
        self._stock_cache: Dict[str, MultiHorizonForecast] = {}

    def recommend_sectors(
        self, sectors: List[str] = None, bucket: str = "short",
        top_n: int = 5
    ) -> List[Recommendation]:
        """推荐板块"""
        sectors = sectors or list(SECTOR_CODES.keys())
        bucket_cfg = HORIZON_BUCKETS.get(bucket, HORIZON_BUCKETS["short"])
        merge_key = bucket_cfg["merge_key"]
        recs = []

        for s in sectors[:15]:
            codes = SECTOR_CODES.get(s, [])
            if not codes:
                continue
            if s not in self._sector_cache:
                try:
                    self._sector_cache[s] = self._forecaster.forecast_sector(s, codes,
                                                                              horizons=[merge_key])
                except Exception:
                    continue
            fc = self._sector_cache[s]
            fr = fc.horizons.get(merge_key)
            if not fr:
                continue
            reasons = [f"{dr['dimension']}面{dr['contribution']:+.0f}分: {dr['reason'][:35]}"
                       for dr in fr.top_drivers[:3]]

            recs.append(Recommendation(
                target_type="sector", code=s, name=s,
                horizon_bucket=bucket, direction=fr.direction,
                predicted_pct=fr.predicted_pct, score=fr.composite_score,
                confidence=fr.confidence,
                top_reasons=reasons, risk_notes=fr.risk_factors[:2],
            ))
        # 按得分排序
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:top_n]

    def recommend_stocks(
        self, codes: List[str] = None, sector: str = None,
        bucket: str = "short", top_n: int = 5
    ) -> List[Recommendation]:
        """推荐个股"""
        if codes is None:
            parts = []
            if sector and sector in SECTOR_CODES:
                parts = SECTOR_CODES[sector]
            else:
                # 取所有板块 Top1 代表股
                for c_list in SECTOR_CODES.values():
                    parts.append(c_list[0])
            codes = list(dict.fromkeys(parts))
        bucket_cfg = HORIZON_BUCKETS.get(bucket, HORIZON_BUCKETS["short"])
        merge_key = bucket_cfg["merge_key"]
        recs = []
        for code in codes[:20]:
            c = str(code).zfill(6)
            if c not in self._stock_cache:
                try:
                    self._stock_cache[c] = self._forecaster.forecast_stock(
                        c, horizons=[merge_key])
                except Exception:
                    continue
            fc = self._stock_cache[c]
            fr = fc.horizons.get(merge_key)
            if not fr:
                continue
            reasons = [f"{dr['dimension']}面{dr['contribution']:+.0f}分: {dr['reason'][:35]}"
                       for dr in fr.top_drivers[:3]]
            recs.append(Recommendation(
                target_type="stock", code=c, name="",
                horizon_bucket=bucket, direction=fr.direction,
                predicted_pct=fr.predicted_pct, score=fr.composite_score,
                confidence=fr.confidence,
                top_reasons=reasons, risk_notes=fr.risk_factors[:2],
            ))
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:top_n]

    def recommend_all(
        self, sectors: List[str] = None, top_n: int = 5
    ) -> Dict[str, Dict[str, List[Recommendation]]]:
        """三档全推：shortsector + mid + long，含板块和个股"""
        result = {}
        for bucket in ["short", "mid", "long"]:
            sectors_rec = self.recommend_sectors(sectors, bucket, top_n)
            # 从推荐板块中提取代表股做个股推荐
            stock_codes = []
            for sr in sectors_rec[:3]:
                stock_codes.extend(SECTOR_CODES.get(sr.code, [])[:2])
            stocks_rec = self.recommend_stocks(
                list(dict.fromkeys(stock_codes)), bucket=bucket, top_n=top_n)
            result[bucket] = {"sectors": sectors_rec, "stocks": stocks_rec}
        return result


def get_recommendations(
    horizon: str = "short", asset_type: str = "sector", top_n: int = 5
) -> List[Recommendation]:
    """便捷入口"""
    eng = RecommendationEngine()
    if asset_type == "stock":
        return eng.recommend_stocks(bucket=horizon, top_n=top_n)
    return eng.recommend_sectors(bucket=horizon, top_n=top_n)


def format_recommendations(recos: Dict[str, Dict[str, List[Recommendation]]]) -> str:
    lines = ["⭐ 投资推荐  |  " + datetime.now().strftime("%Y-%m-%d %H:%M"),
             "=" * 70]
    for bucket in ["short", "mid", "long"]:
        data = recos.get(bucket, {})
        hlabel = HORIZON_BUCKETS[bucket]["label"]
        sr = data.get("sectors", [])
        lines.append(f"")
        lines.append(f"【{hlabel} - 板块推荐】")
        if not sr:
            lines.append("  (暂无明确推荐板块)")
            continue
        for i, r in enumerate(sr, 1):
            lines.append(f"  #{i} [{r.code}] {r.direction} | 涨跌幅度{r.predicted_pct:+.2f}% "
                         f"| 得分{r.score:+.0f} | 置信{r.confidence:.0%}")
            for re in r.top_reasons[:2]:
                lines.append(f"       → {re}")
            if r.risk_notes:
                lines.append(f"       ⚠️ {r.risk_notes[0]}")
        st = data.get("stocks", [])
        if st:
            lines.append(f"  ── 代表个股 ──")
            for i, r in enumerate(st[:3], 1):
                lines.append(f"  #{i} [{r.code}] {r.direction} "
                             f"涨跌幅{r.predicted_pct:+.2f}% 得分{r.score:+.0f}")
    lines.append("=" * 70)
    return "\n".join(lines)
