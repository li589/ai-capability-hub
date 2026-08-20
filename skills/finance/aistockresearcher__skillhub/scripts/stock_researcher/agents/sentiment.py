#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪分析师 Agent
Sentiment Analyst Agent
新闻情感 + 资金流向 + 内幕交易 综合分析
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """情绪分析结果"""
    # 新闻情绪
    news_score: float = 0    # -100 ~ +100
    news_positive: int = 0   # 正面新闻数
    news_negative: int = 0   # 负面新闻数
    news_neutral: int = 0    # 中性新闻数

    # 资金流向
    money_flow_score: float = 0  # -100 ~ +100
    main_net_flow: float = 0     # 主力净流入(万)
    flow_direction: str = "中性"  # 流入/流出/中性

    # 内幕交易
    insider_score: float = 0  # -100 ~ +100

    # 综合情绪
    sentiment_score: float = 0  # -100 ~ +100
    sentiment_label: str = "中性"  # 利好/中性/利空
    confidence: float = 0.5


class SentimentAnalyzer:
    """
    情绪分析师

    双重信号源：
    1. 内幕交易 (30%): 大股东增减持、高管买卖
    2. 新闻情绪 (70%): 正面/负面关键词匹配

    评分体系：
    - 强烈利好: > 60
    - 利好: 30 ~ 60
    - 中性: -30 ~ 30
    - 利空: -60 ~ -30
    - 强烈利空: < -60
    """

    # 正面关键词
    POSITIVE_KEYWORDS = [
        "涨停", "大涨", "暴涨", "净流入", "业绩预增", "政策利好",
        "回购", "增持", "上调评级", "突破", "创新高", "国产替代",
        "中标", "订单", "合作", "扩张", "分拆上市", "转型成功",
        "超预期", "大幅增长", "行业龙头", "技术突破", "产能扩张"
    ]

    # 负面关键词
    NEGATIVE_KEYWORDS = [
        "跌停", "大跌", "暴跌", "净流出", "业绩下滑", "被调查",
        "被处罚", "减持", "下调评级", "产能过剩", "黑天鹅",
        "诉讼", "亏损", "债务危机", "流动性紧张", "商誉减值",
        "业绩变脸", "大幅减少", "库存积压", "竞争加剧", "政策利空"
    ]

    # 强信号词（权重加倍）
    STRONG_POSITIVE = ["涨停", "大涨", "业绩预增", "回购", "增持", "突破"]
    STRONG_NEGATIVE = ["跌停", "大跌", "被调查", "被处罚", "债务危机"]

    def analyze(
        self,
        news_list: List[Dict] = None,  # 新闻列表 [{"title": "", "content": "", "sentiment": 0}]
        main_net_flow: float = 0,      # 主力净流入(万)
        mkt_cap: float = 0,            # 市值(万)
        change_pct: float = 0,         # 当日涨跌幅%
        insider_buys: int = 0,         # 内幕买入次数
        insider_sells: int = 0,        # 内幕卖出次数
        short_interest: float = 0,     # 做空比例
    ) -> SentimentResult:
        """
        执行情绪分析

        Args:
            news_list: 新闻列表
            main_net_flow: 主力净流入(万)
            mkt_cap: 市值(万)
            change_pct: 当日涨跌幅%
            insider_buys: 内幕买入次数
            insider_sells: 内幕卖出次数
            short_interest: 做空比例

        Returns:
            SentimentResult
        """
        news_list = news_list or []

        # 1. 新闻情绪分析 (70%)
        news_score, positive_count, negative_count, neutral_count = self._analyze_news(news_list)

        # 2. 资金流向分析 (权重取决于规模)
        flow_ratio = main_net_flow / mkt_cap * 100 if mkt_cap > 0 else 0
        money_flow_score = self._calc_money_flow_score(main_net_flow, mkt_cap, change_pct)

        # 3. 内幕交易分析 (30%)
        insider_score = self._calc_insider_score(insider_buys, insider_sells)

        # 综合情绪评分
        # 新闻 70% + 资金 20% + 内幕 10%
        sentiment_score = (
            news_score * 0.70 +
            money_flow_score * 0.20 +
            insider_score * 0.10
        )

        # 置信度
        total_news = positive_count + negative_count + neutral_count
        confidence = min(0.95, 0.3 + total_news * 0.1)

        # 情绪标签
        sentiment_label = self._get_sentiment_label(sentiment_score)

        # 资金流向方向
        if flow_ratio > 0.5:
            flow_direction = "大幅流入"
        elif flow_ratio > 0.1:
            flow_direction = "流入"
        elif flow_ratio < -0.5:
            flow_direction = "大幅流出"
        elif flow_ratio < -0.1:
            flow_direction = "流出"
        else:
            flow_direction = "中性"

        return SentimentResult(
            news_score=round(news_score, 1),
            news_positive=positive_count,
            news_negative=negative_count,
            news_neutral=neutral_count,
            money_flow_score=round(money_flow_score, 1),
            main_net_flow=round(main_net_flow, 1),
            flow_direction=flow_direction,
            insider_score=round(insider_score, 1),
            sentiment_score=round(sentiment_score, 1),
            sentiment_label=sentiment_label,
            confidence=round(confidence, 2)
        )

    def _analyze_news(self, news_list: List[Dict]) -> Tuple[float, int, int, int]:
        """分析新闻情绪"""
        if not news_list:
            return 0, 0, 0, 0

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            text = title + " " + content

            score = self._calc_text_sentiment(text)

            if score > 0.5:
                positive_count += 1
            elif score < -0.5:
                negative_count += 1
            else:
                neutral_count += 1

        # 计算新闻情绪得分
        total = len(news_list)
        if total == 0:
            return 0, 0, 0, 0

        net_score = positive_count - negative_count

        # 归一化到 -100 ~ +100
        news_score = (net_score / total) * 100

        return news_score, positive_count, negative_count, neutral_count

    def _calc_text_sentiment(self, text: str) -> float:
        """计算文本情感分数"""
        if not text:
            return 0

        text_lower = text.lower()
        score = 0

        # 检查强信号词
        for kw in self.STRONG_POSITIVE:
            if kw in text:
                score += 2

        for kw in self.STRONG_NEGATIVE:
            if kw in text:
                score -= 2

        # 检查普通关键词
        for kw in self.POSITIVE_KEYWORDS:
            if kw in text:
                score += 1

        for kw in self.NEGATIVE_KEYWORDS:
            if kw in text:
                score -= 1

        # 归一化
        return max(-3, min(3, score))

    def _calc_money_flow_score(
        self,
        main_net_flow: float,
        mkt_cap: float,
        change_pct: float
    ) -> float:
        """计算资金流向评分"""
        # 净流入/市值比率
        flow_ratio = main_net_flow / mkt_cap * 100 if mkt_cap > 0 else 0

        score = 0

        # 资金比率评分
        if flow_ratio > 1:
            score += 40
        elif flow_ratio > 0.5:
            score += 30
        elif flow_ratio > 0.1:
            score += 20
        elif flow_ratio > 0:
            score += 10
        elif flow_ratio < -1:
            score -= 40
        elif flow_ratio < -0.5:
            score -= 30
        elif flow_ratio < -0.1:
            score -= 20
        else:
            score -= 10

        # 涨跌幅辅助判断
        if change_pct > 5:
            score += 20
        elif change_pct > 2:
            score += 10
        elif change_pct < -5:
            score -= 20
        elif change_pct < -2:
            score -= 10

        return max(-100, min(100, score))

    def _calc_insider_score(self, buys: int, sells: int) -> float:
        """计算内幕交易评分"""
        total = buys + sells
        if total == 0:
            return 0

        buy_ratio = buys / total

        # 买入多于卖出
        if buy_ratio > 0.7:
            return 30
        elif buy_ratio > 0.6:
            return 20
        elif buy_ratio > 0.5:
            return 10
        elif buy_ratio < 0.3:
            return -30
        elif buy_ratio < 0.4:
            return -20
        else:
            return 0

    def _get_sentiment_label(self, score: float) -> str:
        """获取情绪标签"""
        if score > 60:
            return "强烈利好"
        elif score > 30:
            return "利好"
        elif score > -30:
            return "中性"
        elif score > -60:
            return "利空"
        else:
            return "强烈利空"

    def get_sentiment_advice(self, result: SentimentResult) -> Dict:
        """获取情绪分析建议"""
        advice = {
            "sentiment_label": result.sentiment_label,
            "sentiment_score": result.sentiment_score,
            "confidence": result.confidence,
            "key_factors": []
        }

        # 新闻因素
        if result.news_positive > result.news_negative:
            advice["key_factors"].append(f"正面新闻多({result.news_positive} vs {result.news_negative})")
        elif result.news_negative > result.news_positive:
            advice["key_factors"].append(f"负面新闻多({result.news_negative} vs {result.news_positive})")

        # 资金因素
        if result.main_net_flow > 0:
            advice["key_factors"].append(f"主力净流入{result.main_net_flow:.0f}万")
        else:
            advice["key_factors"].append(f"主力净流出{abs(result.main_net_flow):.0f}万")

        # 建议
        if result.sentiment_label in ("强烈利好", "利好"):
            advice["suggestion"] = "情绪面支持上涨，可关注"
        elif result.sentiment_label == "中性":
            advice["suggestion"] = "情绪面中性，等待更多信号"
        else:
            advice["suggestion"] = "情绪面偏空，谨慎操作"

        return advice