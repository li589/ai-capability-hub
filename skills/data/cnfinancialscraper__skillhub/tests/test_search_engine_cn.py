# -*- coding: utf-8 -*-
"""v5.0.0 模块B：百度/搜狗中文搜索引擎测试（离线 fixture，无网络）"""

import pytest

from scripts.search_engine import (
    BaiduHTML, SogouHTML, MultiEngineSearch, SearchResult,
)


BAIDU_HTML = """
<div class="result c-container">
  <h3 class="t"><a href="https://www.baidu.com/link?url=real1%3A%2F%2Fexample.com%2Fmoutai&wd=kw">贵州茅台 2026半年报 营收增长</a></h3>
  <div class="c-abstract">茅台营收同比增长 18%，净利润创新高。</div>
</div>
<div class="result c-container">
  <h3 class="t"><a href="https://finance.eastmoney.com/a/2026.html">东方财富：白酒板块走强</a></h3>
  <div class="c-abstract">白酒股集体上涨。</div>
</div>
"""

SOGOU_HTML = """
<div class="vrwrap">
  <h3 class="vr-title"><a href="https://www.sogou.com/link?url=abc123">微信：茅台经销商大会</a></h3>
  <p class="star-wiki">经销商库存下降。</p>
</div>
<div class="vrwrap">
  <h3 class="vr-title"><a href="https://cninfo.com.cn/x">深交所公告：茅台回购</a></h3>
  <p class="txt-info">拟回购金额上限 30 亿。</p>
</div>
"""


# ============================================================
# 1. 百度 /link?url= 还原
# ============================================================

def test_baidu_url_resolve():
    assert BaiduHTML._resolve_baidu_url(
        "https://www.baidu.com/link?url=https%3A%2F%2Fexample.com%2Fa&wd=x"
    ) == "https://example.com/a"


def test_baidu_url_resolve_plain():
    assert BaiduHTML._resolve_baidu_url("https://eastmoney.com/x") == "https://eastmoney.com/x"


def test_sogou_url_resolve():
    assert SogouHTML._resolve_sogou_url("https://www.sogou.com/link?url=abc") == "abc"


def test_sogou_url_resolve_plain():
    assert SogouHTML._resolve_sogou_url("https://cninfo.com.cn/x") == "https://cninfo.com.cn/x"


# ============================================================
# 2. 百度 HTML 解析
# ============================================================

def test_baidu_parse(monkeypatch):
    engine = BaiduHTML(timeout=3)
    monkeypatch.setattr(engine, "_http_get", lambda url, headers=None: BAIDU_HTML)
    results = engine.search("贵州茅台", limit=5)
    assert len(results) == 2
    # 第一条是百度跳转链接 → 还原为真实 URL
    assert results[0].url == "real1://example.com/moutai"
    assert "贵州茅台" in results[0].title
    assert results[0].snippet != ""
    # 第二条普通 URL 原样保留
    assert results[1].url == "https://finance.eastmoney.com/a/2026.html"


def _no_sleep(monkeypatch):
    import scripts.search_engine as se
    monkeypatch.setattr(se.time, "sleep", lambda *a, **k: None)


def test_baidu_parse_empty(monkeypatch):
    _no_sleep(monkeypatch)
    engine = BaiduHTML(timeout=3)
    monkeypatch.setattr(engine, "_http_get", lambda url, headers=None: "")
    assert engine.search("不存在", limit=5) == []


def test_baidu_parse_none(monkeypatch):
    _no_sleep(monkeypatch)
    engine = BaiduHTML(timeout=3)
    monkeypatch.setattr(engine, "_http_get", lambda url, headers=None: None)
    assert engine.search("xxx", limit=5) == []


# ============================================================
# 3. 搜狗 HTML 解析
# ============================================================

def test_sogou_parse(monkeypatch):
    engine = SogouHTML(timeout=3)
    monkeypatch.setattr(engine, "_http_get", lambda url, headers=None: SOGOU_HTML)
    results = engine.search("茅台", limit=5)
    assert len(results) == 2
    assert results[0].title == "微信：茅台经销商大会"
    assert results[0].url == "abc123"
    assert results[1].url == "https://cninfo.com.cn/x"


def test_sogou_parse_empty(monkeypatch):
    _no_sleep(monkeypatch)
    engine = SogouHTML(timeout=3)
    monkeypatch.setattr(engine, "_http_get", lambda url, headers=None: None)
    assert engine.search("xxx", limit=5) == []


# ============================================================
# 4. 引擎注册与自动检测
# ============================================================

def test_registry_has_cn_engines():
    reg = MultiEngineSearch.ENGINE_REGISTRY
    assert "baidu_html" in reg
    assert "sogou_html" in reg
    assert reg["baidu_html"] is BaiduHTML
    assert reg["sogou_html"] is SogouHTML


def test_auto_detect_prefers_cn_engines():
    m = MultiEngineSearch()
    names = [e.name for e in m.engines]
    assert names[0] == "baidu_html"
    assert names[1] == "sogou_html"


def test_create_engine_baidu_sogou():
    m = MultiEngineSearch(engines=["baidu_html", "sogou_html"])
    assert any(isinstance(e, BaiduHTML) for e in m.engines)
    assert any(isinstance(e, SogouHTML) for e in m.engines)


def test_cn_engines_need_no_api_key():
    assert BaiduHTML.needs_api_key is False
    assert SogouHTML.needs_api_key is False
