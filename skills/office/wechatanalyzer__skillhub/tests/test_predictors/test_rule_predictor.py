"""predictors.rule_predictor 单元测试"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictionContext
from predictors.rule_predictor import RulePredictor


class TestRulePredictor(unittest.TestCase):
    """RulePredictor 测试"""

    def setUp(self):
        self.predictor = RulePredictor()

    def test_is_available(self):
        self.assertTrue(self.predictor.is_available())

    def test_predict_basic(self):
        ctx = PredictionContext(
            messages=[Message(sender="other", content="今天吃饭？")],
            mbti="ENFP",
            scenario="romantic",
        )
        result = self.predictor.predict(ctx)
        self.assertIsNotNone(result.top_prediction)
        self.assertGreater(result.top_prediction.confidence, 0)

    def test_predict_with_mbti(self):
        """MBTI 模板匹配"""
        ctx = PredictionContext(
            messages=[Message(sender="other", content="x")],
            mbti="ENFP",
            scenario="social",
        )
        result = self.predictor.predict(ctx)
        # ENFP 模板："太有趣了！"、"你有没有想过..."、"让我们尝试点新鲜的"
        # 应有 ENFP 模板的预测
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_enfp = any("有趣" in t or "新鲜" in t or "想" in t for t in all_texts)
        self.assertTrue(has_enfp, f"未找到 ENFP 模板预测: {all_texts}")

    def test_predict_with_scenario(self):
        """场景模板"""
        ctx = PredictionContext(
            messages=[Message(sender="other", content="x")],
            scenario="work",
        )
        result = self.predictor.predict(ctx)
        # work 模板："收到，我处理一下" 等
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_work = any("处理" in t or "确认" in t or "跟进" in t for t in all_texts)
        self.assertTrue(has_work, f"未找到 work 场景预测: {all_texts}")

    def test_predict_with_keyword(self):
        """关键词触发"""
        msgs = [Message(sender="other", content="一起吃饭吧") for _ in range(5)]
        ctx = PredictionContext(messages=msgs, scenario="social")
        result = self.predictor.predict(ctx)
        # "吃饭" 关键词应触发："一起吃吗？"、"你定时间"、"想吃什么？"
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_keyword = any("吃" in t for t in all_texts)
        self.assertTrue(has_keyword, f"未触发'吃饭'关键词: {all_texts}")

    def test_predict_no_messages(self):
        """无消息"""
        ctx = PredictionContext(messages=[], scenario="social")
        result = self.predictor.predict(ctx)
        # 仍应有默认预测
        self.assertIsNotNone(result.top_prediction)
        self.assertGreater(len(result.top_prediction.text), 0)

    def test_predict_multiple_predictions(self):
        """多个预测候选"""
        msgs = [Message(sender="other", content="工作很忙，加班很多，想看电影")]
        ctx = PredictionContext(
            messages=msgs,
            mbti="ENFP",
            scenario="work",
        )
        result = self.predictor.predict(ctx)
        # 应该有 top + alternatives
        self.assertGreaterEqual(len(result.alternatives), 1)

    def test_predict_sentiment_driven(self):
        """情感驱动预测"""
        msgs = [Message(sender="other", content="很开心" * 5)]
        ctx = PredictionContext(
            messages=msgs,
            sentiment={"trend": "up"},
        )
        result = self.predictor.predict(ctx)
        # 上升趋势应触发："继续保持这样挺好的"
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_sentiment = any("继续" in t or "挺好" in t for t in all_texts)
        self.assertTrue(has_sentiment, f"情感趋势未触发: {all_texts}")


if __name__ == "__main__":
    unittest.main()
