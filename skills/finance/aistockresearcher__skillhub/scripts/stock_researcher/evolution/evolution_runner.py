#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""进化辅助模块 (v4.0.0)
- feedback_store: 用户反馈持久化
- weight_optimizer: 滚动命中率指数加权权重建议(仅建议,不自动应用)
- audit_log: 进化操作审计日志
- evolution_runner: 定期进化例行
"""
from __future__ import annotations
import sys, json, math, uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
EVO_DIR = SKILL_DIR / "data" / "evolution"
EVO_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SKILL_DIR / "scripts"))

# ────────────────────────────────────────────────────────────
# feedback_store
# ────────────────────────────────────────────────────────────
class FeedbackStore:
    def __init__(self):
        self._file = EVO_DIR / "feedback.jsonl"

    def submit(self, prediction_id: str, action: str, comment: str = "") -> bool:
        """action: like/dislike/adopted/rejected"""
        try:
            entry = {
                "prediction_id": prediction_id,
                "action": action,
                "comment": comment,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(self._file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception:
            return False

    def get_all(self, limit: int = 100) -> List[Dict]:
        entries = []
        if not self._file.exists():
            return entries
        with open(self._file, "r", encoding="utf-8") as f:
            for line in f.readlines()[-limit:]:
                try:
                    entries.append(json.loads(line.strip()))
                except Exception:
                    pass
        return entries


# ────────────────────────────────────────────────────────────
# weight_optimizer
# ────────────────────────────────────────────────────────────
class WeightOptimizer:
    """基于滚动命中率的指数加权权重建议器 (半自动)"""

    @staticmethod
    def propose_weights(accuracy_report: Dict) -> Optional[Dict]:
        """从准确率报告生成权重调整建议。
        by_model 命中率 → 指数加权转化为建议权重。
        返回 None 表示无明显调整信号或数据不足。
        """
        by_model = accuracy_report.get("by_model", {})
        if not by_model or len(by_model) < 2:
            return None

        # 指数加权: weight ∝ exp(hit_rate - baseline)
        rates = []
        for model, rate in by_model.items():
            if rate > 0:
                rates.append((model, rate))
        if not rates:
            return None

        baseline = sum(r for _, r in rates) / len(rates)
        weights = {}
        for model, rate in rates:
            w = math.exp((rate - baseline) / 10)
            weights[model] = round(w, 4)

        total = sum(weights.values())
        if total > 0:
            weights = {k: round(v / total, 4) for k, v in weights.items()}

        # 按周期汇总（若有）
        by_horizon = accuracy_report.get("by_horizon", {})
        horizon_weights = {}
        for h, rate in by_horizon.items():
            if rate > 0:
                horizon_weights[h] = round(math.exp((rate - baseline) / 10), 4)
        if horizon_weights:
            ht = sum(horizon_weights.values())
            if ht > 0:
                horizon_weights = {k: round(v / ht, 4) for k, v in horizon_weights.items()}

        return {
            "model_weights": weights,
            "horizon_weights": horizon_weights or None,
            "baseline_hit_rate": round(baseline, 1),
            "proposed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


# ────────────────────────────────────────────────────────────
# audit_log
# ────────────────────────────────────────────────────────────
class AuditLog:
    def __init__(self):
        self._file = EVO_DIR / "audit.jsonl"

    def log(self, action: str, before: Dict = None, after: Dict = None,
            reason: str = "", report: Dict = None):
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "before": before or {},
            "after": after or {},
            "reason": reason,
            "accuracy_report": report or {},
        }
        with open(self._file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def tail(self, n: int = 20) -> List[Dict]:
        entries = []
        if not self._file.exists():
            return entries
        with open(self._file, "r", encoding="utf-8") as f:
            for line in f.readlines()[-n:]:
                try:
                    entries.append(json.loads(line.strip()))
                except Exception:
                    pass
        return entries


def get_audit_log(n: int = 20) -> List[Dict]:
    return AuditLog().tail(n)


# ────────────────────────────────────────────────────────────
# evolution_runner
# ────────────────────────────────────────────────────────────
class EvolutionRunner:
    """定期进化例行（半自动：建议 → 审计 → 待确认）"""

    def __init__(self):
        self.tracker = PredictionTracker()
        self.optimizer = WeightOptimizer()
        self.audit = AuditLog()

    def run(self, mode: str = "propose") -> Dict:
        """执行进化例行。

        mode: "propose" — 解析pending→计算命中→输出权重建议(不应用,写审计)
              "apply"  — 同上+应用权重到 weights.json(半自动,用户确认后调用)

        Returns:
            Dict: 进化操作摘要
        """
        # 1. 解析 pending 预测
        resolved = self.tracker.resolve_pending()

        # 2. 获取准确率报告
        report = self.tracker.accuracy_report(window_days=90)

        # 3. 生成权重建议
        proposal = self.optimizer.propose_weights(report)

        result = {
            "resolved_predictions": resolved,
            "total_tracked": report["total_predictions"],
            "hit_rate_pct": report["hit_rate_pct"],
            "by_horizon": report.get("by_horizon", {}),
            "by_model": report.get("by_model", {}),
            "proposal": proposal,
            "applied": False,
        }

        # 审计
        if proposal:
            self.audit.log("evolution_propose", reason=f"hit_rate={report['hit_rate_pct']}%",
                           report=report)
            if mode == "apply":
                # 将模型层权重映射为融合层可读格式
                # fusion 读取: {horizon: {dimension: weight}} 或 {"_flat": {dimension: weight}}
                weights_file = EVO_DIR / "weights.json"
                fusion_weights = self._to_fusion_format(proposal)
                with open(weights_file, "w", encoding="utf-8") as f:
                    json.dump(fusion_weights, f, ensure_ascii=False, indent=2)
                result["applied"] = True
                self.audit.log("evolution_apply", after=fusion_weights,
                               reason=f"用户确认应用: hit_rate={report['hit_rate_pct']}%",
                               report=report)
        else:
            result["note"] = "数据不足以生成权重调整建议(需≥2个模型有命中数据)"

        return result

    @staticmethod
    def _to_fusion_format(proposal: Dict) -> Dict:
        """将 flat model_weights 扩展为融合层兼容的 {horizon: {dimension: weight}} 格式。

        策略：以默认 horizon weights 为模板，用 model_weights 中的维度相对权重等比缩放各周期内该维度的权重，
        缺失维度保持默认值。"""
        from stock_researcher.fusion.multi_horizon_forecaster import DEFAULT_HORIZON_WEIGHTS
        model_weights = proposal.get("model_weights", {})
        if not model_weights:
            return DEFAULT_HORIZON_WEIGHTS

        # model_weights 的维度名与融合维度名相同，但权重反映相对重要性
        # 缩放逻辑：对于每个维度 d，new_weight[h][d] = default[h][d] * (model_weights[d] / avg_model_weight)
        avg_mw = sum(model_weights.values()) / len(model_weights) if model_weights else 1.0
        result = {}
        for horizon, dim_weights in DEFAULT_HORIZON_WEIGHTS.items():
            result[horizon] = {}
            for dim, dw in dim_weights.items():
                mw = model_weights.get(dim, avg_mw)
                scale = mw / avg_mw if avg_mw > 0 else 1.0
                result[horizon][dim] = round(dw * max(0.3, min(3.0, scale)), 4)
            # 按周期内重新归一化
            total = sum(result[horizon].values())
            if total > 0:
                result[horizon] = {k: round(v / total, 4) for k, v in result[horizon].items()}
        return result


def run_self_evolution(mode: str = "propose") -> Dict:
    return EvolutionRunner().run(mode)
