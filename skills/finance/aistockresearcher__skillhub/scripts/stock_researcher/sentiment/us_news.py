#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股新闻舆情 (v6.0.0)
=====================
美股市场新闻获取与情感分析。
数据源：东方财富全球频道（免费，国内直连）。
"""

import re
import json
import urllib.request
import ssl
from typing import Dict, List

from .sentiment_keywords import (
    calc_text_sentiment, classify_sentiment,
    EN_POSITIVE_KEYWORDS, EN_NEGATIVE_KEYWORDS,
    EN_STRONG_POSITIVE, EN_STRONG_NEGATIVE,
)


class UsNewsSentiment:
    """
    美股新闻舆情分析。

    数据源: 东方财富全球频道 column=358 (全球财经快讯)

    用法:
        us = UsNewsSentiment()
        news = us.fetch_us_stock_news("AAPL")
        sentiment = us.analyze(news)
    """

    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def fetch_us_stock_news(self, code: str, limit: int = 15) -> List[Dict]:
        """
        获取美股个股新闻。

        通过东方财富搜索 API 搜索美股代码相关新闻。
        """
        param = json.dumps({
            "uid": "",
            "keyword": code,
            "type": ["cmsArticle"],
            "client": "web",
            "clientType": "pc",
            "clientVersion": "curr",
            "param": {
                "cmsArticle": {
                    "searchScope": "default",
                    "sort": "default",
                    "pageIndex": 1,
                    "pageSize": limit,
                    "preTag": "",
                    "postTag": "",
                }
            }
        }, ensure_ascii=False).replace(" ", "")

        encoded = urllib.parse.quote(param, safe="")
        url = f"https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param={encoded}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.eastmoney.com/",
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")

            json_match = re.search(r'jQuery\((\{.*\})\)', raw, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                return []

            data = json.loads(json_match.group(1) if json_match.group(1).startswith('{') else json_match.group(0))
            articles = []
            items = data.get("result", {}).get("cmsArticle", {}).get("data", [])
            for item in items[:limit]:
                articles.append({
                    "title": item.get("title", ""),
                    "content": item.get("content", item.get("summary", "")),
                    "time": item.get("date", ""),
                    "source": item.get("source", "东方财富"),
                })
            return articles
        except Exception as e:
            print(f"[UsNewsSentiment] 获取美股新闻失败: {e}")
            return []

    def fetch_us_market_news(self, limit: int = 20) -> List[Dict]:
        """
        获取美股市场整体新闻。

        东方财富全球频道 column=358
        """
        url = (
            "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?"
            f"columns=358&pageIndex=1&pageSize={limit}&sort=default&"
        )
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.eastmoney.com/",
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            news_list = data.get("data", {}).get("list", [])
            return [
                {"title": n.get("title", ""), "content": n.get("content", ""),
                 "time": n.get("showTime", ""), "source": "东方财富"}
                for n in news_list[:limit]
            ]
        except Exception as e:
            print(f"[UsNewsSentiment] 获取市场新闻失败: {e}")
            return []

    def analyze(self, news_list: List[Dict]) -> Dict:
        """
        分析英语新闻列表的情感。

        Returns:
            {"score": float, "label": str, "positive_count": int,
             "negative_count": int, "total": int, "keywords": List[str]}
        """
        if not news_list:
            return {"score": 0.0, "label": "中性", "positive_count": 0,
                    "negative_count": 0, "total": 0, "keywords": []}

        pos_count = 0
        neg_count = 0
        total_score = 0.0
        all_keywords = []

        for news in news_list:
            text = (news.get("title", "") + " " + news.get("content", ""))[:500].lower()

            score = 0.0
            for kw in EN_STRONG_POSITIVE:
                if kw in text:
                    score += 2.0
                    all_keywords.append(kw)
            for kw in EN_POSITIVE_KEYWORDS:
                if kw in text:
                    score += 0.5
                    all_keywords.append(kw)
            for kw in EN_STRONG_NEGATIVE:
                if kw in text:
                    score -= 2.0
                    all_keywords.append(kw)
            for kw in EN_NEGATIVE_KEYWORDS:
                if kw in text:
                    score -= 0.5
                    all_keywords.append(kw)

            total_score += max(-3, min(3, score))
            if score > 0.5:
                pos_count += 1
            elif score < -0.5:
                neg_count += 1

        n = len(news_list)
        avg_score = total_score / n * 33 if n > 0 else 0

        label = "positive" if avg_score > 15 else ("negative" if avg_score < -15 else "neutral")

        return {
            "score": round(avg_score, 1),
            "label": label,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "total": n,
            "keywords": list(set(all_keywords))[:10],
        }


def get_vix_sentiment() -> Dict:
    """
    从 VIX 指数推断市场恐慌程度。

    VIX < 15: 极度乐观
    VIX 15-20: 乐观
    VIX 20-25: 中性
    VIX 25-30: 恐慌
    VIX > 30: 极度恐慌
    """
    try:
        import urllib.request, ssl, re
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = "https://qt.gtimg.cn/q=usVIX"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}
        req = urllib.request.Request(url, headers=headers)
        raw = urllib.request.urlopen(req, timeout=8, context=ctx).read().decode("gbk")
        fields = raw.split("~")
        vix = float(fields[3]) if len(fields) > 3 else 20

        if vix < 15:
            label, score = "极度乐观", 80
        elif vix < 20:
            label, score = "乐观", 60
        elif vix < 25:
            label, score = "中性", 40
        elif vix < 30:
            label, score = "恐慌", 20
        else:
            label, score = "极度恐慌", 5

        return {"vix": vix, "fear_greed": score, "label": label}
    except Exception:
        return {"vix": None, "fear_greed": 50, "label": "未知"}
