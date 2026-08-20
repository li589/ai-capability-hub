"""analyzers.pattern_analyzer 单元测试

关键测试：v1.2.0 的 reply_speed 丢失 bug 已修复
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.pattern_analyzer import PatternAnalyzer


class TestPatternAnalyzer(unittest.TestCase):
    """PatternAnalyzer 测试"""

    def setUp(self):
        self.analyzer = PatternAnalyzer()

    def test_basic_analysis(self):
        msgs = [
            Message(sender="self", content="你好"),
            Message(sender="other", content="你好"),
            Message(sender="self", content="最近好吗"),
        ]
        result = self.analyzer.analyze(msgs)
        self.assertIn("initiation", result.details)
        self.assertIn("reply_speed", result.details)
        self.assertIn("message_length", result.details)
        self.assertIn("punctuation", result.details)

    def test_reply_speed_present(self):
        """关键测试：v1.2.0 修复的 reply_speed 必须存在"""
        base = datetime(2024, 1, 1, 12, 0, 0)
        msgs = []
        for i in range(10):
            msgs.append(Message(
                sender="other" if i % 2 == 0 else "self",
                content="测试" + str(i),
                timestamp=base + timedelta(seconds=i * 60),
            ))
        result = self.analyzer.analyze(msgs)
        # v1.2.0 修复：reply_speed 字段必须存在
        self.assertIn("reply_speed", result.details)
        rs = result.details["reply_speed"]
        self.assertIn("avg_seconds", rs)
        self.assertIn("count", rs)
        self.assertIn("fast_replies", rs)
        self.assertIn("slow_replies", rs)

    def test_initiation_ratio(self):
        """主动发起对话比例"""
        base = datetime(2024, 1, 1, 12, 0, 0)
        msgs = [
            Message(sender="self", content="hi", timestamp=base),
            Message(sender="other", content="hello", timestamp=base + timedelta(seconds=10)),
        ]
        result = self.analyzer.analyze(msgs)
        init = result.details["initiation"]
        self.assertIn("self", init)
        self.assertIn("other", init)
        self.assertIn("self_pct", init)
        self.assertIn("other_pct", init)

    def test_message_length(self):
        msgs = [
            Message(sender="self", content="短"),
            Message(sender="other", content="这是一条比较长的消息内容"),
        ]
        result = self.analyzer.analyze(msgs)
        ml = result.details["message_length"]
        self.assertIn("self_avg", ml)
        self.assertIn("other_avg", ml)

    def test_punctuation_count(self):
        """问号/感叹号计数"""
        msgs = [
            Message(sender="other", content="你好吗？"),
            Message(sender="other", content="太好了！"),
        ]
        result = self.analyzer.analyze(msgs)
        p = result.details["punctuation"]
        self.assertGreater(p["question_ratio"], 0)
        self.assertGreater(p["exclamation_ratio"], 0)

    def test_burst_detection(self):
        """突发对话检测（>2 小时间隔 = 新一轮）"""
        base = datetime(2024, 1, 1, 12, 0, 0)
        msgs = [
            Message(sender="self", content="hi", timestamp=base),
            # 3 小时后开始新一轮
            Message(sender="other", content="hello", timestamp=base + timedelta(hours=3)),
        ]
        result = self.analyzer.analyze(msgs)
        # 应该有 1 次 self 主动 + 1 次 other 主动
        self.assertEqual(result.details["initiation"]["self"], 1)
        self.assertEqual(result.details["initiation"]["other"], 1)

    def test_duration_days(self):
        """聊天跨度计算"""
        base = datetime(2024, 1, 1, 12, 0, 0)
        msgs = [
            Message(sender="other", content="x", timestamp=base),
            Message(sender="other", content="y", timestamp=base + timedelta(days=10)),
        ]
        result = self.analyzer.analyze(msgs)
        self.assertEqual(result.details["duration_days"], 10)


if __name__ == "__main__":
    unittest.main()
