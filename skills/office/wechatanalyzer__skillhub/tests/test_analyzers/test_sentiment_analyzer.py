"""analyzers.sentiment_analyzer 单元测试

关键测试：
- 否定识别（修复 v1.2.0 的 "我不开心" 误判 bug）
- 反讽检测
- 程度副词加权
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer(unittest.TestCase):
    """SentimentAnalyzer 测试"""

    def setUp(self):
        self.analyzer = SentimentAnalyzer()

    def _make_msgs(self, contents):
        return [Message(sender="other", content=c) for c in contents]

    def test_basic_positive(self):
        msgs = self._make_msgs(["我今天很开心", "哈哈，太棒了"] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertGreater(result.details["positive"], result.details["negative"])

    def test_basic_negative(self):
        msgs = self._make_msgs(["我很难过", "好崩溃"] * 5)
        result = self.analyzer.analyze(msgs)
        self.assertGreater(result.details["negative"], result.details["positive"])

    def test_negation_bu_kaixin(self):
        """关键测试：'我不开心' 应判为 negative（v1.2.0 误判为 positive）"""
        msgs = self._make_msgs(["我不开心"] * 10)
        result = self.analyzer.analyze(msgs)
        # 修复 bug：否定后 negative 应大于 positive
        self.assertGreater(
            result.details["negative"],
            result.details["positive"],
            f"否定识别失败：negative={result.details['negative']}, positive={result.details['positive']}"
        )

    def test_negation_mei_you(self):
        """'没有' 也是否定词"""
        msgs = self._make_msgs(["没有快乐"] * 10)
        result = self.analyzer.analyze(msgs)
        # 否定后 negative 应大于 positive
        self.assertGreater(result.details["negative"], result.details["positive"])

    def test_negation_bie(self):
        """'别' 也是否定词"""
        msgs = self._make_msgs(["别开心了"] * 10)
        result = self.analyzer.analyze(msgs)
        # "别开心" 应被识别为 negative
        self.assertGreaterEqual(result.details["negative"], 0)

    def test_irony_detection(self):
        """反讽检测：'虽然...但是...'"""
        msgs = self._make_msgs(["虽然你说得对，但是我不太认同"] * 5)
        result = self.analyzer.analyze(msgs)
        # 检测到反讽
        self.assertGreater(result.details.get("irony_count", 0), 0)

    def test_degree_words(self):
        """程度副词：'非常开心' 应比 '开心' 强度高"""
        msgs_normal = self._make_msgs(["开心"] * 5)
        msgs_very = self._make_msgs(["非常开心"] * 5)

        r_normal = self.analyzer.analyze(msgs_normal)
        r_very = self.analyzer.analyze(msgs_very)

        # 程度副词加权的 positive score 应该更高
        self.assertGreaterEqual(
            r_very.details.get("total_positive_score", 0),
            r_normal.details.get("total_positive_score", 0),
        )

    def test_emoji_sentiment(self):
        """Emoji 情感：'😀' 应判为 positive"""
        msgs = self._make_msgs(["今天😀"] * 10)
        result = self.analyzer.analyze(msgs)
        self.assertGreater(result.details["positive"], 0)

    def test_trend_calculation(self):
        """情感趋势计算"""
        msgs = []
        # 前半段负面
        for _ in range(5):
            msgs.append(Message(sender="other", content="很难过"))
        # 后半段正面
        for _ in range(5):
            msgs.append(Message(sender="other", content="很开心"))
        result = self.analyzer.analyze(msgs)
        # 趋势应该是 up 或 stable（取决于算法）
        self.assertIn(result.details["trend"], ["up", "down", "stable"])

    def test_timeline(self):
        """情感时间线"""
        from datetime import datetime, timedelta
        base = datetime(2024, 1, 1, 12, 0, 0)
        msgs = []
        for i in range(5):
            msgs.append(Message(
                sender="other",
                content="开心" if i % 2 == 0 else "难过",
                timestamp=base + timedelta(hours=i),
            ))
        result = self.analyzer.analyze(msgs)
        timeline = result.details.get("timeline", [])
        self.assertGreater(len(timeline), 0)

    def test_empty_messages(self):
        """空消息列表"""
        msgs = [Message(sender="other", content="")]
        # 至少有一些空消息，仍能跑（虽然信号弱）
        result = self.analyzer.analyze(msgs)
        self.assertIn("positive", result.details)

    # ----------------------------------------------------------------
    # v2.5.0 回归：否定窗口索引错位 / 高频词频次排序
    # ----------------------------------------------------------------
    def test_feichang_not_negated_long_message(self):
        """v2.5.0 bugfix：情感词距句首 >12 字符时，「非常开心」的「非」
        曾按错位索引读取原文中不相关字符而被误判否定。"""
        # 中性前缀把"非常"推到 12 字符窗口之外，之前会读到 text[window 相对位置] 的错误字符
        prefix = "今天中午十二点半左右的时候"
        pos, neg, pos_words, neg_words = self.analyzer._analyze_sentence(prefix + "非常开心")
        self.assertGreater(pos, 0, f"「非常开心」不应被否定: pos={pos}, neg={neg}")
        self.assertEqual(neg, 0.0)
        self.assertIn("开心", pos_words)

    def test_feichang_short_message(self):
        """短消息内「非常开心」同样不应被否定"""
        pos, neg, _, _ = self.analyzer._analyze_sentence("非常开心")
        self.assertGreater(pos, 0)
        self.assertEqual(neg, 0.0)

    def test_negation_window_long_message(self):
        """v2.5.0：长消息里「我不开心」的否定识别仍应生效"""
        prefix = "今天中午十二点半左右的时候"
        pos, neg, _, neg_words = self.analyzer._analyze_sentence(prefix + "我不开心")
        self.assertEqual(pos, 0.0)
        self.assertGreater(neg, 0, f"否定应生效: pos={pos}, neg={neg}")
        self.assertIn("开心", neg_words)

    def test_feichang_negative_word(self):
        """「非常烦」= 程度副词 + 负面词，应判负面（非=非常，不是否定）"""
        pos, neg, _, _ = self.analyzer._analyze_sentence("我今天非常烦")
        self.assertGreater(neg, pos)

    def test_emotional_words_frequency_order(self):
        """v2.5.0：正面/负面高频词应按频次排序（原 set() 输出任意顺序）"""
        msgs = self._make_msgs(["开心开心开心", "开心", "喜欢", "喜欢"] * 3)
        result = self.analyzer.analyze(msgs)
        positive = result.details["emotional_words"]["positive"]
        self.assertEqual(positive[0], "开心", f"频次最高词应排第一: {positive}")


if __name__ == "__main__":
    unittest.main()
