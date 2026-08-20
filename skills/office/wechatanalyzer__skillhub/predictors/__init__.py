"""
预测器集合 v2.0.0

三层融合预测：
    - RulePredictor: 基于 MBTI + 场景 + 关键词的规则预测
    - RAGPredictor: 基于历史相似对话的检索增强预测
    - MiroFishPredictor: 多智能体博弈模拟预测

通过 EnsemblePredictor 加权融合。
"""

import sys
sys.dont_write_bytecode = True

from core.predictor_base import PredictorBase, PredictionContext
from core.result import PredictionResult, Prediction
from predictors.rule_predictor import RulePredictor
from predictors.rag_predictor import RAGPredictor
from predictors.mirofish_predictor import MiroFishPredictor
from predictors.ensemble import EnsemblePredictor


__version__ = "2.3.0"


def create_default_ensemble(config: dict = None) -> EnsemblePredictor:
    """创建默认的集成预测器

    Args:
        config: 配置字典

    Returns:
        EnsemblePredictor
    """
    cfg = config or {}
    predictor_cfg = cfg.get("conversation_predictor", {})

    ensemble = EnsemblePredictor(config=cfg)

    # 规则预测器：始终启用
    if predictor_cfg.get("enabled", True):
        ensemble.add_predictor(RulePredictor(config=cfg))

    # RAG 预测器：如果 RAG 可用
    if cfg.get("rag", {}).get("enabled", True):
        try:
            ensemble.add_predictor(RAGPredictor(config=cfg))
        except Exception:
            pass  # RAG 不可用时跳过

    # MiroFish 预测器：仅在 mirofish.enabled = true
    if cfg.get("mirofish", {}).get("enabled", False):
        try:
            ensemble.add_predictor(MiroFishPredictor(config=cfg))
        except Exception:
            pass

    return ensemble


__all__ = [
    "PredictorBase",
    "PredictionContext",
    "PredictionResult",
    "Prediction",
    "RulePredictor",
    "RAGPredictor",
    "MiroFishPredictor",
    "EnsemblePredictor",
    "create_default_ensemble",
]
