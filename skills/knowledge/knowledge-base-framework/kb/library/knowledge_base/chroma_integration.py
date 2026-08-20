"""
ChromaDB Integration for Lumens Knowledge Base
===============================================

Phase 1: Vector Search Foundation
Local ChromaDB instance with SQLite as primary store.

Embedding model: sentence-transformers/all-MiniLM-L6-v2
Dimensionality: 384

Source: KB_Erweiterungs_Plan.md (Phase 1)
"""

import chromadb
from chromadb.config import Settings
from chromadb.errors import NotFoundError as ChromaNotFoundError
from pathlib import Path
import logging
from typing import Optional
from contextlib import contextmanager

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from kb.base.config import KBConfig
    _default_chroma_path = str(KBConfig.get_instance().chroma_path)
except ImportError:
    _default_chroma_path = str(Path.home() / ".openclaw" / "kb" / "chroma_db")

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaIntegration:
    """
    ChromaDB wrapper for knowledge base integration.
    
    Responsibility:
    - Connection management to ChromaDB
    - Collection creation/retrieval
    - Embedding function (all-MiniLM-L6-v2)
    """
    
    # Singleton instance
    _instance: Optional['ChromaIntegration'] = None
    
    def __init__(
        self, 
        chroma_path: str = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize ChromaDB connection.
        
        Args:
            chroma_path: Path for persistent ChromaDB instance
            model_name: Embedding model (Hugging Face model name)
        """
        if chroma_path is None:
            self.chroma_path = Path(_default_chroma_path)
        else:
            self.chroma_path = Path(chroma_path).expanduser()
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self._model = None
        self._client = None
        
        logger.info(f"ChromaIntegration init: path={self.chroma_path}, model={model_name}")
    
    @property
    def client(self) -> chromadb.PersistentClient:
        """Lazy-load ChromaDB Client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("ChromaDB Client initialized")
        return self._client
    
    @property
    def model(self):
        """Lazy-load Sentence Transformer Model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Sentence Transformer loaded: {self.model_name}")
        return self._model
    
    def embed_text(self, text: str) -> list[float]:
        """
        Converts text to vector embedding.
        
        Args:
            text: Input text
            
        Returns:
            Normalized embedding vector (384 dimensions)
        """
        if not text or not text.strip():
            return [0.0] * 384
        return self.model.encode(
            text, 
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Batch embedding for multiple texts.
        
        Args:
            texts: List of texts
            batch_size: Batch size for inference
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=True
        ).tolist()
    
    # -------------------------------------------------------------------------
    # Phase 4: Alternative Embedding Model
    # -------------------------------------------------------------------------
    
    @property
    def alternative_model_name(self) -> str:
        """Phase 4: Alternative model name for better multilingual support."""
        return "paraphrase-multilingual-MiniLM-L12-v2"
    
    def embed_text_v2(self, text: str) -> list[float]:
        """
        Embed text using the alternative multilingual model.
        
        Phase 4: paraphrase-multilingual-MiniLM-L12-v2
        Better for mixed German/English content.
        
        Args:
            text: Input text
            
        Returns:
            Normalized embedding vector (384 dimensions)
        """
        if not text or not text.strip():
            return [0.0] * 384
        
        model = SentenceTransformer(self.alternative_model_name)
        return model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()
    
    def embed_batch_v2(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Batch embedding using the alternative multilingual model.
        
        Phase 4: paraphrase-multilingual-MiniLM-L12-v2
        
        Args:
            texts: List of texts
            batch_size: Batch size for inference
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        model = SentenceTransformer(self.alternative_model_name)
        return model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=True
        ).tolist()
    
    def switch_to_v2_model(self) -> 'ChromaIntegration':
        """
        Create a new ChromaIntegration instance with the V2 (multilingual) model.
        
        Phase 4: Returns new instance with paraphrase-multilingual-MiniLM-L12-v2.
        Does NOT modify existing instance (immutable switch).
        
        Returns:
            New ChromaIntegration with V2 model
        """
        new_instance = ChromaIntegration(
            chroma_path=str(self.chroma_path),
            model_name=self.alternative_model_name
        )
        logger.info(f"Switched to V2 model: {self.alternative_model_name}")
        return new_instance
    
    # -------------------------------------------------------------------------
    # Collection Management
    # -------------------------------------------------------------------------
    
    def get_or_create_collection(
        self, 
        name: str, 
        metadata: Optional[dict] = None
    ) -> chromadb.Collection:
        """
        Creates or retrieves a collection.
        
        Args:
            name: Collection name
            metadata: Optional metadata
            
        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Collection retrieved: {name}")
        except ChromaNotFoundError:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {"description": f"Collection: {name}"}
            )
            logger.info(f"Collection created: {name}")
        
        return collection
    
    def delete_collection(self, name: str) -> bool:
        """
        Deletes a collection.
        
        Args:
            name: Collection name
            
        Returns:
            True if deleted
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Collection deleted: {name}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete collection {name}: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # Pre-configured Collections
    # -------------------------------------------------------------------------
    
    # Alternative embedding models
    # Phase 4: paraphrase-multilingual-MiniLM-L12-v2 (better multilingual, 384 dim)
    ALTERNATIVE_MODELS = {
        "paraphrase-multilingual-MiniLM-L12-v2": {
            "dimension": 384,
            "description": "Better multilingual support, recommended for mixed DE/EN content"
        }
    }
    
    # Phase 4: V2 Collection for new model
    @property
    def sections_collection(self) -> chromadb.Collection:
        """Collection for file_sections embeddings (original model)."""
        return self.get_or_create_collection(
            name="kb_sections",
            metadata={
                "description": "Knowledge Base Sections Embeddings",
                "embedding_model": self.model_name,
                "dimension": 384
            }
        )
    
    @property
    def sections_collection_v2(self) -> chromadb.Collection:
        """
        Collection for file_sections embeddings using paraphrase-multilingual-MiniLM-L12-v2.
        
        Phase 4: New embedding model with better multilingual support.
        768 → 384 dimensions (MiniLM-L12-v2 is 384, not 768 as sometimes stated).
        """
        model_key = "paraphrase-multilingual-MiniLM-L12-v2"
        dim = self.ALTERNATIVE_MODELS[model_key]["dimension"]
        
        return self.get_or_create_collection(
            name="kb_sections_v2",
            metadata={
                "description": "Knowledge Base Sections Embeddings V2 (multilingual)",
                "embedding_model": model_key,
                "dimension": dim
            }
        )
    
    @property
    def entities_collection(self) -> chromadb.Collection:
        """Collection for knowledge graph entities."""
        return self.get_or_create_collection(
            name="kg_entities",
            metadata={
                "description": "Knowledge Graph Entities Embeddings",
                "embedding_model": self.model_name,
                "dimension": 384
            }
        )
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def get_collection_stats(self, collection_name: str) -> dict:
        """Retrieves statistics for a collection."""
        collection = self.client.get_collection(collection_name)
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    
    def delete_by_file_id(self, file_id: str, collection_name: str = "kb_sections") -> int:
        """
        Deletes all embeddings for a file_id from ChromaDB.
        
        ChromaDB does not support DELETE with WHERE, so:
        1. Query all IDs with matching file_id via metadata
        2. Delete via delete_by_ids()
        
        Args:
            file_id: UUID of the file
            collection_name: ChromaDB collection name
            
        Returns:
            Number of deleted entries
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Query all IDs with matching file_id in metadata
            results = collection.get(where={"file_id": file_id})
            
            if not results or not results.get('ids'):
                logger.debug(f"No ChromaDB entries found for file_id: {file_id}")
                return 0
            
            ids_to_delete = results['ids']
            collection.delete(ids=ids_to_delete)
            
            logger.info(f"Deleted {len(ids_to_delete)} entries from ChromaDB for file_id: {file_id}")
            return len(ids_to_delete)
            
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB for file_id {file_id}: {e}")
            return 0
    
    def list_collections(self) -> list[dict]:
        """Lists all collections with statistics."""
        collections = self.client.list_collections()
        return [
            {
                "name": c.name,
                "count": c.count(),
                "metadata": c.metadata
            }
            for c in collections
        ]
    
    def reset_all(self) -> None:
        """Reset all collections (dangerous!)."""
        self.client.reset()
        logger.warning("All ChromaDB collections reset!")
    
    # -------------------------------------------------------------------------
    # Singleton Access
    # -------------------------------------------------------------------------
    
    @classmethod
    def get_instance(cls, **kwargs) -> 'ChromaIntegration':
        """Singleton pattern for connection sharing."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for tests)."""
        cls._instance = None


