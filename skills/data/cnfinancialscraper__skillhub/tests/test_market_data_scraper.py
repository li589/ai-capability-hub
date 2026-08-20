# -*- coding: utf-8 -*-
"""v4.7 市场宏观数据测试（LPR / 国债收益率曲线）。

全部使用 mock，不发起真实网络请求。
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestLprRates(unittest.TestCase):

    def test_parse(self):
        from market_data_scraper import get_lpr_rates
        records = [
            {"showDateCN": "2026-07-20", "1Y": "3.00", "5Y": "3.50"},
            {"showDateCN": "2026-06-22", "1Y": "3.45", "5Y": "3.95"},
        ]
        with mock.patch("market_data_scraper._requests.post") as m:
            resp = mock.MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"records": records}
            m.return_value = resp
            r = get_lpr_rates(days=90)
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0]["date"], "2026-07-20")
        self.assertEqual(r[0]["one_year"], 3.0)
        self.assertEqual(r[0]["five_year"], 3.5)

    def test_empty_on_failure(self):
        from market_data_scraper import get_lpr_rates
        with mock.patch("market_data_scraper._requests.post") as m:
            m.side_effect = Exception("网络错误")
            self.assertEqual(get_lpr_rates(), [])


class TestBondYieldCurve(unittest.TestCase):

    def _fake_data(self):
        # 模拟 inityc 返回：索引→期限代码 + 数值列表（含完整曲线 seriesData）
        codes = {"3": "R01Y", "11": "R02Y", "13": "R03Y", "4": "R05Y",
                 "0": "R07Y", "1": "R10Y", "2": "R30Y"}
        series = []
        # 生成 0-30 年曲线，收益率从 1.0 线性到 3.0
        for year in range(0, 301):
            y = year / 10.0
            series.append([y, 1.0 + y * 0.05])
        curve_obj = {"seriesData": series, "worktime": "2026-07-31",
                     "ycDefName": "中债国债收益率曲线(到期)"}
        return [codes, [10, [curve_obj]]]

    def test_parse_terms(self):
        from market_data_scraper import get_bond_yield_curve
        with mock.patch("market_data_scraper._requests.post") as m:
            resp = mock.MagicMock()
            resp.status_code = 200
            resp.json.return_value = self._fake_data()
            m.return_value = resp
            r = get_bond_yield_curve()
        self.assertEqual(r["date"], "2026-07-31")
        self.assertIn("1Y", r["terms"])
        self.assertIn("10Y", r["terms"])
        self.assertIn("30Y", r["terms"])
        # 1Y 收益 ≈ 1.0 + 1*0.05 = 1.05
        self.assertAlmostEqual(r["terms"]["1Y"], 1.05, places=2)
        # 利差
        self.assertIn("spread_10_2", r)

    def test_error_response(self):
        from market_data_scraper import get_bond_yield_curve
        with mock.patch("market_data_scraper._requests.post") as m:
            resp = mock.MagicMock()
            resp.status_code = 200
            resp.json.return_value = [{"11": "R01Y"}, [10, []]]
            m.return_value = resp
            r = get_bond_yield_curve()
        self.assertIn("warning", r)  # 曲线数据为空时应返回警告

    def test_network_failure(self):
        from market_data_scraper import get_bond_yield_curve
        with mock.patch("market_data_scraper._requests.post") as m:
            m.side_effect = Exception("超时")
            r = get_bond_yield_curve()
        self.assertIn("error", r)


class TestDateNormalize(unittest.TestCase):

    def test_normalize(self):
        from market_data_scraper import _normalize_date
        self.assertEqual(_normalize_date("2026/7/1"), "2026-07-01")
        self.assertEqual(_normalize_date("2026-07-31 00:00:00"), "2026-07-31")
        self.assertEqual(_normalize_date(""), "")
        self.assertEqual(_normalize_date(None), "")


if __name__ == "__main__":
    unittest.main()
