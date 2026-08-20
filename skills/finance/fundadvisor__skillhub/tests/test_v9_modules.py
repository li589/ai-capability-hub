# -*- coding: utf-8 -*-
"""v9.0.0 模块A/B 测试：数据稳定性 + 三件套完整实现（离线 mock）"""

import ast
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "data_collection"))


# ============================================================
# A: 沙箱 / 解析容错 / 占位识别
# ============================================================

def test_validate_file_sandbox():
    import mcp_server
    # 合法路径（DATA_DIR 内）应返回 None；穿越应拒绝
    ok = mcp_server._validate_file(str(ROOT / "data" / "x.png"), (".png",))
    assert ok is None or "格式" in str(ok)
    bad = mcp_server._validate_file(str(ROOT / "data" / ".." / "secret.png"), (".png",))
    assert bad is not None


def test_validate_url_whitelist():
    import mcp_server
    assert mcp_server._validate_url("https://fund.eastmoney.com/001924.html") is None
    assert mcp_server._validate_url("https://evil.com/x") is not None
    assert mcp_server._validate_url("file:///etc/passwd") is not None


def test_to_float_robust():
    import mcp_server
    assert mcp_server._to_float("abc") == 0.0
    assert mcp_server._to_float("1,234.56") == 1234.56
    assert mcp_server._to_float(None) == 0.0


def test_should_update_placeholder(monkeypatch, tmp_path):
    from scripts.maintenance.auto_updater import AutoUpdater
    # 合成空（占位）数据文件 → should_update True
    for fname in ("fund_managers_distilled.json", "fund_companies_distilled.json",
                  "fund_products.json"):
        (tmp_path / fname).write_text('{"_f":[],"c":[],"m":{}}', encoding="utf-8")
    au = AutoUpdater(data_dir=tmp_path)
    ok, msg = au.should_update()
    assert ok is True
    assert "重建" in msg or "为空" in msg


def test_should_update_fresh(monkeypatch, tmp_path):
    from scripts.maintenance.auto_updater import AutoUpdater
    # 合成新鲜数据（count>0, last_update=今天）→ should_update False
    today = datetime.now().strftime('%Y-%m-%d')
    meta = {"m": {"count": 10, "last_update": today}}
    (tmp_path / "fund_managers_distilled.json").write_text(
        json.dumps(meta), encoding="utf-8")
    (tmp_path / "fund_companies_distilled.json").write_text(
        json.dumps(meta), encoding="utf-8")
    (tmp_path / "fund_products.json").write_text(json.dumps(meta), encoding="utf-8")
    au = AutoUpdater(data_dir=tmp_path)
    ok, _ = au.should_update()
    assert ok is False


# ============================================================
# B1: 回测四策略（mock 净值）
# ============================================================

class _FakeNavCache:
    def get_nav_series(self, code, start, end):
        base = {"F1": 1.0, "F2": 1.05, "F3": 0.95, "F4": 1.1, "000300": 1.0}
        n = 260
        drift = 0.001 if code in ("F2", "F4") else -0.0002
        return [base.get(code, 1.0) * (1 + 0.0005 * i + drift) for i in range(n)]


@pytest.fixture
def bt_engine():
    from scripts.analysis.backtest_engine import BacktestEngine
    engine = BacktestEngine.__new__(BacktestEngine)
    engine.nav_cache = _FakeNavCache()
    engine._batch_get_nav = lambda codes, start, end: {
        c: _FakeNavCache().get_nav_series(c, start, end) for c in codes}
    return engine


@pytest.mark.parametrize("strat,params", [
    ("momentum", {"lookback": 3, "top_k": 2}),
    ("mean_reversion", {"top_k": 2}),
    ("risk_parity", {"vol_window": 30}),
    ("equity_bond_rotation", {"top_k": 2}),
])
def test_backtest_strategies_run(bt_engine, strat, params):
    r = bt_engine.run_strategy_backtest(
        strat, ["F1", "F2", "F3", "F4"], "2026-01-01", "2026-12-31",
        params=params, benchmark_code="000300")
    assert r.degraded is False, f"{strat} 应真实模拟而非降级"
    assert isinstance(r.total_return_pct, float)
    assert isinstance(r.sharpe_ratio, float)
    assert r.total_trades >= 0


