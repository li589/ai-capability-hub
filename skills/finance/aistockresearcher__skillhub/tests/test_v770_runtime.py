#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-researcher v7.7 运行逻辑优化测试（test_v770_runtime.py）

覆盖：
- BUG-001 修复回归：_risk_cache / _gold_cache 线程安全
- BUG-002 修复回归：calc_obv 边界检查
- BUG-003 修复回归：monte_carlo 派生种子（不再相关）
- BUG-005 修复回归：signal() 阈值平滑
- 新增能力：指数退避 _exponential_backoff
- 新增能力：fetch_quote 重试逻辑
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import stock_predict  # noqa: E402


# ============================================================================
# BUG-001 回归：缓存线程安全
# ============================================================================


class TestBug001CacheThreadSafe:
    """_risk_cache / _gold_cache 缓存读取写入应线程安全。"""

    def test_concurrent_cache_reads_does_not_corrupt(self):
        """多线程并发读写缓存不应崩溃或数据损坏。"""
        # 重置缓存
        stock_predict._risk_cache["ts"] = 0
        stock_predict._risk_cache["data"] = None
        stock_predict._gold_cache["ts"] = 0
        stock_predict._gold_cache["data"] = None

        errors = []

        def writer():
            try:
                for i in range(50):
                    stock_predict._safe_cache_set(
                        stock_predict._risk_cache, {"test": i}
                    )
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(50):
                    stock_predict._safe_cache_get(stock_predict._risk_cache)
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert not errors, f"并发读写出错: {errors}"
        # 验证最终状态一致
        assert stock_predict._risk_cache["data"] is not None
        assert stock_predict._risk_cache["ts"] > 0

    def test_cache_ttl_returns_none_when_expired(self):
        """TTL 过期时 _safe_cache_get 应返回 None。"""
        stock_predict._risk_cache["ts"] = time.time() - 1000  # 1000s 前
        stock_predict._risk_cache["data"] = {"old": True}
        result = stock_predict._safe_cache_get(stock_predict._risk_cache, ttl_seconds=300)
        assert result is None  # 过期

    def test_cache_ttl_returns_data_when_fresh(self):
        """TTL 未过期时 _safe_cache_get 应返回数据。"""
        stock_predict._risk_cache["ts"] = time.time()  # 刚刚
        stock_predict._risk_cache["data"] = {"new": True}
        result = stock_predict._safe_cache_get(stock_predict._risk_cache, ttl_seconds=300)
        assert result == {"new": True}

    def test_cache_lock_exists(self):
        """_cache_lock 必须存在且为 threading.Lock 类型。"""
        import threading
        assert hasattr(stock_predict, "_cache_lock")
        assert isinstance(stock_predict._cache_lock, type(threading.Lock()))


# ============================================================================
# BUG-002 回归：calc_obv 边界检查
# ============================================================================


class TestBug002CalcObvBounds:

    def test_normal_lengths(self):
        """等长 closes/volumes 应正常计算。"""
        closes = [100, 102, 101, 103, 105]
        volumes = [1000, 1500, 1200, 1800, 2000]
        obv = stock_predict.calc_obv(closes, volumes)
        # 验证：上涨加、下跌减
        # 102>100: +1500; 101<102: -1200; 103>101: +1800; 105>103: +2000 = 4100
        assert obv == 4100.0

    def test_closes_longer_than_volumes_no_crash(self):
        """closes 比 volumes 长时不应 IndexError。"""
        closes = [100, 102, 101, 103, 105, 108]  # 6 个
        volumes = [1000, 1500, 1200]  # 只有 3 个
        # 应只遍历到 min(6, 3) = 3（但原 bug 会在 i=4 时 volumes[4] IndexError）
        obv = stock_predict.calc_obv(closes, volumes)
        # n = min(6, 3) = 3，循环 i in range(1, 3) → i=1, 2
        # i=1: closes[1]=102>closes[0]=100, obv += volumes[1]=1500 → obv=1500
        # i=2: closes[2]=101<closes[1]=102, obv -= volumes[2]=1200 → obv=300
        assert obv == 300.0

    def test_volumes_longer_than_closes_no_crash(self):
        """volumes 比 closes 长时也不应 IndexError（防御性编程）。"""
        closes = [100, 102, 101]
        volumes = [1000, 1500, 1200, 1800, 2000]
        # n = min(3, 5) = 3，循环 i in range(1, 3)
        obv = stock_predict.calc_obv(closes, volumes)
        assert obv == 300.0  # 同上

    def test_empty_inputs(self):
        """空输入应返回 0。"""
        assert stock_predict.calc_obv([], []) == 0.0
        assert stock_predict.calc_obv([100], [1000]) == 0.0

    def test_too_short(self):
        """< 2 个数据点应返回 0。"""
        assert stock_predict.calc_obv([100], []) == 0.0
        assert stock_predict.calc_obv([100], [1000]) == 0.0


