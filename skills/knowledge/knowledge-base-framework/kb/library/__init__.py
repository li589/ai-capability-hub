"""
KB Library Module
=================

High-level library functions for KB Framework.
Contains knowledge base integrations and utilities.

Public API:
-----------
- kb.library.knowledge_base: Search, indexing, and retrieval
"""

from kb.library.knowledge_base import (
    HybridSearch,
    ChromaIntegration,
    EmbeddingPipeline,
    Reranker,
    Chunk,
    SynonymExpander,
    StopwordHandler,
    ChromaDBPlugin,
    SearchResult,
    SearchConfig,
)

__all__ = [
    # Main search class
    'HybridSearch',
    # ChromaDB integration
    'ChromaIntegration',
    # Embedding pipeline
    'EmbeddingPipeline',
    # Reranking
    'Reranker',
    # Chunker
    'Chunk',
    'SentenceChunker',
    'SimpleChunker',
    # Synonyms
    'SynonymExpander',
    # Stopwords
    'StopwordHandler',
    # Chroma Plugin
    'ChromaDBPlugin',
    # Search result types
    'SearchResult',
    'SearchConfig',
]