# -*- coding: utf-8 -*-
"""
数据源管理器 - 多源冗余 + 自动降级 + 健康检查

设计原则：
1. 多数据源冗余：主源失败自动切换备用源
2. 指数退避重试：网络错误自动重试，避免频繁请求
3. 健康检查：定期检测数据源可用性
4. 降级策略：优先返回缓存数据，而非直接报错
5. 统一接口：对上层透明，无需关心底层数据源

数据源优先级：
- 实时行情：腾讯财经 > 新浪财经 > 东方财富
- 历史K线：腾讯财经 > 新浪财经 > 本地缓存
- 财务数据：东方财富 > 同花顺 > 缓存快照
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class SourceStatus(Enum):
    """数据源状态"""
    HEALTHY = "healthy"          # 健康
    DEGRADED = "degraded"        # 降级（响应慢或部分失败）
    UNAVAILABLE = "unavailable"  # 不可用
    UNKNOWN = "unknown"          # 未知（未检测）


@dataclass
class SourceHealth:
    """数据源健康状态"""
    name: str
    status: SourceStatus = SourceStatus.UNKNOWN
    last_success: float = 0.0      # 最后成功时间戳
    last_failure: float = 0.0      # 最后失败时间戳
    success_count: int = 0         # 成功次数
    failure_count: int = 0         # 失败次数
    avg_latency: float = 0.0       # 平均响应时间（秒）
    error_message: str = ""        # 最后错误信息

    @property
    def reliability(self) -> float:
        """可靠性评分（0-1）"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5  # 未知状态
        return self.success_count / total

    @property
    def is_usable(self) -> bool:
        """是否可用"""
        return self.status in (SourceStatus.HEALTHY, SourceStatus.DEGRADED)


@dataclass
class DataSource:
    """数据源配置"""
    name: str
    fetch_func: Callable          # 获取数据的函数
    priority: int = 1             # 优先级（数字越小优先级越高）
    timeout: float = 10.0         # 超时时间（秒）
    max_retries: int = 2          # 最大重试次数
    cache_ttl: int = 60           # 缓存TTL（秒）
    health: SourceHealth = field(default_factory=lambda: SourceHealth(name=""))


