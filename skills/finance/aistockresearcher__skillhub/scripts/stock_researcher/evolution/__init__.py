#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evolution 包 — 自我迭代与进化 (v4.0.0 新增，半自动+审计)

模块：
- prediction_tracker: 记录预测→事后解析实际结果→计算命中率
- feedback_store:    用户反馈(赞/踩/采纳) 持久化
- weight_optimizer:  基于滚动命中率计算权重调整建议(半自动,不自动应用)
- audit_log:         进化操作审计日志(追加JSONL,可追溯回滚)
- evolution_runner:  定期进化例行(解析/分析/提议/审计)
"""
from .prediction_tracker import PredictionTracker
from .evolution_runner import (
    FeedbackStore, WeightOptimizer, AuditLog, get_audit_log,
    EvolutionRunner, run_self_evolution,
)

__all__ = [
    "PredictionTracker", "FeedbackStore", "WeightOptimizer",
    "AuditLog", "get_audit_log",
    "EvolutionRunner", "run_self_evolution",
]
