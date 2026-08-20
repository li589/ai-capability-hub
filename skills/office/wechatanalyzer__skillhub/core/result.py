"""
统一分析结果数据模型

v2.0.0 所有分析器输出 AnalysisResult 格式，便于统一调度和持久化。
预测器输出 PredictionResult，包含多个候选预测。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional


@dataclass
class AnalysisResult:
    """分析结果统一格式

    字段:
        analyzer_name: 分析器名称（'mbti' / 'bigfive' / 'sentiment' / 'risk' 等）
        score: 主分数（0-100 或 0-1，由分析器决定）
        confidence: 置信度（0-100）
        details: 详细数据（按分析器自定义）
        metadata: 元数据（耗时、样本量、版本等）
    """
    analyzer_name: str
    score: float = 0.0
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        return cls(
            analyzer_name=data.get("analyzer_name", "unknown"),
            score=data.get("score", 0.0),
            confidence=data.get("confidence", 0.0),
            details=data.get("details", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Prediction:
    """单条预测"""
    text: str
    confidence: float = 0.5
    strategy: str = "default"  # 'defensive' / 'offensive' / 'diplomatic' / 'rag' / 'simulation' / 'rule'
    rationale: str = ""  # 预测理由
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PredictionResult:
    """预测结果统一格式

    字段:
        top_prediction: 最可能的下一条消息
        alternatives: 备选预测列表
        scenario: 场景判断
        context: 上下文信息（mbti / big_five / sentiment 等）
        metadata: 元数据（耗时、来源等）
    """
    top_prediction: Prediction
    alternatives: List[Prediction] = field(default_factory=list)
    scenario: str = "social"
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "top_prediction": self.top_prediction.to_dict(),
            "alternatives": [p.to_dict() for p in self.alternatives],
            "scenario": self.scenario,
            "context": self.context,
            "metadata": self.metadata,
        }

    @classmethod
    def from_legacy(cls, legacy: Dict[str, Any]) -> "PredictionResult":
        """从 v1.2.0 的 dict 格式构造（向后兼容）"""
        next_msg = legacy.get("next_message", "")
        alts = legacy.get("alternatives", [])
        top = Prediction(
            text=next_msg,
            confidence=0.7,
            strategy="rule",
            rationale=legacy.get("based_on", ""),
        )
        return cls(
            top_prediction=top,
            alternatives=[Prediction(text=a) for a in alts],
            scenario=legacy.get("scenario", "social"),
            context=legacy,
        )
