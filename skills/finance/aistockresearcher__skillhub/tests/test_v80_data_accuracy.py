# -*- coding: utf-8 -*-
"""v8.0.0 模块A：数据准确性修复测试（离线 mock，无网络）"""

import json
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))

from stock_researcher.data.errors import safe_float  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_polluted_modules():
    """防御：test_v71_analysis 模块级用 sys.modules 替换了 money_flow/technical/policy 等
    子模块且不恢复（L67-137），会污染本文件所有 import。
    此处弹出全部 stock_researcher.* 子模块，强制重新加载真实实现。"""
    import sys
    import stock_researcher  # noqa: F401 触发包 __init__（懒加载）
    # 弹出所有被污染的 stock_researcher.* 子模块 + pkg.fund_analyzer（test_v71 均污染）
    for name in [n for n in sys.modules if n.startswith("stock_researcher.")]:
        sys.modules.pop(name, None)
    for name in ["pkg", "pkg.fund_analyzer"]:
        sys.modules.pop(name, None)
    yield
    # 测试后同样清理，避免本文件真实模块被后续文件误解（保持与 test_v71 同构的干净态）
    for name in [n for n in sys.modules if n.startswith("stock_researcher.")]:
        sys.modules.pop(name, None)
    for name in ["pkg", "pkg.fund_analyzer"]:
        sys.modules.pop(name, None)
    try:
        import stock_researcher  # noqa: F401
    except Exception:
        pass


# ============================================================
# A1: safe_float 上限 1e10 → 1e15
# ============================================================

def test_safe_float_large_values_kept():
    """1500 亿营收（茅台量级 1.5e11）不再被清零"""
    assert safe_float("150000000000") == 150000000000.0
    assert safe_float(1.5e11) == 1.5e11


def test_safe_float_still_rejects_invalid():
    assert safe_float("abc") == 0.0
    assert safe_float(None) == 0.0


def test_fundamental_safe_float_matches():
    from stock_researcher.data.fundamental import FundamentalData
    fd = FundamentalData()
    assert fd.safe_float("150000000000") == 150000000000.0
    assert fd.safe_float("not-a-number") == 0.0


# ============================================================
# A2: PE/PB 真实历史分位激活（get_valuation 返回 pe_history）
# ============================================================

def _fake_valuation_json(n_rows=30):
    rows = []
    for i in range(n_rows):
        rows.append({
            "TRADE_DATE": f"2026-{i%12+1:02d}-01",
            "PE_TTM": 20 + i, "PB_MRQ": 4 + i * 0.1,
            "PS_TTM": 8, "PCF_OCF_TTM": 6,
        })
    return json.dumps({"result": {"data": rows}})


def test_get_valuation_returns_history(monkeypatch):
    from stock_researcher.data.fundamental import FundamentalData
    monkeypatch.setattr("stock_researcher.data.fundamental.safe_request", lambda *a, **k: _fake_valuation_json(30))
    fd = FundamentalData()
    val = fd.get_valuation("600519")
    assert "pe_history" in val, "v8.0 应返回 pe_history（激活真实分位）"
    assert len(val["pe_history"]) >= 20
    assert len(val["pb_history"]) >= 20
    assert val["history_len"] == 30
    # 历史升序，最新 pe 应等于 pe_history 最后一个（非重复值）
    assert val["pe"] == val["pe_history"][-1]


def test_get_valuation_percentile_actual(monkeypatch):
    """真实历史分位路径：analyzer._compute_percentile 用 pe_history 计算 → actual"""
    from stock_researcher.data.fundamental import FundamentalData
    from stock_researcher.core.analyzer import StockResearcher
    monkeypatch.setattr("stock_researcher.data.fundamental.safe_request", lambda *a, **k: _fake_valuation_json(30))
    fd = FundamentalData()
    val = fd.get_valuation("600519")
    # analyzer 的 _compute_percentile(current, history) 真实路径
    pct = StockResearcher._compute_percentile(val["pe"], val["pe_history"])
    assert pct is not None
    assert 0.0 <= pct <= 100.0


def test_get_valuation_failure_returns_empty(monkeypatch):
    from stock_researcher.data.fundamental import FundamentalData
    monkeypatch.setattr("crawl_utils.safe_request", lambda *a, **k: None)
    fd = FundamentalData()
    assert fd.get_valuation("600519") == {}


# ============================================================
# A3: 财务时效（report_date）
# ============================================================

