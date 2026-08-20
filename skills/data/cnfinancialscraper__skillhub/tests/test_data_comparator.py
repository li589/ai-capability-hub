# -*- coding: utf-8 -*-
"""v4.7 同类数据横向对比与回测测试 + 监管政策文件分析测试。

纯本地，不发起网络请求。
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestBacktestSeries(unittest.TestCase):

    def _clean_series(self):
        return [
            {"date": "2026-07-28", "margin_balance": 100.0, "margin_buy": 5.0},
            {"date": "2026-07-29", "margin_balance": 102.0, "margin_buy": 6.0},
            {"date": "2026-07-30", "margin_balance": 105.0, "margin_buy": 4.0},
            {"date": "2026-07-31", "margin_balance": 103.0, "margin_buy": 7.0},
        ]

    def test_clean_series_passes(self):
        from data_comparator import backtest_series
        r = backtest_series("股票A", self._clean_series())
        self.assertTrue(r["passed"])
        self.assertGreaterEqual(r["score"], 60)
        self.assertEqual(r["record_count"], 4)

    def test_empty_series_fails(self):
        from data_comparator import backtest_series
        r = backtest_series("空序列", [])
        self.assertFalse(r["passed"])
        self.assertEqual(r["score"], 0)

    def test_abnormal_jump_detected(self):
        from data_comparator import backtest_series
        series = self._clean_series() + [
            {"date": "2026-08-01", "margin_balance": 5000.0, "margin_buy": 7.0},
        ]
        r = backtest_series("跳变", series, jump_threshold=5.0)
        # 跳变超阈值 → 应有 numeric 问题
        numeric_issues = [i for i in r["issues"] if i["field"] == "margin_balance"]
        self.assertTrue(any("跳变" in i["message"] for i in numeric_issues))

    def test_duplicate_dates_warned(self):
        from data_comparator import backtest_series
        series = self._clean_series() + [
            {"date": "2026-07-31", "margin_balance": 103.0, "margin_buy": 7.0},
        ]
        r = backtest_series("重复", series)
        dup_issues = [i for i in r["issues"] if "重复日期" in i["message"]]
        self.assertTrue(dup_issues)


class TestCompareSeries(unittest.TestCase):

    def test_ranking(self):
        from data_comparator import compare_series
        a = [{"date": "2026-07-31", "margin_balance": 100.0}]
        b = [{"date": "2026-07-31", "margin_balance": 50.0}]
        r = compare_series({"股票A": a, "股票B": b})
        self.assertEqual(r["series_count"], 2)
        rank = r["ranking"]["margin_balance"]
        self.assertEqual(rank[0]["label"], "股票A")  # 值大者第一
        self.assertEqual(rank[1]["label"], "股票B")

    def test_latest_and_change(self):
        from data_comparator import compare_series
        a = [
            {"date": "2026-07-30", "margin_balance": 100.0},
            {"date": "2026-07-31", "margin_balance": 103.0},
        ]
        r = compare_series({"股票A": a})
        self.assertEqual(r["latest"]["股票A"]["margin_balance"], 103.0)
        self.assertEqual(r["change"]["股票A"]["margin_balance"], 3.0)

    def test_empty(self):
        from data_comparator import compare_series
        self.assertEqual(compare_series({})["series_count"], 0)


class TestCompareAndBacktest(unittest.TestCase):

    def test_integration(self):
        from data_comparator import compare_and_backtest
        a = [{"date": "2026-07-31", "margin_balance": 100.0, "margin_buy": 5.0}]
        b = [{"date": "2026-07-31", "margin_balance": 50.0, "margin_buy": 2.0}]
        r = compare_and_backtest({"A": a, "B": b})
        self.assertEqual(len(r["backtests"]), 2)
        self.assertEqual(r["summary"]["group_count"], 2)
        self.assertIn("comparison", r)
        self.assertIn("best", r["summary"])

    def test_format_report(self):
        from data_comparator import compare_and_backtest, format_comparison_report
        a = [{"date": "2026-07-31", "margin_balance": 100.0}]
        r = compare_and_backtest({"A": a})
        text = format_comparison_report(r)
        self.assertIn("横向对比", text)
        self.assertIn("回测", text)


class TestRegulatoryAnalysis(unittest.TestCase):
    """监管政策文件分析（本地文件，无网络）。"""

    def test_analyze_local_file(self):
        from regulatory_scraper import RegulatoryScraper
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         delete=False, encoding="utf-8") as f:
            f.write("某商业银行发布2026年利率政策公告。本公告旨在降低实体经济融资成本。")
            path = f.name
        try:
            r = RegulatoryScraper().analyze_policy(path, keyword="利率")
            self.assertIn("利率", r["keywords_hit"])
            self.assertGreater(r["content_length"], 0)
            self.assertTrue(r["summary"])
        finally:
            Path(path).unlink(missing_ok=True)

    def test_download_invalid_url(self):
        from regulatory_scraper import download_policy_document
        self.assertEqual(download_policy_document(""), "")


if __name__ == "__main__":
    unittest.main()
