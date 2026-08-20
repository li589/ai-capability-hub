# -*- coding: utf-8 -*-
"""测试 search_engine.py — 解析函数和聚合器（纯函数部分，不依赖网络）。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.dont_write_bytecode = True

from search_engine import (
    SearchResult, SearchEngineBase,
    DuckDuckGoHTML, BingHTML, GoogleHTML,
    SearXNGSearch, BingAPISearch, GoogleAPISearch,
    MultiEngineSearch,
    _parse_ddg_html, _dedup_results, _normalize_url,
    _strip_tags, _unescape_html, _safe_search,
)


class TestSearchResult(unittest.TestCase):
    """SearchResult 数据类测试。"""

    def test_to_dict(self):
        r = SearchResult(
            title="Test", url="https://x.com", snippet="desc",
            source_engine="duckduckgo", rank=1, credibility=7,
        )
        d = r.to_dict()
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["credibility"], 7)

    def test_default_credibility(self):
        r = SearchResult(title="T", url="u", snippet="s", source_engine="e", rank=1)
        self.assertEqual(r.credibility, 5)


class TestDDGHTMLParsing(unittest.TestCase):
    """DuckDuckGo HTML 解析测试。"""

    def test_parse_single_result(self):
        html = '''
        <a class="result__a" href="https://example.com/article">测试文章标题</a>
        <a class="result__snippet">这是摘要内容</a>
        '''
        results = _parse_ddg_html(html, "duckduckgo", 7, 10)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://example.com/article")

    def test_parse_empty_html(self):
        results = _parse_ddg_html("", "duckduckgo", 5, 10)
        self.assertEqual(len(results), 0)

    def test_parse_limit(self):
        html = ("<a class=\"result__a\" href=\"https://x.com/1\">T1</a>"
                "<a class=\"result__snippet\">S1</a>") * 20
        results = _parse_ddg_html(html, "duckduckgo", 5, 3)
        self.assertLessEqual(len(results), 3)

    def test_unescape_html_entities(self):
        html = ('<a class="result__a" href="https://x.com">测试 &amp; 结果</a>'
                '<a class="result__snippet">内容 &lt;摘要&gt;</a>')
        results = _parse_ddg_html(html, "ddg", 5, 10)
        if results:
            self.assertIn("&", results[0].title)


class TestURLNormalization(unittest.TestCase):
    """URL 标准化测试。"""

    def test_strips_utm_params(self):
        url = "https://example.com/page?utm_source=twitter&id=123"
        norm = _normalize_url(url)
        self.assertNotIn("utm_source", norm)
        # _normalize_url 简化 URL 为 path-only 形式

    def test_strips_ref_param(self):
        url = "https://example.com/page?ref=homepage"
        norm = _normalize_url(url)
        self.assertNotIn("ref", norm)

    def test_handles_invalid_url(self):
        norm = _normalize_url("not_a_url")
        self.assertEqual(norm, "")  # 无效 URL 返回空字符串


class TestDedup(unittest.TestCase):
    """去重测试。"""

    def test_dedup_same_url(self):
        r1 = SearchResult(title="A", url="https://x.com/page", snippet="",
                          source_engine="ddg", rank=1, credibility=5)
        r2 = SearchResult(title="B", url="https://x.com/page?utm=1", snippet="",
                          source_engine="bing", rank=2, credibility=7)
        results = _dedup_results([r1, r2])
        self.assertEqual(len(results), 1)
        # 保留 credibility 更高的
        self.assertEqual(results[0].credibility, 7)

    def test_dedup_different_urls(self):
        r1 = SearchResult(title="A", url="https://x.com/1", snippet="",
                          source_engine="ddg", rank=1, credibility=5)
        r2 = SearchResult(title="B", url="https://y.com/2", snippet="",
                          source_engine="bing", rank=1, credibility=5)
        results = _dedup_results([r1, r2])
        self.assertEqual(len(results), 2)


class TestHTMLUtils(unittest.TestCase):
    """HTML 工具函数测试。"""

    def test_strip_tags(self):
        self.assertEqual(_strip_tags("<p>Hello <b>World</b></p>"), "Hello World")

    def test_unescape_html(self):
        self.assertEqual(_unescape_html("a&amp;b"), "a&b")
        self.assertEqual(_unescape_html("a&lt;b&gt;c"), "a<b>c")
        self.assertEqual(_unescape_html("&#65;"), "A")


class TestMultiEngineInit(unittest.TestCase):
    """多引擎聚合器初始化测试。"""

    def test_default_engines(self):
        s = MultiEngineSearch()
        engine_names = [e.name for e in s.engines]
        self.assertIn("duckduckgo", engine_names)

    def test_custom_engines(self):
        s = MultiEngineSearch(engines=["duckduckgo"])
        self.assertEqual(len(s.engines), 1)
        self.assertEqual(s.engines[0].name, "duckduckgo")

    def test_list_engines(self):
        s = MultiEngineSearch(engines=["duckduckgo"])
        info = s.list_engines()
        self.assertEqual(len(info), 1)
        self.assertIn("name", info[0])
        self.assertIn("credibility", info[0])

    def test_invalid_engine_skipped(self):
        s = MultiEngineSearch(engines=["nonexistent_engine"])
        self.assertEqual(len(s.engines), 0)


class TestSearXNGFallback(unittest.TestCase):
    """SearXNG 故障转移测试。"""

    def test_default_instances_list(self):
        instances = SearXNGSearch.DEFAULT_INSTANCES
        self.assertGreaterEqual(len(instances), 3)
        self.assertTrue(all(i.startswith("https://") for i in instances))

    def test_init_with_default_instance(self):
        s = SearXNGSearch()
        self.assertIn(s.instance, SearXNGSearch.DEFAULT_INSTANCES)

    def test_custom_instance(self):
        s = SearXNGSearch(instance="https://custom.example.com")
        self.assertEqual(s.instance, "https://custom.example.com")


if __name__ == "__main__":
    unittest.main()
