#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多周期预测编排器 (v4.0.0 新增)

对个股或板块，融合 10 维信号，按 1日/3日/5日/1月/1季 五个周期
输出统一 ForecastResult：涨跌方向 + 涨跌幅度 + 百分位置信区间 + 推演说明。

融合权重按周期特异：
  - 短期(1d/3d): 技术 + 情绪 + 资金 + 新闻 + 量化(短期) 主导
  - 中期(5d/1M): 技术 + 资金 + 券商 + 估值 + 政策 均衡
  - 长期(1Q): 估值 + 券商 + 政策 + 历史 + 宏观 主导

权重源优先级：
  1. data/evolution/weights.json（进化模块产出）
  2. 硬编码默认值（内置后备）

输出 ForecastResult 必含：
  - direction（看多/看空/震荡）
  - predicted_pct（预测涨跌幅度%）
  - p10/p50/p90（蒙特卡洛模拟的 80% 置信区间）
  - confidence（综合置信度 0~1）
  - top_drivers（贡献最大的信号维度+理由）
  - risk_factors（主要风险因素）
  - narrative（推演说明：一段可读的自然语言解释）
"""
from __future__ import annotations

import sys
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from stock_researcher.fusion.signal_collector import (
    SignalCollector, SignalBundle, DimensionSignal,
)

# 预测周期定义（v7.0 新增 3M/6M 长周期）
HORIZONS = {"1d": 1, "3d": 3, "5d": 5, "1M": 22, "3M": 63, "6M": 126, "1Q": 66}

# ── 默认逐周期权重（若 evolution/weights.json 不存在）───────
# 短期(1d/3d): 技术面主导 + 情绪/资金 + 量化波动
# 中期(5d/1M): 均衡混合 技术+资金+券商+估值+政策
# 长期(1Q/3M/6M): 估值+券商+政策+宏观主导
DEFAULT_HORIZON_WEIGHTS = {
    "1d": {
        "technical": 0.30, "sentiment": 0.20, "money_flow": 0.20,
        "news": 0.10, "quant_vol": 0.10, "macro": 0.05, "policy": 0.03,
        "valuation": 0.02,
    },
    "3d": {
        "technical": 0.25, "sentiment": 0.18, "money_flow": 0.18,
        "news": 0.10, "quant_vol": 0.08, "macro": 0.08,
        "broker": 0.05, "policy": 0.05, "valuation": 0.03,
    },
    "5d": {
        "technical": 0.18, "money_flow": 0.15, "sentiment": 0.12,
        "broker": 0.12, "valuation": 0.10, "policy": 0.10,
        "news": 0.08, "macro": 0.08, "quant_vol": 0.05, "quant_factor": 0.02,
    },
    "1M": {
        "valuation": 0.20, "broker": 0.18, "technical": 0.15,
        "policy": 0.12, "macro": 0.10, "money_flow": 0.08,
        "sentiment": 0.07, "quant_factor": 0.05, "news": 0.05,
    },
    "1Q": {
        "valuation": 0.25, "broker": 0.20, "policy": 0.15,
        "macro": 0.12, "technical": 0.10, "quant_factor": 0.08,
        "money_flow": 0.05, "sentiment": 0.03, "news": 0.02,
    },
    # v7.0 新增：3个月（63交易日）和6个月（126交易日）
    "3M": {
        "valuation": 0.22, "policy": 0.20, "macro": 0.18,
        "broker": 0.15, "technical": 0.10, "quant_factor": 0.08,
        "money_flow": 0.04, "sentiment": 0.02, "news": 0.01,
    },
    "6M": {
        "valuation": 0.25, "policy": 0.22, "macro": 0.20,
        "broker": 0.15, "technical": 0.08, "quant_factor": 0.05,
        "money_flow": 0.03, "sentiment": 0.01, "news": 0.01,
    },
}

# v7.0 资产类型特定权重覆盖（指数/商品/基金）
ASSET_TYPE_WEIGHTS = {
    "index": {
        "1M": {"macro": 0.25, "policy": 0.22, "valuation": 0.18,
               "technical": 0.15, "broker": 0.10, "sentiment": 0.05,
               "money_flow": 0.05},
        "3M": {"policy": 0.28, "macro": 0.25, "valuation": 0.20,
               "broker": 0.12, "technical": 0.10, "sentiment": 0.05},
        "6M": {"policy": 0.30, "macro": 0.28, "valuation": 0.22,
               "broker": 0.10, "technical": 0.05, "sentiment": 0.05},
    },
    "commodity": {
        "1d": {"technical": 0.25, "sentiment": 0.10, "money_flow": 0.15,
               "macro": 0.20, "quant_vol": 0.15, "news": 0.10, "policy": 0.05},
        "5d": {"macro": 0.30, "technical": 0.20, "money_flow": 0.15,
               "policy": 0.15, "sentiment": 0.10, "news": 0.10},
        "1M": {"macro": 0.35, "policy": 0.20, "technical": 0.15,
               "money_flow": 0.10, "valuation": 0.10, "sentiment": 0.10},
    },
    "fund": {
        "5d": {"technical": 0.15, "sentiment": 0.15, "valuation": 0.20,
               "macro": 0.20, "policy": 0.15, "quant_factor": 0.15},
        "1M": {"valuation": 0.30, "macro": 0.25, "policy": 0.15,
               "quant_factor": 0.15, "sentiment": 0.10, "technical": 0.05},
    },
}

# 信号方向中文描述
DIRECTION_LABELS = {
    True: {"看多": "看多", "看空": "看空", "中性": "震荡"},
    False: {"positive": "积极", "negative": "消极", "neutral": "中性"},
}


@dataclass
class ForecastResult:
    """单周期预测结果"""
    horizon: str               # "1d"/"3d"/"5d"/"1M"/"1Q"
    horizon_days: int          # 对应交易日数
    direction: str             # "看多"/"看空"/"震荡"/"分歧偏多"/"分歧偏空"/"分歧"
    predicted_pct: float       # 预测涨跌幅度 %
    p10: float                 # 蒙特卡洛 10% 分位数（80%区间下界）
    p50: float                 # 中位数
    p90: float                 # 90% 分位数（80%区间上界）
    prob_up: float             # 上涨概率 %
    confidence: float          # 综合置信度 0~1
    composite_score: float     # 融合得分 -100~+100
    top_drivers: List[Dict]    # [{"dimension":"券商面","contribution":+25,"reason":"一致买入"},...]
    risk_factors: List[str]    # 风险因素
    narrative: str             # 推演说明（自然语言）
    # v9.0 增量字段（默认空，向后兼容）
    regime: Optional[str] = None          # 预测时所处市场体制
    consensus: Optional[Dict] = None      # 信号共识度
    scenario: Optional[Dict] = None       # 宏观情景（概率加权）


@dataclass
class MultiHorizonForecast:
    """多周期预测结果集"""
    target_type: str           # "stock"|"sector"|"index"|"commodity"|"fund"
    asset_type: str = "stock"  # v7.0: 资产类型标识
    code: str = ""
    name: str = ""
    timestamp: str = ""
    horizons: Dict[str, ForecastResult] = field(default_factory=dict)
    signal_summary: Dict = field(default_factory=dict)
    source_status: Dict[str, str] = field(default_factory=dict)
    # v9.0 增量
    regime: Optional[str] = None          # 整体市场体制（自上而下）


class MultiHorizonForecaster:
    """多周期预测编排器"""

    def __init__(self, seed: int = None):
        # 独立随机源，不污染全局 random 状态
        self._rng = random.Random(seed)
        # 加载进化权重（若存在）
        self._weights = self._load_weights()
        self._collector = SignalCollector()

    def _load_weights(self) -> Dict[str, Dict[str, float]]:
        """从 data/evolution/weights.json 读取自定义权重，否则用默认"""
        wfile = SKILL_DIR / "data" / "evolution" / "weights.json"
        if wfile.exists():
            try:
                with open(wfile, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                if isinstance(custom, dict) and all(
                    isinstance(v, dict) for v in custom.values()
                ):
                    return custom
            except Exception:
                pass
        return DEFAULT_HORIZON_WEIGHTS

    def _make_reason(self, d: DimensionSignal) -> str:
        """从维度信号提取有效的理由文本"""
        # 优先取最有趣的详情字段
        detail = d.detail
        if detail:
            for key in ("ma_trend", "rsi14", "label", "regime", "bullish_ratio",
                        "consensus", "avg_score", "articles", "composite_score", "pe"):
                v = detail.get(key)
                if v is not None and v != "" and v != 0:
                    if isinstance(v, float):
                        v = round(v, 1)
                    return f"{d.direction}({d.dimension}面,{key}={v})"
        # 回退
        if d.note:
            return d.note[:40]
        return f"{d.direction}({d.dimension}面)"

    def _fuse_scores(
        self, bundle: SignalBundle, horizon: str, asset_type: str = "stock",
        regime: Optional[str] = None,
    ) -> Tuple[List[DimensionSignal], float, float, List[str]]:
        """按 horizon 权重融合，返回 (入选信号列表, 综合得分, 置信, 风险)

        v7.0: 支持 asset_type 特定权重覆盖（index/commodity/fund）
        v9.0: 支持 regime 体制条件化权重 + 动量折扣（regime=None 时行为不变）
        """
        # 优先加载资产类型特定权重，其次通用权重
        hw = None
        if asset_type in ASSET_TYPE_WEIGHTS:
            asset_cfg = ASSET_TYPE_WEIGHTS[asset_type]
            hw = asset_cfg.get(horizon)
        if hw is None:
            hw = self._weights.get(horizon, DEFAULT_HORIZON_WEIGHTS.get(horizon, {}))
        # v9.0: 体制权重叠加（regime=None 时不变）
        if regime:
            try:
                from stock_researcher.fusion.regime_overlay import RegimeOverlay
                hw = RegimeOverlay.apply_regime_weights(hw, regime, horizon)
            except Exception:
                pass
        if not hw:
            dims = [d for d in bundle.dimensions if d.available]
            if not dims:
                return [], 0, 0.1, ["无可用信号"]
            avg = sum(d.score for d in dims) / len(dims)
            return dims, avg, 0.3, []

        # 只使用本周期有权重的维度
        used: List[DimensionSignal] = []
        total_w = 0.0
        for d in bundle.dimensions:
            w = hw.get(d.dimension, 0)
            if w > 0 and d.available:
                used.append(d)
                total_w += w

        if not used or total_w == 0:
            return [], 0, 0.1, ["该周期无有效信号维度"]

        # 加权融合（v9.0: 体制对动量类信号折扣）
        composite = 0.0
        for d in used:
            w = hw.get(d.dimension, 0)
            score = d.score
            if regime:
                try:
                    from stock_researcher.fusion.regime_overlay import RegimeOverlay
                    score = RegimeOverlay.momentum_dampening(score, d.dimension, regime)
                except Exception:
                    pass
            composite += score * w / total_w

        # 置信度 = (1 - 离散度惩罚) × 信号覆盖率（可用维度数 / 全部10维）
        if len(used) > 1:
            dispersion = sum(abs(d.score - composite) for d in used) / len(used)
            base = 1.0 - (dispersion / 100 * 0.5)
        else:
            base = 0.4
        coverage = len(used) / 10.0
        confidence = base * coverage
        confidence = max(0.15, min(0.95, confidence))

        # 风险因素
        risks = []
        if composite < -20:
            risks.append("综合信号偏空")
        for d in used:
            if d.score < -50:
                risks.append(f"{d.dimension}面信号极弱({d.score:.0f})")
        if len(used) < 3:
            risks.append(f"可用信号维度仅{len(used)}个，置信有限")
        return used, round(composite, 1), round(confidence, 3), risks

    def _monte_carlo(
        self, prices: List[float], horizon_days: int, sims: int = 500,
        composite: float = 0.0,
    ) -> Tuple[float, float, float, float, float]:
        """蒙特卡洛模拟：返回 (predicted_pct, p10, p50, p90, prob_up)

        融合信号 composite(-100~+100) 映射为日收益 μ 的调整项：
        mu_adj = mu + clamp(composite/100 * 0.5, ±0.25) * sigma，
        调整上限 ±0.25σ/日，避免信号主导淹没历史波动结构。
        """
        if len(prices) < 30:
            # 数据不足，简单趋势外推
            if len(prices) > 1:
                chg = (prices[-1] / prices[0] - 1) / len(prices)**0.5 * horizon_days**0.5 * 100
                lo, hi = sorted((chg * 0.5, chg * 1.5))
                return round(chg, 2), round(lo, 2), round(chg, 2), round(hi, 2), 50
            return 0, -2, 0, 2, 50

        # 日收益率统计
        returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
        mu = sum(returns) / len(returns)
        variance = sum((r - mu) ** 2 for r in returns) / len(returns)
        sigma = math.sqrt(max(variance, 1e-12))

        # 融合信号 → μ 调整（封上限 ±0.25σ）
        adj = max(-0.25, min(0.25, composite / 100 * 0.5))
        mu_adj = mu + adj * sigma

        # 模拟 horizon_days 个交易日
        results = []
        for _ in range(sims):
            price = 1.0
            for _ in range(horizon_days):
                price *= (1 + self._rng.gauss(mu_adj, sigma))
            results.append(price - 1.0)  # 收益率

        results.sort()
        n = len(results)
        predicted_pct = sum(results) / n * 100
        p10 = results[int(n * 0.1)] * 100
        p50 = results[n // 2] * 100
        p90 = results[int(n * 0.9)] * 100
        prob_up = sum(1 for r in results if r > 0) / n * 100

        return round(predicted_pct, 2), round(p10, 2), round(p50, 2), round(p90, 2), round(prob_up, 1)

    def _generate_narrative(
        self, horizon: str, result: ForecastResult,
        used_dimensions: List[DimensionSignal]
    ) -> str:
        """生成推演说明"""
        hlabel = {"1d": "下一个交易日", "3d": "未来3个交易日",
                  "5d": "未来一周", "1M": "未来一个月", "1Q": "未来一个季度"}
        period = hlabel.get(horizon, horizon)

        # 按归一化贡献 |score×权重| 排序
        hw = self._weights.get(horizon, DEFAULT_HORIZON_WEIGHTS.get(horizon, {}))
        tw = sum(hw.get(d.dimension, 0) for d in used_dimensions) or 1
        dims_sorted = sorted(
            used_dimensions,
            key=lambda d: abs(d.score * hw.get(d.dimension, 0) / tw),
            reverse=True,
        )
        top_dimensions = dims_sorted[:4]

        parts = [f"{period}，"]

        if result.direction == "看多":
            parts.append("综合信号偏多，")
        elif result.direction == "看空":
            parts.append("综合信号偏空，")
        elif result.direction == "分歧偏多":
            parts.append("信号看多但历史动量不配合（分歧偏多），")
        elif result.direction == "分歧偏空":
            parts.append("信号看空但历史动量偏强（分歧偏空），")
        else:
            parts.append("信号分化，方向不明确，")

        # 关键驱动
        drivers_text = []
        for d in top_dimensions:
            dname = {"technical": "技术", "sentiment": "情绪", "money_flow": "资金",
                     "policy": "政策", "news": "新闻", "broker": "券商",
                     "valuation": "估值", "macro": "宏观",
                     "quant_vol": "量化波动率", "quant_factor": "量化因子"}.get(d.dimension, d.dimension)
            drivers_text.append(f"{dname}面{'+' if d.score > 0 else ''}{d.score:.0f}分")
        parts.append("、".join(drivers_text[:3]) + "；")

        parts.append(f"蒙特卡洛{horizon}模拟显示{result.prob_up:.0f}%概率上涨，"
                     f"预期涨跌幅{result.predicted_pct:+.2f}%，"
                     f"80%置信区间为{result.p10:+.2f}%至{result.p90:+.2f}%。")

        if result.risk_factors:
            parts.append("注意风险：" + "；".join(result.risk_factors[:2]) + "。")

        parts.append(f"综合置信度{result.confidence:.0%}。")
        return "".join(parts)

    @staticmethod
    def _kline_to_ohlcv(kline):
        """v8.0: 把 kline dict（dates/opens/highs/lows/closes/volumes）转 OHLCV 列表。"""
        if not kline or not kline.get("closes"):
            return []
        closes = kline.get("closes", [])
        opens = kline.get("opens", []) or closes
        highs = kline.get("highs", []) or closes
        lows = kline.get("lows", []) or closes
        volumes = kline.get("volumes", []) or [0] * len(closes)
        out = []
        for i in range(len(closes)):
            out.append({
                "open": opens[i] if i < len(opens) else closes[i],
                "high": highs[i] if i < len(highs) else closes[i],
                "low": lows[i] if i < len(lows) else closes[i],
                "close": closes[i],
                "volume": volumes[i] if i < len(volumes) else 0,
            })
        return out

    def _ml_overlay(self, fr: ForecastResult, kline) -> ForecastResult:
        """v8.0: 短期(1d/3d/5d)ML 叠加 — 有 sklearn 时把 ML 概率与 MC prob_up 按 0.4/0.6 混合。
        任何异常/缺依赖都静默降级返回原结果（不改变融合链路行为）。"""
        if fr.horizon not in ("1d", "3d", "5d"):
            return fr
        try:
            from stock_researcher.quantitative.ml_predictor import ml_available
            if not ml_available():
                return fr
            from stock_researcher.quantitative.ml_predictor import MultiHorizonMLPredictor
            ohlcv = self._kline_to_ohlcv(kline)
            if len(ohlcv) < 60:
                return fr
            mres = MultiHorizonMLPredictor(model_type="randomforest").train_and_predict(ohlcv)
            if not isinstance(mres, dict) or fr.horizon not in mres:
                return fr
            m = mres[fr.horizon]
            ml_up = m.get("prob_up")
            ml_conf = m.get("confidence", 0.0)
            if ml_up is None:
                return fr
            ml_up_pct = ml_up * 100.0 if ml_up <= 1.0 else float(ml_up)
            # 仅当 ML 置信度高且方向分歧明显时才改写（避免低置信噪声）
            if ml_conf >= 0.5 and abs(ml_up_pct - fr.prob_up) > 15:
                fr.prob_up = round(0.6 * fr.prob_up + 0.4 * ml_up_pct, 1)
                if fr.prob_up > 55:
                    fr.direction = "看多"
                elif fr.prob_up < 45:
                    fr.direction = "看空"
                else:
                    fr.direction = "震荡"
                fr.narrative += f"｜ML叠加↑(prob_up→{fr.prob_up:.0f}%, conf={ml_conf:.2f})"
        except Exception:
            pass
        return fr

    def _track_predictions(self, target_type: str, code, hresults) -> None:
        """v8.0: 接通进化闭环（PredictionTracker）— 默认关闭，track=True 时启用。"""
        try:
            from stock_researcher.evolution.prediction_tracker import PredictionTracker
            t = PredictionTracker()
            for h, fr in (hresults or {}).items():
                if isinstance(fr, ForecastResult):
                    t.new_record(target_type, str(code), h, "multi_horizon_forecaster",
                                 fr.direction, fr.predicted_pct, fr.confidence)
        except Exception:
            pass

    def _forecast_from_bundle(
        self, bundle: SignalBundle, prices: List[float],
        horizons: List[str] = None, kline=None, regime: Optional[str] = None,
    ) -> Dict[str, ForecastResult]:
        """从 SignalBundle 生成所有周期的 ForecastResult

        v9.0: regime 非 None 时启用体制条件化融合（权重+动量折扣+置信调整）。
        """
        horizons = horizons or list(HORIZONS.keys())
        results = {}

        # v9.0: 体制下的信号共识度（一次性，供各周期置信调整复用）
        consensus_dict = None
        if regime:
            try:
                from stock_researcher.fusion.signal_consensus import SignalConsensus
                cons = SignalConsensus().compute(bundle.dimensions)
                consensus_dict = {
                    "label": cons.label, "consensus_score": cons.consensus_score,
                    "dispersion": cons.dispersion,
                    "confidence_multiplier": cons.confidence_multiplier,
                }
            except Exception:
                pass

        for h in horizons:
            horizon_days = HORIZONS[h]

            # 融合得分（v9.0: 传入 regime）
            used, composite, conf_fusion, risks = self._fuse_scores(
                bundle, h, regime=regime,
            )

            # 蒙特卡洛（融合得分以 μ 调整项进入模拟）
            if prices and len(prices) >= 20:
                pred_pct, p10, p50, p90, prob_up = self._monte_carlo(
                    prices, horizon_days, sims=500, composite=composite
                )
            else:
                # 无价格数据：仅用融合得分推断
                pred_pct = composite * 0.1  # 简单缩放
                lo, hi = sorted((pred_pct * 0.7, pred_pct * 1.3))
                p10, p50, p90 = lo, pred_pct, hi
                prob_up = 50

            # 方向判定（综合融合得分 + MC结果，当两者矛盾时标注"分歧"）
            mc_bullish = prob_up > 55
            signal_bullish = composite > 10
            signal_bearish = composite < -10

            if signal_bullish and mc_bullish:
                direction = "看多"
            elif signal_bearish and not mc_bullish:
                direction = "看空"
            elif signal_bullish and not mc_bullish:
                direction = "分歧偏多"  # 信号看多但动量/趋势不配合
            elif signal_bearish and mc_bullish:
                direction = "分歧偏空"
            elif abs(composite) <= 10:
                direction = "震荡"
            else:
                direction = "分歧"

            # MC 置信度：预测幅度越小越可信，并随区间宽度惩罚（长周期区间宽 → 置信降）
            if prices and len(prices) >= 30:
                width_penalty = max(0.5, 1.0 - (p90 - p10) / 60)
                mc_conf = 0.6 * max(0.1, 1.0 - abs(pred_pct) / 20) * width_penalty
            else:
                mc_conf = 0.3
            confidence = round(max(0.1, min(0.95, conf_fusion * 0.6 + mc_conf * 0.4)), 3)

            # v9.0: 体制 + 共识度对置信度的调整（regime=None 时不变）
            if regime:
                try:
                    from stock_researcher.fusion.regime_overlay import RegimeOverlay
                    confidence *= RegimeOverlay.confidence_adjustment(regime)
                    if consensus_dict:
                        confidence *= consensus_dict["confidence_multiplier"]
                    confidence = round(max(0.1, min(0.95, confidence)), 3)
                except Exception:
                    pass

            # 驱动因素（按归一化贡献 |score×权重| 排序）
            hw = self._weights.get(h, DEFAULT_HORIZON_WEIGHTS.get(h, {}))
            tw = sum(hw.get(d.dimension, 0) for d in used) or 1

            def _contrib(d: DimensionSignal) -> float:
                return d.score * hw.get(d.dimension, 0) / tw

            dims_sorted = sorted(used, key=lambda d: abs(_contrib(d)), reverse=True)
            top_drivers = [
                {
                    "dimension": d.dimension,
                    "contribution": round(_contrib(d), 1),
                    "reason": self._make_reason(d),
                }
                for d in dims_sorted[:4]
            ]

            fr = ForecastResult(
                horizon=h, horizon_days=horizon_days, direction=direction,
                predicted_pct=pred_pct, p10=p10, p50=p50, p90=p90,
                prob_up=prob_up, confidence=confidence, composite_score=composite,
                top_drivers=top_drivers, risk_factors=risks[:3],
                narrative="",
                regime=regime, consensus=consensus_dict,
            )
            fr.narrative = self._generate_narrative(h, fr, used)
            # v8.0: 短期 ML 叠加（有 sklearn 时生效，否则 no-op）
            if kline is not None:
                fr = self._ml_overlay(fr, kline)
            results[h] = fr

        return results

    # ─── 个股预测 ────────────────────────────────────────
    def forecast_stock(
        self, code: str, kline: Dict = None, horizons: List[str] = None,
        track: bool = False, regime: Optional[str] = None,
    ) -> MultiHorizonForecast:
        """个股多周期预测。

        v8.0: track=True 时写入 PredictionTracker 接通进化闭环。
        v9.0: regime 启用体制条件化预测。
              regime=None（默认）→ 行为与 v8.0 完全一致（向后兼容）；
              regime="auto"     → 从价格历史自动检测体制（牛/熊/震荡）；
              regime="牛市"/"熊市"/"震荡" → 显式指定体制。
        """
        bundle = self._collector.collect_stock(code, kline)
        prices = kline.get("closes", []) if kline else []
        if not prices:
            try:
                from stock_researcher.data.market import MarketData
                kline = MarketData().fetch_history(code, days=120) or {}
                prices = kline.get("closes", [])
            except Exception:
                prices = []

        # v9.0: 体制检测（仅 regime="auto" 时）
        effective_regime = regime
        if regime == "auto":
            effective_regime = self._detect_regime(prices)

        hresults = self._forecast_from_bundle(
            bundle, prices, horizons, kline=kline, regime=effective_regime,
        )
        if track:
            self._track_predictions("stock", code, hresults)
        name = ""
        try:
            from core.data_providers.stock_price import StockPriceProvider
            name = StockPriceProvider().get(str(code).zfill(6)).get("name", "") or ""
        except Exception:
            pass
        return MultiHorizonForecast(
            target_type="stock", code=code, name=name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            horizons=hresults,
            signal_summary={d.dimension: d.score for d in bundle.dimensions if d.available},
            source_status=bundle.source_status,
            regime=effective_regime,
        )

    def _detect_regime(self, prices: List[float]) -> Optional[str]:
        """v9.0: 从价格序列推断体制（复用 scenario_simulator 检测器 + 归一）。"""
        if not prices or len(prices) < 60:
            return None
        try:
            from stock_researcher.fusion.regime_overlay import (
                detect_regime_from_prices, normalize_regime,
            )
            raw = detect_regime_from_prices(prices)
            return normalize_regime(raw)
        except Exception:
            return None

    # ─── 板块预测 ────────────────────────────────────────
    def forecast_sector(
        self, sector_name: str, codes: List[str], horizons: List[str] = None,
        track: bool = False
    ) -> MultiHorizonForecast:
        """板块多周期预测（取代表股信号均值 + 代表性最相关的K线）"""
        bundle = self._collector.collect_sector(sector_name, codes)

        # 取第一只代表股的价格做 MC（板块指数本身不直接有K线）
        prices = []
        kline = None
        if codes:
            try:
                from stock_researcher.data.market import MarketData
                kline = MarketData().fetch_history(codes[0], days=120) or {}
                prices = kline.get("closes", [])
            except Exception:
                pass

        hresults = self._forecast_from_bundle(bundle, prices, horizons, kline=kline)
        if track:
            self._track_predictions("sector", sector_name, hresults)
        return MultiHorizonForecast(
            target_type="sector", code=sector_name, name=sector_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            horizons=hresults,
            signal_summary={d.dimension: d.score for d in bundle.dimensions if d.available},
            source_status=bundle.source_status,
        )

    # ─── v7.0 统一资产预测 ─────────────────────────────────
    def forecast_asset(
        self, code: str, asset_type: str = "stock",
        name: str = "", horizons: List[str] = None,
        prices: List[float] = None, track: bool = False,
    ) -> MultiHorizonForecast:
        """
        统一资产多周期预测（v7.0 新增；v8.0 支持 ML overlay + 进化闭环 track）。

        支持四种资产类型：
          - "stock": 个股（默认，走 forecast_stock）
          - "index": 指数（走宏观+政策+估值主导权重）
          - "commodity": 商品（走宏观+技术主导权重）
          - "fund": 基金（走估值+宏观+政策主导权重）

        Args:
            code: 资产代码
            asset_type: "stock"|"index"|"commodity"|"fund"
            name: 资产名称（可选）
            horizons: 预测周期列表（默认全部）
            prices: 历史价格序列（可选，用于蒙特卡洛）
            track: v8.0 是否写入 PredictionTracker（进化闭环，默认关）

        Returns:
            MultiHorizonForecast
        """
        horizons = horizons or list(HORIZONS.keys())

        # 按资产类型选择信号采集方式
        if asset_type == "stock":
            bundle = self._collector.collect_stock(code)
        elif asset_type in ("index", "commodity"):
            # 指数/商品走通用信号采集（禁用不适用维度）
            bundle = self._collector.collect_stock(code)
        elif asset_type == "fund":
            bundle = self._collector.collect_stock(code)
        else:
            bundle = self._collector.collect_stock(code)

        # 获取价格序列（v8.0: 保留 kline 供 ML overlay 使用）
        kline = None
        if prices is None:
            try:
                from stock_researcher.data.market import MarketData
                kline = MarketData().fetch_history(code, days=250) or {}
                prices = kline.get("closes", [])
            except Exception:
                try:
                    from stock_researcher.data.global_market import fetch_global_kline
                    kline = fetch_global_kline(code, days=250)
                    prices = [k["close"] for k in kline] if kline else []
                except Exception:
                    prices = []

        # 按资产类型融合权重进行预测
        hresults = {}
        for h in horizons:
            horizon_days = HORIZONS[h]
            used, composite, conf_fusion, risks = self._fuse_scores(
                bundle, h, asset_type=asset_type
            )
            if prices and len(prices) >= 20:
                pred_pct, p10, p50, p90, prob_up = self._monte_carlo(
                    prices, horizon_days, sims=500, composite=composite
                )
            else:
                pred_pct = composite * 0.1
                lo, hi = sorted((pred_pct * 0.7, pred_pct * 1.3))
                p10, p50, p90 = lo, pred_pct, hi
                prob_up = 50

            # 方向判定
            mc_bullish = prob_up > 55
            signal_bullish = composite > 10
            signal_bearish = composite < -10
            if signal_bullish and mc_bullish:
                direction = "看多"
            elif signal_bearish and not mc_bullish:
                direction = "看空"
            elif signal_bullish and not mc_bullish:
                direction = "分歧偏多"
            elif signal_bearish and mc_bullish:
                direction = "分歧偏空"
            elif abs(composite) <= 10:
                direction = "震荡"
            else:
                direction = "分歧"

            if prices and len(prices) >= 30:
                width_penalty = max(0.5, 1.0 - (p90 - p10) / 80)
                mc_conf = 0.6 * max(0.1, 1.0 - abs(pred_pct) / 25) * width_penalty
            else:
                mc_conf = 0.3
            confidence = round(max(0.1, min(0.95, conf_fusion * 0.6 + mc_conf * 0.4)), 3)

            # 驱动因素
            hw = self._weights.get(h, DEFAULT_HORIZON_WEIGHTS.get(h, {}))
            if asset_type in ASSET_TYPE_WEIGHTS:
                asset_cfg = ASSET_TYPE_WEIGHTS[asset_type]
                if h in asset_cfg:
                    hw = {**hw, **asset_cfg[h]}
            tw = sum(hw.get(d.dimension, 0) for d in used) or 1

            def _contrib(d): return d.score * hw.get(d.dimension, 0) / tw
            dims_sorted = sorted(used, key=lambda d: abs(_contrib(d)), reverse=True)
            top_drivers = [
                {"dimension": d.dimension, "contribution": round(_contrib(d), 1),
                 "reason": self._make_reason(d)}
                for d in dims_sorted[:4]
            ]

            fr = ForecastResult(
                horizon=h, horizon_days=horizon_days, direction=direction,
                predicted_pct=pred_pct, p10=p10, p50=p50, p90=p90,
                prob_up=prob_up, confidence=confidence, composite_score=composite,
                top_drivers=top_drivers, risk_factors=risks[:3], narrative="",
            )
            fr.narrative = self._generate_narrative(h, fr, used)
            # v8.0: 短期 ML 叠加（有 sklearn 时生效，否则 no-op）
            if kline is not None:
                fr = self._ml_overlay(fr, kline)
            hresults[h] = fr

        if track:
            self._track_predictions(asset_type, code, hresults)

        return MultiHorizonForecast(
            target_type=asset_type, asset_type=asset_type,
            code=code, name=name or code,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            horizons=hresults,
            signal_summary={d.dimension: d.score for d in bundle.dimensions if d.available},
            source_status=bundle.source_status,
        )


# ── 模块级便捷函数 ──────────────────────────────────────────
def forecast_stock(code: str) -> MultiHorizonForecast:
    return MultiHorizonForecaster().forecast_stock(code)


def forecast_sector(sector_name: str, codes: List[str]) -> MultiHorizonForecast:
    return MultiHorizonForecaster().forecast_sector(sector_name, codes)


def format_forecast(fc: MultiHorizonForecast) -> str:
    asset_label = {"stock": "个股", "index": "指数", "sector": "板块",
                   "commodity": "商品", "fund": "基金"}.get(
        getattr(fc, 'asset_type', fc.target_type), fc.target_type)
    lines = [f"📊 多周期预测  |  {asset_label} {fc.code}  |  {fc.timestamp}",
             "=" * 75]
    labels = {"1d": "1个交易日", "3d": "3个交易日", "5d": "一周(5日)",
              "1M": "一个月(22日)", "1Q": "一个季度(66日)",
              "3M": "三个月(63日)", "6M": "半年(126日)"}
    for h in ["1d", "3d", "5d", "1M", "1Q", "3M", "6M"]:
        r = fc.horizons.get(h)
        if not r:
            continue
        lines.append(f"")
        lines.append(f"  [{labels.get(h, h):<16}]  {r.direction}  "
                     f"涨跌幅预测: {r.predicted_pct:+.2f}%")
        lines.append(f"    置信区间(80%): [{r.p10:+.2f}%  ~  {r.p90:+.2f}%]  "
                     f"中位数: {r.p50:+.2f}%  |  上涨概率: {r.prob_up:.0f}%")
        lines.append(f"    置信度: {r.confidence:.0%}  |  综合得分: {r.composite_score:+.0f}")
        for dr in r.top_drivers[:3]:
            lines.append(f"    · {dr['dimension']}面 {dr['contribution']:+.0f}分: {dr['reason'][:40]}")
        lines.append(f"    推演: {r.narrative}")
        if r.risk_factors:
            lines.append(f"    风险: {' | '.join(r.risk_factors[:2])}")
    lines.append("=" * 75)
    return "\n".join(lines)


def main():
    fc = forecast_stock("600519")
    print(format_forecast(fc))


if __name__ == "__main__":
    main()
