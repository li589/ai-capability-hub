"""scripts.calendar_manager 单元测试（v2.7.0 补全）

覆盖：
- 日期解析（今天/明天/后天/X天后/周/标准日期/月日）
- 事件类型 / 重要性 / 时间 / 标题 提取
- 从消息完整提取事件 + 存取回环
"""

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.calendar_manager import CalendarManager


class TestCalendarManagerDateParse(unittest.TestCase):
    """日期解析测试"""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.cm = CalendarManager({"db_path": str(tmp / "test.db")})
        self.ref = datetime(2026, 8, 13)

    def test_parse_today(self):
        self.assertEqual(self.cm._parse_date("今天", self.ref), self.ref)

    def test_parse_tomorrow(self):
        self.assertEqual(self.cm._parse_date("明天", self.ref), datetime(2026, 8, 14))

    def test_parse_day_after_tomorrow(self):
        self.assertEqual(self.cm._parse_date("后天", self.ref), datetime(2026, 8, 15))

    def test_parse_days_later(self):
        self.assertEqual(self.cm._parse_date("3天后", self.ref), datetime(2026, 8, 16))

    def test_parse_weeks_later(self):
        self.assertEqual(self.cm._parse_date("2周后", self.ref), datetime(2026, 8, 27))

    def test_parse_standard_date(self):
        self.assertEqual(self.cm._parse_date("2026-09-01", self.ref), datetime(2026, 9, 1))

    def test_parse_slash_date(self):
        self.assertEqual(self.cm._parse_date("2026/09/01", self.ref), datetime(2026, 9, 1))

    def test_parse_month_day_no_year(self):
        # "01-01" 无年份 → 补参考年份
        self.assertEqual(self.cm._parse_date("01-01", self.ref), datetime(2026, 1, 1))

    def test_parse_invalid_returns_none(self):
        self.assertIsNone(self.cm._parse_date("随便", self.ref))


class TestCalendarManagerDetect(unittest.TestCase):
    """事件类型 / 重要性 / 时间 / 标题 提取测试"""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.cm = CalendarManager({"db_path": str(tmp / "test.db")})

    def test_detect_meeting(self):
        self.assertEqual(self.cm._detect_event_type("明天开会讨论方案"), "meeting")

    def test_detect_deadline(self):
        self.assertEqual(self.cm._detect_event_type("周五前截止提交"), "deadline")

    def test_detect_appointment(self):
        self.assertEqual(self.cm._detect_event_type("周末见面聊聊"), "appointment")

    def test_detect_birthday(self):
        self.assertEqual(self.cm._detect_event_type("下月生日聚会"), "birthday")

    def test_detect_no_event(self):
        self.assertIsNone(self.cm._detect_event_type("今天天气不错"))

    def test_detect_importance_high(self):
        self.assertEqual(self.cm._detect_importance("紧急：今天必须完成"), "high")

    def test_detect_importance_medium(self):
        self.assertEqual(self.cm._detect_importance("记得提醒我"), "medium")

    def test_detect_importance_low(self):
        self.assertEqual(self.cm._detect_importance("随便聊聊"), "low")

    def test_extract_time(self):
        self.assertEqual(self.cm._extract_time("下午 14:30 开会"), "14:30")

    def test_extract_time_none(self):
        self.assertIsNone(self.cm._extract_time("下午开会"))

    def test_extract_title_strips_datetime(self):
        title = self.cm._extract_event_title("2026-08-20 14:30 项目评审会议", "meeting")
        self.assertIn("项目评审会议", title)
        self.assertNotIn("2026-08-20", title)
        self.assertNotIn("14:30", title)

    def test_extract_title_empty_fallback(self):
        self.assertEqual(self.cm._extract_event_title("2026-08-20", None), "待确认事项")


class TestCalendarManagerExtract(unittest.TestCase):
    """完整事件提取 + 存取回环测试"""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.cm = CalendarManager({"db_path": str(tmp / "test.db")})

    def test_extract_events(self):
        msgs = [
            {"content": "明天 14:00 开会讨论项目进度", "timestamp": "2026-08-13"},
            {"content": "周五前记得提交报告", "timestamp": "2026-08-13"},
        ]
        events = self.cm.extract_events_from_messages(msgs, "chat1")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event_type"], "meeting")
        self.assertEqual(events[0]["event_time"], "14:00")
        self.assertEqual(events[1]["event_type"], "deadline")

    def test_extract_no_events(self):
        msgs = [{"content": "今天天气不错", "timestamp": "2026-08-13"}]
        events = self.cm.extract_events_from_messages(msgs, "chat1")
        self.assertEqual(len(events), 0)

    def test_save_and_get_roundtrip(self):
        msgs = [{"content": "明天开会", "timestamp": "2026-08-13"}]
        self.cm.extract_events_from_messages(msgs, "chat1")
        saved = self.cm.get_events()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["event_type"], "meeting")
        self.assertEqual(saved[0]["chat_id"], "chat1")

    def test_delete_event(self):
        msgs = [{"content": "明天开会", "timestamp": "2026-08-13"}]
        self.cm.extract_events_from_messages(msgs, "chat1")
        saved = self.cm.get_events()
        self.cm.delete_event(saved[0]["id"])
        self.assertEqual(len(self.cm.get_events()), 0)


if __name__ == "__main__":
    unittest.main()
