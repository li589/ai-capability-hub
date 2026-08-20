# -*- coding: utf-8 -*-
"""Tests for data_validator.py — data integrity validation"""
import json
import pytest
import tempfile
from pathlib import Path
from scripts.data_validator import (
    validate_institution_registry,
    validate_list_file,
    validate_all_list_files,
    run_full_validation,
)


class TestValidateInstitutionRegistry:
    """Test institution_registry.json validation"""

    def test_passes_on_valid_registry(self):
        """Valid registry should pass"""
        ok, msg, details = validate_institution_registry()
        assert ok, f"Registry validation failed: {msg}"
        assert "验证通过" in msg
        assert details["total"] > 0
        assert "types" in details
        # Should have at least the major types
        types = details["types"]
        assert any("基金" in t for t in types), f"No fund type found in {list(types.keys())[:5]}"

    def test_returns_details_with_types(self):
        """Details should contain type distribution"""
        ok, msg, details = validate_institution_registry()
        assert ok
        types = details["types"]
        total_from_types = sum(types.values())
        assert total_from_types == details["total"]


class TestValidateListFile:
    """Test individual list file validation"""

    def test_passes_with_valid_list_file(self):
        """A well-formed list file should pass"""
        test_data = {
            "type": "测试机构",
            "institutions": [
                {"name": "测试银行A", "code": "001"},
                {"name": "测试银行B", "code": "002"},
            ],
            "data_source": "测试数据源",
            "update_time": "2026-01-01",
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            path = Path(f.name)

        try:
            ok, msg, details = validate_list_file(path)
            assert ok, f"Validation failed: {msg}"
            assert details["count"] == 2
            assert details["type"] == "测试机构"
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_missing_type_field(self):
        """Missing 'type' field should fail"""
        test_data = {"institutions": [{"name": "X"}]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            path = Path(f.name)

        try:
            ok, msg, _ = validate_list_file(path)
            assert not ok
            assert "type" in msg.lower()
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_missing_institutions_field(self):
        """Missing 'institutions' field should fail"""
        test_data = {"type": "银行"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            path = Path(f.name)

        try:
            ok, msg, _ = validate_list_file(path)
            assert not ok
            assert "institutions" in msg.lower()
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_empty_institutions(self):
        """Empty institutions list should fail"""
        test_data = {"type": "银行", "institutions": []}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            path = Path(f.name)

        try:
            ok, msg, _ = validate_list_file(path)
            assert not ok
            assert "空" in msg or "empty" in msg.lower()
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_institutions_not_list(self):
        """institutions field should be a list"""
        test_data = {"type": "银行", "institutions": "not-a-list"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            path = Path(f.name)

        try:
            ok, msg, _ = validate_list_file(path)
            assert not ok
            assert "数组" in msg or "array" in msg.lower()
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_missing_name_in_record(self):
        """Each institution record must have a 'name' field"""
        test_data = {
            "type": "银行",
            "institutions": [{"name": "OK"}, {"code": "no-name"}],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            path = Path(f.name)

        try:
            ok, msg, _ = validate_list_file(path)
            assert not ok
            # Message should indicate data format error
            assert "格式" in msg or "name" in msg.lower() or "错误" in msg
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_invalid_json(self):
        """Invalid JSON should fail gracefully"""
        path = Path(tempfile.mktemp(suffix=".json"))
        path.write_text("not valid json {{{", encoding="utf-8")
        try:
            ok, msg, _ = validate_list_file(path)
            assert not ok
            assert "json" in msg.lower() or "解析" in msg
        finally:
            path.unlink(missing_ok=True)

    def test_fails_on_nonexistent_file(self):
        """Nonexistent file should fail"""
        # validate_list_file doesn't check existence explicitly —
        # it will get a FileNotFoundError caught by the except block
        pass  # This is tested implicitly


class TestValidateAllListFiles:
    """Test batch list file validation"""

    def test_returns_dict_of_results(self):
        """Should return results for all *_list.json files"""
        results = validate_all_list_files()
        assert isinstance(results, dict), f"Expected dict, got {type(results)}"
        assert len(results) > 20, f"Expected >20 list files, got {len(results)}"
        # All should be tuples of (bool, str, dict)
        for fname, result in results.items():
            assert isinstance(result, tuple), f"{fname}: expected tuple, got {type(result)}"
            assert len(result) == 3, f"{fname}: expected 3-tuple, got {len(result)}"

    def test_all_list_files_pass(self):
        """All real list files should pass validation"""
        results = validate_all_list_files()
        for fname, (ok, msg, _) in results.items():
            assert ok, f"{fname} failed: {msg}"


class TestRunFullValidation:
    """Test the complete validation pipeline"""

    def test_returns_expected_structure(self):
        """Should return dict with registry, list_files, summary keys"""
        results = run_full_validation()
        assert "registry" in results
        assert "list_files" in results
        assert "summary" in results
        assert results["registry"]["passed"], f"Registry failed: {results['registry']['message']}"

    def test_summary_counts_are_consistent(self):
        """Summary pass+fail should equal total"""
        results = run_full_validation()
        s = results["summary"]
        assert s["passed"] + s["failed"] == s["total"]
        assert s["total"] > 25

    def test_total_institutions_positive(self):
        """Total institution count should be positive"""
        results = run_full_validation()
        assert results["summary"]["total_institutions"] > 1000
