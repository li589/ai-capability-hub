"""rag.retriever 单元测试（依赖检查）"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message


def _check_dependencies():
    try:
        import sentence_transformers  # noqa
        import chromadb  # noqa
        return True
    except ImportError:
        return False


@unittest.skipUnless(_check_dependencies(), "sentence-transformers/chromadb not installed")
class TestRetriever(unittest.TestCase):
    """Retriever 测试（需要 sentence-transformers + chromadb）"""

    def test_skip_when_no_dependencies(self):
        """跳过如果没有依赖"""
        if not _check_dependencies():
            self.skipTest("Dependencies not available")

    def test_create_components(self):
        """创建组件"""
        from rag.embedder import Embedder
        from rag.vector_store import VectorStore
        from rag.retriever import Retriever

        e = Embedder()
        vs = VectorStore(
            persist_dir=str(Path(__file__).parent / "tmp_chroma"),
            collection_name="test",
        )
        r = Retriever(e, vs)
        self.assertIsNotNone(r)


if __name__ == "__main__":
    unittest.main()
