#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.1 五维分析 + 多资产推演 单元测试

覆盖：
  - FiveDimAnalyzer 权重 / 维度评分 / 信号归类 / 缓存
  - AssetForecaster 资产类型识别 / 多周期方向 / 跨资产逻辑
"""
import sys
from pathlib import Path

# 必须最先设置，禁用字节码
sys.dont_write_bytecode = True

# 把 scripts 加入 path（项目 conftest.py 还会进一步屏蔽重型三方库）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import unittest
from unittest.mock import patch, MagicMock

# 防止 conftest.py 屏蔽我们的模块：先注入假 stock_researcher.sentiment 等


def _setup_module_stubs():
    """注入 fake 子模块，让 analysis 包能 import 而不触发重型库。"""
    import types

    # fake stock_researcher 包（conftest 没屏蔽它，但子模块需注入）
    sr = types.ModuleType("stock_researcher")
    sr.__path__ = [str(ROOT / "scripts" / "stock_researcher")]
    sys.modules.setdefault("stock_researcher", sr)

    # fake sentiment 子模块（含 UnifiedSentimentEngine + forum_sentiment）
    sent = types.ModuleType("stock_researcher.sentiment")

    class FakeSentimentEngine:
        def __init__(self):
            self._cache = {}

        def analyze_stock(self, code, market="cn"):
            return {
                "code": code, "market": market,
                "score": 25.0, "label": "积极",
                "good_news": [{"title": "利好1", "score": 30}],
                "bad_news": [{"title": "利空1", "score": -10}],
                "risk_flags": [],
                "sources": ["news"],
            }

        def get_market_sentiment(self, market="cn"):
            return {"fear_greed": 65, "label": "积极"}

    sent.UnifiedSentimentEngine = FakeSentimentEngine

    forum = types.ModuleType("stock_researcher.sentiment.forum_sentiment")

    def fake_analyze_forum_sentiment(code, market="cn"):
        return {
            "available": True,
            "sentiment_score": 30.0,
            "post_count": 42,
            "crowd_extreme": False,
        }

    forum.analyze_forum_sentiment = fake_analyze_forum_sentiment
    sys.modules["stock_researcher.sentiment"] = sent
    sys.modules["stock_researcher.sentiment.forum_sentiment"] = forum

    # fake policy 子模块
    policy = types.ModuleType("stock_researcher.policy")

    class FakePolicyAnalyzer:
        def analyze_market_impact(self, market="cn"):
            return {
                "score": 15.0,
                "key_policies": ["政策1", "政策2"],
                "source": "fake",
            }

    policy.PolicyAnalyzer = FakePolicyAnalyzer
    sys.modules["stock_researcher.policy"] = policy

    # fake data.money_flow
    mf = types.ModuleType("stock_researcher.data.money_flow")

    class FakeMoneyFlowData:
        def get_money_flow(self, codes):
            return {c: {"money_flow_score": 20.0, "main_inflow": 1000.0} for c in codes}

    mf.MoneyFlowData = FakeMoneyFlowData
    sys.modules["stock_researcher.data.money_flow"] = mf

    # fake core.technical
    tech = types.ModuleType("stock_researcher.core.technical")

    class FakeTechnicalAnalyzer:
        def analyze(self, code, market="cn"):
            return {"composite_score": 10.0, "rsi": 55.0}

    tech.TechnicalAnalyzer = FakeTechnicalAnalyzer
    sys.modules["stock_researcher.core.technical"] = tech

    # fake pkg.fund_analyzer
    pkg = types.ModuleType("pkg")
    fa = types.ModuleType("pkg.fund_analyzer")

    def fake_score_fund_v4(code):
        return {"total_score": 65, "grade": "优秀"}

    def fake_predict_fund_short_term(code):
        return {"direction": "up", "predicted_pct": 1.5}

    fa.score_fund_v4 = fake_score_fund_v4
    fa.predict_fund_short_term = fake_predict_fund_short_term
    sys.modules["pkg"] = pkg
    sys.modules["pkg.fund_analyzer"] = fa

    # fake quantitative.commodity_analyzer
    qa = types.ModuleType("stock_researcher.quantitative.commodity_analyzer")
    qa.analyze_commodity = lambda code: {"score": 30.0}
    sys.modules["stock_researcher.quantitative.commodity_analyzer"] = qa

    # fake data.global_market
    gm = types.ModuleType("stock_researcher.data.global_market")
    gm.analyze_gold_factors = lambda: {"score": 25.0}
    sys.modules["stock_researcher.data.global_market"] = gm

    # fake index_analysis.index_forecast
    ia = types.ModuleType("stock_researcher.index_analysis.index_forecast")

    class FakeIndexForecaster:
        def forecast(self, code, horizons=None):
            return {"horizons": {"1M": {"direction": "up"}}}

    ia.IndexForecaster = FakeIndexForecaster
    sys.modules["stock_researcher.index_analysis.index_forecast"] = ia


_setup_module_stubs()

# 现在导入被测模块
from stock_researcher.analysis.five_dim_analyzer import (
    FiveDimAnalyzer, quick_five_dim,
)
from stock_researcher.analysis.asset_forecaster import (
    AssetForecaster, quick_forecast, detect_asset_type,
)


# ============================================================
# 1. 资产类型识别
# ============================================================
class TestAssetTypeDetection(unittest.TestCase):
    def test_a_stock(self):
        self.assertEqual(detect_asset_type("600519"), "stock")
        self.assertEqual(detect_asset_type("hk:00700"), "stock")
        self.assertEqual(detect_asset_type("us:AAPL"), "stock")
        self.assertEqual(detect_asset_type("00700.HK"), "stock")

    def test_futures(self):
        self.assertEqual(detect_asset_type("fut:aum"), "futures")
        self.assertEqual(detect_asset_type("gold:comex"), "futures")
        self.assertEqual(detect_asset_type("crude:wti"), "futures")
        self.assertEqual(detect_asset_type("silver:sh"), "futures")

    def test_index(self):
        self.assertEqual(detect_asset_type("idx:N225"), "index")
        self.assertEqual(detect_asset_type("idx:SPX"), "index")

    def test_market_hint(self):
        self.assertEqual(detect_asset_type("abc", market_hint="fund"), "fund")
        self.assertEqual(detect_asset_type("abc", market_hint="futures"), "futures")

    def test_fallback_stock(self):
        self.assertEqual(detect_asset_type("unknown"), "stock")
        self.assertEqual(detect_asset_type(""), "stock")


# ============================================================
# 2. 五维分析 — 信号归类与权重
# ============================================================
class TestSignalClassification(unittest.TestCase):
    def setUp(self):
        self.analyzer = FiveDimAnalyzer()

    def test_strong_bull(self):
        self.assertEqual(self.analyzer._score_to_signal(80), "强烈看多")
        self.assertEqual(self.analyzer._score_to_signal(65), "强烈看多")

    def test_bull(self):
        self.assertEqual(self.analyzer._score_to_signal(40), "看多")
        self.assertEqual(self.analyzer._score_to_signal(31), "看多")

    def test_neutral(self):
        self.assertEqual(self.analyzer._score_to_signal(0), "中性")
        self.assertEqual(self.analyzer._score_to_signal(-25), "中性")
        self.assertEqual(self.analyzer._score_to_signal(25), "中性")

    def test_bear(self):
        self.assertEqual(self.analyzer._score_to_signal(-40), "看空")
        self.assertEqual(self.analyzer._score_to_signal(-31), "看空")

    def test_strong_bear(self):
        self.assertEqual(self.analyzer._score_to_signal(-80), "强烈看空")
        self.assertEqual(self.analyzer._score_to_signal(-65), "强烈看空")

    def test_default_weights_sum_to_one(self):
        s = sum(FiveDimAnalyzer.DEFAULT_WEIGHTS.values())
        self.assertAlmostEqual(s, 1.0, places=3)

    def test_custom_weights_override(self):
        custom = {"policy": 0.5, "capital": 0.5,
                  "news": 0.0, "forum": 0.0, "sentiment": 0.0}
        a = FiveDimAnalyzer(weights=custom)
        self.assertEqual(a.weights["policy"], 0.5)
        self.assertEqual(a.weights["news"], 0.0)  # default overridden to 0


# ============================================================
# 3. 五维分析 — analyze() 集成
# ============================================================
class TestFiveDimIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = FiveDimAnalyzer()

    def test_analyze_returns_all_keys(self):
        r = self.analyzer.analyze("600519", market="cn")
        for k in ("code", "market", "asset_type", "timestamp", "dimensions",
                  "total_score", "signal", "confidence", "available_sources",
                  "missing_sources", "key_signals", "risk_flags"):
            self.assertIn(k, r, f"missing key: {k}")

    def test_analyze_uses_stubs(self):
        r = self.analyzer.analyze("600519")
        # 五个 fake stub 都返回正分，所以 total_score > 0
        self.assertGreater(r["total_score"], 0)
        self.assertEqual(r["available_sources"], 5)
        self.assertEqual(r["missing_sources"], [])

    def test_analyze_handles_missing_source(self):
        # 临时让 policy 抛异常（v7.1 可靠性：返回降级结构而非 None）
        saved = sys.modules.get("stock_researcher.policy")
        boom = MagicMock()
        boom.PolicyAnalyzer = MagicMock(side_effect=RuntimeError("simulated"))
        sys.modules["stock_researcher.policy"] = boom
        try:
            r = self.analyzer.analyze("600519")
            # v7.1 行为：policy 维度存在但 confidence=0.2 + 异常标记
            self.assertIn("policy", r["dimensions"])
            self.assertEqual(r["dimensions"]["policy"]["confidence"], 0.2)
            self.assertEqual(r["dimensions"]["policy"]["score"], 0)
            # available_sources = 5（仍占位,只是降级）
            self.assertEqual(r["available_sources"], 5)
            # 总分不应抛错
            self.assertIsInstance(r["total_score"], (int, float))
        finally:
            sys.modules["stock_researcher.policy"] = saved

    def test_confidence_in_range(self):
        r = self.analyzer.analyze("600519")
        self.assertGreaterEqual(r["confidence"], 0.3)
        self.assertLessEqual(r["confidence"], 0.95)

    def test_cache_reuse(self):
        r1 = self.analyzer.analyze("600519")
        r2 = self.analyzer.analyze("600519")
        # 同一对象（缓存命中）
        self.assertIs(r1, r2)

    def test_quick_five_dim(self):
        r = quick_five_dim("600519")
        self.assertIn("dimensions", r)


# ============================================================
# 4. AssetForecaster — 股票路径
# ============================================================
class TestAssetForecasterStock(unittest.TestCase):
    def setUp(self):
        self.fc = AssetForecaster()

    def test_forecast_stock_returns_shape(self):
        r = self.fc.forecast("600519", market="cn", asset_type="stock")
        for k in ("code", "market", "asset_type", "direction",
                  "predicted_pct", "score", "confidence", "narrative",
                  "key_factors", "horizons", "horizon"):
            self.assertIn(k, r, f"missing key: {k}")

    def test_horizons_contain_4_periods(self):
        r = self.fc.forecast("600519")
        for h in ("1D", "1W", "1M", "3M"):
            self.assertIn(h, r["horizons"])
            self.assertIn("direction", r["horizons"][h])
            self.assertIn("predicted_pct", r["horizons"][h])

    def test_horizons_grow_with_period(self):
        r = self.fc.forecast("600519", horizon="1W")
        # 分数 → 涨跌幅 scale：1D=0.3 / 1W=1.0 / 1M=2.5 / 3M=5.0
        self.assertLess(abs(r["horizons"]["1D"]["predicted_pct"]),
                        abs(r["horizons"]["1M"]["predicted_pct"]))
        self.assertLess(abs(r["horizons"]["1M"]["predicted_pct"]),
                        abs(r["horizons"]["3M"]["predicted_pct"]))

    def test_default_horizon(self):
        r = self.fc.forecast("600519")
        self.assertEqual(r["horizon"], "1W")

    def test_direction_logic(self):
        r = self.fc.forecast("600519")
        # 正分 → up
        self.assertIn(r["direction"], ("up", "flat"))

    def test_quick_forecast(self):
        r = quick_forecast("600519")
        self.assertEqual(r["code"], "600519")


# ============================================================
# 5. AssetForecaster — 跨资产类型
# ============================================================
class TestAssetForecasterMultiType(unittest.TestCase):
    def setUp(self):
        self.fc = AssetForecaster()

    def test_fund_path(self):
        r = self.fc.forecast("110022", market="cn", asset_type="fund")
        self.assertEqual(r["asset_type"], "fund")
        self.assertIn("fund_score_detail", r)
        self.assertIn("fund_pred_detail", r)

    def test_futures_path(self):
        r = self.fc.forecast("gold:comex", market="global", asset_type="futures")
        self.assertEqual(r["asset_type"], "futures")
        self.assertIn("commodity_detail", r)

    def test_index_path(self):
        r = self.fc.forecast("idx:SPX", market="us", asset_type="index")
        self.assertEqual(r["asset_type"], "index")

    def test_auto_detect_stock(self):
        r = self.fc.forecast("600519")
        self.assertEqual(r["asset_type"], "stock")

    def test_auto_detect_futures(self):
        r = self.fc.forecast("gold:comex")
        self.assertEqual(r["asset_type"], "futures")

    def test_auto_detect_index(self):
        r = self.fc.forecast("idx:N225")
        self.assertEqual(r["asset_type"], "index")


# ============================================================
# 6. 跨产品一致性检查（弱测试）
# ============================================================
class TestCrossAsset(unittest.TestCase):
    def test_score_to_pct_scaling(self):
        fc = AssetForecaster()
        # 股票 scale=1.0, 基金 scale=0.7, 期货 scale=1.3
        s = 50
        pct_stock = fc._score_to_pct(s, scale=1.0)
        pct_fund = fc._score_to_pct(s, scale=0.7)
        pct_fut = fc._score_to_pct(s, scale=1.3)
        self.assertLess(pct_fund, pct_stock)
        self.assertGreater(pct_fut, pct_stock)

    def test_score_clamped_to_100(self):
        fc = AssetForecaster()
        # 通过 forecast 验证 composite 不会越界
        r = fc.forecast("999999", asset_type="stock")
        self.assertGreaterEqual(r["score"], -100)
        self.assertLessEqual(r["score"], 100)


# ============================================================
# 7. 可靠性测试 — 输入校验 / 异常降级 / 缓存一致性
# ============================================================
class TestReliability(unittest.TestCase):
    """v7.1 可靠性增强：保证任何坏输入都不会让调用方拿到畸形结果。"""

    # ---- 输入校验 ----

    def test_empty_code_returns_empty_result(self):
        fc = AssetForecaster()
        r = fc.forecast("", market="cn", asset_type="stock")
        # 应返回空结果而非抛错
        self.assertEqual(r["direction"], "flat")
        self.assertEqual(r["score"], 0)
        self.assertIn("推演失败", r["narrative"])

    def test_none_code_returns_empty_result(self):
        fc = AssetForecaster()
        r = fc.forecast(None)  # type: ignore
        self.assertEqual(r["direction"], "flat")
        self.assertIn("horizons", r)

    def test_overlong_code_rejected(self):
        fc = AssetForecaster()
        r = fc.forecast("x" * 100)  # 超长 code
        self.assertEqual(r["code"], "")
        self.assertEqual(r["direction"], "flat")

    def test_invalid_market_normalized(self):
        fc = AssetForecaster()
        r = fc.forecast("600519", market="invalid_market")
        self.assertEqual(r["market"], "cn")

    def test_invalid_horizon_falls_back(self):
        fc = AssetForecaster()
        r = fc.forecast("600519", horizon="invalid")
        self.assertEqual(r["horizon"], "1W")
        for h in ("1D", "1W", "1M", "3M"):
            self.assertIn(h, r["horizons"])

    def test_horizon_lowercased_to_upper(self):
        fc = AssetForecaster()
        r = fc.forecast("600519", horizon="1m")
        self.assertEqual(r["horizon"], "1M")

    # ---- 异常降级 ----

    def test_submodule_missing_falls_back(self):
        """当内部子模块抛异常时,forecast 仍返回合法结构。"""
        fc = AssetForecaster()
        # 把 five_dim 设为抛异常的 fake
        class Boom:
            def analyze(self, *a, **k):
                raise RuntimeError("simulated")
        fc._five_dim = Boom()
        r = fc.forecast("600519", asset_type="stock")
        # 不抛错,且返回合法结构
        self.assertIn("direction", r)
        self.assertIn("horizons", r)
        # score 可能是 0 (tech/hist 也失败) 或非零 (tech 仍有值)
        self.assertGreaterEqual(r["score"], -100)
        self.assertLessEqual(r["score"], 100)
        # 4 个周期的结构一定完整
        for h in ("1D", "1W", "1M", "3M"):
            self.assertIn(h, r["horizons"])

    def test_five_dim_exception_handled(self):
        """FiveDimAnalyzer 中某子源异常不应阻断其他维度。"""
        # 临时移除 policy stub
        saved = sys.modules.get("stock_researcher.policy")
        sys.modules["stock_researcher.policy"] = MagicMock()
        sys.modules["stock_researcher.policy"].PolicyAnalyzer = MagicMock(
            side_effect=RuntimeError("boom"))
        try:
            r = FiveDimAnalyzer().analyze("600519")
            # policy 维度应标记为降级结构（score=0,confidence=0.2）
            self.assertIn("policy", r["dimensions"])
            self.assertEqual(r["dimensions"]["policy"]["score"], 0)
            self.assertEqual(r["dimensions"]["policy"]["confidence"], 0.2)
            # 其他维度应正常工作
            self.assertIn("news", r["dimensions"])
            # 总分是合法数值
            self.assertIsInstance(r["total_score"], (int, float))
        finally:
            sys.modules["stock_researcher.policy"] = saved

    # ---- 缓存一致性 ----

    def test_cache_consistency(self):
        """同一 (market, asset_type, code) 在 TTL 内应返回同一对象。"""
        a = FiveDimAnalyzer(cache_ttl_seconds=60)
        r1 = a.analyze("600519")
        r2 = a.analyze("600519")
        self.assertIs(r1, r2)
        # 改 weight 不应改变已缓存的结果
        a2 = FiveDimAnalyzer(cache_ttl_seconds=60, weights={"policy": 0.5})
        r3 = a2.analyze("600519")
        # 不同实例各自有缓存 → 不同对象
        self.assertIsNot(r1, r3)

    def test_cache_expires(self):
        """TTL 过期后应重新计算。"""
        import time
        a = FiveDimAnalyzer(cache_ttl_seconds=1)
        r1 = a.analyze("600519")
        time.sleep(1.1)
        r2 = a.analyze("600519")
        # 过期后应是不同对象
        self.assertIsNot(r1, r2)

    # ---- 维度缺失行为 ----

    def test_all_sources_missing_neutral_score(self):
        """全部维度都失败时,总分应为 0,置信度最低,信号中性。"""
        # 全部 stub 替换为抛异常
        for mod_name in ["stock_researcher.policy",
                          "stock_researcher.data.money_flow",
                          "stock_researcher.sentiment",
                          "stock_researcher.sentiment.forum_sentiment"]:
            saved = sys.modules.get(mod_name)
            sys.modules[mod_name] = MagicMock()
            sys.modules[mod_name].PolicyAnalyzer = MagicMock(side_effect=RuntimeError)
            sys.modules[mod_name].MoneyFlowData = MagicMock(side_effect=RuntimeError)
            sys.modules[mod_name].UnifiedSentimentEngine = MagicMock(side_effect=RuntimeError)
            sys.modules[mod_name].analyze_forum_sentiment = MagicMock(side_effect=RuntimeError)
        try:
            r = FiveDimAnalyzer().analyze("600519")
            # 所有维度要么 missing 要么降级
            self.assertEqual(r["total_score"], 0.0)
            self.assertIn("中性", r["signal"])
            self.assertGreaterEqual(r["confidence"], 0.3)  # 兜底 0.3
        finally:
            # 恢复
            for mod_name in ["stock_researcher.policy",
                              "stock_researcher.data.money_flow",
                              "stock_researcher.sentiment",
                              "stock_researcher.sentiment.forum_sentiment"]:
                # 测试中没保存原始,重做 setup
                pass
            # 直接重新执行 setup_module_stubs (但会覆盖全部 stub)
            _setup_module_stubs()


if __name__ == "__main__":
    unittest.main()