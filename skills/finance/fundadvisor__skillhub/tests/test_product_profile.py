# -*- coding: utf-8 -*-
"""v10.0 测试：产品档案采集（fund_profile_collector）+ db_format 列扩宽"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "data_collection"))


# ── db_format 列扩宽 ───────────────────────────────────────────

def test_db_format_product_cols_widened(tmp_path):
    from db_format import write_products, _PRODUCT_COLS
    assert "investment_scope" in _PRODUCT_COLS
    assert "management_fee" in _PRODUCT_COLS
    assert "perf_1y" in _PRODUCT_COLS
    rows = [{"code": "000001", "name": "华夏成长", "type": "混合型", "pinyin": "hxcz",
             "update": "2026-08-14", "risk_level": "中风险", "scale": "120.5",
             "investment_scope": "股票资产60%-95%", "management_fee": "1.50%",
             "perf_1y": "12.3%"}]
    p = tmp_path / "fund_products.json"
    write_products(p, rows, meta={"updated": "2026-08-14"})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["_f"][-1] == "benchmark"  # 全部扩宽列都在
    assert data["c"][0] == ["000001"]


def test_db_format_old_loader_compat(tmp_path):
    """旧 loader（_decode_columnar）读新列文件应兼容缺列"""
    from db_format import write_products
    from fund_advisor_paths import load_json_data
    rows = [{"code": "000001", "name": "华夏成长", "type": "混合型", "pinyin": "hxcz",
             "update": "2026-08-14"}]
    p = tmp_path / "fund_products.json"
    write_products(p, rows)
    data = load_json_data(str(p))
    items = data.get("items", [])
    assert items[0]["code"] == "000001"
    assert items[0].get("investment_scope") is None  # 缺失列 → None 不崩


# ── 解析工具 ───────────────────────────────────────────────────

def test_parse_h4_sections():
    from fund_profile_collector import _parse_h4_sections
    html = """
    <h4 class="t">投资目标</h4><div class="txt_in"><p>通过投资优质企业实现长期增值</p></div>
    <h4 class="t">投资范围</h4><div class="txt_in"><p>股票资产占基金资产60%-95%</p></div>
    """
    out = _parse_h4_sections(html)
    assert out["投资目标"] == "通过投资优质企业实现长期增值"
    assert "60%-95%" in out["投资范围"]


def test_parse_table_rows():
    from fund_profile_collector import _parse_table_rows
    html = """
    <table><tr><th>成立日期</th><td>2001-12-18</td></tr>
    <tr><th>资产规模</th><td>120.50亿元（2026年06月30日）</td></tr>
    <tr><th>基金经理</th><td>张坤</td></tr></table>
    """
    out = _parse_table_rows(html)
    assert out["成立日期"] == "2001-12-18"
    assert out["资产规模"] == "120.50亿元（2026年06月30日）"
    assert out["基金经理"] == "张坤"


def test_parse_performance():
    from fund_profile_collector import FundProfileCollector
    js = """
    var Data_performanceEvaluation = {
      "data": {"1": [
        {"title": "近1月", "values": [["2026-07-14", "3.21%"], ["2026-08-14", "4.56%"]]},
        {"title": "近1年", "values": [["2026-08-14", "12.34%"]]}
      ]},
      "code": "000001", "name": "华夏成长"
    };
    """
    perf = FundProfileCollector._parse_performance(js)
    assert perf["perf_1m"] == "4.56%"
    assert perf["perf_1y"] == "12.34%"


def test_parse_performance_missing():
    from fund_profile_collector import FundProfileCollector
    assert FundProfileCollector._parse_performance("var x = 1;") == {}
    assert FundProfileCollector._parse_performance("") == {}


# ── 单基金采集（mock 网络） ───────────────────────────────────

def test_fetch_profile_mocked(monkeypatch, tmp_path):
    """mock http_get：jbgk 文本 + jjfl 表格 拼接出一个完整档案（按真实页面文本结构）"""
    import fund_profile_collector as fpc
    pages = {
        'jbgk': ("投资目标 通过投资优质企业实现长期资本增值 投资范围 股票资产占基金资产的60%-95%，"
                 "其中投资于中小盘股票的比例不低于股票资产的80% 投资策略 精选优质企业长期持有 "
                 "业绩比较基准 沪深300指数收益率*80%+中债总指数收益率*20% 跟踪标的 无 "
                 "风险收益特征 本基金为混合型基金 成立日期：2001-12-18 基金经理：张坤 "
                 "类型：混合型 管理人：易方达基金 净资产规模：120.50亿元"),
        'jjfl': ("<table><tr><th>管理费率</th><td>1.50%（每年）</td></tr>"
                 "<tr><th>托管费率</th><td>0.25%（每年）</td></tr>"
                 "<tr><th>最低申购金额</th><td>10元</td></tr></table>"),
        'pingzhong': "var Data_performanceEvaluation = {'data': []};",
    }

    def fake_get(url, timeout=15, encoding='utf-8'):
        if 'jbgk_' in url:
            return pages['jbgk']
        if 'jjfl_' in url:
            return pages['jjfl']
        if 'pingzhongdata' in url:
            return pages['pingzhong']
        return ''

    monkeypatch.setattr(fpc, "http_get", fake_get)
    coll = fpc.FundProfileCollector(delay=0)
    rec = coll.fetch_profile("000001")
    assert rec["code"] == "000001"
    assert rec["inception_date"] == "2001-12-18"
    assert rec["scale"] == "120.50"
    assert "张坤" in rec["manager"]
    assert rec["investment_goal"] == "通过投资优质企业实现长期资本增值"
    assert "60%-95%" in rec["investment_scope"]
    assert rec["benchmark"].startswith("沪深300")
    assert rec["management_fee"] == "1.50%（每年）"
    assert rec["min_subscription"] == "10元"


def test_enrich_products_mocked(monkeypatch, tmp_path):
    import fund_profile_collector as fpc

    def fake_get(url, timeout=15, encoding='utf-8'):
        if 'jbgk_' in url:
            return ("投资目标 长期资本增值 投资范围 股票资产占基金资产的60%-95% "
                    "投资策略 精选优质企业 业绩比较基准 沪深300指数收益率 跟踪标的 无 "
                    "风险收益特征 混合型基金 成立日期：2001-12-18 基金经理：张三 "
                    "类型：混合型 净资产规模：50亿元")
        return ''

    monkeypatch.setattr(fpc, "http_get", fake_get)
    coll = fpc.FundProfileCollector(delay=0)
    products = [{"code": "000001", "name": "华夏成长", "type": "混合型", "pinyin": "hxcz"}]
    enriched = coll.enrich_products(products, progress=False)
    assert len(enriched) == 1
    assert enriched[0]["name"] == "华夏成长"
    assert enriched[0]["type"] == "混合型"
    assert "60%-95%" in enriched[0]["investment_scope"]
    assert enriched[0]["update"]


def test_full_data_refresh_import_ok():
    """full_data_refresh 应能干净导入（含 v10.0 档案增强步骤）"""
    import full_data_refresh
    assert hasattr(full_data_refresh, "fetch_all_products")
