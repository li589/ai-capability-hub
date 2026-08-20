"""
风险检测分析器 - v2.0.0

升级点（相对 v1.2.0 关键词命中即告警）：
- 反讽识别：检测"投资个生日礼物"等无害场景
- 否定排除：检测"不[风险词]"模式
- 上下文累积：同一会话中风险词出现 ≥3 次才升级到 high
- 时序特征：消息突然变密集 + 风险词 → 升级告警
- 三类风险等级：low / medium / high
"""

import re
from typing import List, Dict, Any
from collections import Counter

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult
from core.utils import tokenize, HAS_JIEBA


class RiskAnalyzer(AnalyzerBase):
    """风险检测器"""

    name = "risk"
    version = "2.1.0"
    description = "风险检测（杀猪盘/职场甩锅/HR不当/猪队友）"

    # v2.0.0 扩充 + 反讽识别
    RISK_KEYWORDS = {
        "work_shirt": {  # 职场甩锅
            "keywords": ["不是我的问题", "我以为", "我不知道", "问别人", "找领导",
                         "不归我管", "按规定", "流程问题", "沟通问题", "责任不在我",
                         "你没说清楚", "我没收到", "等通知", "再等等", "我没空",
                         "你找别人", "这是你的事"],
            "description": "对方可能正在推卸责任或拖延",
            "innocent_phrases": ["我不知道...我想问一下", "我以为你知道我们...是朋友"],
        },
        "pig_butcher": {  # 杀猪盘
            "keywords": ["投资", "赚钱", "高回报", "稳赚", "区块链", "虚拟币", "彩票",
                         "赌博", "平台", "充值", "转账", "保证金", "税务", "账户异常",
                         "安全账户", "代收", "先借我", "借我点钱", "稳赚不赔", "内部消息"],
            "description": "对方可能正在实施诈骗",
            "innocent_phrases": ["投资个生日礼物", "投资自己", "投资学习", "投资理财"],
        },
        "hr_bad": {  # HR 不当
            "keywords": ["试用期", "工资打折", "不加金", "末尾淘汰", "强制加班", "免费加班",
                         "不签合同", "社保", "公积金", "绩效", "优化", "输送", "毕业",
                         "向社会输送", "996", "007", "ICU", "大小周", "PIP"],
            "description": "对方可能在进行不当用工行为",
            "innocent_phrases": [],
        },
        "teammate_trouble": {  # 猪队友
            "keywords": ["忘了", "不好意思", "抱歉", "我以为你知道", "别人也是这么做的",
                         "大家都这样", "问题不大", "没事的", "没关系", "小问题", "差不多得了",
                         "将就一下", "能跑就行", "先上线再说", "后面再改", "来不及了"],
            "description": "对方可能不负责任或敷衍了事",
            "innocent_phrases": ["不好意思打扰了", "抱歉打扰您"],
        },
    }

    # 多方案应对话术
    RESPONSE_STRATEGIES = {
        "work_shirt": {
            "defensive": ["好的，我先记录一下这个情况", "我需要确认一下具体责任划分",
                          "我们可以一起回顾一下流程", "请给我发邮件确认具体要求"],
            "offensive": ["这个情况我需要向领导汇报一下", "建议我们开个会明确一下责任",
                          "我可以配合，但需要您先确认需求"],
            "diplomatic": ["我理解您的立场，我们看看怎么协作解决",
                           "感谢您的反馈，我会跟进处理的", "好的，我这边会配合您的工作"],
        },
        "pig_butcher": {
            "defensive": ["我需要考虑一下，和家里人商量一下", "我最近资金比较紧张",
                          "我对这个不太懂，不敢轻易尝试"],
            "offensive": ["请问这个平台有正规资质吗？", "能问一下您的投资经验吗？",
                          "我可以先了解一下这个项目吗？"],
            "diplomatic": ["听起来不错，但我得先研究研究", "好的，我先看看资料",
                           "我最近在忙别的项目，以后再说吧"],
        },
        "hr_bad": {
            "defensive": ["我需要咨询一下专业人士的意见", "我查一下劳动法的规定",
                          "我考虑一下这个方案"],
            "offensive": ["请问有书面的offer吗？", "这个待遇和面试时说的不太一样",
                          "我可以了解一下公司的正规流程吗？"],
            "diplomatic": ["我理解公司的考量，但这个条件我可能需要再沟通一下",
                           "这个我需要和家人商量一下", "我可以先考虑一下吗？"],
        },
        "teammate_trouble": {
            "defensive": ["好的，我这边先做备份", "我增加一些检查环节", "我单独测试一下"],
            "offensive": ["这个问题可能会影响用户", "建议我们先解决这个风险",
                          "我需要向领导报备一下这个情况"],
            "diplomatic": ["我们一起检查一下有没有其他问题吧", "我这边帮你多测几遍",
                           "我看一下能不能优化一下"],
        },
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 5

    def validate(self, messages: List[Message]) -> bool:
        return len(messages) >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        """检测风险

        Returns:
            AnalysisResult with details={
                'risks': {
                    'pig_butcher': {
                        'detected': True,
                        'level': 'high',
                        'matched_keywords': [...],
                        'false_positive': False,
                        'innocent_match': [],
                        'description': '...',
                        'response_strategies': {...},
                    }
                },
                'overall_level': 'high',
                'risk_score': 75.0,
            }
        """
        other_messages = [m for m in messages if m.is_other() and m.has_content()]
        if not other_messages:
            return AnalysisResult(
                analyzer_name=self.name,
                score=0.0,
                confidence=100.0,
                details={"risks": {}, "overall_level": "low", "risk_score": 0.0},
            )

        # 构建完整文本
        all_text = " ".join(m.content for m in other_messages)

        # 风险类型检测
        risk_results: Dict[str, Dict[str, Any]] = {}
        for risk_type, data in self.RISK_KEYWORDS.items():
            matched = self._match_keywords(data["keywords"], all_text)
            if not matched:
                continue

            # v2.0.0 新增：检测反讽/无害场景
            innocent_match = [p for p in data.get("innocent_phrases", []) if p in all_text]
            # 否定排除：检查"不[风险词]"模式
            negation_excluded = self._check_negation_exclude(matched, all_text)

            # 上下文累积：统计风险词出现次数
            keyword_counts = Counter()
            for msg in other_messages:
                for kw in data["keywords"]:
                    if kw in msg.content:
                        keyword_counts[kw] += 1
            total_occurrences = sum(keyword_counts.values())

            # 风险等级判定
            is_false_positive = bool(innocent_match)
            if is_false_positive:
                level = "low"
            elif negation_excluded:
                level = "low"
            elif total_occurrences >= 3:
                level = "high"
            elif total_occurrences >= 2:
                level = "medium"
            else:
                # 时序特征：消息密度 + 风险词
                burst_density = self._check_burst(other_messages)
                if burst_density > 0.7 and len(matched) >= 2:
                    level = "high"
                else:
                    level = "medium"

            risk_results[risk_type] = {
                "detected": True,
                "level": level,
                "matched_keywords": matched,
                "false_positive_likely": is_false_positive,
                "innocent_match": innocent_match,
                "negation_excluded": negation_excluded,
                "keyword_count": total_occurrences,
                "description": data["description"],
                "response_strategies": self.RESPONSE_STRATEGIES.get(risk_type, {}),
            }

        # 综合风险等级
        if not risk_results:
            overall_level = "low"
            risk_score = 0.0
        else:
            levels = [r["level"] for r in risk_results.values()]
            if "high" in levels:
                overall_level = "high"
                risk_score = 85.0
            elif "medium" in levels:
                overall_level = "medium"
                risk_score = 50.0
            else:
                overall_level = "low"
                risk_score = 20.0

        return AnalysisResult(
            analyzer_name=self.name,
            score=risk_score,
            confidence=80.0,
            details={
                "risks": risk_results,
                "overall_level": overall_level,
                "risk_score": risk_score,
            },
            metadata={
                "analyzer": "RiskAnalyzer",
                "version": self.version,
                "total_messages": len(other_messages),
            },
        )

    def _match_keywords(self, keywords: List[str], text: str) -> List[str]:
        """匹配命中的关键词"""
        return [kw for kw in keywords if kw in text]

    def _check_negation_exclude(self, matched: List[str], text: str) -> bool:
        """检查"不[风险词]"否定模式"""
        for kw in matched:
            # 检测"不" + 风险词（窗口=1-2）
            patterns = [
                f"不{kw}",
                f"没{kw}",
                f"别{kw}",
                f"无{kw}",
                f"非{kw}",
            ]
            for p in patterns:
                if p in text:
                    return True
        return False

    def _check_burst(self, messages: List[Message]) -> float:
        """检测消息突增密度（最近 1/4 时间 vs 之前 3/4）

        Returns:
            0-1，>0.7 表示有突发
        """
        if len(messages) < 8:
            return 0.0

        msgs_with_ts = [m for m in messages if m.timestamp]
        if len(msgs_with_ts) < 8:
            return 0.0

        msgs_with_ts.sort(key=lambda m: m.timestamp)
        # 取最近 1/4
        n = len(msgs_with_ts)
        recent = msgs_with_ts[3 * n // 4:]
        earlier = msgs_with_ts[:3 * n // 4]

        if len(earlier) < 2 or len(recent) < 2:
            return 0.0

        # 简单密度：每条消息的平均间隔
        def avg_interval(msgs):
            intervals = []
            for i in range(1, len(msgs)):
                delta = (msgs[i].timestamp - msgs[i - 1].timestamp).total_seconds()
                intervals.append(max(1, delta))
            return sum(intervals) / len(intervals)

        recent_interval = avg_interval(recent)
        earlier_interval = avg_interval(earlier)

        if recent_interval == 0:
            return 1.0
        return min(1.0, earlier_interval / (recent_interval * 5))
