# -*- coding: utf-8 -*-
"""
量化模型模块
Quantitative Models Module

基于 QuantConnect Lean 架构的A股量化模型：
- Alpha模型：信号生成
- Risk模型：风险管理
- Portfolio模型：组合构建
- 技术指标：技术分析
- GARCH模型：波动率预测 (v2.1.0 新增)
- 因子分析：A股多因子评分 (v2.1.0 新增)
- 配对交易：协整统计套利 (v2.1.0 新增)
- ML预测：机器学习涨跌方向预测 (v2.1.0 新增)
- 因子库：多因子模型组件 (v7.1.0 新增)
- 策略回测：轻量级回测引擎 (v7.1.0 新增)

适配A股市场数据源（东方财富/腾讯财经/同花顺/mootdx）
"""

from .alpha_models import (
    DualThrustAlpha,
    RateOfChangeAlpha,
    MeanReversionAlpha,
    MomentumAlpha,
    ValueInvestingAlpha,
)
from .risk_models import (
    MaximumDrawdownRiskModel,
    StopLossRiskModel,
    TargetProfitRiskModel,
)
from .portfolio_models import (
    EqualWeightPortfolio,
    RiskParityPortfolio,
    ValueWeightedPortfolio,
)
from .indicators import (
    QuantIndicators,
    BollingerBands,
    MACD,
    RSI,
    ADX,
    HurstIndex,
)
from .metrics import (
    QuantMetrics,
    compute_quant_metrics,
    daily_returns,
    max_drawdown,
    format_quant_metrics,
)

# v2.1.0 新增量化工具 — 可选依赖，按需导入
# (numpy/scipy/statsmodels/arch/sklearn 可能未安装)
GarchForecaster = GarchResult = None
FactorAnalyzer = FactorScore = StockFactorReport = None
PairsTrader = PairResult = None
MLPredictor = FeatureEngineer = MLPrediction = None
GoldAnalyzer = GoldSignal = None
FuturesAnalyzer = FuturesSignal = None

try:
    from .garch_model import GarchForecaster, GarchResult
except ImportError:
    pass

try:
    from .factor_analysis import FactorAnalyzer, FactorScore, StockFactorReport
except ImportError:
    pass

try:
    from .pairs_trading import PairsTrader, PairResult
except ImportError:
    pass

try:
    from .ml_predictor import MLPredictor, FeatureEngineer, MLPrediction
except ImportError:
    pass

# v4.4 新增：商品/黄金 + 期货量化分析
try:
    from .commodity_analyzer import GoldAnalyzer, GoldSignal, analyze_gold
except ImportError:
    pass

try:
    from .futures_analyzer import FuturesAnalyzer, FuturesSignal, analyze_futures
except ImportError:
    pass

# v7.1.0 新增：因子库 + 策略回测
from .factors import FactorLibrary, FactorResult, CompositeScore, quick_score
from .backtest import (
    Backtester, Strategy, RSIStrategy, MACDStrategy, DualMAStrategy,
    BacktestResult, quick_backtest
)

# v7.6.0 新增：高级量化因子库（4 大类新因子 + 自适应权重）
from .enhanced_factors import (
    FactorScore, EnhancedCompositeResult,
    MomentumReversionFactor, CapitalFlowFactor,
    VolatilityFactor, CalendarFactor,
    EnhancedFactorLibrary, quick_enhanced_score,
)

# v7.6.0 新增：场景模拟器（牛市/熊市/震荡市多场景概率预测）
from .scenario_simulator import (
    ScenarioResult, ScenarioSimulator,
    quick_scenario_forecast, detect_market_regime_from_history,
)

# v9.3.0 新增：历史形态匹配预测（股票/基金/期货通用，纯标准库）
from .pattern_predictor import (
    HistoricalPatternPredictor, quick_pattern_forecast, pattern_direction_label,
)

