# -*- coding: utf-8 -*-
"""v5.0.0 模块B：RSS 接线到舆情爬虫测试（离线 mock）"""

import json
from pathlib import Path

import pytest

from scripts.rss_feeds import RssFetcher, _parse_rss_xml, RssItem
from scripts.sentiment_crawler import SentimentCrawler, SentimentSourceLoader


RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>测试财经</title>
  <item><title>贵州茅台发布2026半年报</title><link>https://example.com/1</link>
    <description>业绩增长 30%</description><pubDate>Wed, 01 Aug 2026 10:00:00 GMT</pubDate>
    <guid>guid-1</guid></item>
  <item><title>无关新闻</title><link>https://example.com/2</link>
    <description>天气晴朗</description><pubDate>Wed, 01 Aug 2026 11:00:00 GMT</pubDate>
    <guid>guid-2</guid></item>
</channel></rss>"""

ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>测试Atom</title>
  <entry><title>宁德时代扩产</title><link href="https://example.com/a"/>
    <summary>投资 100 亿</summary><updated>2026-08-01T09:00:00Z</updated>
    <id>atom-1</id></entry>
</feed>"""


# ============================================================
# 1. RSS 解析器
# ============================================================

def test_parse_rss2():
    items = _parse_rss_xml(RSS_XML.encode("utf-8"), source_name="测试")
    assert len(items) == 2
    assert items[0].title == "贵州茅台发布2026半年报"
    assert items[0].link == "https://example.com/1"


def test_parse_atom():
    items = _parse_rss_xml(ATOM_XML.encode("utf-8"), source_name="atom")
    assert len(items) == 1
    assert items[0].title == "宁德时代扩产"
    assert items[0].link == "https://example.com/a"


def test_rss_fetcher_fetch_success(monkeypatch):
    class FakeResp:
        status_code = 200
        content = RSS_XML.encode("utf-8")

    monkeypatch.setattr("scripts.http_utils.http_get", lambda *a, **k: FakeResp())
    fetcher = RssFetcher()
    items = fetcher.fetch({"name": "测试", "url": "https://example.com/rss"})
    assert len(items) == 2
    assert items[0].guid == "guid-1"


def test_rss_fetcher_fetch_none_returns_empty(monkeypatch):
    monkeypatch.setattr("scripts.http_utils.http_get", lambda *a, **k: None)
    fetcher = RssFetcher()
    assert fetcher.fetch({"name": "x", "url": "https://x/rss"}) == []


def test_rss_fetcher_bad_status_returns_empty(monkeypatch):
    class FakeResp:
        status_code = 403
        content = b""

    monkeypatch.setattr("scripts.http_utils.http_get", lambda *a, **k: FakeResp())
    fetcher = RssFetcher(max_retries=0)
    assert fetcher.fetch({"name": "x", "url": "https://x/rss"}) == []


# ============================================================
# 2. SentimentSourceLoader.sources_with_rss
# ============================================================

def test_sources_with_rss():
    loader = SentimentSourceLoader()
    with_rss = loader.sources_with_rss()
    # v6.0.0 商业媒体源（FT中文网/CNBC 等配置了 RSS）
    assert len(with_rss) >= 2, f"非空 RSS 站点过少: {len(with_rss)}"
    # 所有返回项都有非空 rss_feeds
    for s in with_rss:
        assert s.get("rss_feeds")


# ============================================================
# 3. SentimentCrawler._query_source 的 RSS 分支
# ============================================================

def _fake_source(name="东方财富", rss=None):
    return {"name": name, "category": "authoritative",
            "search_urls": [], "rss_feeds": rss or ["https://example.com/rss"],
            "credibility": 10, "language": "zh", "tags": []}


def test_query_source_uses_rss(monkeypatch):
    """配置了 rss_feeds 的源走 RSS 分支产出文章"""
    crawler = SentimentCrawler(use_rss=True)

    class FakeFetcher:
        def fetch(self, feed):
            return [RssItem(title="贵州茅台业绩增长", link="https://example.com/1",
                            description="增 30%", pub_date="2026-08-01")]

    crawler._rss_fetcher = FakeFetcher()
    crawler._time_up = lambda: False

    arts = list(crawler._query_source(
        _fake_source(), "贵州茅台", "贵州茅台", "listed_company", "上市公司",
        cutoff_time=None))
    assert len(arts) == 1
    assert arts[0].title == "贵州茅台业绩增长"


def test_query_source_rss_filters_by_keyword(monkeypatch):
    """RSS 条目不含关键词时被过滤"""
    crawler = SentimentCrawler(use_rss=True)

    class FakeFetcher:
        def fetch(self, feed):
            return [RssItem(title="无关新闻", link="https://example.com/x",
                            description="天气", pub_date="2026-08-01")]

    crawler._rss_fetcher = FakeFetcher()
    crawler._time_up = lambda: False
    arts = list(crawler._query_source(
        _fake_source(), "贵州茅台", "贵州茅台", "listed_company", "上市公司",
        cutoff_time=None))
    assert arts == []


def test_query_source_rss_disabled(monkeypatch):
    """use_rss=False 时不走 RSS 分支"""
    crawler = SentimentCrawler(use_rss=False)
    called = {"n": 0}

    class FakeFetcher:
        def fetch(self, feed):
            called["n"] += 1
            return []

    crawler._rss_fetcher = FakeFetcher()
    crawler._time_up = lambda: False
    list(crawler._query_source(_fake_source(), "贵州茅台", "贵州茅台", "x", "y", None))
    assert called["n"] == 0


def test_query_source_rss_fetch_exception_safe(monkeypatch):
    """RSS 抓取抛异常时跳过不崩"""
    crawler = SentimentCrawler(use_rss=True)

    class BoomFetcher:
        def fetch(self, feed):
            raise RuntimeError("rss down")

    crawler._rss_fetcher = BoomFetcher()
    crawler._time_up = lambda: False
    arts = list(crawler._query_source(_fake_source(), "贵州茅台", "贵州茅台", "x", "y", None))
    assert arts == []


def test_crawl_sentiment_accepts_use_rss():
    from scripts.sentiment_crawler import crawl_sentiment
    # 仅验证签名可传 use_rss 不破坏（dry_run 不发网络）
    snap = crawl_sentiment(targets=["贵州茅台"], dry_run=True, use_rss=True, max_articles=5)
    assert snap is not None
    assert snap.is_plan or not snap.articles
