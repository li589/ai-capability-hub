"""predictors.rule_predictor v2.2.0 升级测试

覆盖 v2.2.0 新增能力：
- 上下文意图识别（question / request / complaint）
- 风险信号检测 + 防守话术
- 风格匹配（基于最近我方回复）
- 情感驱动（暖心/共情）
- 关键词软触发（频次加权）
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictionContext
from predictors.rule_predictor import RulePredictor


def _make_msg(sender: str, content: str, days_ago: int = 0) -> Message:
    return Message(
        sender=sender,
        content=content,
        timestamp=datetime.now() - timedelta(days=days_ago),
    )


class TestRulePredictorV22(unittest.TestCase):
    """RulePredictor v2.2.0 升级测试"""

    def setUp(self):
        self.predictor = RulePredictor()

    # ---- 上下文意图识别 ----

    def test_intent_question(self):
        """问句意图：对方问 '在吗' 应触发答复型话术"""
        msgs = [_make_msg("other", "在吗？", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        # top 或 alternatives 应包含意图响应
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        # 应该有针对 question 的回复
        has_intent_response = any(
            t in ["我看看", "我觉得", "我先确认一下", "你希望呢", "我等下告诉你"]
            for t in all_texts
        )
        self.assertTrue(has_intent_response, f"question 意图未触发: {all_texts}")

    def test_intent_request(self):
        """请求意图：对方说 '帮我' 应触发承诺型话术"""
        msgs = [_make_msg("other", "帮我确认下", 0)]
        ctx = PredictionContext(messages=msgs, scenario="work")
        result = self.predictor.predict(ctx)
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_request_response = any(
            t in ["好的，我处理一下", "我马上看看", "没问题", "我帮你", "确认一下时间"]
            for t in all_texts
        )
        self.assertTrue(has_request_response, f"request 意图未触发: {all_texts}")

    def test_intent_complaint(self):
        """抱怨意图：对方说 '我好累' 应触发共情话术"""
        msgs = [_make_msg("other", "今天好累啊", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_complaint_response = any(
            t in ["怎么了？", "我懂你", "需要我帮忙吗？", "你还好吗？", "要不聊聊？"]
            for t in all_texts
        )
        self.assertTrue(has_complaint_response, f"complaint 意图未触发: {all_texts}")

    # ---- 风险信号 ----

    def test_risk_signal_defensive(self):
        """风险信号：对方说 '别理我' 应触发防守话术"""
        msgs = [_make_msg("other", "别理我，烦死了", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        # top_prediction 应是防守话术
        defensive = {
            "我们冷静一下", "我理解你的感受", "我们换个角度想想", "你的想法很重要",
            "我不想吵架", "我们好好说", "我愿意倾听", "我先冷静一下", "我们都需要时间",
        }
        self.assertIn(result.top_prediction.text, defensive,
                      f"风险场景未触发防守话术: {result.top_prediction.text}")

    def test_risk_signal_high_confidence(self):
        """风险场景下防守话术置信度应较高"""
        msgs = [_make_msg("other", "你太过分了", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        self.assertGreaterEqual(result.top_prediction.confidence, 0.6)

    # ---- 情感驱动 ----

    def test_sentiment_up_warmth(self):
        """情感上升应触发暖心话术"""
        msgs = [_make_msg("other", "今天很开心", 0)]
        ctx = PredictionContext(
            messages=msgs,
            scenario="social",
            sentiment={"trend": "up"},
        )
        result = self.predictor.predict(ctx)
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        warmth_keywords = ["谢谢", "珍惜", "一起", "开心", "好幸福", "暖暖"]
        has_warmth = any(any(kw in t for kw in warmth_keywords) for t in all_texts)
        self.assertTrue(has_warmth, f"情感上升未触发暖心话术: {all_texts}")

    def test_sentiment_down_empathy(self):
        """情感下降应触发共情话术"""
        msgs = [_make_msg("other", "今天心情不好", 0)]
        ctx = PredictionContext(
            messages=msgs,
            scenario="social",
            sentiment={"trend": "down"},
        )
        result = self.predictor.predict(ctx)
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        empathy_keywords = ["懂你", "辛苦", "抱抱", "你很重要", "陪伴"]
        has_empathy = any(any(kw in t for kw in empathy_keywords) for t in all_texts)
        self.assertTrue(has_empathy, f"情感下降未触发共情话术: {all_texts}")

    # ---- 关键词软触发 ----

    def test_keyword_soft_trigger(self):
        """关键词软触发：'吃饭' 出现 3 次应触发"""
        msgs = [_make_msg("other", "吃饭", 0) for _ in range(3)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        keyword_hits = any("吃" in t for t in all_texts)
        self.assertTrue(keyword_hits, f"关键词 '吃饭' 未触发: {all_texts}")

    # ---- 风格匹配 ----

    def test_style_match_question(self):
        """我方历史风格：常提问，应产出疑问型预测"""
        msgs = (
            [_make_msg("self", "你觉得呢？", 0),
             _make_msg("other", "嗯嗯", 0),
             _make_msg("self", "怎么样？", 0),
             _make_msg("other", "好的", 0),
             _make_msg("self", "是什么？", 0),
             _make_msg("other", "嗯", 0)]
        )
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_style_match = any("？" in t or "呢" in t for t in all_texts)
        self.assertTrue(has_style_match, f"风格匹配未触发疑问型: {all_texts}")

    # ---- 综合 ----

    def test_metadata_includes_features(self):
        """metadata 应包含上下文特征"""
        msgs = [_make_msg("other", "你好吗？", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        meta = result.metadata
        self.assertIn("feature_snapshot", meta)
        self.assertIn("total_candidates", meta)
        # 上下文应有 last_intent
        self.assertIn("last_intent", result.context)

    def test_context_intent_propagated(self):
        """预测结果 context 应包含 last_intent"""
        msgs = [_make_msg("other", "在吗？", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        self.assertEqual(result.context["last_intent"], "question")

    def test_risk_flag_propagated(self):
        """风险信号应传播到 context"""
        msgs = [_make_msg("other", "滚", 0)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        self.assertTrue(result.context["has_risk"])


if __name__ == "__main__":
    unittest.main()
