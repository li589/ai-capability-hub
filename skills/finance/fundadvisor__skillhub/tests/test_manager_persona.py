# -*- coding: utf-8 -*-
"""v10.0 测试：基金经理人设卡（manager_persona）"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))


def _write(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _setup_data(tmp_path):
    """合成经理/观点/新闻/产品档案数据"""
    _write(tmp_path, "fund_managers_distilled.json", {"items": [{
        "manager_id": "M001", "name": "张坤", "company_name": "易方达",
        "current_fund_code": "110011", "current_fund_name": "易方达中小盘混合",
        "tenure_days": 3650, "total_scale": "700亿", "best_return": "280.5",
        "investment_style": "成长型", "sector_description": "重点布局消费、医药行业",
        "stock_pool": ["贵州茅台", "五粮液", "泸州老窖", "爱尔眼科"],
        "fund_stage": "老牌期", "stage_description": "历经多轮市场周期，风格稳定",
        "risk_warning": "成长风格波动较大，请注意控制仓位。",
        "education": "清华硕士", "work_years": "12",
    }]})
    # 观点：新版 schema（fund_code/views）
    _write(tmp_path, "manager_views.json", {"views": [{
        "manager_id": "M001", "manager_name": "张坤", "fund_code": "110011",
        "report_date": "2026-07-18", "report_title": "2026年二季报",
        "views": "报告期内基金保持较高仓位运作，重点配置消费行业优质公司。",
        "outlook": "我们对权益市场保持乐观，关注消费升级与品牌企业的长期价值。",
        "quarter": "2026Q2",
    }]})
    # 新闻
    _write(tmp_path, "manager_news.json", {"news": [{
        "manager_id": "M001", "manager_name": "张坤", "title": "张坤最新调仓路径曝光",
        "date": "2026-08-01", "source": "东方财富-经理档案页", "url": "https://x",
        "type": "新闻",
    }]})
    # 产品档案（v10 扩宽列）
    _write(tmp_path, "fund_products.json", {"items": [{
        "code": "110011", "name": "易方达中小盘混合", "type": "混合型",
        "investment_goal": "通过投资具有持续成长潜力的中小企业实现长期资本增值",
        "investment_scope": "股票资产占基金资产的60%-95%，其中投资于中小盘股票的比例不低于股票资产的80%",
        "benchmark": "中证700指数收益率×80%+中债总财富指数收益率×20%",
        "risk_level": "中高风险",
    }]})


def test_persona_build_by_name(tmp_path):
    _setup_data(tmp_path)
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    persona = eng.build(manager_name="张坤")
    assert persona is not None
    assert persona["name"] == "张坤"
    assert persona["company"] == "易方达"
    assert persona["fund"]["code"] == "110011"


def test_persona_build_by_fund_code(tmp_path):
    _setup_data(tmp_path)
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    persona = eng.build(fund_code="110011")
    assert persona is not None
    assert persona["manager_id"] == "M001"


def test_persona_scope_from_product_profile(tmp_path):
    _setup_data(tmp_path)
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    persona = eng.build(manager_name="张坤")
    assert persona["scope"].get("investment_scope")
    assert "60%-95%" in persona["scope"]["investment_scope"]
    assert persona["scope"].get("benchmark", "").startswith("中证700")


def test_persona_views_schema_compat(tmp_path):
    """manager_views.json 新旧 schema（fc/v 与 fund_code/views）都应解析"""
    _setup_data(tmp_path)
    # 追加旧版 schema 记录
    p = tmp_path / "manager_views.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["views"].append({"fc": "110011", "date": "2026-04-20", "v": "旧版观点字段"})
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    persona = eng.build(manager_name="张坤")
    assert len(persona["views"]) >= 2
    assert persona["views"][0]["fund_code"] == "110011"


def test_persona_news_loaded(tmp_path):
    _setup_data(tmp_path)
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    persona = eng.build(manager_name="张坤")
    assert len(persona["news"]) == 1
    assert persona["news"][0]["title"] == "张坤最新调仓路径曝光"


def test_persona_not_found(tmp_path):
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    assert eng.build(manager_name="不存在的人") is None


def test_persona_format_contains_sections(tmp_path):
    _setup_data(tmp_path)
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    persona = eng.build(manager_name="张坤")
    text = eng.format_persona(persona)
    assert "人设卡" in text
    assert "风格" in text
    assert "投资范围" in text
    assert "风险提示" in text


def test_persona_empty_data_dir(tmp_path):
    """空数据目录：persona 构建不崩，返回 None"""
    from manager_persona import ManagerPersona
    eng = ManagerPersona(data_dir=tmp_path)
    assert eng.build(manager_name="张坤") is None
