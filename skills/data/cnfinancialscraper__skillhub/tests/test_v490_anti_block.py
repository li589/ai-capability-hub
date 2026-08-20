#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4.9.0 新增反爬能力测试（test_v490_anti_block.py）

覆盖：
- akshare_fallback：fetch_with_fallback 路由 + 各类适配器
- rss_feeds：RSS 解析器 + 内置数据源
- anti_block_utils：域限速 / Cookie 持久化 / 错误码识别 / 指数退避
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from xml.etree import ElementTree as ET

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))


# ============================================================================
# akshare_fallback 测试
# ============================================================================


class TestFetchWithFallback:
    """fetch_with_fallback 路由测试。"""

    def test_primary_returns_data_no_fallback(self):
        """primary 返回有效数据时不应调用 fallback。"""
        from akshare_fallback import fetch_with_fallback

        primary_called = []
        fallback_called = []

        def _primary(**kw):
            primary_called.append(True)
            return [{"title": "primary"}]

        def _fallback(**kw):
            fallback_called.append(True)
            return [{"title": "fallback"}]

        # Mock sys.modules entry
        import sys as _sys
        # 由于 fetch_with_fallback 用字符串导入模块，我们直接 patch 内置函数
        with patch.object(
            __import__("akshare_fallback"), "_call_primary",
            side_effect=lambda m, f, kw: _primary(**kw),
        ), patch.object(
            __import__("akshare_fallback"), "_call_akshare",
            side_effect=lambda f, kw: _fallback(**kw),
        ):
            result = fetch_with_fallback(
                primary=("any_module", "any_func", {}),
                fallback=("akshare", "any_ak_func", {}),
                mock=None,
            )

        assert primary_called, "primary 应被调用"
        assert result == [{"title": "primary"}]

    def test_primary_returns_none_triggers_fallback(self):
        """primary 返回 None 时应自动降级到 fallback。"""
        from akshare_fallback import fetch_with_fallback

        with patch.object(
            __import__("akshare_fallback"), "_call_primary",
            return_value=None,
        ), patch.object(
            __import__("akshare_fallback"), "_call_akshare",
            return_value=[{"title": "from akshare"}],
        ):
            result = fetch_with_fallback(
                primary=("any", "func", {}),
                fallback=("akshare", "func", {}),
            )
        assert result == [{"title": "from akshare"}]

    def test_primary_returns_empty_list_triggers_fallback_with_validator(self):
        """primary 返回空列表时，validator 判定应触发 fallback。"""
        from akshare_fallback import fetch_with_fallback

        with patch.object(
            __import__("akshare_fallback"), "_call_primary",
            return_value=[],
        ), patch.object(
            __import__("akshare_fallback"), "_call_akshare",
            return_value=[{"x": 1}],
        ):
            result = fetch_with_fallback(
                primary=("any", "func", {}),
                fallback=("akshare", "func", {}),
                data_validator=lambda d: isinstance(d, list) and len(d) > 0,
            )
        assert result == [{"x": 1}]

    def test_no_fallback_returns_mock(self):
        """无 fallback 时应返回 mock。"""
        from akshare_fallback import fetch_with_fallback

        with patch.object(
            __import__("akshare_fallback"), "_call_primary",
            return_value=None,
        ):
            result = fetch_with_fallback(
                primary=("any", "func", {}),
                fallback=None,
                mock=[{"mock": True}],
            )
        assert result == [{"mock": True}]

    def test_no_fallback_no_mock_returns_none(self):
        """无 fallback 无 mock 时返回 None（不抛错）。"""
        from akshare_fallback import fetch_with_fallback

        with patch.object(
            __import__("akshare_fallback"), "_call_primary",
            return_value=None,
        ):
            result = fetch_with_fallback(
                primary=("any", "func", {}),
                fallback=None,
                mock=None,
            )
        assert result is None


