"""analyzers.mbti_analyzer 单元测试"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.mbti_analyzer import MBTIAnalyzer


class TestMBTIAnalyzer(unittest.TestCase):
    """MBTIAnalyzer 测试"""

    def setUp(self):
        self.analyzer = MBTIAnalyzer()
        self.min_msgs = [
            Message(sender="other", content="我们一起出去玩吧" * 3),
            Message(sender="other", content="大家觉得呢" * 3),
        ] * 6  # 12 条

    def test_validate_too_few_messages(self):
        msgs = [Message(sender="other", content="x")] * 5
        self.assertFalse(self.analyzer.validate(msgs))

    def test_validate_enough_messages(self):
        self.assertTrue(self.analyzer.validate(self.min_msgs))

    def test_analyze_basic(self):
        result = self.analyzer.analyze(self.min_msgs)
        self.assertEqual(result.analyzer_name, "mbti")
        self.assertIn("type", result.details)
        self.assertIn("name", result.details)
        self.assertIn("dimension_scores", result.details)
        self.assertEqual(len(result.details["type"]), 4)  # MBTI 4 个字母

    def test_analyze_mbti_in_valid_types(self):
        result = self.analyzer.analyze(self.min_msgs)
        mbti = result.details["type"]
        valid_types = [
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP",
        ]
        self.assertIn(mbti, valid_types)

    def test_confidence_in_range(self):
        result = self.analyzer.analyze(self.min_msgs)
        self.assertGreaterEqual(result.confidence, 0)
        self.assertLessEqual(result.confidence, 100)

    def test_dimension_scores_complete(self):
        result = self.analyzer.analyze(self.min_msgs)
        scores = result.details["dimension_scores"]
        for dim in ["E", "I", "S", "N", "T", "F", "J", "P"]:
            self.assertIn(dim, scores)
            self.assertGreaterEqual(scores[dim], 0)

    def test_preference_format(self):
        result = self.analyzer.analyze(self.min_msgs)
        pref = result.details["preference"]
        for k in ["EI", "SN", "TF", "JP"]:
            self.assertIn(k, pref)
            self.assertIn(pref[k], ["E", "I", "S", "N", "T", "F", "J", "P"])

    def test_confidence_with_more_messages(self):
        # 大量消息 → 更高置信度
        many_msgs = [
            Message(sender="other", content="我们一起出去玩吧")
            for _ in range(100)
        ]
        result = self.analyzer.analyze(many_msgs)
        # 大量消息 + 强信号 → 置信度应该较高
        self.assertGreaterEqual(result.confidence, 50)


if __name__ == "__main__":
    unittest.main()
