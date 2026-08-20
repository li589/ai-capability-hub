#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8.1 修复回归测试

覆盖：
  1. nav_vs_target_tracking 实际权重/漂移计算（修复市值未归一化）
  2. fund_predictor 跨进程稳定随机种子（修复默认 hash 不可复现）
  3. LazyDataCache 文件修改后旧缓存立即失效
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_nav_vs_target_tracking_uses_market_value():
    from analysis.position_tracker import PortfolioPositionTracker
    tracker = PortfolioPositionTracker()
    holdings = [
        {"fund_code": "A", "name": "A基金", "shares": 100},
        {"fund_code": "B", "name": "B基金", "shares": 100},
    ]
    result = tracker.nav_vs_target_tracking(
        holdings,
        {"A": 50, "B": 50},
        nav_updates={"A": 1.0, "B": 3.0},
    )
    pos = {p["code"]: p for p in result["positions"]}
    assert pos["A"]["actual_weight_pct"] == 25.0
    assert pos["B"]["actual_weight_pct"] == 75.0
    assert pos["A"]["drift_pct"] == -25.0
    assert pos["B"]["drift_pct"] == 25.0
    assert result["total_drift_pct"] == 50.0
    assert result["needs_rebalance"] is True


def test_nav_vs_target_tracking_weight_fallback():
    from analysis.position_tracker import PortfolioPositionTracker
    tracker = PortfolioPositionTracker()
    holdings = [
        {"fund_code": "A", "name": "A基金", "weight": 30},
        {"fund_code": "B", "name": "B基金", "weight": 70},
    ]
    result = tracker.nav_vs_target_tracking(holdings, {"A": 40, "B": 60})
    pos = {p["code"]: p for p in result["positions"]}
    assert pos["A"]["actual_weight_pct"] == 30.0
    assert pos["B"]["actual_weight_pct"] == 70.0
    assert pos["A"]["drift_pct"] == -10.0
    assert pos["B"]["drift_pct"] == 10.0
    assert result["total_drift_pct"] == 20.0


def test_stable_seed_is_deterministic_and_distinct():
    from analysis.fund_predictor import _stable_seed
    assert _stable_seed("110022", "week") == _stable_seed("110022", "week")
    assert _stable_seed("110022", "week") != _stable_seed("110022", "month")
    assert _stable_seed("110022", "week") != _stable_seed("110023", "week")


def test_fund_predictor_reproducible_with_same_inputs():
    from analysis.fund_predictor import FundPredictor
    nav = [1.0 + i * 0.001 for i in range(120)]
    fp = FundPredictor()
    r1 = fp.predict_fund("110022", periods=["week", "month"], nav_history=nav)
    r2 = fp.predict_fund("110022", periods=["week", "month"], nav_history=nav)
    assert r1["overall_score"] == r2["overall_score"]
    assert r1["predictions"]["week"]["mean_return"] == r2["predictions"]["week"]["mean_return"]
    assert r1["predictions"]["month"]["median_return"] == r2["predictions"]["month"]["median_return"]


def test_lazy_cache_invalidates_on_file_change():
    from fund_advisor_paths import LazyDataCache
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "sample.json"
        path.write_text(json.dumps({"version": 1}), encoding="utf-8")
        cache = LazyDataCache(max_size=5, ttl_seconds=3600)
        cache.set(str(path), {"version": 1})
        assert cache.get(str(path))["version"] == 1

        time.sleep(0.02)
        path.write_text(json.dumps({"version": 2}), encoding="utf-8")
        os.utime(path, (time.time() + 1, time.time() + 1))
        assert cache.get(str(path)) is None, "文件更新后旧缓存应立即失效"

        cache.set(str(path), {"version": 2})
        assert cache.get(str(path))["version"] == 2
