#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五维信息聚合分析器 (v7.1)
=========================
统一聚合政策面 / 资金面 / 财经信息 / 论坛信息 / 社会舆情 五类信号，
对股票/基金/期货/指数给出 -100 ~ +100 的综合评分 + 维度拆分 + 信号归类。

v7.1 设计要点：
  - 复用现有 PolicyAnalyzer / UnifiedSentimentEngine / MoneyFlowData
  - 失败优雅降级（每个维度单独 try/except，不阻断其他维度）
  - 权重可在 __init__ 覆盖（默认 policy=0.10/capital=0.25/news=0.25/forum=0.20/sentiment=0.20）
  - 输出包含每个维度的 raw_score + confidence + key_signals
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.dont_write_bytecode = True


class FiveDimAnalyzer:
    """五维信息聚合器 — 政策/资金/财经/论坛/舆情"""

    # 默认权重（v7.1：资金面加重到 25%，反映 A股资金驱动特征）
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "policy": 0.10,    # 政策面
        "capital": 0.25,   # 资金面
        "news": 0.25,      # 财经信息（新闻利好/利空）
        "forum": 0.20,     # 论坛信息（股吧/雪球情绪）
        "sentiment": 0.20, # 社会舆情（综合情绪）
    }

    # 信号等级阈值
    SIGNAL_THRESHOLDS = [
        (60, "强烈看多"),
        (30, "看多"),
        (-30, "中性"),
        (-60, "看空"),
    ]
    NEG_INF_SIGNAL = "强烈看空"

    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 cache_ttl_seconds: int = 300):
        self.weights = {**self.DEFAULT_WEIGHTS, **(weights or {})}
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = cache_ttl_seconds

    # ===== 主入口 =====

    def analyze(self, code: str, market: str = "cn",
                asset_type: str = "stock") -> Dict[str, Any]:
        """对单标的做五维分析。

        Args:
            code: 代码（如 "600519" / "hk:00700" / "us:AAPL" / "gold:comex"）
            market: 市场代码 cn/hk/us/global
            asset_type: 资产类型 stock/fund/futures/index/commodity

        Returns:
            {
              "code": str, "market": str, "asset_type": str,
              "timestamp": str,
              "dimensions": {                  # 五维各自详情
                "policy":   {"score": -100~+100, "confidence": 0~1, "signals": [...]},
                "capital":  {...},
                "news":     {...},
                "forum":    {...},
                "sentiment":{...},
              },
              "total_score": -100~+100,        # 加权综合
              "signal": "强烈看多/看多/中性/看空/强烈看空",
              "confidence": 0~1,               # 五维一致性 × 平均强度
              "available_sources": int,        # 实际成功获取的维度数（0~5）
              "missing_sources": [str],        # 失败的维度名
              "key_signals": [str],            # 高影响信号摘要
              "risk_flags": [str],
            }
        """
        cache_key = f"{market}:{asset_type}:{code}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        import time
        from datetime import datetime
        dimensions: Dict[str, Dict] = {}
        missing: List[str] = []
        key_signals: List[str] = []

        # 1) 政策面
        policy_result = self._analyze_policy(code, market, asset_type)
        if policy_result is None:
            missing.append("policy")
        else:
            dimensions["policy"] = policy_result
            key_signals.extend(policy_result.get("signals", [])[:2])

        # 2) 资金面
        capital_result = self._analyze_capital(code, market)
        if capital_result is None:
            missing.append("capital")
        else:
            dimensions["capital"] = capital_result
            key_signals.extend(capital_result.get("signals", [])[:2])

        # 3) 财经信息（新闻利好/利空）
        news_result = self._analyze_news(code, market)
        if news_result is None:
            missing.append("news")
        else:
            dimensions["news"] = news_result
            key_signals.extend(news_result.get("signals", [])[:2])

        # 4) 论坛信息（股吧/雪球）
        forum_result = self._analyze_forum(code, market)
        if forum_result is None:
            missing.append("forum")
        else:
            dimensions["forum"] = forum_result
            key_signals.extend(forum_result.get("signals", [])[:2])

        # 5) 社会舆情（综合情绪指数）
        sentiment_result = self._analyze_sentiment(code, market)
        if sentiment_result is None:
            missing.append("sentiment")
        else:
            dimensions["sentiment"] = sentiment_result
            key_signals.extend(sentiment_result.get("signals", [])[:2])

        # 加权综合（按可用维度归一化）
        total_score, total_weight = 0.0, 0.0
        for name, dim in dimensions.items():
            w = self.weights.get(name, 0.0)
            total_score += dim.get("score", 0) * w
            total_weight += w
        if total_weight > 0:
            total_score = total_score / total_weight
        total_score = max(-100.0, min(100.0, total_score))

        # 一致性 × 平均强度
        if dimensions:
            abs_scores = [abs(d.get("score", 0)) for d in dimensions.values()]
            avg_abs = sum(abs_scores) / len(abs_scores)
            # 一致性：所有维度是否同号
            signs = [1 if d.get("score", 0) >= 0 else -1 for d in dimensions.values()]
            consistency = abs(sum(signs)) / len(signs) if signs else 0
            confidence = round(min(0.95, max(0.30,
                0.5 * (avg_abs / 100) + 0.5 * consistency)), 3)
        else:
            confidence = 0.3

        result = {
            "code": code,
            "market": market,
            "asset_type": asset_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dimensions": dimensions,
            "total_score": round(total_score, 2),
            "signal": self._score_to_signal(total_score),
            "confidence": confidence,
            "available_sources": len(dimensions),
            "missing_sources": missing,
            "key_signals": key_signals[:5],
            "risk_flags": self._collect_risk_flags(dimensions),
        }

        self._cache_set(cache_key, result)
        return result

    def analyze_batch(self, codes: List[str], market: str = "cn",
                      asset_type: str = "stock") -> List[Dict[str, Any]]:
        """批量分析（顺序调用，依赖各自缓存）。"""
        return [self.analyze(code, market=market, asset_type=asset_type) for code in codes]

    # ===== 各维度 =====

    def _analyze_policy(self, code: str, market: str, asset_type: str) -> Optional[Dict]:
        """政策面：调用 PolicyAnalyzer 的市场级 + 板块级影响。

        可靠性：
          - try/except 包裹整个调用，任何失败返回 None（不阻断其他维度）
          - 输入白名单校验（market 在 cn/hk/us/global）
          - 返回结构始终一致
        """
        if not self._validate_market(market):
            return None
        try:
            from stock_researcher.policy import PolicyAnalyzer
            pa = PolicyAnalyzer()
            market_impact = pa.analyze_market_impact(market)
            if not isinstance(market_impact, dict):
                return None
            score = market_impact.get("score", 0)
            signals = []
            if market_impact.get("key_policies"):
                signals.extend(market_impact["key_policies"][:2])
            return {
                "score": max(-100, min(100, float(score) if score is not None else 0)),
                "confidence": 0.6 if score else 0.3,
                "signals": signals or ["政策环境稳定"],
                "source": market_impact.get("source", "policy_analyzer"),
            }
        except Exception as e:
            # 静默失败，不抛给上层（保证五维中其他维度仍能跑）
            return {"score": 0, "confidence": 0.2,
                    "signals": [f"政策数据异常:{type(e).__name__}"],
                    "source": "policy_analyzer (error)"}

    def _analyze_capital(self, code: str, market: str) -> Optional[Dict]:
        """资金面：调用 MoneyFlowData 拿单只/北向/主力资金流向。

        可靠性：
          - 输入校验（code 必须非空）
          - 数据缺失返回 None（让上层记录 missing_sources）
          - 异常也返回降级结构而非 None（避免完全丢失该维度）
        """
        if not code or not isinstance(code, str):
            return None
        try:
            from stock_researcher.data.money_flow import MoneyFlowData
            mf = MoneyFlowData()
            data = mf.get_money_flow([code])
            if not isinstance(data, dict) or code not in data:
                return None
            item = data[code]
            if not isinstance(item, dict):
                return None
            raw_score = float(item.get("money_flow_score", 0) or 0)
            signals = []
            main_inflow = item.get("main_inflow", 0)
            if main_inflow:
                if main_inflow > 0:
                    signals.append(f"主力资金净流入 {main_inflow:.0f}万")
                elif main_inflow < 0:
                    signals.append(f"主力资金净流出 {abs(main_inflow):.0f}万")
            return {
                "score": max(-100, min(100, raw_score)),
                "confidence": 0.7 if raw_score != 0 else 0.4,
                "signals": signals or ["资金流向平稳"],
                "source": "money_flow",
            }
        except Exception as e:
            return {"score": 0, "confidence": 0.2,
                    "signals": [f"资金数据异常:{type(e).__name__}"],
                    "source": "money_flow (error)"}

    def _analyze_news(self, code: str, market: str) -> Optional[Dict]:
        """财经信息：调用 UnifiedSentimentEngine 的新闻利好/利空分析。

        可靠性：
          - 输入校验（code/market）
          - 返回字典始终含 score / confidence / signals
          - 异常返回降级结构（避免五维中该维度消失）
        """
        if not code or not self._validate_market(market):
            return None
        try:
            from stock_researcher.sentiment import UnifiedSentimentEngine
            engine = UnifiedSentimentEngine()
            report = engine.analyze_stock(code, market=market)
            if not isinstance(report, dict):
                return None
            news_good = len(report.get("good_news", []) or [])
            news_bad = len(report.get("bad_news", []) or [])
            raw_score = float(report.get("score", 0) or 0)
            signals = []
            if news_good > news_bad:
                signals.append(f"利好新闻 {news_good} 条")
            elif news_bad > news_good:
                signals.append(f"利空新闻 {news_bad} 条")
            if report.get("risk_flags"):
                signals.append("新闻提示风险标记")
            return {
                "score": max(-100, min(100, raw_score)),
                "confidence": 0.6 if (news_good + news_bad) > 0 else 0.3,
                "signals": signals or ["暂无显著新闻"],
                "source": "news_impact",
                "good_count": news_good,
                "bad_count": news_bad,
            }
        except Exception as e:
            return {"score": 0, "confidence": 0.2,
                    "signals": [f"新闻数据异常:{type(e).__name__}"],
                    "source": "news_impact (error)"}

    def _analyze_forum(self, code: str, market: str) -> Optional[Dict]:
        """论坛信息：调用 forum_sentiment 拿股吧/雪球情绪聚合。

        可靠性：
          - 调用方可能返回 None 或 {"available": False}，统一降级为 0 分结构
          - 异常返回降级结构，confidence=0.2（不让该维度彻底消失）
        """
        if not code:
            return None
        try:
            from stock_researcher.sentiment.forum_sentiment import analyze_forum_sentiment
            result = analyze_forum_sentiment(code, market=market)
            if not result or not result.get("available"):
                return {
                    "score": 0, "confidence": 0.2,
                    "signals": ["论坛数据不可用"],
                    "source": "forum_sentiment (degraded)",
                }
            score = float(result.get("sentiment_score", 0) or 0)
            signals = []
            post_count = int(result.get("post_count", 0) or 0)
            if post_count > 0:
                signals.append(f"论坛帖数 {post_count}")
            if result.get("crowd_extreme"):
                signals.append("⚠️ 论坛情绪极端（反向风险）")
            return {
                "score": max(-100, min(100, score)),
                "confidence": 0.5 if post_count > 10 else 0.3,
                "signals": signals or ["论坛情绪平稳"],
                "source": "forum_sentiment",
                "post_count": post_count,
            }
        except Exception as e:
            return {"score": 0, "confidence": 0.2,
                    "signals": [f"论坛数据异常:{type(e).__name__}"],
                    "source": "forum_sentiment (error)"}

    def _analyze_sentiment(self, code: str, market: str) -> Optional[Dict]:
        """社会舆情：调用 get_market_sentiment + 关键词扫描。

        可靠性：
          - 即使 get_market_sentiment 返回非 dict，也降级返回中性值
          - 输入校验（market 在白名单内）
        """
        if not self._validate_market(market):
            return None
        try:
            from stock_researcher.sentiment import UnifiedSentimentEngine
            engine = UnifiedSentimentEngine()
            ms = engine.get_market_sentiment(market=market)
            if not isinstance(ms, dict):
                ms = {"fear_greed": 50, "label": "中性"}
            fear_greed = int(ms.get("fear_greed", 50) or 50)
            # fear_greed 0-100 转换为 -100 ~ +100
            raw_score = (fear_greed - 50) * 2
            label = ms.get("label", "中性")
            signals = [f"市场情绪: {label} ({fear_greed})"]
            return {
                "score": max(-100, min(100, raw_score)),
                "confidence": 0.5,
                "signals": signals,
                "source": "market_sentiment",
                "fear_greed": fear_greed,
            }
        except Exception as e:
            return {"score": 0, "confidence": 0.3,
                    "signals": [f"舆情数据异常:{type(e).__name__}"],
                    "source": "market_sentiment (error)"}

    # ===== 输入校验 =====

    @staticmethod
    def _validate_market(market: str) -> bool:
        """校验 market 参数。"""
        return market in ("cn", "hk", "us", "global")

    # ===== 辅助 =====

    def _score_to_signal(self, score: float) -> str:
        for thresh, sig in self.SIGNAL_THRESHOLDS:
            if score > thresh:
                return sig
        return self.NEG_INF_SIGNAL

    def _collect_risk_flags(self, dimensions: Dict[str, Dict]) -> List[str]:
        flags = []
        for name, dim in dimensions.items():
            if "⚠️" in str(dim.get("signals", [])):
                flags.append(f"{name}: 论坛情绪极端")
            for sig in dim.get("signals", []):
                if "风险" in str(sig) and "⚠️" not in str(sig):
                    flags.append(f"{name}: {sig}")
        return flags

    def _cache_get(self, key: str):
        import time
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
        return None

    def _cache_set(self, key: str, value):
        import time
        self._cache[key] = (time.time(), value)


# ===== 便捷函数 =====

def quick_five_dim(code: str, market: str = "cn",
                   asset_type: str = "stock") -> Dict[str, Any]:
    """便捷函数：用默认配置做五维分析。"""
    return FiveDimAnalyzer().analyze(code, market=market, asset_type=asset_type)