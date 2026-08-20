"""
RAG 引擎 v2.0.0

完全本地化的检索增强生成：
    - Embedder: 基于 sentence-transformers 的本地 embedding
    - VectorStore: 基于 ChromaDB 的持久化向量库
    - Retriever: top-K 检索 + 元数据过滤

无需云端 LLM，零数据外传。
"""

import sys
sys.dont_write_bytecode = True

from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.retriever import Retriever

__version__ = "2.1.0"

__all__ = ["Embedder", "VectorStore", "Retriever"]