def test_backtest_mdd_numeric(bt_engine):
    """v9.0 修复: max_drawdown 应为数值非字符串"""
    r = bt_engine.run_strategy_backtest(
        "momentum", ["F1", "F2", "F3", "F4"], "2026-01-01", "2026-12-31",
        params={"top_k": 2}, benchmark_code="000300")
    assert isinstance(r.max_drawdown_pct, float)


def test_backtest_empty_degraded():
    from scripts.analysis.backtest_engine import BacktestEngine
    engine = BacktestEngine.__new__(BacktestEngine)
    engine.nav_cache = _FakeNavCache()
    engine._batch_get_nav = lambda *a, **k: {}
    r = engine.run_strategy_backtest("momentum", ["F1"], "2026-01-01", "2026-12-31",
                                     params={}, benchmark_code="000300")
    assert r.degraded is True


# ============================================================
# B2: 因子 value/sentiment 穿透 + degraded
# ============================================================

def _make_factor_dir(tmp_path, with_val=True):
    (tmp_path / "holdings_database.json").write_text(json.dumps({"holdings": [
        {"fund_code": "000001", "stock_code": "600519", "weight": 50},
        {"fund_code": "000001", "stock_code": "000858", "weight": 50},
    ], "m": {}}), encoding="utf-8")
    (tmp_path / "stock_valuations.json").write_text(json.dumps(
        {"items": [{"code": "600519", "pe": 30, "pb": 8},
                   {"code": "000858", "pe": 20, "pb": 6}], "m": {}}) if with_val
        else json.dumps({"items": [], "m": {}}), encoding="utf-8")
    (tmp_path / "external_data.json").write_text(json.dumps({"ratings": [
        {"fund_code": "000001", "avg_star": 4.5, "profit_probability": 80,
         "source_count": 3}], "m": {}}), encoding="utf-8")
    (tmp_path / "fund_managers_distilled.json").write_text(
        json.dumps({"_f": [], "c": [], "m": {}}), encoding="utf-8")
    (tmp_path / "fund_products.json").write_text(
        json.dumps({"_f": [], "c": [], "m": {}}), encoding="utf-8")


def test_factor_value_sentiment_penetrate(tmp_path):
    from scripts.analysis.factor_engine import FactorEngine
    _make_factor_dir(tmp_path)
    fe = FactorEngine(data_dir=tmp_path)
    exp = fe.compute_factor_exposures("000001")
    assert "value" in exp["factors"]
    assert "sentiment" in exp["factors"]
    # 有估值/评级数据 → 不 degraded
    assert exp["degraded"] is False
    # 高 PE 股票 → 价值分应低于中性（<0.5）
    assert exp["factors"]["value"] < 0.5


def test_factor_value_degraded_fallback(tmp_path):
    from scripts.analysis.factor_engine import FactorEngine
    _make_factor_dir(tmp_path, with_val=False)
    fe = FactorEngine(data_dir=tmp_path)
    exp = fe.compute_factor_exposures("000001")
    assert "value" in exp["degraded_factors"]
    assert exp["notes"], "无数据时应有 notes"
    assert 0 <= exp["factors"]["value"] <= 1


def test_factor_attribution_uses_type_benchmark(tmp_path):
    from scripts.analysis.factor_engine import FactorEngine
    _make_factor_dir(tmp_path)
    fe = FactorEngine(data_dir=tmp_path)
    att = fe.factor_attribution("000001")
    assert att["attribution"]
    assert att["unexplained_alpha"] >= 0


# ============================================================
# B3: 情景五模板 + fund_swap 费率复用
# ============================================================

def _scenario_dir(tmp_path):
    (tmp_path / "fund_products.json").write_text(json.dumps({"items": [
        {"code": "000001", "type": "股票型"}, {"code": "000002", "type": "QDII"},
        {"code": "000003", "type": "债券型"}], "m": {}}), encoding="utf-8")


