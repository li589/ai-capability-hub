#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.2 BUG 修复 + 数据质量回归测试

策略：直接 import 真实子模块（避免污染 sys.modules），用最小 stub 隔离。
覆盖 6 个修复点：
  1. AssetForecaster._get_technical_score 签名错误（修后能拿到真实 tech_score）
  2. _build_stock_narrative 字段名错误（composite_score → tech_score）
  3. StockResearcher.analyze_stock 的 analysis_start 起始日期逻辑（不再误用 strptime）
  4. StockResearcher.generate_report 参数完整转发 (start_date/end_date/strict)
  5. stock_researcher.__version__ = "7.2.0"
  6. data_quality 模块四级标记
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import unittest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Dict


# ============================================================
# 测试 1+2：AssetForecaster._get_technical_score / _build_stock_narrative
# （不需要 import 主包，直接 import asset_forecaster）
# ============================================================
class TestV72AssetForecasterTechScore(unittest.TestCase):
    """v7.2 BUG 修复：_get_technical_score 签名错误 + narrative 字段名"""

    def setUp(self):
        # 用 MagicMock 隔离 _get_technical_score 内部的依赖
        from stock_researcher.analysis.asset_forecaster import AssetForecaster
        self.AssetForecaster = AssetForecaster

    def test_technical_score_uses_correct_signature(self):
        """修后 _get_technical_score 调用 ta.analyze(code, prices)，能拿到真实 tech_score。"""
        from stock_researcher.analysis.asset_forecaster import AssetForecaster
        af = AssetForecaster()

        # Mock MarketData.fetch_history 返回模拟收盘价
        # Mock TechnicalAnalyzer.analyze 返回的实例 tech_score=42
        fake_tech_instance = SimpleNamespace(tech_score=42.0, tech_signal="买入")

        with patch("stock_researcher.data.market.MarketData") as MockMarket, \
             patch("stock_researcher.core.technical.TechnicalAnalyzer") as MockTA:
            MockMarket.return_value.fetch_history.return_value = {
                "closes": [100 + i * 0.05 for i in range(250)],
            }
            MockTA.return_value.analyze.return_value = fake_tech_instance

            score, factors = af._get_technical_score("600519", "cn")

        self.assertEqual(score, 42.0, "应返回 Fake 技术分 42.0")
        self.assertEqual(factors.get("tech_score"), 42.0)
        self.assertEqual(factors.get("tech_signal"), "买入")

    def test_technical_score_falls_back_when_data_short(self):
        """修复后：收盘价 < 30 天时，返回 0 + 原因（不再静默报错）。"""
        from stock_researcher.analysis.asset_forecaster import AssetForecaster
        af = AssetForecaster()
        with patch("stock_researcher.data.market.MarketData") as MockMarket:
            MockMarket.return_value.fetch_history.return_value = {"closes": [100] * 10}
            score, factors = af._get_technical_score("600519", "cn")
        self.assertEqual(score, 0.0)
        self.assertIn("数据不足", factors.get("reason", ""))

    def test_stock_narrative_no_longer_shows_zero_tech(self):
        """修复后 narrative 显示真实技术分 + 信号，不再永远是 0。"""
        af = self.AssetForecaster()
        fd = {"total_score": 35, "missing_sources": []}
        tech_factors = {"tech_score": 42.0, "tech_signal": "买入"}
        narrative = af._build_stock_narrative("600519", fd, tech_factors)
        self.assertIn("42", narrative, "narrative 应包含技术分 42")
        self.assertIn("买入", narrative, "narrative 应包含技术信号 买入")

    def test_stock_narrative_handles_missing_tech_fields(self):
        """_build_stock_narrative 容错：缺字段时不崩。"""
        af = self.AssetForecaster()
        fd = {"total_score": 0, "missing_sources": ["policy"]}
        narrative = af._build_stock_narrative("600519", fd, {})
        self.assertIn("0", narrative)
        self.assertIn("缺失维度：policy", narrative)


# ============================================================
# 测试 5：版本号
# ============================================================
class TestV72Version(unittest.TestCase):
    def test_version_is_current(self):
        # 直接读 __init__.py 内容，找到 __version__ 行
        init_path = ROOT / "scripts" / "stock_researcher" / "__init__.py"
        content = init_path.read_text(encoding="utf-8")
        # 找到 version 字符串
        import re
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        self.assertIsNotNone(m, "必须存在 __version__ 定义")
        self.assertEqual(m.group(1), "9.3.0")

    def test_init_header_mentions_v72(self):
        init_path = ROOT / "scripts" / "stock_researcher" / "__init__.py"
        content = init_path.read_text(encoding="utf-8")
        self.assertIn("v7.4", content.lower() or content, "开头注释应提到 v7.4")
        self.assertIn("数据质量", content, "应提到 v7.2 数据质量")