# =============================================================================
# Convenience Functions (Module-Level API)
# =============================================================================

# Lazy-initialized global instance
_global_instance: Optional[ChromaIntegration] = None

def get_chroma(**kwargs) -> ChromaIntegration:
    """Gets or creates global ChromaIntegration instance."""
    global _global_instance
    if _global_instance is None:
        _global_instance = ChromaIntegration.get_instance(**kwargs)
    return _global_instance

def embed_text(text: str) -> list[float]:
    """Convenience: Single text embedding."""
    return get_chroma().embed_text(text)

def embed_batch(texts: list[str], **kwargs) -> list[list[float]]:
    """Convenience: Batch text embedding."""
    return get_chroma().embed_batch(texts, **kwargs)


# =============================================================================
# Main: Quick Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ChromaDB Integration - Quick Test")
    print("=" * 60)
    
    chroma = ChromaIntegration()
    
    # Test embedding
    test_texts = [
        "MTHFR Genmutation C677T Behandlung mit 5-MTHF",
        "BSV Blockchain Semantic Verification für KI-Agenten",
        "LDL Cholesterin Zielwert unter 100 mg/dL"
    ]
    
    print("\n[1] Testing Embedding...")
    embeddings = chroma.embed_batch(test_texts)
    print(f"   Generated {len(embeddings)} embeddings")
    print(f"   Dimension: {len(embeddings[0]) if embeddings else 0}")
    
    print("\n[2] Testing Collection Management...")
    collection = chroma.sections_collection
    print(f"   Collection: {collection.name}")
    print(f"   Count: {collection.count()}")
    
    print("\n[3] Listing Collections...")
    for col in chroma.list_collections():
        print(f"   - {col['name']}: {col['count']} items")
    
    print("\n[4] Testing Query (semantic search)...")
    test_query = "Genetische Behandlung Methylierung"
    query_emb = chroma.embed_text(test_query)
    
    # Add some test data first
    test_ids = ["test1", "test2", "test3"]
    test_metadatas = [
        {"source": "gesundheit", "type": "fact"},
        {"source": "projekte", "type": "fact"},
        {"source": "gesundheit", "type": "advice"}
    ]
    
    collection.upsert(
        ids=test_ids,
        embeddings=embeddings,
        metadatas=test_metadatas,
        documents=test_texts
    )
    print(f"   Upserted {len(test_ids)} test documents")
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=3
    )
    print(f"   Query: '{test_query}'")
    print(f"   Results: {len(results['ids'][0])} matches")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
