# -*- coding: utf-8 -*-
"""v9.0 板块相对强度(RPS) + 多市场修复 测试（离线）"""

import sys
import math
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.sector_analysis.relative_strength import (
    align_and_rebase, rs_ratio_series, pct_change_over, sma,
    mansfield_rps, percentile_rank, rs_trend_label, slope_sign,
    SectorRelativeStrength, RelativeStrengthResult,
)
from stock_researcher.sector_analysis.sectors import SectorAnalyzer, SectorResult


# ============================================================
# 1. align_and_rebase —— 代理指数构造
# ============================================================

def test_align_two_flat_series_proxy_stays_at_100():
    """两只全程走平的股票 → 等权代理恒为 100。"""
    flat = [100.0] * 30
    proxy, n = align_and_rebase({"a": flat, "b": flat})
    assert n == 2
    assert max(abs(p - 100.0) for p in proxy) < 1e-9


def test_align_rising_plus_flat_proxy_rises():
    """一只翻倍上涨 + 一只走平 → 代理从 100 升到 150。"""
    rising = [10.0 * (1 + 0.01 * i) for i in range(30)]  # 末值约为 12.9 → 重定基后 129
    flat = [50.0] * 30
    proxy, n = align_and_rebase({"a": rising, "b": flat})
    assert n == 2
    assert proxy[0] == pytest.approx(100.0)
    # 末点 = (129 + 100)/2 = 114.5 左右，且 > 起点
    assert proxy[-1] > 110.0


def test_align_unequal_lengths_trims_to_min_from_end():
    """长度不一致 → 按最短末端对齐。"""
    long_s = list(range(1, 21))         # 1..20
    short_s = list(range(100, 113))     # 100..112（12 个）
    proxy, n = align_and_rebase({"a": long_s, "b": short_s})
    assert n == 2
    assert len(proxy) == min(len(long_s), len(short_s))   # 取最短


def test_align_empty_or_single_point_returns_empty():
    """空输入或单点 → ([], 0)。"""
    assert align_and_rebase({}) == ([], 0)
    assert align_and_rebase({"a": [5.0]}) == ([], 0)


def test_align_drops_nonpositive_and_invalid():
    """非正数/None/非数 被过滤，但仍用有效点构造。"""
    proxy, n = align_and_rebase({"a": [10, 0, 20, None, "x", 30]})
    assert n == 1


# ============================================================
# 2. rs_ratio_series / pct_change_over
# ============================================================

def test_rs_ratio_when_proxy_outperforms_increases():
    """代理涨得比基准快 → RS 序列递增。"""
    proxy = [100 + i for i in range(20)]
    bench = [100 + 0.1 * i for i in range(20)]
    rs = rs_ratio_series(proxy, bench)
    assert len(rs) == 20
    assert rs[-1] > rs[0]


def test_pct_change_over_known_value():
    assert pct_change_over([100, 110, 121], 2) == pytest.approx(0.21)
    assert pct_change_over([100, 90], 1) == pytest.approx(-0.10)


def test_pct_change_over_insufficient_returns_none():
    assert pct_change_over([100], 1) is None
    assert pct_change_over([100, 110], 5) is None


# ============================================================
# 3. mansfield_rps / percentile_rank / rs_trend_label
# ============================================================

def test_mansfield_rps_positive_when_rs_above_mean():
    """RS 现值高于历史均值 → RPS > 0（强于基准）。"""
    rs = [1.0] * 100 + [1.2] * 30   # 末段抬升
    assert mansfield_rps(rs) > 0


def test_mansfield_rps_negative_when_rs_below_mean():
    rs = [1.2] * 100 + [1.0] * 30
    assert mansfield_rps(rs) < 0


def test_mansfield_rps_short_series_returns_none():
    assert mansfield_rps([1.0, 1.1]) is None


def test_percentile_rank_extremes_and_median():
    pop = [1, 2, 3, 4, 5]
    assert percentile_rank(5, pop) == pytest.approx(100.0)
    assert percentile_rank(1, pop) == pytest.approx(0.0)
    assert percentile_rank(3, pop) == pytest.approx(50.0)


def test_percentile_rank_empty_returns_50():
    assert percentile_rank(1.0, []) == 50.0


