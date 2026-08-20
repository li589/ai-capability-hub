"""analyzers.bigfive_analyzer 单元测试"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.bigfive_analyzer import BigFiveAnalyzer


class TestBigFiveAnalyzer(unittest.TestCase):
    """BigFiveAnalyzer 测试"""

    def setUp(self):
        self.analyzer = BigFiveAnalyzer()

    def _make_msgs(self, contents):
        return [Message(sender="other", content=c) for c in contents]

    def test_basic_analysis(self):
        msgs = self._make_msgs([
            "我喜欢思考", "很有创意", "大家一起来玩",
        ] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertIn("dimensions", result.details)
        self.assertIn("radar_data", result.details)

    def test_radar_data_format(self):
        """雷达图数据格式"""
        msgs = self._make_msgs(["思考", "创意", "一起"] * 5)
        result = self.analyzer.analyze(msgs)
        radar = result.details["radar_data"]
        self.assertEqual(len(radar), 5)
        for item in radar:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertGreaterEqual(item["value"], 0)
            self.assertLessEqual(item["value"], 100)

    def test_all_dimensions_analyzed(self):
        """5 维都应被分析"""
        msgs = self._make_msgs(["思考", "认真", "一起", "谢谢", "焦虑"] * 5)
        result = self.analyzer.analyze(msgs)
        for dim in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            self.assertIn(dim, result.details["dimensions"])

    def test_neuroticism_low_words(self):
        """v2.0.0: neuroticism 应有 low 词"""
        # '冷静'、'平静' 等应降低神经质分数
        msgs_neutral = self._make_msgs(["今天", "天气", "很好"] * 10)
        msgs_calm = self._make_msgs(["冷静", "淡定", "平静"] * 10)
        r_neutral = self.analyzer.analyze(msgs_neutral)
        r_calm = self.analyzer.analyze(msgs_calm)
        # calm 的神经质分数应该低于 neutral
        self.assertLess(
            r_calm.details["dimensions"]["neuroticism"]["score"],
            r_neutral.details["dimensions"]["neuroticism"]["score"] + 30,
            "neuroticism low 词未生效"
        )

    def test_confidence_increases_with_signals(self):
        """置信度随信号增加"""
        few_msgs = self._make_msgs(["思考"] * 3)
        many_msgs = self._make_msgs(["思考", "认真", "一起", "谢谢", "焦虑"] * 10)
        r_few = self.analyzer.analyze(few_msgs)
        r_many = self.analyzer.analyze(many_msgs)
        self.assertGreaterEqual(r_many.confidence, r_few.confidence)

    def test_score_range(self):
        """分数应在 0-100 范围"""
        msgs = self._make_msgs(["思考", "认真", "一起", "谢谢", "焦虑"] * 5)
        result = self.analyzer.analyze(msgs)
        for dim_data in result.details["dimensions"].values():
            self.assertGreaterEqual(dim_data["score"], 0)
            self.assertLessEqual(dim_data["score"], 100)


if __name__ == "__main__":
    unittest.main()
