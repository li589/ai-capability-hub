"""
ChromaDB Plugin for BiblioIndexer
==================================

Plugin system for automatic ChromaDB integration after indexing.

Uses background queue for non-blocking embedding.

Usage:
    from kb.indexer import BiblioIndexer
    from kb.library.knowledge_base.chroma_plugin import ChromaDBPlugin
    
    with BiblioIndexer("knowledge.db", plugins=[ChromaDBPlugin()]) as indexer:
        indexer.index_file(Path("test.md"))
        # -> SQLite + ChromaDB (automatic via plugin)
"""

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Set

# Import shared utility for embedding text building
from kb.library.knowledge_base.utils import build_embedding_text
from queue import Queue, Empty
from dataclasses import dataclass, field
from datetime import datetime

# Import config - prefer modern singleton pattern
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from kb.base.config import KBConfig
_default_chroma_path = str(KBConfig.get_instance().chroma_path)

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingTask:
    """An embedding task to be processed."""
    section_id: str
    file_id: str
    file_path: str
    section_header: str
    content_full: str
    content_preview: str
    section_level: int
    keywords: List[str] = field(default_factory=list)


class ChromaDBPlugin:
    """
    ChromaDB embedding plugin for BiblioIndexer.
    
    Responsibility:
    - Queue manages freshly indexed sections for embedding
    - Background thread for non-blocking processing
    - Batch processing for efficiency
    
    Features:
    - Non-blocking: Indexing not blocked by embedding
    - Batch processing: Sections processed in batches
    - Toggle: can be enabled/disabled
    - Graceful: works even when ChromaDB is unavailable
    """
    
    def __init__(
        self,
        db_path: str = "library/biblio.db",
        chroma_path: str = None,
        batch_size: int = 32,
        enabled: bool = True,
        auto_flush: bool = True,
        collection_name: str = "kb_sections"
    ):
        """
        Initialize ChromaDB plugin.
        
        Args:
            db_path: Path to SQLite database
            chroma_path: Path for ChromaDB
            batch_size: Batch size for embedding
            enabled: Whether plugin is active
            auto_flush: Auto flush after index_directory
            collection_name: ChromaDB collection name
        """
        self.db_path = Path(db_path).expanduser()
        if chroma_path is None:
            self.chroma_path = Path(_default_chroma_path)
        else:
            self.chroma_path = Path(chroma_path).expanduser()
        self.batch_size = batch_size
        self.enabled = enabled
        self.auto_flush = auto_flush
        self.collection_name = collection_name
        
        # Queue for background embedding
        self._queue: List[EmbeddingTask] = []
        self._processed_files: Set[str] = set()  # file_ids already queued
        
        # Thread-safety
        self._lock = threading.Lock()
        
        # Background thread
        self._bg_thread: Optional[threading.Thread] = None
        self._bg_running = False
        
        # Lazy-loaded components
        self._chroma = None
        self._pipeline = None
        
        logger.info(f"ChromaDBPlugin init: enabled={enabled}, batch_size={batch_size}")
    
    @property
    def chroma(self):
        """Lazy-load ChromaDB integration."""
        if self._chroma is None:
            try:
                from kb.library.knowledge_base.chroma_integration import ChromaIntegration
                self._chroma = ChromaIntegration(chroma_path=str(self.chroma_path))
                logger.info("ChromaDB connection established")
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}")
                self._chroma = None
        return self._chroma
    
    @property
    def pipeline(self):
        """Lazy-load EmbeddingPipeline."""
        if self._pipeline is None:
            try:
                from kb.library.knowledge_base.embedding_pipeline import EmbeddingPipeline
                self._pipeline = EmbeddingPipeline(
                    db_path=str(self.db_path),
                    chroma_path=str(self.chroma_path),
                    batch_size=self.batch_size
                )
                logger.info("EmbeddingPipeline initialized")
            except Exception as e:
                logger.warning(f"EmbeddingPipeline not available: {e}")
                self._pipeline = None
        return self._pipeline
    
    def on_file_indexed(self, file_path: Path, sections: int, file_id: str) -> None:
        """
        Callback after successful indexing of a file.
        
        Queues all sections of the file for later embedding.
        
        Args:
            file_path: Path to indexed file
            sections: Number of indexed sections
            file_id: UUID of the file in database
        """
        if not self.enabled:
            return
        
        if file_id in self._processed_files:
            logger.debug(f"File {file_id} already queued, skipping")
            return
        
        try:
            # Hole alle section_ids für diese file_id
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                rows = conn.execute("""
                    SELECT 
                        id, file_id, file_path, section_header,
                        content_full, content_preview, section_level,
                        keywords
                    FROM file_sections
                    WHERE file_id = ?
                """, (file_id,)).fetchall()
            
            if not rows:
                logger.debug(f"No sections found for file_id {file_id}")
                return
            
            with self._lock:
                for row in rows:
                    # Parse keywords
                    keywords = []
                    if row['keywords']:
                        try:
                            keywords = json.loads(row['keywords'])
                        except Exception:
                            keywords = []
                    
                    task = EmbeddingTask(
                        section_id=row['id'],
                        file_id=row['file_id'],
                        file_path=row['file_path'],
                        section_header=row['section_header'] or "",
                        content_full=row['content_full'] or "",
                        content_preview=row['content_preview'] or "",
                        section_level=row['section_level'] or 0,
                        keywords=keywords
                    )
                    self._queue.append(task)
                
                self._processed_files.add(file_id)
            
            logger.info(f"Queued {len(rows)} sections for embedding: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error queuing sections for {file_path}: {e}")
    
    def on_file_removed(self, file_path: Path) -> None:
        """
        Callback after removing a file from index.
        
        Removes corresponding entries from ChromaDB.
        
        Args:
            file_path: Path of removed file
        """
        if not self.enabled:
            return
        
        try:
            # Hole alle file_ids für diesen Pfad
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT id FROM files WHERE file_path = ?", (str(file_path),)
                ).fetchall()
            
            if not rows:
                logger.debug(f"No file entries found for: {file_path}")
                return
            
            file_ids = [row['id'] for row in rows]
            
            # Lösche aus ChromaDB
            if self.chroma:
                for file_id in file_ids:
                    self.chroma.delete_by_file_id(file_id)
                logger.info(f"ChromaDB entries removed for: {file_path}")
            else:
                logger.warning("ChromaDB not available, orphan entries may remain")
                
        except Exception as e:
            logger.error(f"Error removing ChromaDB entries for {file_path}: {e}")
    
    def on_indexing_complete(self, stats: dict) -> None:
        """
        Optional callback after complete indexing.
        
        Args:
            stats: Statistics dict with 'files' and 'sections' counters
        """
        if not self.enabled:
            return
        
        if self.auto_flush and stats.get('sections', 0) > 0:
            logger.info(f"Indexing complete: {stats['sections']} sections queued")
            # Non-blocking background flush
            self.flush_async()
    
    def flush(self) -> int:
        """
        Processes the queue and writes to ChromaDB.
        
        Blocking method - should not be called in main thread with many items.
        
        Returns:
            Number of processed sections
        """
        if not self.enabled:
            return 0
        
        if not self.chroma or not self.pipeline:
            logger.warning("ChromaDB or Pipeline not available, skipping flush")
            return 0
        
        with self._lock:
            if not self._queue:
                logger.debug("Queue empty, nothing to flush")
                return 0
            
            # Copy queue and clear
            tasks = self._queue.copy()
            self._queue.clear()
        
        if not tasks:
            return 0
        
        logger.info(f"Flushing {len(tasks)} sections to ChromaDB...")
        
        # Process in batches
        processed = 0
        failed = 0
        
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i + self.batch_size]
            
            try:
                # Build texts for embedding
                texts = []
                for task in batch:
                    text = build_embedding_text(
                        task.section_header,
                        task.content_full,
                        task.keywords
                    )
                    texts.append(text)
                
                # Batch embedding
                embeddings = self.chroma.embed_batch(texts, batch_size=len(batch))
                
                # Prepare ChromaDB upsert
                collection = self.chroma.get_or_create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Knowledge Base Sections Embeddings",
                        "source": "chroma_plugin.py"
                    }
                )
                
                ids = []
                emb_list = []
                metadatas = []
                documents = []
                
                for idx, (task, embedding) in enumerate(zip(batch, embeddings)):
                    ids.append(task.section_id)
                    emb_list.append(embedding)
                    metadatas.append({
                        "file_id": task.file_id,
                        "file_path": task.file_path,
                        "section_header": task.section_header[:200] if task.section_header else "",
                        "section_level": task.section_level,
                        "keywords": json.dumps(task.keywords[:10]),
                        "processed_at": datetime.now().isoformat()
                    })
                    documents.append(texts[idx][:2000])
                
                # Upsert to ChromaDB
                collection.upsert(
                    ids=ids,
                    embeddings=emb_list,
                    metadatas=metadatas,
                    documents=documents
                )
                
                # Write tracking info to embeddings table
                if self.db_path and batch:
                    with sqlite3.connect(str(self.db_path)) as track_conn:
                        for task in batch:
                            # Get file_id from section_id
                            cur = track_conn.execute(
                                "SELECT file_id FROM file_sections WHERE id = ?", 
                                (task.section_id,)
                            )
                            row = cur.fetchone()
                            file_id = row[0] if row else None
                            
                            track_conn.execute("""
                                INSERT OR REPLACE INTO embeddings 
                                (section_id, file_id, model, dimension, created_at)
                                VALUES (?, ?, 'all-MiniLM-L6-v2', 384, CURRENT_TIMESTAMP)
                            """, (task.section_id, file_id))
                
                processed += len(batch)
                logger.info(f"Batch {i // self.batch_size + 1}: {len(batch)} sections embedded")
                
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                failed += len(batch)
        
        logger.info(f"Flush complete: {processed} processed, {failed} failed")
        return processed
    
    def flush_async(self) -> None:
        """
        Starts background thread for non-blocking flush.
        
        Non-blocking important so indexing is not blocked.
        """
        if self._bg_thread and self._bg_thread.is_alive():
            logger.debug("Background flush already running")
            return
        
        self._bg_running = True
        self._bg_thread = threading.Thread(
            target=self._bg_flush_worker,
            name="ChromaDB-Flush",
            daemon=True
        )
        self._bg_thread.start()
        logger.info("Background flush started")
    
    def _bg_flush_worker(self) -> None:
        """Background worker for flush."""
        try:
            self.flush()
        except Exception as e:
            logger.error(f"Background flush error: {e}")
        finally:
            self._bg_running = False
    
    # _build_embedding_text removed - using shared build_embedding_text from utils.py
    
    def get_queue_size(self) -> int:
        """Returns current queue size."""
        with self._lock:
            return len(self._queue)
    
    def clear_queue(self) -> int:
        """
        Clears the queue without processing.
        
        Returns:
            Number of discarded tasks
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._processed_files.clear()
        logger.info(f"Queue cleared: {count} tasks discarded")
        return count
    
    def stop(self) -> None:
        """Stops background thread."""
        self._bg_running = False
        if self._bg_thread:
            self._bg_thread.join(timeout=2.0)
        logger.info("ChromaDBPlugin stopped")
