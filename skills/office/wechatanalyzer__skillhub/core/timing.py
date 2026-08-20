"""对话时间特征（v2.3.0 新增）

把聊天时间信息转成预测器可用的“及时性”特征：
  - last_message_age_minutes: 最后一条消息距今多少分钟
  - urgency: immediate / soon / today / stale / unknown
  - time_of_day: morning / day / evening / night / unknown
  - day_type: weekday / weekend / unknown
  - burst: 最近几条消息是否属于密集连续对话
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class TimingInfo:
    """聊天时间特征快照。"""

    has_timestamps: bool = False
    last_message_age_minutes: Optional[float] = None
    urgency: str = "unknown"
    time_of_day: str = "unknown"
    day_type: str = "unknown"
    recent_gap_minutes: Optional[float] = None
    burst: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


def _time_of_day(dt: datetime) -> str:
    hour = dt.hour
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 18:
        return "day"
    if 18 <= hour < 23:
        return "evening"
    return "night"


def _day_type(dt: datetime) -> str:
    return "weekend" if dt.weekday() >= 5 else "weekday"


def analyze_timing(messages: List, now: Optional[datetime] = None) -> TimingInfo:
    """从消息列表提取时间特征。

    Args:
        messages: Message 对象列表（顺序随意，内部按 timestamp 排序）
        now: 当前时间，缺省使用 datetime.now()

    Returns:
        TimingInfo
    """
    now = now or datetime.now()
    timestamps = []
    for msg in messages or []:
        ts = getattr(msg, "timestamp", None)
        if isinstance(ts, datetime):
            timestamps.append(ts)
    if not timestamps:
        return TimingInfo()

    timestamps.sort()
    last_ts = timestamps[-1]
    age_minutes = max(0.0, (now - last_ts).total_seconds() / 60.0)

    if age_minutes <= 15:
        urgency = "immediate"
    elif age_minutes <= 120:
        urgency = "soon"
    elif age_minutes <= 1440:
        urgency = "today"
    else:
        urgency = "stale"

    recent_gap = None
    if len(timestamps) >= 2:
        gaps = [
            (timestamps[i] - timestamps[i - 1]).total_seconds() / 60.0
            for i in range(1, len(timestamps))
            if timestamps[i] > timestamps[i - 1]
        ]
        if gaps:
            # v2.5.0：gaps[-3:] 对长度 <3 的列表即全列表，原
            # len(gaps) >= 3 分支是冗余的（语义等价），简化。
            recent_gap = min(gaps[-3:])

    # 最近 3 条消息跨 30 分钟内，视为密集连续对话
    burst = False
    if len(timestamps) >= 3:
        burst = (timestamps[-1] - timestamps[-3]).total_seconds() / 60.0 <= 30

    return TimingInfo(
        has_timestamps=True,
        last_message_age_minutes=round(age_minutes, 1),
        urgency=urgency,
        time_of_day=_time_of_day(last_ts),
        day_type=_day_type(last_ts),
        recent_gap_minutes=round(recent_gap, 1) if recent_gap is not None else None,
        burst=burst,
    )
