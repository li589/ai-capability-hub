#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v9.2 定期报告解读测试（离线，纯逻辑，不联网）。

覆盖：报告期解析 / 同比环比计算 / 亮点风险规则引擎 / 结论 / markdown 报告 / 降级。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from stock_researcher.research.financial_report import (
    FinancialReportInterpreter,
    interpret_report,
    _resolve_period,
    _shift_date,
    _pct_change,
    _period_label,
)


# ── mock 数据 ──────────────────────────────────────────
def _mock_growth():
    """高增长公司：营收/利润双增、毛利率改善、现金流充裕、去杠杆。"""
    return {
        "code": "600519",
        "income": [
            {"report_date": "2024-12-31", "TOTAL_OPERATE_INCOME": 1500e8, "PARENT_NETPROFIT": 180e8,
             "GROSS_MARGIN": 55.0, "BASIC_EPS": 60.0, "ROE": 30.0},
            {"report_date": "2024-09-30", "TOTAL_OPERATE_INCOME": 1100e8, "PARENT_NETPROFIT": 130e8,
             "GROSS_MARGIN": 54.0, "BASIC_EPS": 45.0, "ROE": 22.0},
            {"report_date": "2023-12-31", "TOTAL_OPERATE_INCOME": 1300e8, "PARENT_NETPROFIT": 120e8,
             "GROSS_MARGIN": 52.0, "BASIC_EPS": 50.0, "ROE": 28.0},
            {"report_date": "2023-09-30", "TOTAL_OPERATE_INCOME": 950e8, "PARENT_NETPROFIT": 85e8,
             "GROSS_MARGIN": 51.0, "BASIC_EPS": 33.0, "ROE": 20.0},
        ],
        "balance": [
            {"report_date": "2024-12-31", "DEBT_ASSET_RATIO": 20.0},
            {"report_date": "2023-12-31", "DEBT_ASSET_RATIO": 25.0},
        ],
        "cashflow": [
            {"report_date": "2024-12-31", "NETCASH_OPERATE": 200e8},
            {"report_date": "2023-12-31", "NETCASH_OPERATE": 140e8},
        ],
    }


def _mock_decline():
    """承压公司：增收不增利/毛利率下滑/现金流差/加杠杆。"""
    return {
        "code": "000001",
        "income": [
            {"report_date": "2024-12-31", "TOTAL_OPERATE_INCOME": 900e8, "PARENT_NETPROFIT": 60e8,
             "GROSS_MARGIN": 30.0, "BASIC_EPS": 1.0, "ROE": 5.0},
            {"report_date": "2023-12-31", "TOTAL_OPERATE_INCOME": 1000e8, "PARENT_NETPROFIT": 80e8,
             "GROSS_MARGIN": 35.0, "BASIC_EPS": 1.3, "ROE": 8.0},
        ],
        "balance": [
            {"report_date": "2024-12-31", "DEBT_ASSET_RATIO": 60.0},
            {"report_date": "2023-12-31", "DEBT_ASSET_RATIO": 55.0},
        ],
        "cashflow": [
            {"report_date": "2024-12-31", "NETCASH_OPERATE": 10e8},
            {"report_date": "2023-12-31", "NETCASH_OPERATE": 30e8},
        ],
    }


# ── 工具函数 ──────────────────────────────────────────
def test_shift_date_yoy_qoq():
    assert _shift_date("2024-12-31", 12) == "2023-12-31"
    assert _shift_date("2024-03-31", 12) == "2023-03-31"
    assert _shift_date("2024-12-31", 3) == "2024-09-30"
    assert _shift_date("2024-03-31", 3) == "2023-12-31"
    assert _shift_date("bad-date", 12) == ""


def test_pct_change_handles_zero_base():
    assert _pct_change(150, 100) == 50.0
    assert _pct_change(90, 100) == -10.0
    assert _pct_change(100, 0) is None, "base=0 不应编造百分比"
    assert _pct_change(100, None) is None


def test_resolve_period():
    income = [{"report_date": "2024-12-31"}, {"report_date": "2024-09-30"},
              {"report_date": "2023-12-31"}]
    assert _resolve_period(income, None) == "2024-12-31", "None 应取最新"
    assert _resolve_period(income, "2024") == "2024-12-31", "年份应映射到年报"
    assert _resolve_period(income, "2024Q3") == "2024-09-30"
    assert _resolve_period(income, "2024-12-31") == "2024-12-31"
    assert _resolve_period([], None) == ""


