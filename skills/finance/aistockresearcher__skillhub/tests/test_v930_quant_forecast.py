#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v9.3 量化预测增强测试（离线，纯逻辑，不联网）。

覆盖：
  - 历史形态匹配预测（pattern_predictor）：降级 / 确定性 / 排序 / 分位 / 标签
  - 基金量化增强：尾部风险 / 回撤恢复 / 稳定性 / NAV 预测 / 便捷函数回归
  - 期货量化增强：置信区间 / 波动率预测 / 仓位建议 / 展期收益
  - quant_analyze_asset 接线 + 顶层导出 + 版本号
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from stock_researcher.quantitative.pattern_predictor import (
    HistoricalPatternPredictor,
    quick_pattern_forecast,
    pattern_direction_label,
)
from stock_researcher.funds.fund_quant_analyzer import (
    FundQuantAnalyzer,
    FundPerformance,
    analyze_fund_performance,
)
from stock_researcher.quantitative.futures_analyzer import FuturesAnalyzer
from stock_researcher.quantitative.asset_quant import quant_analyze_asset


# ── 确定性样本 ──────────────────────────────────────────
def _sine_prices(n=120, drift=0.001, amp=0.03, period=5.0):
    """趋势 + 正弦震荡：形态会周期性重演，保证能匹配到相似窗口。"""
    return [100 * (1 + drift * i) * (1 + amp * math.sin(i / period))
            for i in range(n)]


def _trend_nav(days=400, daily=0.0006, vol=0.008, seed=7):
    random.seed(seed)
    nav = [1.0]
    for _ in range(days):
        nav.append(nav[-1] * (1 + random.gauss(daily, vol)))
    return nav


# ══ 一、历史形态匹配预测 ══════════════════════════════
class TestPatternPredictor:
    def test_insufficient_data(self):
        r = quick_pattern_forecast([100, 101, 102], horizon=5)
        assert r["data_mode"] == "insufficient"
        assert r["confidence"] == 0.0
        assert r["prob_up"] == 50.0, "无数据时不应编造方向"

    def test_deterministic(self):
        prices = _sine_prices()
        r1 = quick_pattern_forecast(prices, horizon=5)
        r2 = quick_pattern_forecast(prices, horizon=5)
        assert r1 == r2, "纯逻辑预测必须可复现"

    def test_basic_forecast_structure(self):
        r = quick_pattern_forecast(_sine_prices(), horizon=5)
        assert r["data_mode"] == "ok"
        assert r["n_matches"] >= 1
        assert 0 <= r["prob_up"] <= 100
        assert 0 <= r["confidence"] <= 100
        assert r["p_low"] <= r["p_high"]
        assert r["current_price"] == round(_sine_prices()[-1], 4)

    def test_top_k_limit_and_sort(self):
        p = HistoricalPatternPredictor(window=20, top_k=3)
        r = p.predict(_sine_prices(150), horizon=5)
        assert len(r["matches"]) <= 3
        sims = [m["similarity"] for m in r["matches"]]
        assert sims == sorted(sims, reverse=True), "匹配应按相似度降序"
        assert all(0 <= s <= 1 for s in sims)

    def test_matches_forward_pct_consistent(self):
        r = quick_pattern_forecast(_sine_prices(), horizon=5)
        fwds = sorted(m["forward_pct"] for m in r["matches"])
        # p_low/p_high 来自 matches 的 forward 收益分位
        assert r["p_low"] >= fwds[0] - 0.01
        assert r["p_high"] <= fwds[-1] + 0.01

    def test_no_match_honest_fallback(self):
        # 恒定价格 → 收益序列全 0 → 形态窗口方差为 0 → 无有效匹配
        flat = [100.0] * 120
        r = HistoricalPatternPredictor().predict(flat, horizon=5)
        assert r["data_mode"] == "no_match"
        assert r["n_matches"] == 0

    def test_direction_label(self):
        up = {"data_mode": "ok", "predicted_pct": 3.0, "confidence": 60}
        down = {"data_mode": "ok", "predicted_pct": -3.0, "confidence": 60}
        flat = {"data_mode": "ok", "predicted_pct": 0.2, "confidence": 60}
        lowconf = {"data_mode": "ok", "predicted_pct": 5.0, "confidence": 10}
        assert pattern_direction_label(up) == "看涨"
        assert pattern_direction_label(down) == "看跌"
        assert pattern_direction_label(flat) == "震荡"
        assert pattern_direction_label(lowconf) == "震荡", "低置信度不应喊方向"
        assert pattern_direction_label({"data_mode": "insufficient"}) == "数据不足"

    def test_window_param_guard(self):
        p = HistoricalPatternPredictor(window=2, top_k=0)
        assert p.window >= 5 and p.top_k >= 1, "参数应有安全下限"


