# -*- coding: utf-8 -*-
"""v5.0.0 模块C：浏览器增强测试（离线 mock，不真实启动 Playwright）"""

import pytest

import scripts.browser_scraper as bs_mod
from scripts.browser_scraper import (
    BrowserScraper, _should_block_url, _get_browser_scraper, release_browser,
    AD_BLOCK_DOMAINS,
)


# ============================================================
# 1. 广告拦截判定（纯逻辑）
# ============================================================

def test_should_block_ad_image():
    assert _should_block_url("https://ad.doubleclick.net/banner.jpg", "image") is True


def test_should_block_baidu_track():
    assert _should_block_url("https://hm.baidu.com/hm.js?x=1", "script") is False  # script 不拦
    assert _should_block_url("https://hm.baidu.com/hm.js?x=1", "image") is True


def test_should_block_not_block_regular():
    assert _should_block_url("https://eastmoney.com/pic.png", "image") is False
    assert _should_block_url("https://example.com/article.html", "document") is False


def test_should_block_small_resources_kept():
    # 非 image/media/font 类型（脚本/样式）不拦截，避免破坏页面
    assert _should_block_url("https://doubleclick.net/x.js", "script") is False
    assert _should_block_url("https://doubleclick.net/x.css", "stylesheet") is False


def test_ad_block_domains_nonempty():
    assert len(AD_BLOCK_DOMAINS) >= 8


# ============================================================
# 2. proxy 解析（静态方法）
# ============================================================

def test_resolve_proxy_string():
    assert BrowserScraper._resolve_proxy("http://127.0.0.1:8080") == {"server": "http://127.0.0.1:8080"}


def test_resolve_proxy_socks():
    assert BrowserScraper._resolve_proxy("socks5://1.2.3.4:1080") == {"server": "socks5://1.2.3.4:1080"}


def test_resolve_proxy_dict():
    assert BrowserScraper._resolve_proxy({"server": "http://x", "username": "u"}) == \
        {"server": "http://x", "username": "u"}


# ============================================================
# 3. 新参数（实例化不启动浏览器）
# ============================================================

def test_init_accepts_new_params():
    if not bs_mod.PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright 不可用")
    bs = BrowserScraper(headless=True, proxy="http://127.0.0.1:8080", ad_block=False, channel="chromium")
    assert bs.proxy == "http://127.0.0.1:8080"
    assert bs.ad_block is False
    assert bs.channel == "chromium"


def test_init_default_params():
    if not bs_mod.PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright 不可用")
    bs = BrowserScraper(headless=True)
    assert bs.proxy is None
    assert bs.ad_block is True
    assert bs.channel == "chromium"


# ============================================================
# 4. extract_many / _with_retry
# ============================================================

def test_extract_many_empty():
    bs = object.__new__(BrowserScraper)
    bs.timeout_ms = 30000
    assert bs.extract_many([]) == []


def test_extract_many_playwright_missing(monkeypatch):
    monkeypatch.setattr(bs_mod, "PLAYWRIGHT_AVAILABLE", False)
    bs = object.__new__(BrowserScraper)
    bs.timeout_ms = 30000
    out = bs.extract_many(["https://a.com/1", "https://b.com/2"])
    assert out == [("https://a.com/1", None), ("https://b.com/2", None)]


def test_with_retry_success():
    if not bs_mod.PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright 不可用")
    bs = BrowserScraper(headless=True)
    assert bs._with_retry(lambda: 42, retries=2) == 42


def test_with_retry_failure(monkeypatch):
    if not bs_mod.PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright 不可用")
    monkeypatch.setattr(bs_mod.time, "sleep", lambda *a, **k: None)
    bs = BrowserScraper(headless=True)

    def _boom():
        raise ValueError("x")

    assert bs._with_retry(_boom, retries=1) is None


# ============================================================
# 5. 进程级单例
# ============================================================

def test_singleton_none_when_unavailable(monkeypatch):
    monkeypatch.setattr(bs_mod, "PLAYWRIGHT_AVAILABLE", False)
    assert _get_browser_scraper(headless=True) is None


def test_release_browser_safe():
    release_browser()  # 不应抛异常


def test_singleton_idempotent_release(monkeypatch):
    """连续 release 幂等"""
    release_browser()
    release_browser()


# ============================================================
# 6. 软封禁检测（sentiment_crawler 接线）
# ============================================================

def test_is_soft_blocked_detects_captcha():
    from scripts.sentiment_crawler import SentimentCrawler
    c = SentimentCrawler()
    html = "<html><body>访问频率过高，请稍后再试，请输入验证码</body></html>"
    assert c._is_soft_blocked(html) is True


def test_is_soft_blocked_false_for_normal():
    from scripts.sentiment_crawler import SentimentCrawler
    c = SentimentCrawler()
    assert c._is_soft_blocked("<html>正常新闻内容</html>") is False


def test_is_soft_blocked_empty():
    from scripts.sentiment_crawler import SentimentCrawler
    c = SentimentCrawler()
    assert c._is_soft_blocked("") is False
