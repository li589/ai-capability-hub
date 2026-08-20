"""core.message 单元测试"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message, MessageType, SenderRole, messages_from_legacy


class TestMessage(unittest.TestCase):
    """Message 数据模型测试"""

    def test_create_basic(self):
        msg = Message(sender="self", content="你好")
        self.assertEqual(msg.sender, "self")
        self.assertEqual(msg.content, "你好")
        self.assertEqual(msg.message_type, MessageType.TEXT)
        self.assertIsNone(msg.timestamp)

    def test_create_with_timestamp(self):
        ts = datetime(2024, 1, 1, 12, 30, 0)
        msg = Message(sender="other", content="hello", timestamp=ts)
        self.assertEqual(msg.timestamp, ts)
        self.assertTrue(msg.is_other())
        self.assertFalse(msg.is_self())

    def test_is_self_other(self):
        self_msg = Message(sender="self", content="x")
        other_msg = Message(sender="other", content="x")
        self.assertTrue(self_msg.is_self())
        self.assertFalse(self_msg.is_other())
        self.assertTrue(other_msg.is_other())
        self.assertFalse(other_msg.is_self())

    def test_has_content(self):
        self.assertTrue(Message(sender="self", content="x").has_content())
        self.assertFalse(Message(sender="self", content="").has_content())
        self.assertFalse(Message(sender="self", content="   ").has_content())

    def test_to_dict_from_dict(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        original = Message(
            sender="other",
            content="测试",
            timestamp=ts,
            message_type=MessageType.TEXT,
            metadata={"key": "value"},
        )
        d = original.to_dict()
        restored = Message.from_dict(d)
        self.assertEqual(restored.sender, "other")
        self.assertEqual(restored.content, "测试")
        self.assertEqual(restored.timestamp, ts)
        self.assertEqual(restored.metadata, {"key": "value"})

    def test_from_dict_string_timestamp(self):
        d = {
            "sender": "self",
            "content": "x",
            "timestamp": "2024-01-01T12:30:00",
        }
        msg = Message.from_dict(d)
        self.assertIsNotNone(msg.timestamp)
        self.assertEqual(msg.timestamp.year, 2024)

    def test_from_dict_invalid_timestamp(self):
        d = {
            "sender": "self",
            "content": "x",
            "timestamp": "invalid",
        }
        msg = Message.from_dict(d)
        self.assertIsNone(msg.timestamp)

    def test_from_legacy_dict(self):
        legacy = [
            {"sender": "self", "content": "你好"},
            {"sender": "other", "content": "hello"},
        ]
        msgs = messages_from_legacy(legacy)
        self.assertEqual(len(msgs), 2)
        self.assertTrue(all(isinstance(m, Message) for m in msgs))

    def test_from_legacy_already_message(self):
        msg = Message(sender="self", content="x")
        msgs = messages_from_legacy([msg])
        self.assertEqual(len(msgs), 1)
        self.assertIs(msgs[0], msg)

    def test_from_legacy_invalid_type(self):
        with self.assertRaises(TypeError):
            messages_from_legacy([123])

    # ----------------------------------------------------------------
    # v2.5.0：旧生产者的 msg_type 键名兼容
    # ----------------------------------------------------------------
    def test_from_dict_legacy_msg_type_key(self):
        """v2.5.0 bugfix：旧 dict 用 'msg_type' 键，之前类型全丢（image→text）"""
        d = {"sender": "self", "content": "x", "msg_type": "image"}
        msg = Message.from_dict(d)
        self.assertEqual(msg.message_type, MessageType.IMAGE)

    def test_from_dict_canonical_key_wins(self):
        """规范键 'message_type' 优先于 'msg_type'"""
        d = {"sender": "self", "content": "x", "msg_type": "image",
             "message_type": "voice"}
        msg = Message.from_dict(d)
        self.assertEqual(msg.message_type, MessageType.VOICE)

    def test_from_dict_unknown_type_falls_back_text(self):
        d = {"sender": "self", "content": "x", "msg_type": "weird"}
        msg = Message.from_dict(d)
        self.assertEqual(msg.message_type, MessageType.TEXT)

    def test_message_types(self):
        text_msg = Message(sender="self", content="x", message_type=MessageType.TEXT)
        image_msg = Message(sender="self", content="x", message_type=MessageType.IMAGE)
        self.assertTrue(text_msg.is_text())
        self.assertFalse(image_msg.is_text())


class TestSenderRole(unittest.TestCase):
    """SenderRole 枚举测试"""

    def test_values(self):
        self.assertEqual(SenderRole.SELF.value, "self")
        self.assertEqual(SenderRole.OTHER.value, "other")
        self.assertEqual(SenderRole.UNKNOWN.value, "unknown")


class TestMessageType(unittest.TestCase):
    """MessageType 枚举测试"""

    def test_values(self):
        self.assertEqual(MessageType.TEXT.value, "text")
        self.assertEqual(MessageType.IMAGE.value, "image")
        self.assertEqual(MessageType.VOICE.value, "voice")


if __name__ == "__main__":
    unittest.main()
