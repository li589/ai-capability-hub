# -*- coding: utf-8 -*-
"""Tests for scrapable_registry.py — institution registry operations"""
import pytest
from scripts.scrapable_registry import ScrapableRegistry, PREDEFINED_URLS


class TestScrapableRegistry:
    """Test ScrapableRegistry class"""

    def test_initialization_loads_data(self):
        """Registry should load on initialization"""
        registry = ScrapableRegistry()
        assert registry.total > 0, "Registry should have institutions"

    def test_institutions_property(self):
        """institutions property should return a list"""
        registry = ScrapableRegistry()
        institutions = registry.institutions
        assert isinstance(institutions, list)
        assert len(institutions) > 0

    def test_get_returns_institution(self):
        """get() should return institution info for known names"""
        registry = ScrapableRegistry()
        # Get any institution
        all_inst = registry.institutions
        if all_inst:
            first = all_inst[0]
            result = registry.get(first["name"])
            assert result is not None
            assert result["name"] == first["name"]

    def test_get_returns_none_for_unknown(self):
        """get() should return None for unknown names"""
        registry = ScrapableRegistry()
        result = registry.get("ZZZ不存在的机构名称XYZ")
        assert result is None

    def test_search_finds_institutions(self):
        """Search should find matching institutions"""
        registry = ScrapableRegistry()
        results = registry.search("工商银行")
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert r is not None

    def test_search_no_match(self):
        """Search with no match should return empty"""
        registry = ScrapableRegistry()
        results = registry.search("ZZZ不存在的机构123456")
        assert results == []

    def test_list_by_type(self):
        """list_by_type should filter institutions"""
        registry = ScrapableRegistry()
        # Find an actual type from the data
        all_inst = registry.institutions
        if all_inst:
            first_type = all_inst[0].get("type", "")
            results = registry.list_by_type(first_type)
            assert isinstance(results, list)

    def test_list_scrapable(self):
        """list_scrapable should return institutions with URLs"""
        registry = ScrapableRegistry()
        results = registry.list_scrapable()
        assert isinstance(results, list)
        # All should have scrapable=True
        for r in results:
            assert r["scrapable"] is True

    def test_total_property(self):
        """Total should be positive"""
        registry = ScrapableRegistry()
        assert registry.total > 0

    def test_get_statistics(self):
        """get_statistics should return stats dict"""
        registry = ScrapableRegistry()
        stats = registry.get_statistics()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "scrapable" in stats
        assert "by_type" in stats
        assert stats["total"] > 0

    def test_generate_report(self):
        """generate_report should return a string"""
        registry = ScrapableRegistry()
        report = registry.generate_report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "机构" in report

    def test_is_scrapable(self):
        """is_scrapable should correctly identify institutions with URLs"""
        registry = ScrapableRegistry()
        assert registry.is_scrapable("华夏基金") is True
        assert registry.is_scrapable("ZZZ不存在") is False


class TestPredefinedUrls:
    """Test the PREDEFINED_URLS dictionary"""

    def test_contains_major_banks(self):
        assert "中国工商银行" in PREDEFINED_URLS
        assert "中国建设银行" in PREDEFINED_URLS
        assert "招商银行" in PREDEFINED_URLS

    def test_contains_major_securities(self):
        assert "中信证券" in PREDEFINED_URLS
        assert "华泰证券" in PREDEFINED_URLS

    def test_contains_major_fund_companies(self):
        assert "华夏基金" in PREDEFINED_URLS
        assert "易方达基金" in PREDEFINED_URLS

    def test_all_urls_are_valid_format(self):
        for name, url in PREDEFINED_URLS.items():
            assert url.startswith("https://"), f"{name}: {url} must use HTTPS"
            assert len(url) > 10, f"{name}: URL too short"

    def test_no_duplicate_urls(self):
        """No two institutions should share the same URL"""
        urls = list(PREDEFINED_URLS.values())
        assert len(urls) == len(set(urls)), f"Found {len(urls) - len(set(urls))} duplicate URL(s)"
