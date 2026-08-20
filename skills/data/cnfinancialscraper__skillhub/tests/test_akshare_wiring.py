# -*- coding: utf-8 -*-
"""v5.0.0 模块B：akshare 兜底接线 + requests 限流接线测试（离线 mock）"""

import pytest

from scripts.akshare_fallback import akshare_to_records, fallback_akshare


# ============================================================
# 1. akshare_fallback 公共 helper
# ============================================================

def test_akshare_to_records_none():
    assert akshare_to_records(None) == []


def test_akshare_to_records_list_of_dict():
    assert akshare_to_records([{"a": 1, "b": 2}]) == [{"a": 1, "b": 2}]


def test_akshare_to_records_with_map(monkeypatch):
    class FakeDF:
        def to_dict(self, orient):
            return [{"标题": "A", "链接": "http://x", "其他": "y"}]

    out = akshare_to_records(FakeDF(), {"title": ["标题"], "url": ["链接"]})
    assert out == [{"title": "A", "url": "http://x"}]


def test_akshare_to_records_bad_type():
    assert akshare_to_records("not-a-list") == []


def test_fallback_akshare_no_such_func_returns_empty():
    # akshare 未装或函数不存在 → 返回 [] 不抛
    assert fallback_akshare("__no_such_func__", {}) == []


# ============================================================
# 2. cls_scraper 兜底接线
# ============================================================