def test_rs_trend_label_rising():
    """单调递增 RS → 上升。"""
    rs = [1.0 + 0.001 * i for i in range(60)]
    assert rs_trend_label(rs) == "上升"


def test_rs_trend_label_falling():
    rs = [1.5 - 0.001 * i for i in range(60)]
    assert rs_trend_label(rs) == "下降"


def test_slope_sign_basic():
    assert slope_sign([1, 2, 3, 4, 5]) > 0
    assert slope_sign([5, 4, 3, 2, 1]) < 0


# ============================================================
# 4. SectorRelativeStrength 集成（monkeypatch 真实数据源）
# ============================================================

class _StubRS(SectorRelativeStrength):
    """覆写联网方法，注入合成数据，验证完整链路。"""

    def _fetch_closes(self, codes, days=130):
        # 板块成分股：明显跑赢（每只翻倍）
        return {c: [10 * (1.005 ** i) for i in range(130)] for c in codes}

    def _fetch_benchmark_closes(self, market, days=130):
        # 基准：几乎走平
        return [100 + 0.0001 * i for i in range(130)]


def test_relative_strength_outperforming_sector_is_strong():
    """板块成分股持续跑赢基准 → RPS 强、趋势上升。"""
    srs = _StubRS()
    r = srs.relative_strength("电子", market="cn")
    assert isinstance(r, RelativeStrengthResult)
    assert r.n_stocks > 0
    assert r.rps_score > 0
    assert r.rs_trend in ("上升",)
    assert r.data_mode in ("proxy", "full")
    # 多周期 RS 收益为正
    assert r.rs_lookups.get("20d", 0) > 0


class _StubRSWeak(SectorRelativeStrength):
    def _fetch_closes(self, codes, days=130):
        # 板块成分股持续下跌
        return {c: [10 * (0.995 ** i) for i in range(130)] for c in codes}

    def _fetch_benchmark_closes(self, market, days=130):
        return [100 + 0.0001 * i for i in range(130)]


def test_relative_strength_underperforming_sector_is_weak():
    srs = _StubRSWeak()
    r = srs.relative_strength("化工", market="cn")
    assert r.rps_score < 0
    assert r.rs_trend == "下降"


def test_relative_strength_no_constituents_returns_neutral():
    srs = SectorRelativeStrength()
    r = srs.relative_strength("不存在的板块XYZ", market="cn")
    assert r.rps_score == 0.0
    assert "无成分股" in r.note or "失败" in r.note


# ============================================================
# 5. sectors.py 多市场死代码修复
# ============================================================

def test_analyze_sector_uses_hk_map_when_market_hk():
    """v9.0 修复：market='hk' 应使用港股映射，而非 A 股。"""
    captured = {}

    class FakeMarketData:
        def fetch_realtime(self, codes):
            captured["codes"] = list(codes)
            # 返回与请求代码对应的伪行情
            return {c: {"price": 1.0, "change_pct": 1.0,
                        "turnover": 0, "main_net_flow": 0} for c in codes}

    sa = SectorAnalyzer()
    sa.market = FakeMarketData()          # 直接注入，确定性高
    res = sa.analyze_sector("科技", market="hk")
    assert res.market == "hk"
    # 港股「科技」代表股含 00700（腾讯）
    assert "00700" in captured["codes"]


def test_analyze_all_sectors_market_us():
    """market='us' 时遍历的是美股 GICS 行业。"""
    class FakeMarketData:
        def fetch_realtime(self, codes):
            return {c: {"price": 1.0, "change_pct": 0.5,
                        "turnover": 0, "main_net_flow": 0} for c in codes}

    sa = SectorAnalyzer()
    sa.market = FakeMarketData()
    results = sa.analyze_all_sectors(market="us")
    names = {r.name for r in results}
    assert "信息技术" in names       # 美股 GICS 行业
    assert all(r.market == "us" for r in results)


def test_sector_result_new_fields_backward_compatible():
    """新增字段有默认值，旧式构造不破。"""
    r = SectorResult(name="银行", code="银行", stocks=["600036"])
    assert r.market == "cn"
    assert r.rps_score == 0.0
    assert r.data_mode == "proxy"
