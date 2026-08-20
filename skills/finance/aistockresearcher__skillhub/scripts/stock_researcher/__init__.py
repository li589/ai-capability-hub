"""
全球智能投研模块 v9.2
Professional Global Investment Research Module

覆盖12个全球主流市场 + 黄金/商品期货。
纯 Python 标准库核心，零 pip install。

v9.2 新增：
  - 定期报告解读（年报/半年报/季报 同比环比 + 亮点风险 + 中文报告）

v9.0 三大支柱：
  - 深度板块：RPS 相对强度 / 板块宽度 / 横截面离散度 / 主题概念 / 轮动周期
  - 深度指数：市场体制 / 波动率体制 / 市场结构 / 市场内含 / 真实 PE 分位
  - 体制感知预测：regime 条件化权重 / 信号共识度 / 宏观情景 / 置信度校准

历史：
  v8.0 全资产量化入口 quant_analyze_asset + 真实数据 + 组合优化 + MC 增强 + ML 接入
  v7.4 统一量化绩效指标 QuantMetrics（收益/波动/Sharpe/Sortino/Calmar/VaR/胜率/Beta/Alpha）
  v7.3 腾讯行情字段映射 + 基金/ETF 资产类型识别
  v7.2 数据质量四级标记 + 严格模式 + PE/PB 真实历史分位
  v7.1 五维信息聚合 + 多资产涨跌推演
"""
import sys
sys.dont_write_bytecode = True

from .core.analyzer import StockResearcher

# v7.0 新模块导出
from .data.market_classifier import MarketClassifier, detect_market, normalize_code
from .data.global_market import (
    fetch_global_quote, fetch_global_kline,
    get_global_risk_appetite, analyze_gold_factors,
    get_market_correlation, GLOBAL_INDICES, GLOBAL_MARKETS,
)

