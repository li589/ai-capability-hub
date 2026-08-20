#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻数据获取
News Data Fetching
"""

import re
import json
import time
from typing import Dict, List, Optional

try:
    from crawl_utils import safe_request
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False


class NewsData:
    """
    新闻数据获取

    数据来源：东方财富、同花顺
    """

    def __init__(self):
        self.positive_keywords = [
            "涨停", "大涨", "暴涨", "净流入", "业绩预增", "政策利好",
            "回购", "增持", "上调评级", "突破", "创新高", "国产替代",
            "中标", "订单", "合作", "扩张", "超预期", "大幅增长"
        ]
        self.negative_keywords = [
            "跌停", "大跌", "暴跌", "净流出", "业绩下滑", "被调查",
            "被处罚", "减持", "下调评级", "产能过剩", "黑天鹅",
            "诉讼", "亏损", "债务危机", "商誉减值", "大幅减少"
        ]

    def fetch_stock_news(self, code: str, limit: int = 20) -> List[Dict]:
        """
        获取个股新闻

        Args:
            code: 股票代码
            limit: 获取数量

        Returns:
            List[Dict]: 新闻列表
        """
        import urllib.parse
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
                    "area": "",
                    "time": "",
                    "titleLenght": "32"
                }
            }
        }, ensure_ascii=False).replace(" ", "")
        encoded = urllib.parse.quote(param, safe="")
        url = f"https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param={encoded}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.eastmoney.com/"
        }

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, headers=headers, timeout=8)
                if isinstance(raw, tuple):
                    raw = raw[0]
            else:
                import urllib.request
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")

            # 解析JSONP: jQuery(...)包裹的JSON
            m = re.search(r'jQuery\((.+)\)[;]?$', raw.strip())
            if not m:
                return []
            data = json.loads(m.group(1))
            articles = data.get("result", {}).get("cmsArticle", [])

            result = []
            for a in articles:
                result.append({
                    "title": a.get("title", ""),
                    "content": a.get("content", "") or a.get("title", ""),
                    "public_date": a.get("time", ""),
                    "type": a.get("type", ""),
                    "source": "东方财富"
                })

            return result

        except Exception as e:
            print(f"[NewsData] 获取新闻失败: {e}")
            return []

    def analyze_news_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        分析新闻情感

        Args:
            news_list: 新闻列表

        Returns:
            Dict: 情感分析结果
        """
        if not news_list:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "overall": "中性",
                "score": 0
            }

        positive = 0
        negative = 0
        neutral = 0

        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            text = title + " " + content

            score = 0
            for kw in self.positive_keywords:
                if kw in text:
                    score += 1
            for kw in self.negative_keywords:
                if kw in text:
                    score -= 1

            if score > 0:
                positive += 1
            elif score < 0:
                negative += 1
            else:
                neutral += 1

        total = len(news_list)
        net = positive - negative

        # 情感评分
        sentiment_score = (net / total) * 100 if total > 0 else 0

        # 整体判断
        if positive > negative * 2:
            overall = "偏利好"
        elif negative > positive * 2:
            overall = "偏利空"
        else:
            overall = "中性"

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "overall": overall,
            "score": round(sentiment_score, 1)
        }

    def get_market_digest(self) -> Dict:
        """
        获取市场摘要新闻

        Returns:
            Dict: 市场摘要
        """
        # 使用东方财富市场新闻API
        url = "https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param=%7B%22uid%22%3A%22%22%2C%22keyword%22%3A%22%E5%A4%A7%E7%9B%86%22%2C%22type%22%3A%5B%22cmsArticle%22%5D%2C%22client%22%3A%22web%22%2C%22clientVersion%22%3A%22curr%22%2C%22clientType%22%3A%22web%22%2C%22param%22%3A%7B%22cmsArticle%22%3A%7B%22searchScope%22%3A%22default%22%2C%22sort%22%3A%22default%22%2C%22pageIndex%22%3A1%2C%22pageSize%22%3A10%2C%22preTag%22%3A%22%22%2C%22postTag%22%3A%22%22%2C%22area%22%3A%22%22%2C%22time%22%3A%22%22%2C%22titleLenght%22%3A%2232%22%7D%7D%7D"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.eastmoney.com/"
        }

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, headers=headers, timeout=8)
                if isinstance(raw, tuple):
                    raw = raw[0]
            else:
                import urllib.request
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")

            # 解析JSONP
            m = re.search(r'\((\{.*\})\)', raw, re.S)
            if m:
                data = json.loads(m.group(1))
                items = data.get("result", {}).get("data", [])
                return {
                    "news": [{"title": i.get("title", ""), "time": i.get("time", "")} for i in items[:10]]
                }
        except Exception as e:
            print(f"[NewsData] 获取市场摘要失败: {e}")

        return {"news": []}