"""
微信聊天分析器 v2.0.0

模块化拆分自 v1.2.0 的 text_analyzer.py，每个分析器独立成模块。
所有分析器继承 core.AnalyzerBase，统一通过 AnalyzerRegistry 调度。

可用分析器：
    - mbti: MBTI 人格推断
    - bigfive: 大五人格
    - sentiment: 情感分析（支持否定识别 + 程度副词）
    - risk: 风险检测（支持反讽识别 + 上下文验证）
    - scenario: 场景分类
    - pattern: 对话模式分析
    - inference: 5 大推演能力（v2.2.0 新增）
    - interpretation: 4 大解读能力（v2.2.0 新增）
"""

import sys
sys.dont_write_bytecode = True

from core.analyzer_base import AnalyzerBase, AnalyzerRegistry
from analyzers.mbti_analyzer import MBTIAnalyzer
from analyzers.bigfive_analyzer import BigFiveAnalyzer
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.risk_analyzer import RiskAnalyzer
from analyzers.scenario_analyzer import ScenarioAnalyzer
from analyzers.pattern_analyzer import PatternAnalyzer
# v2.2.0 新增
from analyzers.inference_analyzer import InferenceAnalyzer
from analyzers.interpretation_analyzer import InterpretationAnalyzer


__version__ = "2.2.0"


def create_default_registry(config: dict = None) -> AnalyzerRegistry:
    """创建默认的注册中心（包含所有分析器）"""
    registry = AnalyzerRegistry()

    cfg = config or {}
    analysis_cfg = cfg.get("analysis", {})

    if analysis_cfg.get("mbti_enabled", True):
        registry.register(MBTIAnalyzer(config=cfg))
    if analysis_cfg.get("bigfive_enabled", True):
        registry.register(BigFiveAnalyzer(config=cfg))
    if analysis_cfg.get("sentiment_enabled", True):
        registry.register(SentimentAnalyzer(config=cfg))
    if analysis_cfg.get("risk_detection_enabled", True):
        registry.register(RiskAnalyzer(config=cfg))

    # 场景和模式默认开启
    registry.register(ScenarioAnalyzer(config=cfg))
    registry.register(PatternAnalyzer(config=cfg))

    # v2.2.0 新增：推演 + 信息解读（默认开启）
    if analysis_cfg.get("inference_enabled", True):
        registry.register(InferenceAnalyzer(config=cfg))
    if analysis_cfg.get("interpretation_enabled", True):
        registry.register(InterpretationAnalyzer(config=cfg))

    return registry


__all__ = [
    "AnalyzerBase",
    "AnalyzerRegistry",
    "MBTIAnalyzer",
    "BigFiveAnalyzer",
    "SentimentAnalyzer",
    "RiskAnalyzer",
    "ScenarioAnalyzer",
    "PatternAnalyzer",
    # v2.2.0 新增
    "InferenceAnalyzer",
    "InterpretationAnalyzer",
    "create_default_registry",
]
