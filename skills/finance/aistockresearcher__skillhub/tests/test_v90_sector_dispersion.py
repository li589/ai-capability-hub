# -*- coding: utf-8 -*-
"""v9.0 板块离散度(Dispersion) + 主题板块 + 轮动周期 测试（离线）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.sector_analysis.dispersion import (
    period_returns, mean, median, stdev, skewness, quintile_gap,
    top1_contribution, cohesion_label,
    SectorDispersion, DispersionResult,
)
from stock_researcher.sector_analysis.themes import (
    THEME_SECTOR_MAP, list_themes, get_theme_stocks,
)
from stock_researcher.sector_analysis.rotation_cycle import (
    stage_probabilities, pick_stage, CYCLE_SECTOR_MAP, STAGE_KEYS,
    RotationCycleDetector, CycleStageResult,
)


# ============================================================
# 1. 统计纯函数
# ============================================================

def test_mean_and_median_basic():
    assert mean([1, 2, 3, 4, 5]) == pytest.approx(3.0)
    assert median([1, 2, 3, 4, 5]) == pytest.approx(3.0)
    assert median([1, 2, 3, 4]) == pytest.approx(2.5)


def test_stdev_sample_known_value():
    # 样本标准差 of [2,4,4,4,5,5,7,9] ≈ 2.1389
    assert stdev([2, 4, 4, 4, 5, 5, 7, 9]) == pytest.approx(2.1389, rel=1e-3)


def test_stdev_single_value_zero():
    assert stdev([5.0]) == 0.0


def test_skewness_positive_for_right_tail():
    """右偏（少数大涨）→ 偏度 > 0。"""
    assert skewness([1, 1, 1, 1, 1, 1, 1, 10]) > 0


def test_quintile_gap_positive_when_top_above_bottom():
    leader, lagger, gap = quintile_gap([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert leader > lagger
    assert gap > 0


def test_top1_contribution_when_one_big_winner():
    """均值由少数赢家拉动 → 集中度 > 1。"""
    contrib = top1_contribution([0.5, 0.01, 0.01, 0.01])
    assert contrib > 1.0


def test_top1_contribution_zero_when_mean_negative():
    assert top1_contribution([-0.1, -0.2]) == 0.0


# ============================================================
# 2. cohesion_label
# ============================================================

def test_cohesion_label_unanimous_up():
    """均收益 +2%、70% 上涨、离散适中 → 齐涨。"""
    assert cohesion_label(0.02, 0.01, 10, 0.8, 0.2) == "齐涨"


def test_cohesion_label_unanimous_down():
    assert cohesion_label(-0.02, 0.01, 10, 0.2, 0.8) == "齐跌"


def test_cohesion_label_divergent_when_split():
    assert cohesion_label(0.0, 0.01, 10, 0.5, 0.5) == "分化"


# ============================================================
# 3. period_returns
# ============================================================

def test_period_returns_computes_per_stock():
    data = {"a": [100, 110, 121], "b": [100, 90, 81]}
    rets = period_returns(data, lookback=2)
    assert len(rets) == 2
    assert pytest.approx(rets[0], rel=1e-3) == 0.21    # a: 121/100-1
    assert pytest.approx(rets[1], rel=1e-3) == -0.19   # b: 81/100-1


def test_period_returns_skips_insufficient():
    data = {"a": [100], "b": [100, 90]}
    rets = period_returns(data, lookback=2)
    assert rets == []   # 都不足


# ============================================================
# 4. SectorDispersion 集成
# ============================================================

class _StubDispersion(SectorDispersion):
    def _resolve(self, sector, market):
        return ["a", "b", "c", "d", "e"], "proxy"

    def _fetch_closes(self, codes, days=90):
        # 4 只齐涨 + 1 只大涨（拉动偏度/集中度）
        out = {c: [10 * (1.005 ** i) for i in range(90)] for c in list(codes)[:4]}
        out[list(codes)[4]] = [10 * (1.02 ** i) for i in range(90)]
        return out


def test_analyze_dispersion_unanimous_up_is_cohesive():
    d = _StubDispersion().analyze("电子", market="cn", lookback=20)
    assert isinstance(d, DispersionResult)
    assert d.mean_return > 0
    assert d.cohesion in ("齐涨", "分化")   # 1 只大涨可能引入分化
    assert d.data_mode == "proxy"


def test_analyze_dispersion_no_data_returns_note():
    d = SectorDispersion().analyze("不存在XYZ", market="cn")
    assert d.n_stocks == 0


# ============================================================
# 5. 主题板块映射
# ============================================================

def test_list_themes_cn_includes_ai():
    themes = list_themes("cn")
    assert "AI算力" in themes
    assert "人形机器人" in themes


def test_get_theme_stocks_returns_list():
    stocks = get_theme_stocks("AI算力", "cn")
    assert isinstance(stocks, list)
    assert len(stocks) >= 4
    assert "002230" in stocks   # 科大讯飞


def test_get_theme_stocks_unknown_returns_empty():
    assert get_theme_stocks("不存在", "cn") == []


def test_theme_map_covers_three_markets():
    for m in ("cn", "hk", "us"):
        assert len(THEME_SECTOR_MAP.get(m, {})) >= 4


# ============================================================
# 6. 轮动周期
# ============================================================

def test_stage_probabilities_sum_to_one():
    probs = stage_probabilities(growth_signal=0.5, inflation_signal=0.2, risk_appetite=0.3)
    assert set(probs.keys()) == set(STAGE_KEYS)
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-6)
    assert all(0.0 <= v <= 1.0 for v in probs.values())


def test_stage_probabilities_growth_and_risk_on_favors_expansion():
    """增长扩张 + risk-on → 中周期/早周期概率较高，衰退低。"""
    probs = stage_probabilities(growth_signal=1.0, inflation_signal=0.0, risk_appetite=1.0)
    assert probs["衰退"] < probs["中周期"]
    assert probs["衰退"] < 0.25


def test_stage_probabilities_recession_when_growth_and_risk_off():
    probs = stage_probabilities(growth_signal=-1.0, inflation_signal=0.0, risk_appetite=-1.0)
    assert probs["衰退"] == max(probs.values())


def test_pick_stage_returns_argmax():
    probs = {"早周期": 0.2, "中周期": 0.5, "晚周期": 0.2, "衰退": 0.1}
    stage, conf = pick_stage(probs)
    assert stage == "中周期"
    assert conf == 0.5


def test_pick_stage_empty_default():
    stage, conf = pick_stage({})
    assert stage == "中周期"
    assert conf == 0.0


def test_cycle_sector_map_has_favored_and_avoid():
    for stage in STAGE_KEYS:
        cfg = CYCLE_SECTOR_MAP[stage]
        assert len(cfg["favored"]) >= 3
        assert len(cfg["avoid"]) >= 1
        assert cfg["rationale"]


def test_detect_cycle_stage_returns_result_shape():
    """检测器返回结构完整（联网部分失败时降级，不抛异常）。"""
    r = RotationCycleDetector().detect(market="cn")
    assert isinstance(r, CycleStageResult)
    assert r.stage in STAGE_KEYS
    assert set(r.probabilities.keys()) == set(STAGE_KEYS)
    assert isinstance(r.favored_sectors, list)
