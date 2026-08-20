# -*- coding: utf-8 -*-
"""v10.0 测试：基金经理对话（manager_dialogue）"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))


def _setup_data(tmp_path):
    (tmp_path / "fund_managers_distilled.json").write_text(json.dumps({"items": [{
        "manager_id": "M001", "name": "张坤", "company_name": "易方达",
        "current_fund_code": "110011", "current_fund_name": "易方达中小盘混合",
        "tenure_days": 3650, "total_scale": "700亿", "best_return": "280.5",
        "investment_style": "成长型", "sector_description": "重点布局消费、医药行业",
        "stock_pool": ["贵州茅台", "五粮液"], "fund_stage": "老牌期",
        "stage_description": "历经多轮市场周期，风格稳定",
        "risk_warning": "成长风格波动较大，请注意控制仓位。",
    }]}), encoding="utf-8")
    (tmp_path / "manager_views.json").write_text(json.dumps({"views": [{
        "manager_id": "M001", "manager_name": "张坤", "fund_code": "110011",
        "report_date": "2026-07-18", "report_title": "2026年二季报",
        "views": "报告期内基金保持较高仓位运作，重点配置消费行业优质公司。",
        "outlook": "我们对权益市场保持乐观，关注消费升级与品牌企业的长期价值。",
        "quarter": "2026Q2",
    }]}), encoding="utf-8")
    (tmp_path / "manager_news.json").write_text(json.dumps({"news": [{
        "manager_id": "M001", "manager_name": "张坤", "title": "张坤访谈：看好消费",
        "date": "2026-08-01", "source": "东方财富", "url": "https://x", "type": "访谈",
    }]}), encoding="utf-8")


def _make_dialogue(tmp_path, llm=None):
    """离线对话框：默认禁用 LLM（避免环境 key 串扰测试断言）"""
    from manager_dialogue import ManagerDialogue
    if llm is not None:
        return ManagerDialogue(data_dir=tmp_path, llm_client=llm)
    return ManagerDialogue(data_dir=tmp_path, use_llm=False)


def test_detect_intent():
    from manager_dialogue import detect_intent
    assert detect_intent("你对后市怎么看") == "views"
    assert detect_intent("你的投资风格是什么") == "style"
    assert detect_intent("你的投资范围是什么") == "scope"
    assert detect_intent("最近有什么新闻") == "news"
    assert detect_intent("自我介绍") == "profile"
    assert detect_intent("业绩怎么样") == "perf"
    assert detect_intent("随便聊聊") == "general"


def test_chat_views_offline(tmp_path):
    _setup_data(tmp_path)
    dlg = _make_dialogue(tmp_path)
    out = dlg.chat(manager_name="张坤", question="你对后市怎么看？")
    assert "张坤" in out or "消费" in out
    assert "免责" in out or "不构成投资建议" in out
    assert "2026年二季报" in out


def test_chat_profile_offline(tmp_path):
    _setup_data(tmp_path)
    dlg = _make_dialogue(tmp_path)
    out = dlg.chat(manager_name="张坤", question="介绍一下你自己")
    assert "易方达" in out
    assert "从业" in out


def test_chat_scope_offline(tmp_path):
    """无产品档案时给出引导提示，不崩溃"""
    (tmp_path / "fund_managers_distilled.json").write_text(json.dumps({"items": [{
        "manager_id": "M001", "name": "张坤", "company_name": "易方达",
        "current_fund_code": "110011", "current_fund_name": "易方达中小盘混合",
        "tenure_days": 3650, "investment_style": "成长型",
    }]}), encoding="utf-8")
    dlg = _make_dialogue(tmp_path)
    out = dlg.chat(manager_name="张坤", question="投资范围是什么？")
    assert "投资范围" in out


def test_chat_unknown_manager(tmp_path):
    dlg = _make_dialogue(tmp_path)
    out = dlg.chat(manager_name="不存在的人", question="你好")
    assert "未找到" in out


class _FakeLLM:
    """假 LLM：记录 prompt，返回固定口吻回答"""

    def __init__(self):
        self.calls = []

    def chat(self, messages, system_prompt=""):
        self.calls.append((system_prompt, messages))
        return "我是张坤，基于公开信息，我对消费板块保持乐观。"


def test_chat_uses_llm_when_available(tmp_path):
    _setup_data(tmp_path)
    fake = _FakeLLM()
    dlg = _make_dialogue(tmp_path, llm=fake)
    out = dlg.chat(manager_name="张坤", question="你对后市怎么看？")
    assert fake.calls, "有观点数据时应调用 LLM 蒸馏"
    assert "保持乐观" in out
    assert "不构成投资建议" in out


def test_chat_without_llm_never_calls(tmp_path):
    _setup_data(tmp_path)
    dlg = _make_dialogue(tmp_path, llm=None)
    dlg.chat(manager_name="张坤", question="你对后市怎么看？")
    assert dlg.llm_client is None


def test_chat_empty_question_default(tmp_path):
    _setup_data(tmp_path)
    dlg = _make_dialogue(tmp_path)
    out = dlg.chat(manager_name="张坤", question="")
    assert isinstance(out, str) and len(out) > 20
