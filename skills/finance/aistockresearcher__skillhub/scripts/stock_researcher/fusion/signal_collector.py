#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全维度信号归一化收集器 (v4.0.0 新增)

对给定个股/板块，从 10 个维度收集归一化信号（-100 ~ +100），
输出统一 SignalBundle 供多周期预测编排器融合。

维度及数据来源：
  1. 技术面 technical    — MA/RSI/MACD/布林带/K线形态 (复用 MarketData+指标计算)
  2. 情绪面 sentiment    — 东方财富股吧/雪球论坛情绪 (SentimentForumCrawler)
  3. 资金面 money_flow   — 主力/北向/龙虎榜 (MoneyFlowData+SentimentEngine)
  4. 政策面 policy       — 政策板块影响映射 (policy_crawler)
  5. 新闻面 news         — 财联社/东财新闻关键词情感 (NewsProvider)
  6. 券商面 broker       — 机构评级/一致预期/目标价 (broker_research) [NEW]
  7. 估值面 valuation    — PE/PB 历史分位 (FundamentalData)
  8. 量化面 quant_vol    — GARCH 波动率状态 (量化引擎)
  9. 宏观面 macro        — 国际宏观风险偏好 (macro_signals) [NEW]
  10. 量化面 quant_factor— 多因子评分 (FactorAnalyzer)

设计原则：
  - 每个维度独立 fetch + 独立 try/except，任一失败不影响其余。
  - 归一化输出 -100 ~ +100 浮点分数（正=看多，负=看空）。
  - 附带 detail 原始数据供下游推理引用。
  - 板块模式：取代表股均值聚合。
