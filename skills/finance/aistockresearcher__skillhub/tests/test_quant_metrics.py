#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一量化绩效与风险指标测试（纯标准库，不依赖 numpy/pandas）"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))

import unittest


class TestQuantMetrics(unittest.TestCase):
    def test_basic_metrics(self):
        from stock_researcher.quantitative.metrics import compute_quant_metrics
        prices = [100, 110, 121, 108.9, 119.79]
        m = compute_quant_metrics(prices, symbol="TEST")
        self.assertAlmostEqual(m.total_return_pct, 19.79, places=2)
        self.assertAlmostEqual(m.max_drawdown_pct, 10.0, places=2)
        self.assertEqual(m.positive_days, 3)
        self.assertEqual(m.negative_days, 1)
        self.assertAlmostEqual(m.best_day_pct, 10.0, places=2)
        self.assertAlmostEqual(m.worst_day_pct, -10.0, places=2)
        self.assertGreater(m.sharpe_ratio, 0)
        self.assertGreater(m.sortino_ratio, 0)

    def test_benchmark_metrics(self):
        from stock_researcher.quantitative.metrics import compute_quant_metrics
        prices = [100.0]
        for i in range(1, 30):
            chg = 0.01 if i % 2 else -0.005
            prices.append(round(prices[-1] * (1 + chg), 6))
        m = compute_quant_metrics(prices, benchmark_prices=prices,
                                  risk_free=0.0, symbol="BENCH")
        self.assertAlmostEqual(m.beta, 1.0, places=4)
        self.assertAlmostEqual(m.correlation, 1.0, places=4)
        self.assertAlmostEqual(m.tracking_error_pct, 0.0, places=4)
        self.assertAlmostEqual(m.alpha_annual_pct, 0.0, places=2)

    def test_insufficient_data(self):
        from stock_researcher.quantitative.metrics import compute_quant_metrics
        m = compute_quant_metrics([100], symbol="SHORT")
        self.assertEqual(m.data_points, 1)
        self.assertIsNone(m.total_return_pct)
        self.assertIsNone(m.sharpe_ratio)

    def test_daily_returns_clean_invalid(self):
        from stock_researcher.quantitative.metrics import daily_returns
        rets = daily_returns([100, "bad", 110, None, 121])
        self.assertEqual(len(rets), 2)
        self.assertAlmostEqual(rets[0], 0.10, places=6)
        self.assertAlmostEqual(rets[1], 0.10, places=6)

    def test_top_level_export_without_numpy(self):
        from stock_researcher.quantitative import compute_quant_metrics, QuantMetrics
        m = compute_quant_metrics([100, 101, 102, 103, 104])
        self.assertIsInstance(m, QuantMetrics)

    def test_format_output(self):
        from stock_researcher.quantitative.metrics import (
            compute_quant_metrics,
            format_quant_metrics,
        )
        m = compute_quant_metrics([100, 101, 102, 103, 104], symbol="TEST")
        text = format_quant_metrics(m)
        self.assertIn("量化体检", text)
        self.assertIn("TEST", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
