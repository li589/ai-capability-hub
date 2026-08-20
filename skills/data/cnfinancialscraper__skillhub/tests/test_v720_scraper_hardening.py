# -*- coding: utf-8 -*-
"""v7.2.0 爬取硬化测试 — bug 修复 + 软拦截检测 + Retry-After + URL 去重器

覆盖：
1. bug 修复：空 POST 退化为 GET / download_file 保存错误页 /
   raise_for_status 消息 / 熔断 sleep 持锁 / 裸域名 reset / 过期 cookie
2. 能力升级：http_get 软拦截检测接线、Retry-After 遵从、UrlDeduplicator
"""
import time

import pytest

import http_utils
from http_utils import (
    StdlibSession,
    StdlibResponse,
    HTTPError,
    download_file,
    http_get,
)
from anti_block_utils import (
    DomainRateLimiter,
    PersistentCookieStore,
    UrlDeduplicator,
    self_check,
)


# ─── 测试辅助 ──────────────────────────────────────────────────────────────


class _FakeRawResp:
    """模拟 opener.open 返回的原始响应"""

    def __init__(self, body=b"ok", code=200):
        self._body = body
        self._code = code
        self.headers = [("Content-Type", "text/plain")]

    def getcode(self):
        return self._code

    def read(self):
        return self._body

    def close(self):
        pass


class FakeSession:
    """按调用次序返回预设响应的假 session"""

    mobile = False

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, headers=None, timeout=30, **kw):
        self.calls += 1
        return self._responses[min(self.calls - 1, len(self._responses) - 1)]

    post = get


@pytest.fixture
def no_sleep(monkeypatch):
    """记录并跳过 http_utils 内的所有 sleep"""
    recorded = []
    monkeypatch.setattr(http_utils.time, "sleep", lambda s: recorded.append(s))
    return recorded


@pytest.fixture(autouse=True)
def _reset_limiter():
    """每个用例后清理自适应限流器测试域名状态"""
    yield
    limiter = http_utils._get_adaptive_limiter()
    for d in ("softblock-test.example", "retryafter-test.example",
              "blocked-test.example", "dl-test.example"):
        limiter.reset_domain(d)


def _resp(url, code=200, headers=None, body=b""):
    return StdlibResponse(url, code, headers or {}, body)


# ─── 1. bug 修复：空 body POST 不再退化为 GET ─────────────────────────────


class TestPostMethodFix:

    def test_empty_body_post_keeps_post_method(self):
        captured = {}
        s = StdlibSession()
        s._opener.open = lambda req, timeout=None: (
            captured.__setitem__("req", req) or _FakeRawResp()
        )
        s.post("http://example.com/api")
        assert captured["req"].get_method() == "POST"

    def test_json_body_post_keeps_post_method(self):
        captured = {}
        s = StdlibSession()
        s._opener.open = lambda req, timeout=None: (
            captured.__setitem__("req", req) or _FakeRawResp()
        )
        s.post("http://example.com/api", json_body={"k": 1})
        assert captured["req"].get_method() == "POST"
        assert captured["req"].data is not None

    def test_get_stays_get(self):
        captured = {}
        s = StdlibSession()
        s._opener.open = lambda req, timeout=None: (
            captured.__setitem__("req", req) or _FakeRawResp()
        )
        s.get("http://example.com/page")
        assert captured["req"].get_method() == "GET"


# ─── 2. bug 修复：download_file 不再保存错误页 ────────────────────────────


class TestDownloadFileFix:

    def test_error_response_not_saved(self, tmp_path):
        s = StdlibSession()
        s.get = lambda url, headers=None, timeout=60, **kw: _resp(
            url, 404, {}, b"<html>not found</html>")
        result = download_file("http://dl-test.example/a.pdf",
                               save_dir=str(tmp_path), session=s)
        assert result is None
        assert not any(tmp_path.iterdir()), "404 响应不应落盘"

    def test_ok_response_saved(self, tmp_path):
        s = StdlibSession()
        s.get = lambda url, headers=None, timeout=60, **kw: _resp(
            url, 200, {}, b"%PDF-1.4 fake")
        result = download_file("http://dl-test.example/a.pdf",
                               save_dir=str(tmp_path), session=s)
        assert result is not None and result.endswith("a.pdf")


# ─── 3. bug 修复：raise_for_status 消息含状态码 ───────────────────────────


