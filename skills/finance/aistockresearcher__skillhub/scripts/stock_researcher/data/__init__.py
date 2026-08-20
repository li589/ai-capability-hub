"""Data layer v7.1.0 — 多市场数据支持 + 全球市场 + 数据源管理器"""
from .market import MarketData
from .fundamental import FundamentalData
from .money_flow import MoneyFlowData
from .news import NewsData
from .macro import MacroData
from .market_all_stocks_crawler import MarketAllStocksCrawler, StockScreener
from .sentiment_forum_crawler import SentimentForumCrawler, SentimentAlert

# v6.0: 多市场支持
from .market_classifier import MarketClassifier, detect_market, normalize_code
from .hk_market import HkMarketData
from .us_market import UsMarketData
from .errors import DataSourceError, safe_float, make_result, handle_request

# v7.1: 数据源管理器（多源冗余 + 自动降级）
from .source_manager import (
    DataSourceManager, DataSource, SourceStatus, SourceHealth,
    get_source_manager, with_fallback
)

# v7.0: 全球市场（日/韩/欧/澳/印 + 商品期货，东财源，懒加载避免影响启动）
def __getattr__(name):
    if name in ("EastMoneyClient", "fetch_global_quote", "fetch_global_kline",
                "GLOBAL_MARKETS", "GLOBAL_INDICES"):
        from . import global_market
        return getattr(global_market, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "MarketData", "FundamentalData", "MoneyFlowData", "NewsData", "MacroData",
    "MarketAllStocksCrawler", "StockScreener",
    "SentimentForumCrawler", "SentimentAlert",
    # v6.0
    "MarketClassifier", "detect_market", "normalize_code",
    "HkMarketData", "UsMarketData",
    "DataSourceError", "safe_float", "make_result", "handle_request",
    # v7.0
    "EastMoneyClient", "fetch_global_quote", "fetch_global_kline",
    "GLOBAL_MARKETS", "GLOBAL_INDICES",
    # v7.1
    "DataSourceManager", "DataSource", "SourceStatus", "SourceHealth",
    "get_source_manager", "with_fallback",
]