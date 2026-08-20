# -*- coding: utf-8 -*-
"""v9.0 板块宽度(Breadth) 测试（离线）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.sector_analysis.breadth import (
    pct_above_ma, adv_dec_counts, new_highs_lows, zweig_thrust_series,
    detect_thrust, health_label, detect_divergence,
    SectorBreadth, BreadthResult,
)


def _rising(n, start=10.0, step=0.5):
    return [start + step * i for i in range(n)]


def _falling(n, start=50.0, step=0.5):
    return [start - step * i for i in range(n)]


# ============================================================
# 1. pct_above_ma
# ============================================================

def test_pct_above_ma_all_rising_stocks_100pct():
    """全部成分股持续上行 → 现价都在 MA20 之上 → 100%。"""
    data = {f"s{i}": _rising(60) for i in range(5)}
    assert pct_above_ma(data, 20) == pytest.approx(100.0)


def test_pct_above_ma_all_falling_stocks_0pct():
    """全部持续下行 → 现价都在 MA20 之下 → 0%。"""
    data = {f"s{i}": _falling(60) for i in range(5)}
    assert pct_above_ma(data, 20) == pytest.approx(0.0)


def test_pct_above_ma_mixed_half():
    """一半上一半下 → 约 50%。"""
    data = {f"up{i}": _rising(60) for i in range(3)}
    data.update({f"dn{i}": _falling(60) for i in range(3)})
    val = pct_above_ma(data, 20)
    assert 30.0 < val < 70.0


# ============================================================
# 2. adv_dec_counts / new_highs_lows
# ============================================================

def test_adv_dec_counts_rising_vs_falling():
    data = {"up": _rising(40), "dn": _falling(40)}
    adv, dec = adv_dec_counts(data, lookback=20)
    assert adv == 1 and dec == 1


def test_new_highs_lows_rising_makes_new_highs():
    data = {"up": _rising(40)}
    hi, lo = new_highs_lows(data, 20)
    assert hi == 1 and lo == 0


def test_new_highs_lows_falling_makes_new_lows():
    data = {"dn": _falling(40)}
    hi, lo = new_highs_lows(data, 20)
    assert lo == 1 and hi == 0


# ============================================================
# 3. zweig thrust / detect_thrust
# ============================================================

def test_detect_thrust_triggered():
    """%above 序列从 ≤0.5 在 10 期内升至 ≥0.615 → 触发。"""
    series = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    assert detect_thrust(series) is True


def test_detect_thrust_not_triggered_when_no_cross():
    series = [0.7, 0.7, 0.7, 0.7]
    assert detect_thrust(series) is False


def test_zweig_thrust_series_length():
    data = {f"s{i}": _rising(50) for i in range(5)}
    series = zweig_thrust_series(data, 20)
    assert len(series) > 0
    assert all(0.0 <= x <= 1.0 for x in series)


# ============================================================
# 4. health_label / detect_divergence
# ============================================================

def test_health_label_overheated():
    assert health_label(85, 80) == "过热"


def test_health_label_freezing():
    assert health_label(15, 18) == "冰点"


def test_health_label_healthy():
    assert health_label(65, 62) == "健康"


def test_detect_divergence_top_divergence():
    """价格创新高但宽度未创新高 → 顶背离。"""
    proxy = [100 + i for i in range(40)]            # 价格持续新高
    breadth = [0.8 - 0.01 * i for i in range(40)]   # 宽度反而走低
    assert detect_divergence(proxy, breadth) == "顶背离"


def test_detect_divergence_bottom_divergence():
    proxy = [100 - i for i in range(40)]
    breadth = [0.2 + 0.01 * i for i in range(40)]   # 宽度反而走高
    assert detect_divergence(proxy, breadth) == "底背离"


def test_detect_divergence_none_when_aligned():
    proxy = [100 + i for i in range(40)]
    breadth = [0.5 + 0.01 * i for i in range(40)]   # 同步新高
    assert detect_divergence(proxy, breadth) == "无"


# ============================================================
# 5. SectorBreadth 集成（注入合成数据）
# ============================================================

class _StubBreadth(SectorBreadth):
    def _resolve(self, sector, market):
        return ["a", "b", "c", "d", "e"], "proxy"

    def _fetch_closes(self, codes, days=220):
        return {c: _rising(220) for c in codes}


def test_analyze_breadth_healthy_when_all_rising():
    b = _StubBreadth().analyze("电子", market="cn")
    assert isinstance(b, BreadthResult)
    assert b.pct_above_ma20 >= 80.0
    assert b.health in ("过热", "健康")
    assert b.advancers >= 1


class _StubBreadthWeak(SectorBreadth):
    def _resolve(self, sector, market):
        return ["a", "b", "c"], "proxy"

    def _fetch_closes(self, codes, days=220):
        return {c: _falling(220) for c in codes}


def test_analyze_breadth_freezing_when_all_falling():
    b = _StubBreadthWeak().analyze("煤炭", market="cn")
    assert b.pct_above_ma20 <= 20.0
    assert b.health in ("冰点", "偏弱")
    assert b.decliners >= 1
