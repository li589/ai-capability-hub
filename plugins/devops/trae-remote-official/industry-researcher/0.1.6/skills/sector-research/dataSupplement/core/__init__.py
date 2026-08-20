# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 核心基础设施包
====================================

本包提供金融数据获取所需的底层基础设施:

模块一览:
  - client: 统一 HTTP 客户端(零外部依赖, 自动重试, 双 SSL)
  - throttle: 域名级别请求限流器
  - cache: 带 TTL 的内存缓存
  - ticker: 多市场股票代码标准化与转换

快速使用:
    from fin_data_skills.core import (
        http_get, http_post, throttled_get,
        cache_get, cache_set, make_key, TTL_QUOTE,
        normalize, detect_market, to_eastmoney_secid,
    )
"""

# === HTTP 客户端 ===
from .client import (
    HttpResponse,
    http_get,
    http_post,
)

# === 限流器 ===
from .throttle import (
    Throttle,
    throttled_get,
    get_throttle_for_domain,
    register_domain_throttle,
    DOMAIN_THROTTLE_REGISTRY,
)

# === 内存缓存 ===
from .cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_clear,
    cache_stats,
    make_key,
    TTL_QUOTE,
    TTL_KLINE,
    TTL_FUNDAMENTAL,
    TTL_NEWS,
    TTL_FINANCE,
    TTL_REPORT,
)

# === 股票代码标准化 ===
from .ticker import (
    normalize,
    detect_market,
    cn_prefix,
    to_eastmoney_secid,
    to_tencent_code,
    to_sina_code,
    to_yahoo_symbol,
)

# === 公共工具函数 ===
from .utils import (
    safe_float,
    safe_int,
    strip_html,
    ts_to_str,
)

__all__ = [
    # client
    "HttpResponse",
    "http_get",
    "http_post",
    # throttle
    "Throttle",
    "throttled_get",
    "get_throttle_for_domain",
    "register_domain_throttle",
    "DOMAIN_THROTTLE_REGISTRY",
    # cache
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear",
    "cache_stats",
    "make_key",
    "TTL_QUOTE",
    "TTL_KLINE",
    "TTL_FUNDAMENTAL",
    "TTL_NEWS",
    "TTL_FINANCE",
    "TTL_REPORT",
    # ticker
    "normalize",
    "detect_market",
    "cn_prefix",
    "to_eastmoney_secid",
    "to_tencent_code",
    "to_sina_code",
    "to_yahoo_symbol",
    # utils
    "safe_float",
    "safe_int",
    "strip_html",
    "ts_to_str",
]

__version__ = "7.1.0"
