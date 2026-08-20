"""
本地 Embedder - v2.0.0

基于 sentence-transformers 加载本地 embedding 模型。
首次使用时自动下载（约 50-100MB），之后完全离线运行。

推荐模型：
- BAAI/bge-small-zh-v1.5: 95MB，中文优化
- paraphrase-multilingual-MiniLM-L12-v2: 50MB，多语言
"""

import os
from pathlib import Path
from typing import List, Union
import logging

logger = logging.getLogger(__name__)


class Embedder:
    """本地 Embedding 模型封装

    Args:
        model_name: 模型名称或本地路径
        device: 'cpu' / 'cuda'
        cache_dir: 模型缓存目录
    """

    # 推荐的模型
    RECOMMENDED_MODELS = {
        "bge-small-zh": "BAAI/bge-small-zh-v1.5",  # 95MB, 中文
        "bge-base-zh": "BAAI/bge-base-zh-v1.5",    # 400MB, 中文更准
        "minilm-multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # 50MB
    }

    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"

    def __init__(
        self,
        model_name: str = None,
        device: str = "cpu",
        cache_dir: str = None,
    ):
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        # 默认缓存到项目目录下的 models/
        if cache_dir is None:
            cache_dir = str(Path(__file__).resolve().parent.parent / "data" / "models")
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        self._model = None
        self._available = None  # None=未检查, True/False

    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self):
        """加载 sentence-transformers 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir,
            )
            logger.info(f"Model loaded successfully")
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def is_available(self) -> bool:
        """检查模型是否可用"""
        if self._available is not None:
            return self._available
        try:
            # 尝试加载（首次会下载）
            _ = self.model
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """生成 embedding

        Args:
            texts: 单条文本或文本列表

        Returns:
            embedding 向量列表
        """
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # 归一化，便于余弦相似度
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """为查询生成 embedding（部分模型有特殊处理）"""
        return self.embed(query)[0]

    def get_dimension(self) -> int:
        """获取 embedding 维度"""
        return self.model.get_sentence_embedding_dimension()
