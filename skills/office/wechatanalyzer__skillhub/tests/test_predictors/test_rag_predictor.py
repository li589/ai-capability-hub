"""predictors.rag_predictor 单元测试（v2.3.0 补全）

RAGPredictor 依赖 sentence-transformers/chromadb（可选未安装）。
本测试聚焦不依赖 RAG 引擎的纯逻辑方法：
- 查询构造（_build_smart_query / _extract_keywords）
- 候选提取（_extract_candidates / _extract_my_replies / 长度匹配）
- 重排序（_rerank / _text_similarity / _normalize_text）
- 兜底与可用性（_fallback / is_available 降级）
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictionContext
from core.result import Prediction, PredictionResult
from predictors.rag_predictor import RAGPredictor


class TestRAGNormalize(unittest.TestCase):
    """文本规范化 / 相似度"""

    def setUp(self):
        self.p = RAGPredictor(config={})

    def test_normalize_text(self):
        self.assertEqual(self.p._normalize_text(" 你好！世界，" ), "你好世界")
        self.assertEqual(self.p._normalize_text("HELLO，世界"), "hello世界")

    def test_normalize_empty(self):
        self.assertEqual(self.p._normalize_text(""), "")
        self.assertEqual(self.p._normalize_text(None), "")

    def test_text_similarity_identical(self):
        self.assertEqual(self.p._text_similarity("你好", "你好"), 1.0)

    def test_text_similarity_partial(self):
        s = self.p._text_similarity("你好世界", "你好")
        self.assertGreater(s, 0.0)
        self.assertLess(s, 1.0)

    def test_text_similarity_empty(self):
        self.assertEqual(self.p._text_similarity("", "abc"), 0.0)
        self.assertEqual(self.p._text_similarity("abc", ""), 0.0)


class TestRAGQuery(unittest.TestCase):
    """查询构造 / 关键词提取"""

    def setUp(self):
        self.p = RAGPredictor(config={})
        self.ctx = PredictionContext(
            messages=[
                Message(sender="other", content="周末有空吗？"),
                Message(sender="self", content="有啊"),
                Message(sender="other", content="一起吃饭吧"),
            ],
            scenario="social",
        )

    def test_build_smart_query_uses_recent_other(self):
        q = self.p._build_smart_query(self.ctx)
        self.assertIn("周末有空吗", q)
        self.assertIn("一起吃饭吧", q)

    def test_build_smart_query_no_other(self):
        ctx = PredictionContext(messages=[Message(sender="self", content="hi")])
        self.assertEqual(self.p._build_smart_query(ctx), "")

    def test_build_smart_query_empty_messages(self):
        self.assertEqual(self.p._build_smart_query(PredictionContext(messages=[])), "")

    def test_extract_keywords(self):
        msgs = [Message(sender="other", content="周末周末一起玩")]
        kws = self.p._extract_keywords(msgs)
        self.assertIsInstance(kws, list)
        self.assertGreaterEqual(len(kws), 1)

    def test_extract_keywords_empty(self):
        self.assertEqual(self.p._extract_keywords([]), [])


class TestRAGCandidates(unittest.TestCase):
    """候选提取与重排序"""

    def setUp(self):
        self.p = RAGPredictor(config={})
        self.ctx = PredictionContext(
            messages=[
                Message(sender="other", content="这周忙吗"),
                Message(sender="self", content="还行，有事吗"),
                Message(sender="other", content="想约你出来"),
            ],
            scenario="social",
        )

    def test_extract_my_replies(self):
        text = "对方: 在吗\n我: 在的\n对方: 忙吗\n我: 不忙"
        replies = self.p._extract_my_replies(text)
        self.assertIn("在的", replies)
        self.assertIn("不忙", replies)

    def test_extract_my_replies_filters_junk(self):
        text = "对方: hi\n我: 。。\n我: 👍"
        replies = self.p._extract_my_replies(text)
        # 纯标点 / 纯 emoji 应被过滤
        self.assertEqual(replies, [])

    def test_median_length(self):
        self.assertEqual(self.p._median_length([]), 8)
        msgs = [Message(sender="self", content="ab"), Message(sender="self", content="abcd")]
        self.assertEqual(self.p._median_length(msgs), 4)

    def test_length_match_score(self):
        self.assertEqual(self.p._length_match_score(10, 10), 1.0)
        self.assertEqual(self.p._length_match_score(100, 10), 0.3)
        self.assertEqual(self.p._length_match_score(10, 0), 0.5)

    def test_extract_candidates_from_my_replies(self):
        similar = [
            SimpleNamespace(
                text="我: 一起吃饭\n对方: 好啊",
                score=0.8,
                metadata={"content": "备用"},
            )
        ]
        preds = self.p._extract_candidates(similar, self.ctx)
        self.assertTrue(preds)
        self.assertEqual(preds[0].strategy, "rag")
        self.assertIn("一起吃饭", preds[0].text)

    def test_extract_candidates_fallback_metadata(self):
        similar = [
            SimpleNamespace(
                text="对方: 在吗",  # 无"我:"行
                score=0.7,
                metadata={"content": "我: 备用回复内容"},
            )
        ]
        preds = self.p._extract_candidates(similar, self.ctx)
        self.assertTrue(preds)
        self.assertEqual(preds[0].strategy, "rag_pattern")

    def test_extract_candidates_empty(self):
        self.assertEqual(self.p._extract_candidates([], self.ctx), [])

    def test_rerank_deduplicates_similar(self):
        preds = [
            Prediction(text="周末一起去看电影吧", confidence=0.9, strategy="rag"),
            Prediction(text="周末一起去看电影吧！", confidence=0.85, strategy="rag"),
            Prediction(text="周末一起去吃饭吧", confidence=0.8, strategy="rag"),
        ]
        out = self.p._rerank(preds, self.ctx)
        # 相似文本去重后至少保留 1 条
        self.assertGreaterEqual(len(out), 1)
        self.assertEqual(out[0].confidence, 0.9)

    def test_fallback(self):
        r = self.p._fallback("test", self.ctx)
        self.assertIsInstance(r, PredictionResult)
        self.assertEqual(r.top_prediction.text, "嗯嗯")
        self.assertEqual(r.context["fallback_reason"], "test")


class TestRAGAvailability(unittest.TestCase):
    """可用性与 predict 兜底"""

    def test_is_available_false_on_init_error(self):
        p = RAGPredictor(config={})
        with mock.patch.object(RAGPredictor, "_ensure_init",
                               side_effect=RuntimeError("no chromadb")):
            self.assertFalse(p.is_available())

    def test_predict_fallback_when_retriever_missing(self):
        p = RAGPredictor(config={})
        with mock.patch.object(RAGPredictor, "_ensure_init") as mi:
            mi.side_effect = lambda: setattr(p, "_retriever", None)
            ctx = PredictionContext(
                messages=[Message(sender="other", content="在吗")],
                scenario="social",
            )
            r = p.predict(ctx)
        self.assertEqual(r.top_prediction.text, "嗯嗯")
        self.assertIn("rag", r.context["fallback_reason"])


if __name__ == "__main__":
    unittest.main()
