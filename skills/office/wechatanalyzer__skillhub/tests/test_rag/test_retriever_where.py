"""rag.retriever 角色过滤回归测试（v2.5.0）

修复：rag_predictor 传 sender_filter="other" 时，search_similar 曾按原始
sender 名（如"小王"）精确匹配，真实昵称永远匹配不上 → RAG 一直空检索。

本测试用 Fake 组件注入（不依赖 sentence-transformers/chromadb），
验证：
- index_messages 写入 sender_role 元数据
- sender_filter="self"/"other" 按角色过滤（where 使用 sender_role）
- 旧向量库无 sender_role 时自动降级重试（去掉角色过滤）
- 其他 sender_filter 值仍按原始 sender 名匹配（向后兼容）
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from rag.retriever import Retriever, SearchResult


class FakeEmbedder:
    """假 embedder：返回固定向量"""

    def __init__(self, available=True):
        self._available = available

    def is_available(self):
        return self._available

    def embed(self, documents):
        return [[0.0] for _ in documents]

    def embed_query(self, query):
        return [0.0]


class FakeVectorStore:
    """假向量库：记录 query 的 where 条件，可配置返回空结果"""

    def __init__(self):
        self.queries = []
        self.empty_once = False  # 第一次查询返回空（模拟旧库无 sender_role）

    def query(self, query_embedding=None, top_k=None, where=None, **kw):
        self.queries.append(where)
        if self.empty_once and len(self.queries) == 1:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        return {
            "ids": [["d1"]],
            "documents": [["TA: 在吗\n我: 在的"]],
            "metadatas": [[{"sender": "小王", "sender_role": "other"}]],
            "distances": [[0.2]],
        }

    def add(self, **kw):
        pass

    def count(self):
        return 0


class TestRetrieverSenderRole(unittest.TestCase):
    """sender_role 角色过滤（v2.5.0 bugfix）"""

    def _make_retriever(self, store):
        return Retriever(FakeEmbedder(), store)

    def test_index_metadata_contains_sender_role(self):
        """索引时写入 sender_role"""
        msgs = [
            Message(sender="小王", content="在吗"),
            Message(sender="self", content="在的"),
        ]
        store = FakeVectorStore()
        # 拦截 embedder 与 vector_store.add，检查 metadatas
        import rag.retriever as retriever_mod
        orig_add = store.add
        captured = []

        def fake_add(ids=None, embeddings=None, documents=None, metadatas=None, **kw):
            captured.extend(metadatas or [])

        store.add = fake_add
        r = self._make_retriever(store)
        r.index_messages(msgs, chat_id="c1")
        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0]["sender_role"], "other")  # 小王 → other
        self.assertEqual(captured[1]["sender_role"], "self")   # self → self
        self.assertEqual(captured[0]["sender"], "小王")        # 原始名保留

    def test_sender_filter_other_uses_role(self):
        """sender_filter='other' 用 sender_role 过滤（此前按原始名永远匹配不上）"""
        store = FakeVectorStore()
        r = self._make_retriever(store)
        results = r.search_similar("在吗", top_k=5, sender_filter="other", chat_id="c1")
        self.assertEqual(len(results), 1)
        self.assertEqual(store.queries[0].get("sender_role"), "other")
        self.assertEqual(store.queries[0].get("chat_id"), "c1")
        self.assertNotIn("sender", store.queries[0])  # 不再按原始 sender 名匹配

    def test_sender_filter_self_uses_role(self):
        """sender_filter='self' 同样按角色过滤"""
        store = FakeVectorStore()
        r = self._make_retriever(store)
        r.search_similar("在吗", sender_filter="self")
        self.assertEqual(store.queries[0].get("sender_role"), "self")

    def test_raw_sender_name_still_supported(self):
        """其他值（真实昵称）仍按原始 sender 名精确匹配（向后兼容）"""
        store = FakeVectorStore()
        r = self._make_retriever(store)
        r.search_similar("在吗", sender_filter="小王")
        self.assertEqual(store.queries[0].get("sender"), "小王")
        self.assertNotIn("sender_role", store.queries[0])

    def test_fallback_when_old_store_lacks_sender_role(self):
        """旧向量库无 sender_role 字段：首次空结果 → 自动去掉角色过滤重试"""
        store = FakeVectorStore()
        store.empty_once = True
        r = self._make_retriever(store)
        results = r.search_similar("在吗", sender_filter="other")
        self.assertEqual(len(results), 1)
        self.assertEqual(len(store.queries), 2, "应重试第二次查询")
        # 去掉角色过滤后 where 为空 → 传给向量库的是 None（无过滤）
        self.assertIsNone(store.queries[1])

    def test_parse_raw_result(self):
        """_parse_raw 正确解析余弦距离 → 相似度"""
        raw = {
            "ids": [["a", "b"]],
            "documents": [["doc a", "doc b"]],
            "metadatas": [[{"sender": "x"}, {"sender": "y"}]],
            "distances": [[0.1, 0.9]],
        }
        results = Retriever._parse_raw(raw)
        self.assertEqual(len(results), 2)
        self.assertAlmostEqual(results[0].score, 0.9, places=4)
        self.assertAlmostEqual(results[1].score, 0.1, places=4)
        self.assertIsInstance(results[0], SearchResult)

    def test_parse_raw_empty(self):
        self.assertEqual(Retriever._parse_raw({}), [])
        self.assertEqual(Retriever._parse_raw({"ids": [[]]}), [])


if __name__ == "__main__":
    unittest.main()
