"""scripts.data_manager 单元测试（v2.3.0 补全）

覆盖：
- 文本解析（[时间]发送者/竖线分隔/发送者无时间/纯文本短消息/垃圾行）
- 聊天记录存储与读取（save_chat / get_chat_list / get_messages）
- 分析结果存取（save_analysis / get_analysis / get_latest_analysis）
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.data_manager import DataManager


class TestDataManagerParse(unittest.TestCase):
    """文本解析测试"""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.dm = DataManager({"db_path": str(tmp / "test.db")})

    def test_parse_line_format1_timestamp(self):
        msg = self.dm._parse_line("[2024-01-01 12:30:00] 张三: 你好")
        self.assertEqual(msg["sender"], "张三")
        self.assertEqual(msg["content"], "你好")
        self.assertEqual(msg["timestamp"], "2024-01-01 12:30:00")

    def test_parse_line_format2_pipe(self):
        msg = self.dm._parse_line("2024-01-01 12:30:00 | 张三 | 你好")
        self.assertEqual(msg["sender"], "张三")
        self.assertEqual(msg["content"], "你好")

    def test_parse_line_format3_no_time(self):
        msg = self.dm._parse_line("张三: 你好")
        self.assertEqual(msg["sender"], "张三")
        self.assertEqual(msg["content"], "你好")
        self.assertIn("timestamp", msg)

    def test_parse_line_format4_bare(self):
        # v2.5.0：无发送者的裸文本按设计约定视为自己的消息（此前误标为 other）
        msg = self.dm._parse_line("在吗")
        self.assertEqual(msg["sender"], "self")
        self.assertEqual(msg["content"], "在吗")

    def test_parse_line_timestamp_only_skipped(self):
        # v2.5.0：纯时间戳行（导出文件分隔行）不是消息
        self.assertIsNone(self.dm._parse_line("2024-01-01 12:30:00"))

    def test_parse_line_separator_skipped(self):
        # v2.5.0：分隔线不是消息
        self.assertIsNone(self.dm._parse_line("----------------"))
        self.assertIsNone(self.dm._parse_line("======"))

    def test_parse_line_colon_variant(self):
        msg = self.dm._parse_line("李四：你好")
        self.assertEqual(msg["sender"], "李四")
        self.assertEqual(msg["content"], "你好")

    def test_parse_line_garbage(self):
        # 空字符串无匹配格式（空白行由 parse_text_input 层跳过）
        self.assertIsNone(self.dm._parse_line(""))

    def test_parse_text_input_multiline(self):
        text = (
            "[2024-01-01 12:30:00] 张三: 你好\n"
            "2024-01-01 12:31:00 | 李四 | 嗨\n"
            "张三: 忙吗\n"
            "在吗"
        )
        msgs = self.dm.parse_text_input(text)
        self.assertEqual(len(msgs), 4)
        self.assertEqual(msgs[0]["sender"], "张三")

    def test_parse_text_input_blank(self):
        self.assertEqual(self.dm.parse_text_input("  \n\n"), [])


class TestDataManagerStorage(unittest.TestCase):
    """存储/读取测试"""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.dm = DataManager({"db_path": str(tmp / "test.db")})

    def test_save_get_chat(self):
        msgs = [{"sender": "张三", "content": "你好", "timestamp": "2024-01-01 12:00:00"}]
        chat_id = self.dm.save_chat("聊天A", msgs)
        self.assertTrue(chat_id)

        chat_list = self.dm.get_chat_list()
        self.assertEqual(len(chat_list), 1)
        self.assertEqual(chat_list[0]["name"], "聊天A")
        self.assertEqual(chat_list[0]["message_count"], 1)

        got = self.dm.get_messages(chat_id)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["sender"], "张三")
        self.assertEqual(got[0]["content"], "你好")

    def test_save_multiple_chats(self):
        self.dm.save_chat("A", [{"sender": "x", "content": "1", "timestamp": "t"}])
        self.dm.save_chat("B", [{"sender": "x", "content": "2", "timestamp": "t"}])
        self.assertEqual(len(self.dm.get_chat_list()), 2)

    def test_get_messages_empty_chat(self):
        chat_id = self.dm.save_chat("空", [])
        self.assertEqual(self.dm.get_messages(chat_id), [])

    def test_save_get_analysis(self):
        results = {"positive": 80.0, "negative": 20.0}
        chat_id = self.dm.save_analysis(results)
        self.assertTrue(chat_id)

        got = self.dm.get_analysis(chat_id)
        self.assertEqual(got["positive"], 80.0)
        self.assertEqual(got["negative"], 20.0)

    def test_save_analysis_with_chat_id(self):
        self.dm.save_analysis({"v": 1}, chat_id="chat-1")
        got = self.dm.get_analysis("chat-1")
        self.assertEqual(got["v"], 1)
        self.assertEqual(got["chat_id"], "chat-1")

    def test_latest_analysis(self):
        self.dm.save_analysis({"v": 1})
        self.dm.save_analysis({"v": 2})
        latest = self.dm.get_latest_analysis()
        self.assertEqual(latest["v"], 2)

    def test_get_analysis_missing(self):
        self.assertIsNone(self.dm.get_analysis("nonexistent"))

    def test_results_injected_chat_id(self):
        results = {"positive": 50.0}
        chat_id = self.dm.save_analysis(results)
        # 实现用副本注入 chat_id，不污染调用方字典
        self.assertIsNone(results.get("chat_id"))
        got = self.dm.get_analysis(chat_id)
        self.assertEqual(got["chat_id"], chat_id)


if __name__ == "__main__":
    unittest.main()