class DataSourceManager:
    """
    数据源管理器

    使用示例：
    ```python
    manager = DataSourceManager()

    # 注册数据源
    manager.register_source("realtime", DataSource(
        name="tencent_realtime",
        fetch_func=tencent_fetch_realtime,
        priority=1,
        timeout=8.0,
    ))

    manager.register_source("realtime", DataSource(
        name="sina_realtime",
        fetch_func=sina_fetch_realtime,
        priority=2,
        timeout=10.0,
    ))

    # 获取数据（自动降级）
    data = manager.fetch("realtime", codes=["600519", "000858"])
    ```
    """

    def __init__(self):
        self._sources: Dict[str, List[DataSource]] = {}  # category -> sources
        self._cache: Dict[str, tuple] = {}  # key -> (timestamp, data)
        self._health_check_interval = 300  # 5分钟检查一次
        self._last_health_check = 0.0

    def register_source(self, category: str, source: DataSource) -> None:
        """
        注册数据源

        Args:
            category: 数据类别（如 "realtime", "history", "fundamental"）
            source: 数据源配置
        """
        if category not in self._sources:
            self._sources[category] = []

        source.health.name = source.name
        self._sources[category].append(source)
        # 按优先级排序
        self._sources[category].sort(key=lambda s: s.priority)

        logger.info(f"Registered data source: {source.name} for {category}")

    def fetch(self, category: str, use_cache: bool = True, **kwargs) -> Optional[Any]:
        """
        获取数据（自动降级）

        Args:
            category: 数据类别
            use_cache: 是否使用缓存
            **kwargs: 传递给数据源函数的参数

        Returns:
            数据或None（所有源都失败时）
        """
        if category not in self._sources or not self._sources[category]:
            logger.error(f"No data sources registered for category: {category}")
            return None

        # 生成缓存键
        cache_key = f"{category}:{hash(frozenset(kwargs.items()))}"

        # 检查缓存
        if use_cache:
            cached = self._get_from_cache(cache_key, category)
            if cached is not None:
                logger.debug(f"Cache hit for {category}")
                return cached

        # 尝试每个数据源
        last_error = None
        for source in self._sources[category]:
            if not source.health.is_usable:
                # 检查是否应该重试（冷却期后）
                if time.time() - source.health.last_failure < 60:  # 1分钟冷却
                    logger.debug(f"Skipping unavailable source: {source.name}")
                    continue

            try:
                result = self._fetch_with_retry(source, **kwargs)
                if result is not None:
                    # 成功：更新健康状态
                    self._update_health(source, success=True)
                    # 写入缓存
                    if use_cache:
                        self._set_cache(cache_key, result, source.cache_ttl)
                    return result
            except Exception as e:
                last_error = e
                self._update_health(source, success=False, error=str(e))
                logger.warning(f"Source {source.name} failed: {e}")
                continue

        # 所有源都失败，尝试返回过期缓存
        if use_cache:
            expired_cache = self._get_from_cache(cache_key, category, allow_expired=True)
            if expired_cache is not None:
                logger.warning(f"All sources failed for {category}, using expired cache")
                return expired_cache

        logger.error(f"All data sources failed for {category}. Last error: {last_error}")
        return None

    def _fetch_with_retry(self, source: DataSource, **kwargs) -> Optional[Any]:
        """带重试的数据获取"""
        import functools

        for attempt in range(source.max_retries + 1):
            try:
                start_time = time.time()
                result = source.fetch_func(**kwargs)
                latency = time.time() - start_time

                # 更新平均响应时间
                if source.health.avg_latency == 0:
                    source.health.avg_latency = latency
                else:
                    source.health.avg_latency = (source.health.avg_latency * 0.8 + latency * 0.2)

                # 响应时间过长标记为降级
                if latency > source.timeout * 0.8:
                    source.health.status = SourceStatus.DEGRADED

                return result

            except Exception as e:
                if attempt < source.max_retries:
                    wait_time = 2 ** attempt  # 指数退避：1s, 2s, 4s
                    logger.debug(f"Retry {attempt + 1}/{source.max_retries} for {source.name} after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise

        return None

    def _update_health(self, source: DataSource, success: bool, error: str = "") -> None:
        """更新数据源健康状态"""
        now = time.time()

        if success:
            source.health.last_success = now
            source.health.success_count += 1
            source.health.status = SourceStatus.HEALTHY
            source.health.error_message = ""
        else:
            source.health.last_failure = now
            source.health.failure_count += 1
            source.health.error_message = error

            # 连续失败3次标记为不可用
            if source.health.failure_count >= 3 and source.health.reliability < 0.3:
                source.health.status = SourceStatus.UNAVAILABLE
            else:
                source.health.status = SourceStatus.DEGRADED

    def _get_from_cache(self, key: str, category: str, allow_expired: bool = False) -> Optional[Any]:
        """从缓存获取数据"""
        if key not in self._cache:
            return None

        timestamp, data = self._cache[key]

        # 确定缓存TTL
        ttl = 60  # 默认
        if category in self._sources and self._sources[category]:
            ttl = self._sources[category][0].cache_ttl

        # 检查是否过期
        if time.time() - timestamp > ttl:
            if allow_expired:
                # 过期缓存最多延长2倍TTL
                if time.time() - timestamp < ttl * 2:
                    return data
            return None

        return data

    def _set_cache(self, key: str, data: Any, ttl: int) -> None:
        """写入缓存"""
        self._cache[key] = (time.time(), data)

        # 清理过期缓存（保留最近100条）
        if len(self._cache) > 100:
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][0])
            for k in sorted_keys[:50]:
                del self._cache[k]

    def get_health_report(self) -> Dict[str, Dict]:
        """获取所有数据源的健康报告"""
        report = {}
        for category, sources in self._sources.items():
            report[category] = []
            for source in sources:
                report[category].append({
                    "name": source.name,
                    "status": source.health.status.value,
                    "reliability": round(source.health.reliability, 2),
                    "avg_latency": round(source.health.avg_latency, 3),
                    "success_count": source.health.success_count,
                    "failure_count": source.health.failure_count,
                    "last_error": source.health.error_message,
                })
        return report

    def clear_cache(self, category: str = None) -> int:
        """清除缓存"""
        if category is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        count = 0
        keys_to_remove = [k for k in self._cache if k.startswith(f"{category}:")]
        for k in keys_to_remove:
            del self._cache[k]
            count += 1
        return count


