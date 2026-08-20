# -*- coding: utf-8 -*-
"""v5.0.0 模块D：analyzer 重写测试（离线，无网络）"""

import json
from pathlib import Path

import pytest

from scripts.analyzer import (
    calculate_risk_metrics, analyze_investment_style, suggest_similar_products,
    generate_portfolio_replication, suggest_alternatives, analyze_product,
    _normalize_series, _pct_changes, _max_drawdown,
)


def _synthetic_series(n=120, start=1.0, step=0.001):
    return [{"date": f"d{i}", "nav": start + step * i} for i in range(n)]


# ============================================================
# 1. 真实风险指标
# ============================================================

def test_risk_metrics_returns_full_keys():
    m = calculate_risk_metrics(_synthetic_series())
    for k in ["annualized_return", "annualized_volatility", "max_drawdown",
              "sharpe_ratio", "calmar_ratio", "positive_days", "total_days"]:
        assert k in m, f"缺 {k}"


def test_risk_metrics_positive_series():
    """严格上涨序列：收益为正、回撤近 0、正收益天数 = 总天数"""
    m = calculate_risk_metrics(_synthetic_series(120, step=0.001))
    assert m["annualized_return"] > 0
    assert m["max_drawdown"] < 0.01
    assert m["positive_days"] == m["total_days"]


def test_risk_metrics_insufficient_data():
    assert calculate_risk_metrics([{"nav": 1.0}, {"nav": 1.1}])["insufficient_data"] is True


def test_risk_metrics_sharpe_zero_when_flat():
    """平坦序列波动为 0 → 夏普为 0 而非除零"""
    flat = [{"date": f"d{i}", "nav": 1.0} for i in range(60)]
    m = calculate_risk_metrics(flat)
    assert m["sharpe_ratio"] == 0.0
    assert m["annualized_volatility"] == 0.0


def test_risk_metrics_drawdown_detected():
    """先涨后大跌 → 检测到显著回撤"""
    vals = [1.0]
    for i in range(1, 80):
        vals.append(1.0 + 0.005 * i)  # 上涨
    vals += [vals[-1] * 0.7]  # 单日 -30%
    m = calculate_risk_metrics([{"nav": v} for v in vals])
    assert m["max_drawdown"] > 0.25


def test_risk_metrics_numeric_list_input():
    """纯数值列表入参"""
    m = calculate_risk_metrics([1.0 + 0.01 * i for i in range(60)])
    assert m["annualized_return"] > 0


def test_risk_metrics_legacy_dict_estimate():
    m = calculate_risk_metrics({"1year": 15.67, "3year": 50.0})
    assert m.get("estimate") is True
    assert m.get("annual_return") == pytest.approx(0.1567)


# ============================================================
# 2. 辅助函数
# ============================================================

def test_normalize_series_filters_invalid():
    out = _normalize_series([{"nav": 1.0}, {"nav": None}, {"nav": "abc"}, {"nav": 2.0}])
    assert out == [1.0, 2.0]


def test_max_drawdown():
    assert _max_drawdown([1.0, 1.2, 0.9, 1.1]) == pytest.approx(0.25)


# ============================================================
# 3. 投资风格
# ============================================================

def test_style_concentration():
    stocks = [{"code": f"60000{i}", "weight": w} for i, w in enumerate([20, 15, 12, 10, 8, 3, 2])]
    style = analyze_investment_style({"stocks": stocks}, {"1year": 20})
    assert "集中" in style  # CR5 = 65 ≥ 50


def test_style_diversified():
    stocks = [{"code": f"60000{i}", "weight": 3} for i in range(10)]
    style = analyze_investment_style({"stocks": stocks}, {"1year": 8})
    assert "分散" in style


def test_style_growth_vs_stable():
    g = analyze_investment_style({"stocks": []}, {"1year": 40})
    assert "成长" in g
    s = analyze_investment_style({"stocks": []}, {"1year": 2})
    assert "稳健" in s


def test_style_board_detection():
    stocks = [{"code": "688111", "weight": 5}, {"code": "600519", "weight": 5}]
    style = analyze_investment_style({"stocks": stocks}, None)
    assert "科创板" in style or "沪主板" in style


# ============================================================
# 4. 组合复刻
# ============================================================

def test_replication_fallback_mapping():
    rep = generate_portfolio_replication({
        "product_name": "测试基金",
        "holdings": {"stocks": [{"code": "600519", "name": "贵州茅台", "weight": 5}]},
        "historical_nav": {"1year": 15},
    })
    assert rep["allocation"][0]["mapping_source"] == "fallback"
    assert rep["allocation"][0]["alternative"] == suggest_alternatives("贵州茅台")


def test_replication_data_driven_mapping():
    candidates = [
        {"code": "000858", "name": "五粮液", "weight": 4.5},
        {"code": "600036", "name": "招商银行", "weight": 9.0},
        {"code": "300750", "name": "宁德时代", "weight": 3.0},
    ]
    rep = generate_portfolio_replication({
        "product_name": "白酒基金",
        "holdings": {"stocks": [{"code": "600519", "name": "贵州茅台", "weight": 5.2}]},
        "historical_nav": {"1year": 15},
    }, candidates=candidates)
    item = rep["allocation"][0]
    assert item["mapping_source"] == "data-driven"
    assert item["alternative"][0] == "五粮液"  # 同沪/深主板 + 权重接近


def test_replication_similar_products_present():
    rep = generate_portfolio_replication({
        "product_name": "x", "holdings": {"stocks": []}, "historical_nav": {},
    })
    assert "similar_products" in rep
    assert rep["total_suggestion"]


# ============================================================
# 5. 相似推荐 & 报告
# ============================================================

def test_suggest_similar_products_db_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.analyzer.SKILL_DATA_DIR", tmp_path)
    out = suggest_similar_products({"product_type": "混合型", "historical_nav": {}})
    assert out and ("note" in out[0] or "error" in out[0])


def test_suggest_similar_products_orders_by_distance(tmp_path, monkeypatch):
    db = tmp_path / "fund_managers_distilled.json"
    db.write_text(json.dumps({"managers": [
        {"name": "近", "fund_type": "混合型", "annual_return": 15.0,
         "volatility": 5.0, "max_drawdown": 10.0},
        {"name": "远", "fund_type": "债券型", "annual_return": -40.0,
         "volatility": 90.0, "max_drawdown": 80.0},
    ]}), encoding="utf-8")
    monkeypatch.setattr("scripts.analyzer.SKILL_DATA_DIR", tmp_path)
    out = suggest_similar_products({
        "product_type": "混合型",
        "historical_nav": [{"nav": 1.0 + 0.001 * i} for i in range(60)],
    }, limit=2)
    assert out[0]["name"] == "近"  # 距离更近排前


def test_analyze_product_report_generation():
    report = analyze_product({
        "product_name": "测试", "product_code": "0001", "product_type": "混合型",
        "company": "公司", "manager": "经理", "risk_level": "中",
        "historical_nav": {"1year": 12},
    })
    assert "【产品分析报告】" in report
    assert "风险指标" in report
