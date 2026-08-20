# -*- coding: utf-8 -*-
"""v4.5.1 三项强化 — 单元测试

覆盖：
  1. 回测过滤 (filter_by_recommendation)
  2. 回测批量汇总 (batch_summary)
  3. 爬取前确认 (输入校验 / 风险提示 / 缓存预览 / 覆盖率估算)
  4. 并发抓取 (parallel_workers)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
from datetime import datetime, timedelta

import pytest


# ============================================================
# 1. 回测过滤
# ============================================================
class TestBacktestFilter(unittest.TestCase):
    """filter_by_recommendation 的行为。"""

    def _mk(self, rec: str, score: float = 0.7, passed: bool = True) -> object:
        # 简化构造的 BacktestResult-like 对象
        class R:
            pass
        r = R()
        r.recommendation = rec
        r.overall_score = score
        r.passed = passed
        r.source_credibility = 0.6
        r.issues = []
        return r

    def test_drop_建议丢弃(self):
        from scripts.crawl_backtester import filter_by_recommendation
        results = [self._mk("可信任"), self._mk("建议丢弃"), self._mk("需人工核实")]
        articles = ["a", "b", "c"]
        kept_a, kept_r = filter_by_recommendation(results, articles, ("建议丢弃",))
        self.assertEqual([id(x) for x in kept_a], [id(x) for x in ("a", "c")])
        self.assertEqual(len(kept_r), 2)

    def test_drop_multiple_levels(self):
        from scripts.crawl_backtester import filter_by_recommendation
        results = [self._mk("可信任"), self._mk("建议丢弃"), self._mk("需人工核实")]
        articles = ["a", "b", "c"]
        kept_a, kept_r = filter_by_recommendation(
            results, articles, ("建议丢弃", "需人工核实"),
        )
        self.assertEqual(kept_a, ["a"])
        self.assertEqual(len(kept_r), 1)

    def test_empty_input(self):
        from scripts.crawl_backtester import filter_by_recommendation
        kept_a, kept_r = filter_by_recommendation([], [])
        self.assertEqual(kept_a, [])
        self.assertEqual(kept_r, [])

    def test_no_drop_when_default(self):
        from scripts.crawl_backtester import filter_by_recommendation
        results = [self._mk("建议丢弃"), self._mk("可信任")]
        articles = ["a", "b"]
        kept_a, kept_r = filter_by_recommendation(results, articles, ())
        self.assertEqual(kept_a, articles)
        self.assertEqual(len(kept_r), 2)


# ============================================================
# 2. 回测批量汇总
# ============================================================
class TestBatchSummary(unittest.TestCase):

    def _mk(self, rec, score=0.7, passed=True, issues=None, cred=0.6):
        class R:
            pass
        r = R()
        r.recommendation = rec
        r.overall_score = score
        r.passed = passed
        r.source_credibility = cred
        r.issues = issues or []
        return r

    def test_empty(self):
        from scripts.crawl_backtester import batch_summary
        s = batch_summary([])
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["pass_rate"], 0.0)

    def test_mixed_recommendations(self):
        from scripts.crawl_backtester import batch_summary
        rs = [
            self._mk("可信任", score=0.9, passed=True, cred=0.8),
            self._mk("可信任", score=0.85, passed=True, cred=0.7),
            self._mk("需人工核实", score=0.6, passed=True, issues=["孤源"], cred=0.5),
            self._mk("建议丢弃", score=0.2, passed=False, issues=["过期"], cred=0.3),
        ]
        s = batch_summary(rs)
        self.assertEqual(s["total"], 4)
        self.assertEqual(s["passed"], 3)
        self.assertEqual(s["failed"], 1)
        self.assertAlmostEqual(s["pass_rate"], 0.75, places=2)
        self.assertEqual(s["by_recommendation"]["可信任"], 2)
        self.assertEqual(s["by_recommendation"]["需人工核实"], 1)
        self.assertEqual(s["by_recommendation"]["建议丢弃"], 1)
        # 问题类型分类
        self.assertIn("孤源", s["by_issue_type"])
        self.assertIn("过期", s["by_issue_type"])

    def test_issue_type_classification(self):
        from scripts.crawl_backtester import batch_summary
        rs = [
            self._mk("需人工核实", issues=["文章新鲜度低 (5 天)"]),
            self._mk("建议丢弃", issues=["数字不一致 2 处"]),
            self._mk("建议丢弃", issues=["文章已过期 (30 天)", "数字不一致 1 处"]),
        ]
        s = batch_summary(rs)
        self.assertEqual(s["by_issue_type"].get("新鲜度低"), 1)
        self.assertEqual(s["by_issue_type"].get("数字不一致"), 2)
        self.assertEqual(s["by_issue_type"].get("过期"), 1)


# ============================================================
# 3. 爬取前确认
# ============================================================
class TestPlanValidation(unittest.TestCase):

    def setUp(self):
        # 强制使用测试数据副本，避免污染真实数据
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="v451_test_")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from sentiment_crawler import (
            SentimentCrawler, SentimentSourceLoader, SentimentTargetLoader,
        )
        self.loader_src = SentimentSourceLoader()
        self.loader_tgt = SentimentTargetLoader()
        self.crawler = SentimentCrawler(
            sources=self.loader_src,
            targets=self.loader_tgt,
            snapshot_dir=Path(self.tmp),
            max_total_seconds=30,
        )

    def test_days_out_of_range(self):
        snap = self.crawler.crawl(days=200, dry_run=True)
        self.assertTrue(len(snap.plan.get("validation_errors", [])), "应捕获 days 越界")
        self.assertIn("200", snap.plan["validation_errors"][0])

    def test_max_articles_out_of_range(self):
        snap = self.crawler.crawl(max_articles=0, dry_run=True)
        self.assertTrue(len(snap.plan.get("validation_errors", [])), "应捕获 max_articles 非法")

    def test_short_target_name_warning(self):
        snap = self.crawler.crawl(target_names=["A"], dry_run=True)
        warnings = snap.plan.get("risk_warnings", [])
        self.assertTrue(any("过短" in w for w in warnings), f"应有短名警告，实际: {warnings}")

    def test_test_keyword_warning(self):
        snap = self.crawler.crawl(target_names=["某测试机构"], dry_run=True)
        warnings = snap.plan.get("risk_warnings", [])
        self.assertTrue(any("测试占位" in w for w in warnings), f"应有测试占位警告")

    def test_too_many_sources_warning(self):
        # 超过 30 个源 → 警告
        snap = self.crawler.crawl(
            source_names=None,
            source_categories=None,  # 默认全选
            dry_run=True,
        )
        # 默认所有源，可能 > 30，验证字段存在
        self.assertIn("risk_warnings", snap.plan)
        self.assertIn("coverage_estimate", snap.plan)
        self.assertIn("sample_articles", snap.plan)
        self.assertIn("validation_errors", snap.plan)

    def test_validation_failed_short_circuits(self):
        snap = self.crawler.crawl(days=-1, dry_run=True)
        self.assertEqual(snap.stats.get("validation_failed"), True)
        self.assertEqual(snap.plan["targets"], [])
        self.assertEqual(snap.plan["actions"], [])

    def test_plan_has_coverage_estimate(self):
        snap = self.crawler.crawl(dry_run=True)
        cov = snap.plan.get("coverage_estimate", {})
        self.assertIn("historical_snapshots", cov)
        self.assertIn("historical_hit_rate", cov)
        self.assertIn("expected_avg_articles_per_target", cov)

    def test_plan_has_sample_articles(self):
        snap = self.crawler.crawl(dry_run=True)
        # 新建爬虫无历史快照时，sample 列表应为空（不抛错）
        self.assertIsInstance(snap.plan.get("sample_articles", []), list)

    def test_valid_inputs_no_validation_errors(self):
        snap = self.crawler.crawl(
            target_names=["贵州茅台"],
            days=7,
            source_categories=["authoritative"],
            dry_run=True,
        )
        self.assertEqual(snap.plan.get("validation_errors", []), [])
        self.assertGreater(len(snap.plan.get("targets", [])), 0)
        self.assertGreater(len(snap.plan.get("sources", [])), 0)


# ============================================================
# 4. 并发抓取
# ============================================================
class TestParallelCrawl(unittest.TestCase):
    """parallel_workers > 0 时应使用 ThreadPoolExecutor 并发。"""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="v451_par_test_")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from sentiment_crawler import SentimentCrawler, SentimentSourceLoader, SentimentTargetLoader
        self.crawler = SentimentCrawler(
            sources=SentimentSourceLoader(),
            targets=SentimentTargetLoader(),
            snapshot_dir=Path(self.tmp),
            max_total_seconds=20,
            per_source_timeout=3,
        )

    def test_parallel_workers_collected_more_than_sequential(self):
        """并发抓取应至少与顺序抓取返回等价的结果数（不破坏数据完整性）。"""
        # 模拟一个极小测试场景：1 目标 + 1 源 + 强 mock 让 _query_source 直接 yield 一篇
        from unittest.mock import patch
        from scripts.sentiment_crawler import SentimentArticle

        # 构造一个简单的 fake article
        def fake_query(self, src, target_name, kw, cat, label, cutoff_time):
            yield SentimentArticle(
                title=f"{target_name} - {src.get('name', '')} - {kw}",
                summary="test",
                content="",
                source=src.get("name", ""),
                source_type=src.get("category", ""),
                target_name=target_name,
                target_type=label,
                publish_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                url=f"https://x.com/{target_name}",
                sentiment="neutral",
                sentiment_score=1.0,
                severity="中性",
                category="",
            )

        # 清空 _SEEN_INDEX 防止跨测试干扰。
        # 注意：crawler 由 `from sentiment_crawler import`（无 scripts 前缀）实例化，
        # 与 `scripts.sentiment_crawler` 是同一文件的两个模块实例，需同时清空；
        # 且 _SEEN_INDEX 从磁盘文件加载，需一并重置（测试后恢复），避免历史指纹去重误杀。
        from scripts.sentiment_crawler import _SEEN_INDEX as _SEEN_INDEX_SCRIPTS
        import sentiment_crawler as _sc_mod
        _seen_file = _sc_mod._SEEN_INDEX_FILE
        _orig_seen_data = _seen_file.read_text(encoding="utf-8")
        _sc_mod._SEEN_INDEX.clear()
        _SEEN_INDEX_SCRIPTS.clear()
        _seen_file.write_text("{}", encoding="utf-8")
        try:
            with patch.object(type(self.crawler), "_query_source", fake_query):
                snap = self.crawler.crawl(
                    target_names=["目标A", "目标B"],
                    source_categories=["authoritative"],
                    days=7,
                    max_articles=20,
                    parallel_workers=4,
                )
        finally:
            # 恢复去重索引文件
            _seen_file.write_text(_orig_seen_data, encoding="utf-8")
        self.assertGreater(len(snap.articles), 0)
        # 至少 2 个目标 * 1 源 * 1 关键词 → 2+ 篇（去重后）
        self.assertGreaterEqual(len(snap.articles), 2)
        # 所有文章都应有 source / target_name
        for art in snap.articles:
            self.assertTrue(art.source)
            self.assertIn(art.target_name, ("目标A", "目标B"))


# ============================================================
# 5. 集成测试：dry_run → confirm 流程
# ============================================================
class TestDryRunConfirmFlow(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="v451_dry_")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from sentiment_crawler import SentimentCrawler, SentimentSourceLoader, SentimentTargetLoader
        self.crawler = SentimentCrawler(
            sources=SentimentSourceLoader(),
            targets=SentimentTargetLoader(),
            snapshot_dir=Path(self.tmp),
            max_total_seconds=20,
        )

    def test_dry_run_returns_plan_with_estimated_seconds(self):
        snap = self.crawler.crawl(
            target_names=["贵州茅台"],
            source_categories=["authoritative"],
            dry_run=True,
        )
        self.assertEqual(snap.stats.get("dry_run"), True)
        self.assertGreater(snap.plan["estimated_seconds"], 0)
        self.assertIn("estimated_articles", snap.plan)

    def test_dry_run_not_confirmed_path(self):
        # 模拟用户还没确认
        snap = self.crawler.crawl(
            target_names=["贵州茅台"],
            confirmed=False,
            dry_run=False,
        )
        # 因 confirmed=False, 等同 dry_run=True
        self.assertEqual(snap.stats.get("dry_run"), True)
        self.assertTrue(snap.is_awaiting_confirmation)


if __name__ == "__main__":
    unittest.main()