# -*- coding: utf-8 -*-
"""v4.7 东方财富新增数据函数测试（两融/大宗/ETF流/龙虎榜席位/股东增减持）。

全部使用 mock，不发起真实网络请求，可在离线环境运行。
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ==================== 两融 ====================

class TestMarginTrading(unittest.TestCase):

    def _sample(self):
        return [{
            "DATE": "2026-07-31 00:00:00", "MARKET": "1", "SCODE": "600519",
            "SECNAME": "贵州茅台", "RZYE": "18520000000", "RQYE": "130000000",
            "RZRQYE": "18650000000", "RZRQYECZ": "210000000",
            "RZMRE": "560000000", "RZCHE": "380000000", "RZJME": "180000000",
            "RQMCL": "125000", "RQYL": "89000",
        }]

    def test_parse_fields(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get",
                        return_value=self._sample()):
            from eastmoney_scraper import get_margin_trading
            r = get_margin_trading(limit=10)
            self.assertEqual(len(r), 1)
            item = r[0]
            self.assertEqual(item["code"], "600519")
            self.assertEqual(item["name"], "贵州茅台")
            self.assertEqual(item["margin_balance"], 185.2)   # 亿元
            self.assertEqual(item["short_balance"], 1.3)
            self.assertEqual(item["margin_short_total"], 186.5)
            self.assertEqual(item["margin_net_buy"], 1.8)

    def test_empty_on_failure(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=[]):
            from eastmoney_scraper import get_margin_trading
            self.assertEqual(get_margin_trading(), [])

    def test_date_filter(self):
        data = [{"DATE": "2026-07-31 00:00:00", "SCODE": "600519", "SECNAME": "A", "RZYE": "1"},
                {"DATE": "2026-07-01 00:00:00", "SCODE": "000001", "SECNAME": "B", "RZYE": "2"}]
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=data):
            from eastmoney_scraper import get_margin_trading
            r = get_margin_trading(start_date="2026-07-30", end_date="2026-07-31")
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0]["code"], "600519")

    def test_market_filter_passed(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get",
                        return_value=[]) as mocked:
            from eastmoney_scraper import get_margin_trading
            get_margin_trading(market="sh")
            # 校验 filter 包含 MARKET='1'
            args, kwargs = mocked.call_args
            self.assertIn("(MARKET='1')", kwargs.get("filter_str", ""))


# ==================== 大宗交易 ====================

class TestBlockTrades(unittest.TestCase):

    def test_parse_datacenter(self):
        data = [{
            "TRADE_DATE": "2026-07-31 00:00:00", "SECURITY_CODE": "600519",
            "SECURITY_NAME_ABBR": "贵州茅台", "DEAL_PRICE": 1600.0,
            "CLOSE_PRICE": 1650.0, "PREMIUM_RATIO": -0.0303,
            "DEAL_VOLUME": 500000, "DEAL_AMT": 800000000,
            "BUYER_NAME": "机构专用", "SELLER_NAME": "中信证券",
            "CHANGE_RATE": 1.2, "TURNOVER_RATE": 0.5,
        }]
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=data):
            from eastmoney_scraper import get_block_trades
            r = get_block_trades(limit=10)
            self.assertEqual(len(r), 1)
            item = r[0]
            self.assertEqual(item["code"], "600519")
            self.assertEqual(item["price"], 1600.0)
            self.assertEqual(item["discount_pct"], -3.03)
            self.assertEqual(item["volume"], 500000)
            self.assertEqual(item["buyer_branch"], "机构专用")

    def test_empty_on_failure(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=[]):
            from eastmoney_scraper import get_block_trades
            self.assertEqual(get_block_trades(), [])


# ==================== ETF 资金流 ====================

class TestEtfFundFlow(unittest.TestCase):

    def test_parse(self):
        data = {"data": {"diff": [{
            "f12": "510050", "f14": "上证50ETF", "f2": 2.865, "f3": 0.35,
            "f20": 58050000000, "f62": 250000000, "f66": 120000000,
            "f72": 130000000, "f78": -50000000, "f84": -200000000,
            "f124": "2026-07-31",
        }]}}
        with mock.patch("eastmoney_scraper._em_json_get", return_value=data):
            from eastmoney_scraper import get_etf_fund_flow
            r = get_etf_fund_flow(limit=10)
            self.assertEqual(len(r), 1)
            item = r[0]
            self.assertEqual(item["code"], "510050")
            self.assertEqual(item["name"], "上证50ETF")
            self.assertEqual(item["main_net_inflow"], 2.5)
            self.assertEqual(item["super_large_net"], 1.2)

    def test_empty_on_failure(self):
        with mock.patch("eastmoney_scraper._em_json_get", return_value=None):
            from eastmoney_scraper import get_etf_fund_flow
            self.assertEqual(get_etf_fund_flow(), [])


# ==================== 龙虎榜席位 ====================

class TestDragonTigerSeats(unittest.TestCase):

    def test_parse(self):
        data = [{
            "SECURITY_CODE": "000628", "SECURITY_NAME_ABBR": "高新发展",
            "TRADE_DATE": "2026-07-31 00:00:00",
            "BILLBOARD_BUY_AMT": 1580000000, "BILLBOARD_SELL_AMT": 1230000000,
            "BILLBOARD_NET_AMT": 350000000, "CHANGE_RATE": 10.02,
            "CLOSE_PRICE": 35.5, "EXPLANATION": "日涨幅偏离值达7%",
            "BUY_RATIO": 8.5, "SELL_RATIO": 6.2,
            "BUY_SEAT": "机构专用；中信证券深圳分公司",
            "SELL_SEAT": "机构专用",
        }]
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=data):
            from eastmoney_scraper import get_dragon_tiger_seats
            r = get_dragon_tiger_seats("000628")
            self.assertEqual(r["code"], "000628")
            self.assertEqual(r["total_buy"], 15.8)
            self.assertEqual(r["net"], 3.5)
            self.assertIn("机构专用", r["buy_seats"])

    def test_fallback_on_empty(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=[]), \
             mock.patch("eastmoney_scraper.get_dragon_tiger", return_value=[]):
            from eastmoney_scraper import get_dragon_tiger_seats
            r = get_dragon_tiger_seats("000628")
            self.assertIn("warning", r)
            self.assertIn("error", r)


# ==================== 股东增减持 ====================

class TestShareholderChanges(unittest.TestCase):

    def _sample(self):
        return [{
            "CHANGE_DATE": "2026-07-31 00:00:00", "SECURITY_CODE": "600519",
            "SECURITY_NAME": "贵州茅台", "PERSON_NAME": "张三",
            "CHANGE_SHARES": -50000, "CHANGE_RATIO": -0.12,
            "AVERAGE_PRICE": 1650.0, "CHANGE_AMOUNT": -82500000,
            "CHANGE_AFTER_HOLDNUM": 25000000, "CHANGE_REASON": "个人资金需求",
            "POSITION_NAME": "董事",
        }]

    def test_parse_direction(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get",
                        return_value=self._sample()):
            from eastmoney_scraper import get_shareholder_changes
            r = get_shareholder_changes(limit=10)
            self.assertEqual(len(r), 1)
            item = r[0]
            # 负变动 → 减持
            self.assertEqual(item["change_type"], "减持")
            self.assertEqual(item["change_shares"], -50000)
            self.assertEqual(item["person"], "张三")

    def test_change_type_filter(self):
        data = self._sample() + [{
            "CHANGE_DATE": "2026-07-30 00:00:00", "SECURITY_CODE": "000001",
            "SECURITY_NAME": "平安银行", "PERSON_NAME": "李四",
            "CHANGE_SHARES": 100000, "CHANGE_REASON": "增持",
            "POSITION_NAME": "",
        }]
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=data):
            from eastmoney_scraper import get_shareholder_changes
            r = get_shareholder_changes(change_type="增持")
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0]["person"], "李四")

    def test_empty_on_failure(self):
        with mock.patch("eastmoney_scraper._em_datacenter_get", return_value=[]):
            from eastmoney_scraper import get_shareholder_changes
            self.assertEqual(get_shareholder_changes(), [])


# ==================== 安全转换边界 ====================

class TestSafeConvertBoundary(unittest.TestCase):

    def test_safe_float_edge(self):
        from eastmoney_scraper import _safe_float
        self.assertEqual(_safe_float(None), 0.0)
        self.assertEqual(_safe_float("-"), 0.0)
        self.assertEqual(_safe_float("--"), 0.0)
        self.assertEqual(_safe_float(""), 0.0)
        self.assertEqual(_safe_float("1.23"), 1.23)
        self.assertEqual(_safe_float("abc", 9.9), 9.9)

    def test_safe_int_edge(self):
        from eastmoney_scraper import _safe_int
        self.assertEqual(_safe_int("0"), 0)
        self.assertEqual(_safe_int(None), 0)
        self.assertEqual(_safe_int("42"), 42)


if __name__ == "__main__":
    unittest.main()
