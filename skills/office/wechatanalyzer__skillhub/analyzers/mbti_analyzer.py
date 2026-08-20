"""
MBTI 人格分析器 - v2.0.0

升级点：
- 维度差距 + 样本量综合置信度算法
- 4 维独立判定，输出稳定性评分
- 支持 jieba 分词后的关键词识别
"""

import math
from typing import List, Dict, Any

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult
from core.utils import tokenize, HAS_JIEBA


class MBTIAnalyzer(AnalyzerBase):
    """MBTI 16 型人格推断"""

    name = "mbti"
    version = "2.1.0"
    description = "基于聊天风格推断 MBTI 16 型人格"

    # v2.0.0 扩充的 MBTI 关键词库（覆盖度 +30%）
    KEYWORDS = {
        "E": {  # 外向
            "energy": ["我们", "大家", "一起", "聚会", "朋友", "社交", "热闹",
                       "聊天", "有趣", "参加", "活动", "派对", "群体", "共享",
                       "讨论", "互动", "沟通", "对话", "交流", "分享", "众人"],
            "phrases": ["我喜欢和大家一起", "我们一起", "找朋友", "出去玩", "出来聚聚"],
        },
        "I": {  # 内向
            "energy": ["自己", "独处", "安静", "思考", "看书", "一个人", "独自",
                       "内向", "个人", "单独", "宅", "独享", "私密", "个人空间",
                       "独来独往", "一个人待", "自己一个人"],
            "phrases": ["我喜欢一个人", "想一个人", "独自一人", "自己待着"],
        },
        "S": {  # 实感
            "sensing": ["具体", "实际", "事实", "数据", "真的", "确定", "发生",
                        "做过", "经验", "细节", "步骤", "流程", "方法", "技术",
                        "操作", "实现", "执行", "落实", "具体点", "实际点"],
            "phrases": ["具体怎么", "实际是", "事实上", "我做过", "细节是"],
        },
        "N": {  # 直觉
            "sensing": ["可能", "也许", "感觉", "想象", "未来", "如果", "大概",
                        "觉得", "似乎", "或许", "憧憬", "愿景", "概念", "想法",
                        "灵感", "直觉", "创新", "创意", "发明", "假设", "推想"],
            "phrases": ["感觉会", "可能吧", "也许会", "我想象", "假如"],
        },
        "T": {  # 思维
            "thinking": ["逻辑", "道理", "应该", "分析", "理性", "原因", "对错",
                         "公平", "原则", "推理", "论证", "判断", "客观", "利弊",
                         "权衡", "效率", "最优", "解决方案", "问题分析", "数据支持"],
            "phrases": ["从逻辑上", "客观讲", "分析一下", "原因是什么"],
        },
        "F": {  # 情感
            "thinking": ["感觉", "觉得", "情感", "在乎", "关心", "重要", "理解",
                         "感受", "心意", "心情", "心情好", "情绪", "感受",
                         "感受", "心疼", "舍不得", "感动", "温暖", "暖心", "人心"],
            "phrases": ["我理解", "我感受", "感同身受", "心里", "心里话"],
        },
        "J": {  # 判断
            "judging": ["计划", "决定", "安排", "应该", "必须", "完成", "准时",
                        "组织", "结构", "deadline", "截止", "目标", "任务",
                        "清单", "规划", "方案", "制定", "执行", "期限", "按时"],
            "phrases": ["按计划", "需要安排", "必须做", "我决定了", "先计划"],
        },
        "P": {  # 感知
            "judging": ["随性", "看情况", "再说", "到时候", "灵活", "慢慢来",
                        "随意", "随心", "随机", "随机应变", "即兴", "随时",
                        "慢慢", "不急", "先这样", "看心情", "看状态"],
            "phrases": ["到时候再说", "看情况", "随意", "不着急"],
        },
    }

    MBTI_NAMES = {
        "INTJ": ("建筑师", "独立思考者，战略性强，追求长远目标"),
        "INTP": ("逻辑学家", "理性分析者，好奇心强，喜欢抽象思考"),
        "ENTJ": ("指挥官", "果断领导型，决策力强，注重效率"),
        "ENTP": ("辩论家", "思维敏捷，善于创新，喜欢挑战传统"),
        "INFJ": ("倡导者", "理想主义者，洞察力强，追求意义"),
        "INFP": ("调停者", "浪漫主义者，善解人意，重视内心价值"),
        "ENFJ": ("主人公", "热情领导者，有感染力，关注他人成长"),
        "ENFP": ("竞选者", "充满激情，创造力强，热爱可能性"),
        "ISTJ": ("物流师", "尽职尽责，稳重可靠，尊重传统"),
        "ISFJ": ("守护者", "体贴细心，默默付出，重视和谐"),
        "ESTJ": ("总经理", "执行能力强，管理风格，务实有序"),
        "ESFJ": ("供给者", "热情助人，人际导向，重视合作"),
        "ISTP": ("鉴赏家", "实际动手，灵活变通，冷静理性"),
        "ISFP": ("艺术家", "敏感细腻，美感丰富，活在当下"),
        "ESTP": ("企业家", "行动导向，适应力强，注重结果"),
        "ESFP": ("表演者", "活泼开朗，享受当下，富有感染力"),
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 10  # 最少消息数

    def validate(self, messages: List[Message]) -> bool:
        """至少需要 10 条对方消息才分析"""
        other_count = sum(1 for m in messages if m.is_other() and m.has_content())
        return other_count >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        """分析 MBTI

        Returns:
            AnalysisResult with details={
                'type': 'ENFP',
                'name': '竞选者',
                'description': '...',
                'dimension_scores': {'E': 5, 'I': 2, ...},
                'dim_probabilities': {'EI': 0.71, 'SN': 0.65, ...},
                'stability': 0.85
            }
        """
        # 提取对方消息
        other_messages = [m for m in messages if m.is_other() and m.has_content()]

        # 分词 + 词频统计
        token_counts: Dict[str, int] = {}
        for msg in other_messages:
            tokens = tokenize(msg.content, use_jieba=True)
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

        # 8 个维度的得分
        dim_scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}

        for dim, categories in self.KEYWORDS.items():
            for cat_name, words in categories.items():
                for word in words:
                    # 关键词 + 短语都计数
                    if word in token_counts:
                        # 单字词权重低（避免误判）
                        weight = 1 if len(word) >= 2 else 0.5
                        dim_scores[dim] += token_counts[word] * weight

        # 维度胜出 + 归一化概率
        preference = {
            "EI": "E" if dim_scores["E"] >= dim_scores["I"] else "I",
            "SN": "S" if dim_scores["S"] >= dim_scores["N"] else "N",
            "TF": "T" if dim_scores["T"] >= dim_scores["F"] else "F",
            "JP": "J" if dim_scores["J"] >= dim_scores["P"] else "P",
        }
        mbti_type = preference["EI"] + preference["SN"] + preference["TF"] + preference["JP"]

        # 维度概率（0-1）
        def safe_div(a, b):
            return a / (a + b) if (a + b) > 0 else 0.5

        dim_probs = {
            "EI": safe_div(dim_scores["E"], dim_scores["I"]),
            "SN": safe_div(dim_scores["S"], dim_scores["N"]),
            "TF": safe_div(dim_scores["T"], dim_scores["F"]),
            "JP": safe_div(dim_scores["J"], dim_scores["P"]),
        }

        # 综合置信度
        confidence = self._compute_confidence(dim_probs, len(other_messages))

        # 稳定性（如果历史结果存在，输出稳定性评分）
        stability = self._compute_stability(mbti_type, dim_probs, other_messages)

        name, desc = self.MBTI_NAMES.get(mbti_type, ("未知", "样本不足以推断"))

        # 维度描述
        dim_desc_map = {
            "EI": "外向" if preference["EI"] == "E" else "内向",
            "SN": "实感" if preference["SN"] == "S" else "直觉",
            "TF": "思维" if preference["TF"] == "T" else "情感",
            "JP": "判断" if preference["JP"] == "J" else "感知",
        }

        return AnalysisResult(
            analyzer_name=self.name,
            score=confidence,
            confidence=round(confidence, 1),
            details={
                "type": mbti_type,
                "name": name,
                "description": desc,
                "dim_description": " | ".join(f"{k}: {v}" for k, v in dim_desc_map.items()),
                "dimension_scores": dim_scores,
                "dim_probabilities": {k: round(v, 3) for k, v in dim_probs.items()},
                "preference": preference,
                "stability": round(stability, 3),
                "sample_size": len(other_messages),
            },
            metadata={
                "analyzer": "MBTIAnalyzer",
                "version": self.version,
                "has_jieba": HAS_JIEBA,
            },
        )

    def _compute_confidence(self, dim_probs: Dict[str, float], sample_size: int) -> float:
        """v2.0.0 新算法：维度差距 + 样本量

        dim_probs: 每对维度的胜出概率（0-1）
        sample_size: 对方消息数
        """
        # 1. 最小维度差距（0-0.5）：所有维度中最不明确的差距
        min_gap = min(abs(p - 0.5) * 2 for p in dim_probs.values())

        # 2. 样本量因子（0-1）：log 缩放，避免大样本过度加权
        size_factor = min(1.0, math.log10(sample_size + 1) / 2.5)

        # 3. 综合置信度
        # 基础 50 + 差距贡献 30 + 样本贡献 20
        confidence = 50 + min_gap * 30 + size_factor * 20

        # 限制在 20-95 之间
        return min(95.0, max(20.0, confidence))

    def _compute_stability(self, mbti_type: str, dim_probs: Dict[str, float],
                           messages: List[Message]) -> float:
        """v2.0.0 新增：人格稳定性

        基于：
        - 维度概率分布的极差（差距越大越稳定）
        - 消息内容的一致性（前后半段类型一致则稳定）

        返回 0-1，1 表示最稳定
        """
        if not messages:
            return 0.0

        # 1. 维度差距稳定性（最大差距 - 最小差距，差距越接近越稳定）
        gaps = [abs(p - 0.5) * 2 for p in dim_probs.values()]
        gap_stability = 1.0 - (max(gaps) - min(gaps))  # 0-1

        # 2. 前后半段一致性
        mid = len(messages) // 2
        if mid < 5:
            consistency = 0.5  # 样本不足，取中性
        else:
            first_half = messages[:mid]
            second_half = messages[mid:]

            # 简单一致性：前/后 MBTI 关键词分布相似度
            from collections import Counter
            def keyword_dist(msgs):
                tokens = []
                for m in msgs:
                    tokens.extend(tokenize(m.content, use_jieba=True))
                return Counter(tokens)

            first_dist = keyword_dist(first_half)
            second_dist = keyword_dist(second_half)
            all_keys = set(first_dist.keys()) | set(second_dist.keys())
            if not all_keys:
                consistency = 0.5
            else:
                # 余弦相似度
                dot = sum(first_dist.get(k, 0) * second_dist.get(k, 0) for k in all_keys)
                mag1 = math.sqrt(sum(v**2 for v in first_dist.values()))
                mag2 = math.sqrt(sum(v**2 for v in second_dist.values()))
                consistency = dot / (mag1 * mag2) if mag1 * mag2 > 0 else 0.5

        return 0.4 * gap_stability + 0.6 * consistency