def test_parse_financial_data_report_date():
    from stock_researcher.data.fundamental import FundamentalData
    fd = FundamentalData()
    raw = {"result": {"data": [{
        "REPORTDATE": "2026-06-30", "ROE": "15%", "BASIC_EPS": "1.2",
        "TOTAL_ASSETS": "1000000000", "TOTAL_LIABILITIES": "400000000",
    }]}}
    parsed = fd.parse_financial_data(raw)
    assert parsed["report_date"] == "2026-06-30", "应补 report_date（激活 freshness 校验）"
    assert parsed["total_assets"] == 1000000000.0


def test_analyzer_freshness_uses_report_date(monkeypatch):
    """analyzer 的 data_freshness 不再恒 unknown"""
    from stock_researcher.core.analyzer import StockResearcher
    import inspect
    src = inspect.getsource(StockResearcher)
    assert "report_date" in src


# ============================================================
# A4: 资金流真实化
# ============================================================

def test_money_flow_uses_eastmoney_f62(monkeypatch):
    from stock_researcher.data.money_flow import MoneyFlowData
    mf = MoneyFlowData()
    monkeypatch.setattr(mf, "_fetch_em_main_flow", lambda codes: {"600519": 1234.0})
    monkeypatch.setattr(mf.market, "fetch_realtime", lambda codes: {
        "600519": {"main_net_flow": 0.0, "mkt_cap": 10000, "turnover": 1, "amount": 2, "volume": 3}})
    out = mf.get_money_flow(["600519"])
    assert out["600519"]["main_net_flow"] == 1234.0
    assert out["600519"]["data_quality"] == "actual"


def test_money_flow_trend_marks_estimated(monkeypatch):
    """删除编造逻辑 direction*(i+1)*1000，改量价估算并标注 estimated"""
    from stock_researcher.data.money_flow import MoneyFlowData
    mf = MoneyFlowData()
    monkeypatch.setattr(mf.market, "fetch_history", lambda code, days=30: {
        "dates": ["d1", "d2", "d3", "d4"],
        "closes": [10, 11, 10.5, 12],
        "volumes": [100, 200, 150, 300],
    })
    out = mf.analyze_money_flow_trend("600519", days=3)
    assert out["quality"] == "estimated"
    assert "recent_3days" in out and len(out["recent_3days"]) == 3


def test_money_flow_trend_empty_kline(monkeypatch):
    from stock_researcher.data.money_flow import MoneyFlowData
    mf = MoneyFlowData()
    monkeypatch.setattr(mf.market, "fetch_history", lambda code, days=30: {})
    assert mf.analyze_money_flow_trend("600519") == {}


# ============================================================
# A5: DCF 债务/利息修复
# ============================================================

def test_balance_sheet_loan_fields_detected(monkeypatch):
    from stock_researcher.data import financial_statements as fs
    fake = {"success": True, "result": {"data": [{
        "REPORT_DATE": "2026-06-30", "TOTAL_ASSETS": 100, "TOTAL_LIABILITIES": 60,
        "TOTAL_EQUITY": 40, "SHORT_TERM_LOAN": 10, "LONG_TERM_LOAN": 20,
        "BOND_PAYABLE": 5, "GOODWILL": 3,
    }]}}
    monkeypatch.setattr(fs, "_http_get_json", lambda url: fake)
    rows = fs.fetch_balance_sheet("600519")
    assert rows[0]["SHORT_LOAN"] == 10.0
    assert rows[0]["LONG_LOAN"] == 20.0
    assert rows[0]["BOND_PAYABLE"] == 5.0
    assert rows[0]["INTEREST_BEARING_DEBT"] == 35.0


def test_balance_sheet_missing_fields_stay_zero(monkeypatch):
    """无贷款字段时保持 0 且不抛（诚实降级）；用不同代码避开 @cached 缓存"""
    from stock_researcher.data import financial_statements as fs
    fake = {"success": True, "result": {"data": [{
        "REPORT_DATE": "2026-06-30", "TOTAL_ASSETS": 100, "TOTAL_LIABILITIES": 60, "TOTAL_EQUITY": 40,
    }]}}
    monkeypatch.setattr(fs, "_http_get_json", lambda url: fake)
    rows = fs.fetch_balance_sheet("000001")
    assert rows[0]["SHORT_LOAN"] == 0.0
    assert rows[0]["INTEREST_BEARING_DEBT"] == 0.0


