"""
大五人格分析器 - v2.1.0

升级点：
- neuroticism 补全 low 词
- v2.1.0 归一化校准：基于信号量的对数平滑映射，
  避免小样本下单边命中直接饱和 100%，各维度落在合理分散区间
- 输出 5 维雷达图数据
"""

import math
from typing import List, Dict, Any

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult
from core.utils import tokenize, HAS_JIEBA


class BigFiveAnalyzer(AnalyzerBase):
    """大五人格（OCEAN）分析"""

    name = "bigfive"
    version = "2.1.0"
    description = "大五人格 OCEAN 模型分析"

    # v2.0.0 扩充关键词（含 neuroticism low 词补全）
    KEYWORDS = {
        "openness": {  # 开放性
            "high": ["思考", "想象", "创意", "新颖", "好奇", "艺术", "哲学", "抽象",
                     "有趣", "探索", "创造", "新", "独特", "奇思妙想", "灵感",
                     "诗意", "美感", "艺术性", "文学", "诗", "远方", "梦"],
            "low": ["实际", "传统", "习惯", "常规", "稳定", "保守", "按部就班",
                    "务实", "落地", "常规", "经验", "旧", "从前", "以前"],
        },
        "conscientiousness": {  # 尽责性
            "high": ["计划", "安排", "准时", "完成", "认真", "负责", "组织", "效率",
                     "目标", "deadline", "截止", "清单", "严谨", "细致", "负责",
                     "执行", "坚持", "达成", "实现", "做好", "做完"],
            "low": ["随意", "拖延", "马虎", "随便", "看心情", "无所谓", "差不多",
                    "懒", "懒得", "拖延症", "磨蹭", "磨叽", "凑合", "将就"],
        },
        "extraversion": {  # 外向性
            "high": ["我们", "一起", "大家", "热闹", "聊天", "聚会", "朋友", "社交",
                     "主动", "搭讪", "外向", "开朗", "活泼", "合群", "外向",
                     "party", "嗨", "玩", "浪", "嗨皮"],
            "low": ["自己", "安静", "独处", "思考", "内向", "一个人", "低调",
                    "社恐", "害羞", "腼腆", "怕生", "宅", "封闭"],
        },
        "agreeableness": {  # 宜人性
            "high": ["谢谢", "感谢", "帮忙", "理解", "体贴", "关心", "温暖", "善良",
                     "友好", "客气", "包容", "宽容", "感恩", "暖心", "贴心",
                     "温柔", "和善", "和气", "慈祥", "乐于助人"],
            "low": ["但是", "不过", "可是", "不同意", "批评", "反驳", "质疑", "挑战",
                    "强硬", "强硬", "刻薄", "冷嘲", "热讽", "对抗", "敌对",
                    "咄咄逼人", "不客气", "不理"],
        },
        "neuroticism": {  # 神经质（情绪不稳定性）
            "high": ["担心", "焦虑", "害怕", "紧张", "不安", "压力", "失眠", "烦恼",
                     "难过", "崩溃", "绝望", "抑郁", "情绪化", "易怒", "急躁",
                     "心烦", "烦躁", "郁闷", "糟糕", "完蛋", "糟糕透了"],
            # v2.0.0 补全：neuroticism 的 low 词
            "low": ["平静", "淡定", "冷静", "放松", "稳定", "随和", "乐观", "沉着",
                    "从容", "平和", "稳重", "豁达", "开朗", "开心", "满足", "安然",
                    "心如止水", "波澜不惊", "稳重", "安心", "放松"],
        },
    }

    LABELS = {
        "openness": "开放性",
        "conscientiousness": "尽责性",
        "extraversion": "外向性",
        "agreeableness": "宜人性",
        "neuroticism": "神经质",
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 10

    def validate(self, messages: List[Message]) -> bool:
        other_count = sum(1 for m in messages if m.is_other() and m.has_content())
        return other_count >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        other_messages = [m for m in messages if m.is_other() and m.has_content()]

        # 分词后词频
        token_counts: Dict[str, int] = {}
        for msg in other_messages:
            for token in tokenize(msg.content, use_jieba=True):
                token_counts[token] = token_counts.get(token, 0) + 1

        # 5 维独立计算 high/low 命中
        dim_results: Dict[str, Dict[str, Any]] = {}
        for dim, kws in self.KEYWORDS.items():
            high_count = sum(token_counts.get(w, 0) for w in kws.get("high", []))
            low_count = sum(token_counts.get(w, 0) for w in kws.get("low", []))
            total = high_count + low_count

            # v2.1.0 校准归一化：
            # 旧版 high/(high+low) 在小样本单边命中时直接饱和 100%，区分度差。
            # 新版以 50 为中点，按极性比例偏移，再乘以基于信号量的对数平滑因子，
            # 信号越少越贴近 50（不确定），信号充分时最多偏移 ±35（落在 15~85）。
            if total > 0:
                polarity = (high_count - low_count) / total  # -1 ~ +1
                # 对数平滑：total≈30 时因子趋近 1，小样本时显著收缩
                smooth = min(1.0, math.log1p(total) / math.log1p(30))
                high_pct = 50.0 + polarity * 35.0 * smooth
            else:
                # 无信号时使用先验 50
                high_pct = 50.0

            # 置信度：有信号 = 高，无信号 = 低
            confidence = min(90.0, 30.0 + total * 5)

            dim_results[dim] = {
                "high_count": high_count,
                "low_count": low_count,
                "score": round(high_pct, 1),
                "confidence": round(confidence, 1),
                "label": self.LABELS[dim],
            }

        # 计算综合得分（5 维平均）
        avg_score = sum(d["score"] for d in dim_results.values()) / 5

        return AnalysisResult(
            analyzer_name=self.name,
            score=avg_score,
            confidence=round(sum(d["confidence"] for d in dim_results.values()) / 5, 1),
            details={
                "dimensions": dim_results,
                "labels": self.LABELS,
                "radar_data": [
                    {
                        "label": self.LABELS[dim],
                        "value": dim_results[dim]["score"],
                    }
                    for dim in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                ],
            },
            metadata={
                "analyzer": "BigFiveAnalyzer",
                "version": self.version,
                "has_jieba": HAS_JIEBA,
            },
        )
