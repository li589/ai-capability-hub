# -*- coding: utf-8 -*-
"""v4.7 北交所数据函数测试。

全部使用 mock，不发起真实网络请求。
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestBseStocks(unittest.TestCase):

    def _fake_em_data(self):
        return {"data": {"diff": [
            {"f12": "837592", "f14": "华信永道", "f13": "837592",
             "f26": "2023-02-16", "f100": "信息技术", "f2": 12.5},
        ]}}

    def test_parse_em_fallback(self):
        """北交所原生接口失败时应降级到东方财富并正确解析。"""
        from exchange_scraper import get_bse_stocks
        # 原生接口返回异常参数错误
        with mock.patch("exchange_scraper._fetch_bse_native", return_value=None), \
             mock.patch("exchange_scraper._fetch_em_bse_stocks",
                        return_value=self._fake_em_data()["data"]["diff"] and [{
                            "code": "837592", "name": "华信永道",
                            "short_code": "837592", "listing_date": "2023-02-16",
                            "industry": "信息技术", "market": "bj",
                        }]):
            r = get_bse_stocks(limit=10)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["code"], "837592")
        self.assertEqual(r[0]["name"], "华信永道")
        self.assertEqual(r[0]["market"], "bj")

    def test_empty_on_failure(self):
        from exchange_scraper import get_bse_stocks
        with mock.patch("exchange_scraper._fetch_bse_native", return_value=None), \
             mock.patch("exchange_scraper._fetch_em_bse_stocks", return_value=[]):
            self.assertEqual(get_bse_stocks(), [])

    def test_parse_native(self):
        """北交所原生接口正常返回时应直接解析。"""
        from exchange_scraper import get_bse_stocks
        native = '[{"xxzqdm":"837592","jc":"华信永道","ssrq":"2023-02-16","hy":"信息技术"}]'
        with mock.patch("exchange_scraper._fetch_bse_native", return_value=native):
            r = get_bse_stocks()
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["code"], "837592")
        self.assertEqual(r[0]["name"], "华信永道")


class TestBseIpo(unittest.TestCase):

    def test_parse_native(self):
        from exchange_scraper import get_bse_ipo
        native = '[{"xxzqdm":"920001","jc":"某北交所公司","zt":"已注册","sxrq":"2026-07-31"}]'
        with mock.patch("exchange_scraper._fetch_bse_native", return_value=native):
            r = get_bse_ipo(limit=10)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["code"], "920001")
        self.assertEqual(r[0]["status"], "已注册")
        self.assertEqual(r[0]["market"], "bj")

    def test_empty_on_failure(self):
        from exchange_scraper import get_bse_ipo
        with mock.patch("exchange_scraper._fetch_bse_native", return_value=None), \
             mock.patch("exchange_scraper.get_ipo_calendar", return_value=[]):
            self.assertEqual(get_bse_ipo(), [])


if __name__ == "__main__":
    unittest.main()
