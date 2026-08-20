"""
本地向量存储 - v2.0.0

基于 ChromaDB 的持久化向量库。
按 chat_id 分 collection，支持元数据过滤。
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class VectorStore:
    """本地向量存储

    Args:
        persist_dir: 持久化目录
        collection_name: collection 名称（每个 chat_id 一个）
    """

    def __init__(
        self,
        persist_dir: str = None,
        collection_name: str = "default",
    ):
        if persist_dir is None:
            persist_dir = str(Path(__file__).resolve().parent.parent / "data" / "vector_store")
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        os.makedirs(persist_dir, exist_ok=True)

        self._client = None
        self._collection = None

    @property
    def client(self):
        if self._client is None:
            self._init_client()
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._init_client()
        return self._collection

    def _init_client(self):
        """初始化 ChromaDB 客户端"""
        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # 余弦相似度
            )
        except ImportError:
            raise ImportError(
                "chromadb not installed. Run: pip install chromadb"
            )

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]] = None,
    ) -> None:
        """添加文档到向量库

        Args:
            ids: 文档 ID 列表
            embeddings: embedding 向量列表
            documents: 文档原文列表
            metadatas: 元数据列表（可选）
        """
        if metadatas is None:
            metadatas = [{} for _ in ids]
        # ChromaDB 的 metadata 值必须可序列化
        clean_metadatas = []
        for m in metadatas:
            clean_m = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_m[k] = v
                elif v is None:
                    continue
                else:
                    clean_m[k] = str(v)
            clean_metadatas.append(clean_m)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_metadatas,
        )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """查询相似文档

        Args:
            query_embedding: 查询向量
            top_k: 返回 top-K
            where: 元数据过滤

        Returns:
            {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]], 'distances': [[...]]}
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

    def count(self) -> int:
        """文档数量"""
        return self.collection.count()

    def delete(self, ids: List[str] = None, where: Dict[str, Any] = None) -> None:
        """删除文档"""
        if ids:
            self.collection.delete(ids=ids)
        elif where:
            self.collection.delete(where=where)
        else:
            raise ValueError("Must provide ids or where")

    def reset(self) -> None:
        """清空 collection"""
        self.client.delete_collection(self.collection_name)
        self._collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
