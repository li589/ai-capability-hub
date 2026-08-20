#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球指数趋势预测 (v7.0.0)
===========================
多周期（1M/3M/6M）全球主要股指趋势预测。
融合技术面、估值面、政策面、宏观面、全球联动五大维度。

纯 Python 标准库，零依赖。
数据源：东方财富 push2（免费、无 Key）。

用法:
    from stock_researcher.index_analysis.index_forecast import IndexForecaster
    fc = IndexForecaster()
    result = fc.forecast("sh000001", horizons=["1M", "3M", "6M"])
    print(fc.format_report(result))
"""

import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from stock_researcher.data.market import MarketData
from stock_researcher.core.technical import TechnicalAnalyzer


# ── 全球指数配置 ──────────────────────────────
# 指数代码 → {名称, 市场, 币种, 东财secid}
GLOBAL_INDEX_CONFIG = {
    # A股
    "sh000001": {"name": "上证指数", "market": "cn", "currency": "CNY", "secid": "1.000001"},
    "sz399001": {"name": "深证成指", "market": "cn", "currency": "CNY", "secid": "0.399001"},
    "sz399006": {"name": "创业板指", "market": "cn", "currency": "CNY", "secid": "0.399006"},
    "sh000688": {"name": "科创50", "market": "cn", "currency": "CNY", "secid": "1.000688"},
    # 港股
    "100.HSI": {"name": "恒生指数", "market": "hk", "currency": "HKD", "secid": "100.HSI"},
    "100.HSCEI": {"name": "国企指数", "market": "hk", "currency": "HKD", "secid": "100.HSCEI"},
    # 美股
    "100.SPX": {"name": "标普500", "market": "us", "currency": "USD", "secid": "100.SPX"},
    "100.NDX": {"name": "纳斯达克", "market": "us", "currency": "USD", "secid": "100.NDX"},
    "100.DJIA": {"name": "道琼斯", "market": "us", "currency": "USD", "secid": "100.DJIA"},
    # 亚太
    "100.N225": {"name": "日经225", "market": "jp", "currency": "JPY", "secid": "100.N225"},
    "100.KS11": {"name": "韩国KOSPI", "market": "kr", "currency": "KRW", "secid": "100.KS11"},
    "100.AS51": {"name": "澳洲ASX200", "market": "au", "currency": "AUD", "secid": "100.AS51"},
    "100.SENSEX": {"name": "印度SENSEX", "market": "in", "currency": "INR", "secid": "100.SENSEX"},
    "100.TWII": {"name": "台湾加权", "market": "tw", "currency": "TWD", "secid": "100.TWII"},
    # 欧洲
    "100.FTSE": {"name": "英国富时100", "market": "uk", "currency": "GBP", "secid": "100.FTSE"},
    "100.GDAXI": {"name": "德国DAX", "market": "de", "currency": "EUR", "secid": "100.GDAXI"},
    "100.FCHI": {"name": "法国CAC40", "market": "fr", "currency": "EUR", "secid": "100.FCHI"},
    # 北美其他
    "100.TSX": {"name": "加拿大TSX", "market": "ca", "currency": "CAD", "secid": "100.TSX"},
}


@dataclass
class IndexForecastResult:
    """指数预测结果"""
    code: str
    name: str
    market: str
    currency: str
    timestamp: str
    current_price: float = 0
    change_pct: float = 0

    # 各周期预测
    horizons: Dict[str, dict] = field(default_factory=dict)

    # 综合指标
    tech_score: float = 0        # 技术面得分 -100~+100
    valuation_score: float = 0   # 估值面得分 -100~+100
    policy_score: float = 0      # 政策面得分 -100~+100
    macro_score: float = 0       # 宏观面得分 -100~+100
    global_linkage: float = 0    # 全球联动强度 0~100

    # 跨市场相关性
    correlations: List[dict] = field(default_factory=list)

    # 风险提示
    risk_factors: List[str] = field(default_factory=list)
    summary: str = ""


class IndexForecaster:
    """
    全球指数多周期趋势预测器。

    分析维度：
      1. 技术面 (30%): 均线排列、RSI、MACD、ADX 趋势强度
      2. 估值面 (20%): PE 历史分位、股息率
      3. 政策面 (20%): 对该市场影响最大的政策信号
      4. 宏观面 (20%): 全球风险偏好、VIX、汇率
      5. 全球联动 (10%): 与标普500/恒生/日经的相关性

    预测周期：1M(22日) / 3M(63日) / 6M(126日)
    """

    HORIZON_DAYS = {"1M": 22, "3M": 63, "6M": 126}
    HORIZON_LABELS = {"1M": "未来一个月", "3M": "未来三个月", "6M": "未来半年"}

    def __init__(self):
        self._market_data = MarketData()
        self._tech_analyzer = TechnicalAnalyzer()

    def forecast(
        self, index_code: str, horizons: List[str] = None
    ) -> IndexForecastResult:
        """
        预测单个指数多周期走势。

        Args:
            index_code: 指数代码，如 "sh000001"、"100.N225"、"100.SPX"
            horizons: 预测周期列表，默认 ["1M", "3M", "6M"]

        Returns:
            IndexForecastResult
        """
        horizons = horizons or list(self.HORIZON_DAYS.keys())
        self._current_code = index_code   # v9.0：供 _analyze_valuation 取真实指数 PE
        cfg = GLOBAL_INDEX_CONFIG.get(index_code, {
            "name": index_code, "market": "cn", "currency": "CNY",
            "secid": index_code,
        })

        # 1) 获取行情数据
        quote = self._get_index_quote(index_code, cfg)
        current_price = quote.get("price", 0)
        change_pct = quote.get("chg_pct", 0)

        # 2) 技术分析
        tech = self._analyze_technical(index_code, cfg)

        # 3) 估值分析
        valuation = self._analyze_valuation(quote, cfg)

        # 4) 政策分析
        policy = self._analyze_policy(cfg)

        # 5) 宏观分析
        macro = self._analyze_macro()

        # 6) 全球联动
        global_link = self._analyze_global_linkage(index_code, cfg)

        # 7) 各周期预测
        horizon_results = {}
        risk_factors = []

        for h in horizons:
            days = self.HORIZON_DAYS[h]
            h_result = self._predict_horizon(
                tech, valuation, policy, macro, global_link, days, h, cfg
            )
            horizon_results[h] = h_result
            risk_factors.extend(h_result.get("risks", []))

        # 去重风险因素
        risk_factors = list(dict.fromkeys(risk_factors))[:5]

        # 生成摘要
        summary = self._generate_summary(horizon_results, cfg, change_pct)

        return IndexForecastResult(
            code=index_code,
            name=cfg["name"],
            market=cfg["market"],
            currency=cfg["currency"],
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_price=current_price,
            change_pct=change_pct,
            horizons=horizon_results,
            tech_score=tech["score"],
            valuation_score=valuation["score"],
            policy_score=policy["score"],
            macro_score=macro["score"],
            global_linkage=global_link["strength"],
            correlations=global_link.get("correlations", []),
            risk_factors=risk_factors,
            summary=summary,
        )

    def _get_index_quote(self, code: str, cfg: dict) -> dict:
        """获取指数实时行情"""
        if cfg["market"] == "cn":
            try:
                from stock_researcher.index_analysis.indices import IndexAnalyzer
                result = IndexAnalyzer().analyze_index(code)
                return {"price": result.price, "chg_pct": result.change_pct,
                        "pe": 0, "name": result.name}
            except Exception:
                pass

        # 全球指数走东财数据源
        try:
            from stock_researcher.data.global_market import (
                fetch_global_quote, _CLIENT
            )
            secid = cfg.get("secid", code)
            q = _CLIENT.get_quote(secid)
            if q:
                return {"price": q.get("price", 0), "chg_pct": q.get("chg_pct", 0),
                        "pe": q.get("pe", 0), "name": q.get("name", cfg["name"])}
            result = fetch_global_quote(f"idx:{code}")
            if result and "error" not in result:
                return result
        except Exception:
            pass

        return {"price": 0, "chg_pct": 0, "pe": 0, "name": cfg["name"]}

    def _analyze_technical(self, code: str, cfg: dict) -> dict:
        """技术面分析"""
        prices = []
        try:
            if cfg["market"] == "cn":
                kline = self._market_data.fetch_history(code, days=120)
                prices = kline.get("closes", []) if kline else []
            else:
                from stock_researcher.data.global_market import fetch_global_kline
                kline = fetch_global_kline(f"idx:{code}", days=120)
                prices = [k["close"] for k in kline] if kline else []
        except Exception:
            pass

        if len(prices) < 20:
            return {"score": 0, "ma_status": "data_insufficient", "rsi": 50}

        try:
            tech = self._tech_analyzer.analyze(code, prices)
        except Exception:
            return {"score": 0, "ma_status": "error", "rsi": 50}

        return {
            "score": tech.tech_score if hasattr(tech, 'tech_score') else 0,
            "ma_status": tech.ma_arrangement if hasattr(tech, 'ma_arrangement') else "",
            "rsi": tech.rsi14 if hasattr(tech, 'rsi14') else 50,
            "macd_hist": tech.macd_hist if hasattr(tech, 'macd_hist') else 0,
        }

    def _analyze_valuation(self, quote: dict, cfg: dict) -> dict:
        """估值面分析（v9.0：优先真实指数 PE 历史分位，失败降级粗阈值）。"""
        # v9.0 主路径：真实指数 PE 分位
        try:
            from stock_researcher.index_analysis.index_valuation import IndexValuation
            iv = IndexValuation().classify(
                getattr(self, "_current_code", ""), market=cfg["market"],
            )
            if iv.pe_percentile is not None:
                # 分位→score：低分位(便宜)→正分，高分位(贵)→负分
                score = (50.0 - iv.pe_percentile) * 0.6   # 0分位→+30, 100分位→-30
                return {
                    "score": round(max(-30, min(30, score)), 1),
                    "pe": iv.pe, "percentile": iv.pe_percentile,
                    "data_mode": iv.data_mode,
                    "note": f"真实PE分位{iv.pe_percentile:.0f}%({iv.data_mode})",
                }
            # 有 PE 无分位：用 PE 走下方阈值
            if iv.pe:
                quote = dict(quote, pe=iv.pe)
        except Exception:
            pass

        # 降级：原粗阈值逻辑（PE 分位估算）
        pe = quote.get("pe", 0) or 0
        if pe <= 0:
            return {"score": 0, "pe": 0, "note": "估值数据不可用"}

        # 粗略 PE 分位映射（按市场调整阈值）
        market = cfg["market"]
        if market in ("us", "jp"):
            cheap, expensive = 15, 25
        elif market in ("hk", "uk", "de", "fr"):
            cheap, expensive = 10, 20
        else:
            cheap, expensive = 12, 22

        if pe < cheap:
            score = 30
            note = f"PE={pe:.1f}，处于历史低位区间"
        elif pe < (cheap + expensive) / 2:
            score = 10
            note = f"PE={pe:.1f}，估值合理偏低"
        elif pe < expensive:
            score = -10
            note = f"PE={pe:.1f}，估值合理偏高"
        else:
            score = -30
            note = f"PE={pe:.1f}，处于历史高位区间"

        return {"score": score, "pe": pe, "note": note}

    def _analyze_policy(self, cfg: dict) -> dict:
        """政策面分析（集成 policy_analyzer）"""
        try:
            from stock_researcher.policy.policy_analyzer import PolicyAnalyzer
            pa = PolicyAnalyzer()
            impact = pa.analyze_market_impact(cfg["market"])
            return {
                "score": impact.get("score", 0),
                "direction": impact.get("direction", "中性"),
                "top_policies": impact.get("top_policies", []),
                "affected_sectors": impact.get("affected_sectors", []),
            }
        except Exception:
            pass
        return {"score": 0, "direction": "中性", "top_policies": [], "note": "政策数据暂不可用"}

    def _analyze_macro(self) -> dict:
        """宏观面分析（全球风险偏好）"""
        try:
            from stock_researcher.data.global_market import get_global_risk_appetite
            risk = get_global_risk_appetite()
            return {
                "score": risk.get("score", 0),
                "label": risk.get("label", "neutral"),
                "vix": risk.get("vix"),
                "signals": risk.get("signals", []),
            }
        except Exception:
            pass
        return {"score": 0, "label": "neutral", "vix": None}

    def _analyze_global_linkage(self, code: str, cfg: dict) -> dict:
        """全球联动分析"""
        correlations = []
        # 只对标普500和恒生做相关性（最关键的跨市场参考）
        try:
            from stock_researcher.data.global_market import get_market_correlation
            for ref_code, ref_name in [("100.SPX", "标普500"), ("100.HSI", "恒生指数")]:
                if ref_code != code:
                    corr = get_market_correlation(code, ref_code, days=60)
                    if corr.get("sample_days", 0) >= 10:
                        correlations.append({
                            "reference": ref_name,
                            "correlation": corr["correlation"],
                            "strength": corr["strength"],
                        })
        except Exception:
            pass

        # 计算联动强度
        avg_corr = sum(abs(c["correlation"]) for c in correlations) / max(len(correlations), 1)
        strength = avg_corr * 100  # 0-100

        return {"strength": round(strength, 1), "correlations": correlations}

    def _predict_horizon(
        self, tech: dict, valuation: dict, policy: dict,
        macro: dict, global_link: dict, days: int, horizon: str, cfg: dict
    ) -> dict:
        """单周期预测"""
        # 权重分配（按周期）
        if days <= 22:  # 1M
            w_tech, w_val, w_policy, w_macro, w_global = 0.30, 0.15, 0.20, 0.20, 0.15
        elif days <= 63:  # 3M
            w_tech, w_val, w_policy, w_macro, w_global = 0.20, 0.20, 0.25, 0.20, 0.15
        else:  # 6M
            w_tech, w_val, w_policy, w_macro, w_global = 0.10, 0.25, 0.30, 0.25, 0.10

        composite = (
            tech["score"] * w_tech +
            valuation["score"] * w_val +
            policy["score"] * w_policy +
            macro["score"] * w_macro +
            (global_link["strength"] - 50) / 50 * 20 * w_global  # 映射到-20~+20
        )

        # 方向判定
        if composite > 20:
            direction = "看多"
        elif composite > 5:
            direction = "偏多"
        elif composite > -5:
            direction = "震荡"
        elif composite > -20:
            direction = "偏空"
        else:
            direction = "看空"

        # 置信度
        confidence = min(0.9, 0.4 + abs(composite) / 100 * 0.5)

        # 风险因素
        risks = []
        if tech["score"] < -30:
            risks.append(f"技术面走弱({tech.get('ma_status', '')})")
        if valuation["score"] < -20:
            risks.append(f"估值偏高({valuation.get('pe', 0):.1f})")
        if macro.get("label") in ("risk_off", "mild_risk_off"):
            risks.append("全球风险偏好低迷")
        if composite < -15:
            risks.append("综合信号偏空，注意控制风险")

        return {
            "horizon": horizon,
            "horizon_label": self.HORIZON_LABELS.get(horizon, horizon),
            "days": days,
            "direction": direction,
            "composite_score": round(composite, 1),
            "confidence": round(confidence, 2),
            "drivers": {
                "tech": round(tech["score"] * w_tech, 1),
                "valuation": round(valuation["score"] * w_val, 1),
                "policy": round(policy["score"] * w_policy, 1),
                "macro": round(macro["score"] * w_macro, 1),
            },
            "risks": risks,
        }

    def _generate_summary(
        self, results: dict, cfg: dict, chg_pct: float
    ) -> str:
        """生成综合摘要"""
        parts = [f"{cfg['name']}今日{'涨' if chg_pct > 0 else '跌'}{abs(chg_pct):.2f}%。"]

        for h in ["1M", "3M", "6M"]:
            r = results.get(h)
            if r:
                dir_label = {"看多": "📈", "偏多": "↗", "震荡": "→",
                            "偏空": "↘", "看空": "📉"}.get(r["direction"], "")
                parts.append(
                    f"{self.HORIZON_LABELS.get(h, h)}{dir_label}{r['direction']}"
                    f"(得分{r['composite_score']:+.0f})"
                )

        return "；".join(parts)

    def format_report(self, result: IndexForecastResult) -> str:
        """格式化指数预测报告"""
        lines = [
            f"\n{'='*65}",
            f"  📊 {result.name}({result.code}) 指数趋势预测 v7.0",
            f"  {result.timestamp}",
            f"{'='*65}",
            f"  现价: {_fmt_currency(result.currency)}{result.current_price:.2f}  "
            f"涨跌: {result.change_pct:+.2f}%",
            f"",
            f"  ── 五维评分 ──",
            f"  技术面: {result.tech_score:+5.0f}  │  估值面: {result.valuation_score:+5.0f}  │  "
            f"政策面: {result.policy_score:+5.0f}",
            f"  宏观面: {result.macro_score:+5.0f}  │  全球联动: {result.global_linkage:.0f}/100",
            f"",
            f"  ── 多周期预测 ──",
        ]

        for h in ["1M", "3M", "6M"]:
            r = result.horizons.get(h)
            if r:
                lines.append(
                    f"  {r['horizon_label']:<12} {r['direction']:<6}  "
                    f"得分{r['composite_score']:+.0f}  置信度{r['confidence']:.0%}"
                )

        if result.risk_factors:
            lines.append(f"\n  ⚠ 风险提示: {' | '.join(result.risk_factors[:3])}")

        if result.correlations:
            lines.append(f"\n  ── 跨市场相关性 ──")
            for c in result.correlations:
                lines.append(f"  · {c['reference']}: {c['strength']}(r={c['correlation']:.2f})")

        lines.append(f"\n  {result.summary}")
        lines.append(f"{'='*65}")
        return "\n".join(lines)


# ── 便捷函数 ──

def _fmt_currency(ccy: str) -> str:
    return {"CNY": "¥", "HKD": "HK$", "USD": "$", "JPY": "JP¥",
            "GBP": "£", "EUR": "€", "INR": "₹", "KRW": "₩",
            "TWD": "NT$", "AUD": "A$", "CAD": "C$"}.get(ccy, "")


def forecast_index(code: str, horizons: List[str] = None) -> IndexForecastResult:
    """便捷函数：预测指数多周期走势"""
    return IndexForecaster().forecast(code, horizons)


def list_global_indices() -> List[dict]:
    """列出所有支持的全球指数"""
    return [
        {"code": code, "name": cfg["name"], "market": cfg["market"],
         "currency": cfg["currency"]}
        for code, cfg in GLOBAL_INDEX_CONFIG.items()
    ]
