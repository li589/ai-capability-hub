# -*- coding: utf-8 -*-
"""v5.0.0 模块A：数据源扩充测试（离线 mock，无网络）"""

import json
import re
from pathlib import Path

import pytest

from scripts.scrapable_registry import ScrapableRegistry, PREDEFINED_URLS

SKILL_DIR = Path(__file__).resolve().parent.parent
SOURCES_FILE = SKILL_DIR / "data" / "sentiment_sources.json"


# ============================================================
# 1. sentiment_sources.json schema 校验
# ============================================================

@pytest.fixture(scope="module")
def sources():
    return json.loads(SOURCES_FILE.read_text(encoding="utf-8"))


REQUIRED_KEYS = ["name", "homepage", "search_urls", "credibility", "language", "tags"]
CATEGORIES = ["authoritative", "financial_vertical", "self_media", "international"]


def test_meta_version_is_700(sources):
    assert sources["_meta"]["version"] == "7.0.0"


def test_total_sites_gte_50(sources):
    total = sum(len(sources[c]) for c in CATEGORIES)
    assert total >= 50, f"站点数 {total} < 50"


def test_every_category_grows(sources):
    """每类站点数相比 v4.9(9/11/10/7) 均有增加"""
    baseline = {"authoritative": 14, "financial_vertical": 11,
                "self_media": 10, "international": 7}
    for cat in CATEGORIES:
        assert len(sources[cat]) > baseline[cat], f"{cat} 未增长"


def test_required_keys_present(sources):
    bad = []
    for cat in CATEGORIES:
        for s in sources[cat]:
            for k in REQUIRED_KEYS:
                if k not in s:
                    bad.append((s.get("name"), k))
    assert not bad, f"缺必填键: {bad}"


def test_rss_feeds_key_on_all_sites(sources):
    missing = [s["name"] for cat in CATEGORIES for s in sources[cat] if "rss_feeds" not in s]
    assert not missing, f"无 rss_feeds 键: {missing}"


def test_some_sites_have_real_rss(sources):
    """至少 2 个站点有非空 RSS（v6.0.0 商业媒体源）"""
    n = sum(1 for cat in CATEGORIES for s in sources[cat] if s.get("rss_feeds"))
    assert n >= 2, f"非空 RSS 站点过少: {n}"


def test_homepage_urls_valid(sources):
    bad = []
    for cat in CATEGORIES:
        for s in sources[cat]:
            hp = s.get("homepage", "")
            if not (hp.startswith("http://") or hp.startswith("https://")):
                bad.append((s["name"], hp))
    assert not bad, f"非法 homepage: {bad}"


def test_search_urls_templates_valid(sources):
    """search_urls 模板必须含 {kw} 占位符"""
    bad = []
    for cat in CATEGORIES:
        for s in sources[cat]:
            for tpl in s.get("search_urls", []):
                if "{kw}" not in tpl:
                    bad.append((s["name"], tpl))
    assert not bad, f"search_urls 缺 {{kw}}: {bad}"


def test_search_engines_include_baidu_sogou(sources):
    engines = sources.get("search_engines", [])
    names = {e["name"] for e in engines}
    assert "baidu" in names, "缺 baidu 搜索引擎"
    assert "sogou" in names, "缺 sogou 搜索引擎"
    by_name = {e["name"]: e for e in engines}
    assert by_name["baidu"]["engine"] == "baidu_html"
    assert by_name["sogou"]["engine"] == "sogou_html"
    assert by_name["baidu"]["needs_api_key"] is False
    assert by_name["baidu"]["enabled"] is True


# ============================================================
# 2. scrapable_registry PREDEFINED_URLS 校验
# ============================================================

def test_predefined_urls_gte_220():
    assert len(PREDEFINED_URLS) >= 220, f"PREDEFINED_URLS {len(PREDEFINED_URLS)} < 220"


def test_predefined_urls_format():
    bad = [(n, u) for n, u in PREDEFINED_URLS.items()
           if not (u.startswith("http://") or u.startswith("https://"))]
    assert not bad, f"非法 URL: {bad}"


def test_new_entities_added():
    for name in ["上海期货交易所", "上海银行间同业拆放利率", "香港交易所",
                 "中国银行业协会", "中国证券业协会"]:
        assert name in PREDEFINED_URLS, f"缺少 {name}"


def test_futures_exchanges_all_present():
    for name in ["上海期货交易所", "大连商品交易所", "郑州商品交易所",
                 "中国金融期货交易所", "上海国际能源交易中心", "广州期货交易所"]:
        assert name in PREDEFINED_URLS


