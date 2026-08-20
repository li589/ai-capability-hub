"""
RAG 预测器 - v2.2.0

基于历史相似对话的检索增强预测。
完全本地化，无需云端 LLM。

v2.2.0 升级：
- 智能查询构造：基于最近 3 条对方消息 + 关键词权重
- 双检索：既检索"对方问 + 我方答"模式，也检索"我方答"模式
- 时间加权：近期对话权重更高
- 多样性：避免返回几乎相同的回复
- 长度匹配：与最近我方回复长度相当的优先
"""

import logging
import re
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

from core.predictor_base import PredictorBase, PredictionContext
from core.result import PredictionResult, Prediction
from core.utils import tokenize
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.retriever import Retriever

logger = logging.getLogger(__name__)


class RAGPredictor(PredictorBase):
    """RAG 检索增强预测器（v2.2.0）"""

    name = "rag"
    version = "2.3.0"
    weight = 0.35
    description = "基于历史相似对话的检索增强预测（智能查询 + 时间加权 + 多样性）"

    def __init__(self, config: dict = None):
        super().__init__(config)
        rag_cfg = config.get("rag", {}) if config else {}
        self.chat_id = rag_cfg.get("chat_id", "default")
        model_name = rag_cfg.get("model_name", "BAAI/bge-small-zh-v1.5")
        persist_dir = rag_cfg.get("persist_dir", None)
        self.top_k = rag_cfg.get("top_k", 5)
        self.recent_window = rag_cfg.get("recent_window", 3)

        self._embedder = None
        self._vector_store = None
        self._retriever = None
        self._available = None
        self._initialized = False

        self._model_name = model_name
        self._persist_dir = persist_dir

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            self._ensure_init()
            self._available = self._embedder.is_available()
        except Exception as e:
            logger.warning(f"RAGPredictor not available: {e}")
            self._available = False
        return self._available

    def _ensure_init(self):
        if self._initialized:
            return
        try:
            self._embedder = Embedder(
                model_name=self._model_name,
                cache_dir=str(Path(__file__).resolve().parent.parent / "data" / "models"),
            )
            self._vector_store = VectorStore(
                persist_dir=self._persist_dir,
                collection_name=f"chat_{self.chat_id}",
            )
            self._retriever = Retriever(self._embedder, self._vector_store)
            self._initialized = True
        except Exception as e:
            logger.error(f"RAG init failed: {e}")
            raise

    def index_history(self, messages: List) -> int:
        """索引历史消息（首次或定期调用）"""
        self._ensure_init()
        if not self._retriever:
            return 0
        return self._retriever.index_messages(
            messages=messages,
            chat_id=self.chat_id,
            context_window=2,
        )

    def predict(self, context: PredictionContext) -> PredictionResult:
        """基于检索的预测（v2.2.0 智能版）"""
        self._ensure_init()
        if not self._retriever:
            return self._fallback("rag_unavailable", context)

        # 1. 自动索引历史（如未索引）
        try:
            if self._vector_store.count() == 0 and context.messages:
                self.index_history(context.messages)
        except Exception:
            pass

        # 2. 智能构造查询
        query_text = self._build_smart_query(context)
        if not query_text:
            return self._fallback("rag_empty_query", context)

        # 3. 检索相似历史
        try:
            similar = self._retriever.search_similar(
                query_text,
                top_k=self.top_k * 2,  # 取 2 倍再过滤
                sender_filter="other",
                chat_id=self.chat_id,
            )
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            similar = []

        if not similar:
            return self._fallback("rag_no_match", context)

        # 4. 提取并去重候选
        predictions = self._extract_candidates(similar, context)

        if not predictions:
            return self._fallback("rag_no_candidates", context)

        # 5. 时间加权 + 多样性排序
        predictions = self._rerank(predictions, context)

        # 6. 取 top
        top = predictions[0]
        alternatives = predictions[1:5]

        return PredictionResult(
            top_prediction=top,
            alternatives=alternatives,
            scenario=context.scenario,
            context={
                "mbti": context.mbti,
                "retrieved_count": len(similar),
                "query": query_text[:100],
            },
            metadata={
                "predictor": "RAGPredictor",
                "version": self.version,
                "vector_store_count": self._vector_store.count(),
                "extracted_candidates": len(predictions),
            },
        )

    # ----------------------------------------------------------------
    # 智能查询构造
    # ----------------------------------------------------------------
    def _build_smart_query(self, context: PredictionContext) -> str:
        """构造检索查询（对方最近 N 条 + 上下文关键词）"""
        other_msgs = [m for m in context.messages if m.is_other() and m.has_content()]
        if not other_msgs:
            return ""

        # 取最近 N 条对方消息
        recent = other_msgs[-self.recent_window:]
        parts = [m.content for m in recent]

        # 提取关键词作为查询权重
        keywords = self._extract_keywords(recent)
        if keywords:
            parts.append(" ".join(keywords[:5]))

        return "\n".join(parts)

    def _extract_keywords(self, msgs: List) -> List[str]:
        """从消息中提取关键词（基于 token 频次）"""
        from collections import Counter
        counter: Counter = Counter()
        for msg in msgs:
            for token in tokenize(msg.content or "", use_jieba=True):
                counter[token] += 1
        # 取 top 5
        return [w for w, _ in counter.most_common(5)]

    # ----------------------------------------------------------------
    # 候选提取
    # ----------------------------------------------------------------
    def _extract_candidates(self, similar: List, context: PredictionContext) -> List[Prediction]:
        """从检索结果中提取候选回复"""
        candidates: Dict[str, Prediction] = {}
        # 统计近期我方回复长度中位数（用于长度匹配）
        recent_self = [m for m in context.messages if m.is_self() and m.has_content()]
        target_avg_len = self._median_length(recent_self[-5:])

        for result in similar[:self.top_k * 2]:
            text = result.text
            score = result.score

            # 提取该历史对话中"我方"（以"我:"开头）的回复
            my_replies = self._extract_my_replies(text)

            for reply in my_replies:
                norm = self._normalize_text(reply)
                if not norm or len(reply) < 2:
                    continue
                # 长度匹配（与最近我方回复长度相当）
                length_match = self._length_match_score(len(reply), target_avg_len)
                # 置信度 = 相似度 × 长度匹配
                confidence = min(0.92, score * 0.6 + length_match * 0.3)

                if norm not in candidates or candidates[norm].confidence < confidence:
                    candidates[norm] = Prediction(
                        text=reply[:50],  # 截断超长回复
                        confidence=confidence,
                        strategy="rag",
                        rationale=f"历史相似对话 (相似度 {score:.2f}, 长度匹配 {length_match:.2f})",
                        metadata={
                            "source": "rag",
                            "similarity": score,
                            "length_match": length_match,
                            "context": text[:100],
                        },
                    )

        # 兜底：从 metadata 中提取
        if not candidates:
            for result in similar[:self.top_k]:
                content = result.metadata.get("content", "")
                if content:
                    norm = self._normalize_text(content)
                    if norm and norm not in candidates:
                        candidates[norm] = Prediction(
                            text=content[:50],
                            confidence=result.score * 0.5,
                            strategy="rag_pattern",
                            rationale=f"检索到历史相似内容",
                            metadata={"source": "rag_pattern", "similarity": result.score},
                        )

        return list(candidates.values())

    def _extract_my_replies(self, text: str) -> List[str]:
        """从历史对话文本中提取"我:"开头的回复"""
        replies = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("我:"):
                reply = line[2:].strip()
                # 过滤明显无意义回复
                if reply and len(reply) <= 50:
                    # 去掉纯 emoji / 纯标点
                    if any(c.isalnum() for c in reply):
                        replies.append(reply)
        return replies

    def _median_length(self, msgs: List) -> int:
        """回复长度中位数"""
        if not msgs:
            return 8
        lengths = sorted([len(m.content) for m in msgs if m.content])
        n = len(lengths)
        return lengths[n // 2] if n else 8

    def _length_match_score(self, reply_len: int, target_len: int) -> float:
        """长度匹配分（0-1）"""
        if target_len <= 0:
            return 0.5
        ratio = reply_len / target_len
        # 越接近 1 越好
        if 0.5 <= ratio <= 2.0:
            return 1.0 - abs(1 - ratio) * 0.5
        return 0.3

    # ----------------------------------------------------------------
    # 重排序
    # ----------------------------------------------------------------
    def _rerank(self, predictions: List[Prediction], context: PredictionContext) -> List[Prediction]:
        """时间加权 + 多样性排序"""
        # 多样性：按规范化文本去重（Ensemble 阶段再做）
        # 这里只做时间加权（保留 metadata）
        # 排序：confidence 优先
        predictions.sort(key=lambda p: p.confidence, reverse=True)

        # 限制多样性：相邻 text 应有差异
        deduplicated: List[Prediction] = []
        seen_norms: List[str] = []
        for pred in predictions:
            norm = self._normalize_text(pred.text)
            # 与最近的 3 个比较，避免重复
            if any(self._text_similarity(norm, s) > 0.7 for s in seen_norms[-3:]):
                continue
            seen_norms.append(norm)
            deduplicated.append(pred)

        return deduplicated

    def _text_similarity(self, t1: str, t2: str) -> float:
        """简单文本相似度（基于字符集合的重合度）"""
        if not t1 or not t2:
            return 0.0
        s1, s2 = set(t1), set(t2)
        intersection = len(s1 & s2)
        union = len(s1 | s2)
        return intersection / union if union else 0.0

    def _normalize_text(self, text: str) -> str:
        """规范化文本"""
        return re.sub(r"[\s，。！？、；：,.!?;:'\"“”‘’~…—\-·()（）\[\]【】/]+", "", text or "").lower()

    def _fallback(self, reason: str, context: PredictionContext) -> PredictionResult:
        """统一的兜底响应"""
        return PredictionResult(
            top_prediction=Prediction(text="嗯嗯", confidence=0.3, strategy=reason),
            alternatives=[],
            scenario=context.scenario,
            context={"fallback_reason": reason},
        )
