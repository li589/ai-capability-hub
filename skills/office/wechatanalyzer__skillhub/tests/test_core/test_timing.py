"""core.timing 时间特征测试（v2.3.0）"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.timing import analyze_timing


class TestTimingInfo(unittest.TestCase):
    def test_immediate_urgency(self):
        now = datetime(2026, 8, 1, 12, 0, 0)
        msg = Message(
            sender="other",
            content="在吗？",
            timestamp=now - timedelta(minutes=3),
        )
        timing = analyze_timing([msg], now=now)
        self.assertEqual(timing.urgency, "immediate")
        self.assertEqual(timing.time_of_day, "day")

    def test_stale_urgency(self):
        now = datetime(2026, 8, 1, 12, 0, 0)
        msg = Message(
            sender="other",
            content="你好",
            timestamp=now - timedelta(days=3),
        )
        timing = analyze_timing([msg], now=now)
        self.assertEqual(timing.urgency, "stale")
        self.assertGreater(timing.last_message_age_minutes, 24 * 60)

    def test_burst_detection(self):
        now = datetime(2026, 8, 1, 12, 0, 0)
        messages = [
            Message(sender="other", content="1", timestamp=now - timedelta(minutes=25)),
            Message(sender="other", content="2", timestamp=now - timedelta(minutes=10)),
            Message(sender="other", content="3", timestamp=now - timedelta(minutes=1)),
        ]
        timing = analyze_timing(messages, now=now)
        self.assertTrue(timing.burst)

    def test_no_timestamps(self):
        msg = Message(sender="other", content="你好")
        timing = analyze_timing([msg])
        self.assertFalse(timing.has_timestamps)
        self.assertEqual(timing.urgency, "unknown")
