"""
统一消息数据模型

v2.0.0 引入 dataclass 风格的 Message，替代 v1.2.0 中的 dict 形式。
所有分析器、预测器都应使用此模型以保证类型一致。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    EMOJI = "emoji"
    SYSTEM = "system"  # 系统消息（如"你已添加对方为好友"）


class SenderRole(str, Enum):
    """发送者角色"""
    SELF = "self"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass
class Message:
    """统一消息模型

    字段:
        sender: 发送者标识（'self' / 'other' / 群昵称）
        content: 消息文本内容
        timestamp: 消息时间
        message_type: 消息类型
        raw: 原始字符串（用于调试和回溯）
        metadata: 附加元数据（图片路径、语音时长等）
    """
    sender: str
    content: str
    timestamp: Optional[datetime] = None
    message_type: MessageType = MessageType.TEXT
    raw: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转字典（用于 JSON 序列化）"""
        return {
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_type": self.message_type.value,
            "raw": self.raw,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典构造"""
        ts = data.get("timestamp")
        if isinstance(ts, str) and ts:
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                ts = None
        elif not isinstance(ts, datetime):
            ts = None

        # v2.5.0：兼容旧生产者（file_importer/data_manager）的 "msg_type" 键。
        # 之前只读 "message_type"，旧 dict 全部丢失类型（image/voice/system
        # 被当作 text），导致下游非文本过滤失效。
        msg_type = data.get("message_type", data.get("msg_type", "text"))
        if isinstance(msg_type, str):
            try:
                msg_type = MessageType(msg_type)
            except ValueError:
                msg_type = MessageType.TEXT

        return cls(
            sender=data.get("sender", "unknown"),
            content=data.get("content", ""),
            timestamp=ts,
            message_type=msg_type,
            raw=data.get("raw", ""),
            metadata=data.get("metadata", {}),
        )

    def is_self(self) -> bool:
        """判断是否自己发送的消息

        支持：
        - 显式 "self" 标识
        - "我" 开头
        - 各种自我标识
        """
        if self.sender == SenderRole.SELF.value:
            return True
        if self.sender in {"我", "me", "myself", "I"}:
            return True
        return False

    def is_other(self) -> bool:
        """判断是否对方发送的消息

        任何非 self 标识都视为 other（包括真实姓名、群昵称等）
        """
        return not self.is_self() and self.sender != SenderRole.UNKNOWN.value

    def is_text(self) -> bool:
        return self.message_type == MessageType.TEXT

    def has_content(self) -> bool:
        return bool(self.content and self.content.strip())


def messages_from_legacy(legacy_list: list) -> list:
    """从 v1.2.0 的 dict 列表转换为 Message 列表

    用于向后兼容 v1.2.0 的 data_manager 输出。
    """
    result = []
    for item in legacy_list:
        if isinstance(item, Message):
            result.append(item)
        elif isinstance(item, dict):
            result.append(Message.from_dict(item))
        else:
            raise TypeError(f"Unsupported message type: {type(item)}")
    return result
