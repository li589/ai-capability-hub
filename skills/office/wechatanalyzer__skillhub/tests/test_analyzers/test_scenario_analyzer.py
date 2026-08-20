"""analyzers.scenario_analyzer 单元测试"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.scenario_analyzer import ScenarioAnalyzer


class TestScenarioAnalyzer(unittest.TestCase):
    """ScenarioAnalyzer 测试"""

    def setUp(self):
        self.analyzer = ScenarioAnalyzer()

    def _make_msgs(self, contents):
        return [Message(sender="other", content=c) for c in contents]

    def test_romantic_scenario(self):
        """恋爱场景"""
        msgs = self._make_msgs([
            "我喜欢你", "想你了", "亲爱的", "约会吧"
        ] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertEqual(result.details["primary"], "romantic")

    def test_work_scenario(self):
        """工作场景"""
        msgs = self._make_msgs([
            "项目进度", "deadline", "开会", "加班"
        ] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertEqual(result.details["primary"], "work")

    def test_social_scenario(self):
        """社交场景"""
        msgs = self._make_msgs([
            "朋友聚会", "一起玩", "旅游", "美食"
        ] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertEqual(result.details["primary"], "social")

    def test_important_scenario(self):
        """重要事项"""
        msgs = self._make_msgs([
            "紧急", "必须完成", "deadline", "交付"
        ] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertEqual(result.details["primary"], "important")

    def test_weights_returned(self):
        """返回权重字典"""
        msgs = self._make_msgs(["工作", "聚会"] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertIn("weights", result.details)
        self.assertEqual(len(result.details["weights"]), 4)

    def test_suggestions_provided(self):
        """提供建议"""
        msgs = self._make_msgs(["喜欢", "想你"] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertIn("suggestions", result.details)


if __name__ == "__main__":
    unittest.main()
