"""
预测器抽象基类

所有预测器（Rule / RAG / MiroFish）必须继承 PredictorBase，
EnsemblePredictor 在 predictors/__init__.py 中实现三层融合。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core.message import Message
from core.result import PredictionResult, Prediction


@dataclass
class PredictionContext:
    """预测上下文

    字段:
        messages: 历史消息（按时间正序）
        mbti: 已推断的 MBTI 类型（可选）
        big_five: 大五人格数据（可选）
        sentiment: 情感分析数据（可选）
        scenario: 场景（romantic / work / social / important）
        recent_window: 用于检索的最近消息窗口大小
        metadata: 附加元数据
    """
    messages: List[Message]
    mbti: Optional[str] = None
    big_five: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None
    scenario: str = "social"
    recent_window: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


class PredictorBase(ABC):
    """预测器抽象基类

    子类需实现：
        - name: 唯一标识
        - predict(): 核心预测逻辑
        - is_available(): 依赖检查
    """

    name: str = "base"
    version: str = "2.3.0"
    weight: float = 1.0  # 在 EnsemblePredictor 中的默认权重
    description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def predict(self, context: PredictionContext) -> PredictionResult:
        """执行预测

        Args:
            context: 预测上下文

        Returns:
            PredictionResult
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查依赖是否满足（模型是否下载、Zep 是否在线等）

        Returns:
            True 表示可用
        """
        pass

    def get_weight(self) -> float:
        """获取在集成中的权重"""
        return self.weight
