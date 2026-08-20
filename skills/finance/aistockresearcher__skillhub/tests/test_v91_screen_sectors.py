#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v9.1 修复：screen_sectors 不再编造板块评分（回归测试，离线 mock）。

背景：旧实现 avg_chg = len(codes) * 0.1 是占位值，导致评分只与成分股数量
正相关（等量成分股的板块恒同分，大板块恒靠前），与真实行情无关。
本测试用 mock 的 SectorResult 验证评分已改用真实平均涨跌幅 + 资金流。
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _fake_analyze_sector(self, sector_name, market="cn"):
    from stock_researcher.sector_analysis.sectors import SectorResult
    # 两只板块成分股数量相同（都是5只），但真实行情天差地别：
    # 电子大涨 +5% → 应高分；银行下跌 -1% → 应低分。
    # 旧 placeholder 逻辑会给二者同样 52.5 分，无法区分。
    fake = {
        "电子": SectorResult(name="电子", code="电子", stocks=list("12345"),
                            market=market, avg_change_pct=5.0,
                            up_count=5, down_count=0, total_net_flow=80000,
                            score=20.0, signal="强于大盘"),
        "银行": SectorResult(name="银行", code="银行", stocks=list("67890"),
                            market=market, avg_change_pct=-1.0,
                            up_count=1, down_count=4, total_net_flow=-60000,
                            score=-10.0, signal="弱于大盘"),
    }
    return fake.get(sector_name, SectorResult(
        name=sector_name, code=sector_name, stocks=[], market=market))


def test_screen_sectors_uses_real_change_not_count():
    """板块评分应基于真实涨跌幅+资金流，而非成分股数量。"""
    from stock_researcher.screening.screening_engine import UnifiedScreener
    with patch("stock_researcher.sector_analysis.sectors.SectorAnalyzer.analyze_sector",
               _fake_analyze_sector):
        results = UnifiedScreener().screen_sectors(market="cn", top_n=20)

    assert results, "screen_sectors 应返回结果"
    by_name = {r["name"]: r for r in results}
    tech = by_name["电子"]
    bank = by_name["银行"]

    # 电子（+5%）应排在银行（-1%）之前，尽管二者成分股数量相同
    pos_tech = next(i for i, r in enumerate(results) if r["name"] == "电子")
    pos_bank = next(i for i, r in enumerate(results) if r["name"] == "银行")
    assert pos_tech < pos_bank, f"大涨板块应排在大跌板块之前：电子@{pos_tech} 银行@{pos_bank}"

    assert tech["avg_change_pct"] == 5.0
    assert tech["score"] > 50, f"大涨板块得分应>50，实际 {tech['score']}"
    assert tech["signal"] == "强于大盘"
    assert "平均涨跌幅" in tech["reasons"][0], f"理由应含真实涨跌幅，实际 {tech['reasons']}"

    assert bank["score"] < 50, f"下跌板块得分应<50，实际 {bank['score']}"

    # 同数量成分股的板块得分必须不同（旧 bug 会给二者相同 52.5 分）
    assert tech["score"] != bank["score"], "不同行情应产生不同评分"
    print("  ✅ test_screen_sectors_uses_real_change_not_count")


def test_screen_sectors_offline_degrades_gracefully():
    """离线（fetch_realtime 返回空）时不应抛异常，且评分诚实（中性 50，不编造）。"""
    from stock_researcher.screening.screening_engine import UnifiedScreener
    with patch("stock_researcher.data.market.MarketData.fetch_realtime",
               return_value={}):
        results = UnifiedScreener().screen_sectors(market="cn", top_n=3)
    # 离线场景 score 均为 50（中性），不因成分股数量倾斜
    assert results, "离线时应返回中性结果而非空列表"
    for r in results:
        assert r["score"] == 50.0, f"离线中性评分应为50，实际 {r['score']}"
    print("  ✅ test_screen_sectors_offline_degrades_gracefully")


if __name__ == "__main__":
    test_screen_sectors_uses_real_change_not_count()
    test_screen_sectors_offline_degrades_gracefully()
    print("\n  🎉 All v9.1 screen_sectors tests passed!")
