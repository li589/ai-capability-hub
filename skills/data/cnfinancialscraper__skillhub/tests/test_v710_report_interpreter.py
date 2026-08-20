# -*- coding: utf-8 -*-
"""v7.1.0 定期报告分析解读引擎测试（全离线 mock 数据）。"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

from scripts.report_interpreter import (
    ReportInterpreter, interpret_data, normalize_period, _band, _f,
)

# 高增长优质公司（模拟）：茅台式
GOOD_PERIODS = [
    {"REPORTDATE": "2026-06-30 00:00:00", "SECURITY_NAME_ABBR": "示例股份",
     "TOTAL_OPERATE_INCOME": 92_278_000_000.0, "PARENT_NETPROFIT": 44_517_000_000.0,
     "BASIC_EPS": 35.57, "WEIGHTAVG_ROE": 16.8, "XSMLL": 89.6,
     "YSTZ": 12.3, "SJLTZ": 18.5, "YSHZ": -5.0, "SJLHZ": -8.0,
     "MGJYXJJE": 56.5, "BPS": 200.99},
    {"REPORTDATE": "2026-03-31 00:00:00", "SECURITY_NAME_ABBR": "示例股份",
     "TOTAL_OPERATE_INCOME": 40_000_000_000.0, "PARENT_NETPROFIT": 20_000_000_000.0,
     "BASIC_EPS": 16.0, "WEIGHTAVG_ROE": 7.5, "XSMLL": 88.0,
     "YSTZ": 9.0, "SJLTZ": 15.0, "MGJYXJJE": 22.0, "BPS": 190.0},
]

# 承压公司（模拟）：营收净利双降
BAD_PERIODS = [
    {"REPORTDATE": "2026-06-30 00:00:00", "SECURITY_NAME_ABBR": "示例承压",
     "TOTAL_OPERATE_INCOME": 5_000_000_000.0, "PARENT_NETPROFIT": -300_000_000.0,
     "BASIC_EPS": -0.15, "WEIGHTAVG_ROE": -2.5, "XSMLL": 15.0,
     "YSTZ": -22.5, "SJLTZ": -45.0, "MGJYXJJE": -0.8, "BPS": 1.2},
    {"REPORTDATE": "2026-03-31 00:00:00", "SECURITY_NAME_ABBR": "示例承压",
     "TOTAL_OPERATE_INCOME": 2_800_000_000.0, "PARENT_NETPROFIT": 50_000_000.0,
     "BASIC_EPS": 0.02, "WEIGHTAVG_ROE": 0.4, "XSMLL": 18.0,
     "YSTZ": -10.0, "SJLTZ": -12.0, "MGJYXJJE": -0.2, "BPS": 1.3},
]


class TestReportInterpreter(unittest.TestCase):
    """解读引擎核心：归一化 / 指标 / 信号 / 评分 / 文本。"""

    def test_normalize_period(self):
        row = normalize_period(GOOD_PERIODS[0])
        self.assertAlmostEqual(row["revenue"], 92_278_000_000.0)
        self.assertAlmostEqual(row["net_profit"], 44_517_000_000.0)
        self.assertAlmostEqual(row["gross_margin"], 89.6)
        self.assertAlmostEqual(row["revenue_yoy"], 12.3)
        self.assertEqual(row["name"], "示例股份")
        self.assertIn("report_date", row)

    def test_f_float_safety(self):
        self.assertIsNone(_f(None))
        self.assertIsNone(_f("-"))
        self.assertIsNone(_f("--"))
        self.assertAlmostEqual(_f("12.5%"), 12.5)
        self.assertAlmostEqual(_f("1,234.5"), 1234.5)

    def test_band_ranges(self):
        label, _ = _band(35.0, {"30~50": ("x", "{}")} if False else {
            ">30": ("高增长", "{}"), "10~30": ("稳健", "{}"),
            "0~10": ("低增长", "{}"), "<0": ("下滑", "{}")})
        self.assertEqual(label, "高增长")
        label2, _ = _band(-3.0, {
            ">30": ("高增长", "{}"), "10~30": ("稳健", "{}"),
            "0~10": ("低增长", "{}"), "<0": ("下滑", "{}")})
        self.assertEqual(label2, "下滑")

    def test_interpret_good_company(self):
        result = ReportInterpreter().interpret(GOOD_PERIODS)
        self.assertNotIn("error", result)
        self.assertAlmostEqual(result["revenue"], 92_278_000_000.0)
        self.assertGreaterEqual(result["score"], 70)      # 优质公司高分
        self.assertIn(result["rating"], ("积极", "中性偏积极"))
        # 亮点应包含增长/高毛利信号
        hl = " ".join(result["highlights"])
        self.assertIn("毛利率", hl)
        # 环比下滑进风险
        self.assertTrue(any("环比" in r for r in result["risks"]))

    def test_interpret_bad_company(self):
        result = ReportInterpreter().interpret(BAD_PERIODS)
        self.assertNotIn("error", result)
        self.assertLess(result["score"], 45)              # 承压公司低分
        self.assertEqual(result["rating"], "谨慎")
        risk = " ".join(result["risks"])
        self.assertIn("下滑", risk)
        self.assertIn("现金流", risk)                     # 经营现金流为负
        self.assertGreaterEqual(len(result["risks"]), 3)

    def test_interpret_data_single_dict(self):
        result = interpret_data({"营收": 1000.0, "净利润": 200.0,
                                 "毛利率": 45.0, "ROE": 15.0,
                                 "营收同比": 25.0, "净利同比": 35.0,
                                 "EPS": 2.0, "每股经营现金流": 2.5})
        self.assertNotIn("error", result)
        self.assertGreaterEqual(result["score"], 70)

    def test_interpret_empty(self):
        result = ReportInterpreter().interpret([])
        self.assertIn("error", result)
        self.assertIn("无财务数据", result["error"])

    def test_format_text_structure(self):
        result = ReportInterpreter().interpret(GOOD_PERIODS)
        text = result["text"]
        for key in ("定期报告解读", "业绩概览", "盈利能力", "亮点信号",
                    "综合评分", "不构成投资建议"):
            self.assertIn(key, text)

    def test_missing_fields_graceful(self):
        result = interpret_data({"营收": 100.0})   # 只有营收
        self.assertNotIn("error", result)
        self.assertIsNotNone(result.get("text"))
        self.assertEqual(result["rating"], "数据不足")


class TestSanitizationV710(unittest.TestCase):
    """v7.1.0 新增文件脱敏零残留。"""

    def test_report_interpreter_clean(self):
        src = (Path(__file__).resolve().parent.parent
               / "scripts" / "report_interpreter.py").read_text(encoding="utf-8")
        for term in ("gov.cn", "人民日报", "新华社", "央视财经"):
            self.assertNotIn(term, src)


if __name__ == "__main__":
    unittest.main()