def test_registry_loadable():
    reg = ScrapableRegistry()
    assert reg.total > 0
    inst = reg.get("中国工商银行")
    assert inst is not None
    # PREDEFINED_URLS 作为 URL 补全表：已注册机构缺 website 时用预定义补全
    assert inst["website"] == PREDEFINED_URLS["中国工商银行"]
    assert inst["scrapable"] is True


# ============================================================
# 3. structured_market_data 模块（akshare 缺失时安全降级）
# ============================================================

def test_list_data_types_nonempty():
    from scripts.structured_market_data import list_data_types, AKSHARE_ROUTES
    types = list_data_types()
    assert len(types) >= 10
    for t in types:
        assert t["data_type"] in AKSHARE_ROUTES


def test_unknown_data_type_returns_none():
    from scripts.structured_market_data import get_structured_data
    assert get_structured_data("not_exist") is None


def test_akshare_missing_returns_none(monkeypatch):
    """akshare 不可用时：非宏观类型返回 None；宏观 4 项走 v7.0.0 HTTP 兜底"""
    from scripts.structured_market_data import get_structured_data
    monkeypatch.setattr("scripts.structured_market_data._call_akshare", lambda *a, **k: None)
    # HTTP 兜底也模拟失败 → 全部 None（不抛异常）
    monkeypatch.setattr("scripts.market_data_scraper.get_macro_indicator",
                        lambda *a, **k: [])
    for dt in ["futures_spot", "macro_cpi", "shibor", "hk_spot", "us_spot",
               "futures_daily", "futures_holding", "macro_gdp", "macro_ppi",
               "macro_pmi", "macro_fx_reserves", "repo_rate"]:
        assert get_structured_data(dt) is None, f"{dt} 应返回 None"


def test_akshare_missing_macro_http_fallback(monkeypatch):
    """v7.0.0: akshare 缺失但 HTTP 兜底可用时，宏观返回数据而非 None"""
    from scripts.structured_market_data import get_structured_data
    monkeypatch.setattr("scripts.structured_market_data._call_akshare", lambda *a, **k: None)
    monkeypatch.setattr("scripts.market_data_scraper.get_macro_indicator",
                        lambda *a, **k: [{"date": "2026-07-01", "yoy": 0.5}])
    rows = get_structured_data("macro_cpi", limit=2)
    assert isinstance(rows, list) and rows and rows[0]["yoy"] == 0.5
    # 非宏观类型不启用 HTTP 兜底
    assert get_structured_data("shibor") is None


def test_akshare_missing_never_raises(monkeypatch):
    """_call_akshare 抛异常时 get_structured_data 吞掉；宏观兜底也失败时返回 None"""
    from scripts.structured_market_data import get_structured_data

    def _boom(*a, **k):
        raise RuntimeError("akshare 异常")

    monkeypatch.setattr("scripts.structured_market_data._call_akshare", _boom)
    monkeypatch.setattr("scripts.market_data_scraper.get_macro_indicator",
                        lambda *a, **k: [])
    assert get_structured_data("shibor") is None
    assert get_structured_data("macro_cpi") is None


def test_kwargs_override_defaults(monkeypatch):
    """kwargs 覆盖默认参数；显式 None 不覆盖"""
    from scripts.structured_market_data import get_structured_data
    calls = {}

    def _fake_call(func_name, kwargs):
        calls["func"] = func_name
        calls["kwargs"] = dict(kwargs)
        return "OK"

    monkeypatch.setattr("scripts.structured_market_data._call_akshare", _fake_call)
    assert get_structured_data("macro_cpi", start_year="2022") == "OK"
    assert calls["func"] == "macro_china_cpi"
    assert calls["kwargs"]["start_year"] == "2022"


def test_fallback_to_empty_kwargs(monkeypatch):
    """默认参数调用失败时降级为空参数调用"""
    from scripts.structured_market_data import get_structured_data
    calls = []

    def _fake_call(func_name, kwargs):
        calls.append(dict(kwargs))
        if kwargs:
            return None
        return "EMPTY_OK"

    monkeypatch.setattr("scripts.structured_market_data._call_akshare", _fake_call)
    assert get_structured_data("repo_rate") == "EMPTY_OK"
    assert len(calls) == 2
    assert calls[1] == {}


def test_akshare_routes_shape():
    from scripts.structured_market_data import AKSHARE_ROUTES
    for k, v in AKSHARE_ROUTES.items():
        assert isinstance(v["func"], str) and v["func"]
        assert isinstance(v["defaults"], dict)


def test_predefined_urls_no_duplicates():
    """PREDEFINED_URLS 无重复 URL（与既有 test_scrapable_registry 约束一致）"""
    from collections import Counter
    c = Counter(PREDEFINED_URLS.values())
    dups = {u: n for u, n in c.items() if n > 1}
    assert not dups, f"重复 URL: {dups}"
