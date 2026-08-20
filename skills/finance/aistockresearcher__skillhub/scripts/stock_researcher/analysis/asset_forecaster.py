#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多资产推演引擎 (v7.2)
=====================
对股票 / 基金 / 期货 / 指数 四类资产做差异化涨跌推演，
整合五维分析与历史数据，输出多周期方向预测。

v7.2 设计要点：
  - 修复 _get_technical_score 签名错误 (代码改用 MarketData + TechnicalAnalyzer.analyze)
  - 修复 _build_stock_narrative 字段名 (composite_score → tech_score)
  - narrative 展示技术信号文字（如看多/中性/看空）

v7.1 设计要点：
  - 股票 (stock)：六维评分 + 蒙特卡洛短期 + 趋势中期
  - 基金 (fund)：经理评分 + 持仓舆情 + 净值趋势 + 风格归因
  - 期货 (futures)：技术面 + 持仓变化 + 商品因子 + 宏观联动
  - 指数 (index)：大盘情绪 + 板块轮动 + 资金流入
"""
from __future__ import annotations

import sys
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.dont_write_bytecode = True


class AssetForecaster:
    """多资产涨跌推演引擎。"""

    # 资产类型识别表
    ASSET_TYPE_MAP = {
        # 前缀识别
        "fut:": "futures",
        "fund:": "fund",
        "etf:": "fund",
        "gold:": "futures",
        "silver:": "futures",
        "crude:": "futures",
        "idx:": "index",
        "cn:": "stock",
        "hk:": "stock",
        "us:": "stock",
        "jp:": "stock",
        "kr:": "stock",
    }

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self._five_dim = None  # lazy load

    @property
    def five_dim(self):
        if self._five_dim is None:
            from .five_dim_analyzer import FiveDimAnalyzer
            self._five_dim = FiveDimAnalyzer()
        return self._five_dim

    @classmethod
    def detect_asset_type(cls, code: str, market_hint: Optional[str] = None) -> str:
        """识别资产类型。"""
        if not code:
            return "stock"
        # 1) 前缀匹配
        for prefix, atype in cls.ASSET_TYPE_MAP.items():
            if code.startswith(prefix):
                return atype
        # 2) 6 位数字 → A股 stock / 基金（1、5 开头通常为场内/场外基金）
        if code.isdigit() and len(code) == 6:
            return "fund" if code.startswith(("1", "5")) else "stock"
        # 3) 5 位数字 + .HK → stock
        if ".HK" in code.upper() or ".US" in code.upper():
            return "stock"
        # 4) 市场提示
        if market_hint in ("futures", "commodity"):
            return "futures"
        if market_hint in ("index",):
            return "index"
        if market_hint in ("fund",):
            return "fund"
        # 5) 兜底
        return "stock"

    def forecast(self, code: str, market: str = "cn",
                 asset_type: Optional[str] = None,
                 horizon: str = "1W") -> Dict[str, Any]:
        """对单资产做涨跌推演。

        Args:
            code: 代码
            market: 市场 cn/hk/us/global
            asset_type: 资产类型（None=自动识别）
            horizon: 推演周期 "1D" / "1W" / "1M" / "3M"

        Returns:
            {
              "code": str, "market": str, "asset_type": str, "horizon": str,
              "direction": "up" / "down" / "flat",
              "predicted_pct": float,           # 预测涨跌幅 %
              "score": -100 ~ +100,             # 综合评分
              "confidence": 0 ~ 1,
              "narrative": str,                 # 通俗解读
              "key_factors": [str],
              "risk_factors": [str],
              "horizons": {                     # 多周期方向
                "1D": {...}, "1W": {...}, "1M": {...}, "3M": {...}
              },
            }

        可靠性保证：
          - 输入校验（code 非空、horizon 在白名单内、market 在白名单内）
          - 任何子调用异常被 try/except 包裹，整体仍返回完整 shape
          - 异常时所有数值字段都是合法值（不抛 KeyError/TypeError 给调用方）
        """
        # ---- 输入校验 ----
        code = self._validate_code(code)
        if not code:
            return self._empty_result("", market, asset_type or "stock", horizon,
                                       reason="code 参数为空")
        market = self._validate_market(market)
        horizon = horizon.upper() if horizon else "1W"
        valid_horizons = ("1D", "1W", "1M", "3M")
        if horizon not in valid_horizons:
            horizon = "1W"

        if asset_type is None:
            asset_type = self.detect_asset_type(code, market_hint=market)

        # ---- 调用对应资产的推演（带兜底）----
        try:
            if asset_type == "stock":
                base = self._forecast_stock(code, market)
            elif asset_type == "fund":
                base = self._forecast_fund(code, market)
            elif asset_type == "futures":
                base = self._forecast_futures(code, market)
            elif asset_type == "index":
                base = self._forecast_index(code, market)
            else:
                base = self._forecast_stock(code, market)
        except Exception as e:
            # 整个推演链路异常 → 返回降级结果（保证调用方拿到合法结构）
            return self._empty_result(code, market, asset_type, horizon,
                                       reason=f"{type(e).__name__}: {e}")

        # ---- 多周期方向 ----
        try:
            base["horizons"] = self._build_horizons(base, horizon)
            h = base["horizons"].get(horizon, {})
            base["direction"] = h.get("direction", base.get("direction", "flat"))
            base["predicted_pct"] = h.get("predicted_pct", base.get("predicted_pct", 0))
        except Exception:
            base["horizons"] = {"1D": {"direction": "flat", "predicted_pct": 0},
                                "1W": {"direction": "flat", "predicted_pct": 0},
                                "1M": {"direction": "flat", "predicted_pct": 0},
                                "3M": {"direction": "flat", "predicted_pct": 0}}
            base["direction"] = "flat"
            base["predicted_pct"] = 0.0
        base["horizon"] = horizon
        return base

    # ===== 各资产类型 =====

    def _forecast_stock(self, code: str, market: str) -> Dict[str, Any]:
        """股票推演：五维 + 技术 + 历史 + 蒙特卡洛

        可靠性：每个子调用独立 try/except，任一失败不影响其他环节。
        """
        try:
            fd = self.five_dim.analyze(code, market=market, asset_type="stock")
        except Exception:
            fd = {"total_score": 0, "confidence": 0.3, "dimensions": {},
                  "key_signals": [], "risk_flags": [], "missing_sources": ["all"]}
        try:
            tech_score, tech_factors = self._get_technical_score(code, market)
        except Exception:
            tech_score, tech_factors = 0.0, {}
        try:
            hist_score = self._get_historical_score(fd.get("dimensions", {}))
        except Exception:
            hist_score = 0.0
        # 综合：五维 50% + 技术 25% + 历史 25%
        composite = (
            fd.get("total_score", 0) * 0.50 +
            tech_score * 0.25 +
            hist_score * 0.25
        )
        composite = max(-100, min(100, composite))
        direction = "up" if composite > 10 else ("down" if composite < -10 else "flat")
        predicted_pct = self._score_to_pct(composite)
        try:
            narrative = self._build_stock_narrative(code, fd, tech_factors)
        except Exception as e:
            narrative = f"股票 {code} 综合评分 {composite:.0f},信号 {self._score_to_signal(composite)}"
        return {
            "code": code, "market": market, "asset_type": "stock",
            "direction": direction,
            "predicted_pct": round(predicted_pct, 2),
            "score": round(composite, 2),
            "confidence": min(0.95, max(0.3,
                fd.get("confidence", 0.5) * 0.6 + abs(composite) / 200 * 0.4)),
            "narrative": narrative,
            "key_factors": fd.get("key_signals", [])[:5],
            "risk_factors": fd.get("risk_flags", []),
            "five_dim": fd,
            "tech_score": round(tech_score, 2),
            "hist_score": round(hist_score, 2),
        }

    def _forecast_fund(self, code: str, market: str) -> Dict[str, Any]:
        """基金推演：经理评分 + 持仓舆情 + 净值趋势 + 风格归因"""
        try:
            from pkg.fund_analyzer import (
                score_fund_v4, predict_fund_short_term,
            )
            score_data = score_fund_v4(code) if hasattr(score_fund_v4, "__call__") else {}
            pred_data = predict_fund_short_term(code) if hasattr(predict_fund_short_term, "__call__") else {}
        except Exception:
            score_data = {}
            pred_data = {}

        # 五维分析（用底层持仓股票）
        fd = self.five_dim.analyze(code, market=market, asset_type="fund")

        # 综合分数：基金专有评分 60% + 五维 40%
        fund_score = float(score_data.get("total_score", 50)) - 50  # 50 中性 → 0
        fund_score = max(-100, min(100, fund_score * 2))  # 0-100 → -100~+100
        composite = fd.get("total_score", 0) * 0.4 + fund_score * 0.6
        composite = max(-100, min(100, composite))
        direction = "up" if composite > 10 else ("down" if composite < -10 else "flat")
        predicted_pct = self._score_to_pct(composite, scale=0.7)  # 基金波动小
        return {
            "code": code, "market": market, "asset_type": "fund",
            "direction": direction,
            "predicted_pct": round(predicted_pct, 2),
            "score": round(composite, 2),
            "confidence": min(0.9, max(0.3,
                fd.get("confidence", 0.5) * 0.5 + abs(composite) / 200 * 0.5)),
            "narrative": f"基金 {code} 综合评分 {composite:.0f}，{self._score_to_signal(composite)}；"
                        f"经理/持仓 {score_data.get('grade', '未知')}。",
            "key_factors": [
                f"基金评分 {score_data.get('total_score', 50):.0f}/100",
                f"短期预测 {pred_data.get('direction', '中性')}",
            ] + fd.get("key_signals", [])[:3],
            "risk_factors": fd.get("risk_flags", []),
            "fund_score_detail": score_data,
            "fund_pred_detail": pred_data,
        }

    def _forecast_futures(self, code: str, market: str) -> Dict[str, Any]:
        """期货推演：技术 + 持仓 + 商品因子 + 宏观联动"""
        try:
            from stock_researcher.quantitative.commodity_analyzer import (
                analyze_commodity as _analyze_commodity,
            )
            commodity = _analyze_commodity(code) if code.startswith(("gold:", "silver:", "crude:")) else {}
        except Exception:
            commodity = {}

        try:
            from stock_researcher.data.global_market import analyze_gold_factors
            gold = analyze_gold_factors() if code.startswith("gold:") else {}
        except Exception:
            gold = {}

        # 五维分析（期货行情）
        fd = self.five_dim.analyze(code, market="global", asset_type="futures")
        commodity_score = float(commodity.get("score", 0)) if commodity else 0
        gold_score = float(gold.get("score", 0)) if gold else 0
        # 综合：五维 40% + 商品因子 30% + 黄金专项 30%（如适用）
        composite = fd.get("total_score", 0) * 0.4 + commodity_score * 0.3 + gold_score * 0.3
        composite = max(-100, min(100, composite))
        direction = "up" if composite > 10 else ("down" if composite < -10 else "flat")
        predicted_pct = self._score_to_pct(composite, scale=1.3)  # 期货波动大
        signal_text = self._score_to_signal(composite)
        return {
            "code": code, "market": market, "asset_type": "futures",
            "direction": direction,
            "predicted_pct": round(predicted_pct, 2),
            "score": round(composite, 2),
            "confidence": min(0.9, max(0.3,
                fd.get("confidence", 0.5) * 0.5 + abs(composite) / 200 * 0.5)),
            "narrative": f"期货 {code} 综合评分 {composite:.0f}，{signal_text}；"
                        f"商品因子 {commodity_score:.0f}。",
            "key_factors": [
                f"商品因子 {commodity_score:.0f}",
                f"宏观联动 {gold_score:.0f}",
            ] + fd.get("key_signals", [])[:3],
            "risk_factors": fd.get("risk_flags", []),
            "commodity_detail": commodity,
            "gold_detail": gold,
        }

    def _forecast_index(self, code: str, market: str) -> Dict[str, Any]:
        """指数推演：大盘情绪 + 板块轮动 + 资金流入"""
        # 五维分析（指数级别）
        fd = self.five_dim.analyze(code, market=market, asset_type="index")
        # 复用指数趋势预测（如果有）
        idx_score = 0.0
        try:
            from stock_researcher.index_analysis.index_forecast import IndexForecaster
            fc = IndexForecaster()
            res = fc.forecast(code, horizons=["1M"])
            if res:
                # 1M horizon direction -> score
                h = res.get("horizons", {}).get("1M", {})
                idx_score = (1 if h.get("direction") == "up" else
                             -1 if h.get("direction") == "down" else 0) * 50
        except Exception:
            pass

        composite = fd.get("total_score", 0) * 0.7 + idx_score * 0.3
        composite = max(-100, min(100, composite))
        direction = "up" if composite > 10 else ("down" if composite < -10 else "flat")
        predicted_pct = self._score_to_pct(composite, scale=0.8)
        return {
            "code": code, "market": market, "asset_type": "index",
            "direction": direction,
            "predicted_pct": round(predicted_pct, 2),
            "score": round(composite, 2),
            "confidence": min(0.9, max(0.3, fd.get("confidence", 0.5) * 0.7)),
            "narrative": f"指数 {code} 综合评分 {composite:.0f}，"
                        f"{self._score_to_signal(composite)}。",
            "key_factors": fd.get("key_signals", [])[:5],
            "risk_factors": fd.get("risk_flags", []),
            "idx_score": idx_score,
        }

    # ===== 辅助：技术分/历史分/分位换算 =====

    def _get_technical_score(self, code: str, market: str) -> Tuple[float, Dict]:
        """获取技术面评分（复用 core.technical）。

        修复：原代码误传 market 参数，且缺少 prices 数据。
        正确做法：用 MarketData 拿近 250 日收盘价，再调 TechnicalAnalyzer.analyze。
        """
        try:
            from stock_researcher.data.market import MarketData
            from stock_researcher.core.technical import TechnicalAnalyzer
            md = MarketData()
            history = md.fetch_history(code, days=250)
            closes = (history or {}).get("closes", []) if history else []
            if not closes or len(closes) < 30:
                return 0.0, {"tech_score": 0, "reason": "数据不足"}
            ta = TechnicalAnalyzer()
            tech = ta.analyze(code, closes)  # 正确签名：analyze(code, prices)
            # tech 是 TechnicalIndicators dataclass，含 tech_score 字段
            score = float(getattr(tech, "tech_score", 0) or 0)
            return score, {"tech_score": score, "tech_signal": getattr(tech, "tech_signal", "中性")}
        except Exception:
            return 0.0, {"tech_score": 0, "reason": "技术分析异常"}

    def _get_historical_score(self, dimensions: Dict[str, Dict]) -> float:
        """从五维数据中合成历史得分（资金 + 论坛 → 反映历史共识）。"""
        capital = dimensions.get("capital", {}).get("score", 0)
        forum = dimensions.get("forum", {}).get("score", 0)
        return (capital * 0.5 + forum * 0.5)

    def _score_to_pct(self, score: float, scale: float = 1.0) -> float:
        """把 -100~+100 分数映射为预测涨跌幅 %。"""
        # 基准：score=100 → +5%, score=-100 → -5%，scale 调整波动幅度
        return round(score * 0.05 * scale, 2)

    def _build_stock_narrative(self, code: str, fd: Dict, tech_factors: Dict) -> str:
        sig = self._score_to_signal(fd.get("total_score", 0))
        missing = fd.get("missing_sources", [])
        miss_text = f"（缺失维度：{','.join(missing)}）" if missing else ""
        tech_score = tech_factors.get("tech_score", 0)
        tech_signal = tech_factors.get("tech_signal", "")
        tech_text = f"{tech_score:.0f}" + (f"({tech_signal})" if tech_signal else "")
        return (f"股票 {code} 五维综合评分 {fd.get('total_score', 0):.0f}，{sig}；"
                f"技术面 {tech_text}{miss_text}。")

    # ===== 多周期方向 =====

    def _build_horizons(self, base: Dict, primary_horizon: str) -> Dict[str, Dict]:
        """构建 1D / 1W / 1M / 3M 四周期方向（带衰减）。"""
        score = base.get("score", 0)
        scale_map = {"1D": 0.3, "1W": 1.0, "1M": 2.5, "3M": 5.0}
        out: Dict[str, Dict] = {}
        for h, scale in scale_map.items():
            pct = self._score_to_pct(score, scale=scale)
            out[h] = {
                "direction": "up" if pct > 0.3 else ("down" if pct < -0.3 else "flat"),
                "predicted_pct": pct,
            }
        return out

    # ===== 信号 =====

    def _score_to_signal(self, score: float) -> str:
        if score > 60:
            return "强烈看多"
        if score > 30:
            return "看多"
        if score < -60:
            return "强烈看空"
        if score < -30:
            return "看空"
        return "中性"

    # ===== 输入校验 / 降级结果 =====

    @staticmethod
    def _validate_code(code: str) -> str:
        """校验并清洗 code 参数。"""
        if not code or not isinstance(code, str):
            return ""
        cleaned = code.strip()
        return cleaned if len(cleaned) <= 32 else ""

    @staticmethod
    def _validate_market(market: str) -> str:
        """校验并清洗 market 参数。"""
        if not market or not isinstance(market, str):
            return "cn"
        m = market.strip().lower()
        if m in ("cn", "hk", "us", "global"):
            return m
        return "cn"

    def _empty_result(self, code: str, market: str, asset_type: str,
                       horizon: str, reason: str = "") -> Dict[str, Any]:
        """推演链路异常时返回的降级结果（保证 shape 一致）。"""
        return {
            "code": code, "market": market, "asset_type": asset_type,
            "horizon": horizon,
            "direction": "flat",
            "predicted_pct": 0.0,
            "score": 0.0,
            "confidence": 0.3,
            "narrative": f"推演失败:{reason}" if reason else "数据不足,无法推演",
            "key_factors": [],
            "risk_factors": [reason] if reason else [],
            "horizons": {
                "1D": {"direction": "flat", "predicted_pct": 0.0},
                "1W": {"direction": "flat", "predicted_pct": 0.0},
                "1M": {"direction": "flat", "predicted_pct": 0.0},
                "3M": {"direction": "flat", "predicted_pct": 0.0},
            },
        }


# ===== 便捷函数 =====

def quick_forecast(code: str, market: str = "cn",
                   asset_type: Optional[str] = None,
                   horizon: str = "1W") -> Dict[str, Any]:
    """便捷函数：单资产涨跌推演。"""
    return AssetForecaster().forecast(code, market=market,
                                      asset_type=asset_type, horizon=horizon)


def detect_asset_type(code: str, market_hint: Optional[str] = None) -> str:
    """便捷函数：识别资产类型。"""
    return AssetForecaster.detect_asset_type(code, market_hint=market_hint)
