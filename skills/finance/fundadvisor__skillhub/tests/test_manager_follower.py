# -*- coding: utf-8 -*-
"""v10.0 测试：基金经理跟仓引擎（manager_follower）"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))


def _write_holdings(tmp_path, quarter, manager="张坤"):
    """合成持仓库（v7.2+ 紧凑格式）"""
    (tmp_path / "holdings_database.json").write_text(json.dumps({
        "h": [{
            "fc": "110011", "fn": "易方达中小盘混合", "mg": manager, "co": "易方达",
            "ss": [["600519", "贵州茅台", 9.8], ["000858", "五粮液", 8.5],
                   ["000333", "美的集团", 7.0], ["300750", "宁德时代", 5.0]],
        }],
        "m": {"count": 1, "quarter": quarter, "asof": "2026-06-30"},
    }, ensure_ascii=False), encoding="utf-8")


def _archive(tmp_path, quarter):
    from data_collection.holdings_history import archive_current_holdings
    return archive_current_holdings(tmp_path)


# ── diff ────────────────────────────────────────────────────────

def test_diff_holdings_categories():
    from manager_follower import ManagerFollower
    prev = [
        {"stock_code": "600519", "stock_name": "贵州茅台", "weight": 9.8},
        {"stock_code": "000858", "stock_name": "五粮液", "weight": 8.5},
        {"stock_code": "000333", "stock_name": "美的集团", "weight": 7.0},
    ]
    curr = [
        {"stock_code": "600519", "stock_name": "贵州茅台", "weight": 10.5},  # 加仓
        {"stock_code": "000858", "stock_name": "五粮液", "weight": 6.0},    # 减仓
        {"stock_code": "000333", "stock_name": "美的集团", "weight": 7.0},  # 维持
        {"stock_code": "300750", "stock_name": "宁德时代", "weight": 5.0},  # 新增
    ]
    d = ManagerFollower.diff_holdings(prev, curr)
    assert d["summary"]["added_count"] == 1
    assert d["summary"]["removed_count"] == 0
    assert d["summary"]["increased_count"] == 1
    assert d["summary"]["decreased_count"] == 1
    assert d["summary"]["kept_count"] == 1
    assert d["added"][0]["stock_code"] == "300750"
    assert d["increased"][0]["stock_code"] == "600519"
    assert d["increased"][0]["change"] == 0.7
    assert d["decreased"][0]["stock_code"] == "000858"


def test_diff_removed():
    from manager_follower import ManagerFollower
    prev = [{"stock_code": "600519", "stock_name": "贵州茅台", "weight": 9.8}]
    curr = [{"stock_code": "000858", "stock_name": "五粮液", "weight": 8.5}]
    d = ManagerFollower.diff_holdings(prev, curr)
    assert d["summary"]["added_count"] == 1
    assert d["summary"]["removed_count"] == 1
    assert d["removed"][0]["stock_code"] == "600519"


# ── 季度对比（走历史快照） ─────────────────────────────────────

def test_diff_fund_holdings_two_quarters(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q1")
    _archive(tmp_path, "2026Q1")
    _write_holdings(tmp_path, quarter="2026Q2")
    _archive(tmp_path, "2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    d = f.diff_fund_holdings("110011")
    assert d.get("error") is None
    assert d["quarters"] == ["2026Q1", "2026Q2"]
    assert d["summary"]["added_count"] >= 0
    assert d["summary"]["kept_count"] >= 1


def test_diff_fund_holdings_no_history(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    _archive(tmp_path, "2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    d = f.diff_fund_holdings("110011")
    assert d.get("error") == "no_history"
    assert "基线" in d.get("message", "")


# ── 镜像组合 ───────────────────────────────────────────────────

def test_mirror_portfolio_weighted(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    pf = f.build_mirror_portfolio("110011", mode="weighted", total_amount=100000)
    assert pf.get("error") is None
    assert len(pf["positions"]) == 4
    assert pf["concentration"]["top1"] == 9.8
    assert pf["cash_ratio"] > 0  # 十大重仓未覆盖部分
    # 金额分解
    first = pf["positions"][0]
    assert abs(first["amount_breakdown"] - 100000 * 9.8 / 100) < 1
    assert "风险提示" in pf["disclaimer"]


def test_mirror_portfolio_equal_mode(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    pf = f.build_mirror_portfolio("110011", mode="equal")
    assert pf["mode"] == "equal"
    assert abs(sum(p["mirror_weight"] for p in pf["positions"]) - 100.0) < 0.5


def test_mirror_portfolio_no_holdings(tmp_path):
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    pf = f.build_mirror_portfolio("110011")
    assert pf.get("error") == "no_holdings"


def test_track_mirror_degraded_without_nav(tmp_path):
    """无净值序列时应降级而非崩溃"""
    _write_holdings(tmp_path, quarter="2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    r = f.track_mirror_performance("110011", days=30)
    assert r["fund_code"] == "110011"
    assert r["fund_nav_return_pct"] is None or isinstance(r["fund_nav_return_pct"], float)
    assert "note" in r


# ── 跟仓信号 ───────────────────────────────────────────────────

def test_follow_signals_baseline(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2")
    _archive(tmp_path, "2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    r = f.get_follow_signals()
    assert r["signals"], "有持仓应有至少一条基线信号"
    assert r["signals"][0]["signal"] == "baseline"
    assert r["signals"][0]["level"] == "info"


def test_follow_signals_change_and_confidence(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q1")
    _archive(tmp_path, "2026Q1")
    # Q2 大幅换仓（新增3只 → 高换手）
    (tmp_path / "holdings_database.json").write_text(json.dumps({
        "h": [{
            "fc": "110011", "fn": "易方达中小盘混合", "mg": "张坤", "co": "易方达",
            "ss": [["600519", "贵州茅台", 10.0], ["601318", "中国平安", 8.0],
                   ["000001", "平安银行", 7.0], ["600036", "招商银行", 6.0]],
        }],
        "m": {"count": 1, "quarter": "2026Q2", "asof": "2026-06-30"},
    }, ensure_ascii=False), encoding="utf-8")
    _archive(tmp_path, "2026Q2")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    r = f.get_follow_signals()
    sig = r["signals"][0]
    assert sig["signal"] == "holdings_change"
    assert sig["summary"]["added_count"] >= 2
    assert sig["level"] in ("high", "medium")
    assert sig["confidence"] in ("high", "medium")


def test_follow_signals_manager_change_alert(tmp_path):
    _write_holdings(tmp_path, quarter="2026Q2", manager="张坤")
    _archive(tmp_path, "2026Q2")
    # 监控产物：经理变更
    (tmp_path / "manager_changes.json").write_text(json.dumps({
        "changes": [{
            "fund_code": "110011", "fund_name": "易方达中小盘混合",
            "old_manager": "张坤", "new_manager": "李四",
            "source": "本地档案对比", "date": "2026-08-01",
            "detail": "基金经理由 张坤 变更为 李四",
        }]
    }, ensure_ascii=False), encoding="utf-8")
    from manager_follower import ManagerFollower
    f = ManagerFollower(data_dir=tmp_path)
    r = f.get_follow_signals()
    sig = r["signals"][0]
    assert sig.get("manager_change") is not None
    assert sig["level"] == "high"
    assert "经理变动" in sig["message"]
