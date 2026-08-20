#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTL 缓存装饰器（v5.0 新增）

按数据类型分级 TTL：
- 行情：5s（盘中）/ 60s（盘后）
- 财务快照：1h
- 财务报表：24h
- F10 股东/治理：7d

两层缓存：内存 LRU（热路径）+ 磁盘 JSON（跨进程持久化）。
磁盘路径复用 core/cache_manager.py 的 hashlib 命名约定。
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

# 缓存常量（秒）
TTL_QUOTE_INTRADAY = 5
TTL_QUOTE_CLOSED = 60
TTL_FINANCIAL_SNAPSHOT = 3600          # 1h
TTL_FINANCIAL_STATEMENT = 86400        # 24h（年报数据更新慢）
TTL_F10_GOVERNANCE = 7 * 86400         # 7d（股东/治理变化慢）
TTL_INDEX = 60

# 内存缓存（线程安全）
_MEM_CACHE: dict[str, tuple[float, Any]] = {}
_MEM_LOCK = threading.Lock()
_MEM_MAX_SIZE = 1000

# 磁盘缓存目录
_DISK_CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "v5"
_DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _disk_key(key: str) -> Path:
    """生成磁盘缓存文件路径（md5 哈希避免非法字符）"""
    h = hashlib.md5(key.encode("utf-8")).hexdigest()
    return _DISK_CACHE_DIR / f"{h}.json"


def _disk_get(key: str, ttl: int) -> Optional[Any]:
    """从磁盘读取缓存，过期返回 None 并删除"""
    fp = _disk_key(key)
    if not fp.exists():
        return None
    try:
        with fp.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if time.time() - payload.get("_ts", 0) > ttl:
            try:
                fp.unlink()
            except OSError:
                pass
            return None
        return payload.get("value")
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _disk_set(key: str, value: Any) -> None:
    """写入磁盘缓存"""
    fp = _disk_key(key)
    try:
        with fp.open("w", encoding="utf-8") as f:
            json.dump({"_ts": time.time(), "value": value}, f, ensure_ascii=False)
    except (OSError, TypeError, ValueError):
        pass  # 不可序列化值静默跳过


def _mem_get(key: str, ttl: int) -> Optional[Any]:
    """从内存读取缓存"""
    with _MEM_LOCK:
        ent = _MEM_CACHE.get(key)
        if ent is None:
            return None
        ts, val = ent
        if time.time() - ts > ttl:
            _MEM_CACHE.pop(key, None)
            return None
        return val


def _mem_set(key: str, value: Any) -> None:
    """写入内存缓存，超限时淘汰最旧条目"""
    with _MEM_LOCK:
        if len(_MEM_CACHE) >= _MEM_MAX_SIZE:
            # 淘汰 20% 最旧条目
            sorted_items = sorted(_MEM_CACHE.items(), key=lambda kv: kv[1][0])
            for k, _ in sorted_items[: max(1, _MEM_MAX_SIZE // 5)]:
                _MEM_CACHE.pop(k, None)
        _MEM_CACHE[key] = (time.time(), value)


def cached(ttl: int = TTL_FINANCIAL_SNAPSHOT,
           key_fn: Optional[Callable] = None,
           use_disk: bool = True,
           skip_cache: bool = False) -> Callable:
    """
    TTL 缓存装饰器。

    Args:
        ttl: 缓存有效期（秒）
        key_fn: 自定义缓存键生成函数 (args, kwargs) -> str；默认用函数名+参数
        use_disk: 是否启用磁盘缓存（默认 True）；纯行情类可关闭
        skip_cache: True 时完全跳过缓存（调试用）

    被装饰函数返回 None / 空 dict / 空 list / 含 "error" 键的 dict 时不缓存。
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if skip_cache:
                return fn(*args, **kwargs)

            # 生成缓存键
            if key_fn is not None:
                cache_key = f"{fn.__module__}.{fn.__name__}:{key_fn(*args, **kwargs)}"
            else:
                # 默认键：函数名 + 位置参数 + 关键参数
                key_parts = [str(a) for a in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{fn.__module__}.{fn.__name__}:{'|'.join(key_parts)}"

            # 内存层
            mem_val = _mem_get(cache_key, ttl)
            if mem_val is not None:
                return mem_val

            # 磁盘层
            if use_disk:
                disk_val = _disk_get(cache_key, ttl)
                if disk_val is not None:
                    _mem_set(cache_key, disk_val)
                    return disk_val

            # 实际调用
            result = fn(*args, **kwargs)

            # 失败结果不缓存（让下次重试）
            if result is None:
                return result
            if isinstance(result, dict) and (not result or "error" in result):
                return result
            if isinstance(result, (list, tuple)) and len(result) == 0:
                return result

            # 写入双层缓存
            _mem_set(cache_key, result)
            if use_disk:
                _disk_set(cache_key, result)

            return result

        # 暴露手动清除接口
        wrapper.cache_clear = lambda: (_MEM_CACHE.clear(),
                                       [_disk_key(k).unlink(missing_ok=True)
                                        for k in list(_MEM_CACHE)])
        return wrapper
    return decorator


def clear_all_cache() -> int:
    """清除全部缓存，返回清除的磁盘文件数"""
    with _MEM_LOCK:
        _MEM_CACHE.clear()
    count = 0
    for fp in _DISK_CACHE_DIR.glob("*.json"):
        try:
            fp.unlink()
            count += 1
        except OSError:
            pass
    return count


def cache_stats() -> dict:
    """返回缓存统计信息"""
    with _MEM_LOCK:
        mem_size = len(_MEM_CACHE)
    disk_size = sum(1 for _ in _DISK_CACHE_DIR.glob("*.json"))
    return {
        "memory_entries": mem_size,
        "memory_max": _MEM_MAX_SIZE,
        "disk_entries": disk_size,
        "disk_dir": str(_DISK_CACHE_DIR),
    }
