"""rag.vector_store 单元测试（v2.3.0 补全）

VectorStore 依赖 chromadb（可选）。本测试通过注入 FakeClient/FakeCollection
验证纯逻辑：metadata 清洗、add/query/count/delete/reset 委托、缺依赖时友好报错。
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.vector_store import VectorStore


class FakeCollection:
    """记录调用参数的假 collection"""

    def __init__(self):
        self.added = []
        self.queried = []
        self.deleted = []
        self._count = 0

    def add(self, ids=None, embeddings=None, documents=None, metadatas=None, **kw):
        self.added.append((ids, embeddings, documents, metadatas))
        self._count += len(ids or [])

    def query(self, query_embeddings=None, n_results=None, where=None, **kw):
        self.queried.append((query_embeddings, n_results, where))
        return {
            "ids": [["d1"]],
            "documents": [["doc1"]],
            "metadatas": [[{"k": "v"}]],
            "distances": [[0.1]],
        }

    def count(self):
        return self._count

    def delete(self, ids=None, where=None, **kw):
        self.deleted.append((ids, where))
        self._count -= 1


class FakeClient:
    def __init__(self, col):
        self.col = col
        self.delete_calls = []

    def get_or_create_collection(self, name=None, metadata=None, **kw):
        return self.col

    def delete_collection(self, name=None):
        self.delete_calls.append(name)


class TestVectorStore(unittest.TestCase):
    """VectorStore 纯逻辑测试"""

    def _make_store(self):
        col = FakeCollection()
        client = FakeClient(col)
        vs = VectorStore(persist_dir=str(Path(tempfile.mkdtemp())))
        vs._client = client
        vs._collection = col
        return vs, col, client

    def test_init_creates_dir(self):
        tmp = Path(tempfile.mkdtemp()) / "sub" / "store"
        VectorStore(persist_dir=str(tmp))
        self.assertTrue(tmp.is_dir())

    def test_add_cleans_metadata(self):
        vs, col, _ = self._make_store()
        vs.add(
            ids=["1"],
            embeddings=[[0.1, 0.2]],
            documents=["doc"],
            metadatas=[{"ok": "str", "num": 3, "pi": 3.14, "flag": True,
                        "none": None, "nested": {"a": 1}, "list": [1, 2]}],
        )
        _, _, _, meta = col.added[0]
        cleaned = meta[0]
        self.assertEqual(cleaned["ok"], "str")
        self.assertEqual(cleaned["num"], 3)
        self.assertEqual(cleaned["flag"], True)
        self.assertNotIn("none", cleaned, "None 值应被丢弃")
        self.assertEqual(cleaned["nested"], "{'a': 1}", "不可序列化应转 str")

    def test_add_default_metadata(self):
        vs, col, _ = self._make_store()
        vs.add(ids=["1"], embeddings=[[0.1]], documents=["doc"])
        _, _, _, meta = col.added[0]
        self.assertEqual(meta, [{}])

    def test_query_delegates(self):
        vs, col, _ = self._make_store()
        result = vs.query([0.1, 0.2], top_k=3, where={"k": "v"})
        self.assertEqual(result["ids"], [["d1"]])
        _qe, n_results, where = col.queried[0]
        self.assertEqual(n_results, 3)
        self.assertEqual(where, {"k": "v"})

    def test_count(self):
        vs, col, _ = self._make_store()
        col._count = 5
        self.assertEqual(vs.count(), 5)

    def test_delete_by_ids(self):
        vs, col, _ = self._make_store()
        vs.delete(ids=["1", "2"])
        self.assertEqual(col.deleted, [(["1", "2"], None)])

    def test_delete_by_where(self):
        vs, col, _ = self._make_store()
        vs.delete(where={"source": "x"})
        self.assertEqual(col.deleted, [(None, {"source": "x"})])

    def test_delete_raises_without_args(self):
        vs, _, _ = self._make_store()
        with self.assertRaises(ValueError):
            vs.delete()

    def test_reset(self):
        vs, col, client = self._make_store()
        vs.reset()
        self.assertEqual(client.delete_calls, [vs.collection_name])
        self.assertIsNotNone(vs.collection)

    def test_import_error_without_chromadb(self):
        vs = VectorStore(persist_dir=str(Path(tempfile.mkdtemp())))
        # 未安装 chromadb（或 import 被阻断）时给出友好提示
        with mock.patch.dict(sys.modules, {"chromadb": None}):
            with self.assertRaises(ImportError) as ctx:
                _ = vs.collection
        self.assertIn("chromadb", str(ctx.exception))

    def test_default_persist_dir(self):
        vs = VectorStore()
        # 默认持久化到 <技能根>/data/vector_store
        expected = Path(__file__).resolve().parent.parent.parent / "data" / "vector_store"
        self.assertEqual(Path(vs.persist_dir), expected)


if __name__ == "__main__":
    unittest.main()
