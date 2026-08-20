"""Sentiment module v7.0.0 — 多源多市场舆情监控 + 新闻利好识别 + 论坛情绪聚合"""
from .sentiment_keywords import calc_text_sentiment, classify_sentiment
from .sentiment_engine import UnifiedSentimentEngine
from .hk_news import HkNewsSentiment
from .us_news import UsNewsSentiment
from .notifier import Notifier
from .news_impact import (
    analyze_news_impact, summarize_good_news, summarize_bad_news, news_score,
)
from .forum_sentiment import analyze_forum_sentiment

__all__ = [
    "calc_text_sentiment", "classify_sentiment",
    "UnifiedSentimentEngine",
    "HkNewsSentiment", "UsNewsSentiment",
    "Notifier",
    # v7.0
    "analyze_news_impact", "summarize_good_news", "summarize_bad_news",
    "news_score", "analyze_forum_sentiment",
]
