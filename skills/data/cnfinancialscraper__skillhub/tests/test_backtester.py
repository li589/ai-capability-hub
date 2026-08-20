# -*- coding: utf-8 -*-
"""crawl_backtester.py 单元测试 — 4 维回测/数字一致性/历史快照。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
from datetime import datetime, timedelta
from scripts.crawl_backtester import (
    CrawlBacktester, quick_backtest,
    _parse_datetime, _extract_numbers,
)


class TestParseDatetime(unittest.TestCase):
    def test_iso(self):
        dt = _parse_datetime("2026-07-29T10:00:00")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 7)
        self.assertEqual(dt.day, 29)

    def test_date_only(self):
        dt = _parse_datetime("2026-07-29")
        self.assertEqual(dt.year, 2026)

    def test_chinese_format(self):
        dt = _parse_datetime("2026年7月29日")
        self.assertEqual(dt.year, 2026)

    def test_relative(self):
        dt = _parse_datetime("3天前")
        self.assertIsNotNone(dt)
        self.assertAlmostEqual((datetime.now() - dt).days, 3, delta=1)

    def test_invalid(self):
        self.assertIsNone(_parse_datetime("not a date"))


class TestExtractNumbers(unittest.TestCase):
    def test_amount_yi(self):
        out = _extract_numbers("营收 1500 亿元")
        self.assertEqual(out["amounts"], [150000000000])

    def test_amount_wan(self):
        out = _extract_numbers("营收 150000 万元")
        self.assertEqual(out["amounts"], [1500000000])

    def test_percentage(self):
        out = _extract_numbers("增长 15.5%")
        self.assertIn(15.5, out["percentages"])

    def test_year(self):
        out = _extract_numbers("2024 年财报")
        self.assertIn(2024, out["years"])

    def test_year_filter(self):
        # 不应抽到手机号/年份外的数字
        out = _extract_numbers("电话 13800138000")
        # 13800138000 不应进入 years（不匹配 19xx/20xx 模式）
        self.assertEqual(out["years"], [])


class TestFreshness(unittest.TestCase):
    def setUp(self):
        self.bt = CrawlBacktester(max_age_days=7)

    def test_fresh(self):
        today = datetime.now().strftime("%Y-%m-%d")
        f = self.bt.check_freshness({"published_at": today})
        self.assertEqual(f["level"], "fresh")
        self.assertGreater(f["score"], 0.8)

    def test_stale(self):
        old = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        f = self.bt.check_freshness({"published_at": old})
        self.assertEqual(f["level"], "stale")

    def test_expired(self):
        old = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        f = self.bt.check_freshness({"published_at": old})
        self.assertEqual(f["level"], "expired")
        self.assertLess(f["score"], 0.3)

    def test_unknown(self):
        f = self.bt.check_freshness({"published_at": None})
        self.assertEqual(f["level"], "unknown")


class TestNumericConsistency(unittest.TestCase):
    def setUp(self):
        self.bt = CrawlBacktester()

    def test_consistent_amounts(self):
        n = self.bt.numeric_consistency({
            "title": "x", "content": "营收 1500 亿元，同比增长 15%"
        })
        self.assertGreaterEqual(len(n["extracted"]["amounts"]), 1)
        self.assertIn(15, n["extracted"]["percentages"])

    def test_inconsistent_years(self):
        n = self.bt.numeric_consistency({
            "title": "x", "content": "2099 年某事"
        })
        self.assertGreater(n["inconsistency_count"], 0)

    def test_clean_text(self):
        n = self.bt.numeric_consistency({
            "title": "x", "content": "无数字内容"
        })
        self.assertEqual(n["inconsistency_count"], 0)


class TestCrossSource(unittest.TestCase):
    def test_no_match_no_snapshot(self):
        bt = CrawlBacktester()
        # 空快照索引 → 应返回 0 matched
        c = bt.cross_source_validate({
            "title": "某新闻",
            "source": "x"
        })
        self.assertEqual(c["matched_sources"], [])


class TestSnapshotCompare(unittest.TestCase):
    def test_newly_emerged_no_history(self):
        bt = CrawlBacktester()
        s = bt.compare_with_snapshot({"title": "全新新闻"})
        self.assertEqual(s["appeared_in_n_snapshots"], 0)
        self.assertTrue(s["newly_emerged"])


class TestFullBacktest(unittest.TestCase):
    def test_fresh_article_passes(self):
        today = datetime.now().strftime("%Y-%m-%d")
        r = quick_backtest({
            "title": "测试",
            "url": "https://x.com",
            "published_at": today,
            "content": "2024 年某事",
            "source": "财联社",
        })
        # 综合分应 >= 0.6
        self.assertGreater(r.overall_score, 0.5)

    def test_old_article_fails(self):
        r = quick_backtest({
            "title": "老新闻",
            "url": "https://x.com",
            "published_at": "2020-01-01",
            "content": "2020 年事",
            "source": "财联社",
        })
        self.assertFalse(r.passed)

    def test_explain_returns_text(self):
        r = quick_backtest({"title": "x"})
        text = CrawlBacktester().explain(r)
        self.assertIn("回测报告", text)


if __name__ == "__main__":
    unittest.main()