# ============================================================
# 测试 6：data_quality 模块
# ============================================================
class TestV72DataQuality(unittest.TestCase):
    """数据质量四级标记模块"""

    def setUp(self):
        # 直接 import data_quality，绕开 stock_researcher 主包
        from stock_researcher.data import data_quality as dq
        self.dq = dq

    def test_dataclass_constants(self):
        self.assertEqual(self.dq.DataQuality.ACTUAL, "actual")
        self.assertEqual(self.dq.DataQuality.DERIVED, "derived")
        self.assertEqual(self.dq.DataQuality.ESTIMATED, "estimated")
        self.assertEqual(self.dq.DataQuality.UNAVAILABLE, "unavailable")

    def test_mark_field_structure(self):
        r = self.dq.mark_field(15.2, "actual", "腾讯财经", "实时")
        self.assertEqual(r["value"], 15.2)
        self.assertEqual(r["quality"], "actual")
        self.assertEqual(r["source"], "腾讯财经")
        self.assertEqual(r["note"], "实时")

    def test_is_estimated_unavailable(self):
        e = self.dq.mark_field(50, "estimated", "经验映射")
        u = self.dq.mark_field(0, "unavailable", "", "API 不返回")
        self.assertTrue(self.dq.is_estimated(e))
        self.assertFalse(self.dq.is_estimated(u))
        self.assertTrue(self.dq.is_unavailable(u))
        self.assertFalse(self.dq.is_unavailable(e))

    def test_unwrap_returns_value(self):
        r = self.dq.mark_field(7.5, "actual")
        self.assertEqual(self.dq.unwrap(r), 7.5)
        self.assertEqual(self.dq.unwrap(42), 42)
        self.assertEqual(self.dq.unwrap(None, default=0), 0)

    def test_build_quality_report(self):
        fields = {
            "pe": self.dq.mark_field(15, "actual"),
            "pb": self.dq.mark_field(3.2, "actual"),
            "cost": self.dq.mark_field(100, "derived"),
            "pctl": self.dq.mark_field(35, "estimated"),
            "exp": self.dq.mark_field(0, "unavailable"),
        }
        report = self.dq.build_quality_report(fields)
        self.assertEqual(report["actual_count"], 2)
        self.assertEqual(report["derived_count"], 1)
        self.assertEqual(report["estimated_count"], 1)
        self.assertEqual(report["unavailable_count"], 1)
        self.assertEqual(report["estimated_fields"], ["pctl"])
        self.assertEqual(report["unavailable_fields"], ["exp"])
        self.assertIn(report["overall_quality"], ("🟢 高", "🟡 中", "🔴 低"))

    def test_financial_statements_marks_derived_fields(self):
        """数据层验证：financial_statements.fetch_income_statement 应在派生字段打 _derived 标记。"""
        # 由于 fetch_income_statement 需要联网，我们直接检查代码中存在该标记逻辑
        from pathlib import Path
        f = (ROOT / "scripts" / "stock_researcher" / "data" / "financial_statements.py").read_text(
            encoding="utf-8")
        self.assertIn("_data_quality", f)
        self.assertIn("OPERATE_COST_derived", f)
        self.assertIn("OPERATE_PROFIT_derived", f)


# ============================================================
# 测试 3+4：analyzer.analyze_stock / generate_report
# （读取源码验证修复 + 子进程独立验证 generate_report 转发）
# ============================================================
class TestV72AnalyzerBugfix(unittest.TestCase):
    """v7.2 BUG 修复：源码静态检查 + 独立子进程跑 generate_report 验证参数转发"""

    def test_analyze_stock_no_datetime_strptime_bug(self):
        """修复前源码存在 `datetime.now().strptime(period, ...)` 错调用。
        修复后源码不应再出现这种反向解析。"""
        src = (ROOT / "scripts" / "stock_researcher" / "core" / "analyzer.py").read_text(
            encoding="utf-8")
        self.assertNotIn("datetime.now().strptime(period", src,
                          "修复：不能再用 datetime.now().strptime 反向解析 period")

    def test_analyzer_imports_timedelta(self):
        """修复后源码必须 import timedelta。"""
        src = (ROOT / "scripts" / "stock_researcher" / "core" / "analyzer.py").read_text(
            encoding="utf-8")
        self.assertIn("timedelta", src, "analyzer.py 需要 timedelta")

    def test_generate_report_signature_has_start_end_strict(self):
        """修复后 generate_report 签名必须包含 start_date/end_date/strict。"""
        import ast
        src = (ROOT / "scripts" / "stock_researcher" / "core" / "analyzer.py").read_text(
            encoding="utf-8")
        tree = ast.parse(src)
        # 找到 StockResearcher 类下的 generate_report 函数
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "StockResearcher":
                for fn in node.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name == "generate_report":
                        args = [a.arg for a in fn.args.args]
                        self.assertIn("start_date", args,
                                      "generate_report 签名缺 start_date")
                        self.assertIn("end_date", args,
                                      "generate_report 签名缺 end_date")
                        self.assertIn("strict", args,
                                      "generate_report 签名缺 strict")
                        return
                self.fail("未找到 generate_report 方法")

    def test_generate_report_calls_analyze_stock_with_all_args(self):
        """修复后 generate_report 内必须显式给 analyze_stock 传 start_date/end_date/strict。
        用 AST 检查内部调用，避免被 v71 测试 stub 污染。"""
        import ast
        src = (ROOT / "scripts" / "stock_researcher" / "core" / "analyzer.py").read_text(
            encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "StockResearcher":
                for fn in node.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name == "generate_report":
                        for sub in ast.walk(fn):
                            if (isinstance(sub, ast.Call) and
                                isinstance(sub.func, ast.Attribute) and
                                sub.func.attr == "analyze_stock"):
                                # 检查 keyword arguments
                                kwargs = {kw.arg for kw in sub.keywords if kw.arg}
                                self.assertIn("start_date", kwargs,
                                              "修复：analyze_stock 调用必须传 start_date")
                                self.assertIn("end_date", kwargs,
                                              "修复：analyze_stock 调用必须传 end_date")
                                self.assertIn("strict", kwargs,
                                              "修复：analyze_stock 调用必须传 strict")
                                return
                self.fail("未找到 analyze_stock 调用")
        self.fail("未找到 StockResearcher.generate_report")


if __name__ == "__main__":
    unittest.main(verbosity=2)