__all__ = [
    # Alpha模型
    "DualThrustAlpha", "RateOfChangeAlpha", "MeanReversionAlpha",
    "MomentumAlpha", "ValueInvestingAlpha",
    # 风险模型
    "MaximumDrawdownRiskModel", "StopLossRiskModel", "TargetProfitRiskModel",
    # 组合模型
    "EqualWeightPortfolio", "RiskParityPortfolio", "ValueWeightedPortfolio",
    # 指标
    "QuantIndicators", "BollingerBands", "MACD", "RSI", "ADX", "HurstIndex",
    # 引擎
    "QuantitativeEngine",
    # v7.3 统一量化体检
    "QuantMetrics",
    "compute_quant_metrics",
    "daily_returns",
    "max_drawdown",
    "format_quant_metrics",
    # v2.1.0
    "GarchForecaster", "GarchResult",
    "FactorAnalyzer", "FactorScore", "StockFactorReport",
    "PairsTrader", "PairResult",
    "MLPredictor", "FeatureEngineer", "MLPrediction",
    # v4.4 商品/期货
    "GoldAnalyzer", "GoldSignal", "analyze_gold",
    "FuturesAnalyzer", "FuturesSignal", "analyze_futures",
    # v7.1.0 因子库 + 回测
    "FactorLibrary", "FactorResult", "CompositeScore", "quick_score",
    "Backtester", "Strategy", "RSIStrategy", "MACDStrategy", "DualMAStrategy",
    "BacktestResult", "quick_backtest",
    # v7.6.0 增强因子 + 场景模拟
    "FactorScore", "EnhancedCompositeResult",
    "MomentumReversionFactor", "CapitalFlowFactor",
    "VolatilityFactor", "CalendarFactor",
    "EnhancedFactorLibrary", "quick_enhanced_score",
    "ScenarioResult", "ScenarioSimulator",
    "quick_scenario_forecast", "detect_market_regime_from_history",
    # v9.3.0 历史形态匹配预测
    "HistoricalPatternPredictor", "quick_pattern_forecast",
    "pattern_direction_label",
    # v8.0.0 组合优化
    "mean_variance_optimize", "max_sharpe_weights",
    "risk_parity_weights", "portfolio_var_es", "allocate_portfolio",
    # v8.0.0 债券 / 货币基金 / 可转债
    "bond_price", "bond_duration", "bond_convexity",
    "ytm_from_price", "credit_spread", "yield_curve_metrics", "analyze_bond",
    "MoneyFundAnalyzer", "ConvertibleBondAnalyzer",
    # v8.0.0 统一全资产量化入口
    "quant_analyze_asset", "detect_asset_type",
]


def __getattr__(name):
    """懒加载需要 numpy 的量化引擎，保证纯标准库子模块可独立使用。"""
    if name == "QuantitativeEngine":
        from .engine import QuantitativeEngine
        return QuantitativeEngine
    # v8.0.0 组合优化（纯 stdlib，可按需导入）
    if name in ("mean_variance_optimize", "max_sharpe_weights",
                "risk_parity_weights", "portfolio_var_es", "allocate_portfolio"):
        from .portfolio_models import (mean_variance_optimize, max_sharpe_weights,
                                       risk_parity_weights, portfolio_var_es,
                                       allocate_portfolio)
        return locals()[name]
    # v8.0.0 债券量化
    if name in ("bond_price", "bond_duration", "bond_convexity",
                "ytm_from_price", "credit_spread", "yield_curve_metrics", "analyze_bond"):
        from .bond_analyzer import (bond_price, bond_duration, bond_convexity,
                                    ytm_from_price, credit_spread, yield_curve_metrics,
                                    analyze_bond)
        return locals()[name]
    if name == "MoneyFundAnalyzer":
        from .money_fund_analyzer import MoneyFundAnalyzer
        return MoneyFundAnalyzer
    if name == "ConvertibleBondAnalyzer":
        from .convertible_bond_analyzer import ConvertibleBondAnalyzer
        return ConvertibleBondAnalyzer
    if name in ("quant_analyze_asset", "detect_asset_type"):
        from .asset_quant import quant_analyze_asset, detect_asset_type
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
