"""Index analysis"""
from .indices import IndexAnalyzer
from .global_trends import (
    GLOBAL_INDEX_UNIVERSE,
    COMMODITY_ALIASES,
    fetch_index_data,
    fetch_kline,
    fetch_quote,
    fetch_batch_quotes,
    analyze_index,
    global_market_outlook,
    index_forecast,
    sector_trend_report,
)
# v9.0 深度指数分析
from .market_regime import (
    MarketRegimeClassifier, RegimeResult, classify_market_regime,
)
from .volatility_regime import (
    VolatilityRegimeAnalyzer, VolatilityResult, analyze_volatility,
)
from .market_structure import (
    MarketStructureAnalyzer, StructureResult, analyze_market_structure,
)
from .market_internals import (
    MarketInternalsAnalyzer, InternalsResult, analyze_market_internals,
)
from .index_valuation import (
    IndexValuation, IndexValuationResult, classify_index_valuation,
)

__all__ = [
    # legacy
    "IndexAnalyzer",
    "GLOBAL_INDEX_UNIVERSE",
    "COMMODITY_ALIASES",
    "fetch_index_data",
    "fetch_kline",
    "fetch_quote",
    "fetch_batch_quotes",
    "analyze_index",
    "global_market_outlook",
    "index_forecast",
    "sector_trend_report",
    # v9.0 体制 / 波动率 / 结构 / 内含 / 估值
    "MarketRegimeClassifier",
    "RegimeResult",
    "classify_market_regime",
    "VolatilityRegimeAnalyzer",
    "VolatilityResult",
    "analyze_volatility",
    "MarketStructureAnalyzer",
    "StructureResult",
    "analyze_market_structure",
    "MarketInternalsAnalyzer",
    "InternalsResult",
    "analyze_market_internals",
    "IndexValuation",
    "IndexValuationResult",
    "classify_index_valuation",
]
