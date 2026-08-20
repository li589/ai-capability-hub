#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.3 数据质量与运行逻辑回归测试

覆盖：
  1. 腾讯行情字段映射：涨跌额/涨跌幅/PE/市值/换手率不再错位
  2. 主力净流入不再被 PE 误读
  3. 港股市场字段按港股映射解析
  4. 基金/ETF 资产类型识别
  5. runtests.py 不再用 os.execvp（Windows stdout OSError）
  6. 版本元数据一致
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))


class _FakeResp:
    def __init__(self, raw: bytes):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self.raw


def _cn_tencent_raw() -> bytes:
    fields = [""] * 60
    fields[1] = "贵州茅台"
    fields[3] = "1350.60"
    fields[4] = "1361.76"
    fields[5] = "1330.03"
    fields[6] = "55128"
    fields[31] = "-11.16"
    fields[32] = "-0.82"
    fields[33] = "1355.72"
    fields[34] = "1325.77"
    fields[37] = "737346"
    fields[38] = "0.44"
    fields[39] = "20.41"
    fields[44] = "16000.00"
    fields[45] = "16883.60"
    return ('v_sh600519="' + "~".join(fields) + '";\n').encode("gbk")


def _hk_tencent_raw() -> bytes:
    fields = [""] * 60
    fields[1] = "腾讯控股"
    fields[3] = "500.00"
    fields[4] = "490.00"
    fields[5] = "495.00"
    fields[6] = "10000"
    fields[31] = "2.00"
    fields[32] = "0.41"
    fields[33] = "505.00"
    fields[34] = "488.00"
    fields[38] = "123456"
    fields[39] = "0.55"
    fields[47] = "45678"
    return ('v_r_hk00700="' + "~".join(fields) + '";\n').encode("gbk")


class TestTencentFieldMapping(unittest.TestCase):
    """腾讯行情字段映射修复回归。"""

    def test_market_data_cn_fields(self):
        from stock_researcher.data.market import MarketData
        md = MarketData()
        with patch("stock_researcher.data.market._retry_request",
                   return_value=_cn_tencent_raw()):
            result = md.fetch_realtime(["600519"])
        row = result["600519"]
        self.assertEqual(row["change"], -11.16)
        self.assertEqual(row["change_pct"], -0.82)
        self.assertEqual(row["pe"], 20.41)
        self.assertEqual(row["amount"], 737346)
        self.assertEqual(row["turnover"], 0.44)
        self.assertEqual(row["mkt_cap"], 16883.60)
        self.assertEqual(row["main_net_flow"], 0.0)
        self.assertEqual(row["source"], "tencent")

    def test_market_data_hk_fields(self):
        from stock_researcher.data.market import MarketData
        md = MarketData()
        with patch("stock_researcher.data.market._retry_request",
                   return_value=_hk_tencent_raw()):
            result = md.fetch_realtime(["hk:00700"])
        row = result["hk:00700"]
        self.assertEqual(row["amount"], 123456)
        self.assertEqual(row["mkt_cap"], 45678)
        self.assertEqual(row["change_pct"], 0.41)

    def test_market_all_stocks_crawler_change_pct(self):
        from stock_researcher.data import market_all_stocks_crawler as mod
        from stock_researcher.data.market_all_stocks_crawler import MarketAllStocksCrawler
        with tempfile.TemporaryDirectory() as d:
            crawler = MarketAllStocksCrawler(data_dir=d)
            with patch.object(mod, "HAS_CRAWL_UTILS", False), \
                 patch("urllib.request.urlopen",
                       return_value=_FakeResp(_cn_tencent_raw())):
                result = crawler.update_realtime_quotes(["600519"])
        self.assertEqual(result["600519"]["change_pct"], -0.82)
        self.assertEqual(result["600519"]["change"], -11.16)

    def test_report_generator_realtime_quote_fields(self):
        from stock_researcher.report import stock_report_generator as mod
        from stock_researcher.report.stock_report_generator import StockResearchReportGenerator
        with tempfile.TemporaryDirectory() as d:
            gen = StockResearchReportGenerator(data_dir=d, output_dir=d)
            with patch.object(mod, "HAS_CRAWL_UTILS", False), \
                 patch("urllib.request.urlopen",
                       return_value=_FakeResp(_cn_tencent_raw())):
                quote = gen._fetch_realtime_quote("600519")
        self.assertEqual(quote["change_pct"], -0.82)
        self.assertEqual(quote["turnover_rate"], 0.44)
        self.assertEqual(quote["market_cap"], 16883.60)
        self.assertEqual(quote["float_capital"], 16000.00)


class TestAssetTypeRecognition(unittest.TestCase):
    """基金/ETF 资产类型识别。"""

    def test_fund_and_etf_prefix(self):
        from stock_researcher.analysis.asset_forecaster import detect_asset_type
        self.assertEqual(detect_asset_type("fund:110022"), "fund")
        self.assertEqual(detect_asset_type("etf:510300"), "fund")

    def test_a_share_fund_codes(self):
        from stock_researcher.analysis.asset_forecaster import detect_asset_type
        self.assertEqual(detect_asset_type("110022"), "fund")
        self.assertEqual(detect_asset_type("510300"), "fund")
        self.assertEqual(detect_asset_type("600519"), "stock")


class TestRuntimeHarnessAndMetadata(unittest.TestCase):
    """运行逻辑与版本元数据一致性。"""

    def test_runtests_uses_pytest_main(self):
        src = (ROOT / "runtests.py").read_text(encoding="utf-8")
        self.assertNotIn("os.execvp", src, "runtests.py 不应再用 os.execvp")
        self.assertIn("pytest.main", src, "runtests.py 应改为同一进程内 pytest.main")

    def test_version_metadata_consistent(self):
        """v7.7 修复：版本号随项目升级同步（当前 7.7）。"""
        settings = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
        meta = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
        # 修复 BUG-007：版本号应统一（v7.7+ 同步到最新）
        self.assertEqual(settings["version"], meta["version"])
        # 版本号格式应为语义化版本
        import re as _re
        self.assertRegex(meta["version"], r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
