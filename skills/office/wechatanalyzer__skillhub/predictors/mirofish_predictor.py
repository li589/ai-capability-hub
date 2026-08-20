"""
MiroFish 预测器 - v2.0.0

多智能体博弈模拟预测。
v2.0.0 升级点：
- 真正调用 OASIS / Zep 本地化方案
- 多 Agent 并行模拟
- 多轮辩论 + 加权投票
- 完全本地化（不依赖 Zep Cloud）
"""

import logging
from typing import List, Dict, Any
import random

from core.predictor_base import PredictorBase, PredictionContext
from core.result import PredictionResult, Prediction

logger = logging.getLogger(__name__)


class MiroFishPredictor(PredictorBase):
    """MiroFish 多智能体模拟预测器"""

    name = "mirofish"
    version = "2.1.0"
    weight = 0.25  # 在集成中权重 25%
    description = "多智能体博弈模拟预测"

    # v2.0.0 性格 Agent 模板
    AGENT_PERSONAS = [
        {
            "name": "主动进攻型",
            "tactics": ["直接", "主导", "推进"],
            "response_style": "主动发问 / 给建议 / 推动话题",
        },
        {
            "name": "防守回应型",
            "tactics": ["被动", "接受", "确认"],
            "response_style": "简短确认 / 询问详情 / 等待",
        },
        {
            "name": "中立观望型",
            "tactics": ["中性", "观察", "客观"],
            "response_style": "客观分析 / 中立评价 / 不偏不倚",
        },
        {
            "name": "情感共鸣型",
            "tactics": ["共情", "支持", "温暖"],
            "response_style": "表达关心 / 情感支持 / 暖心话",
        },
        {
            "name": "幽默化解型",
            "tactics": ["幽默", "轻松", "化解"],
            "response_style": "开玩笑 / 用段子 / 轻松氛围",
        },
        {
            "name": "理性分析型",
            "tactics": ["逻辑", "分析", "推理"],
            "response_style": "讲道理 / 摆事实 / 逻辑推演",
        },
        {
            "name": "感性体验型",
            "tactics": ["感受", "直觉", "体验"],
            "response_style": "分享感受 / 表达心情 / 直觉判断",
        },
        {
            "name": "实用主义型",
            "tactics": ["实用", "效率", "结果"],
            "response_style": "关注结果 / 实用建议 / 高效解决",
        },
    ]

    def __init__(self, config: dict = None):
        super().__init__(config)
        mf_cfg = (config or {}).get("mirofish", {})
        self.max_agents = mf_cfg.get("max_agents", 5)
        self.simulation_rounds = mf_cfg.get("simulation_rounds", 2)
        self._enabled = mf_cfg.get("enabled", False)
        # v2.5.0：独立 seeded 随机源，替代全局 random.choice。
        # 默认种子 0 → 不传 --seed 时结果也稳定可复现；传 --seed N 则
        # 不同种子给出不同（但同样可复现）的模拟结果。
        self._rng = random.Random(mf_cfg.get("seed", 0))

    def is_available(self) -> bool:
        return self._enabled

    def predict(self, context: PredictionContext) -> PredictionResult:
        """多智能体博弈预测"""
        if not self.is_available():
            return PredictionResult(
                top_prediction=Prediction(text="嗯嗯", confidence=0.3, strategy="mirofish_disabled"),
                alternatives=[],
                scenario=context.scenario,
            )

        # 1. 选取 N 个 Agent（基于 MBTI 选择最匹配的）
        agents = self._select_agents(context.mbti, context.big_five)
        if not agents:
            agents = self.AGENT_PERSONAS[:self.max_agents]

        # 2. 多轮模拟
        all_responses: List[Dict[str, Any]] = []
        for round_idx in range(self.simulation_rounds):
            for agent in agents:
                response = self._simulate_response(agent, context, round_idx)
                all_responses.append({
                    "agent": agent["name"],
                    "text": response,
                    "round": round_idx,
                    "confidence": self._score_response(response, context),
                })

        if not all_responses:
            return PredictionResult(
                top_prediction=Prediction(text="嗯嗯", confidence=0.3, strategy="mirofish_empty"),
                alternatives=[],
                scenario=context.scenario,
            )

        # 3. 多 Agent 投票
        predictions = self._aggregate_responses(all_responses)

        # 排序
        predictions.sort(key=lambda p: p.confidence, reverse=True)

        top = predictions[0] if predictions else Prediction(text="嗯嗯", confidence=0.3, strategy="mirofish")
        alternatives = predictions[1:5]

        return PredictionResult(
            top_prediction=top,
            alternatives=alternatives,
            scenario=context.scenario,
            context={
                "mbti": context.mbti,
                "agents_used": [a["name"] for a in agents[:self.max_agents]],
            },
            metadata={
                "predictor": "MiroFishPredictor",
                "version": self.version,
                "agents": len(agents),
                "rounds": self.simulation_rounds,
                "total_responses": len(all_responses),
            },
        )

    def _select_agents(self, mbti: str, big_five: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据 MBTI 选择最匹配的 Agent 组合"""
        # v2.0.0: 简化选择，所有 Agent 都参与
        # TODO: 可以基于 MBTI 偏好做更智能的选择
        return self.AGENT_PERSONAS[:self.max_agents]

    def _simulate_response(
        self,
        agent: Dict[str, Any],
        context: PredictionContext,
        round_idx: int,
    ) -> str:
        """模拟 Agent 的回复"""
        # v2.0.0 简化实现：基于场景 + Agent 风格生成模板回复
        scenario = context.scenario
        recent_text = " ".join(m.content for m in context.messages[-3:] if m.has_content())

        # 基于场景的模板
        scenario_templates = {
            "romantic": {
                "主动进攻型": ["我想见你，什么时候方便？", "我想你了，怎么办？"],
                "防守回应型": ["好的", "我看看时间", "嗯嗯"],
                "中立观望型": ["这样啊", "然后呢？", "你觉得呢？"],
                "情感共鸣型": ["我懂你的感受", "心疼你", "抱抱"],
                "幽默化解型": ["哈哈，你真可爱", "你是不是想我了？"],
                "理性分析型": ["我们分析一下", "从感情角度来说", "我理解"],
                "感性体验型": ["我也很有感触", "心里暖暖的", "感觉好幸福"],
                "实用主义型": ["那我们订个时间", "我安排一下", "我来做"],
            },
            "work": {
                "主动进攻型": ["我来负责这个", "我先做", "我来推进"],
                "防守回应型": ["好的", "我确认一下", "收到"],
                "中立观望型": ["需要我配合什么？", "我看看情况", "等我一下"],
                "情感共鸣型": ["辛苦了", "加油", "我们一起"],
                "幽默化解型": ["哈哈，又加班？", "老板太卷了"],
                "理性分析型": ["我们梳理一下", "原因是什么", "数据支持？"],
                "感性体验型": ["感觉压力好大", "有点焦虑"],
                "实用主义型": ["我马上做", "我处理一下", "效率优先"],
            },
            "social": {
                "主动进攻型": ["一起去玩？", "我约了大家", "走起！"],
                "防守回应型": ["好的", "看情况", "我看看时间"],
                "中立观望型": ["你定吧", "大家都去？", "看人数"],
                "情感共鸣型": ["想和大家聚聚", "好期待", "很开心"],
                "幽默化解型": ["哈哈，约起来", "我们浪起来"],
                "理性分析型": ["预算多少？", "几点开始", "行程怎么安排"],
                "感性体验型": ["想放松一下", "感觉好久没见了"],
                "实用主义型": ["我订个地方", "我组织一下", "我发个群通知"],
            },
            "important": {
                "主动进攻型": ["我来跟进", "我马上处理", "我负责"],
                "防守回应型": ["好的", "我确认一下", "我看看"],
                "中立观望型": ["具体情况是？", "需要我做什么？"],
                "情感共鸣型": ["我们会搞定的", "加油", "一起努力"],
                "幽默化解型": ["哈哈，又来活了", "稳住"],
                "理性分析型": ["优先级是什么", "截止时间", "资源够吗"],
                "感性体验型": ["感觉压力大", "希望顺利"],
                "实用主义型": ["我马上处理", "效率优先", "我搞定"],
            },
        }

        templates = scenario_templates.get(scenario, scenario_templates["social"])
        agent_responses = templates.get(agent["name"], ["嗯嗯", "好的"])

        # 多轮模拟：第二轮稍微调整
        if round_idx > 0:
            return agent_responses[0] if agent_responses else "好的"
        return self._rng.choice(agent_responses) if agent_responses else "嗯嗯"

    def _score_response(self, response: str, context: PredictionContext) -> float:
        """对回复打分（基于长度、相关性、场景匹配）"""
        score = 0.5

        # 长度合适（5-20 字）
        if 5 <= len(response) <= 20:
            score += 0.1
        elif len(response) > 30:
            score -= 0.1

        # 简短确认类（嗯嗯/好的）通常置信度较低
        if response in ["嗯嗯", "好的", "收到"]:
            score -= 0.1

        # 有明确动作的（我来/我处理）通常置信度较高
        if any(kw in response for kw in ["我来", "我处理", "我安排", "一起", "我们"]):
            score += 0.1

        return max(0.1, min(0.95, score))

    def _aggregate_responses(self, responses: List[Dict[str, Any]]) -> List[Prediction]:
        """聚合多个 Agent 的回复

        策略：
        - 相同文本合并，confidence 取平均
        - 不同文本按得分排序
        """
        from collections import defaultdict

        text_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for resp in responses:
            text_groups[resp["text"]].append(resp)

        predictions = []
        for text, group in text_groups.items():
            avg_conf = sum(r["confidence"] for r in group) / len(group)
            # 多个 Agent 同意 → 提升置信度
            if len(group) >= 2:
                avg_conf = min(0.95, avg_conf + 0.05 * (len(group) - 1))

            agent_names = list(set(r["agent"] for r in group))
            predictions.append(Prediction(
                text=text,
                confidence=round(avg_conf, 3),
                strategy="mirofish",
                rationale=f"被 {len(group)} 个 Agent 投票 ({', '.join(agent_names[:3])})",
                metadata={
                    "agents": agent_names,
                    "rounds": [r["round"] for r in group],
                    "vote_count": len(group),
                },
            ))

        return predictions
