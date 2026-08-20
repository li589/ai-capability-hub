"""
推演分析器 - v2.2.0 (新增)

5 大推演能力：
    1. 行业/话题趋势推演：基于词频 + 时间窗口，提炼上升/下降话题
    2. 对手行为推演：基于对话模式预测对方倾向（冷漠/配合/对抗）
    3. 情感轨迹推演：把对话切分为 N 个时间窗口，预测下一窗口情感倾向
    4. 风险演化推演：从近 N 条消息提取风险信号，预测是否会升级
    5. 对话走向预测：当前最强场景 + 主动率 → 推断走向（升温/降温/僵持）

所有推演都是基于规则和历史模式的启发式估计，非定论。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult
from core.utils import tokenize, HAS_JIEBA


class InferenceAnalyzer(AnalyzerBase):
    """推演分析器：5 大子推演能力"""

    name = "inference"
    version = "2.2.0"
    description = "5 大推演能力：话题趋势/对手行为/情感轨迹/风险演化/对话走向"

    # 升温词（更可能走向亲密/合作/修复的对话）
    WARMING_WORDS = {
        "喜欢", "感谢", "谢谢", "好的", "同意", "达成", "可以", "希望",
        "期待", "开心", "哈哈", "太好了", "一起", "愿意", "支持",
        "爱", "想你", "想见", "见面", "约定", "下次",
    }
    # 降温词（关系疏远/对抗/破裂）
    COOLING_WORDS = {
        "算了", "随便", "无所谓", "不必", "不用", "不要", "再见",
        "累", "失望", "算了", "取消", "不", "算了", "没意思", "拉倒",
        "失望", "算了", "对吧", "行吧", "就这样",
    }
    # 对抗升级词
    CONFRONTATION = {
        "凭什么", "烦死", "恶心", "滚", "滚蛋", "你算", "你懂什么",
        "不可能", "做梦", "骗人", "虚伪", "装", "得了吧",
        "幼稚", "废话", "搞笑", "讽刺",
    }

    # 风险升级信号（与 risk_analyzer 配合）
    ESCALATION_SIGNALS = {
        "high": {
            "威胁", "拉黑", "删除", "报警", "起诉", "曝光", "找人",
            "动手", "打死", "毁了", "报复",
        },
        "medium": {
            "过分", "太过分", "有完没完", "别再", "最后一次",
            "无赖", "混蛋", "下流", "无耻",
        },
    }

    # 行为风格词典（推断对方当下状态）
    OPPONENT_BEHAVIORS = {
        "冷漠型": {"信号": ["哦", "嗯", "随便", "行", "可以", "好的"], "权重": 0},
        "配合型": {"信号": ["好的", "可以", "没问题", "同意", "一起", "乐意"], "权重": 0},
        "对抗型": {"信号": ["不", "不要", "不可能", "凭什么", "烦", "滚", "废话"], "权重": 0},
        "理性型": {"信号": ["所以", "那么", "分析", "考虑", "建议", "方案", "认为"], "权重": 0},
        "情绪型": {"信号": ["!", "？", "气死", "伤", "难过", "开心", "激动", "崩溃"], "权重": 0},
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 5
        # v2.5.0：行为信号集合预构建（原实现在每条消息 × 每种行为的
        # 内层循环里反复 set() 重建，纯浪费）
        self._behavior_signals = {
            bt: set(info["信号"]) for bt, info in self.OPPONENT_BEHAVIORS.items()
        }

    def validate(self, messages: List[Message]) -> bool:
        return len(messages) >= self.min_messages

    # ----------------------------------------------------------------
    # 主入口
    # ----------------------------------------------------------------
    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        # 各子推演
        topic_trends = self._infer_topic_trends(messages)
        opponent = self._infer_opponent_behavior(messages)
        sentiment_trajectory = self._infer_sentiment_trajectory(messages)
        risk_escalation = self._infer_risk_escalation(messages)
        conversation_trajectory = self._infer_conversation_trajectory(
            messages, opponent, sentiment_trajectory
        )

        # 综合判定（主分数 = 各子推演加权，0-100）
        # 权重：风险演化 35 / 对手行为 25 / 情感轨迹 20 / 对话走向 15 / 话题趋势 5
        safety_score = 100 - risk_escalation["escalation_score"]
        composite = (
            safety_score * 0.35
            + opponent["safety_score"] * 0.25
            + sentiment_trajectory["next_stability"] * 0.20
            + conversation_trajectory["stability_score"] * 0.15
            + topic_trends["consistency_score"] * 0.05
        )

        # 置信度：样本量与时间跨度
        confidence = self._compute_confidence(messages)

        # 给出综合结论
        overall_verdict = self._overall_verdict(
            composite, risk_escalation, opponent, conversation_trajectory
        )

        return AnalysisResult(
            analyzer_name=self.name,
            score=round(composite, 2),
            confidence=round(confidence, 1),
            details={
                "overall_verdict": overall_verdict,
                "topic_trends": topic_trends,
                "opponent_behavior": opponent,
                "sentiment_trajectory": sentiment_trajectory,
                "risk_escalation": risk_escalation,
                "conversation_trajectory": conversation_trajectory,
                "weights": {
                    "risk_escalation": 0.35,
                    "opponent_behavior": 0.25,
                    "sentiment_trajectory": 0.20,
                    "conversation_trajectory": 0.15,
                    "topic_trends": 0.05,
                },
            },
            metadata={
                "analyzer": "InferenceAnalyzer",
                "version": self.version,
                "sample_size": len(messages),
                "has_jieba": HAS_JIEBA,
            },
        )

    # ----------------------------------------------------------------
    # 1. 话题趋势推演
    # ----------------------------------------------------------------
    def _infer_topic_trends(self, messages: List[Message]) -> Dict[str, Any]:
        """切分时间窗口，对比早/晚期话题词频 → 上升/下降/稳定话题清单。"""
        valid = [m for m in messages if m.timestamp and m.content]
        if len(valid) < 4:
            return {
                "available": False,
                "reason": "消息数 < 4 或缺少时间戳",
                "rising_topics": [],
                "falling_topics": [],
                "stable_topics": [],
                "consistency_score": 50.0,
            }

        valid.sort(key=lambda m: m.timestamp)
        mid = len(valid) // 2
        early_msgs = valid[:mid]
        late_msgs = valid[mid:]

        early_tokens = self._count_tokens(early_msgs)
        late_tokens = self._count_tokens(late_msgs)

        # 计算每个词的变化率（late - early）/ early
        all_topics = set(early_tokens.keys()) | set(late_tokens.keys())
        changes: Dict[str, float] = {}
        for topic in all_topics:
            early_count = early_tokens.get(topic, 0)
            late_count = late_tokens.get(topic, 0)
            # 用对数平滑避免 0 误差
            if early_count == 0 and late_count > 0:
                changes[topic] = 1.0  # 新出现 = 上升 1.0
            elif early_count == 0:
                continue
            else:
                changes[topic] = (late_count - early_count) / early_count

        # 排序取最显著的话题
        sorted_topics = sorted(changes.items(), key=lambda x: x[1], reverse=True)
        rising = [{"topic": t, "growth_rate": round(c, 2)} for t, c in sorted_topics[:5] if c > 0]
        falling = [
            {"topic": t, "decline_rate": round(-c, 2)}
            for t, c in sorted([(t, c) for t, c in sorted_topics if c < 0], key=lambda x: x[1])[:5]
        ]
        stable = [
            {"topic": t, "growth_rate": round(c, 2)}
            for t, c in sorted_topics if -0.1 <= c <= 0.1
        ][:5]

        # 一致性评分：上升话题占比越少、变化越温和，关系越稳定
        total_topics = len(all_topics)
        rising_ratio = len(rising) / total_topics if total_topics else 0
        consistency = max(0, 100 - rising_ratio * 100)

        return {
            "available": True,
            "early_window_count": len(early_msgs),
            "late_window_count": len(late_msgs),
            "rising_topics": rising,
            "falling_topics": falling,
            "stable_topics": stable,
            "consistency_score": round(consistency, 1),
        }

    # ----------------------------------------------------------------
    # 2. 对手/对方行为推演
    # ----------------------------------------------------------------
    def _infer_opponent_behavior(self, messages: List[Message]) -> Dict[str, Any]:
        """基于对方最新消息风格，判断其当前行为倾向。"""
        # 取对方（is_self=False）的最近 20 条消息
        other_msgs = [m for m in messages if not m.is_self()]
        recent = other_msgs[-20:]

        if not recent:
            return {
                "available": False,
                "reason": "无对方消息",
                "dominant_behavior": "unknown",
                "behavior_distribution": {},
                "safety_score": 50.0,
            }

        # 行为类型计数
        behavior_counts = {bt: 0 for bt in self.OPPONENT_BEHAVIORS}
        for msg in recent:
            content = msg.content or ""
            tokens = set(tokenize(content, use_jieba=True))
            for bt, signal_set in self._behavior_signals.items():
                if tokens & signal_set:
                    behavior_counts[bt] += 1

        # 找主导
        total_signals = sum(behavior_counts.values())
        distribution = (
            {bt: round(c / max(total_signals, 1), 3) for bt, c in behavior_counts.items()}
            if total_signals else {bt: 0 for bt in behavior_counts}
        )
        dominant = max(behavior_counts, key=behavior_counts.get) if total_signals else "unknown"

        # 安全性评分：对抗型越低，安全性越高
        confrontation_pct = distribution.get("对抗型", 0)
        safety = max(0, 100 - confrontation_pct * 150)  # 对抗型 67% ≈ 0 分

        return {
            "available": True,
            "recent_count": len(recent),
            "dominant_behavior": dominant,
            "behavior_distribution": distribution,
            "safety_score": round(safety, 1),
            "evidence": {
                bt: [
                    {"preview": msg.content[:40], "timestamp": msg.timestamp.isoformat() if msg.timestamp else None}
                    for msg in recent
                    if any(sig in (msg.content or "") for sig in signals)
                ][:2]
                for bt, signals in self._behavior_signals.items()
                if any(sig in (msg.content or "") for msg in recent for sig in signals)
            },
        }

    # ----------------------------------------------------------------
    # 3. 情感轨迹推演
    # ----------------------------------------------------------------
    def _infer_sentiment_trajectory(self, messages: List[Message]) -> Dict[str, Any]:
        """分窗口统计情绪词，预测下一窗口的倾向。"""
        valid = [m for m in messages if m.content]
        if len(valid) < 6:
            return {
                "available": False,
                "reason": "消息数 < 6",
                "windows": [],
                "trend": "unknown",
                "next_stability": 50.0,
            }

        # 按时间分 3 个窗口（如果时间戳可用），否则按消息数等分
        valid_sorted = sorted(valid, key=lambda m: m.timestamp or datetime.min)
        n = len(valid_sorted)
        third = max(1, n // 3)
        windows = [valid_sorted[:third], valid_sorted[third:2*third], valid_sorted[2*third:]]

        sentiment_series = []
        for window in windows:
            tokens = self._count_tokens(window)
            warmth = sum(tokens.get(w, 0) for w in self.WARMING_WORDS)
            cool = sum(tokens.get(w, 0) for w in self.COOLING_WORDS)
            total = warmth + cool
            sentiment_series.append({
                "window_size": len(window),
                "warming_signal": warmth,
                "cooling_signal": cool,
                "warmth_score": round(warmth / max(total, 1), 3),
            })

        # 推导趋势
        if len(sentiment_series) >= 2:
            last_two = [s["warmth_score"] for s in sentiment_series[-2:]]
            delta = last_two[1] - last_two[0]
            if delta > 0.1:
                trend = "warming"
            elif delta < -0.1:
                trend = "cooling"
            else:
                trend = "stable"
        else:
            trend = "unknown"
            delta = 0.0

        # 下一窗口稳定性：当前升温 → 略微降温（正常波动）；否则维持
        if trend == "warming":
            predicted = 70.0  # 仍较稳定
        elif trend == "cooling":
            predicted = 40.0  # 需要关注
        else:
            predicted = 60.0  # 维持

        return {
            "available": True,
            "windows": sentiment_series,
            "trend": trend,
            "delta_recent": round(delta, 3),
            "prediction": (
                f"下一窗口情感倾向预计为 {trend}"
                + ("（建议：主动表态巩固关系）" if trend == "warming" else "")
                + ("（建议：及时化解，避免恶化）" if trend == "cooling" else "")
                + ("（建议：保持现状）" if trend == "stable" else "")
            ),
            "next_stability": predicted,
        }

    # ----------------------------------------------------------------
    # 4. 风险演化推演
    # ----------------------------------------------------------------
    def _infer_risk_escalation(self, messages: List[Message]) -> Dict[str, Any]:
        """从近 N 条消息提取风险信号，预测是否会升级。"""
        # 只看最近的 30 条（风险信号更可能在近期）
        recent = [m for m in messages[-30:] if m.content]

        if not recent:
            return {
                "available": False,
                "reason": "无消息可分析",
                "current_signals": [],
                "escalation_probability": 0.0,
                "escalation_score": 0.0,
                "predicted_trajectory": "stable",
            }

        # 检测到的信号
        high_hits = []
        medium_hits = []

        for msg in recent:
            content = msg.content or ""
            tokens = tokenize(content, use_jieba=True)
            for hit in self.ESCALATION_SIGNALS["high"]:
                if hit in content:
                    high_hits.append({
                        "sender": msg.sender,
                        "signal": hit,
                        "preview": content[:80],
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    })
            for hit in self.ESCALATION_SIGNALS["medium"]:
                if hit in content:
                    medium_hits.append({
                        "sender": msg.sender,
                        "signal": hit,
                        "preview": content[:80],
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    })

        # 升级概率：高危信号权重高
        score = (
            min(len(high_hits) * 25, 100) * 0.7
            + min(len(medium_hits) * 8, 100) * 0.3
        )
        score = min(score, 100)

        # 推导轨迹
        if score >= 60:
            trajectory = "high_escalation_risk"
            prob = 0.75
        elif score >= 30:
            trajectory = "moderate_escalation_risk"
            prob = 0.5
        elif score >= 10:
            trajectory = "mild_warning"
            prob = 0.25
        else:
            trajectory = "stable"
            prob = 0.05

        return {
            "available": True,
            "window": f"最近 {len(recent)} 条消息",
            "current_signals": {
                "high": high_hits,
                "medium": medium_hits,
            },
            "escalation_probability": prob,
            "escalation_score": round(score, 1),
            "predicted_trajectory": trajectory,
            "recommendation": self._risk_recommendation(trajectory),
        }

    def _risk_recommendation(self, trajectory: str) -> str:
        return {
            "high_escalation_risk": "⚫ 高危：建议立即降温、冷处理或寻求第三方调解",
            "moderate_escalation_risk": "🔴 中风险：建议主动暂停争论，等待情绪稳定",
            "mild_warning": "🟡 轻微警示：建议减少对抗性表达，避免激化",
            "stable": "🟢 当前信号稳定，保持现状即可",
        }.get(trajectory, "")

    # ----------------------------------------------------------------
    # 5. 对话走向预测
    # ----------------------------------------------------------------
    def _infer_conversation_trajectory(
        self,
        messages: List[Message],
        opponent: Dict,
        sentiment: Dict,
    ) -> Dict[str, Any]:
        """综合对方行为 + 情感轨迹 + 主动率 → 推断对话走向。"""
        # 主动率
        initiations = {"self": 0, "other": 0}
        last_sender = None
        last_ts = None
        for msg in messages:
            if not msg.timestamp:
                continue
            is_self = msg.is_self()
            if last_sender is None or last_sender != msg.sender:
                gap = (msg.timestamp - last_ts).total_seconds() if last_ts else 0
                if last_ts is None or gap > 7200:
                    if is_self:
                        initiations["self"] += 1
                    else:
                        initiations["other"] += 1
            last_sender = msg.sender
            last_ts = msg.timestamp

        total = initiations["self"] + initiations["other"]
        self_pct = initiations["self"] / total * 100 if total else 50.0

        # 状态分类
        if self_pct >= 65:
            initiation_pattern = "self_dominant"
        elif self_pct <= 35:
            initiation_pattern = "other_dominant"
        else:
            initiation_pattern = "balanced"

        # 综合稳定性
        opponent_safety = opponent.get("safety_score", 50)
        sentiment_stability = sentiment.get("next_stability", 50)

        stability = (opponent_safety + sentiment_stability) / 2

        # 走向预测
        opponent_behavior = opponent.get("dominant_behavior", "unknown")
        sentiment_trend = sentiment.get("trend", "unknown")

        if sentiment_trend == "cooling" and opponent_behavior in ("对抗型", "冷漠型"):
            trajectory = "deteriorating"
            advice = "⚠️ 关系在恶化，建议主动降温或暂停对话"
        elif sentiment_trend == "warming" and opponent_behavior in ("配合型", "理性型"):
            trajectory = "improving"
            advice = "✅ 关系在升温，建议保持当前节奏"
        elif initiation_pattern == "self_dominant" and stability < 50:
            trajectory = "burning_out_self"
            advice = "⚠️ 你主动太多，对面反应冷淡，建议降低主动率"
        elif sentiment_trend == "stable" and opponent_behavior == "理性型":
            trajectory = "stable_functional"
            advice = "🟢 当前是功能性稳定状态，可继续"
        else:
            trajectory = "stalemate"
            advice = "🟡 处于僵持状态，可主动打破僵局"

        return {
            "initiation_pattern": initiation_pattern,
            "self_initiation_pct": round(self_pct, 1),
            "stability_score": round(stability, 1),
            "predicted_trajectory": trajectory,
            "advice": advice,
            "factors": {
                "opponent_behavior": opponent_behavior,
                "sentiment_trend": sentiment_trend,
                "self_initiation": self_pct,
            },
        }

    # ----------------------------------------------------------------
    # 综合结论
    # ----------------------------------------------------------------
    def _overall_verdict(
        self,
        composite: float,
        risk: Dict,
        opponent: Dict,
        trajectory: Dict,
    ) -> Dict[str, str]:
        if composite >= 80:
            label, advice = "🟢 健康", "整体对话状态健康，可继续当前互动"
        elif composite >= 60:
            label, advice = "🟡 观察", "整体状态尚可，但有 1-2 项需要关注"
        elif composite >= 40:
            label, advice = "🟠 警示", "出现明显风险信号，建议主动调整"
        else:
            label, advice = "🔴 危险", "高风险，建议冷处理或寻求外部协助"

        return {
            "label": label,
            "advice": advice,
            "composite": round(composite, 1),
        }

    def _compute_confidence(self, messages: List[Message]) -> float:
        n = len(messages)
        ts_count = sum(1 for m in messages if m.timestamp)
        ts_ratio = ts_count / n if n else 0

        size_factor = min(n / 30, 1.0) * 50  # 30+ = 50 分
        time_factor = ts_ratio * 50            # 时间戳完整度 = 50 分
        return min(size_factor + time_factor, 100)

    # ----------------------------------------------------------------
    # 工具
    # ----------------------------------------------------------------
    def _count_tokens(self, messages: List[Message]) -> Counter:
        """统计所有消息的 token 词频"""
        counter: Counter = Counter()
        for msg in messages:
            for token in tokenize(msg.content or "", use_jieba=True):
                counter[token] += 1
        return counter