class TestRaiseForStatusFix:

    def test_message_contains_code(self):
        resp = _resp("http://x.example/missing", 404, {}, b"")
        with pytest.raises(HTTPError) as ei:
            resp.raise_for_status()
        assert ei.value.code == 404
        assert "404" in ei.value.reason

    def test_ok_status_no_raise(self):
        _resp("http://x.example/ok", 200, {}, b"fine").raise_for_status()


# ─── 4. bug 修复：熔断 sleep 不再持有全局域名锁 ───────────────────────────


class TestRateLimitLockFix:

    def test_blocked_sleep_outside_lock(self, monkeypatch):
        limiter = http_utils._get_adaptive_limiter()
        domain = "blocked-test.example"
        for _ in range(3):  # 触发熔断（fail_threshold=3）
            limiter.report_failure(domain, 503)
        assert limiter.is_blocked(domain)

        lock_state_during_sleep = []

        def fake_sleep(s):
            lock_state_during_sleep.append(http_utils._domain_lock.locked())

        monkeypatch.setattr(http_utils.time, "sleep", fake_sleep)
        http_utils.rate_limit(0, f"https://{domain}/x")
        assert lock_state_during_sleep, "熔断应产生等待"
        assert all(held is False for held in lock_state_during_sleep), \
            "sleep 期间不应持有 _domain_lock"


# ─── 5. 升级：http_get 软拦截检测 ─────────────────────────────────────────


SOFT_BLOCK_HTML = "<html><body>请输入验证码，访问被拒绝</body></html>".encode("utf-8")
NORMAL_HTML = "<html><body>正常财经新闻内容</body></html>".encode("utf-8")


class TestSoftBlockDetection:

    def test_soft_block_triggers_retry_then_success(self, no_sleep):
        fs = FakeSession([
            _resp("u", 200, {"Content-Type": "text/html"}, SOFT_BLOCK_HTML),
            _resp("u", 200, {"Content-Type": "text/html"}, NORMAL_HTML),
        ])
        resp = http_get("http://softblock-test.example/news",
                        session=fs, use_cache=False, rate_limit_delay=0)
        assert resp is not None
        assert "正常财经新闻" in resp.text
        assert fs.calls == 2

    def test_soft_block_disabled_returns_page(self, no_sleep):
        fs = FakeSession([
            _resp("u", 200, {"Content-Type": "text/html"}, SOFT_BLOCK_HTML),
        ])
        resp = http_get("http://softblock-test.example/news",
                        session=fs, use_cache=False, rate_limit_delay=0,
                        detect_soft_block=False)
        assert resp is not None
        assert fs.calls == 1

    def test_all_retries_soft_blocked_returns_none(self, no_sleep):
        fs = FakeSession([
            _resp("u", 200, {"Content-Type": "text/html"}, SOFT_BLOCK_HTML),
        ])
        resp = http_get("http://softblock-test.example/news",
                        session=fs, use_cache=False, rate_limit_delay=0,
                        retries=2)
        assert resp is None
        assert fs.calls == 2

    def test_json_body_not_flagged(self, no_sleep):
        body = b'{"title": "market challenge ahead", "ok": true}'
        fs = FakeSession([_resp("u", 200, {"Content-Type": "application/json"}, body)])
        resp = http_get("http://softblock-test.example/api",
                        session=fs, use_cache=False, rate_limit_delay=0)
        assert resp is not None and fs.calls == 1

    def test_large_html_not_flagged(self, no_sleep):
        big = (b"<html><body>" + b"x" * 9000
               + "请输入验证码".encode("utf-8") + b"</body></html>")
        fs = FakeSession([_resp("u", 200, {"Content-Type": "text/html"}, big)])
        resp = http_get("http://softblock-test.example/big",
                        session=fs, use_cache=False, rate_limit_delay=0)
        assert resp is not None and fs.calls == 1


# ─── 6. 升级：Retry-After 遵从 ────────────────────────────────────────────


class TestRetryAfter:

    def test_retry_after_seconds_honored(self, no_sleep):
        fs = FakeSession([
            _resp("u", 429, {"Retry-After": "7"}, b"slow down"),
            _resp("u", 200, {}, b"ok now"),
        ])
        resp = http_get("http://retryafter-test.example/data",
                        session=fs, use_cache=False, rate_limit_delay=0)
        assert resp is not None and resp.text == "ok now"
        assert any(abs(w - 7.0) < 0.01 for w in no_sleep), \
            f"应等待 Retry-After 声明的 7s，实际 sleeps={no_sleep}"

    def test_retry_after_capped(self):
        resp = _resp("u", 429, {"Retry-After": "9999"}, b"")
        assert http_utils._retry_after_seconds(resp) == 60.0

    def test_retry_after_invalid_header(self):
        resp = _resp("u", 429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, b"")
        assert http_utils._retry_after_seconds(resp) == 0.0


