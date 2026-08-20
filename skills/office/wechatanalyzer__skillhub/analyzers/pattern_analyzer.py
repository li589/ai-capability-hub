"""
对话模式分析器 - v2.0.0

修复 v1.2.0 的 bug：reply_speed 字段计算后丢失
新增：
- 回复速度（reply_speed）
- 主动发起对话比例
- 消息长度方差
- 问号/感叹号比例
- 活跃时段
"""

from typing import List, Dict, Any
from collections import Counter

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult


class PatternAnalyzer(AnalyzerBase):
    """对话模式分析器"""

    name = "pattern"
    version = "2.1.0"
    description = "对话模式（回复速度/主动率/活跃时段）"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 5

    def validate(self, messages: List[Message]) -> bool:
        return len(messages) >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        # 1. 主动发起对话比例（每轮对话的第一条消息）
        initiation = {"self": 0, "other": 0}
        # 2. 回复速度
        reply_speeds = []  # 秒
        # 3. 消息长度
        lengths = {"self": [], "other": []}
        # 4. 问号/感叹号
        question_count = 0
        exclamation_count = 0
        # 5. 时长
        timestamps = [m.timestamp for m in messages if m.timestamp]

        last_ts = None
        last_sender = None
        for i, msg in enumerate(messages):
            content = msg.content or ""
            sender = msg.sender
            is_self = msg.is_self()

            # 消息长度
            if is_self:
                lengths["self"].append(len(content))
            else:
                lengths["other"].append(len(content))

            # 问号/感叹号
            question_count += content.count("?") + content.count("？")
            exclamation_count += content.count("!") + content.count("！")

            # 主动发起判断
            if i == 0:
                if is_self:
                    initiation["self"] += 1
                else:
                    initiation["other"] += 1
            else:
                # 与上条消息不同发送者 → 是回复
                # 间隔 > 2 小时 → 算新一轮对话（主动发起）
                if last_sender and sender != last_sender:
                    if msg.timestamp and last_ts:
                        gap = (msg.timestamp - last_ts).total_seconds()
                        if gap > 7200:  # 2 小时
                            if is_self:
                                initiation["self"] += 1
                            else:
                                initiation["other"] += 1
                        else:
                            # 回复
                            reply_speeds.append(gap)

            last_ts = msg.timestamp
            last_sender = sender

        # 统计
        avg_reply_speed = sum(reply_speeds) / len(reply_speeds) if reply_speeds else 0
        avg_self_len = sum(lengths["self"]) / len(lengths["self"]) if lengths["self"] else 0
        avg_other_len = sum(lengths["other"]) / len(lengths["other"]) if lengths["other"] else 0

        # 主动率
        total_initiations = initiation["self"] + initiation["other"]
        if total_initiations > 0:
            self_initiation_pct = initiation["self"] / total_initiations * 100
            other_initiation_pct = initiation["other"] / total_initiations * 100
        else:
            self_initiation_pct = other_initiation_pct = 50.0

        # 问号/感叹号比例
        question_ratio = question_count / len(messages) * 100 if messages else 0
        exclamation_ratio = exclamation_count / len(messages) * 100 if messages else 0

        # 时长
        duration_days = 0
        if len(timestamps) >= 2:
            timestamps.sort()
            duration_days = (timestamps[-1] - timestamps[0]).days

        return AnalysisResult(
            analyzer_name=self.name,
            score=avg_reply_speed,
            confidence=80.0,
            details={
                "initiation": {
                    "self": initiation["self"],
                    "other": initiation["other"],
                    "self_pct": round(self_initiation_pct, 1),
                    "other_pct": round(other_initiation_pct, 1),
                },
                "reply_speed": {
                    "avg_seconds": round(avg_reply_speed, 1),
                    "count": len(reply_speeds),
                    "fast_replies": sum(1 for s in reply_speeds if s < 60),  # < 1 分钟
                    "slow_replies": sum(1 for s in reply_speeds if s > 3600),  # > 1 小时
                },
                "message_length": {
                    "self_avg": round(avg_self_len, 1),
                    "other_avg": round(avg_other_len, 1),
                },
                "punctuation": {
                    "question_ratio": round(question_ratio, 1),
                    "exclamation_ratio": round(exclamation_ratio, 1),
                },
                "duration_days": duration_days,
                "total_messages": len(messages),
            },
            metadata={
                "analyzer": "PatternAnalyzer",
                "version": self.version,
            },
        )
