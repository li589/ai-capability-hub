"""
场景分析器 - v2.0.0

升级点：
- 4 个核心场景：romantic / work / social / important
- v2.0.0 引入 jieba 分词，识别准确率更高
- 场景权重计算 + 主场景判定
- 输出场景化的建议
"""

from typing import List, Dict, Any

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult
from core.utils import tokenize, HAS_JIEBA


class ScenarioAnalyzer(AnalyzerBase):
    """场景分类分析器"""

    name = "scenario"
    version = "2.1.0"
    description = "对话场景分类（恋爱/工作/社交/重要事项）"

    SCENARIOS = {
        "romantic": {
            "keywords": ["喜欢", "爱", "想你", "约会", "吃饭", "电影", "逛街", "礼物",
                         "生日", "纪念日", "晚安", "早安", "宝贝", "亲爱的", "甜蜜",
                         "幸福", "老公", "老婆", "在一起", "表白", "想你了", "想你"],
            "weight": 0,
        },
        "work": {
            "keywords": ["工作", "加班", "项目", "开会", "报告", "方案", "客户", "领导",
                         "同事", "工资", "晋升", "面试", "入职", "辞职", "deadline",
                         "KPI", "OKR", "需求", "评审", "上线", "提测", "bug", "复盘"],
            "weight": 0,
        },
        "social": {
            "keywords": ["朋友", "聚会", "一起", "玩", "游戏", "运动", "旅游", "美食",
                         "分享", "八卦", "聊天", "有趣", "电影", "唱歌", "ktv", "剧本杀",
                         "密室", "桌游", "露营", "爬山", "骑行"],
            "weight": 0,
        },
        "important": {
            "keywords": ["重要", "紧急", "确认", "deadline", "截止", "必须", "完成",
                         "交付", "审核", "签约", "合同", "付款", "转账", "借", "还",
                         "贷款", "信用卡", "医保", "社保", "签证"],
            "weight": 0,
        },
    }

    SUGGESTIONS = {
        "romantic": {
            "communication": ["可以主动邀约，但要给对方留余地",
                              "注意观察对方回复的积极程度",
                              "保持适度的神秘感和新鲜感"],
            "monitoring": ["注意聊天频率变化", "关注情绪关键词的变化",
                           "记录重要的纪念日和承诺"],
        },
        "work": {
            "communication": ["重要事项要用书面确认", "及时记录决策和承诺",
                              "明确责任边界"],
            "monitoring": ["识别甩锅信号", "注意加班频率变化", "关注态度突然变化"],
        },
        "social": {
            "communication": ["保持真诚，不要过度奉承", "找到共同兴趣话题",
                              "给对方适当的空间"],
            "monitoring": ["识别过度索取型朋友", "注意借钱相关话题",
                           "观察承诺兑现情况"],
        },
        "important": {
            "communication": ["重要事项必须书面确认", "及时跟进进度",
                              "设置提醒节点"],
            "monitoring": ["识别拖延信号", "注意模糊承诺", "监控关键时间节点"],
        },
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 3

    def validate(self, messages: List[Message]) -> bool:
        return len(messages) >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        # 分词后词频
        token_counts: Dict[str, int] = {}
        for msg in messages:
            for token in tokenize(msg.content, use_jieba=True):
                token_counts[token] = token_counts.get(token, 0) + 1

        # 场景权重
        scenario_weights: Dict[str, int] = {}
        for scenario, data in self.SCENARIOS.items():
            weight = 0
            for kw in data["keywords"]:
                if kw in token_counts:
                    weight += token_counts[kw]
            scenario_weights[scenario] = weight

        # 主场景
        sorted_scenarios = sorted(scenario_weights.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_scenarios[0][0] if sorted_scenarios[0][1] > 0 else "social"

        # 置信度
        max_w = sorted_scenarios[0][1]
        second_w = sorted_scenarios[1][1] if len(sorted_scenarios) > 1 else 0
        gap = max_w - second_w
        confidence = min(95.0, 50.0 + gap * 5)

        return AnalysisResult(
            analyzer_name=self.name,
            score=max_w,
            confidence=round(confidence, 1),
            details={
                "primary": primary,
                "weights": scenario_weights,
                "sorted": [{"scenario": s, "weight": w} for s, w in sorted_scenarios],
                "suggestions": self.SUGGESTIONS.get(primary, {}),
            },
            metadata={
                "analyzer": "ScenarioAnalyzer",
                "version": self.version,
                "has_jieba": HAS_JIEBA,
            },
        )
