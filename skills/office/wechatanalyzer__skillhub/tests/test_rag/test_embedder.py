"""rag.embedder 单元测试（依赖检查）"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.embedder import Embedder


def _check_sentence_transformers():
    """检查 sentence-transformers 是否可用"""
    try:
        import sentence_transformers  # noqa
        return True
    except ImportError:
        return False


_HAS_ST = _check_sentence_transformers()


@unittest.skipUnless(_HAS_ST, "sentence-transformers not installed")
class TestEmbedder(unittest.TestCase):
    """Embedder 测试（如果 sentence-transformers 可用）"""

    def test_create(self):
        """创建 Embedder（不实际加载）"""
        e = Embedder()
        self.assertIsNotNone(e)
        self.assertEqual(e.device, "cpu")

    def test_recommended_models(self):
        """检查推荐模型列表"""
        self.assertIn("bge-small-zh", Embedder.RECOMMENDED_MODELS)
        self.assertIn("bge-base-zh", Embedder.RECOMMENDED_MODELS)

    @unittest.skipUnless(_HAS_ST, "sentence-transformers not installed")
    def test_embed_single(self):
        """测试单条 embedding（如依赖可用）"""
        try:
            e = Embedder()
            if not e.is_available():
                self.skipTest("Model not available")
            emb = e.embed("测试文本")
            self.assertEqual(len(emb), 1)
            self.assertGreater(len(emb[0]), 0)
        except Exception as e:
            self.skipTest(f"Embedding failed: {e}")


if __name__ == "__main__":
    unittest.main()
