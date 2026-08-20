"""
情感分析器 - v2.0.0

升级点（相对 v1.2.0 词频计数）：
- 集成 HowNet 情感词典（强度加权）
- 否定词识别（窗口=3，修复"我不开心"被误判）
- 程度副词加权（很/非常/极其...）
- 反讽检测（虽然...但是... / 说是...其实...）
- Emoji 情感映射
- 情感时间线（按时间序列输出）
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict

from core.analyzer_base import AnalyzerBase
from core.message import Message
from core.result import AnalysisResult


class SentimentAnalyzer(AnalyzerBase):
    """情感分析器（支持否定/程度/反讽）"""

    name = "sentiment"
    version = "2.1.0"
    description = "情感分析（HowNet词典 + 否定识别 + 程度副词 + 反讽检测）"

    # 反讽模式
    IRONY_PATTERNS = [
        re.compile(r"虽然.{1,20}但是"),
        re.compile(r"说(?:是|得).{1,10}其实"),
        re.compile(r"好一个"),
        re.compile(r"真是.{0,5}好"),
        re.compile(r"厉害了我的"),
    ]

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_messages = 3
        # 加载词典
        self.negation_words = self._load_set("negation_words.txt")
        self.degree_words = self._load_degree("degree_words.txt")
        self.emoji_dict = self._load_emoji("emoji_dict.txt")
        self.positive_words, _ = self._load_hownet("hownet_positive.txt")
        self.negative_words, _ = self._load_hownet("hownet_negative.txt")
        # 合并词典
        self.sentiment_dict = {**{w: ("pos", s) for w, s in self.positive_words.items()},
                               **{w: ("neg", s) for w, s in self.negative_words.items()}}
        # v2.5.0：首字索引——扫描时只遍历首字出现在文本中的词条，
        # 避免每条消息全词典（数千词）线性扫描。
        self._sentiment_by_first: Dict[str, List[str]] = defaultdict(list)
        for word in self.sentiment_dict:
            if word:
                self._sentiment_by_first[word[0]].append(word)

    def _load_set(self, filename: str) -> set:
        path = Path(__file__).parent / "lexicon" / filename
        if not path.exists():
            return set()
        result = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    result.add(line)
        return result

    def _load_degree(self, filename: str) -> Dict[str, float]:
        path = Path(__file__).parent / "lexicon" / filename
        if not path.exists():
            return {}
        result = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        result[parts[0]] = float(parts[1])
                    except ValueError:
                        pass
        return result

    def _load_emoji(self, filename: str) -> Dict[str, str]:
        path = Path(__file__).parent / "lexicon" / filename
        if not path.exists():
            return {}
        result = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    result[parts[0]] = parts[1]
        return result

    def _load_hownet(self, filename: str) -> Tuple[Dict[str, float], Dict[str, float]]:
        path = Path(__file__).parent / "lexicon" / filename
        words = {}
        strengths = {}
        if not path.exists():
            return words, strengths
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    word = parts[0]
                    try:
                        strength = float(parts[1])
                        words[word] = strength
                        strengths[word] = strength
                    except ValueError:
                        pass
        return words, strengths

    def validate(self, messages: List[Message]) -> bool:
        other_count = sum(1 for m in messages if m.is_other() and m.has_content())
        return other_count >= self.min_messages

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        """分析情感

        Returns:
            AnalysisResult with details={
                'positive': 65.0,
                'negative': 25.0,
                'neutral': 10.0,
                'trend': 'up',
                'timeline': [...],
                'emotional_words': {...},
                'irony_count': 0,
            }
        """
        other_messages = [m for m in messages if m.is_other() and m.has_content()]

        timeline = []
        total_pos_score = 0.0
        total_neg_score = 0.0
        neutral_count = 0
        all_positive = []
        all_negative = []
        irony_count = 0

        for msg in other_messages:
            content = msg.content
            if not content:
                continue

            # 反讽检测
            is_irony = any(p.search(content) for p in self.IRONY_PATTERNS)
            if is_irony:
                irony_count += 1

            pos_score, neg_score, pos_words, neg_words = self._analyze_sentence(content)

            # 反讽 → 情感反转
            if is_irony:
                pos_score, neg_score = neg_score, pos_score

            total_pos_score += pos_score
            total_neg_score += neg_score

            if pos_score == 0 and neg_score == 0:
                neutral_count += 1

            all_positive.extend(pos_words)
            all_negative.extend(neg_words)

            # 时间线
            if msg.timestamp:
                timeline.append({
                    "timestamp": msg.timestamp.isoformat(),
                    "pos_score": round(pos_score, 2),
                    "neg_score": round(neg_score, 2),
                    "dominant": "positive" if pos_score > neg_score else
                                "negative" if neg_score > pos_score else "neutral",
                    "irony": is_irony,
                })

        # 归一化
        total = total_pos_score + total_neg_score + neutral_count
        if total == 0:
            return AnalysisResult(
                analyzer_name=self.name,
                score=50.0,
                confidence=0.0,
                details={
                    "positive": 50.0,
                    "negative": 50.0,
                    "neutral": 0.0,
                    "trend": "stable",
                    "timeline": [],
                    "emotional_words": {"positive": [], "negative": []},
                    "irony_count": 0,
                },
            )

        positive_pct = (total_pos_score / total) * 100
        negative_pct = (total_neg_score / total) * 100
        neutral_pct = (neutral_count / total) * 100

        # 趋势
        if len(timeline) >= 2:
            first_half_pos = sum(t["pos_score"] for t in timeline[:len(timeline)//2])
            second_half_pos = sum(t["pos_score"] for t in timeline[len(timeline)//2:])
            if second_half_pos > first_half_pos * 1.1:
                trend = "up"
            elif second_half_pos < first_half_pos * 0.9:
                trend = "down"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # 置信度：消息数 + 信号强度
        confidence = min(95.0, 40.0 + len(other_messages) * 1.5)

        return AnalysisResult(
            analyzer_name=self.name,
            score=positive_pct,
            confidence=round(confidence, 1),
            details={
                "positive": round(positive_pct, 1),
                "negative": round(negative_pct, 1),
                "neutral": round(neutral_pct, 1),
                "trend": trend,
                "timeline": timeline,
                "emotional_words": {
                    # v2.5.0：Counter 按频次排序（原 set() 破坏频次，输出的是任意去重词）
                    "positive": [w for w, _ in Counter(all_positive).most_common(20)],
                    "negative": [w for w, _ in Counter(all_negative).most_common(20)],
                },
                "irony_count": irony_count,
                "total_positive_score": round(total_pos_score, 2),
                "total_negative_score": round(total_neg_score, 2),
            },
            metadata={
                "analyzer": "SentimentAnalyzer",
                "version": self.version,
                "lexicon_size": len(self.sentiment_dict),
            },
        )

    # 单字否定符（不含"非"——单独处理以排除"非常"等误判）
    _NEGATION_CHARS = ("不", "没", "无", "别", "莫", "勿", "弗", "毋", "未")

    def _analyze_sentence(self, text: str) -> Tuple[float, float, List[str], List[str]]:
        """分析单句情感

        基于原文扫描情感词（不受 jieba/停用词过滤影响），否定与程度判断
        同样基于原文窗口，修复两个已知缺陷：
        1. 程度副词"非常"的"非"字被 token 字符级匹配误判为否定 → 情感反转
        2. jieba 分词过滤停用词后否定词"不"消失 → 否定识别失效

        Returns:
            (positive_score, negative_score, pos_words, neg_words)
        """
        pos_score = 0.0
        neg_score = 0.0
        pos_words: List[str] = []
        neg_words: List[str] = []

        # 1. 在原文中定位全部情感词（子串扫描，最长非重叠匹配）
        # v2.5.0：经首字索引只遍历首字出现在文本中的词条，避免全词典扫描
        spans = []  # (start, end, word, category, strength)
        for ch in set(text):
            for word in self._sentiment_by_first.get(ch, ()):
                category, strength = self.sentiment_dict[word]
                for m in re.finditer(re.escape(word), text):
                    spans.append((m.start(), m.end(), word, category, strength))

        if spans:
            # 按起始位置排序；同一起始位置优先更长的词（如"不开心"优先于"开心"）
            spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
            picked = []
            last_end = -1
            for s in spans:
                if s[0] >= last_end:
                    picked.append(s)
                    last_end = s[1]

            for start, _end, word, category, strength in picked:
                negated = self._is_negated(text, start)
                degree = self._degree_before(text, start)
                actual_strength = -strength * degree if negated else strength * degree

                if actual_strength >= 0:
                    if category == "pos":
                        pos_score += actual_strength
                        pos_words.append(word)
                    else:
                        neg_score += actual_strength
                        neg_words.append(word)
                else:
                    if category == "pos":
                        neg_score += abs(actual_strength)
                        neg_words.append(word)
                    else:
                        pos_score += abs(actual_strength)
                        pos_words.append(word)

        # 2. Emoji 情感
        for emoji, category in self.emoji_dict.items():
            if emoji in text:
                if category == "positive":
                    pos_score += 3.0
                    pos_words.append(emoji)
                elif category == "negative":
                    neg_score += 3.0
                    neg_words.append(emoji)

        return pos_score, neg_score, pos_words, neg_words

    def _is_negated(self, text: str, start: int) -> bool:
        """判断情感词前是否是否定语境（基于原文字符窗口，约 3-4 个词）。

        依次匹配：
        1. 双字及以上否定词组（不会/没有/不行…）
        2. 单字否定符（不/没/无/别…）
        3. "非"（仅当后不接"常"，排除"非常"）
        """
        window_start = max(0, start - 12)
        context = text[window_start:start]
        if not context:
            return False

        # 1. 双字及以上否定词组
        for neg in self.negation_words:
            if len(neg) >= 2 and neg in context:
                return True

        # 2. 单字否定符
        for ch in self._NEGATION_CHARS:
            if ch in context:
                return True

        # 3. "非"作为否定词（后不接"常"）
        # v2.5.0 bugfix：m 的位置是相对 window（context）的，必须用
        # context[m.end()] 判断后一个字，之前用 text[m.end()] 在
        # window_start > 0 时会读到原文中毫不相干的字符。
        for m in re.finditer("非", context):
            if context[m.end():m.end() + 1] != "常":
                return True

        return False

    def _degree_before(self, text: str, start: int) -> float:
        """情感词前（约 6 字符）最近的程度副词权重，默认 1.0"""
        window_start = max(0, start - 6)
        context = text[window_start:start]
        max_degree = 1.0
        for word, degree in self.degree_words.items():
            if word in context:
                max_degree = max(max_degree, degree)
        return max_degree
