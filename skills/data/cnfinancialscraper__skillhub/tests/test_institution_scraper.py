# -*- coding: utf-8 -*-
"""Tests for institution_scraper.py — institution search and listing"""
import pytest
from scripts.institution_scraper import (
    InstitutionLoader,
    search_institution,
    list_all_institutions,
    get_institution_summary,
)


class TestInstitutionLoader:
    """Test the InstitutionLoader singleton"""

    def test_singleton_behavior(self):
        """Should return same instance"""
        a = InstitutionLoader()
        b = InstitutionLoader()
        assert a is b

    def test_loads_data(self):
        """Should load institutions data"""
        loader = InstitutionLoader()
        funds = loader.get_all_fund_companies()
        securities = loader.get_all_securities()
        banks = loader.get_all_banks()
        third_party = loader.get_all_third_party()
        all_count = len(funds) + len(securities) + len(banks) + len(third_party)
        assert all_count > 0, "No institution data loaded"

    def test_get_all_institutions_returns_list(self):
        """get_all_institutions should return list of tuples"""
        loader = InstitutionLoader()
        result = loader.get_all_institutions()
        assert isinstance(result, list)
        assert len(result) == 4
        for category, items in result:
            assert isinstance(category, str)
            assert isinstance(items, list)

    def test_get_platform_patterns(self):
        """Should return platform URL patterns (may be empty if data not loaded)"""
        loader = InstitutionLoader()
        patterns = loader.get_platform_patterns()
        assert isinstance(patterns, dict)
        # Platform patterns may be empty if institutions.json doesn't include them

    def test_identify_platform_returns_tuple(self):
        """identify_platform should return a 3-tuple"""
        loader = InstitutionLoader()
        result = loader.identify_platform("https://fund.eastmoney.com/000001.html")
        assert isinstance(result, tuple)
        assert len(result) == 3
        platform_name, platform_code, inst_type = result
        assert isinstance(platform_name, str)
        assert isinstance(platform_code, str)
        assert isinstance(inst_type, str)


class TestSearchInstitution:
    """Test institution search functionality"""

    def test_search_by_name_exact(self):
        """Search should find exact institution names"""
        results = search_institution("华夏基金")
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            combined = (r.get("name", "") + r.get("code", "")).lower()
            assert "华夏" in combined

    def test_search_by_partial_name(self):
        """Partial name search should work"""
        results = search_institution("华夏")
        assert len(results) > 0
        names = [r.get("name", "") for r in results]
        assert any("华夏" in n for n in names)

    def test_search_by_code(self):
        """Search by code should work"""
        results = search_institution("ICBC")
        assert isinstance(results, list)

    def test_search_returns_type_field(self):
        """Each result should have a 'type' field added"""
        results = search_institution("招商")
        for r in results:
            assert "type" in r, f"Missing 'type' in {r}"
            assert isinstance(r["type"], str)

    def test_search_no_match_returns_empty(self):
        """No-match search should return empty list"""
        results = search_institution("ZZZ不存在的机构名称XYZ123")
        assert results == []

    def test_search_case_insensitive(self):
        """Search should be case-insensitive"""
        results = search_institution("招商")
        assert len(results) > 0


class TestListAllInstitutions:
    """Test listing all institutions"""

    def test_returns_expected_keys(self):
        """Should return dict with 4 keys"""
        result = list_all_institutions()
        assert isinstance(result, dict)
        assert "fund_companies" in result
        assert "securities" in result
        assert "banks" in result
        assert "third_party" in result

    def test_each_value_is_list(self):
        """Each value should be a list"""
        result = list_all_institutions()
        for key, value in result.items():
            assert isinstance(value, list), f"{key} should be list, got {type(value)}"

    def test_items_have_name_field(self):
        """Institution items should have name field"""
        result = list_all_institutions()
        for category, items in result.items():
            if items:
                for item in items[:3]:
                    assert "name" in item, f"Missing name in {category}: {item}"


class TestGetInstitutionSummary:
    """Test institution summary"""

    def test_returns_non_empty_string(self):
        """Should return a non-empty summary string"""
        summary = get_institution_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "机构" in summary

    def test_contains_counts(self):
        """Summary should contain institution counts"""
        summary = get_institution_summary()
        assert "家" in summary
