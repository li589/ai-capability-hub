"""
信息解读分析器 - v2.2.0 (新增)

4 大解读能力（解决「信息获取+解读」短板）：
    1. 意图识别（Intent Recognition）：识别每条消息的交流目的
       —— 询问 / 告知 / 请求 / 抱怨 / 道歉 / 安慰 / 邀请 / 拒绝 / 表白 / 抱怨 ...
    2. 实体识别（NER Lite）：抽取人名/时间/金额/地点/组织
    3. 主题抽取（Topic Extraction）：自动归纳对话的几个核心主题
    4. 立场识别（Stance Detection）：判断双方对关键议题的态度（同意/反对/中立）

实现方式：基于规则 + 词典启发式（非 LLM 调用），零外部依赖。
"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult
from core.utils import tokenize, HAS_JIEBA


class InterpretationAnalyzer(AnalyzerBase):
    """信息解读分析器"""

    name = "interpretation"
    version = "2.2.0"
    description = "意图/实体/主题/立场 四维信息解读"

    # 意图词典（关键词 → 意图）
    INTENT_KEYWORDS: Dict[str, List[str]] = {
        "询问": ["吗", "什么", "怎么", "为什么", "哪里", "几", "多少", "?", "？", "谁", "能否"],
        "请求": ["帮", "麻烦", "请", "能否", "可以", "麻烦你", "帮我", "替我"],
        "告知": ["我", "今天", "昨天", "明天", "刚才", "已经", "刚刚", "现在"],
        "抱怨": ["怎么", "为什么", "烦", "累", "受不了", "过分", "太差", "失望"],
        "道歉": ["对不起", "抱歉", "不好意思", "歉", "我错了", "原谅", "请见谅"],
        "安慰": ["别", "没事", "没关系", "想开点", "会好的", "加油", "挺住"],
        "邀请": ["一起", "要不要", "来吧", "约", "有空吗", "出来"],
        "拒绝": ["不", "不要", "没空", "算了", "下次吧", "改天", "不方便"],
        "表白": ["喜欢", "爱", "想和你", "在一起", "做我", "我喜欢你"],
        "感谢": ["谢谢", "感谢", "辛苦了", "多谢"],
        "调侃": ["哈哈", "嘿嘿", "lol", "233", "逗你", "开玩笑"],
        "强调": ["!", "！", "一定", "必须", "千万", "务必"],
    }

    # NER 规则
    NER_PATTERNS: Dict[str, str] = {
        "金额": r"[¥￥$]\s?(\d+(?:\.\d+)?(?:[万亿千百]{0,2}))",
        "百分比": r"(\d+(?:\.\d+)?%)",
        "日期": r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{1,2}[-/月]\d{1,2}日?)",
        "时间": r"(\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}点\d{0,2}分?)",
        "手机": r"(?<!\d)1[3-9]\d{9}(?!\d)",
        "邮箱": r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}",
        "URL": r"https?://[^\s]+",
    }

    # 主题词典（聚合用）
    TOPIC_KEYWORDS: Dict[str, List[str]] = {
        "工作": ["项目", "会议", "客户", "老板", "加班", "同事", "工作", "任务", "需求", "KPI", "汇报"],
        "家庭": ["家人", "爸妈", "父母", "孩子", "宝宝", "老公", "老婆", "婆媳", "夫妻"],
        "感情": ["喜欢", "爱", "想你", "分手", "复合", "在一起", "表白", "心动"],
        "健康": ["病", "医院", "检查", "吃药", "手术", "发烧", "感冒", "症状", "医生"],
        "购物": ["买", "下单", "快递", "包邮", "优惠", "折扣", "淘宝", "京东", "拼多多"],
        "美食": ["吃", "喝", "餐厅", "外卖", "菜", "味道", "火锅", "烧烤"],
        "娱乐": ["游戏", "王者", "吃鸡", "原神", "抖音", "B站", "追剧", "综艺", "电影"],
        "学习": ["考试", "作业", "论文", "课程", "老师", "学生", "学校", "毕业", "考研"],
        "财务": ["钱", "工资", "转账", "借", "还", "还款", "信用卡", "余额", "存钱"],
    }

    # 立场词典
    STANCE_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
        "positive_stance": {
            # 注意避免单字"对"——子串匹配会命中"反对/不对"里的"对"，导致负面被抵消
            "通用": ["同意", "支持", "好的", "可以的", "没问题", "完全", "确实", "对的", "没错", "说得对", "赞", "我愿意"],
            "工作": ["我来做", "我来负责", "保证完成", "尽力", "积极"],
            "感情": ["我也", "我也是", "我想和你", "好想"],
        },
        "negative_stance": {
            "通用": ["反对", "不同意", "不行", "不", "不可能", "拒绝", "免谈", "算了"],
            "工作": ["推不动", "做不了", "人手不够", "资源不足"],
            "感情": ["不喜欢", "不爱", "不想", "别再", "我们"],
        },
        "neutral_stance": {
            "通用": ["考虑", "再看看", "再说", "让我想想", "不一定", "可能", "或许", "再说吧", "我研究一下"],
        },
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 3

    def validate(self, messages: List[Message]) -> bool:
        return len(messages) >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        # 1. 意图识别
        intents = self._recognize_intents(messages)

        # 2. 实体识别
        entities = self._extract_entities(messages)

        # 3. 主题抽取
        topics = self._extract_topics(messages)

        # 4. 立场识别
        stances = self._detect_stances(messages, topics)

        # 综合分数：信息丰富度（实体数量 × 权重 + 主题多样性）
        info_richness = (
            min(entities["total_count"] / 10, 1.0) * 40 +
            min(len([t for t in topics["topics"] if t["weight"] > 0]) / 3, 1.0) * 30 +
            min(intents["distinct_intent_count"] / 5, 1.0) * 30
        )

        confidence = self._compute_confidence(messages)

        return AnalysisResult(
            analyzer_name=self.name,
            score=round(info_richness, 2),
            confidence=round(confidence, 1),
            details={
                "summary": self._build_summary(intents, entities, topics, stances),
                "intents": intents,
                "entities": entities,
                "topics": topics,
                "stances": stances,
            },
            metadata={
                "analyzer": "InterpretationAnalyzer",
                "version": self.version,
                "sample_size": len(messages),
                "has_jieba": HAS_JIEBA,
            },
        )

    # ----------------------------------------------------------------
    # 1. 意图识别
    # ----------------------------------------------------------------
    def _recognize_intents(self, messages: List[Message]) -> Dict[str, Any]:
        intent_counts = {intent: 0 for intent in self.INTENT_KEYWORDS}
        intent_by_sender: Dict[str, Counter] = defaultdict(Counter)

        for msg in messages:
            content = msg.content or ""
            # 标记这条消息属于哪个意图（多意图计多意图）
            matched: set = set()
            for intent, keywords in self.INTENT_KEYWORDS.items():
                if any(kw in content for kw in keywords):
                    intent_counts[intent] += 1
                    matched.add(intent)

            for intent in matched:
                intent_by_sender[msg.sender][intent] += 1

        # 主导意图
        total_intents = sum(intent_counts.values())
        distribution = {
            intent: round(c / max(total_intents, 1), 3)
            for intent, c in intent_counts.items()
        } if total_intents else {intent: 0 for intent in intent_counts}
        dominant = max(intent_counts, key=intent_counts.get) if total_intents else "unknown"

        return {
            "available": total_intents > 0,
            "intent_counts": intent_counts,
            "distribution": distribution,
            "dominant_intent": dominant,
            "distinct_intent_count": sum(1 for c in intent_counts.values() if c > 0),
            "by_sender": {
                sender: dict(counter.most_common(3))
                for sender, counter in intent_by_sender.items()
            },
        }

    # ----------------------------------------------------------------
    # 2. 实体识别
    # ----------------------------------------------------------------
    def _extract_entities(self, messages: List[Message]) -> Dict[str, Any]:
        per_type: Dict[str, List[Dict]] = {t: [] for t in self.NER_PATTERNS}
        per_type_counts = Counter()
        total = 0

        for msg in messages:
            content = msg.content or ""
            for ent_type, pattern in self.NER_PATTERNS.items():
                for match in re.finditer(pattern, content):
                    value = match.group(0).strip()
                    # 去重（按 value 在同一消息内）
                    if value and not any(e["value"] == value for e in per_type[ent_type]):
                        per_type[ent_type].append({
                            "value": value,
                            "sender": msg.sender,
                            "context": msg.content[max(0, match.start() - 10):match.end() + 10],
                        })
                        per_type_counts[ent_type] += 1
                        total += 1
                # 限制每个类型最多保留 20 个，避免数据爆炸
                per_type[ent_type] = per_type[ent_type][:20]

        return {
            "available": total > 0,
            "total_count": total,
            "by_type": per_type_counts.most_common(),
            "entities": per_type,
        }

    # ----------------------------------------------------------------
    # 3. 主题抽取
    # ----------------------------------------------------------------
    def _extract_topics(self, messages: List[Message]) -> Dict[str, Any]:
        topic_weights = {topic: 0 for topic in self.TOPIC_KEYWORDS}

        for msg in messages:
            content = msg.content or ""
            for topic, keywords in self.TOPIC_KEYWORDS.items():
                if any(kw in content for kw in keywords):
                    # 一次消息里命中多个关键词只算 1 次
                    topic_weights[topic] += 1

        # 排序
        sorted_topics = sorted(topic_weights.items(), key=lambda x: x[1], reverse=True)
        top_topics = [
            {"name": topic, "weight": weight}
            for topic, weight in sorted_topics
            if weight > 0
        ][:5]

        # 自动推断主题摘要（用关键词构造）
        inferred = []
        if top_topics:
            top_name = top_topics[0]["name"]
            inferred.append(f"主要讨论主题：{top_name}（占比 {top_topics[0]['weight']} 条消息）")
        for t in top_topics[1:3]:
            inferred.append(f"次要主题：{t['name']}（{t['weight']} 条）")

        return {
            "available": bool(top_topics),
            "topics": top_topics,
            "all_weights": topic_weights,
            "summary": inferred,
        }

    # ----------------------------------------------------------------
    # 4. 立场识别
    # ----------------------------------------------------------------
    def _detect_stances(self, messages: List[Message], topics: Dict) -> Dict[str, Any]:
        # 推断每个发送方对当前主要话题的立场
        if not topics.get("available"):
            return {
                "available": False,
                "reason": "无可分析的主题",
                "by_sender": {},
                "by_topic": {},
            }

        primary_topic = topics["topics"][0]["name"] if topics["topics"] else None
        # 构造主话题相关词典
        topic_keywords = self.TOPIC_KEYWORDS.get(primary_topic, []) if primary_topic else []

        by_sender = {}
        for msg in messages:
            sender = msg.sender
            content = msg.content or ""
            stance = self._classify_stance(content, topic_keywords)
            if sender not in by_sender:
                by_sender[sender] = {"positive": 0, "negative": 0, "neutral": 0}
            by_sender[sender][stance] += 1

        # 简化展示：每个发送方的主导立场
        by_sender_summary = {}
        for sender, counts in by_sender.items():
            total = sum(counts.values())
            if total == 0:
                continue
            dominant = max(counts, key=counts.get)
            by_sender_summary[sender] = {
                "dominant": dominant,
                "distribution": {k: round(v / total, 3) for k, v in counts.items()},
                "total_signals": total,
            }

        # 按主题聚合立场
        by_topic = {}
        for topic in topics.get("topics", []):
            by_topic[topic["name"]] = {
                "discussion_count": topic["weight"],
                "stance_signals_by_sender": by_sender_summary,
            }

        return {
            "available": bool(by_sender_summary),
            "primary_topic": primary_topic,
            "by_sender": by_sender_summary,
            "by_topic": by_topic,
        }

    def _classify_stance(self, content: str, topic_keywords: List[str]) -> str:
        """单条消息的立场分类。"""
        # 检查立场词典
        pos_score = sum(
            content.count(kw)
            for kw in self.STANCE_KEYWORDS["positive_stance"]["通用"]
        )
        neg_score = sum(
            content.count(kw)
            for kw in self.STANCE_KEYWORDS["negative_stance"]["通用"]
        )
        neutral_score = sum(
            content.count(kw)
            for kw in self.STANCE_KEYWORDS["neutral_stance"]["通用"]
        )

        # 主题特定词加权
        for kw in topic_keywords:
            if kw in content:
                pos_score += 0.5  # 出现主题词默认中性偏正向
                neutral_score += 0.3

        if pos_score > neg_score and pos_score > neutral_score:
            return "positive"
        elif neg_score > pos_score and neg_score > neutral_score:
            return "negative"
        else:
            return "neutral"

    # ----------------------------------------------------------------
    # 报告摘要
    # ----------------------------------------------------------------
    def _build_summary(self, intents: Dict, entities: Dict, topics: Dict, stances: Dict) -> str:
        parts = []
        if intents.get("dominant_intent") and intents["dominant_intent"] != "unknown":
            parts.append(f"主要意图：{intents['dominant_intent']}")
        if topics.get("summary"):
            parts.extend(topics["summary"])
        if entities.get("total_count", 0) > 0:
            types = [t for t, _ in entities["by_type"][:3]]
            parts.append(f"包含 {entities['total_count']} 个关键实体（{', '.join(types)}）")
        if stances.get("primary_topic"):
            for sender, info in stances.get("by_sender", {}).items():
                parts.append(f"{sender} 对主题[{stances['primary_topic']}] 倾向：{info['dominant']}")
        return "；".join(parts) if parts else "无足够信息解读"

    def _compute_confidence(self, messages: List[Message]) -> float:
        n = len(messages)
        if n < 5:
            return 30.0
        if n < 20:
            return 60.0
        if n < 50:
            return 80.0
        return 90.0
