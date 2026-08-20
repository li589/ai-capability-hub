#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股新闻舆情 (v6.0.0)
=====================
港股市场新闻获取与情感分析。
数据源：东方财富全球频道（免费，国内直连）。
"""

import re
import json
import time
import urllib.request
import ssl
from typing import Dict, List, Optional

from .sentiment_keywords import (
    calc_text_sentiment, CN_POSITIVE_KEYWORDS, CN_NEGATIVE_KEYWORDS,
    HK_SPECIFIC_POSITIVE, HK_SPECIFIC_NEGATIVE,
)


class HkNewsSentiment:
    """
    港股新闻舆情分析。

    数据源:
      - 东方财富全球频道 column=362 (港股新闻)
      - 东方财富搜索 API (个股新闻)

    用法:
        hk = HkNewsSentiment()
        news = hk.fetch_hk_stock_news("00700")
        sentiment = hk.analyze(news)
    """

    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def fetch_hk_stock_news(self, code: str, limit: int = 15) -> List[Dict]:
        """
        获取港股个股新闻。

        Args:
            code: 港股代码，如 "00700"
            limit: 获取数量

        Returns:
            List[Dict]: 新闻列表，含 title/content/time/source
        """
        param = json.dumps({
            "uid": "",
            "keyword": f"hk{code}",
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

            # 解析 JSONP
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
                    "url": item.get("url", ""),
                })
            return articles
        except Exception as e:
            print(f"[HkNewsSentiment] 获取港股新闻失败: {e}")
            return []

    def fetch_hk_market_news(self, limit: int = 20) -> List[Dict]:
        """
        获取港股市场整体新闻。

        东方财富全球频道 column=362
        """
        url = (
            "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?"
            f"columns=362&pageIndex=1&pageSize={limit}&sort=default&"
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
            print(f"[HkNewsSentiment] 获取市场新闻失败: {e}")
            return []

    def analyze(self, news_list: List[Dict]) -> Dict:
        """
        分析新闻列表的情感倾向。

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
            text = (news.get("title", "") + " " + news.get("content", ""))[:500]
            # 使用中+港关键词
            score = 0.0
            for kw in CN_POSITIVE_KEYWORDS + HK_SPECIFIC_POSITIVE:
                if kw in text:
                    score += 1.0
                    all_keywords.append(kw)
            for kw in CN_NEGATIVE_KEYWORDS + HK_SPECIFIC_NEGATIVE:
                if kw in text:
                    score -= 1.0
                    all_keywords.append(kw)

            total_score += max(-3, min(3, score))
            if score > 0.5:
                pos_count += 1
            elif score < -0.5:
                neg_count += 1

        n = len(news_list)
        avg_score = total_score / n * 33 if n > 0 else 0

        label = "积极" if avg_score > 15 else ("消极" if avg_score < -15 else "中性")

        return {
            "score": round(avg_score, 1),
            "label": label,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "total": n,
            "keywords": list(set(all_keywords))[:10],
        }
