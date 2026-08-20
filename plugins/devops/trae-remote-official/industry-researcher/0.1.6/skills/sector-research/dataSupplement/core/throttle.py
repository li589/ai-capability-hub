# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 核心基础设施 · 请求限流器
===============================================

功能概览:
  - Throttle: 可配置最小间隔 + 随机抖动的令牌桶式限流器
  - throttled_get: 自动按域名查找限流策略并执行节流后的 GET 请求
  - 全局域名限流注册表: 内置常见财经数据源的限流配置

设计目标:
  - 防止高频请求触发源站反爬 / IP 封禁
  - 支持细粒度的域名级别差异化限流
  - 线程安全

零外部依赖 — 仅使用 Python 标准库。
"""

from __future__ import annotations

import random
import threading
import time
import urllib.parse
from typing import Any, Dict, Optional

from .client import HttpResponse, http_get

__all__ = [
    "Throttle",
    "throttled_get",
    "get_throttle_for_domain",
    "register_domain_throttle",
    "DOMAIN_THROTTLE_REGISTRY",
]

# ---------------------------------------------------------------------------
# Throttle 限流器
# ---------------------------------------------------------------------------


class Throttle:
    """基于最小时间间隔的限流器。

    每次调用 wait() 会确保距离上次放行至少经过 min_interval 秒,
    并叠加 [0, jitter] 的随机延迟以打散并发请求。

    Args:
        min_interval: 两次请求之间的最小间隔(秒)。
        jitter: 随机抖动上限(秒), 实际延迟为 [0, jitter] 均匀分布。

    示例:
        >>> t = Throttle(min_interval=1.0, jitter=0.2)
        >>> t.wait()  # 首次不等待
        >>> t.wait()  # 至少等待 1.0 ~ 1.2 秒
    """

    def __init__(self, min_interval: float = 0.3, jitter: float = 0.1):
        self.min_interval: float = min_interval
        self.jitter: float = jitter
        self._last_time: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """阻塞直到满足限流间隔要求。线程安全。"""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_time
            required = self.min_interval + random.uniform(0, self.jitter)

            if elapsed < required:
                sleep_time = required - elapsed
                time.sleep(sleep_time)

            self._last_time = time.time()

    def reset(self) -> None:
        """重置限流器状态, 下次调用 wait() 将立即通过。"""
        with self._lock:
            self._last_time = 0.0

    def __repr__(self) -> str:
        return (
            f"Throttle(min_interval={self.min_interval}, "
            f"jitter={self.jitter})"
        )


# ---------------------------------------------------------------------------
# 全局域名限流注册表
# ---------------------------------------------------------------------------

# 键: 域名关键词(会通过 `in` 匹配)  值: Throttle 实例
# 越具体的条目应放在前面以优先匹配
DOMAIN_THROTTLE_REGISTRY: Dict[str, Throttle] = {
    # 东方财富 — 限流较严, 间隔 1.2s
    "eastmoney": Throttle(min_interval=1.2, jitter=0.3),
    # 同花顺 — 间隔 1.0s
    "10jqka": Throttle(min_interval=1.0, jitter=0.2),
    "mairui": Throttle(min_interval=1.0, jitter=0.2),
    # 新浪财经
    "sina": Throttle(min_interval=0.5, jitter=0.1),
    # 腾讯股票
    "tencent": Throttle(min_interval=0.4, jitter=0.1),
    "qq.com": Throttle(min_interval=0.4, jitter=0.1),
    # 百度股市通
    "baidu": Throttle(min_interval=0.5, jitter=0.1),
    # 巨潮资讯
    "cninfo": Throttle(min_interval=0.8, jitter=0.2),
    # 通达信
    "tdx": Throttle(min_interval=0.3, jitter=0.1),
    "mootdx": Throttle(min_interval=0.3, jitter=0.1),
}

# 默认限流器(匹配不到特定域名时使用)
_DEFAULT_THROTTLE = Throttle(min_interval=0.3, jitter=0.1)


def _extract_domain(url: str) -> str:
    """从 URL 中提取域名部分(小写)。"""
    parsed = urllib.parse.urlparse(url)
    return (parsed.hostname or "").lower()


def get_throttle_for_domain(url: str) -> Throttle:
    """根据 URL 域名查找对应的限流器。

    匹配逻辑: 遍历注册表的 key, 如果 key 出现在域名中则命中。
    未命中返回默认限流器(0.3s)。

    Args:
        url: 请求目标 URL。

    Returns:
        匹配到的 Throttle 实例。
    """
    domain = _extract_domain(url)
    for keyword, throttle in DOMAIN_THROTTLE_REGISTRY.items():
        if keyword in domain:
            return throttle
    return _DEFAULT_THROTTLE


def register_domain_throttle(
    keyword: str, min_interval: float = 0.5, jitter: float = 0.1
) -> Throttle:
    """向全局注册表添加/更新域名限流配置。

    Args:
        keyword: 域名匹配关键词(如 "eastmoney")。
        min_interval: 最小请求间隔(秒)。
        jitter: 随机抖动上限(秒)。

    Returns:
        新创建的 Throttle 实例。
    """
    throttle = Throttle(min_interval=min_interval, jitter=jitter)
    DOMAIN_THROTTLE_REGISTRY[keyword] = throttle
    return throttle


# ---------------------------------------------------------------------------
# 公开 API — 带限流的请求函数
# ---------------------------------------------------------------------------


def throttled_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    encoding: str = "utf-8",
) -> HttpResponse:
    """发送带自动限流的 HTTP GET 请求。

    根据目标 URL 的域名自动查找对应的限流策略, 在发送请求前
    执行必要的等待, 确保不超过配置的频率限制。

    Args:
        url: 目标 URL。
        params: 查询参数字典。
        headers: 自定义请求头。
        timeout: 超时时间(秒)。
        encoding: 响应体编码。

    Returns:
        HttpResponse 实例。

    示例:
        >>> resp = throttled_get("https://push2.eastmoney.com/api/qt/stock/get",
        ...                      params={"secid": "1.600519"})
        >>> data = resp.json()
    """
    throttle = get_throttle_for_domain(url)
    throttle.wait()
    return http_get(url, params=params, headers=headers, timeout=timeout, encoding=encoding)