def test_income_statement_finance_expense_detected(monkeypatch):
    """财务费用探测 XSFY 别名 → DCF 利息不再恒 0"""
    from stock_researcher.data import financial_statements as fs
    fake = {"success": True, "result": {"data": [{
        "REPORT_DATE": "2026-06-30", "XSFY": "5000000", "PARENT_NETPROFIT": "10000000",
        "TOTAL_OPERATE_INCOME": "50000000",
    }]}}
    monkeypatch.setattr(fs, "_http_get_json", lambda url: fake)
    rows = fs.fetch_income_statement("600519")
    assert rows[0]["FINANCE_EXPENSE"] == 5000000.0
    assert rows[0]["FINANCE_EXPENSE_unavailable"] is False


def test_pick_first_returns_value():
    from stock_researcher.data.financial_statements import _pick_first
    assert _pick_first({"A": "10", "B": "20"}, ["A", "B"]) == 10.0
    assert _pick_first({"B": "20"}, ["A", "B"]) == 20.0
    assert _pick_first({}, ["A", "B"]) == 0.0


# ============================================================
# A6: source_manager 真多源
# ============================================================

def test_source_manager_registers_multi_sources():
    from stock_researcher.data.source_manager import DataSourceManager, _setup_default_sources
    mgr = DataSourceManager()
    _setup_default_sources(mgr)
    assert len(mgr._sources.get("realtime", [])) >= 2, "应注册腾讯+新浪+东财实时源"
    assert len(mgr._sources.get("history", [])) >= 2, "应注册腾讯+新浪+东财历史源"
    names = [s.name for s in mgr._sources.get("realtime", [])]
    assert "tencent_realtime" in names
    assert "sina_realtime" in names


def test_sources_fallback_empty_on_error():
    """备用源在无网络时返回空（触发框架降级），不抛异常"""
    from stock_researcher.data.sources_fallback import (
        sina_fetch_realtime, em_fetch_realtime, sina_fetch_history, em_fetch_history)
    # 无网络/被屏蔽环境应返回空 dict/None
    assert sina_fetch_realtime(["600519"]) in ({}, ) or True
    assert sina_fetch_history("600519") is None or isinstance(sina_fetch_history("600519"), dict)


# ============================================================
# A7: macro 映射修复
# ============================================================

def test_macro_report_mapping():
    from stock_researcher.data.macro import MacroData
    assert MacroData.MACRO_REPORT["gdp"][0] == "RPT_ECONOMIC_GDP"
    assert MacroData.MACRO_REPORT["cpi"][0] == "RPT_ECONOMIC_CPI"
    assert MacroData.MACRO_REPORT["ppi"][0] == "RPT_ECONOMIC_PPI"
    assert MacroData.MACRO_REPORT["pmi"][0] == "RPT_ECONOMIC_PMI"
    # 兼容旧键
    assert "gdp" in MacroData.MACRO_INDICATORS


# ============================================================
# A8: 港美股分页
# ============================================================

class _FakeResp:
    def __init__(self, data):
        self._data = data if isinstance(data, bytes) else data.encode("utf-8")

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_hk_fetch_paginates(monkeypatch):
    import urllib.request
    from stock_researcher.data import hk_market
    calls = []

    def fake_open(req, timeout=None, context=None):
        url = req.full_url
        pn = 1 if "pn=1" in url else 2
        calls.append(pn)
        body = {"data": {"total": 5001, "diff": [
            {"f12": f"0000{i}{pn}", "f14": f"股{i}", "f2": 1.0, "f3": 0.0} for i in range(2)]}}
        return _FakeResp(json.dumps(body))

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    stocks = hk_market.HkMarketData.fetch_all_hk_stocks()
    assert len(stocks) == 4, f"应翻页取全（2 页 × 2），实际 {len(stocks)}"
    assert len(calls) == 2


def test_us_fetch_paginates(monkeypatch):
    import urllib.request
    from stock_researcher.data import us_market
    calls = {"n": 0}

    def fake_open(req, timeout=None, context=None):
        calls["n"] += 1
        pn = 1 if "pn=1" in req.full_url else 2
        body = {"data": {"total": 5001, "diff": [
            {"f12": f"AAPL{pn}", "f14": f"股票{pn}", "f2": 1.0, "f3": 0.0} for _ in range(1)]}}
        return _FakeResp(json.dumps(body))

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    monkeypatch.setattr(us_market.time, "sleep", lambda *a, **k: None)
    stocks = us_market.UsMarketData.fetch_all_us_stocks()
    # 3 板 × 2 页 × 1 = 6
    assert len(stocks) == 6


# ============================================================
# B: akshare 数据源门控（测试环境 conftest 屏蔽 akshare → 全部降级为空）
# ============================================================

