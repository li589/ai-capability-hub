"""analyzers.risk_analyzer 单元测试"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzer(unittest.TestCase):
    """RiskAnalyzer 测试"""

    def setUp(self):
        self.analyzer = RiskAnalyzer()

    def _make_msgs(self, contents):
        return [Message(sender="other", content=c) for c in contents]

    def test_pig_butcher_detection(self):
        """杀猪盘检测"""
        msgs = self._make_msgs([
            "我推荐一个投资平台",
            "稳赚不赔",
            "高回报",
        ] * 3)
        result = self.analyzer.analyze(msgs)
        self.assertIn("pig_butcher", result.details.get("risks", {}))

    def test_work_shirt_detection(self):
        """职场甩锅检测"""
        msgs = self._make_msgs([
            "不是我的问题",
            "我没收到",
            "按规定",
        ] * 3)
        result = self.analyzer.analyze(msgs)
        self.assertIn("work_shirt", result.details.get("risks", {}))

    def test_hr_bad_detection(self):
        """HR 不当检测"""
        msgs = self._make_msgs([
            "试用期",
            "强制加班",
            "不签合同",
        ] * 3)
        result = self.analyzer.analyze(msgs)
        self.assertIn("hr_bad", result.details.get("risks", {}))

    def test_innocent_phrase_exclusion(self):
        """无害场景排除：'投资个生日礼物'"""
        msgs = self._make_msgs([
            "我想投资个生日礼物给你",
            "投资学习很重要",
        ] * 5)
        result = self.analyzer.analyze(msgs)
        # 应该被识别为可能是误报
        if "pig_butcher" in result.details.get("risks", {}):
            risk_data = result.details["risks"]["pig_butcher"]
            self.assertTrue(risk_data.get("false_positive_likely", False))

    def test_negation_exclusion(self):
        """否定排除：'不投资'"""
        msgs = self._make_msgs([
            "我不投资",
            "别充值",
        ] * 3)
        result = self.analyzer.analyze(msgs)
        # 应该不告警或低风险
        if "pig_butcher" in result.details.get("risks", {}):
            risk_data = result.details["risks"]["pig_butcher"]
            self.assertTrue(risk_data.get("negation_excluded", False))

    def test_no_risk(self):
        """无风险"""
        msgs = self._make_msgs([
            "今天天气真好",
            "我们去散步吧",
        ] * 5)
        result = self.analyzer.analyze(msgs)
        # 应该是无风险或低风险
        self.assertEqual(result.details.get("overall_level", "low"), "low")

    def test_high_risk_threshold(self):
        """高风险阈值：≥3 次匹配"""
        msgs = self._make_msgs([
            "投资", "赚钱", "充值", "转账", "高回报"
        ] * 3)
        result = self.analyzer.analyze(msgs)
        if "pig_butcher" in result.details.get("risks", {}):
            self.assertEqual(result.details["risks"]["pig_butcher"]["level"], "high")

    def test_response_strategies(self):
        """应对话术生成"""
        msgs = self._make_msgs(["投资", "充值"] * 3)
        result = self.analyzer.analyze(msgs)
        if "pig_butcher" in result.details.get("risks", {}):
            strategies = result.details["risks"]["pig_butcher"].get("response_strategies", {})
            self.assertIn("defensive", strategies)
            self.assertIn("offensive", strategies)
            self.assertIn("diplomatic", strategies)


if __name__ == "__main__":
    unittest.main()
