# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 核心基础设施 · 内存缓存
=============================================

功能概览:
  - cache_get / cache_set: 带 TTL 的键值缓存操作
  - make_key: 从多个参数生成规范化缓存键
  - 预定义 TTL 常量: 按数据类型提供合理的默认过期时间
  - 自动过期清理: 读取时惰性清理 + 周期性全量清理

设计目标:
  - 减少对数据源的重复请求, 降低被限流/封禁风险
  - 对实时性要求不同的数据采用差异化 TTL
  - 线程安全, 适合多线程环境下使用

零外部依赖 — 仅使用 Python 标准库。
"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Optional, Tuple

__all__ = [
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear",
    "make_key",
    "TTL_QUOTE",
    "TTL_KLINE",
    "TTL_FUNDAMENTAL",
    "TTL_NEWS",
    "TTL_FINANCE",
    "TTL_REPORT",
]

# ---------------------------------------------------------------------------
# 默认 TTL 常量(秒)
# ---------------------------------------------------------------------------

TTL_QUOTE: int = 30
"""实时行情类数据 TTL: 30 秒。适用于当前价、涨跌幅、成交量等。"""

TTL_KLINE: int = 300
"""K 线数据 TTL: 5 分钟。适用于日 K / 周 K / 月 K 历史数据。"""

TTL_FUNDAMENTAL: int = 3600
"""基本面数据 TTL: 1 小时。适用于财务报表、估值指标等。"""

TTL_NEWS: int = 120
"""新闻资讯 TTL: 2 分钟。适用于新闻列表、公告等。"""

TTL_FINANCE: int = 3600
"""财务数据 TTL: 1 小时。适用于三大报表、财务指标等。"""

TTL_REPORT: int = 1800
"""研报数据 TTL: 30 分钟。适用于研报列表、评级等。"""

# ---------------------------------------------------------------------------
# 缓存存储
# ---------------------------------------------------------------------------

# 存储结构: {key: (value, expire_timestamp)}
_store: dict[str, Tuple[Any, float]] = {}
_lock = threading.Lock()

# 清理阈值: 当存储条目超过此数量时触发全量清理
_CLEANUP_THRESHOLD = 5000
_last_cleanup_time: float = 0.0
_CLEANUP_INTERVAL = 60.0  # 最多每 60 秒执行一次全量清理


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _is_expired(expire_at: float) -> bool:
    """判断缓存条目是否已过期。"""
    return time.time() > expire_at


def _cleanup_expired() -> None:
    """清理所有已过期的缓存条目(需在持锁状态下调用)。"""
    global _last_cleanup_time
    now = time.time()

    # 限制清理频率
    if now - _last_cleanup_time < _CLEANUP_INTERVAL:
        return

    expired_keys = [k for k, (_, exp) in _store.items() if now > exp]
    for k in expired_keys:
        del _store[k]

    _last_cleanup_time = now


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def make_key(*args: Any) -> str:
    """从多个参数生成规范化的缓存键。

    将所有参数转为字符串后拼接, 计算 MD5 摘要作为短键。
    同时保留可读前缀以便调试。

    Args:
        *args: 任意数量的参数, 通常包括函数名、股票代码、参数等。

    Returns:
        格式为 "{前缀}:{md5[:12]}" 的缓存键。

    示例:
        >>> make_key("quote", "600519", "daily")
        'quote_600519_daily:a1b2c3d4e5f6'
    """
    parts = [str(a) for a in args if a is not None]
    readable = "_".join(parts)[:60]  # 可读前缀, 截断到 60 字符
    digest = hashlib.md5(readable.encode("utf-8")).hexdigest()[:12]
    return f"{readable}:{digest}"


def cache_get(key: str) -> Optional[Any]:
    """从缓存中获取数据。

    如果 key 存在且未过期, 返回缓存的值; 否则返回 None。
    过期条目会被惰性删除。

    Args:
        key: 缓存键(建议使用 make_key 生成)。

    Returns:
        缓存的值, 或 None(未命中/已过期)。
    """
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None

        value, expire_at = entry
        if _is_expired(expire_at):
            del _store[key]
            return None

        return value


def cache_set(key: str, value: Any, ttl: int = TTL_QUOTE) -> None:
    """向缓存中写入数据。

    Args:
        key: 缓存键。
        value: 要缓存的值(任意 Python 对象)。
        ttl: 生存时间(秒), 默认使用 TTL_QUOTE (30s)。

    示例:
        >>> cache_set(make_key("quote", "600519"), price_data, ttl=TTL_QUOTE)
    """
    expire_at = time.time() + ttl
    with _lock:
        _store[key] = (value, expire_at)

        # 当存储量过大时触发清理
        if len(_store) > _CLEANUP_THRESHOLD:
            _cleanup_expired()


def cache_delete(key: str) -> bool:
    """删除指定缓存条目。

    Args:
        key: 缓存键。

    Returns:
        True 如果 key 存在且被删除, False 如果 key 不存在。
    """
    with _lock:
        if key in _store:
            del _store[key]
            return True
        return False


def cache_clear() -> int:
    """清空所有缓存。

    Returns:
        被清除的条目数量。
    """
    with _lock:
        count = len(_store)
        _store.clear()
        return count


def cache_stats() -> dict:
    """获取缓存统计信息(用于调试/监控)。

    Returns:
        包含 total_entries, expired_entries, active_entries 的字典。
    """
    with _lock:
        now = time.time()
        total = len(_store)
        expired = sum(1 for _, (_, exp) in _store.items() if now > exp)
        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
        }
