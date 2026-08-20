"""
微信聊天分析助手 v2.0.0 - 核心抽象层

提供统一的数据模型、抽象基类和工具函数。
所有分析器、预测器、检索器都应继承此处的基类以保证接口一致。
"""

import sys
sys.dont_write_bytecode = True

from core.message import Message, MessageType, SenderRole
from core.result import AnalysisResult, PredictionResult, Prediction
from core.analyzer_base import AnalyzerBase, AnalyzerRegistry
from core.predictor_base import PredictorBase, PredictionContext

# v2.5.0：版本号单一来源（见 core/version.py）
from core.version import __version__
__all__ = [
    "Message",
    "MessageType",
    "SenderRole",
    "AnalysisResult",
    "PredictionResult",
    "Prediction",
    "AnalyzerBase",
    "AnalyzerRegistry",
    "PredictorBase",
    "PredictionContext",
]
