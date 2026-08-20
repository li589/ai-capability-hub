#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发批量数据获取器（v5.0 新增）

用 ThreadPoolExecutor 并发拉取多只股票/基金的数据，替代原有顺序 + sleep 的低效模式。
保留 sleep 节流以避免被数据源限流。
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Iterable, List, TypeVar

T = TypeVar("T")


def fetch_batch_concurrent(
    fetch_fn: Callable[..., T],
    codes: Iterable[str],
    max_workers: int = 5,
    sleep_between: float = 0.2,
    timeout: float = 30.0,
    **fetch_kwargs,
) -> Dict[str, T]:
    """
    并发批量调用 fetch_fn(code, **fetch_kwargs)。

    Args:
        fetch_fn: 单代码获取函数，签名为 fn(code, **kwargs) -> result
        codes: 代码迭代器
        max_workers: 最大并发数（默认 5，避免被限流）
        sleep_between: 每个任务提交后的节流休眠（秒）
        timeout: 单任务超时（秒）
        **fetch_kwargs: 透传给 fetch_fn 的额外参数

    Returns:
        Dict[code, result]；失败代码不包含在结果中（或 value=None，取决于 fetch_fn 行为）
    """
    codes_list = [str(c).zfill(6) if len(str(c)) < 6 else str(c) for c in codes]
    if not codes_list:
        return {}

    results: Dict[str, T] = {}

    # 小批量直接顺序执行，避免线程开销
    if len(codes_list) <= 2:
        for code in codes_list:
            try:
                results[code] = fetch_fn(code, **fetch_kwargs)
            except Exception:
                continue
            if sleep_between > 0:
                time.sleep(sleep_between)
        return results

    with ThreadPoolExecutor(max_workers=min(max_workers, len(codes_list))) as executor:
        future_to_code: Dict = {}
        for code in codes_list:
            future = executor.submit(fetch_fn, code, **fetch_kwargs)
            future_to_code[future] = code
            if sleep_between > 0:
                time.sleep(sleep_between)  # 提交侧节流，平滑请求

        for future in as_completed(future_to_code, timeout=timeout):
            code = future_to_code[future]
            try:
                results[code] = future.result(timeout=timeout)
            except Exception:
                # 单个失败不影响整体，跳过
                continue

    return results


def fetch_batch_sequential(
    fetch_fn: Callable[..., T],
    codes: Iterable[str],
    sleep_between: float = 0.2,
    **fetch_kwargs,
) -> Dict[str, T]:
    """
    顺序批量获取（保留作为 fallback / 调试用）。
    """
    results: Dict[str, T] = {}
    for code in codes:
        code = str(code)
        try:
            results[code] = fetch_fn(code, **fetch_kwargs)
        except Exception:
            continue
        if sleep_between > 0:
            time.sleep(sleep_between)
    return results
