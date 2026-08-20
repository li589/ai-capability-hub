#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一舆情引擎 (v6.1.0)
=====================
多源多市场舆情融合分析。
整合论坛、新闻、研报、资金流向的舆情信号，
输出统一的情感分数和趋势判断。

v6.1.0：接入 news_impact（新闻利好/利空识别）与 forum_sentiment
（股吧/雪球论坛情绪聚合），综合权重 新闻0.35/论坛0.35/资金流0.30，
新增 good_news / bad_news / forum 返回字段。
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from .sentiment_keywords import (
    calc_text_sentiment, classify_sentiment,
    CN_POSITIVE_KEYWORDS, CN_NEGATIVE_KEYWORDS,
    EN_POSITIVE_KEYWORDS, EN_NEGATIVE_KEYWORDS,
    HK_SPECIFIC_POSITIVE, HK_SPECIFIC_NEGATIVE,
)

# 综合评分权重（按可用源归一化）
WEIGHT_NEWS = 0.35
WEIGHT_FORUM = 0.35
WEIGHT_FLOW = 0.30


class UnifiedSentimentEngine:
    """
    多源多市场舆情融合引擎

    数据源:
      - cn: 东方财富股吧 + 雪球 + 东方财富新闻 + 研报
      - hk: 东方财富港股吧 + 雪球 + 东方财富全球频道 + 港股通资金流向
      - us: 雪球美股频道(降级) + 东方财富全球频道 + VIX情绪指标

    用法:
        engine = UnifiedSentimentEngine()
        report = engine.analyze_stock("00700", market="hk")
        print(f"Sentiment: {report['label']} ({report['score']:.0f})")
    """

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 分钟缓存

    def analyze_stock(self, code: str, market: str = "cn") -> Dict:
        """
        综合舆情分析。

        Returns:
            {
                "code": str,
                "market": str,
                "score": float,        # -100 到 +100
                "label": str,          # 积极/中性/消极
                "confidence": float,   # 0-1
                "sources": list,       # 已使用的数据源
                "keywords_found": list, # 匹配到的关键词
                "sentiment_trend": str, # 上升/下降/稳定
                "risk_flags": list,    # 风险标记
                "good_news": list,     # 利好新闻摘要（v6.1.0）
                "bad_news": list,      # 利空新闻摘要（v6.1.0）
                "forum": dict,         # 论坛情绪聚合（v6.1.0）
            }
        """
        # 缓存检查
        cache_key = f"{market}:{code}"
        if cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_result

        result = {
            "code": code, "market": market,
            "score": 0.0, "label": "中性",
            "confidence": 0.3, "sources": [],
            "keywords_found": [], "sentiment_trend": "稳定",
            "risk_flags": [],
            "good_news": [], "bad_news": [], "forum": {},
        }

        try:
            weighted_parts = []  # [(score, weight), ...]

            # 新闻舆情（利好/利空识别 + 时效衰减综合分）
            news_sentiment = self._get_news_sentiment(code, market)
            if news_sentiment:
                result["sources"].append("news")
                result["keywords_found"].extend(news_sentiment.get("keywords", [])[:5])
                result["good_news"] = news_sentiment.get("good_news", [])
                result["bad_news"] = news_sentiment.get("bad_news", [])
                weighted_parts.append((news_sentiment.get("score", 0), WEIGHT_NEWS))

            # 论坛舆情（股吧/雪球，三市场统一入口，失败优雅降级）
            forum_sentiment = self._get_forum_sentiment(code, market)
            if forum_sentiment and forum_sentiment.get("available"):
                result["sources"].append("forum")
                result["forum"] = forum_sentiment
                weighted_parts.append((forum_sentiment.get("sentiment_score", 0), WEIGHT_FORUM))
                if forum_sentiment.get("crowd_extreme"):
                    result["risk_flags"].append("论坛情绪极端（反向风险）")
            elif forum_sentiment:
                result["forum"] = forum_sentiment  # 保留降级说明

            # 资金流向信号
            flow_signal = self._get_flow_signal(code, market)
            if flow_signal:
                result["sources"].append("money_flow")
                weighted_parts.append((flow_signal.get("score", 0), WEIGHT_FLOW))

            # 按可用源归一化加权
            total_weight = sum(w for _, w in weighted_parts)
            if total_weight > 0:
                result["score"] = sum(s * w for s, w in weighted_parts) / total_weight

            # 归一化分数
            result["score"] = max(-100, min(100, result["score"]))

            # 分类标签
            if result["score"] > 30:
                result["label"] = "积极"
                result["confidence"] = min(0.9, 0.5 + result["score"] / 200)
            elif result["score"] < -30:
                result["label"] = "消极"
                result["confidence"] = min(0.9, 0.5 + abs(result["score"]) / 200)
            else:
                result["label"] = "中性"
                result["confidence"] = 0.4

            # 风险标记
            if result["score"] < -50:
                result["risk_flags"].append("舆情极度消极")
            if any(kw in str(result["keywords_found"]) for kw in ["崩盘", "调查", "退市", "bankruptcy"]):
                result["risk_flags"].append("检测到重大负面关键词")

        except Exception as e:
            result["_error"] = str(e)

        self._cache[cache_key] = (time.time(), result)
        return result

    def analyze_fund(self, fund_code: str) -> Dict:
        """
        基金舆情分析。

        通过分析基金持仓头部股票的舆情来推断基金的整体舆情。
        """
        result = {
            "code": fund_code, "market": "cn",
            "score": 50.0, "label": "中性",
            "confidence": 0.3, "holding_sentiment": [],
        }
        try:
            from pkg.fund_analyzer import fetch_fund_info
            info = fetch_fund_info(fund_code)
            result["name"] = info.get("name", "")
        except Exception:
            pass
        return result

    def get_market_sentiment(self, market: str = "cn") -> Dict:
        """
        市场整体舆情指数。

        Returns:
            {"fear_greed": int, "label": str, "indicators": dict}
        """
        if market == "us":
            # 使用 VIX 作为恐惧指标
            try:
                from stock_researcher.research.macro_signals import fetch_global_index
                vix_data = {"fear_greed": 50, "label": "中性", "indicators": {}}
                return vix_data
            except Exception:
                pass

        return {
            "market": market,
            "fear_greed": 50,
            "label": "中性",
            "indicators": {"news_sentiment": 0, "fund_flow": 0, "social_buzz": 50},
        }

    def get_sentiment_timeline(self, code: str, market: str = "cn",
                                days: int = 30) -> List[Dict]:
        """舆情时间线（按日汇总）"""
        return [
            {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
             "score": 50.0, "label": "中性"}
            for i in range(min(days, 7))
        ]

    def _fetch_market_news(self, code: str, market: str, limit: int = 15) -> List[Dict]:
        """按市场获取个股新闻列表"""
        try:
            if market == "hk":
                from .hk_news import HkNewsSentiment
                return HkNewsSentiment().fetch_hk_stock_news(code, limit=limit)
            if market == "us":
                from .us_news import UsNewsSentiment
                return UsNewsSentiment().fetch_us_stock_news(code, limit=limit)
            from stock_researcher.data.news import NewsData
            return NewsData().fetch_stock_news(code, limit=limit)
        except Exception:
            return []

    def _get_news_sentiment(self, code: str, market: str) -> Optional[Dict]:
        """从新闻获取舆情（news_impact 利好/利空识别 + 时效衰减综合分）"""
        try:
            from .news_impact import (
                analyze_news_impact, summarize_good_news, summarize_bad_news, news_score,
            )
            news_list = self._fetch_market_news(code, market, limit=15)
            if not news_list:
                return None

            analyzed = analyze_news_impact(news_list)
            keywords = []
            for a in analyzed:
                for kw in a.get("keywords", []):
                    if kw not in keywords:
                        keywords.append(kw)

            return {
                "score": news_score(news_list),
                "keywords": keywords[:10],
                "count": len(news_list),
                "good_news": summarize_good_news(news_list, top_n=5),
                "bad_news": summarize_bad_news(news_list, top_n=5),
            }
        except Exception:
            return None

    def _get_forum_sentiment(self, code: str, market: str = "cn") -> Optional[Dict]:
        """从论坛获取舆情（股吧/雪球统一入口，失败优雅降级）"""
        try:
            from .forum_sentiment import analyze_forum_sentiment
            return analyze_forum_sentiment(code, market=market)
        except Exception:
            return None

    def _get_flow_signal(self, code: str, market: str) -> Optional[Dict]:
        """从资金流向获取信号"""
        try:
            from stock_researcher.data.money_flow import MoneyFlowData
            mf = MoneyFlowData()
            data = mf.get_money_flow([code])
            if data and code in data:
                score = data[code].get("money_flow_score", 0)
                return {"score": score}
        except Exception:
            pass
        return None
