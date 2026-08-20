#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金舆情分析模块 (v7.0.0)
===========================
为基金量化分析提供舆情维度的数据支持。

分析维度：
  1. 基金吧/讨论区情绪爬取（东方财富基金吧）
  2. 基金经理变更/规模变动/限购公告的影响分析
  3. 基金申购赎回情绪指标
  4. 基金持有股票的加权情绪评分

纯 Python 标准库，零依赖。

用法:
    from stock_researcher.funds.fund_sentiment import FundSentimentAnalyzer
    fsa = FundSentimentAnalyzer()
    sentiment = fsa.analyze("110022")  # 基金代码
    weighted = fsa.estimate_holdings_sentiment("110022")
"""

import json
import re
import ssl
import urllib.request
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


# ── 基金情绪关键词 ──────────────────────────
FUND_POSITIVE_KEYWORDS = [
    "加仓", "买入", "定投", "持有", "锁仓", "看好", "优秀", "稳健",
    "分红", "金牛", "低估值", "低点", "抄底", "布局", "长期持有",
    "赎回费低", "规模适中", "限购解除", "开放申购", "净值新高",
]

FUND_NEGATIVE_KEYWORDS = [
    "赎回", "清仓", "跑路", "踩雷", "亏损", "回撤", "大跌", "踩踏",
    "限购", "暂停申购", "规模过大", "经理变更", "不看好", "清盘",
    "老鼠仓", "内幕", "净值新低", "偏离基准", "风格漂移",
]

FUND_STRONG_SIGNALS = {
    "限购": ("限购有时意味着基金经理保护现有持有人，中等偏正面", -2),
    "清盘": ("清盘风险，强烈利空", -8),
    "经理变更": ("基金经理变更带来不确定性，偏利空", -4),
    "暂停申购": ("暂停申购限制流动性，偏利空", -3),
    "规模过大": ("规模过大影响操作灵活性，偏利空", -2),
    "分红": ("分红回馈持有人，偏正面", +3),
    "金牛": ("金牛奖背书，中等正面", +4),
    "净值新高": ("净值创历史新高，偏正面", +3),
}


class FundSentimentAnalyzer:
    """
    基金舆情分析器。

    功能：
      1. 基金吧情绪爬取与分析
      2. 重大事件影响评估（经理变更/限购/分红等）
      3. 持仓股票加权情绪
    """

    def __init__(self):
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE

    def analyze(self, fund_code: str) -> dict:
        """
        分析基金综合舆情。

        Args:
            fund_code: 基金代码（如 110022）

        Returns:
            {
                "score": -100~+100（正=情绪偏多），
                "label": "积极"|"中性"|"消极",
                "hot_posts": [{title, sentiment}, ...],
                "events": [{event_type, impact_score, note}, ...],
                "holdings_sentiment": float or None,
                "summary": str
            }
        """
        # 1) 基金吧情绪
        forum = self._fetch_fund_forum(fund_code)

        # 2) 重大事件检测
        events = self._detect_events(fund_code)

        # 3) 综合评分
        forum_score = forum.get("score", 0)
        event_score = sum(e["impact_score"] for e in events) if events else 0

        # 论坛权重 0.6，事件权重 0.4
        composite = forum_score * 0.6 + event_score * 0.4

        # 标签
        if composite > 15:
            label = "积极"
        elif composite > -15:
            label = "中性"
        else:
            label = "消极"

        # 持仓情绪（可选，失败不影响）
        holdings_sent = None
        try:
            holdings_sent = self.estimate_holdings_sentiment(fund_code)
        except Exception:
            pass

        # 摘要
        parts = []
        if forum.get("post_count", 0) > 0:
            parts.append(f"基金吧{forum.get('post_count')}条帖子，"
                        f"多头比例{forum.get('bullish_ratio', 50):.0f}%")
        if events:
            for e in events[:2]:
                parts.append(f"{e['event_type']}:{e['note'][:30]}")
        summary = "；".join(parts) if parts else "暂无有效舆情数据"

        return {
            "score": round(composite, 1),
            "label": label,
            "forum": forum,
            "events": events,
            "holdings_sentiment": holdings_sent,
            "summary": summary,
        }

    def _fetch_fund_forum(self, fund_code: str) -> dict:
        """
        爬取基金吧帖子并进行情感分析。

        数据源：东方财富基金吧
        """
        try:
            # 东方财富基金吧
            url = (
                f"https://guba.eastmoney.com/list,{fund_code},2_1.html"
            )
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://guba.eastmoney.com/",
            })
            with urllib.request.urlopen(req, timeout=10,
                                        context=self._ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except Exception:
            return self._fallback_sentiment()

        # 解析帖子
        titles = re.findall(
            r'<span class="l3">.*?<a[^>]*title="([^"]*)"[^>]*>',
            raw, re.DOTALL
        )
        if not titles:
            titles = re.findall(r'class="note">\s*<a[^>]*>([^<]+)<', raw)

        if not titles:
            return self._fallback_sentiment()

        positive = 0
        negative = 0
        hot_posts = []

        for title in titles[:30]:
            sentiment = self._score_text(title)
            if sentiment > 0:
                positive += 1
            elif sentiment < 0:
                negative += 1
            hot_posts.append({
                "title": title[:60],
                "sentiment": sentiment,
            })

        total = len(titles)
        if total == 0:
            return self._fallback_sentiment()

        bullish_ratio = (positive / total * 100) if total > 0 else 50
        score = (positive - negative) / total * 100

        return {
            "post_count": total,
            "positive": positive,
            "negative": negative,
            "bullish_ratio": round(bullish_ratio, 1),
            "score": round(score, 1),
            "hot_posts": sorted(
                hot_posts, key=lambda p: abs(p["sentiment"]), reverse=True
            )[:5],
        }

    def _detect_events(self, fund_code: str) -> List[dict]:
        """
        检测重大事件（经理变更、限购、分红、清盘风险等）。

        通过东方财富基金公告 / 基金吧标题检测。
        """
        events = []
        try:
            url = (
                f"https://fundf10.eastmoney.com/jjgg_{fund_code}.html"
            )
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
            })
            with urllib.request.urlopen(req, timeout=10,
                                        context=self._ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except Exception:
            return events

        for signal, (note, impact) in FUND_STRONG_SIGNALS.items():
            if signal in raw:
                events.append({
                    "event_type": signal,
                    "note": note,
                    "impact_score": impact,
                })

        return events[:5]

    def _score_text(self, text: str) -> float:
        """对单条文本进行情感评分"""
        score = 0.0
        for kw in FUND_POSITIVE_KEYWORDS:
            if kw in text:
                score += 1.0
        for kw in FUND_NEGATIVE_KEYWORDS:
            if kw in text:
                score -= 1.0
        return max(-3, min(3, score))

    def _fallback_sentiment(self) -> dict:
        """无数据时的兜底返回值"""
        return {
            "post_count": 0, "positive": 0, "negative": 0,
            "bullish_ratio": 50, "score": 0, "hot_posts": [],
        }

    def estimate_holdings_sentiment(self, fund_code: str) -> Optional[dict]:
        """
        估算基金持仓股票的综合情绪。

        通过获取基金前十大持仓，计算其加权市场情绪。
        """
        try:
            import sys
            from pathlib import Path
            SKILL_DIR = Path(__file__).resolve().parents[3]
            sys.path.insert(0, str(SKILL_DIR / "scripts"))

            from stock_researcher.sentiment.sentiment_engine import UnifiedSentimentEngine
            engine = UnifiedSentimentEngine()

            # 获取前十大持仓
            try:
                from pkg.fund_analyzer import _fetch_fund_holdings_data
                holdings_data = _fetch_fund_holdings_data(fund_code)
                stock_codes = holdings_data.get("stock_codes", [])

                if not stock_codes:
                    return None

                scores = []
                for code in stock_codes[:10]:
                    try:
                        result = engine.analyze_stock(code, market="cn")
                        scores.append({
                            "code": code,
                            "sentiment_score": result.get("score", 0),
                            "label": result.get("label", "中性"),
                        })
                    except Exception:
                        pass

                if scores:
                    avg_score = sum(s["sentiment_score"] for s in scores) / len(scores)
                    return {
                        "stock_count": len(scores),
                        "weighted_score": round(avg_score, 1),
                        "label": "积极" if avg_score > 10 else (
                            "消极" if avg_score < -10 else "中性"),
                        "holdings": scores[:10],
                    }
            except Exception:
                pass
        except Exception:
            pass

        return None


# ── 便捷函数 ──

def analyze_fund_sentiment(fund_code: str) -> dict:
    """便捷函数：分析基金舆情"""
    return FundSentimentAnalyzer().analyze(fund_code)