# ─── 7. bug 修复：anti_block_utils ────────────────────────────────────────


class TestAntiBlockFixes:

    def test_normalize_bare_domain(self):
        limiter = DomainRateLimiter()
        assert limiter._normalize_domain("cls.cn") == "cls.cn"
        assert limiter._normalize_domain("https://www.cls.cn/api") == "cls.cn"
        assert limiter._normalize_domain("HTTP://WWW.SSE.COM.CN/x") == "com.cn"

    def test_reset_bare_domain_clears_state(self):
        limiter = DomainRateLimiter({"cls.cn": 0.01}, default_interval=0.01)
        limiter.wait("https://www.cls.cn/x")
        assert "cls.cn" in limiter._last_called
        limiter.reset("cls.cn")  # 裸域名传入（此前归一化为 "" 导致失效）
        assert "cls.cn" not in limiter._last_called

    def test_cookie_store_drops_expired(self, tmp_path):
        store = PersistentCookieStore(tmp_path / "cookies.json")
        now = time.time()
        store.save([
            {"name": "expired", "value": "1", "expires": now - 86400},
            {"name": "fresh", "value": "2", "expires": now + 86400},
            {"name": "session", "value": "3"},
        ])
        names = {c["name"] for c in store.load()}
        assert names == {"fresh", "session"}, "已过期 cookie 必须剔除"

    def test_cookie_store_iso_expires(self, tmp_path):
        store = PersistentCookieStore(tmp_path / "cookies.json")
        store.save([
            {"name": "past_iso", "expires": "2020-01-01T00:00:00"},
            {"name": "future_iso", "expires": "2099-01-01T00:00:00"},
        ])
        names = {c["name"] for c in store.load()}
        assert names == {"future_iso"}


# ─── 8. 升级：UrlDeduplicator ─────────────────────────────────────────────


class TestUrlDeduplicator:

    def test_is_new_then_seen(self):
        d = UrlDeduplicator()
        assert d.is_new("https://www.eastmoney.com/a") is True
        assert d.is_new("https://www.eastmoney.com/a") is False
        assert d.is_seen("https://www.eastmoney.com/a") is True

    def test_normalize_rules(self):
        n = UrlDeduplicator.normalize
        assert n("https://WWW.Example.com/Path/#frag") == "https://www.example.com/Path"
        assert n("http://example.com:80/x/") == "http://example.com/x"
        assert n("https://example.com:443/") == "https://example.com/"
        assert n("https://example.com/x?b=1&a=2") == "https://example.com/x?b=1&a=2"

    def test_normalized_variants_deduped(self):
        d = UrlDeduplicator()
        assert d.is_new("https://Example.com/page/") is True
        assert d.is_new("https://example.com/page#top") is False

    def test_persistence_roundtrip(self, tmp_path):
        fp = tmp_path / "seen.json"
        d1 = UrlDeduplicator(fp)
        d1.mark("https://www.cls.cn/detail/1")
        d2 = UrlDeduplicator(fp)  # 新实例从文件恢复
        assert d2.is_seen("https://www.cls.cn/detail/1") is True
        assert d2.is_new("https://www.cls.cn/detail/2") is True

    def test_stats_by_domain(self):
        d = UrlDeduplicator()
        d.mark("https://www.cls.cn/a")
        d.mark("https://www.cls.cn/b")
        d.mark("https://www.jisilu.cn/c")
        stats = d.stats()
        assert stats["total"] == 3
        assert stats["by_domain"]["cls.cn"] == 2
        assert stats["by_domain"]["jisilu.cn"] == 1

    def test_clear(self):
        d = UrlDeduplicator()
        d.mark("https://x.com/1")
        d.clear()
        assert d.stats()["total"] == 0
        assert d.is_new("https://x.com/1") is True


# ─── 9. 接线与版本 ────────────────────────────────────────────────────────


class TestWiringV72:

    def test_self_check_includes_deduplicator(self):
        report = self_check()
        assert "url_deduplicator" in report

    def test_soft_block_helper_safe_on_json(self):
        resp = _resp("u", 200, {"Content-Type": "application/json"},
                     '{"msg": "请稍后再试"}'.encode("utf-8"))
        assert http_utils._is_soft_blocked(resp) is None

    def test_version_is_720(self):
        from pathlib import Path
        init = Path(__file__).parent.parent / "scripts" / "__init__.py"
        assert "__version__ = '7.2.0'" in init.read_text(encoding="utf-8")
