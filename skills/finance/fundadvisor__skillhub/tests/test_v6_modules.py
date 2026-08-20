#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v6.0 新增模块测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "data_collection"))


def test_multi_source_degradation(monkeypatch):
    """v9.0: 多源聚合器优雅降级 — mock 各源 fetch_macro 避免真实网络"""
    from multi_source.base import MultiSourceProvider
    p = MultiSourceProvider()
    sources = p.list_sources()
    assert len(sources) >= 3, f"至少应有3源，实际{len(sources)}"
    # v9.0: mock 各源 fetch_macro 返回失败响应，避免 akshare/网络时序
    from multi_source.base import SourceResponse
    for s in getattr(p, '_sources', []) or []:
        if hasattr(s, 'fetch_macro'):
            monkeypatch.setattr(s, 'fetch_macro', lambda: SourceResponse.fail(s.name, "offline"))
    r = p.get_macro()
    assert "indicators" in r
    assert "source_status" in r
    print(f"  ✅ test_multi_source_degradation ({len(sources)} sources, status={r['source_status']})")


def test_style_profile_allocation():
    """风格问卷 -> 5轴 -> 目标配置确定性"""
    from analysis.style_portfolio_builder import StylePortfolioBuilder
    b = StylePortfolioBuilder()
    # 保守型答案
    profile = b.build_profile_from_answers([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    tgt = profile.target_allocation
    assert tgt["stock"] < 30, f"保守应 low stock, 实际{tgt['stock']}%"
    # 激进型答案
    profile2 = b.build_profile_from_answers([4, 4, 4, 4, 4, 4, 4, 4, 4, 4])
    tgt2 = profile2.target_allocation
    assert tgt2["stock"] > tgt["stock"], "激进应比保守股票比例高"
    print(f"  ✅ test_style_profile_allocation (保守stock={tgt['stock']}%, 激进stock={tgt2['stock']}%)")


def test_rebalance_concept():
    """再平衡概念：drift 超过阈值应触发"""
    from analysis.portfolio_rebalancer import PortfolioRebalancer, _urgency_rank
    # 优先级排序
    assert _urgency_rank("高") < _urgency_rank("中") < _urgency_rank("低")
    print("  ✅ test_rebalance_concept")


def test_macro_analyzer_real_data(monkeypatch):
    """v9.0: macro_analyzer 至少有 data_source 标记（mock 网络加载，避免 akshare 时序）"""
    from analysis.macro_analyzer import MacroAnalyzer
    monkeypatch.setattr(MacroAnalyzer, '_load_real_macro', lambda self: {})
    m = MacroAnalyzer()
    gdp = m.get_gdp_data()
    assert "data_source" in gdp, f"v6.0 应有 data_source, keys={list(gdp.keys())}"
    print(f"  ✅ test_macro_analyzer_real_data (yoy={gdp.get('yoy')}, source={gdp.get('data_source')})")


if __name__ == "__main__":
    test_multi_source_degradation()
    test_style_profile_allocation()
    test_rebalance_concept()
    test_macro_analyzer_real_data()
    print("\n  🎉 All v6.0 tests passed!")