def test_period_label():
    assert _period_label("2024-12-31") == "2024 年报"
    assert _period_label("2024-06-30") == "2024 中报"
    assert _period_label("2024-09-30") == "2024 三季报"
    assert _period_label("2024-03-31") == "2024 一季报"


# ── 解读逻辑 ──────────────────────────────────────────
def test_interpret_growth_company():
    r = FinancialReportInterpreter().analyze(_mock_growth(), code="600519", period="2024")
    assert r.data_mode == "ok"
    assert r.period == "2024-12-31"
    m = r.metrics
    assert m["revenue_yoy"] == 15.38, f"营收同比应 +15.38%，实际 {m['revenue_yoy']}"
    assert m["net_profit_yoy"] == 50.0, f"利润同比应 +50%，实际 {m['net_profit_yoy']}"
    assert m["revenue_qoq"] == 36.36, f"环比应 +36.36%，实际 {m['revenue_qoq']}"
    assert m["gross_margin_change"] == 3.0
    assert m["ocf_to_profit"] == 1.11
    assert m["debt_ratio_change"] == -5.0

    assert len(r.highlights) >= 4, f"高增长公司应有≥4条亮点，实际 {r.highlights}"
    assert r.risks == [], f"高增长公司不应有风险，实际 {r.risks}"
    assert r.verdict == "高增长", f"verdict 应为高增长，实际 {r.verdict}"


def test_interpret_decline_company():
    r = FinancialReportInterpreter().analyze(_mock_decline(), code="000001", period="2024")
    assert r.data_mode == "ok"
    m = r.metrics
    assert m["revenue_yoy"] == -10.0
    assert m["net_profit_yoy"] == -25.0
    assert m["gross_margin_change"] == -5.0
    assert m["ocf_to_profit"] == 0.17
    assert m["debt_ratio_change"] == 5.0

    assert len(r.risks) >= 4, f"承压公司应有≥4条风险，实际 {r.risks}"
    assert r.highlights == [], f"承压公司不应有亮点，实际 {r.highlights}"
    assert r.verdict == "承压", f"verdict 应为承压，实际 {r.verdict}"


def test_interpret_insufficient_data():
    r = FinancialReportInterpreter().analyze({}, code="600519")
    assert r.data_mode == "insufficient"
    assert "无可用" in r.conclusion


def test_format_report_markdown():
    r = FinancialReportInterpreter().analyze(_mock_growth(), code="600519", period="2024")
    txt = FinancialReportInterpreter().format_report(r)
    assert "# 定期报告解读" in txt
    assert "2024 年报" in txt
    assert "## 一、核心指标" in txt
    assert "## 二、业绩亮点" in txt
    assert "## 三、风险提示" in txt
    assert "## 四、结论" in txt
    assert "高增长" in txt
    assert "无显著风险点" in txt, "无风险时应显示占位提示"

    # 承压公司：无亮点时应显示占位提示
    r2 = FinancialReportInterpreter().analyze(_mock_decline(), code="000001", period="2024")
    txt2 = FinancialReportInterpreter().format_report(r2)
    assert "无显著亮点" in txt2


def test_convenience_and_lazy_export():
    # interpret_report 便捷函数 + 顶层懒加载导出
    assert callable(interpret_report)
    from stock_researcher import interpret_report as top_interpret
    from stock_researcher import FinancialReportInterpreter as TopCls
    from stock_researcher import format_report as top_format
    assert callable(top_interpret)
    assert callable(top_format)
    # 顶层懒加载导出应返回正确的类（比对名称与归属，避免与其它测试的模块 stub 产生重复类对象导致 is 误判）
    assert TopCls.__name__ == "FinancialReportInterpreter"
    assert TopCls.__module__.endswith(".financial_report")
    assert callable(TopCls)


if __name__ == "__main__":
    for fn in [test_shift_date_yoy_qoq, test_pct_change_handles_zero_base,
               test_resolve_period, test_period_label,
               test_interpret_growth_company, test_interpret_decline_company,
               test_interpret_insufficient_data, test_format_report_markdown,
               test_convenience_and_lazy_export]:
        fn()
        print(f"  ✅ {fn.__name__}")
    print("\n  🎉 All v9.2 financial_report tests passed!")