# v7.1 新模块：五维分析 + 多资产推演
def __getattr__(name):
    # 懒加载避免强制依赖
    if name in ("FiveDimAnalyzer", "quick_five_dim",
                "AssetForecaster", "quick_forecast", "detect_asset_type"):
        from . import analysis
        return getattr(analysis, name)
    # v7.2 数据质量模块懒加载
    if name in ("DataQuality", "mark_field", "is_estimated", "is_unavailable",
                "unwrap", "build_quality_report"):
        from .data import data_quality as _dq
        return getattr(_dq, name)
    # v7.3 统一量化体检（纯标准库，不触发 numpy）
    if name in ("QuantMetrics", "compute_quant_metrics", "daily_returns",
                "max_drawdown", "format_quant_metrics"):
        from . import quantitative as _q
        return getattr(_q, name)
    # v8.0 统一全资产量化入口
    if name == "quant_analyze_asset":
        from .quantitative.asset_quant import quant_analyze_asset
        return quant_analyze_asset
    # v9.0 深度板块/指数/体制感知预测（懒加载，保持轻量导入）
    if name in ("SectorRelativeStrength", "rps_ranking", "SectorBreadth",
                "analyze_breadth", "SectorDispersion", "analyze_dispersion",
                "list_themes", "analyze_theme", "RotationCycleDetector",
                "detect_cycle_stage"):
        from .sector_analysis import (SectorRelativeStrength, rps_ranking,
                                      SectorBreadth, analyze_breadth,
                                      SectorDispersion, analyze_dispersion,
                                      list_themes, analyze_theme,
                                      RotationCycleDetector, detect_cycle_stage)
        return {
            "SectorRelativeStrength": SectorRelativeStrength,
            "rps_ranking": rps_ranking,
            "SectorBreadth": SectorBreadth,
            "analyze_breadth": analyze_breadth,
            "SectorDispersion": SectorDispersion,
            "analyze_dispersion": analyze_dispersion,
            "list_themes": list_themes,
            "analyze_theme": analyze_theme,
            "RotationCycleDetector": RotationCycleDetector,
            "detect_cycle_stage": detect_cycle_stage,
        }[name]
    if name in ("MarketRegimeClassifier", "classify_market_regime",
                "VolatilityRegimeAnalyzer", "analyze_volatility",
                "MarketStructureAnalyzer", "analyze_market_structure",
                "MarketInternalsAnalyzer", "analyze_market_internals",
                "IndexValuation", "classify_index_valuation"):
        from .index_analysis import (MarketRegimeClassifier,
                                     classify_market_regime,
                                     VolatilityRegimeAnalyzer,
                                     analyze_volatility,
                                     MarketStructureAnalyzer,
                                     analyze_market_structure,
                                     MarketInternalsAnalyzer,
                                     analyze_market_internals,
                                     IndexValuation,
                                     classify_index_valuation)
        return {
            "MarketRegimeClassifier": MarketRegimeClassifier,
            "classify_market_regime": classify_market_regime,
            "VolatilityRegimeAnalyzer": VolatilityRegimeAnalyzer,
            "analyze_volatility": analyze_volatility,
            "MarketStructureAnalyzer": MarketStructureAnalyzer,
            "analyze_market_structure": analyze_market_structure,
            "MarketInternalsAnalyzer": MarketInternalsAnalyzer,
            "analyze_market_internals": analyze_market_internals,
            "IndexValuation": IndexValuation,
            "classify_index_valuation": classify_index_valuation,
        }[name]
    if name in ("MacroScenarioEngine", "analyze_scenarios",
                "PredictionCalibrator", "calibrate_confidence",
                "TopDownReport", "build_topdown"):
        if name in ("MacroScenarioEngine", "analyze_scenarios"):
            from .quantitative.scenario_engine import MacroScenarioEngine, analyze_scenarios
            return {"MacroScenarioEngine": MacroScenarioEngine,
                    "analyze_scenarios": analyze_scenarios}[name]
        if name in ("PredictionCalibrator", "calibrate_confidence"):
            from .evolution.calibration import PredictionCalibrator, calibrate_confidence
            return {"PredictionCalibrator": PredictionCalibrator,
                    "calibrate_confidence": calibrate_confidence}[name]
        from .analysis.top_down import TopDownReport, build_topdown
        return {"TopDownReport": TopDownReport, "build_topdown": build_topdown}[name]
    # v9.2 定期报告解读（年报/半年报/季报 同比环比 + 亮点风险）
    if name in ("FinancialReportInterpreter", "ReportInterpretation",
                "interpret_report", "format_report"):
        from .research.financial_report import (
            FinancialReportInterpreter, ReportInterpretation,
            interpret_report, format_report,
        )
        return {"FinancialReportInterpreter": FinancialReportInterpreter,
                "ReportInterpretation": ReportInterpretation,
                "interpret_report": interpret_report,
                "format_report": format_report}[name]
    # v9.3 历史形态匹配预测（股票/基金/期货通用，纯标准库）
    if name in ("HistoricalPatternPredictor", "quick_pattern_forecast",
                "pattern_direction_label"):
        from .quantitative.pattern_predictor import (
            HistoricalPatternPredictor, quick_pattern_forecast,
            pattern_direction_label,
        )
        return {"HistoricalPatternPredictor": HistoricalPatternPredictor,
                "quick_pattern_forecast": quick_pattern_forecast,
                "pattern_direction_label": pattern_direction_label}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "StockResearcher",
    "MarketClassifier", "detect_market", "normalize_code",
    "fetch_global_quote", "fetch_global_kline",
    "get_global_risk_appetite", "analyze_gold_factors",
    "get_market_correlation", "GLOBAL_INDICES", "GLOBAL_MARKETS",
    # v7.1
    "FiveDimAnalyzer", "quick_five_dim",
    "AssetForecaster", "quick_forecast", "detect_asset_type",
    # v7.2 数据质量
    "DataQuality", "mark_field", "is_estimated", "is_unavailable",
    "unwrap", "build_quality_report",
    # v7.3 统一量化体检
    "QuantMetrics", "compute_quant_metrics", "daily_returns",
    "max_drawdown", "format_quant_metrics",
    # v9.2 定期报告解读
    "FinancialReportInterpreter", "ReportInterpretation",
    "interpret_report", "format_report",
    # v9.3 历史形态匹配预测
    "HistoricalPatternPredictor", "quick_pattern_forecast",
    "pattern_direction_label",
]
__version__ = "9.3.0"