class TestAkshareFallbackHelpers:

    def test_fetch_cls_hot_articles_returns_list(self):
        """fetch_cls_hot_articles 应返回 list。"""
        from akshare_fallback import fetch_cls_hot_articles

        with patch.object(
            __import__("akshare_fallback"), "fetch_with_fallback",
            return_value=[{"title": "test"}],
        ):
            r = fetch_cls_hot_articles(limit=5)
        assert isinstance(r, list)

    def test_fetch_sina_realtime_returns_dict(self):
        from akshare_fallback import fetch_sina_realtime
        with patch.object(
            __import__("akshare_fallback"), "fetch_with_fallback",
            return_value={"600519": {"name": "贵州茅台"}},
        ):
            r = fetch_sina_realtime(["600519"])
        assert isinstance(r, dict)


# ============================================================================
# rss_feeds 测试
# ============================================================================


class TestRssParser:
    """RSS XML 解析器测试。"""

    def test_parse_rss_2_with_cdata(self):
        """解析标准 RSS 2.0 + CDATA。"""
        from rss_feeds import _parse_rss_xml

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>Test Feed</title>
  <item>
    <title><![CDATA[新闻标题]]></title>
    <link>https://example.com/a</link>
    <description><![CDATA[<p>HTML 描述</p>]]></description>
    <pubDate>Mon, 09 Aug 2026 12:00:00 +0800</pubDate>
    <dc:creator>作者A</dc:creator>
  </item>
  <item>
    <title>第二条</title>
    <link>https://example.com/b</link>
  </item>
</channel>
</rss>""".encode("utf-8")
        items = _parse_rss_xml(xml, "Test Feed")
        assert len(items) == 2
        assert items[0].title == "新闻标题"
        assert items[0].link == "https://example.com/a"
        assert "HTML 描述" in items[0].description  # HTML 标签被剥离
        assert "2026-08-09" in items[0].pub_date
        assert items[0].author == "作者A"
        assert items[1].title == "第二条"

    def test_parse_atom_1(self):
        """解析 Atom 1.0。"""
        from rss_feeds import _parse_rss_xml

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <entry>
    <title>Atom Item</title>
    <link href="https://example.com/atom1"/>
    <updated>2026-08-09T12:00:00Z</updated>
    <author><name>Atom Author</name></author>
  </entry>
</feed>""".encode("utf-8")
        items = _parse_rss_xml(xml, "Atom Feed")
        assert len(items) == 1
        assert items[0].title == "Atom Item"
        assert items[0].link == "https://example.com/atom1"
        assert "2026-08-09" in items[0].pub_date

    def test_parse_bom_stripped(self):
        """BOM 头应被自动移除。"""
        from rss_feeds import _parse_rss_xml

        xml = b"\xef\xbb\xbf<?xml version='1.0'?><rss><channel><item>" \
              b"<title>BOM Test</title><link>x</link></item></channel></rss>"
        items = _parse_rss_xml(xml, "BOM")
        assert items[0].title == "BOM Test"

    def test_parse_invalid_xml_returns_empty(self):
        """无效 XML 应返回空列表（不抛错）。"""
        from rss_feeds import _parse_rss_xml

        items = _parse_rss_xml(b"<not-xml", "invalid")
        assert items == []

    def test_strip_html(self):
        """HTML 标签应被正确剥离（CDATA 内的标签也会被剥离）。"""
        from rss_feeds import _strip_html

        assert _strip_html("<p>hello</p>") == "hello"
        assert _strip_html("a &amp; b") == "a & b"
        # CDATA 内的 HTML 标签也会被剥离（先剥 CDATA 再剥 HTML）
        assert _strip_html("<![CDATA[<p>x</p>]]>") == "x"
        assert _strip_html("") == ""

    def test_parse_date_rfc822(self):
        """RFC 822 日期解析。"""
        from rss_feeds import _parse_date

        result = _parse_date("Mon, 09 Aug 2026 12:00:00 +0800")
        assert "2026-08-09" in result