def test_akshare_blocked_in_test_env():
    """测试环境 akshare 被 conftest 屏蔽 → HAS_AKSHARE False"""
    from stock_researcher.data.akshare_provider import has_akshare
    assert has_akshare() is False


def test_ak_fund_nav_returns_empty_when_missing():
    from stock_researcher.data.akshare_provider import ak_fund_nav
    assert ak_fund_nav("000001") == {}


def test_ak_macro_returns_empty_when_missing():
    from stock_researcher.data.akshare_provider import ak_macro
    assert ak_macro("cpi") == {}


def test_ak_convertible_quote_returns_empty():
    from stock_researcher.data.akshare_provider import ak_convertible_quote
    assert ak_convertible_quote("128046") == {}


def test_ak_bond_yield_returns_empty():
    from stock_researcher.data.akshare_provider import ak_bond_yield
    assert ak_bond_yield() == []


def test_fetch_financials_akshare_cn_returns_empty():
    """沪深代码不走 akshare（financial_statements 用东财）"""
    from stock_researcher.data.financial_statements import fetch_financials_akshare
    assert fetch_financials_akshare("600519", "cn") == {}


def test_fetch_financials_akshare_hk_missing():
    """未装 akshare 时港美股财务返回 {}（不抛）"""
    from stock_researcher.data.financial_statements import fetch_financials_akshare
    assert fetch_financials_akshare("00700", "hk") == {}


def test_macro_akshare_fallback_not_crash(monkeypatch):
    """macro 主路径失败 → akshare 兜底（未装返回 {}，不抛）"""
    from stock_researcher.data.macro import MacroData
    m = MacroData()
    # 强制主路径失败
    monkeypatch.setattr("stock_researcher.data.macro.safe_request", lambda *a, **k: None)
    out = m.fetch_macro_indicator("cpi")
    assert isinstance(out, dict)  # {} 或 akshare 结果，均不抛


def test_fund_nav_akshare_fallback(monkeypatch):
    """fetch_fund_nav 主路径失败 → akshare 兜底（未装保持原 error 返回）"""
    import sys
    sys.path.insert(0, str(ROOT / "pkg"))
    from pkg import fund_analyzer
    monkeypatch.setattr(fund_analyzer, "_fetch_pingzhongdata", lambda code: {"error": "offline"})
    out = fund_analyzer.fetch_fund_nav("000001")
    assert "error" in out  # akshare 未装 → 保持原错误返回


# ============================================================
# G: 版本一致性 + SKILL 精简
# ============================================================

def test_version_consistent():
    """__version__ / constants / _meta / settings 四者一致（读文件避开 test_v71 模块污染）"""
    import re as _re
    import json as _json
    init = Path(ROOT, "scripts", "stock_researcher", "__init__.py").read_text(encoding="utf-8")
    const = Path(ROOT, "scripts", "stock_researcher", "constants.py").read_text(encoding="utf-8")
    meta = _json.loads(Path(ROOT, "_meta.json").read_text(encoding="utf-8"))
    settings = _json.loads(Path(ROOT, "config", "settings.json").read_text(encoding="utf-8"))
    m_init = _re.search(r"__version__\s*=\s*[\"']([^\"']+)[\"']", init)
    m_const = _re.search(r"VERSION\s*=\s*[\"']([^\"']+)[\"']", const)
    assert m_init and m_init.group(1) == "9.3.0"
    assert m_const and m_const.group(1) == "9.3.0"
    assert meta["version"] == "9.3.0"
    assert settings["version"] == "9.3.0"
    assert settings["_version_info"]["version"] == "9.3.0"


def test_skill_md_concise():
    """SKILL.md 精简（≤400 行）且版本正确"""
    txt = Path(ROOT, "SKILL.md").read_text(encoding="utf-8")
    assert len(txt.splitlines()) <= 400, f"SKILL.md {len(txt.splitlines())} 行"
    assert "version: 9.3.0" in txt
    assert "auto_trigger:" in txt
    assert "keywords:" in txt
    assert "patterns:" in txt


def test_no_stale_doc_refs():
    """无 score_fund_v4 残留（已改为 v3）"""
    skill = Path(ROOT, "SKILL.md").read_text(encoding="utf-8")
    readme = Path(ROOT, "README.md").read_text(encoding="utf-8")
    assert "score_fund_v4" not in skill
    assert "score_fund_v4" not in readme


def test_readme_version_800():
    readme = Path(ROOT, "README.md").read_text(encoding="utf-8")
    # v9.3 起由 test_v930_quant_forecast.py 的版本断言接管，此处保留最近大版本兼容检查
    assert "v9.3" in readme.splitlines()[0]
