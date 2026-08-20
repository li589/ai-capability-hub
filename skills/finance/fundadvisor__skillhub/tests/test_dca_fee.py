"""test_dca_fee.py — v7.1 新增模块：定投规划器 + 调仓成本测算器"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


# ─── 定投规划器 ─────────────────────────────────────────

def test_plan_dca_basic_split_sums_to_monthly():
    from analysis.dca_planner import plan_dca
    p = plan_dca(2000, risk_level="平衡型", horizon_years=5, goal="教育")
    assert "error" not in p
    total = sum(v["monthly"] for v in p["monthly_split"].values())
    assert abs(total - 2000) < 1.0  # 四舍五入误差 ≤1 元
    assert p["risk_level"] == "平衡型"
    assert p["glide_path"] is not None  # 教育场景应有下滑曲线


def test_plan_dca_answers_override_risk_level():
    from analysis.dca_planner import plan_dca
    p = plan_dca(1000, answers=[0] * 10, risk_level="进取型")
    assert p["risk_level"] == "保守型"  # 全 0 问卷 -> 保守型，覆盖显式参数


def test_plan_dca_projection_consistency():
    from analysis.dca_planner import plan_dca
    p = plan_dca(1000, risk_level="稳健型", horizon_years=3)
    rows = p["projection"]["scenarios"]
    assert len(rows) == 3
    for r in rows:
        assert r["invested"] > 0
        # 三档终值有序：悲观 < 中性 < 乐观
        assert r["pessimistic"] < r["expected"] < r["optimistic"]
    # 中性情景终值应大于累计投入（正收益假设下）
    assert rows[-1]["expected"] > rows[-1]["invested"]


def test_plan_dca_invalid_input():
    from analysis.dca_planner import plan_dca
    assert "error" in plan_dca(0, risk_level="平衡型")
    assert "error" in plan_dca(1000, risk_level="不存在型")


def test_fv_of_dca_zero_rate():
    from analysis.dca_planner import _fv_of_dca
    assert _fv_of_dca(1000, 0.0, 12) == 12000
    assert _fv_of_dca(1000, 0.05, 0) == 0.0


# ─── 调仓成本测算器 ──────────────────────────────────────

def test_redemption_fee_tiers():
    from analysis.fee_calculator import redemption_fee
    # <7 天惩罚性费率
    assert redemption_fee(10000, 5)["rate"] == 0.015
    assert redemption_fee(10000, 5)["punitive"] is True
    # 30-365 天 0.5%
    assert redemption_fee(10000, 200)["rate"] == 0.005
    # 满 2 年免赎回费
    assert redemption_fee(10000, 800)["rate"] == 0.0
    assert redemption_fee(10000, 800)["fee"] == 0.0
    # 货币型免赎回费
    assert redemption_fee(10000, 1, fund_type="货币型")["fee"] == 0.0


def test_subscription_fee_discount():
    from analysis.fee_calculator import subscription_fee
    r = subscription_fee(10000)
    assert abs(r["effective_rate"] - 0.0015) < 1e-9  # 1.5% × 0.1 折
    assert r["fee"] == 15.0


def test_rebalance_cost_and_advice():
    from analysis.fee_calculator import estimate_rebalance_cost
    r = estimate_rebalance_cost(
        sells=[{"name": "A", "amount": 50000, "holding_days": 200},
               {"name": "B", "amount": 30000, "holding_days": 5}],
        buys=[{"name": "C", "amount": 80000}],
    )
    # 50000×0.5% + 30000×1.5% + 80000×0.15% = 250+450+120 = 820
    assert r["total_fee"] == 820.0
    assert any("惩罚性费率" in a for a in r["advice"])
    assert r["cost_pct"] > 0


def test_breakeven_months():
    from analysis.fee_calculator import breakeven_months
    assert breakeven_months(1.025, 3.0)["breakeven_months"] == 4.1
    # 超额为负 -> 永远回不了本
    assert breakeven_months(1.0, -1.0)["breakeven_months"] is None