def test_scenario_all_templates_run(tmp_path):
    from scripts.analysis.scenario_simulator import ScenarioSimulator
    _scenario_dir(tmp_path)
    sim = ScenarioSimulator(data_dir=tmp_path)
    holdings = [
        {"fund_code": "000001", "fund_name": "科技先锋", "weight": 40, "amount": 40000},
        {"fund_code": "000002", "fund_name": "全球QDII", "weight": 30, "amount": 30000},
        {"fund_code": "000003", "fund_name": "稳健债基", "weight": 30, "amount": 30000},
    ]
    r = sim.run_scenarios(holdings)
    assert r["count"] == 5, f"5 模板都应运行，实际 {r['count']}"
    for s in r["scenarios"]:
        assert "total_impact_pct" in s
        assert "severity" in s


def test_scenario_sector_boom(tmp_path):
    from scripts.analysis.scenario_simulator import ScenarioSimulator
    _scenario_dir(tmp_path)
    sim = ScenarioSimulator(data_dir=tmp_path)
    r = sim.sector_boom([{"fund_code": "000001", "fund_name": "科技先锋", "weight": 100,
                          "amount": 100000}], sector="科技", sector_return=0.3, other_return=0.05)
    assert r["total_impact_pct"] > 20  # 科技基金全命中 → ~30%


def test_fund_swap_uses_fee_calculator(tmp_path):
    from scripts.analysis.scenario_simulator import ScenarioSimulator
    _scenario_dir(tmp_path)
    sim = ScenarioSimulator(data_dir=tmp_path)
    holdings = [
        {"fund_code": "000003", "fund_name": "稳健债基", "weight": 50, "amount": 50000},
    ]
    r = sim.fund_swap(holdings, "000003", "000001")
    assert "sell" in r and "buy" in r
    # v9.0 修复: 买入金额 = 卖出净额（不双重扣费）
    assert r["buy"]["amount"] <= 50000 + 1


# ============================================================
# C: db_format / monthly_updater 零依赖 / first_workday
# ============================================================

def test_db_format_columnar_roundtrip(tmp_path):
    from scripts.data_collection.db_format import write_managers_distilled, update_meta_append
    p = tmp_path / "m.json"
    write_managers_distilled(p, [{"code": "A001", "name": "张三"}],
                             meta={"updated": "2026-08-10"})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["_f"][0] == "code"
    assert data["c"][0] == ["A001"]


def test_update_meta_append_preserves_history(tmp_path):
    from scripts.data_collection.db_format import update_meta_append
    p = tmp_path / "meta.json"
    p.write_text(json.dumps({"history": [{"t": 1}], "update_count": 1}), encoding="utf-8")
    update_meta_append(p, {"time": "2026-08-10T00:00:00", "type": "full"})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["history"]) == 2  # 追加而非覆写
    assert data["update_count"] == 2


def test_monthly_updater_top_level_stdlib_only():
    """monthly_updater 顶层 import 应全 stdlib（零依赖可导入）"""
    src = Path(ROOT / "scripts" / "maintenance" / "monthly_updater.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module not in ("dateutil", "requests", "bs4", "akshare"), \
                f"顶层非 stdlib import: {node.module}"
        elif isinstance(node, ast.Import):
            for a in node.names:
                assert a.name not in ("requests", "bs4", "akshare", "dateutil"), \
                    f"顶层非 stdlib import: {a.name}"


def test_get_first_workday_stdlib():
    from scripts.maintenance.monthly_updater import MonthlyUpdater
    m = MonthlyUpdater()
    # 2026-08-01 是周六 → 首个工作日 8-03（周一）
    assert m.get_first_workday_of_month(2026, 8).day == 3


def test_nav_cache_warm_fetch_online(tmp_path, monkeypatch):
    """nav_cache.warm_cache 在线拉取（mock urllib）"""
    from scripts.data_collection.nav_cache import NavCache
    cache = NavCache(str(tmp_path / "nav.db"))
    calls = {"n": 0}

    def fake_open(req, timeout=None):
        calls["n"] += 1
        body = b'var Data_netWorthTrend = [{"x": 1750000000000, "y": 1.2}, {"x": 1750086400000, "y": 1.21}];'
        return _FakeResp(body)

    class _FakeResp:
        def __init__(self, data):
            self._data = data

        def read(self):
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    result = cache.warm_cache(["000001"], force_fetch=True)
    assert calls["n"] >= 1
    assert result.get("000001", 0) >= 2