# ══ 二、基金量化增强 ══════════════════════════════════
class TestFundQuantV93:
    def _perf(self):
        nav = _trend_nav()
        bm = [random.gauss(0.0003, 0.01) for _ in range(len(nav) - 1)]
        return FundQuantAnalyzer().analyze_fund(nav, bm, fund_name="v93基金")

    def test_new_fields_exist_and_finite(self):
        p = self._perf()
        for f in ("treynor_ratio", "skewness", "excess_kurtosis",
                  "var_5pct", "stability"):
            assert math.isfinite(getattr(p, f)), f"字段 {f} 应有限"
        assert isinstance(p.recovery_days, int) and p.recovery_days >= 0
        assert isinstance(p.dd_recovered, bool)
        assert 0 <= p.stability <= 100
        assert p.var_5pct <= 0, "5% 分位 VaR 应为负值（亏损方向）"

    def test_insufficient_returns_defaults(self):
        p = FundQuantAnalyzer().analyze_fund([1.0, 1.1], fund_name="短")
        assert p.rating == "C"
        assert p.treynor_ratio == 0.0 and p.stability == 50.0
        assert p.dd_recovered is True

    def test_skew_kurtosis_math(self):
        fqa = FundQuantAnalyzer()
        sym = [-0.02, -0.01, 0.01, 0.02] * 25
        skew, kurt = fqa._skew_kurt(sym)
        assert abs(skew) < 0.2, "对称分布偏度应接近 0"
        crashy = [0.001] * 99 + [-0.2]
        skew2, kurt2 = fqa._skew_kurt(crashy)
        assert skew2 < -1, "单日暴跌应显著负偏"
        assert kurt2 > 3, "单日暴跌应肥尾"

    def test_drawdown_recovery_recovered(self):
        fqa = FundQuantAnalyzer()
        rec = fqa._drawdown_recovery([1.0, 1.2, 0.9, 1.25])
        assert rec == {"recovered": True, "recovery_days": 1}

    def test_drawdown_recovery_unrecovered(self):
        fqa = FundQuantAnalyzer()
        rec = fqa._drawdown_recovery([1.0, 1.2, 0.9, 1.0])
        assert rec["recovered"] is False
        assert rec["recovery_days"] == 1, "谷底至今未收复，应报已持续天数"

    def test_drawdown_recovery_no_drawdown(self):
        fqa = FundQuantAnalyzer()
        rec = fqa._drawdown_recovery([1.0, 1.1, 1.2, 1.3])
        assert rec == {"recovered": True, "recovery_days": 0}

    def test_forecast_nav_uptrend(self):
        nav = [1.0]
        for _ in range(100):
            nav.append(nav[-1] * 1.002)  # 稳定 +0.2%/日
        fc = FundQuantAnalyzer().forecast_nav(nav, days=5)
        assert fc["data_mode"] == "ok"
        assert fc["trend"] == "up"
        assert fc["predicted_nav"] > fc["current_nav"]
        assert fc["low"] <= fc["predicted_nav"] <= fc["high"]

    def test_forecast_nav_flat_and_insufficient(self):
        flat = [1.0] * 100
        fc = FundQuantAnalyzer().forecast_nav(flat, days=5)
        assert fc["data_mode"] == "ok"
        assert fc["trend"] == "flat"
        assert fc["predicted_nav"] == fc["current_nav"]
        assert FundQuantAnalyzer().forecast_nav([1.0, 1.1])["data_mode"] == "insufficient"

    def test_convenience_function_regression(self):
        # v9.2 之前 analyze_fund_performance 引用了不存在的字段会抛 AttributeError
        d = analyze_fund_performance(_trend_nav(), name="回归")
        assert "sharpe" in d and "sortino" in d and "calmar" in d
        for k in ("treynor", "skewness", "excess_kurtosis", "var_5pct",
                  "recovery_days", "dd_recovered", "stability"):
            assert k in d, f"v9.3 新键 {k} 缺失"


# ══ 三、期货量化增强 ══════════════════════════════════
def _fut_prices(seed=11, n=120):
    random.seed(seed)
    prices = [3800.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + random.gauss(0.0004, 0.012)))
    return prices


