# -*- coding: utf-8 -*-
"""v10.0 测试：客户行为偏差画像（behavioral_profile）"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "client_manager"))


def _engine(tmp_path=None):
    from behavioral_profile import BehavioralBiasEngine
    return BehavioralBiasEngine(data_dir=tmp_path)


def test_questionnaire_loaded():
    eng = _engine()
    assert len(eng.questionnaire.get("questions", [])) == 10


def test_score_range():
    eng = _engine()
    answers = {f"q{i}": 0 for i in range(1, 11)}
    r = eng.score_questionnaire(answers)
    for k, v in r.items():
        assert 0 <= v <= 100, f"{k}={v} 超出 0-100"


def test_loss_aversion_dominant():
    """全选损失厌恶选项 → loss_aversion 最高且类型为割肉敏感型"""
    eng = _engine()
    answers = {"q1": 0, "q2": 1, "q3": 0, "q4": 0, "q5": 0,
               "q6": 2, "q7": 0, "q8": 0, "q9": 1, "q10": 1}
    r = eng.assess(answers=answers)
    scores = r["bias_scores"]
    assert scores["loss_aversion"] >= 60
    assert scores["loss_aversion"] == max(scores.values())
    assert r["investor_type"] == "割肉敏感型"
    assert r["confidence"] == "medium"


def test_herding_dominant():
    eng = _engine()
    answers = {"q4": 3, "q8": 3}  # 两个从众题都选最激进
    r = eng.assess(answers=answers)
    assert r["bias_scores"]["herding"] == 100
    assert r["investor_type"] == "追涨从众型"


def test_stable_type_when_all_low():
    eng = _engine()
    answers = {"q1": 2, "q2": 2, "q3": 0, "q4": 0, "q5": 0,
               "q6": 0, "q7": 2, "q8": 0, "q9": 2, "q10": 3}
    r = eng.assess(answers=answers)
    assert r["investor_type"] in ("稳健配置型", "综合平衡型")
    assert r["confidence"] in ("medium", "high")


def test_adjust_from_emotional_records():
    eng = _engine()
    answers = {f"q{i}": 0 for i in range(1, 11)}
    recs = [
        {"emotion": "焦虑", "cause": "亏损15%", "intensity": 8},
        {"emotion": "恐惧", "cause": "亏损", "intensity": 9},
    ]
    r = eng.assess(answers=answers, emotional_records=recs)
    assert r["bias_scores"]["loss_aversion"] > 0
    assert "情绪记录" in r["data_sources"]


def test_import_history_overtrading():
    eng = _engine()
    answers = {f"q{i}": 0 for i in range(1, 11)}
    import_history = [{"timestamp": "2026-08-01T10:00:00"},
                      {"timestamp": "2026-08-03T10:00:00"},
                      {"timestamp": "2026-08-05T10:00:00"}]
    r = eng.assess(answers=answers, import_history=import_history)
    assert r["bias_scores"]["overtrading"] >= 10
    assert "导入历史" in r["data_sources"]


def test_assess_from_store(tmp_path):
    """client_id 模式：自动读取数据目录中的情绪记录与画像"""
    (tmp_path / "emotional_records.json").write_text(json.dumps({
        "客户A": [{"emotion": "焦虑", "cause": "亏损10%", "intensity": 8}],
    }, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "user_profiles.json").write_text(json.dumps({
        "客户A": {"stop_loss": -4.0},
    }, ensure_ascii=False), encoding="utf-8")
    eng = _engine(tmp_path)
    r = eng.assess(client_id="客户A")
    assert r["bias_scores"]["loss_aversion"] >= 20
    assert "情绪记录" in r["data_sources"]
    assert "画像设置" in r["data_sources"]
    assert r["confidence"] == "medium"


def test_save_answers_roundtrip(tmp_path):
    eng = _engine(tmp_path)
    eng.save_answers("客户B", {"q1": 0, "q2": 1})
    loaded = eng._load_answers("客户B")
    assert loaded == {"q1": 0, "q2": 1}


def test_communication_guide_contents():
    eng = _engine()
    answers = {"q4": 3, "q8": 3}
    r = eng.assess(answers=answers)
    g = r["communication_guide"]
    assert g["tone"]
    assert g["risk_warning_frequency"]
    assert g["alert_thresholds"]
    assert g["do_dont"]


def test_format_report():
    eng = _engine()
    answers = {f"q{i}": 0 for i in range(1, 11)}
    r = eng.assess(client_id="客户C", answers=answers)
    text = eng.format_report(r)
    assert "客户行为画像" in text
    assert "心理类型" in text
    assert "损失厌恶" in text
    assert "沟通策略" in text
