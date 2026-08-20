"""
检索器 - v2.0.0

提供：
- 单条消息检索
- 对话对检索（用于预测上下文）
- 元数据过滤（sender, time range, etc.）
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.message import Message
from rag.embedder import Embedder
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """检索结果"""
    text: str
    score: float  # 相似度，0-1
    metadata: Dict[str, Any]
    id: str


class Retriever:
    """检索器

    Args:
        embedder: Embedder 实例
        vector_store: VectorStore 实例
    """

    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def is_available(self) -> bool:
        return self.embedder.is_available()

    def index_messages(
        self,
        messages: List[Message],
        chat_id: str = "default",
        context_window: int = 2,
    ) -> int:
        """将消息索引到向量库

        Args:
            messages: 消息列表
            chat_id: 聊天 ID（用于 collection 隔离）
            context_window: 上下文窗口（前后各 N 条拼接）

        Returns:
            索引的消息数
        """
        if not messages:
            return 0

        ids = []
        documents = []
        metadatas = []

        for i, msg in enumerate(messages):
            if not msg.has_content():
                continue
            # 拼接上下文
            start = max(0, i - context_window)
            end = min(len(messages), i + context_window + 1)
            context_msgs = messages[start:end]
            doc_text = "\n".join(
                f"{'我' if m.is_self() else 'TA'}: {m.content}"
                for m in context_msgs
            )
            doc_id = f"{chat_id}_{i}_{msg.timestamp.isoformat() if msg.timestamp else i}"
            ids.append(doc_id)
            documents.append(doc_text)
            metadatas.append({
                "chat_id": chat_id,
                "index": i,
                "sender": msg.sender,
                # v2.5.0：记录角色（self/other），供 search_similar 做角色过滤。
                # 之前 rag_predictor 传 sender_filter="other" 时按原始 sender
                # 名精确匹配，真实昵称（如"小王"）永远匹配不上，RAG 一直空检索。
                "sender_role": "self" if msg.is_self() else "other",
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else "",
            })

        if not documents:
            return 0

        # 生成 embeddings
        try:
            embeddings = self.embedder.embed(documents)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return 0

        # 添加到向量库
        try:
            self.vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as e:
            logger.error(f"Vector store add failed: {e}")
            return 0

        return len(documents)

    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        sender_filter: str = None,
        chat_id: str = None,
    ) -> List[SearchResult]:
        """检索相似消息

        Args:
            query: 查询文本
            top_k: top-K
            sender_filter: 发送者过滤。
                'self' / 'other' 按角色过滤（v2.5.0，新增 sender_role 元数据），
                其他值按原始 sender 名精确匹配（向后兼容）。
            chat_id: 聊天 ID 过滤

        Returns:
            SearchResult 列表，按相似度降序
        """
        if not self.is_available():
            return []

        # 生成查询 embedding
        try:
            query_emb = self.embedder.embed_query(query)
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return []

        # 构建 where 条件
        where = {}
        if sender_filter in ("self", "other"):
            where["sender_role"] = sender_filter
        elif sender_filter:
            where["sender"] = sender_filter
        if chat_id:
            where["chat_id"] = chat_id

        # 查询
        raw = self._run_query(query_emb, top_k, where)

        # v2.5.0：兼容旧向量库——若按 sender_role 过滤结果为空（旧库无该字段），
        # 去掉角色过滤重试，保证升级后 RAG 仍有检索结果而非静默空转。
        if (not raw or not raw.get("ids") or not raw["ids"][0]) and where.get("sender_role"):
            compat_where = {k: v for k, v in where.items() if k != "sender_role"}
            raw = self._run_query(query_emb, top_k, compat_where)

        return self._parse_raw(raw)

    def _run_query(self, query_emb, top_k: int, where: Dict[str, Any]) -> Dict[str, Any]:
        """执行一次向量查询，失败时返回空 dict"""
        try:
            return self.vector_store.query(
                query_embedding=query_emb,
                top_k=top_k,
                where=where if where else None,
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {}

    @staticmethod
    def _parse_raw(raw: Dict[str, Any]) -> List["SearchResult"]:
        """把向量库原始结果解析为 SearchResult 列表（各键容错缺失）"""
        results = []
        if not raw:
            return results

        ids = (raw.get("ids") or [[]])[0]
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]

        for i, doc_id in enumerate(ids):
            # cosine distance → similarity (1 - distance)
            similarity = 1.0 - distances[i] if i < len(distances) else 0.0
            results.append(SearchResult(
                text=docs[i] if i < len(docs) else "",
                score=round(similarity, 4),
                metadata=metas[i] if i < len(metas) else {},
                id=doc_id,
            ))

        return results

    def search_similar_pairs(
        self,
        query_message: Message,
        top_k: int = 3,
        chat_id: str = None,
    ) -> List[Dict[str, Any]]:
        """检索相似对话对（对方说的 + 我回应的）

        Returns:
            [{'query': '...', 'response': '...', 'score': 0.85}, ...]
        """
        if not query_message.has_content():
            return []

        # 检索相似消息
        similar = self.search_similar(
            query_message.content,
            top_k=top_k * 3,  # 多检索一些
            sender_filter=query_message.sender,
            chat_id=chat_id,
        )

        # 尝试配对（找相邻消息作为回复）
        pairs = []
        for result in similar:
            # 简化处理：返回检索结果本身，后续可以扩展为配对
            pairs.append({
                "context": result.text,
                "score": result.score,
                "metadata": result.metadata,
            })

        return pairs[:top_k]