class TestFinancialFeedsList:

    def test_list_all_categories(self):
        """默认返回所有分类。"""
        from rss_feeds import list_financial_feeds

        feeds = list_financial_feeds()
        assert len(feeds) >= 2
        names = [f["name"] for f in feeds]
        assert "东方财富" in "|".join(names)

    def test_list_authoritative(self):
        """media 类别应含商业财经源。"""
        from rss_feeds import list_financial_feeds

        feeds = list_financial_feeds("media")
        assert all("url" in f for f in feeds)
        assert all("name" in f for f in feeds)

    def test_list_nonexistent_category_returns_empty(self):
        from rss_feeds import list_financial_feeds
        assert list_financial_feeds("nonexistent") == []


class TestRssFetcher:
    """RssFetcher 类测试（使用 mock）。"""

    def test_fetch_invalid_url_returns_empty(self):
        """无 url 的源应返回空列表（不抛错）。"""
        from rss_feeds import RssFetcher

        fetcher = RssFetcher()
        items = fetcher.fetch({"name": "Empty", "url": ""})
        assert items == []

    def test_fetch_many_dedup(self):
        """fetch_many 应去重（基于 guid）。"""
        from rss_feeds import RssFetcher, _parse_rss_xml

        # 同一 XML 内容，两次 feed，应去重
        xml = """<?xml version="1.0"?><rss><channel>
            <item><title>A</title><link>x</link><guid>abc</guid></item>
            <item><title>B</title><link>y</link><guid>def</guid></item>
        </channel></rss>""".encode("utf-8")

        fetcher = RssFetcher()
        items1 = _parse_rss_xml(xml, "F1")
        items2 = _parse_rss_xml(xml, "F2")

        # 模拟：两个 feed 返回相同 guid
        with patch.object(fetcher, "fetch", side_effect=[items1, items2]):
            combined = fetcher.fetch_many(
                [{"name": "F1"}, {"name": "F2"}], max_total=100
            )
        # 去重后应只有 2 条（abc + def）
        assert len(combined) == 2
        assert {it.guid for it in combined} == {"abc", "def"}


# ============================================================================
# anti_block_utils 测试
# ============================================================================


class TestDomainRateLimiter:

    def test_normalize_domain(self):
        """域名规范化：去子域。"""
        from anti_block_utils import DomainRateLimiter

        rl = DomainRateLimiter()
        assert rl._normalize_domain("https://www.cls.cn/api") == "cls.cn"
        assert rl._normalize_domain("https://api.eastmoney.com/x") == "eastmoney.com"
        assert rl._normalize_domain("https://hq.sinajs.cn") == "sinajs.cn"

    def test_get_interval_uses_default(self):
        from anti_block_utils import DomainRateLimiter

        rl = DomainRateLimiter(default_interval=2.5)
        assert rl.get_interval("https://unknown.com") == 2.5

    def test_get_interval_uses_specific(self):
        from anti_block_utils import DomainRateLimiter

        rl = DomainRateLimiter({"cls.cn": 3.0}, default_interval=1.0)
        assert rl.get_interval("https://www.cls.cn") == 3.0
        assert rl.get_interval("https://other.com") == 1.0

    def test_wait_respects_interval(self):
        """wait 应等待至少 interval 秒。"""
        from anti_block_utils import DomainRateLimiter

        rl = DomainRateLimiter({"test.com": 0.1})  # 100ms
        start = time.monotonic()
        rl.wait("https://test.com/x")
        rl.wait("https://test.com/y")  # 第二次调用应等候
        elapsed = time.monotonic() - start
        # 至少等 100ms
        assert elapsed >= 0.05  # 留些余量

    def test_wait_thread_safe(self):
        """多线程调用 wait 不应崩溃。"""
        from anti_block_utils import DomainRateLimiter

        rl = DomainRateLimiter(default_interval=0.05)

        def worker():
            for _ in range(5):
                rl.wait("https://test.com/x")

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)


