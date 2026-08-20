# -*- coding: utf-8 -*-
"""v10.0 测试：定制报告（report_generator 模块化 + report_scheduler）"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "client_manager"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))


@pytest.fixture
def gen(tmp_path, monkeypatch):
    """隔离网络：新闻/宏观模块用桩替代"""
    from report_generator import ReportGenerator
    # 新闻模块不可用（避免联网）
    monkeypatch.setattr(ReportGenerator, "news_advisor",
                        property(lambda self: None))
    # 宏观分析返回 mock 数据源（避免 akshare 联网）
    import macro_analyzer
    monkeypatch.setattr(
        macro_analyzer.MacroAnalyzer, "analyze_macro_conditions",
        lambda self: {"score": 50, "status": "经济承压", "description": "d",
                      "key_indicators": {"gdp": {"data_source": "mock"}}})
    return ReportGenerator(data_dir=tmp_path)


def _setup_persona_data(tmp_path):
    """经理+观点+新闻（供 manager_views 模块渲染）"""
    (tmp_path / "fund_managers_distilled.json").write_text(json.dumps({"items": [{
        "manager_id": "M001", "name": "张坤", "company_name": "易方达",
        "current_fund_code": "110011", "current_fund_name": "易方达中小盘混合",
        "tenure_days": 3650, "total_scale": "700亿", "best_return": "280.5",
        "investment_style": "成长型", "sector_description": "重点布局消费行业",
        "stock_pool": ["贵州茅台"], "risk_warning": "成长风格波动较大。",
    }]}), encoding="utf-8")
    (tmp_path / "manager_views.json").write_text(json.dumps({"views": [{
        "manager_id": "M001", "manager_name": "张坤", "fund_code": "110011",
        "report_date": "2026-07-18", "report_title": "2026年二季报",
        "views": "重点配置消费行业优质公司。", "outlook": "对权益市场保持乐观。",
        "quarter": "2026Q2",
    }]}), encoding="utf-8")
    (tmp_path / "holdings_database.json").write_text(json.dumps({
        "h": [{"fc": "110011", "fn": "易方达中小盘混合", "mg": "张坤", "co": "易方达",
               "ss": [["600519", "贵州茅台", 9.8]]}],
        "m": {"quarter": "2026Q2"},
    }, ensure_ascii=False), encoding="utf-8")


def test_default_modules_backward_compat(gen):
    """旧签名行为不变：周报默认含 要闻/持仓/展望/风险"""
    report = gen.generate_report(user_id="u1", report_type="weekly")
    assert "财经要闻" in report
    assert "市场展望" in report
    assert "风险提示" in report
    assert "基金投资周报" in report


def test_include_news_false_compat(gen):
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 include_news=False)
    assert "财经要闻" not in report


def test_modules_selection(gen):
    """自定义模块组合：只选 news+risk"""
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 modules=["news", "risk"])
    assert "财经要闻" in report
    assert "风险提示" in report
    assert "市场展望" not in report
    assert "持仓业绩" not in report


def test_template_concise_no_footer(gen):
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 template="concise")
    assert "如需调整报告内容或频率" not in report  # concise 无尾部


def test_template_professional(gen):
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 template="professional")
    assert "模板: professional" in report


def test_manager_views_module(gen, tmp_path):
    _setup_persona_data(tmp_path)
    holdings = [{"fund_code": "110011", "fund_name": "易方达中小盘混合"}]
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 holdings=holdings,
                                 modules=["manager_views", "risk"])
    assert "基金经理观点" in report
    assert "张坤" in report
    assert "2026年二季报" in report


def test_psychology_module_without_data(gen):
    """无行为画像数据时模块给出引导而非崩溃"""
    report = gen.generate_report(user_id="客户X", report_type="weekly",
                                 modules=["psychology", "risk"])
    assert "客户心理状态" in report


def test_follow_module_with_holdings(gen, tmp_path):
    _setup_persona_data(tmp_path)
    holdings = [{"fund_code": "110011"}]
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 holdings=holdings,
                                 modules=["follow", "risk"])
    assert "跟仓信号" in report


def test_unknown_modules_filtered(gen):
    report = gen.generate_report(user_id="u1", report_type="weekly",
                                 modules=["news", "不存在的模块"])
    assert "财经要闻" in report  # 未知模块被过滤，不崩


def test_save_report_records_modules(gen, tmp_path):
    path = gen.save_report("u2", "weekly", modules=["news", "risk"],
                           template="concise")
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["modules"] == ["news", "risk"]
    assert data["template"] == "concise"


# ── ReportScheduler ─────────────────────────────────────────────

def test_scheduler_add_list(tmp_path):
    from report_scheduler import ReportScheduler
    sched = ReportScheduler(data_dir=tmp_path)
    sched.add_subscription("张先生", report_type="weekly",
                           modules=["news", "holdings", "manager_views"])
    subs = sched.list_subscriptions()
    assert len(subs) == 1
    assert subs[0]["client_id"] == "张先生"
    assert subs[0]["modules"] == ["news", "holdings", "manager_views"]
    # 更新同一客户
    sched.add_subscription("张先生", report_type="monthly")
    assert len(sched.list_subscriptions()) == 1
    assert sched.list_subscriptions()[0]["report_type"] == "monthly"


def test_scheduler_remove(tmp_path):
    from report_scheduler import ReportScheduler
    sched = ReportScheduler(data_dir=tmp_path)
    sched.add_subscription("A")
    sched.add_subscription("B")
    assert sched.remove_subscription("A") is True
    assert [s["client_id"] for s in sched.list_subscriptions()] == ["B"]
    assert sched.remove_subscription("不存在") is False


def test_scheduler_generate_one(tmp_path):
    from report_scheduler import ReportScheduler
    sched = ReportScheduler(data_dir=tmp_path)
    sched.add_subscription("张先生", report_type="weekly",
                           modules=["news", "risk"])
    r = sched.generate_one("张先生")
    assert r["ok"] is True
    assert r["path"].endswith(".json")
    saved = json.loads(Path(r["path"]).read_text(encoding="utf-8"))
    assert saved["user_id"] == "张先生"


def test_scheduler_generate_all(tmp_path):
    from report_scheduler import ReportScheduler
    sched = ReportScheduler(data_dir=tmp_path)
    sched.add_subscription("A", report_type="weekly")
    sched.add_subscription("B", report_type="weekly")
    summary = sched.generate_all()
    assert summary["total"] == 2
    assert summary["success"] == 2
    assert summary["failed"] == 0