# ============================================================
# 全局单例
# ============================================================

_global_manager: Optional[DataSourceManager] = None


def get_source_manager() -> DataSourceManager:
    """获取全局数据源管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = DataSourceManager()
        _setup_default_sources(_global_manager)
    return _global_manager


def _setup_default_sources(manager: DataSourceManager) -> None:
    """设置默认数据源"""
    try:
        from .market import MarketData
        market = MarketData()

        # 实时行情数据源
        manager.register_source("realtime", DataSource(
            name="tencent_realtime",
            fetch_func=lambda codes: market.fetch_realtime(codes),
            priority=1,
            timeout=8.0,
            cache_ttl=5,  # 盘中5秒缓存
        ))

        # 历史K线数据源
        manager.register_source("history", DataSource(
            name="tencent_history",
            fetch_func=lambda code, days=120: market.fetch_history(code, days),
            priority=1,
            timeout=10.0,
            cache_ttl=3600,  # 1小时缓存
        ))

        # v8.0: 真实多源备用（此前多源框架只有腾讯单源）。
        # 腾讯失败时自动降级到新浪 → 东财，全部失败返回空触发框架过期缓存兜底。
        try:
            from .sources_fallback import (
                sina_fetch_realtime, em_fetch_realtime,
                sina_fetch_history, em_fetch_history,
            )

            manager.register_source("realtime", DataSource(
                name="sina_realtime",
                fetch_func=lambda codes: sina_fetch_realtime(codes),
                priority=2,
                timeout=8.0,
                cache_ttl=5,
            ))
            manager.register_source("realtime", DataSource(
                name="eastmoney_realtime",
                fetch_func=lambda codes: em_fetch_realtime(codes),
                priority=3,
                timeout=8.0,
                cache_ttl=5,
            ))
            manager.register_source("history", DataSource(
                name="sina_history",
                fetch_func=lambda code, days=120: sina_fetch_history(code, days),
                priority=2,
                timeout=12.0,
                cache_ttl=3600,
            ))
            manager.register_source("history", DataSource(
                name="eastmoney_history",
                fetch_func=lambda code, days=120: em_fetch_history(code, days),
                priority=3,
                timeout=12.0,
                cache_ttl=3600,
            ))
        except ImportError:
            logger.warning("sources_fallback not available, fallback sources disabled")

    except ImportError:
        logger.warning("MarketData not available, some data sources disabled")


# ============================================================
# 装饰器：自动使用数据源管理器
# ============================================================

def with_fallback(category: str, use_cache: bool = True):
    """
    装饰器：为函数添加数据源降级能力

    使用示例：
    ```python
    @with_fallback("realtime")
    def get_stock_price(codes):
        # 这里是主数据源的逻辑
        return market.fetch_realtime(codes)
    ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_source_manager()

            # 检查是否有注册的数据源
            if category in manager._sources:
                # 尝试使用管理器获取数据
                result = manager.fetch(
                    category,
                    use_cache=use_cache,
                    **kwargs
                )
                if result is not None:
                    return result

            # 降级到原函数
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback function failed: {e}")
                return None

        return wrapper
    return decorator
