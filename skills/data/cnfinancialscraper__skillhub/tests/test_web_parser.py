# -*- coding: utf-8 -*-
"""Tests for web_parser.py — product parsing and financial metrics extraction"""
import pytest
from scripts.web_parser import (
    extract_financial_metrics,
    format_product_summary,
    parse_product_from_html,
)


class TestExtractFinancialMetrics:
    """Test extract_financial_metrics function"""

    def test_extracts_return_1m(self):
        text = "近1月收益率：5.23% 近3月收益率：12.5%"
        metrics = extract_financial_metrics(text)
        assert "return_1m" in metrics
        assert metrics["return_1m"] == 5.23

    def test_extracts_return_3m(self):
        text = "近3月收益: -3.14%"
        metrics = extract_financial_metrics(text)
        assert "return_3m" in metrics
        assert metrics["return_3m"] == -3.14

    def test_extracts_return_6m(self):
        text = "近6月收益率: 8.5"
        metrics = extract_financial_metrics(text)
        assert "return_6m" in metrics
        assert metrics["return_6m"] == 8.5

    def test_extracts_return_1y(self):
        text = "近1年收益率: 15.67%"
        metrics = extract_financial_metrics(text)
        assert "return_1y" in metrics
        assert metrics["return_1y"] == 15.67

    def test_extracts_return_3y(self):
        text = "近3年收益率： 45.2%"
        metrics = extract_financial_metrics(text)
        assert "return_3y" in metrics
        assert metrics["return_3y"] == 45.2

    def test_extracts_return_ytd(self):
        text = "今年来收益率: +8.91%"
        metrics = extract_financial_metrics(text)
        assert "return_ytd" in metrics
        assert metrics["return_ytd"] == 8.91

    def test_extracts_negative_values(self):
        text = "近1月收益率: -2.5% 近1年收益：-10.3"
        metrics = extract_financial_metrics(text)
        assert metrics["return_1m"] == -2.5
        assert metrics["return_1y"] == -10.3

    def test_handles_empty_text(self):
        metrics = extract_financial_metrics("")
        assert isinstance(metrics, dict)

    def test_handles_text_without_metrics(self):
        metrics = extract_financial_metrics("这是一段无关文本，没有任何收益率数据")
        assert metrics == {} or all(v is not None for v in metrics.values())

    def test_handles_multiple_colon_formats(self):
        """Test both ： (full-width) and : (half-width) colons"""
        text = "近1月收益率: 3.21% 近3月收益： 7.89%"
        metrics = extract_financial_metrics(text)
        assert metrics.get("return_1m") == 3.21
        assert metrics.get("return_3m") == 7.89

    def test_handles_no_percent_sign(self):
        text = "近1月收益: 5.5"
        metrics = extract_financial_metrics(text)
        assert metrics.get("return_1m") == 5.5


class TestFormatProductSummary:
    """Test format_product_summary function"""

    def test_formats_fund_summary(self):
        info = {
            "product_name": "华夏成长混合",
            "product_code": "000001",
            "product_type": "混合型",
            "nav": "1.2345",
            "fund_manager": "张三",
            "fund_company": "华夏基金",
        }
        summary = format_product_summary(info)
        assert isinstance(summary, str)
        assert "华夏成长混合" in summary
        assert "000001" in summary

    def test_handles_minimal_info(self):
        info = {"product_name": "测试基金"}
        summary = format_product_summary(info)
        assert "测试基金" in summary

    def test_handles_empty_dict(self):
        summary = format_product_summary({})
        assert isinstance(summary, str)


class TestParseProductFromHtml:
    """Test parse_product_from_html function"""

    def test_unsupported_type_returns_error(self):
        result = parse_product_from_html("<html></html>", "unsupported_type")
        assert "error" in result
        assert "不支持" in result["error"]

    def test_fund_type_does_not_crash_on_empty_html(self):
        """parse_product_from_html should handle minimal HTML gracefully"""
        result = parse_product_from_html("<html><body><h1>Test</h1></body></html>", "fund")
        assert isinstance(result, dict)
        # Should not raise; may return empty or error result

    def test_etf_type_does_not_crash(self):
        result = parse_product_from_html("<html></html>", "etf")
        assert isinstance(result, dict)

    def test_stock_type_does_not_crash(self):
        result = parse_product_from_html("<html></html>", "stock")
        assert isinstance(result, dict)

    def test_fof_type_does_not_crash(self):
        result = parse_product_from_html("<html></html>", "fof")
        assert isinstance(result, dict)

    def test_advisor_type_does_not_crash(self):
        result = parse_product_from_html("<html></html>", "advisor")
        assert isinstance(result, dict)