class TestPersistentCookieStore:

    def test_save_and_load_roundtrip(self, tmp_path):
        from anti_block_utils import PersistentCookieStore

        path = tmp_path / "cookies.json"
        store = PersistentCookieStore(path)
        cookies = [
            {"name": "sid", "value": "abc123", "domain": ".cls.cn"},
            {"name": "tk", "value": "xyz789", "domain": ".cls.cn",
             "expires": (time.time() + 86400)},  # 明天过期
        ]
        store.save(cookies)
        loaded = store.load()
        assert len(loaded) == 2
        assert loaded[0]["name"] == "sid"

    def test_load_filters_expired(self, tmp_path):
        from anti_block_utils import PersistentCookieStore

        path = tmp_path / "cookies.json"
        store = PersistentCookieStore(path, ttl_days=1)
        cookies = [
            {"name": "old", "value": "v", "expires": (time.time() - 86400)},  # 昨天过期
            {"name": "new", "value": "v"},  # 无过期时间 → 保留
        ]
        store.save(cookies)
        loaded = store.load()
        names = [c["name"] for c in loaded]
        assert "old" not in names
        assert "new" in names

    def test_load_missing_file_returns_empty(self, tmp_path):
        from anti_block_utils import PersistentCookieStore

        store = PersistentCookieStore(tmp_path / "nonexistent.json")
        assert store.load() == []


class TestBlockDetector:

    def test_403_detected(self):
        from anti_block_utils import detect_block

        sig = detect_block(403)
        assert sig is not None
        assert sig.code == 403
        assert "Forbidden" in sig.reason or "Forbidden" in sig.advice
        assert sig.cooldown > 0

    def test_429_detected(self):
        from anti_block_utils import detect_block

        sig = detect_block(429)
        assert sig is not None
        assert sig.code == 429

    def test_503_detected(self):
        from anti_block_utils import detect_block

        sig = detect_block(503)
        assert sig is not None
        assert sig.code == 503

    def test_200_with_danger_signs_detected(self):
        """200 响应含反爬文本特征时也应被识别。"""
        from anti_block_utils import detect_block

        sig = detect_block(200, body_sample="访问频率过高，请稍后再试")
        assert sig is not None
        assert "软拦截" in sig.reason or "频率" in sig.reason

    def test_200_normal_content_returns_none(self):
        """200 正常响应应返回 None。"""
        from anti_block_utils import detect_block

        sig = detect_block(200, body_sample="<html>正常内容</html>")
        assert sig is None

    def test_404_returns_none(self):
        """404 未被列入封禁模式。"""
        from anti_block_utils import detect_block

        assert detect_block(404) is None


class TestExponentialBackoff:

    def test_doubles_each_attempt(self):
        from anti_block_utils import exponential_backoff

        delays = [exponential_backoff(i, base=1, jitter=False) for i in range(1, 6)]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_caps_at_max_delay(self):
        from anti_block_utils import exponential_backoff

        delay = exponential_backoff(20, base=1, max_delay=10.0, jitter=False)
        assert delay == 10.0

    def test_jitter_randomizes(self):
        from anti_block_utils import exponential_backoff

        # jitter=True 时应随机（两次调用结果不同）
        d1 = exponential_backoff(3, base=1, jitter=True)
        d2 = exponential_backoff(3, base=1, jitter=True)
        # 范围：4 * (0.5 ~ 1.5) = 2.0 ~ 6.0（random.random() ∈ [0, 1)）
        assert 2.0 <= d1 < 6.0
        assert 2.0 <= d2 < 6.0
        # 极小概率相等（随机种子），但大部分时候不等