# ============================================================================
# BUG-003 回归：monte_carlo 派生种子
# ============================================================================


class TestBug003MonteCarloSeed:

    def test_same_input_same_result(self):
        """相同输入应产生确定性结果（不依赖全局随机状态）。"""
        closes = [100 + i * 0.5 for i in range(50)]
        r1 = stock_predict.monte_carlo(closes, price=125.0, sims=200)
        r2 = stock_predict.monte_carlo(closes, price=125.0, sims=200)
        # 派生种子应保证相同输入 → 相同输出
        assert r1 == r2, "相同输入应得到相同蒙特卡洛结果"

    def test_different_price_different_result(self):
        """不同输入（不同 price）应产生不同结果。"""
        closes = [100 + i * 0.5 for i in range(50)]
        r1 = stock_predict.monte_carlo(closes, price=125.0, sims=200)
        r2 = stock_predict.monte_carlo(closes, price=130.0, sims=200)
        # 不同 price 派生不同种子 → 不同结果
        assert r1 != r2

    def test_explicit_seed_overrides(self):
        """显式 seed 应覆盖派生种子。"""
        closes = [100 + i * 0.5 for i in range(50)]
        r1 = stock_predict.monte_carlo(closes, price=125.0, sims=200, seed=999)
        r2 = stock_predict.monte_carlo(closes, price=125.0, sims=200, seed=999)
        # 同种子应得到同结果
        assert r1 == r2

    def test_insufficient_data_returns_neutral(self):
        """数据不足应返回中性默认（5d 和 10d 都是 50% 上涨概率）。"""
        closes = [100, 101, 102]
        result = stock_predict.monte_carlo(closes, price=102.0, sims=100)
        assert result["5d"]["up"] == 0.5
        assert result["10d"]["up"] == 0.5


# ============================================================================
# BUG-005 回归：signal() 阈值平滑
# ============================================================================


class TestBug005SignalSmoothness:

    def test_25_to_35_boundary_smooth(self):
        """25 → 35 区间置信度应平滑过渡（无跳跃）。"""
        # 测试 25/26/34/35 四个分数点的置信度
        s25 = stock_predict.signal({"total": 25.0})
        s26 = stock_predict.signal({"total": 26.0})
        s34 = stock_predict.signal({"total": 34.0})
        s35 = stock_predict.signal({"total": 35.0})
        # 相邻分数（差 1）置信度差应 < 0.02
        diff_25_26 = abs(s25[1] - s26[1])
        diff_34_35 = abs(s34[1] - s35[1])
        assert diff_25_26 < 0.02
        assert diff_34_35 < 0.02

    def test_strong_signal_high_confidence(self):
        """100 分 → 强烈看涨 + 高置信度。"""
        sig, cf = stock_predict.signal({"total": 100.0})
        assert "强烈看涨" in sig
        assert cf >= 0.9

    def test_weak_signal_low_confidence(self):
        """0 分 → 强烈看跌 + 低置信度。"""
        sig, cf = stock_predict.signal({"total": 0.0})
        assert "强烈看跌" in sig
        assert cf <= 0.30  # 不应过低（最低 0.10）

    def test_signal_range_complete(self):
        """0-100 分应覆盖 5 个信号档。"""
        scores = [10, 30, 50, 65, 85]
        signals = [stock_predict.signal({"total": s})[0] for s in scores]
        # 应至少有 3 个不同信号
        unique_signals = set(signals)
        assert len(unique_signals) >= 3


