"""
集成预测器 - v2.2.0

加权融合多个预测器的输出。
v2.2.0 升级：
- 自适应权重（基于各预测器的历史准确率 + 文本相似度）
- 上下文匹配加分：与最近对方消息语义相似的预测获得加权
- 风险规避：检测到对抗信号时降权积极策略
- 风格一致：与历史我方风格不一致的预测降权
- 去重：相同文本的预测合并（规范化文本）
- 多策略加成：被多种预测器独立选中的文本置信度提升
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
import re

from core.predictor_base import PredictorBase, PredictionContext
from core.result import PredictionResult, Prediction
from core.timing import analyze_timing


class EnsemblePredictor(PredictorBase):
    """集成预测器（v2.2.0 智能融合）"""

    name = "ensemble"
    version = "2.3.0"
    weight = 1.0
    description = "多层预测器集成（自适应权重 + 上下文匹配 + 风险规避 + 风格适配）"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._predictors: List[PredictorBase] = []
        # 各预测器历史准确率（可由外部更新）
        self._accuracy: Dict[str, float] = {}
        # 风险信号检测
        self._risk_signals = {
            "生气", "滚", "滚蛋", "讨厌", "烦死", "别理我", "不想", "失望",
            "过分", "混蛋", "威胁", "报警", "拉黑", "删除",
        }

    def add_predictor(self, predictor: PredictorBase) -> None:
        """添加预测器"""
        if not isinstance(predictor, PredictorBase):
            raise TypeError(f"Expected PredictorBase, got {type(predictor)}")
        self._predictors.append(predictor)

    def remove_predictor(self, name: str) -> None:
        """移除预测器"""
        self._predictors = [p for p in self._predictors if p.name != name]

    def list_predictors(self) -> List[str]:
        return [p.name for p in self._predictors]

    def update_accuracy(self, name: str, accuracy: float) -> None:
        """更新预测器的历史准确率（用于自适应权重）"""
        self._accuracy[name] = max(0.0, min(1.0, accuracy))

    def is_available(self) -> bool:
        """至少有一个预测器可用"""
        return any(p.is_available() for p in self._predictors)

    def predict(self, context: PredictionContext) -> PredictionResult:
        """集成预测（v2.2.0 智能融合）"""
        all_predictions: List[Tuple[Prediction, str]] = []  # (预测, 来源)
        strategies_used: List[str] = []

        # 1. 收集所有预测
        for predictor in self._predictors:
            if not predictor.is_available():
                continue
            try:
                result = predictor.predict(context)
                strategies_used.append(predictor.name)
                all_predictions.append((result.top_prediction, predictor.name))
                for alt in result.alternatives:
                    all_predictions.append((alt, predictor.name))
            except Exception:
                continue

        if not all_predictions:
            return PredictionResult(
                top_prediction=Prediction(text="嗯嗯", confidence=0.3, strategy="fallback"),
                alternatives=[],
                scenario=context.scenario,
                context={},
                metadata={"error": "no_predictor_available"},
            )

        # 2. 上下文特征提取
        ctx_features = self._extract_context_features(context)

        # 3. 智能融合
        merged = self._smart_merge(all_predictions, ctx_features)

        # 4. 排序
        merged.sort(key=lambda p: p.confidence, reverse=True)

        top = merged[0]
        alternatives = merged[1:6]
        timing = ctx_features["timing"].to_dict()

        return PredictionResult(
            top_prediction=top,
            alternatives=alternatives,
            scenario=context.scenario,
            context={
                "mbti": context.mbti,
                "big_five": context.big_five,
                "sentiment": context.sentiment,
                "last_intent": ctx_features["last_intent"],
                "has_risk": ctx_features["has_risk"],
                "timing": timing,
            },
            metadata={
                "predictor": "EnsemblePredictor",
                "version": self.version,
                "predictors_used": strategies_used,
                "total_candidates": len(all_predictions),
                "merged_candidates": len(merged),
                "weights_applied": self._accuracy or "default",
                "context_features": {
                    "last_intent": ctx_features["last_intent"],
                    "has_risk": ctx_features["has_risk"],
                    "sentiment_trend": ctx_features["sentiment_trend"],
                    "timing": timing,
                },
            },
        )

    # ----------------------------------------------------------------
    # 上下文特征
    # ----------------------------------------------------------------
    def _extract_context_features(self, context: PredictionContext) -> Dict[str, Any]:
        """提取上下文特征（用于融合阶段）"""
        messages = context.messages or []
        other_msgs = [m for m in messages if m.is_other() and m.has_content()]
        last_other = other_msgs[-1] if other_msgs else None
        last_content = last_other.content if last_other else ""

        # 意图（粗略版）
        last_intent = "statement"
        if last_content:
            if any(q in last_content for q in ["?", "？", "吗", "呢", "怎么", "什么"]):
                last_intent = "question"
            elif any(r in last_content for r in ["帮", "请", "麻烦", "能不能"]):
                last_intent = "request"
            elif any(c in last_content for c in ["烦", "气", "累", "失望"]):
                last_intent = "complaint"

        # 风险信号（子串匹配）
        has_risk = any(sig in last_content for sig in self._risk_signals) if last_content else False

        # 情感趋势
        sentiment_trend = (context.sentiment or {}).get("trend", "unknown")

        # 时间/及时性特征
        timing = analyze_timing(messages)

        return {
            "last_intent": last_intent,
            "has_risk": has_risk,
            "last_content": last_content,
            "sentiment_trend": sentiment_trend,
            "timing": timing,
        }

    # ----------------------------------------------------------------
    # 智能融合
    # ----------------------------------------------------------------
    def _smart_merge(
        self,
        predictions: List[Tuple[Prediction, str]],
        ctx_features: Dict[str, Any],
    ) -> List[Prediction]:
        """v2.2.0 智能融合

        1. 规范化文本去重（合并相同文本）
        2. 加权平均 confidence（基于各预测器历史准确率 + 上下文适配）
        3. 多策略加成（被多种方法选中 → 提升）
        4. 上下文匹配（与最近对方消息相关 → 加权）
        5. 风险规避（风险场景下减分积极策略）
        """
        # 1. 按规范化文本分组
        groups: Dict[str, List[Tuple[Prediction, str]]] = defaultdict(list)
        for pred, source in predictions:
            key = self._normalize_text(pred.text)
            if not key:
                continue
            groups[key].append((pred, source))

        merged: List[Prediction] = []

        for norm_text, group in groups.items():
            # 展示文本取组内置信度最高的原文
            display_text = max(group, key=lambda x: x[0].confidence)[0].text.strip()
            sources = list(set(src for _, src in group))
            strategies = list(set(g[0].strategy for g in group))
            rationales = [g[0].rationale for g in group if g[0].rationale]

            # 2. 计算加权 confidence
            weighted_conf = self._compute_weighted_confidence(group, ctx_features)
            # 3. 多策略加成
            if len(strategies) >= 2:
                weighted_conf = min(0.95, weighted_conf + 0.05 * (len(strategies) - 1))
            if len(sources) >= 2:
                weighted_conf = min(0.95, weighted_conf + 0.03 * (len(sources) - 1))

            # 4. 上下文匹配
            context_bonus = self._context_match_bonus(display_text, ctx_features)
            weighted_conf = min(0.95, weighted_conf + context_bonus)

            # 5. 风险规避（仅在风险场景下）
            if ctx_features["has_risk"]:
                if self._is_aggressive(display_text):
                    weighted_conf *= 0.6  # 风险场景下减分积极策略

            # 6. 风格一致性
            if self._is_inconsistent(display_text, ctx_features):
                weighted_conf *= 0.85

            merged.append(Prediction(
                text=display_text,
                confidence=round(max(0.1, min(0.95, weighted_conf)), 3),
                strategy=",".join(sorted(set(strategies))),
                rationale=" | ".join(rationales[:3]),
                metadata={
                    "merge_count": len(group),
                    "strategies": list(strategies),
                    "sources": sources,
                    "context_bonus": round(context_bonus, 3),
                },
            ))

        return merged

    def _compute_weighted_confidence(
        self,
        group: List[Tuple[Prediction, str]],
        ctx_features: Dict[str, Any],
    ) -> float:
        """计算加权平均 confidence"""
        total_weight = 0.0
        weighted_conf = 0.0

        for pred, source in group:
            # 基础权重 = 预测器历史准确率（默认 0.5）
            base_w = self._accuracy.get(source, 0.5)
            # 上下文适配备加权
            if pred.strategy and pred.strategy.startswith("rule"):
                if ctx_features["has_risk"]:
                    # 风险场景下防守话术加成
                    if "defensive" in pred.metadata.get("source", ""):
                        base_w *= 1.5
                    elif "warmth" in pred.metadata.get("source", "") or \
                         "empathy" in pred.metadata.get("source", ""):
                        base_w *= 1.3
            elif pred.strategy == "rag":
                base_w *= 1.0
            elif pred.strategy == "mirofish":
                base_w *= 0.9

            total_weight += base_w
            weighted_conf += pred.confidence * base_w

        return weighted_conf / total_weight if total_weight > 0 else 0.5

    def _context_match_bonus(self, text: str, ctx_features: Dict[str, Any]) -> float:
        """根据上下文匹配度给 bonus（±0.10）"""
        bonus = 0.0
        last_content = ctx_features["last_content"]
        last_intent = ctx_features["last_intent"]
        sentiment_trend = ctx_features["sentiment_trend"]
        timing = ctx_features.get("timing")

        if not last_content:
            return bonus

        # 疑问句 → 我的回复应该回答或反问
        if last_intent == "question":
            if "？" in text or "?" in text or any(kw in text for kw in ["我", "你", "觉得", "看看"]):
                bonus += 0.05
        # 请求 → 我的回复应该承诺
        elif last_intent == "request":
            if any(kw in text for kw in ["好", "处理", "确认", "帮", "马上"]):
                bonus += 0.05
        # 抱怨 → 我的回复应该共情
        elif last_intent == "complaint":
            if any(kw in text for kw in ["懂", "辛苦", "怎么", "抱", "在"]):
                bonus += 0.05

        # 情感趋势适配
        if sentiment_trend == "down" and any(kw in text for kw in ["懂", "辛苦", "抱", "怎么"]):
            bonus += 0.05
        elif sentiment_trend == "up" and any(kw in text for kw in ["好", "一起", "开心", "珍惜"]):
            bonus += 0.05

        # 时间/及时性适配
        if timing is not None:
            urgency = getattr(timing, "urgency", "unknown")
            if urgency == "stale" and any(kw in text for kw in ["好久", "最近", "刚看到"]):
                bonus += 0.05
            elif urgency in ("immediate", "soon") and len(text) <= 15:
                bonus += 0.03
            if getattr(timing, "time_of_day", "") == "night" and any(
                kw in text for kw in ["休息", "睡", "晚安"]
            ):
                bonus += 0.03

        return bonus

    def _is_aggressive(self, text: str) -> bool:
        """判断是否为积极/对抗性话术"""
        aggressive_keywords = {"不", "滚", "不干", "不想", "不要", "算了", "随便", "懒得", "否决"}
        return any(kw in text for kw in aggressive_keywords)

    def _is_inconsistent(self, text: str, ctx_features: Dict[str, Any]) -> bool:
        """判断是否与上下文不一致"""
        # 风险场景下推卸责任型话术
        if ctx_features["has_risk"]:
            downplay = {"不是我的", "跟我无关", "你自己的", "怪我", "随便你"}
            if any(kw in text for kw in downplay):
                return True
        return False

    @staticmethod
    def _normalize_text(text: str) -> str:
        """规范化文本用于去重比较：去空白/标点、转小写"""
        return re.sub(r"[\s，。！？、；：,.!?;:'\"“”‘’~…—\-·()（）\[\]【】]+", "", text or "").lower()
