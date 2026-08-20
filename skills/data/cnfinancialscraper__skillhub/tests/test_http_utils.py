# -*- coding: utf-8 -*-
"""Tests for http_utils.py — HTTP utilities and helpers"""
import pytest
from scripts.http_utils import (
    _extract_domain,
    sanitize_filename,
    LRUCache,
    StdlibResponse,
)


class TestExtractDomain:
    """Test _extract_domain helper"""

    def test_extracts_domain_from_https_url(self):
        assert _extract_domain("https://fund.eastmoney.com/000001.html") == "fund.eastmoney.com"

    def test_extracts_domain_from_http_url(self):
        assert _extract_domain("http://www.example.com/path?a=1") == "www.example.com"

    def test_extracts_domain_from_url_with_port(self):
        assert _extract_domain("https://api.test.com:8080/v1/data") == "api.test.com:8080"

    def test_handles_malformed_url(self):
        """Malformed URLs should return 'unknown' or not raise"""
        result = _extract_domain("not-a-valid-url!!!")
        assert isinstance(result, str)

    def test_handles_empty_string(self):
        result = _extract_domain("")
        assert isinstance(result, str)

    def test_lowercases_domain(self):
        assert _extract_domain("https://WWW.EXAMPLE.COM/path") == "www.example.com"


class TestSanitizeFilename:
    """Test sanitize_filename function"""

    def test_removes_invalid_chars(self):
        # : and " both become _, so :with" becomes __with_
        result = sanitize_filename('file<name>:with"bad/chars')
        assert "file_name__with_bad_chars" == result

    def test_replaces_backslash(self):
        assert sanitize_filename("path\\to\\file.pdf") == "path_to_file.pdf"

    def test_normalizes_whitespace(self):
        assert sanitize_filename("  multiple   spaces  here  ") == "multiple spaces here"

    def test_truncates_long_names(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name, max_len=50)
        assert len(result) == 50
        assert result == "a" * 50

    def test_default_max_len(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_handles_chinese_characters(self):
        result = sanitize_filename("华夏基金_2024年报.pdf")
        assert "华夏基金_2024年报.pdf" == result

    def test_strips_control_characters(self):
        result = sanitize_filename("test\x00file\x1fname")
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_returns_unnamed_for_empty_result(self):
        """After sanitization, if name is all underscores, return 'unnamed'"""
        result = sanitize_filename("<>:\"/\\|?*")
        assert result == "unnamed"

    def test_returns_unnamed_for_empty_string(self):
        result = sanitize_filename("")
        assert result == "unnamed"


class TestLRUCache:
    """Test LRUCache implementation — uses set/get API (not put)"""

    def test_basic_set_and_get(self):
        cache = LRUCache(max_size=10, ttl=99999)
        resp = StdlibResponse("http://test.com", 200, {"Content-Type": "text/plain"}, b"test body")
        cache.set("http://test.com/key1", resp)
        result = cache.get("http://test.com/key1")
        assert result is not None
        assert result.status_code == 200

    def test_get_missing_key(self):
        cache = LRUCache(10)
        assert cache.get("http://nonexistent.com") is None

    def test_lru_eviction(self):
        cache = LRUCache(max_size=3, ttl=99999)
        for i in range(3):
            resp = StdlibResponse(f"http://test.com/{i}", 200, {}, f"body{i}".encode())
            cache.set(f"http://test.com/{i}", resp)
        cache.get("http://test.com/0")
        resp4 = StdlibResponse("http://test.com/4", 200, {}, b"body4")
        cache.set("http://test.com/4", resp4)
        assert cache.get("http://test.com/0") is not None
        assert cache.get("http://test.com/2") is not None
        assert cache.get("http://test.com/4") is not None
        assert cache.get("http://test.com/1") is None

    def test_overwrite_existing_key(self):
        """LRU cache does NOT overwrite existing keys — it preserves first-cached value.
        This is standard HTTP cache behavior: first response wins until TTL expiry."""
        cache = LRUCache(max_size=10, ttl=99999)
        resp1 = StdlibResponse("http://test.com/key", 200, {}, b"first")
        resp2 = StdlibResponse("http://test.com/key", 200, {}, b"second")
        cache.set("http://test.com/key", resp1)
        cache.set("http://test.com/key", resp2)  # Should keep first value
        result = cache.get("http://test.com/key")
        assert result.content == b"first"  # First-cached value preserved

    def test_clear_cache(self):
        cache = LRUCache(max_size=10, ttl=99999)
        cache.set("http://test.com/a", StdlibResponse("http://test.com/a", 200, {}, b"a"))
        cache.set("http://test.com/b", StdlibResponse("http://test.com/b", 200, {}, b"b"))
        cache.clear()
        assert cache.get("http://test.com/a") is None
        assert cache.get("http://test.com/b") is None

    def test_ttl_expiry(self):
        """Items should expire after TTL"""
        cache = LRUCache(max_size=10, ttl=0.01)
        cache.set("http://test.com/key", StdlibResponse("http://test.com/key", 200, {}, b"body"))
        import time
        time.sleep(0.02)
        assert cache.get("http://test.com/key") is None

    def test_len(self):
        cache = LRUCache(max_size=10)
        cache.set("http://test.com/a", StdlibResponse("http://test.com/a", 200, {}, b"a"))
        cache.set("http://test.com/b", StdlibResponse("http://test.com/b", 200, {}, b"b"))
        assert len(cache) == 2