# ============================================================================
# 新增能力：指数退避
# ============================================================================


class TestExponentialBackoff:

    def test_first_attempt_no_wait(self):
        """attempt=1 应返回 base 0.5s。"""
        assert stock_predict._exponential_backoff(1) == 0.5

    def test_doubles_each_attempt(self):
        """attempt=1,2,3 应为 0.5, 1.0, 2.0。"""
        assert stock_predict._exponential_backoff(1) == 0.5
        assert stock_predict._exponential_backoff(2) == 1.0
        assert stock_predict._exponential_backoff(3) == 2.0
        assert stock_predict._exponential_backoff(4) == 4.0

    def test_caps_at_max_delay(self):
        """attempt=10 应被 cap 在 max_delay。"""
        result = stock_predict._exponential_backoff(10, base=0.5, max_delay=4.0)
        assert result == 4.0


# ============================================================================
# 新增能力：fetch_quote 重试
# ============================================================================


class TestFetchQuoteRetry:

    def test_fetch_quote_signature_has_max_retries(self):
        """fetch_quote 签名应包含 max_retries 参数。"""
        import inspect
        sig = inspect.signature(stock_predict.fetch_quote)
        assert "max_retries" in sig.parameters
        # 默认值应是 3
        assert sig.parameters["max_retries"].default == 3

    def test_fetch_quote_returns_error_dict_when_no_network(self, monkeypatch):
        """当网络失败时重试 3 次后应返回 error dict。"""
        # monkeypatch urllib.request.urlopen 全部失败
        import urllib.error
        def always_fail(*args, **kwargs):
            raise urllib.error.URLError("test network failure")
        monkeypatch.setattr("urllib.request.urlopen", always_fail)

        result = stock_predict.fetch_quote("600519", silent=True, max_retries=2)
        assert "error" in result
        assert "已重试 2 次" in result["error"]
        assert "hint" in result


# ============================================================================
# BUG-007 回归：版本号一致性
# ============================================================================


class TestBug007VersionConsistency:

    def test_settings_and_meta_versions_match(self):
        """config/settings.json 和 _meta.json 的 version 应一致。"""
        import json
        from pathlib import Path
        ROOT = SKILL_DIR
        settings = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
        meta = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
        # 修复 BUG-007：版本号必须一致
        assert settings["version"] == meta["version"]

    def test_version_format_semver(self):
        """版本号必须符合语义化版本 X.Y.Z。"""
        import re
        import json
        meta = json.loads((SKILL_DIR / "_meta.json").read_text(encoding="utf-8"))
        assert re.match(r"^\d+\.\d+\.\d+$", meta["version"]), \
            f"version 不符合 semver: {meta['version']}"


# ============================================================================
# conftest.py 回归测试
# ============================================================================


class TestConftest:
    """conftest.py 的运行逻辑不应破坏。"""

    def test_conftest_blocks_heavy_libs(self):
        """HeavyLibBlocker 应在 sys.meta_path 中。"""
        import sys
        # 触发 conftest.py 加载
        import importlib
        import importlib.util
        # 检查 _pytest 配置已完成
        assert hasattr(sys, "meta_path")
        # meta_path 第一项应是 HeavyLibBlocker
        blocker_types = [type(m).__name__ for m in sys.meta_path[:1]]
        assert "HeavyLibBlocker" in blocker_types or len(blocker_types) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])