"""
from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.path.insert(0, str(SKILL_DIR / "pkg"))


@dataclass
class DimensionSignal:
    """单维度信号"""
    dimension: str       # 维度名
    score: float         # -100 ~ +100
    direction: str       # "看多"/"看空"/"中性"
    detail: Dict = field(default_factory=dict)
    weight: float = 0.1  # 默认融合权重（会被 horizon-specific 覆盖）
    available: bool = True
    note: str = ""


@dataclass
class SignalBundle:
    """全维度信号包"""
    target_type: str     # "stock" | "sector"
    code: str            # 股票代码 或 板块名
    name: str            # 名称
    timestamp: str
    dimensions: List[DimensionSignal] = field(default_factory=list)
    source_status: Dict[str, str] = field(default_factory=dict)

    def get_score(self, dimension: str) -> Optional[float]:
        for d in self.dimensions:
            if d.dimension == dimension and d.available:
                return d.score
        return None

    def available_dimensions(self) -> List[str]:
        return [d.dimension for d in self.dimensions if d.available]


class SignalCollector:
    """全维度信号收集器"""

    # 默认维度权重（会被各周期的 horizon weights 覆盖，这里仅作各维度本身的基准）
    DEFAULT_WEIGHTS = {
        "technical": 0.15, "sentiment": 0.12, "money_flow": 0.12,
        "policy": 0.10, "news": 0.08, "broker": 0.12,
        "valuation": 0.12, "quant_vol": 0.05, "macro": 0.10, "quant_factor": 0.04,
    }

    def __init__(self):
        self._latest_macro = None  # 缓存每次会话的宏观信号（全场共享）

    # ─── 1. 技术面 ───────────────────────────────────────
    def _collect_technical(self, kline: Dict) -> DimensionSignal:
        """基于K线计算技术综合评分"""
        closes = kline.get("closes", []) if kline else []
        if len(closes) < 20:
            return DimensionSignal("technical", 0, "中性", available=False,
                                   note="K线数据不足(需≥20日)")
        import math
        current = closes[-1]
        score = 0.0
        detail = {}

        # 均线排列
        mas = {}
        for p in [5, 10, 20, 60]:
            if len(closes) >= p:
                ma = sum(closes[-p:]) / p
                mas[f"ma{p}"] = round(ma, 2)
        ma_keys = sorted(mas.keys())
        if len(ma_keys) >= 2:
            # 多头排列检查
            bullish = all(mas[k1] > mas[k2] for k1, k2 in zip(ma_keys[:-1], ma_keys[1:]))
            bearish = all(mas[k1] < mas[k2] for k1, k2 in zip(ma_keys[:-1], ma_keys[1:]))
            if bullish:
                score += 30; detail["ma_trend"] = "多头排列"
            elif bearish:
                score -= 30; detail["ma_trend"] = "空头排列"
            else:
                detail["ma_trend"] = "交叉整理"

        # RSI (14)
        rsi = self._calc_rsi(closes, 14)
        detail["rsi14"] = round(rsi, 1)
        if rsi > 70:
            score -= 10  # 超买
        elif rsi < 30:
            score += 15  # 超卖反弹
        elif rsi > 50:
            score += 5

        # MACD
        dif, hist = self._calc_macd(closes)
        detail["macd_hist"] = round(hist, 4)
        # 阈值按价格归一（hist 是价格量纲，高价股/低价股不可比）
        rel = abs(hist) / current if current > 0 else 0
        if hist > 0:
            score += 10 if rel > 0.0005 else 5
        else:
            score -= 10 if rel > 0.0005 else 5

        # 布林带位置
        if len(closes) >= 20:
            ma20 = sum(closes[-20:]) / 20
            std20 = math.sqrt(sum((c - ma20) ** 2 for c in closes[-20:]) / 20)
            bb_pos = (current - (ma20 - 2 * std20)) / (4 * std20) if std20 > 0 else 0.5
            detail["bb_position"] = round(bb_pos, 2)
            if bb_pos < 0.1:
                score += 15
            elif bb_pos > 0.9:
                score -= 10

        # 量比
        volumes = kline.get("volumes", [])
        if len(volumes) >= 6:
            ma5 = sum(volumes[-6:-1]) / 5 if len(volumes) >= 6 else volumes[-1]
            vol_ratio = volumes[-1] / ma5 if ma5 > 0 else 1.0
            detail["vol_ratio"] = round(vol_ratio, 2)
            if vol_ratio > 2.0:
                score += 10  # 放量
            elif vol_ratio < 0.5:
                score -= 5

        score = max(-100.0, min(100.0, score))
        direction = "看多" if score > 15 else ("看空" if score < -15 else "中性")
        return DimensionSignal("technical", round(score, 1), direction,
                               detail=detail, weight=self.DEFAULT_WEIGHTS["technical"])

    @staticmethod
    def _calc_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, period + 1):
            diff = prices[-i] - prices[-i - 1]
            gains.append(max(diff, 0)); losses.append(max(-diff, 0))
        avg_gain = sum(gains) / period; avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        return 100 - 100 / (1 + avg_gain / avg_loss)

    @staticmethod
    def _calc_macd(prices: List[float]) -> Tuple[float, float]:
        if len(prices) < 26:
            return 0.0, 0.0
        def ema_series(data, n):
            k = 2.0 / (n + 1)
            out = [data[0]]
            for v in data[1:]:
                out.append(v * k + out[-1] * (1 - k))
            return out
        ema12 = ema_series(prices, 12)
        ema26 = ema_series(prices, 26)
        dif_series = [a - b for a, b in zip(ema12, ema26)]
        dea_series = ema_series(dif_series, 9)
        dif = dif_series[-1]
        return dif, dif - dea_series[-1]  # hist = DIF - DEA

    # ─── 2. 情绪面 ──────────────────────────────────────
    def _collect_sentiment(self, code: str) -> DimensionSignal:
        try:
            from stock_researcher.sentiment.sentiment_engine import UnifiedSentimentEngine
            engine = UnifiedSentimentEngine()
            report = engine.analyze_stock(code, market="cn")
            if not report.get("sources"):
                return DimensionSignal("sentiment", 0, "中性", available=False,
                                       note="舆情数据不可用(新闻/论坛/资金流均失败)")
            score = report.get("score", 0)
            forum = report.get("forum") or {}
            score = max(-100.0, min(100.0, score))
            direction = "看多" if score > 15 else ("看空" if score < -15 else "中性")
            return DimensionSignal("sentiment", round(score, 1), direction,
                                   detail={"label": report.get("label", ""),
                                           "confidence": report.get("confidence", 0),
                                           "sources": report.get("sources", []),
                                           "forum_score": forum.get("sentiment_score"),
                                           "forum_heat": forum.get("heat"),
                                           "bullish_ratio": forum.get("bullish_ratio"),
                                           "crowd_extreme": forum.get("crowd_extreme", False),
                                           "good_news_count": len(report.get("good_news", [])),
                                           "bad_news_count": len(report.get("bad_news", []))},
                                   weight=self.DEFAULT_WEIGHTS["sentiment"],
                                   note=(report.get("forum") or {}).get("note", "")[:80])
        except Exception as e:
            return DimensionSignal("sentiment", 0, "中性", available=False, note=f"情绪数据获取失败: {e}")

    # ─── 3. 资金面 ──────────────────────────────────────
    def _collect_money_flow(self, code: str, kline: Dict) -> DimensionSignal:
        try:
            from core.data_providers.stock_price import StockPriceProvider
            provider = StockPriceProvider()
            rt = provider.get(code) or {}
            main_flow = rt.get("main_net_flow", 0)
            chg_pct = rt.get("change_pct", 0)
            turnover = rt.get("turnover", 0)
            # 主力净流入评分
            if main_flow and abs(main_flow) > 0:
                score = (main_flow / 1e8) * 0.5  # 每亿流入=0.5分
            else:
                score = chg_pct * 3  # 用涨跌近似
            score = max(-100.0, min(100.0, score))
            direction = "流入" if score > 10 else ("流出" if score < -10 else "中性")
            return DimensionSignal("money_flow", round(score, 1), direction,
                                   detail={"main_net_flow": main_flow, "change_pct": chg_pct,
                                           "turnover": turnover},
                                   weight=self.DEFAULT_WEIGHTS["money_flow"])
        except Exception as e:
            # 降级：用当日涨跌近似
            chg = (kline.get("closes", [0]) or [0])[-1]
            prev = (kline.get("closes", [0, 0]) or [0, 0])[-2]
            chg_pct = (chg - prev) / prev * 100 if prev > 0 else 0
            score = chg_pct * 3
            return DimensionSignal("money_flow", round(max(-100, min(100, score)), 1),
                                   "中性", available=True,
                                   detail={"change_pct_approx": round(chg_pct, 2)},
                                   note=f"实时行情不可用({e})，以K线涨跌幅近似")

    # ─── 4. 政策面 ──────────────────────────────────────
    def _collect_policy(self, sector_hint: str = "") -> DimensionSignal:
        try:
            from scripts.policy_crawler import (
                analyze_policy_impact, fetch_csrc_news, assess_impact,
            )
            news_list = fetch_csrc_news(limit=10) or []
            if not news_list:
                return DimensionSignal("policy", 0, "中性", available=False,
                                       note="未获取到实时政策")
            for n in news_list:
                n["impact"] = assess_impact(n.get("title", ""))
            analysis = analyze_policy_impact(news_list)
            sentiment = analysis.get("sentiment", "中性")
            smap = {"偏多": 30, "中性": 0, "偏空": -30}
            score = smap.get(sentiment, 0)
            detail = {"sentiment": sentiment}
            if sector_hint and analysis.get("sector_impact"):
                si = analysis["sector_impact"].get(sector_hint, {})
                detail["sector_impact"] = si
                if si.get("impact") == "利好":
                    score += 20
                elif si.get("impact") == "利空":
                    score -= 20
            score = max(-100.0, min(100.0, score))
            direction = "看好" if score > 10 else ("看空" if score < -10 else "中性")
            return DimensionSignal("policy", round(score, 1), direction, detail=detail,
                                   weight=self.DEFAULT_WEIGHTS["policy"])
        except Exception as e:
            return DimensionSignal("policy", 0, "中性", available=False, note=f"政策数据获取失败: {e}")

    # ─── 5. 新闻面 ──────────────────────────────────────
    def _collect_news(self, code: str) -> DimensionSignal:
        try:
            from stock_researcher.data.news import NewsData
            from stock_researcher.sentiment.news_impact import (
                analyze_news_impact, summarize_good_news, summarize_bad_news, news_score,
            )
            news = NewsData().fetch_stock_news(code, limit=20)
            if not news:
                return DimensionSignal("news", 0, "中性", available=False,
                                       note="未检索到相关新闻")
            analyzed = analyze_news_impact(news)
            good = summarize_good_news(news, top_n=5)
            bad = summarize_bad_news(news, top_n=5)
            pos = sum(1 for a in analyzed if a["direction"] == "利好")
            neg = sum(1 for a in analyzed if a["direction"] == "利空")
            score = news_score(news)
            score = max(-100.0, min(100.0, score))
            direction = "偏多" if score > 15 else ("偏空" if score < -15 else "中性")
            return DimensionSignal("news", round(score, 1), direction,
                                   detail={"articles": len(news),
                                           "good_news_count": len(good),
                                           "bad_news_count": len(bad),
                                           "positive_hits": pos, "negative_hits": neg,
                                           "good_news": [g.get("title", "") for g in good[:3]],
                                           "bad_news": [b.get("title", "") for b in bad[:3]]},
                                   weight=self.DEFAULT_WEIGHTS["news"])
        except Exception:
            return DimensionSignal("news", 0, "中性", available=False, note="新闻数据获取失败")

    # ─── 6. 券商面 ──────────────────────────────────────
    def _collect_broker(self, code: str) -> DimensionSignal:
        try:
            from stock_researcher.research.broker_research import BrokerResearcher
            nr = BrokerResearcher(recent_days=365)
            result = nr.analyze(code, limit=30)
            score = result.get("broker_score", 0)
            direction = result.get("consensus_rating", "中性")
            return DimensionSignal("broker", round(score, 1), direction,
                                   detail={"avg_score": result.get("avg_rating_score"),
                                           "total_ratings": result.get("total_ratings"),
                                           "consensus": result.get("consensus_rating"),
                                           "target_mean": result.get("target_price", {}).get("mean")},
                                   weight=self.DEFAULT_WEIGHTS["broker"])
        except Exception as e:
            return DimensionSignal("broker", 0, "中性", available=False, note=f"券商数据: {e}")

    # ─── 7. 估值面 ──────────────────────────────────────
    def _collect_valuation(self, code: str) -> DimensionSignal:
        try:
            from stock_researcher.data.fundamental import FundamentalData
            fd = FundamentalData()
            fin = fd.get_valuation(code) or {}
            pe = fin.get("pe", 0)
            pb = fin.get("pb", 0)
            if not pe or pe <= 0:
                return DimensionSignal("valuation", 0, "中性", available=False,
                                       note="估值数据缺失")
            # 简化的估值评分：PE 15~30 为中性偏低负分, PE < 10 为正分
            if pe < 10:
                score = 40
            elif pe < 15:
                score = 20
            elif pe < 30:
                score = 0
            elif pe < 50:
                score = -15
            else:
                score = -30
            detail = {"pe": pe, "pb": pb}
            direction = "低估" if score > 15 else ("高估" if score < -15 else "中性")
            return DimensionSignal("valuation", round(score, 1), direction, detail=detail,
                                   weight=self.DEFAULT_WEIGHTS["valuation"])
        except Exception as e:
            return DimensionSignal("valuation", 0, "中性", available=False,
                                   note=f"财务数据获取失败: {e}")

    # ─── 8. 宏观面 ──────────────────────────────────────
    def _collect_macro(self) -> DimensionSignal:
        try:
            if self._latest_macro is None:
                from stock_researcher.research.macro_signals import get_macro_signals
                self._latest_macro = get_macro_signals(with_news=False)
            risk = self._latest_macro.get("global_risk_appetite", {})
            score = risk.get("score", 0)
            direction = risk.get("label", "中性")[:2]
            return DimensionSignal("macro", round(score, 1), direction,
                                   detail={"label": risk.get("label"), "confidence": risk.get("confidence"),
                                           "contributors": risk.get("contributors", [])},
                                   weight=self.DEFAULT_WEIGHTS["macro"])
        except Exception:
            return DimensionSignal("macro", 0, "中性", available=False, note="宏观数据获取失败")

    # ─── 9 & 10. 量化面 ────────────────────────────────
    def _collect_quant(self, code: str, kline: Dict) -> Dict:
        """返回 quant_vol + quant_factor 两个维度"""
        vol_signal = DimensionSignal("quant_vol", 0, "中性", available=False, note="未启用")
        factor_signal = DimensionSignal("quant_factor", 0, "中性", available=False, note="未启用")
        closes = kline.get("closes", []) if kline else []
        if len(closes) < 50:
            return {"quant_vol": vol_signal, "quant_factor": factor_signal}

        # GARCH 波动率状态
        try:
            from stock_researcher.quantitative.garch_model import GarchForecaster
            fc = GarchForecaster(auto_select=True)
            result = fc.forecast(closes, horizon=5)
            regime = fc.analyze_volatility_regime(closes)
            reg = regime.get("regime", "正常")
            # 低波动偏多，高波动偏空，极低波动中性
            score_map = {"极低波动": -5, "低波动": 15, "正常": 0, "高波动": -20, "极高波动": -40}
            score = score_map.get(reg, 0)
            vol_signal = DimensionSignal("quant_vol", round(score, 1),
                                         "看空" if score < -10 else ("看多" if score > 10 else "中性"),
                                         detail={"regime": reg, "annual_vol": result.current_vol,
                                                 "forecast_vol": result.forecast_annual_vol},
                                         weight=self.DEFAULT_WEIGHTS["quant_vol"])
        except Exception as e:
            vol_signal.note = f"GARCH不可用: {e}"

        # 多因子（真实财务指标 + 真实估值 + K线动量/波动率；取不到真实数据则不可用）
        try:
            from stock_researcher.quantitative.factor_analysis import FactorAnalyzer
            from stock_researcher.data.fundamental import FundamentalData
            fd = FundamentalData()
            raw = fd.fetch_financial_indicators(code) or {}
            rows = raw.get("data") or []
            val = fd.get_valuation(code) or {}
            if not rows or not val.get("pe"):
                raise ValueError("无真实财务/估值数据")
            latest = rows[0]
            rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
            rmu = sum(rets) / len(rets)
            rvar = sum((r - rmu) ** 2 for r in rets) / len(rets)
            stock_data = {
                "symbol": code,
                "pe": val.get("pe", 0), "pb": val.get("pb", 0),
                "roe": fd.safe_float(latest.get("ROEJQ")),
                "gross_margin": fd.safe_float(latest.get("XSMLL")),
                "debt_ratio": fd.safe_float(latest.get("ZCFZL"), 50),
                "eps_growth": fd.safe_float(latest.get("EPSJBTZ")),
                "revenue_growth": fd.safe_float(latest.get("TOTALOPERATEREVETZ")),
                "volatility": math.sqrt(max(rvar, 0)) * (252 ** 0.5) * 100,
                "ret_20d": (closes[-1] / closes[-21] - 1) * 100 if len(closes) > 21 else 0,
                "ret_60d": (closes[-1] / closes[-61] - 1) * 100 if len(closes) > 61 else 0,
            }
            analyzer = FactorAnalyzer()
            reports = analyzer.score_stocks([stock_data])
            if reports:
                comp = reports[0].composite_score
                s = (comp - 50) * 1.0  # 50分→0
                factor_signal = DimensionSignal("quant_factor", round(max(-100, min(100, s)), 1),
                                                reports[0].recommendation,
                                                detail={"composite_score": comp,
                                                        "recommendation": reports[0].recommendation},
                                                weight=self.DEFAULT_WEIGHTS["quant_factor"])
        except Exception as e:
            factor_signal.note = f"因子数据不可用: {e}"
        return {"quant_vol": vol_signal, "quant_factor": factor_signal}

    # ─── 主入口 ──────────────────────────────────────────
    def collect_stock(self, code: str, kline: Optional[Dict] = None,
                       sector_hint: str = "") -> SignalBundle:
        """收集个股全维度信号"""
        code = str(code).zfill(6)
        if kline is None:
            try:
                from stock_researcher.data.market import MarketData
                kline = MarketData().fetch_history(code, days=120) or {}
            except Exception:
                kline = {}

        dimensions = [
            self._collect_technical(kline),
            self._collect_sentiment(code),
            self._collect_money_flow(code, kline),
            self._collect_policy(sector_hint),
            self._collect_news(code),
            self._collect_broker(code),
            self._collect_valuation(code),
            self._collect_macro(),
        ]
        quant_signals = self._collect_quant(code, kline)
        dimensions.append(quant_signals["quant_vol"])
        dimensions.append(quant_signals["quant_factor"])

        status = {d.dimension: ("ok" if d.available else "degraded") for d in dimensions}
        return SignalBundle(
            target_type="stock", code=code, name="",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dimensions=dimensions, source_status=status,
        )

    def collect_sector(self, sector_name: str, codes: List[str]) -> SignalBundle:
        """板块信号 = 代表股 signal bundle 均值聚合"""
        bundles = []
        for c in codes[:5]:  # 最多5只代表股
            try:
                bundles.append(self.collect_stock(c, sector_hint=sector_name))
            except Exception:
                continue
        if not bundles:
            return SignalBundle("sector", sector_name, sector_name,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                source_status={"error": "无代表股数据"})

        # 按维度聚合
        dim_names = list(self.DEFAULT_WEIGHTS.keys())
        merged = []
        for dn in dim_names:
            entries = []
            for b in bundles:
                for d in b.dimensions:
                    if d.dimension == dn and d.available:
                        entries.append(d)
            if entries:
                avg_score = sum(d.score for d in entries) / len(entries)
                merged.append(DimensionSignal(dn, round(avg_score, 1),
                                              "看多" if avg_score > 15 else ("看空" if avg_score < -15 else "中性"),
                                              available=True, weight=self.DEFAULT_WEIGHTS[dn],
                                              note=f"基于{len(entries)}只代表股"))
            else:
                merged.append(DimensionSignal(dn, 0, "中性", available=False))
        return SignalBundle("sector", sector_name, sector_name,
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            dimensions=merged,
                            source_status={d.dimension: ("ok" if d.available else "degraded")
                                           for d in merged})
