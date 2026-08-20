# -*- coding: utf-8 -*-
"""v10.0 测试：持仓历史归档（holdings_history）"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "data_collection"))


def _write_holdings(tmp_path, quarter="2026Q2", manager="张坤"):
    (tmp_path / "holdings_database.json").write_text(json.dumps({
        "h": [{
            "fc": "110011", "fn": "易方达中小盘混合", "mg": manager, "co": "易方达",
            "ss": [["600519", "贵州茅台", 9.8], ["000858", "五粮液", 8.5]],
        }],
        "m": {"count": 1, "quarter": quarter, "asof": "2026-06-30"},
    }, ensure_ascii=False), encoding="utf-8")


def test_archive_creates_quarter_file(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    from holdings_history import archive_current_holdings
    path = archive_current_holdings(tmp_path)
    assert path is not None
    qfile = tmp_path / "holdings_history" / "2026Q2.json"
    assert qfile.exists()
    data = json.loads(qfile.read_text(encoding="utf-8"))
    assert data["m"]["quarter"] == "2026Q2"


def test_archive_skips_existing(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    from holdings_history import archive_current_holdings
    first = archive_current_holdings(tmp_path)
    second = archive_current_holdings(tmp_path)
    assert first is not None
    assert second is None, "同季度不应重复归档（不覆写历史）"


def test_archive_missing_data_returns_none(tmp_path):
    from holdings_history import archive_current_holdings
    assert archive_current_holdings(tmp_path) is None


def test_list_quarters_sorted(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q1")
    from holdings_history import archive_current_holdings, list_history_quarters
    archive_current_holdings(tmp_path)
    _write_holdings(tmp_path, quarter="2026Q2")
    archive_current_holdings(tmp_path)
    assert list_history_quarters(tmp_path) == ["2026Q1", "2026Q2"]


def test_load_quarter_rows_normalized(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    from holdings_history import archive_current_holdings, load_quarter_rows
    archive_current_holdings(tmp_path)
    rows = load_quarter_rows("2026Q2", tmp_path)
    assert len(rows) == 2
    assert rows[0]["fund_code"] == "110011"
    assert rows[0]["stock_name"] == "贵州茅台"
    assert rows[0]["weight"] == 9.8


def test_latest_two_quarters(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q1")
    from holdings_history import archive_current_holdings, latest_two_quarters
    archive_current_holdings(tmp_path)
    _write_holdings(tmp_path, quarter="2026Q2")
    archive_current_holdings(tmp_path)
    latest, prev = latest_two_quarters(tmp_path)
    assert (latest, prev) == ("2026Q2", "2026Q1")


def test_paths_load_holdings_history(tmp_path):
    """fund_advisor_paths 的 loader 也应工作（带 quarter 字段）"""
    _write_holdings(tmp_path, quarter="2026Q2")
    from holdings_history import archive_current_holdings
    archive_current_holdings(tmp_path)
    from fund_advisor_paths import load_holdings_history
    rows = load_holdings_history(data_dir=tmp_path)
    assert rows and all(r.get("quarter") == "2026Q2" for r in rows)
    q1 = load_holdings_history(quarter="2026Q2", data_dir=tmp_path)
    assert len(q1) == 2