class TestFuturesV93:
    def test_predict_futures_confidence_band(self):
        r = FuturesAnalyzer().predict_futures("IF9999", _fut_prices())
        assert "predicted_low" in r and "predicted_high" in r
        assert r["predicted_low"] <= r["predicted"] <= r["predicted_high"]
        assert 0 <= r["confidence"] <= 100
        assert "position_suggestion" in r

    def test_volatility_forecast_ok(self):
        vf = FuturesAnalyzer().volatility_forecast(_fut_prices(), horizon=20)
        assert vf["data_mode"] == "ok"
        assert vf["annual_vol_pct"] > 0
        assert vf["period_vol_pct"] > 0
        assert vf["vol_trend"] in ("扩张", "压缩", "平稳")
        # 区间波动率应随 horizon 单调不降
        vf2 = FuturesAnalyzer().volatility_forecast(_fut_prices(), horizon=60)
        assert vf2["period_vol_pct"] >= vf["period_vol_pct"]

    def test_volatility_forecast_insufficient(self):
        assert FuturesAnalyzer().volatility_forecast([1, 2, 3])["data_mode"] == "insufficient"

    def test_position_size_neutral_and_long(self):
        fa = FuturesAnalyzer()
        prices = _fut_prices()
        assert fa.position_size(prices, "neutral")["position_pct"] == 0.0
        ps = fa.position_size(prices, "long", risk_budget_pct=2.0)
        assert 0 < ps["position_pct"] <= 100
        assert ps["stop_distance_pct"] > 0
        # 风险预算减半 → 仓位减半
        ps_half = fa.position_size(prices, "long", risk_budget_pct=1.0)
        assert abs(ps_half["position_pct"] - ps["position_pct"] / 2) <= 0.2

    def test_roll_yield_contango_and_backwardation(self):
        fa = FuturesAnalyzer()
        contango = fa.roll_yield_estimate([100.0, 100.0], [103.0, 103.0], 30)
        assert contango["structure"] == "contango"
        assert contango["roll_yield_annual_pct"] < 0, "升水下多头展期应亏损"
        back = fa.roll_yield_estimate([100.0, 100.0], [97.0, 97.0], 30)
        assert back["structure"] == "backwardation"
        assert back["roll_yield_annual_pct"] > 0, "贴水下多头展期应获利"
        assert fa.roll_yield_estimate([], [1.0])["data_mode"] == "insufficient"


# ══ 四、接线与导出 ════════════════════════════════════
class TestWiringV93:
    def test_quant_analyze_asset_pattern_forecast(self):
        r = quant_analyze_asset("600519", prices=_sine_prices())
        pf = r["pattern_forecast"]
        assert set(pf.keys()) == {"short", "medium"}
        for k in pf:
            assert "predicted_pct" in pf[k]
            assert pf[k]["direction_label"] in ("看涨", "看跌", "震荡", "数据不足")

    def test_quant_analyze_asset_short_prices(self):
        r = quant_analyze_asset("600519", prices=[100.0, 101.0])
        assert r["pattern_forecast"] == {}, "数据不足时形态预测应为空而非报错"

    def test_top_level_exports_and_version(self):
        import stock_researcher
        assert stock_researcher.__version__ == "9.3.0"
        from stock_researcher import (
            HistoricalPatternPredictor as TopCls,
            quick_pattern_forecast as top_fn,
            pattern_direction_label as top_label,
        )
        assert TopCls.__name__ == "HistoricalPatternPredictor"
        assert callable(top_fn) and callable(top_label)
        r = top_fn(_sine_prices(), horizon=5)
        assert r["data_mode"] == "ok"

    def test_version_consistency_v93(self):
        """v9.3 版本一致性接管：constants / _meta / settings / SKILL 四处一致。"""
        import json
        root = Path(__file__).resolve().parents[1]
        const = (root / "scripts" / "stock_researcher" / "constants.py").read_text(encoding="utf-8")
        assert 'VERSION = "9.3.0"' in const
        meta = json.loads((root / "_meta.json").read_text(encoding="utf-8"))
        assert meta["version"] == "9.3.0"
        settings = json.loads((root / "config" / "settings.json").read_text(encoding="utf-8"))
        assert settings["version"] == "9.3.0"
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        assert "version: 9.3.0" in skill


if __name__ == "__main__":
    import inspect
    n = 0
    for cls in (TestPatternPredictor, TestFundQuantV93, TestFuturesV93, TestWiringV93):
        inst = cls()
        for name, fn in inspect.getmembers(inst, inspect.ismethod):
            if name.startswith("test_"):
                fn()
                print(f"  ✅ {cls.__name__}.{name}")
                n += 1
    print(f"\n  🎉 All {n} v9.3 quant forecast tests passed!")
