"""
规则预测器 - v2.2.0

基于 MBTI + 场景 + 上下文 + 关键词的智能规则预测。

v2.2.0 升级点：
- 上下文感知：提取对方最后一条消息的类型（疑问/陈述/请求/感叹/社交）
- 句末意图识别：疑问尾（?/？/吗/呢）→ 答复合适的口吻
- 情感放大：对方负向情绪 → 暖心/共情话术优先
- 场景理解：周末/工作日/夜间/白天 不同时段的口吻差异
- 关键词扩展：30+ 关键词触发器 + 软触发（近 20 条出现 ≥2 次）
- 风险规避：检测到风险/对抗信号时自动转为防守话术
- 历史模式匹配：最近 5 条我方真实回复的特征（短/长/疑问/感叹）做风格适配
"""

from typing import List, Dict, Any, Tuple
from collections import Counter

from core.predictor_base import PredictorBase, PredictionContext
from core.result import PredictionResult, Prediction
from core.timing import analyze_timing
from core.utils import tokenize, HAS_JIEBA


class RulePredictor(PredictorBase):
    """基于规则的多策略预测器（v2.2.0 上下文智能）"""

    name = "rule"
    version = "2.3.0"
    weight = 0.4  # 在集成中权重 40%
    description = "MBTI + 场景 + 关键词 + 上下文意图 + 情感驱动规则预测"

    # v2.0.0 扩充：16 MBTI × 5 模板
    MBTI_TEMPLATES = {
        "INTJ": [
            "让我分析一下这个情况",
            "从长远来看，我认为...",
            "我需要先了解所有事实",
            "这是否符合我们的长期目标？",
            "我有一个系统的计划",
        ],
        "INTP": [
            "理论上是这样",
            "让我理清思路",
            "我觉得这个问题的关键是...",
            "我倾向于从概念层面理解",
            "这个想法很有趣，值得深入",
        ],
        "ENTJ": [
            "我来明确一下目标",
            "我们需要按步骤执行",
            "结论是...",
            "效率最重要",
            "我决定就这么做",
        ],
        "ENTP": [
            "这个角度很有趣",
            "我有一个新想法",
            "如果我们换个角度看...",
            "为什么不试试这个？",
            "我想到一个可能性",
        ],
        "INFJ": [
            "我理解你的感受",
            "我希望我们能达成共识",
            "从长远来看...",
            "我感受到你想表达的是...",
            "这触及了我内心深处",
        ],
        "INFP": [
            "我觉得这很重要",
            "这让我想到了一些事",
            "希望我们能找到一个双方都接受的方案",
            "我对这件事很在意",
            "我的直觉告诉我...",
        ],
        "ENFJ": [
            "你今天怎么样",
            "我们来聊聊",
            "我有个想法想和你分享",
            "我关心你的感受",
            "我们一起想办法",
        ],
        "ENFP": [
            "太有趣了！",
            "你有没有想过...",
            "让我们尝试点新鲜的",
            "我有好多想法！",
            "这让我兴奋！",
        ],
        "ISTJ": [
            "按照计划进行",
            "我们需要按步骤来",
            "事实是这样的",
            "我负责把事情做好",
            "流程是什么？",
        ],
        "ISFJ": [
            "你还好吗",
            "我来帮你",
            "不用担心，有我在",
            "我注意到你最近...",
            "需要我做什么吗？",
        ],
        "ESTJ": [
            "我来安排一下",
            "我们按流程走",
            "效率很重要",
            "结果说明一切",
            "责任要明确",
        ],
        "ESFJ": [
            "大家一起讨论",
            "气氛有点沉闷啊",
            "有什么我能帮忙的吗？",
            "我们一起做吧",
            "大家开心最重要",
        ],
        "ISTP": [
            "让我看看怎么解决",
            "我试试看",
            "这很直接",
            "我先分析一下技术问题",
            "给我点时间",
        ],
        "ISFP": [
            "慢慢来",
            "你喜欢就好",
            "我觉得这样也不错",
            "让我先感受一下",
            "我想保持现在的状态",
        ],
        "ESTP": [
            "走一步看一步",
            "先试试再说",
            "管他呢，做了再说",
            "机会来了就抓住",
            "我行动派",
        ],
        "ESFP": [
            "太好玩了",
            "我们出去玩吧",
            "开心最重要",
            "现在就去！",
            "我有新计划！",
        ],
    }

    SCENARIO_TEMPLATES = {
        "romantic": [
            "我也想你",
            "那我们约个时间吧",
            "你有什么安排吗？",
            "我们一起去看电影？",
            "想见你了",
        ],
        "work": [
            "收到，我处理一下",
            "我确认一下情况",
            "好的，我跟进",
            "需要我配合什么？",
            "我马上处理",
        ],
        "social": [
            "一起出去玩？",
            "什么时候方便？",
            "你有什么想玩的？",
            "我约了几个朋友",
            "你选地方吧",
        ],
        "important": [
            "好的，我马上确认",
            "我会尽快处理",
            "已经准备好了",
            "麻烦你确认一下",
            "我已记录，会跟进",
        ],
    }

    # v2.2.0 扩充：30+ 关键词 + 软触发
    KEYWORD_TRIGGERS = {
        "吃饭": ["一起吃吗？", "你定时间", "想吃什么？"],
        "餐厅": ["推荐哪家？", "你定吧", "我都可以"],
        "工作": ["工作顺利吗？", "最近忙不忙？", "加油！"],
        "加班": ["辛苦了", "注意身体", "早点休息"],
        "视频": ["最近看了什么好剧？", "推荐一下", "一起看？"],
        "电影": ["什么电影好看？", "推荐一下", "想看什么类型的？"],
        "周末": ["有什么计划？", "一起出来？", "想放松一下"],
        "累": ["好好休息", "辛苦了", "想不想出去散心？"],
        "生病": ["多喝热水", "好好休息", "需要我帮忙吗？"],
        "生日": ["生日快乐！", "想要什么礼物？", "我们庆祝一下"],
        "考试": ["加油！", "祝你顺利", "考完请你吃大餐"],
        "面试": ["祝你成功", "好好发挥", "相信自己"],
        "睡觉": ["早点休息", "做个好梦", "晚安"],
        "晚安": ["晚安", "好梦", "明天见"],
        "早安": ["早安", "今天也要加油", "心情不错"],
        "下班": ["辛苦了", "晚上有什么安排？", "一起吃个饭？"],
        "上班": ["今天也要加油", "顺利吗？", "路上注意安全"],
        "火锅": ["我也想吃", "你定地方", "加我一个"],
        "烧烤": ["走起", "哪里吃", "好想吃"],
        "咖啡": ["喝杯咖啡？", "找个时间", "提神醒脑"],
        "奶茶": ["加一杯", "推荐什么口味", "好想喝"],
        "旅游": ["去哪里？", "好羡慕", "下次带我"],
        "爬山": ["好主意", "什么时间去", "算我一个"],
        "游泳": ["一起去", "好久没游了", "夏日必备"],
        "购物": ["买了什么", "我也要", "帮我也带一个"],
        "孩子": ["宝宝多大了", "真可爱", "以后带出来玩"],
        "爸妈": ["注意身体", "替我问好", "他们喜欢什么"],
        "下雨": ["带伞了吗", "注意安全", "好想睡个懒觉"],
        "雪": ["好美", "注意保暖", "想堆雪人"],
        "堵车": ["我也堵着", "绕路吧", "听个音乐"],
        "升职": ["恭喜！", "加薪了吧", "请你吃饭"],
        "辞职": ["想清楚就好", "休息一下", "我支持你"],
        "失恋": ["没关系", "我陪你", "会好起来的"],
        "考试": ["加油！", "祝你顺利", "考完请你吃大餐"],
        "减肥": ["一起锻炼", "少吃多动", "我也在努力"],
    }

    # v2.2.0 上下文意图识别（对方最后一条消息）
    INTENT_PATTERNS = {
        "question": {
            "markers": ["?", "？", "吗", "呢", "怎么", "为什么", "如何", "什么", "哪", "多少", "谁", "几"],
            "responses": [
                "我看看",
                "我觉得",
                "我先确认一下",
                "你希望呢",
                "我等下告诉你",
            ],
        },
        "request": {
            "markers": ["帮", "帮我", "请", "麻烦", "能不能", "可以", "有空", "替我", "麻烦你"],
            "responses": [
                "好的，我处理一下",
                "我马上看看",
                "没问题",
                "我帮你",
                "确认一下时间",
            ],
        },
        "complaint": {
            "markers": ["烦", "气", "累", "失望", "无语", "受不了", "怎么这样", "又", "失败", "糟糕"],
            "responses": [
                "怎么了？",
                "我懂你",
                "需要我帮忙吗？",
                "你还好吗？",
                "要不聊聊？",
            ],
        },
        "gratitude": {
            "markers": ["谢谢", "感谢", "辛苦了", "多谢", "感恩", "love", "3q"],
            "responses": [
                "不客气",
                "应该的",
                "没什么",
                "能帮到你就好",
                "你也辛苦了",
            ],
        },
        "invitation": {
            "markers": ["一起", "要不要", "约", "要不要", "去吗", "来吧", "邀请"],
            "responses": [
                "好的，什么时候",
                "我看看时间",
                "可以",
                "去！",
                "你定吧",
            ],
        },
        "statement": {  # 默认
            "markers": [],
            "responses": [
                "嗯嗯",
                "好的",
                "我知道了",
                "继续",
                "然后呢？",
            ],
        },
    }

    # v2.2.0 风险信号：触发后转为防守话术
    RISK_SIGNALS = {
        "生气", "滚", "滚蛋", "讨厌", "烦死", "别理我", "不想", "算了", "算了", "失望",
        "过分", "混蛋", "滚", "威胁", "报警", "再见", "拉黑", "删除",
    }

    # v2.2.0 防守话术（风险场景）
    DEFENSIVE_TEMPLATES = [
        "我们冷静一下",
        "我理解你的感受",
        "我们换个角度想想",
        "你的想法很重要",
        "我不想吵架",
        "我们好好说",
        "我愿意倾听",
        "我先冷静一下",
        "我们都需要时间",
    ]

    # v2.2.0 共情话术（对方负向情绪）
    EMPATHY_TEMPLATES = [
        "我懂你的感受",
        "辛苦了",
        "抱抱你",
        "你不是一个人",
        "想聊聊吗？",
        "我能帮你什么？",
        "我一直在",
        "需要陪伴吗？",
        "你很重要",
    ]

    # v2.2.0 暖心话术（对方温升/感谢）
    WARMTH_TEMPLATES = [
        "谢谢你",
        "有你在真好",
        "我也觉得",
        "我们一起",
        "我珍惜我们",
        "很开心",
        "好幸福",
        "希望我们一直这样",
        "我心里暖暖的",
    ]

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_alternatives = 5

    def is_available(self) -> bool:
        return True  # 始终可用

    # ----------------------------------------------------------------
    # 主入口
    # ----------------------------------------------------------------
    def predict(self, context: PredictionContext) -> PredictionResult:
        predictions: List[Prediction] = []

        # 1. 提取上下文特征
        features = self._extract_context_features(context)

        # 2. 根据风险信号选择策略
        time_predictions: List[Prediction] = []
        if features["has_risk_signal"]:
            predictions.extend(self._defensive_predictions(features))
        else:
            # 3. MBTI 模板
            predictions.extend(self._mbti_predictions(features))
            # 4. 场景模板
            predictions.extend(self._scenario_predictions(features))
            # 5. 关键词触发
            predictions.extend(self._keyword_predictions(features))
            # 6. 上下文意图响应
            predictions.extend(self._intent_predictions(features))
            # 7. 情感驱动
            predictions.extend(self._sentiment_predictions(features))
            # 8. 风格适配（基于最近我方真实回复）
            style_predictions = self._style_matched_predictions(features)
            predictions.extend(style_predictions)
            # 9. 时间/及时性适配
            time_predictions = self._time_predictions(features)
            predictions.extend(time_predictions)

        # 10. 排序去重
        predictions = self._dedupe_and_rank(predictions, features)

        # 11. 取 top + 备选
        top = predictions[0] if predictions else Prediction(
            text="嗯嗯", confidence=0.3, strategy="rule"
        )
        alternatives = predictions[1:1 + self.max_alternatives]
        timing = features["timing"].to_dict()

        return PredictionResult(
            top_prediction=top,
            alternatives=alternatives,
            scenario=features["scenario"],
            context={
                "mbti": features["mbti"],
                "big_five": context.big_five,
                "sentiment": context.sentiment,
                "last_intent": features["last_intent"],
                "has_risk": features["has_risk_signal"],
                "timing": timing,
            },
            metadata={
                "predictor": "RulePredictor",
                "version": self.version,
                "total_candidates": len(predictions),
                "timing": timing,
                "time_based_candidates": [p.text for p in time_predictions],
                "feature_snapshot": {
                    "keyword_hits": features["keyword_hits"][:5],
                    "last_tokens": features["last_tokens"][:5],
                    "sentiment_trend": features["sentiment_trend"],
                    "timing": timing,
                },
            },
        )

    # ----------------------------------------------------------------
    # 特征提取
    # ----------------------------------------------------------------
    def _extract_context_features(self, context: PredictionContext) -> Dict[str, Any]:
        """提取所有上下文特征（v2.2.0 核心）"""
        messages = context.messages or []
        other_msgs = [m for m in messages if m.is_other() and m.has_content()]
        self_msgs = [m for m in messages if m.is_self() and m.has_content()]

        # 对方最后一条消息
        last_other = other_msgs[-1] if other_msgs else None
        last_content = last_other.content if last_other else ""
        last_tokens = tokenize(last_content, use_jieba=True) if last_content else []

        # 关键词频次（最近 20 条对方消息）
        token_counts = self._get_token_counts(other_msgs[-20:])

        # 句末意图识别
        last_intent = self._detect_intent(last_content)

        # 风险信号检测（token 匹配 + 子串匹配双保险）
        risk_signals = [t for t in last_tokens if t in self.RISK_SIGNALS]
        # 子串匹配：兜底处理 token 切分不到的情况
        if not risk_signals and last_content:
            for sig in self.RISK_SIGNALS:
                if sig in last_content:
                    risk_signals.append(sig)
        has_risk = bool(risk_signals)

        # 情感趋势
        sentiment_trend = (context.sentiment or {}).get("trend", "unknown")

        # 时间/及时性特征
        timing = analyze_timing(messages)

        # 关键词命中（按频次和权重）
        keyword_hits = []
        for kw in self.KEYWORD_TRIGGERS:
            cnt = token_counts.get(kw, 0)
            if cnt >= 1:
                # 频次越高，权重越高
                weight = 1.0 + min(cnt, 5) * 0.2
                keyword_hits.append((kw, cnt, weight))

        keyword_hits.sort(key=lambda x: x[2], reverse=True)

        # 场景
        scenario = context.scenario or "social"

        # 我方历史风格（最近 5 条）
        self_style = self._analyze_self_style(self_msgs[-5:])

        return {
            "messages": messages,
            "other_msgs": other_msgs,
            "self_msgs": self_msgs,
            "last_other": last_other,
            "last_content": last_content,
            "last_tokens": last_tokens,
            "last_intent": last_intent,
            "risk_signals": risk_signals,
            "has_risk_signal": has_risk,
            "sentiment_trend": sentiment_trend,
            "token_counts": token_counts,
            "keyword_hits": keyword_hits,
            "mbti": context.mbti,
            "scenario": scenario,
            "self_style": self_style,
            "timing": timing,
        }

    def _analyze_self_style(self, msgs: List) -> Dict[str, Any]:
        """分析我方最近回复风格（短/长/疑问/感叹）"""
        if not msgs:
            return {
                "avg_length": 0,
                "question_ratio": 0.0,
                "exclamation_ratio": 0.0,
                "emoji_ratio": 0.0,
                "preferred": "neutral",
            }

        lengths = [len(m.content) for m in msgs]
        questions = sum(1 for m in msgs if "?" in m.content or "？" in m.content)
        exclamations = sum(1 for m in msgs if "!" in m.content or "！" in m.content)
        emojis = sum(1 for m in msgs if any(0x1F300 <= ord(c) <= 0x1FAFF for c in m.content))

        avg_len = sum(lengths) / len(lengths) if lengths else 0
        q_ratio = questions / len(msgs)
        e_ratio = exclamations / len(msgs)
        m_ratio = emojis / len(msgs)

        if avg_len <= 5:
            preferred = "short"
        elif avg_len >= 20:
            preferred = "long"
        else:
            preferred = "medium"

        return {
            "avg_length": avg_len,
            "question_ratio": q_ratio,
            "exclamation_ratio": e_ratio,
            "emoji_ratio": m_ratio,
            "preferred": preferred,
        }

    def _detect_intent(self, content: str) -> str:
        """检测对方最后一条消息的意图"""
        if not content:
            return "statement"

        # 优先按关键词命中数判定
        scores: Dict[str, int] = {}
        for intent, info in self.INTENT_PATTERNS.items():
            score = 0
            for marker in info["markers"]:
                if marker in content:
                    score += 1
            if score > 0:
                scores[intent] = score

        if scores:
            return max(scores, key=scores.get)

        # 兜底：句末标点判断
        if content.rstrip().endswith(("?", "？", "吗", "呢")):
            return "question"
        if content.rstrip().endswith(("!", "！")):
            return "statement"
        return "statement"

    # ----------------------------------------------------------------
    # 各策略预测
    # ----------------------------------------------------------------
    def _mbti_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """MBTI 模板预测"""
        mbti = features["mbti"]
        if not mbti or mbti not in self.MBTI_TEMPLATES:
            return []

        predictions = []
        for i, text in enumerate(self.MBTI_TEMPLATES[mbti]):
            # 基础置信度 0.55，根据上下文调整
            confidence = 0.55
            # 风格匹配加权
            if features["self_style"]["preferred"] == "short" and len(text) <= 15:
                confidence += 0.05
            if features["self_style"]["question_ratio"] > 0.4 and "？" in text:
                confidence += 0.05

            predictions.append(Prediction(
                text=text,
                confidence=confidence,
                strategy="rule",
                rationale=f"基于 {mbti} MBTI 模板 #{i+1}",
                metadata={"source": "mbti_template", "mbti": mbti},
            ))
        return predictions

    def _scenario_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """场景模板预测"""
        scenario = features["scenario"]
        if scenario not in self.SCENARIO_TEMPLATES:
            return []

        predictions = []
        for i, text in enumerate(self.SCENARIO_TEMPLATES[scenario]):
            confidence = 0.50
            # 上下文意图对齐加权
            if (features["last_intent"] == "question" and "？" in text) or \
               (features["last_intent"] == "invitation" and "约" in text) or \
               (features["last_intent"] == "request" and "好" in text):
                confidence += 0.10

            predictions.append(Prediction(
                text=text,
                confidence=confidence,
                strategy="rule",
                rationale=f"基于 {scenario} 场景模板 #{i+1}",
                metadata={"source": "scenario_template", "scenario": scenario},
            ))
        return predictions

    def _keyword_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """关键词触发预测（v2.2.0 软触发 + 频次加权）"""
        predictions = []
        seen: set = set()

        for kw, cnt, weight in features["keyword_hits"][:5]:
            for text in self.KEYWORD_TRIGGERS.get(kw, []):
                if text in seen:
                    continue
                seen.add(text)
                # 基础 0.50，频次加权
                confidence = min(0.85, 0.50 + weight * 0.10)
                predictions.append(Prediction(
                    text=text,
                    confidence=confidence,
                    strategy="rule",
                    rationale=f"关键词 '{kw}' 触发（频次 {cnt}，权重 {weight:.2f}）",
                    metadata={"source": "keyword_trigger", "keyword": kw, "frequency": cnt},
                ))
        return predictions

    def _intent_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """上下文意图响应（v2.2.0 新增）"""
        intent = features["last_intent"]
        if intent not in self.INTENT_PATTERNS:
            return []

        predictions = []
        for i, text in enumerate(self.INTENT_PATTERNS[intent]["responses"]):
            predictions.append(Prediction(
                text=text,
                confidence=0.65,  # 意图匹配基础置信度较高
                strategy="rule",
                rationale=f"对方 {intent} 意图响应 #{i+1}",
                metadata={"source": "intent_match", "intent": intent},
            ))
        return predictions

    def _sentiment_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """情感驱动预测（v2.2.0 升级：暖心/共情/防守）"""
        predictions = []
        sentiment = features["sentiment_trend"]

        if sentiment == "up":
            for i, text in enumerate(self.WARMTH_TEMPLATES[:3]):
                predictions.append(Prediction(
                    text=text,
                    confidence=0.55,
                    strategy="rule",
                    rationale=f"对方情感升温（暖心）#{i+1}",
                    metadata={"source": "sentiment_warmth"},
                ))
        elif sentiment == "down":
            for i, text in enumerate(self.EMPATHY_TEMPLATES[:3]):
                predictions.append(Prediction(
                    text=text,
                    confidence=0.55,
                    strategy="rule",
                    rationale=f"对方情感降温（共情）#{i+1}",
                    metadata={"source": "sentiment_empathy"},
                ))
        elif sentiment == "stable":
            predictions.append(Prediction(
                text="继续保持这样挺好的",
                confidence=0.45,
                strategy="rule",
                rationale="情感稳定（顺势）",
                metadata={"source": "sentiment_stable"},
            ))

        return predictions

    def _time_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """基于时间/及时性的预测（v2.3.0 新增）"""
        timing = features.get("timing")
        if timing is None or not timing.has_timestamps:
            return []

        predictions = []
        urgency = timing.urgency
        time_of_day = timing.time_of_day
        day_type = timing.day_type

        # 隔太久未回复：优先给“找回联系”话术
        if urgency == "stale":
            for text in ("好久不见，最近还好吗？", "刚看到消息，你还在吗？", "最近忙吗？"):
                predictions.append(Prediction(
                    text=text,
                    confidence=0.58,
                    strategy="rule",
                    rationale=f"最后一条消息距今 {timing.last_message_age_minutes:.0f} 分钟，适合主动找回联系",
                    metadata={"source": "timing_stale", "urgency": urgency},
                ))
        elif urgency == "immediate":
            # 对方刚发消息：短回复更符合即时对话节奏
            predictions.append(Prediction(
                text="在的，你说",
                confidence=0.50,
                strategy="rule",
                rationale="对方消息很新，适合即时短回复",
                metadata={"source": "timing_immediate", "urgency": urgency},
            ))
        elif urgency == "soon":
            predictions.append(Prediction(
                text="我看到了，稍等",
                confidence=0.50,
                strategy="rule",
                rationale="消息已过几分钟，先回应避免对方等待",
                metadata={"source": "timing_soon", "urgency": urgency},
            ))

        # 夜间关怀
        if time_of_day == "night":
            predictions.append(Prediction(
                text="这么晚还没睡，注意休息",
                confidence=0.46,
                strategy="rule",
                rationale="夜间场景，适合表达关心",
                metadata={"source": "timing_night", "time_of_day": time_of_day},
            ))

        # 周末互动
        if day_type == "weekend":
            predictions.append(Prediction(
                text="周末愉快，有什么安排吗？",
                confidence=0.45,
                strategy="rule",
                rationale="周末场景，适合轻社交开场",
                metadata={"source": "timing_weekend", "day_type": day_type},
            ))

        # 密集连续对话：保持话题延续
        if timing.burst:
            predictions.append(Prediction(
                text="嗯，接着说",
                confidence=0.48,
                strategy="rule",
                rationale="最近几条消息密集，应保持对话延续",
                metadata={"source": "timing_burst", "burst": True},
            ))

        return predictions

    def _defensive_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """风险信号防守话术（v2.2.0 新增）"""
        predictions = []
        for i, text in enumerate(self.DEFENSIVE_TEMPLATES[:5]):
            predictions.append(Prediction(
                text=text,
                confidence=0.70,  # 风险场景下防守话术置信度高
                strategy="rule",
                rationale=f"检测到风险/对抗信号（{', '.join(features['risk_signals'][:3])}），自动转防守 #{i+1}",
                metadata={
                    "source": "defensive",
                    "risk_signals": features["risk_signals"],
                },
            ))
        return predictions

    def _style_matched_predictions(self, features: Dict[str, Any]) -> List[Prediction]:
        """风格适配预测（基于我方历史风格）"""
        style = features["self_style"]
        if not style["preferred"] or style["preferred"] == "neutral":
            return []

        predictions = []
        # 如果对方倾向于发问，我方也问回去
        if style["question_ratio"] > 0.5:
            predictions.append(Prediction(
                text="你觉得呢？",
                confidence=0.50,
                strategy="rule",
                rationale="我方历史风格：常提问",
                metadata={"source": "style_match"},
            ))
        # 如果我方常用感叹
        if style["exclamation_ratio"] > 0.5:
            predictions.append(Prediction(
                text="确实！",
                confidence=0.45,
                strategy="rule",
                rationale="我方历史风格：感叹号多",
                metadata={"source": "style_match"},
            ))
        return predictions

    # ----------------------------------------------------------------
    # 排序与去重
    # ----------------------------------------------------------------
    def _dedupe_and_rank(self, predictions: List[Prediction], features: Dict[str, Any]) -> List[Prediction]:
        """规范化文本去重 + 按置信度排序 + 长度过滤"""
        seen: Dict[str, Prediction] = {}
        for pred in predictions:
            key = self._normalize_text(pred.text)
            if not key or len(key) < 2:
                continue
            # 取同组最高置信度
            if key not in seen or pred.confidence > seen[key].confidence:
                seen[key] = pred

        result = list(seen.values())
        result.sort(key=lambda p: p.confidence, reverse=True)
        return result

    @staticmethod
    def _normalize_text(text: str) -> str:
        """规范化文本（去空白/标点）"""
        import re
        return re.sub(r"[\s，。！？、；：,.!?;:'\"“”‘’~…—\-·()（）\[\]【】/]+", "", text or "").lower()

    def _get_token_counts(self, messages) -> Counter:
        counter = Counter()
        for msg in messages:
            if msg.is_other() and msg.has_content():
                for token in tokenize(msg.content, use_jieba=True):
                    counter[token] += 1
        return counter
