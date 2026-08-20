"""test_holdings_importer.py — 持仓导入核心 API 测试"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from client_manager.holdings_importer import HoldingsImporter


@pytest.fixture
def importer():
    return HoldingsImporter()


def test_list_clients_empty(importer):
    """空仓库返回空 dict"""
    result = importer.list_clients()
    assert isinstance(result, dict)


def test_load_nonexistent_client(importer):
    """不存在的客户返回空 list"""
    holdings = importer.load_client_holdings("nonexistent_user_zzz_test_12345")
    assert holdings == []


def test_import_nonexistent_file(importer):
    """文件不存在时返回错误，不抛异常"""
    result = importer.import_from_screenshot("Z:/this/does/not/exist.png")
    assert result["success"] is False
    assert "errors" in result
    assert len(result["errors"]) > 0


def test_import_docx_nonexistent(importer):
    result = importer.import_from_docx("Z:/this/does/not/exist.docx")
    assert result["success"] is False
    assert len(result["errors"]) > 0


def test_import_pdf_nonexistent(importer):
    result = importer.import_from_pdf("Z:/this/does/not/exist.pdf")
    assert result["success"] is False
    assert len(result["errors"]) > 0


def test_map_columns_chinese(importer):
    """_map_table_columns 返回 {列索引: 字段名}，能识别中英文表头"""
    col_map = importer._map_table_columns(["基金代码", "基金名称", "持有份额", "成本净值"])
    # 返回 {0: 'fund_code', 1: 'fund_name', 2: 'shares', 3: 'cost'}
    assert 0 in col_map
    assert col_map[0] == "fund_code"
    assert col_map[1] == "fund_name"
    assert col_map[2] == "shares"
    assert col_map[3] == "cost"


def test_map_columns_english(importer):
    """英文表头也能识别"""
    col_map = importer._map_table_columns(["code", "name", "shares", "cost"])
    assert col_map[0] == "fund_code"
    assert col_map[1] == "fund_name"
    assert col_map[2] == "shares"
    assert col_map[3] == "cost"


def test_map_columns_empty(importer):
    """空表头返回空 dict"""
    col_map = importer._map_table_columns([])
    assert col_map == {}


def test_validate_holdings_normal(importer):
    """合法持仓通过校验；返回 (normalized, errors) 元组"""
    holdings, errors = importer.validate_holdings([
        {"fund_code": "001924", "shares": 1000, "cost": 1.5},
        {"fund_code": "000858", "shares": 500, "cost": 2.3},
    ])
    assert len(holdings) == 2
    assert errors == []


def test_validate_holdings_bad_code(importer):
    """非法基金代码应被剔除"""
    holdings, errors = importer.validate_holdings([
        {"fund_code": "abc", "shares": 1000, "cost": 1.5},
    ])
    assert holdings == []  # 非法记录被过滤
    assert len(errors) > 0
    assert any("代码" in e or "code" in e.lower() for e in errors)