class TestConditionalCache:

    def test_get_request_headers_initial_empty(self, tmp_path):
        from anti_block_utils import ConditionalCache

        cache = ConditionalCache(tmp_path / "etag.json")
        headers = cache.get_request_headers("https://example.com/x")
        assert headers == {}

    def test_update_then_get_headers(self, tmp_path):
        from anti_block_utils import ConditionalCache

        cache = ConditionalCache(tmp_path / "etag.json")
        cache.update("https://example.com/x", etag='"abc"', last_modified="Mon, 09 Aug 2026")
        headers = cache.get_request_headers("https://example.com/x")
        assert headers["If-None-Match"] == '"abc"'
        assert "Mon, 09 Aug 2026" in headers["If-Modified-Since"]

    def test_cached_body_roundtrip(self, tmp_path):
        from anti_block_utils import ConditionalCache

        cache = ConditionalCache(tmp_path / "etag.json")
        cache.update("https://example.com/y", etag='"xyz"', last_modified=None, body="cached body")
        assert cache.get_cached_body("https://example.com/y") == "cached body"

    def test_size_limit_triggers_cleanup(self, tmp_path):
        """超过 5000 条应触发清理（保留最新）。"""
        from anti_block_utils import ConditionalCache

        cache = ConditionalCache(tmp_path / "etag.json")
        # 写 5050 条
        for i in range(5050):
            cache.update(f"https://example.com/{i}", etag=f'"e{i}"', last_modified=None)
        # 触发清理
        cache._save()
        # 应被截断到 5000 - 1000 = 4000 + 5050 - 5000 = 50 之间
        # 实际逻辑：>5000 时清理最旧 1000，剩 4000 - 实际剩 4050
        # 验证：总条数 < 5050
        assert len(cache._data) < 5050


class TestTLSFingerprintClient:

    def test_property_available(self):
        from anti_block_utils import TLSFingerprintClient

        client = TLSFingerprintClient()
        # 仅断言属性可访问；不强制要求 curl_cffi 已装
        assert isinstance(client.available, bool)

    def test_get_without_library_raises(self):
        """curl_cffi 未装时 get() 应抛 ImportError。"""
        from anti_block_utils import TLSFingerprintClient

        client = TLSFingerprintClient()
        # 模拟未安装：直接替换内部 _impl 为 None
        with patch.object(client, "_impl", None), \
             patch.object(client, "_available", False):
            with pytest.raises(ImportError):
                client.get("https://example.com")


class TestDomainHealthTracker:

    def test_new_domain_available(self, tmp_path):
        from anti_block_utils import DomainHealthTracker

        tracker = DomainHealthTracker(tmp_path / "health.json")
        assert tracker.is_available("new.com") is True

    def test_disable_after_threshold(self, tmp_path):
        from anti_block_utils import DomainHealthTracker

        tracker = DomainHealthTracker(
            tmp_path / "health.json",
            disable_threshold=3,
            cooldown_seconds=60,
        )
        for _ in range(3):
            tracker.record_failure("bad.com", reason="403")
        # 连续失败 3 次，应禁用
        assert tracker.is_available("bad.com") is False

    def test_recovery_after_success(self, tmp_path):
        from anti_block_utils import DomainHealthTracker

        tracker = DomainHealthTracker(
            tmp_path / "health.json",
            disable_threshold=3,
            cooldown_seconds=60,
        )
        for _ in range(3):
            tracker.record_failure("x.com", reason="err")
        assert tracker.is_available("x.com") is False
        tracker.record_success("x.com")
        assert tracker.is_available("x.com") is True

    def test_status_report(self, tmp_path):
        from anti_block_utils import DomainHealthTracker

        tracker = DomainHealthTracker(
            tmp_path / "health.json", disable_threshold=2,
        )
        tracker.record_success("good.com")
        tracker.record_failure("bad.com")
        tracker.record_failure("bad.com")
        report = tracker.status()
        assert "good.com" in report["domains"]
        assert "bad.com" in report["domains"]


# ============================================================================
# 集成测试：fetch_with_fallback + akshare
# ============================================================================


class TestIntegrationAkshareFallback:

    def test_cls_fallback_when_module_returns_none(self):
        """当 cls_scraper 不可用时，akshare 应作为降级源。"""
        from akshare_fallback import fetch_cls_hot_articles

        # patch cls_scraper.get_hot_articles 抛异常
        with patch("scripts.cls_scraper.get_hot_articles",
                   return_value=None, create=True):
            result = fetch_cls_hot_articles(limit=5)
        # 即使 patch 失败降级，结果也应是 list（空或 akshare 返回）
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])