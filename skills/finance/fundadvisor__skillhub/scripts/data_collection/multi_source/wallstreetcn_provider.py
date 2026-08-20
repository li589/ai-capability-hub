#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""华尔街见闻数据源 (v6.0 新增)

7×24 全球电报 + 宏观文章，质量高于新浪/凤凰滚动。
接口: https://api-one-wscn.awtmt.com/apiv1/content/lives
免费、国内直连。
"""
from __future__ import annotations
import json
import urllib.request
from datetime import datetime
from typing import Dict, List
from .base import DataSource, SourceResponse

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://wallstreetcn.com/",
}


def _http_get(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


class WallstreetcnProvider(DataSource):
    """华尔街见闻源"""

    name = "华尔街见闻"
    capabilities = ["news", "macro"]

    def fetch_news(self, limit: int = 20) -> SourceResponse:
        try:
            url = (f"https://api-one-wscn.awtmt.com/apiv1/content/lives?"
                   f"channel=global-channel&limit={limit}&accept=livestream")
            text = _http_get(url, timeout=8)
            data = json.loads(text)
            items = data.get("data", {}).get("items", [])
            news = []
            for item in items:
                title = item.get("title", "") or item.get("content_text", "")[:40]
                if not title:
                    continue
                dtime = item.get("display_time", 0)
                news.append({
                    "title": title,
                    "content": (item.get("content", "") or "")[:200],
                    "time": datetime.fromtimestamp(dtime).strftime("%Y-%m-%d %H:%M") if dtime else "",
                    "url": item.get("uri", ""),
                    "source": "华尔街见闻",
                })
            if not news:
                return SourceResponse.fail(self.name, "华尔街见闻返回空")
            return SourceResponse.ok(self.name, news)
        except Exception as e:
            return SourceResponse.fail(self.name, f"华尔街见闻获取失败: {e}")

    def fetch_macro(self) -> SourceResponse:
        """华尔街见闻宏观频道文章（标题级，作为宏观叙事补充）"""
        try:
            url = ("https://api-one-wscn.awtmt.com/apiv1/content/articles?"
                   "channel=global-channel&limit=10")
            text = _http_get(url, timeout=8)
            data = json.loads(text)
            items = data.get("data", {}).get("items", [])
            articles = []
            for item in items[:10]:
                articles.append({
                    "title": item.get("title", ""),
                    "summary": (item.get("content", "") or "")[:150],
                    "time": datetime.fromtimestamp(
                        item.get("display_time", 0)).strftime("%Y-%m-%d") if item.get("display_time") else "",
                })
            if not articles:
                return SourceResponse.fail(self.name, "宏观文章返回空")
            return SourceResponse.ok(self.name, {"macro_articles": articles})
        except Exception as e:
            return SourceResponse.fail(self.name, f"宏观文章获取失败: {e}")


def main():
    print("=== 华尔街见闻测试 ===")
    p = WallstreetcnProvider()
    r = p.fetch_news(limit=10)
    print(f"available={r.available}, source={r.source}")
    if r.available:
        for n in r.data[:5]:
            print(f"  [{n['time']}] {n['title'][:50]}")


if __name__ == "__main__":
    main()
