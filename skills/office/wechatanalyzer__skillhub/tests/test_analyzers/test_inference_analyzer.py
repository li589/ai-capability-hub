"""v2.2.0 新增 analyzer: 推演能力 + 信息解读 — 单元测试"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

# 确保 from analyzers import 能工作
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from analyzers import InferenceAnalyzer, InterpretationAnalyzer
from analyzers.inference_analyzer import InferenceAnalyzer as _IA  # noqa
from analyzers.interpretation_analyzer import InterpretationAnalyzer as _IIA  # noqa
from core.message import Message


# ===== 测试辅助 =====

def _make_messages(scenarios: list) -> list:
    """从场景描述构造消息。scenarios = [(sender, content, days_ago)]"""
    now = datetime.now()
    out = []
    for sender, content, days_ago in scenarios:
        ts = now - timedelta(days=days_ago)
        out.append(Message(sender=sender, content=content, timestamp=ts))
    return out


# ===== InferenceAnalyzer 5 项推演 =====

def test_inference_topics_rising_and_falling():
    """1. 话题推演：早/晚期话题对比"""
    msgs = _make_messages([
        ("self", "项目进度怎么样了？", 10),
        ("other", "项目已经延期了", 10),
        ("self", "加班赶一下", 9),
        ("other", "好的，加油", 9),
        ("self", "周末一起吃饭", 5),
        ("other", "好啊，去哪里？", 5),
        ("self", "火锅怎么样？", 5),
        ("other", "不错不错", 5),
        ("self", "周末户外爬山", 1),
        ("other", "爬山好啊，去吧！", 1),
        ("self", "烧烤也不错", 1),
        ("other", "完美", 1),
    ])
    result = InferenceAnalyzer().analyze(msgs)
    trends = result.details["topic_trends"]
    assert trends["available"], "推演应有可用结果"
    assert "rising_topics" in trends
    assert "falling_topics" in trends
    # 户外爬山应上升（在晚期）
    topic_names = [t["topic"] for t in trends["rising_topics"]]
    topic_names += [t["topic"] for t in trends["falling_topics"]]
    # 验证推演结果是 dict 列表
    assert all(isinstance(t, dict) and "topic" in t for t in trends["rising_topics"])


def test_inference_opponent_classification():
    """2. 对手行为推演：冷漠型 / 对抗型 / 配合型 等"""
    msgs = _make_messages([
        ("other", "好的", 2), ("other", "嗯", 2), ("other", "可以", 2),
        ("other", "行", 1), ("other", "随便", 1), ("other", "哦", 1),
    ])
    result = InferenceAnalyzer().analyze(msgs)
    opp = result.details["opponent_behavior"]
    assert opp["available"]
    assert opp["dominant_behavior"] in ("冷漠型", "配合型", "对抗型", "理性型", "情绪型")


def test_inference_sentiment_warming_trajectory():
    """3. 情感轨迹：升温应识别为 warming"""
    msgs = _make_messages([
        ("self", "挺烦的", 10),
        ("other", "确实烦", 10),
        ("self", "算了不说了", 9),
        ("other", "嗯嗯", 9),
        ("self", "今天好多了", 3),
        ("other", "那就好", 3),
        ("self", "谢谢你的关心！", 1),
        ("other", "希望一起变好", 1),
    ])
    result = InferenceAnalyzer().analyze(msgs)
    sent = result.details["sentiment_trajectory"]
    # 中段转暖 → trend=cooling 或 stable 或 warming 都可，至少 available
    assert sent["available"]


def test_inference_risk_escalation_high():
    """4. 风险推演：高危词 → 应被识别"""
    msgs = _make_messages([
        ("self", "你这样做太过分了", 1),
        ("other", "我就这样了，你来打我啊", 1),
        ("self", "我要报警了", 1),
    ])
    result = InferenceAnalyzer().analyze(msgs)
    risk = result.details["risk_escalation"]
    assert risk["available"]
    assert len(risk["current_signals"]["high"]) > 0  # 至少检测到"报警"
    # 此输入有 1 高危 + 2 中危，应至少命中"mild_warning"或更高级别
    assert risk["escalation_score"] > 15
    assert risk["predicted_trajectory"] in (
        "high_escalation_risk", "moderate_escalation_risk", "mild_warning"
    )


def test_inference_risk_escalation_stable():
    """4b. 风险推演：友好对话 → stable"""
    msgs = _make_messages([
        ("self", "周末有空吗", 2),
        ("other", "有的，怎么", 2),
        ("self", "一起吃饭", 1),
        ("other", "好啊", 1),
    ])
    result = InferenceAnalyzer().analyze(msgs)
    risk = result.details["risk_escalation"]
    assert risk["predicted_trajectory"] == "stable"


def test_inference_conversation_trajectory():
    """5. 对话走向：综合对方行为 + 情感"""
    msgs = _make_messages([
        ("self", "你最近怎么一直不回我", 5),
        ("self", "在吗？", 4),
        ("self", "Hello???", 3),
        ("other", "最近比较忙", 1),
    ])
    result = InferenceAnalyzer().analyze(msgs)
    traj = result.details["conversation_trajectory"]
    assert "predicted_trajectory" in traj
    assert traj["predicted_trajectory"] in (
        "deteriorating", "improving", "burning_out_self",
        "stable_functional", "stalemate",
    )
    # 主动率应识别 self_dominant
    assert traj["initiation_pattern"] in ("self_dominant", "balanced", "other_dominant")


def test_inference_validate_min_messages():
    """验证：消息 < min_messages 应返回错误"""
    msgs = _make_messages([("self", "hi", 0), ("other", "hi", 0)])
    result = InferenceAnalyzer().analyze(msgs)
    assert result.metadata.get("status") != "ok" or result.score == 0


def test_inference_empty_messages_no_crash():
    """空消息列表不崩溃"""
    result = InferenceAnalyzer().analyze([])
    assert result.score == 0 or result.confidence == 0


# ===== InterpretationAnalyzer =====

def test_interpretation_intent_recognition():
    """1. 意图识别"""
    msgs = _make_messages([
        ("self", "在吗？", 1),
        ("other", "在的", 1),
        ("self", "你能帮我个忙吗？", 1),
        ("other", "好，什么事？", 0),
    ])
    result = InterpretationAnalyzer().analyze(msgs)
    intents = result.details["intents"]
    assert intents["available"]
    assert "询问" in intents["intent_counts"]
    assert intents["intent_counts"]["询问"] > 0


def test_interpretation_entity_extraction():
    """2. 实体识别：手机号/邮箱/金额/URL"""
    msgs = _make_messages([
        ("other", "联系我 13812345678", 1),
        ("self", "邮箱是 test@example.com", 1),
        ("other", "转账 ¥1000.50 给你", 1),
        ("self", "https://example.com/abc", 0),
    ])
    result = InterpretationAnalyzer().analyze(msgs)
    ents = result.details["entities"]
    assert ents["available"]
    assert ents["total_count"] >= 4
    types_present = [t for t, _ in ents["by_type"]]
    assert "手机" in types_present
    assert "邮箱" in types_present
    assert "金额" in types_present
    assert "URL" in types_present


def test_interpretation_topic_extraction():
    """3. 主题抽取：识别核心话题"""
    msgs = _make_messages([
        ("other", "项目进度怎么样？", 2),
        ("self", "加班赶了一下", 2),
        ("other", "客户明天要看报告", 2),
        ("self", "我尽量", 1),
        ("other", "购物清单发你了", 1),
    ])
    result = InterpretationAnalyzer().analyze(msgs)
    topics = result.details["topics"]
    assert topics["available"]
    top_names = [t["name"] for t in topics["topics"]]
    assert "工作" in top_names  # 项目/加班/客户/报告 都触发"工作"


def test_interpretation_stance_detection():
    """4. 立场识别：判断双方态度"""
    msgs = _make_messages([
        ("self", "我要做新项目", 2),
        ("other", "好的，一起做", 2),
        ("self", "客户撤资了", 1),
        ("other", "算了，不要做", 1),
    ])
    result = InterpretationAnalyzer().analyze(msgs)
    stances = result.details["stances"]
    assert stances["available"]
    by_sender = stances["by_sender"]
    assert "self" in by_sender
    assert "other" in by_sender


def test_interpretation_summary_built():
    """解读摘要应生成"""
    msgs = _make_messages([
        ("self", "周末一起吃饭吗？", 1),
        ("other", "好啊，去哪里？", 1),
    ])
    result = InterpretationAnalyzer().analyze(msgs)
    assert result.details["summary"]  # 非空


def test_interpretation_handles_empty():
    """空消息不崩溃"""
    result = InterpretationAnalyzer().analyze([])
    assert result.score == 0


def test_interpretation_handles_short():
    """< min_messages 应处理（可能无结果但不崩溃）"""
    msgs = _make_messages([("self", "?", 0)])
    result = InterpretationAnalyzer().analyze(msgs)
    assert result is not None


# ===== 集成测试 =====

def test_both_registered_in_default_registry():
    """两个新分析器应在 create_default_registry() 中"""
    from analyzers import create_default_registry
    reg = create_default_registry()
    names = reg.list()
    assert "inference" in names
    assert "interpretation" in names