def test_cls_get_telegraph_falls_back(monkeypatch):
    """主路径失败时降级到 akshare"""
    from scripts import cls_scraper

    monkeypatch.setattr(cls_scraper, "http_post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("blocked")))
    fake = [{"title": "降级新闻", "url": "http://x", "publish_time": "2026-08-01"}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)

    out = cls_scraper.get_telegraph(limit=5)
    assert out == fake


def test_cls_get_hot_articles_falls_back(monkeypatch):
    from scripts import cls_scraper

    monkeypatch.setattr(cls_scraper, "http_post", lambda *a, **k: None)  # 返回空 → 主路径空
    fake = [{"title": "hot"}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)

    # 主路径 resp is None → 直接 return []（不触发 except），只验证 except 分支的降级
    # 通过抛异常验证
    monkeypatch.setattr(cls_scraper, "http_post", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
    assert cls_scraper.get_hot_articles(limit=3) == fake


def test_cls_search_articles_falls_back(monkeypatch):
    from scripts import cls_scraper

    monkeypatch.setattr(cls_scraper, "http_post", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
    fake = [{"title": "搜到", "url": "http://y"}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)
    assert cls_scraper.search_articles("茅台", limit=3) == fake


def test_cls_fallback_internal_import_error_safe(monkeypatch):
    """fallback_akshare 本身抛异常时，scraper 返回空不崩"""
    from scripts import cls_scraper

    monkeypatch.setattr(cls_scraper, "http_post", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))

    def _boom(*a, **k):
        raise RuntimeError("akshare broken")

    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", _boom)
    assert cls_scraper.get_telegraph(limit=3) == []


# ============================================================
# 3. jisilu 兜底接线
# ============================================================

def test_jisilu_bond_fallback(monkeypatch):
    from scripts.jisilu_scraper import _akshare_bond_fallback

    fake = [{"bond_id": "113050", "bond_nm": "南银转债", "price": 120.5}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)
    assert _akshare_bond_fallback() == fake


def test_jisilu_bond_fallback_returns_empty_on_error(monkeypatch):
    from scripts.jisilu_scraper import _akshare_bond_fallback

    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    assert _akshare_bond_fallback() == []


def test_jisilu_get_convertible_bonds_falls_back(monkeypatch):
    """resp is None 时降级到 akshare"""
    from scripts import jisilu_scraper

    monkeypatch.setattr(jisilu_scraper, "get_session", lambda headers=None: None)
    monkeypatch.setattr(jisilu_scraper, "http_get", lambda *a, **k: None)
    monkeypatch.setattr(jisilu_scraper, "rate_limit", lambda *a, **k: None)
    monkeypatch.setattr(jisilu_scraper, "http_post", lambda *a, **k: None)
    fake = [{"bond_id": "110000"}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)
    assert jisilu_scraper.get_convertible_bonds() == fake


# ============================================================
# 4. sina / wallstreetcn 兜底接线
# ============================================================

def test_sina_realtime_falls_back(monkeypatch):
    from scripts import sina_scraper

    monkeypatch.setattr(sina_scraper, "fetch_text", lambda *a, **k: "")
    fake = [{"代码": "600519", "名称": "贵州茅台", "最新价": 1800.0, "涨跌幅": 2.3}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)
    out = sina_scraper.get_realtime_quote(["600519"])
    assert "600519" in out
    assert out["600519"]["name"] == "贵州茅台"


def test_wallstreetcn_live_falls_back(monkeypatch):
    from scripts import wallstreetcn_scraper

    monkeypatch.setattr(wallstreetcn_scraper, "http_get_json", lambda *a, **k: None)
    monkeypatch.setattr(wallstreetcn_scraper, "rate_limit", lambda *a, **k: None)
    fake = [{"title": "快讯", "content_text": "内容", "uri": "http://x"}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)
    out = wallstreetcn_scraper.get_live_news(limit=5)
    assert out["total"] == 1
    assert out["items"][0]["title"] == "快讯"


def test_wallstreetcn_articles_falls_back(monkeypatch):
    from scripts import wallstreetcn_scraper

    monkeypatch.setattr(wallstreetcn_scraper, "http_get_json", lambda *a, **k: None)
    monkeypatch.setattr(wallstreetcn_scraper, "rate_limit", lambda *a, **k: None)
    fake = [{"title": "文章"}]
    monkeypatch.setattr("scripts.akshare_fallback.fallback_akshare", lambda *a, **k: fake)
    out = wallstreetcn_scraper.get_articles(limit=5)
    assert out["total"] == 1


# ============================================================
# 5. requests 限流接线（B4）
# ============================================================

def test_ratelimited_session_calls_rate_limit(monkeypatch):
    from scripts.http_utils import RatelimitedSession

    calls = []
    monkeypatch.setattr("scripts.http_utils.rate_limit", lambda *a, **k: calls.append(k.get("url")))

    class FakeResp:
        def __init__(self): self.ok = True

    class FakeSession:
        def __init__(self): self.last_url = None
        def get(self, url, **kw): self.last_url = url; return FakeResp()

    inner = FakeSession()
    rs = RatelimitedSession(inner)
    rs.get("https://eastmoney.com/api?a=1")
    assert inner.last_url == "https://eastmoney.com/api?a=1"
    assert calls == ["https://eastmoney.com/api?a=1"]


def test_ratelimited_session_proxies_attributes():
    from scripts.http_utils import RatelimitedSession

    class Fake:
        def __init__(self): self.headers = {"UA": "x"}
        def close(self): return "closed"

    rs = RatelimitedSession(Fake())
    assert rs.headers == {"UA": "x"}
    assert rs.close() == "closed"


def test_company_report_session_is_ratelimited():
    from scripts.company_report_scraper import EastMoneyReportAPI
    from scripts.http_utils import RatelimitedSession

    api = EastMoneyReportAPI()
    if api.session is not None:  # requests 可用时
        assert isinstance(api.session, RatelimitedSession)


def test_news_session_is_ratelimited():
    from scripts.news_scraper import EastMoneyNewsAPI
    from scripts.http_utils import RatelimitedSession

    api = EastMoneyNewsAPI()
    if api.session is not None:
        assert isinstance(api.session, RatelimitedSession)


def test_em_json_get_requests_branch_ratelimited(monkeypatch):
    """_em_json_get 的 requests 分支也调用 rate_limit"""
    from scripts import eastmoney_scraper

    rate_calls = []
    monkeypatch.setattr("scripts.http_utils.rate_limit", lambda *a, **k: rate_calls.append(k.get("url", "")))

    class FakeResp:
        text = '{"ok": true}'
        def raise_for_status(self): pass

    monkeypatch.setattr(eastmoney_scraper, "_requests", type("R", (), {"get": lambda *a, **k: FakeResp()})())
    monkeypatch.setattr(eastmoney_scraper, "_HAS_REQUESTS", True)

    out = eastmoney_scraper._em_json_get("https://push2.eastmoney.com/api/1")
    assert out == {"ok": True}
    assert len(rate_calls) == 1
