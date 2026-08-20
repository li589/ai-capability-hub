# -*- coding: utf-8 -*-
"""v10.0 测试：经理新闻采集（manager_news_collector）"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "data_collection"))


def test_classify_types():
    from manager_news_collector import _classify
    assert _classify("张坤专访：谈谈白酒") == "访谈"
    assert _classify("关于基金经理变更的公告") == "公告"
    assert _classify("张坤最新调仓路径曝光") == "新闻"


def test_strip_html():
    from manager_news_collector import _strip_html
    assert _strip_html("<a href='x'>标题</a>  <span>内容</span>") == "标题 内容"


def test_parse_manager_page_links(monkeypatch, tmp_path):
    """用合成 HTML 验证经理档案页解析（不联网；真实页面约 45KB，mock 需加长）"""
    from manager_news_collector import ManagerNewsCollector, http_get
    html = """
    <html><body>
      <div class="news">
        <li><a href="https://fund.eastmoney.com/a/202608011234567.html">张坤最新调仓路径曝光</a><span class="time">08-01</span></li>
        <li><a href="https://fund.eastmoney.com/a/202607281111222.html">张坤访谈实录：谈消费板块投资机会</a></li>
        <li><a href="https://fund.eastmoney.com/a/202607201234567.html">随便一个不相关的链接标题</a></li>
      </div>
    </body></html>
    """ + "<!-- padding -->" * 500  # 真实档案页约 45KB，反爬壳页 <5KB 视为空
    monkeypatch.setattr("manager_news_collector.http_get", lambda *a, **k: html)
    coll = ManagerNewsCollector()
    items = coll._fetch_from_manager_page(
        {"manager_id": "M001", "name": "张坤"})
    titles = [i["title"] for i in items]
    assert "张坤最新调仓路径曝光" in titles
    assert "张坤访谈实录：谈消费板块投资机会" in titles
    # 不相关标题被过滤
    assert "随便一个不相关的链接标题" not in titles
    # type 分类
    inter = next(i for i in items if "访谈" in i["title"])
    assert inter["type"] == "访谈"
    assert inter["manager_id"] == "M001"


def test_manager_page_stub_returns_empty(monkeypatch):
    """反爬壳页（<5KB）应返回空列表而非误报"""
    from manager_news_collector import ManagerNewsCollector
    monkeypatch.setattr("manager_news_collector.http_get",
                        lambda *a, **k: "<html>redirect stub</html>")
    coll = ManagerNewsCollector()
    assert coll._fetch_from_manager_page({"manager_id": "M001", "name": "张坤"}) == []


def test_search_api_parse(monkeypatch):
    """东财官方搜索 API（JSONP）解析：标题/URL/日期/类型/摘要"""
    from manager_news_collector import ManagerNewsCollector
    jsonp = (
        'cb({"code":0,"hitsTotal":1000,"result":{"cmsArticleWebOld":['
        '{"title":"张坤最新调仓路径曝光，二季报仓位降至75%","date":"2026-08-13 17:34:56",'
        '"url":"http://fund.eastmoney.com/a/202608133840564293.html",'
        '"mediaName":"东方财富网","content":"这只基金于今年5月增聘两名基金经理"},'
        '{"title":"张坤专访：谈消费板块中长期机会","date":"2026-08-04 07:38:20",'
        '"url":"http://finance.eastmoney.com/a/202608043830274229.html",'
        '"mediaName":"东方财富网","content":"张坤表示…"},'
        '{"title":"普通股票新闻一则","date":"2026-08-01",'
        '"url":"http://x.eastmoney.com/a/1.html","mediaName":"X","content":""}'
        ']}});'
    )
    monkeypatch.setattr("manager_news_collector.http_get", lambda *a, **k: jsonp)
    coll = ManagerNewsCollector()
    items = coll._fetch_from_search_api({"manager_id": "M001", "name": "张坤"})
    assert len(items) == 2  # 不相关标题被过滤
    first = items[0]
    assert first["title"].startswith("张坤最新调仓")
    assert first["url"].startswith("http://fund.eastmoney.com")
    assert first["date"] == "2026-08-13"
    assert first["type"] == "新闻"
    assert first["summary"]
    inter = next(i for i in items if "专访" in i["title"])
    assert inter["type"] == "访谈"


def test_search_api_bad_response(monkeypatch):
    """搜索 API 异常/空响应应返回空列表不崩"""
    from manager_news_collector import ManagerNewsCollector
    monkeypatch.setattr("manager_news_collector.http_get", lambda *a, **k: "")
    coll = ManagerNewsCollector()
    assert coll._fetch_from_search_api({"manager_id": "M001", "name": "张坤"}) == []
    monkeypatch.setattr("manager_news_collector.http_get", lambda *a, **k: "not jsonp at all")
    assert coll._fetch_from_search_api({"manager_id": "M001", "name": "张坤"}) == []


def test_save_news_file(tmp_path):
    from manager_news_collector import ManagerNewsCollector
    import fund_advisor_paths
    # save 用 DATA_DIR，这里 monkeypatch 模块级 DATA_DIR
    monkey_holder = {}
    orig = fund_advisor_paths.DATA_DIR
    try:
        fund_advisor_paths.DATA_DIR = tmp_path
        import manager_news_collector as mnc
        mnc.DATA_DIR = tmp_path
        path = mnc.ManagerNewsCollector.save(
            [{"manager_id": "M001", "manager_name": "张坤", "title": "t",
              "date": "", "source": "s", "url": "", "type": "新闻"}],
            scanned=1)
        data = json.loads(tmp_path.joinpath("manager_news.json").read_text(encoding="utf-8"))
        assert data["meta"]["total"] == 1
        assert data["news"][0]["manager_name"] == "张坤"
        assert str(path).startswith(str(tmp_path))
    finally:
        fund_advisor_paths.DATA_DIR = orig


def test_load_managers_legacy_fallback(tmp_path, monkeypatch):
    """经理库缺失时应返回空列表而不崩（v10: 隔离真实数据目录）"""
    import fund_advisor_paths
    monkeypatch.setattr(fund_advisor_paths, "DATA_DIR", tmp_path)
    from manager_news_collector import ManagerNewsCollector
    coll = ManagerNewsCollector()
    assert coll.load_managers() == []
