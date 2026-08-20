"""
Embedding Pipeline for Knowledge Base
======================================

Phase 1: Vector Search Foundation
Batch processing for 996 files / 16,626 sections.

Processes file_sections from knowledge.db and generates
embeddings for ChromaDB vector index.

Source: KB_Erweiterungs_Plan.md (Phase 1)
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Generator, List
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import hashlib

from .chroma_integration import ChromaIntegration, get_chroma
from .utils import build_embedding_text

# Import config - prefer modern singleton pattern
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from kb.base.config import KBConfig
_default_chroma_path = str(KBConfig.get_instance().chroma_path)

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SectionRecord:
    """Structure for a section to be embedded."""
    id: str           # UUID from file_sections
    file_id: str      # Reference to parent file
    file_path: str    # Full file path
    section_header: str
    content_full: str
    content_preview: str
    section_level: int
    importance_score: float
    keywords: list[str]


@dataclass
class EmbeddingJob:
    """An embedding job with input and output."""
    section_id: str
    text: str
    embedding: Optional[list[float]] = None
    status: str = "pending"  # pending, completed, failed
    error: Optional[str] = None
    processed_at: Optional[str] = None


class EmbeddingPipeline:
    """
    Pipeline for batch embedding of knowledge base sections.

    Responsibility:
    - Reads sections from SQLite (knowledge.db)
    - Generates embeddings (batch processing)
    - Writes to ChromaDB
    - Tracking with cache for incremental updates
    """

    def __init__(
        self,
        db_path: str = "library/biblio.db",
        chroma_path: str = None,
        cache_path: str = "library/embeddings/cache.json",
        batch_size: int = 32,
        max_workers: int = 4
    ):
        """
        Initialize pipeline.

        Args:
            db_path: Path to knowledge.db
            chroma_path: Path for ChromaDB
            cache_path: Path for embedding cache (JSON)
            batch_size: Batch size for embedding
            max_workers: Thread pool workers for parallel processing
        """
        self.db_path = Path(db_path).expanduser()
        if chroma_path is None:
            self.chroma_path = Path(_default_chroma_path)
        else:
            self.chroma_path = Path(chroma_path).expanduser()
        self.cache_path = Path(cache_path).expanduser()
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        self.batch_size = batch_size
        self.max_workers = max_workers

        self.chroma = ChromaIntegration(chroma_path=str(self.chroma_path))
        self._cache: dict = {}  # section_id -> file_hash

        logger.info(f"EmbeddingPipeline init: db={self.db_path}")

    def get_embedding_hash(self, embedding) -> str:
        """Computes SHA256 hash of an embedding vector."""
        import hashlib
        import json
        vec_str = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
        return hashlib.sha256(vec_str.encode()).hexdigest()

    # -------------------------------------------------------------------------
    # Cache Management
    # -------------------------------------------------------------------------

    def _load_cache(self) -> None:
        """Loads embedding cache from JSON."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path) as f:
                    self._cache = json.load(f)
                logger.info(f"Cache loaded: {len(self._cache)} entries")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
                self._cache = {}

    def _save_cache(self) -> None:
        """Saves embedding cache as JSON."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump(self._cache, f, indent=2)
            logger.info(f"Cache saved: {len(self._cache)} entries")
        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def _needs_update(self, section_id: str, file_hash: str) -> bool:
        """Checks if section needs re-embedding."""
        return self._cache.get(section_id) != file_hash

    # -------------------------------------------------------------------------
    # Database Reading
    # -------------------------------------------------------------------------

    def _get_connection(self) -> sqlite3.Connection:
        """Gets SQLite connection."""
        return sqlite3.connect(str(self.db_path))

    def get_sections_for_embedding(
        self,
        limit: Optional[int] = None,
        force_reload: bool = False
    ) -> Generator[SectionRecord, None, None]:
        """
        Yields sections that need embedding.

        Args:
            limit: Optional limit for testing
            force_reload: If True, ignores cache

        Yields:
            SectionRecord for each section to process
        """
        self._load_cache()

        conn = self._get_connection()
        query = """
            SELECT
                id, file_id, file_path, section_header,
                content_full, content_preview, section_level,
                importance_score, keywords, file_hash
            FROM file_sections
            WHERE content_full IS NOT NULL
              AND content_full != ''
              AND length(content_full) > 10
            ORDER BY importance_score DESC, last_indexed ASC
        """

        if limit:
            query += f" LIMIT ?"  # Parameterized query
            cursor = conn.execute(query, (limit,))
        else:
            cursor = conn.execute(query)

        for row in cursor.fetchall():
            (section_id, file_id, file_path, section_header,
             content_full, content_preview, section_level,
             importance_score, keywords_str, file_hash) = row

            # Parse keywords
            try:
                keywords = json.loads(keywords_str) if keywords_str else []
            except Exception:
                keywords = []

            # Check cache
            if not force_reload and not self._needs_update(section_id, file_hash):
                continue

            # Build text for embedding
            text = build_embedding_text(
                section_header, content_full, keywords
            )

            yield SectionRecord(
                id=section_id,
                file_id=file_id,
                file_path=file_path,
                section_header=section_header or "",
                content_full=content_full or "",
                content_preview=content_preview or "",
                section_level=section_level or 0,
                importance_score=importance_score or 0.5,
                keywords=keywords
            )

        conn.close()

    def count_pending_sections(self, force_reload: bool = False) -> int:
        """Counts sections that need embedding."""
        count = 0
        for _ in self.get_sections_for_embedding(force_reload=force_reload):
            count += 1
        return count

    # -------------------------------------------------------------------------
    # Embedding Processing
    # -------------------------------------------------------------------------

    def process_batch(self, sections: list[SectionRecord]) -> list[EmbeddingJob]:
        """
        Processes a batch of sections.

        Args:
            sections: List of SectionRecords

        Returns:
            List of EmbeddingJobs with results
        """
        jobs = []

        # Texte sammeln
        texts = [build_embedding_text(
            s.section_header, s.content_full, s.keywords
        ) for s in sections]

        try:
            # Batch-Embedding
            embeddings = self.chroma.embed_batch(texts, batch_size=self.batch_size)

            for section, embedding in zip(sections, embeddings):
                job = EmbeddingJob(
                    section_id=section.id,
                    text=texts[sections.index(section)],
                    embedding=embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                    status="completed",
                    processed_at=datetime.now().isoformat()
                )
                jobs.append(job)

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            for section in sections:
                jobs.append(EmbeddingJob(
                    section_id=section.id,
                    text=build_embedding_text(
                        section.section_header, section.content_full, section.keywords
                    ),
                    status="failed",
                    error=str(e)
                ))

        return jobs

    # -------------------------------------------------------------------------
    # ChromaDB Writing
    # -------------------------------------------------------------------------

    def upsert_to_chroma(
        self,
        jobs: list[EmbeddingJob],
        sections: list[SectionRecord],
        collection_name: str = "kb_sections"
    ) -> int:
        """
        Writes embedding results to ChromaDB.

        Args:
            jobs: EmbeddingJobs with results
            sections: Original SectionRecords
            collection_name: Target collection

        Returns:
            Number of successfully written items
        """
        collection = self.chroma.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Knowledge Base Sections Embeddings",
                "source": "embedding_pipeline.py"
            }
        )

        successful = 0
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for job, section in zip(jobs, sections):
            if job.status != "completed" or job.embedding is None:
                continue

            ids.append(job.section_id)
            embeddings.append(job.embedding)
            metadatas.append({
                "file_id": section.file_id,
                "file_path": section.file_path,
                "section_header": section.section_header[:200] if section.section_header else "",
                "section_level": section.section_level,
                "importance_score": section.importance_score,
                "keywords": json.dumps(section.keywords[:10]),
                "processed_at": job.processed_at
            })
            documents.append(job.text[:2000])  # ChromaDB hat 2000 char limit

            successful += 1

        if successful > 0:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )

            # Track embeddings in SQLite
            if self.db_path:
                with sqlite3.connect(str(self.db_path)) as track_conn:
                    for section_id in ids:
                        # Get file_id
                        cur = track_conn.execute(
                            "SELECT file_id FROM file_sections WHERE id = ?",
                            (section_id,)
                        )
                        row = cur.fetchone()
                        file_id = row[0] if row else None

                        track_conn.execute("""
                            INSERT OR REPLACE INTO embeddings
                            (section_id, file_id, model, dimension, created_at)
                            VALUES (?, ?, 'all-MiniLM-L6-v2', 384, CURRENT_TIMESTAMP)
                        """, (section_id, file_id))

            logger.info(f"Upserted {successful} sections to ChromaDB")

        return successful

    # -------------------------------------------------------------------------
    # Main Pipeline Run
    # -------------------------------------------------------------------------

    def run_full(
        self,
        limit: Optional[int] = None,
        force_reload: bool = False,
        collection_name: str = "kb_sections"
    ) -> dict:
        """
        Runs full embedding pipeline.

        Args:
            limit: Optional limit for testing
            force_reload: If True, re-embed despite cache
            collection_name: Collection for output

        Returns:
            Statistics dict with results
        """
        self._load_cache()

        logger.info("=" * 60)
        logger.info("Starting Embedding Pipeline")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Sections sammeln
        logger.info("Collecting sections...")
        sections = list(self.get_sections_for_embedding(
            limit=limit,
            force_reload=force_reload
        ))
        total_sections = len(sections)

        if total_sections == 0:
            logger.info("No sections need embedding (all up to date)")
            return {"status": "up_to_date", "processed": 0}

        logger.info(f"Found {total_sections} sections to embed")

        # Batch-Verarbeitung
        processed = 0
        failed = 0
        batches = [
            sections[i:i + self.batch_size]
            for i in range(0, total_sections, self.batch_size)
        ]

        logger.info(f"Processing {len(batches)} batches...")

        for batch_idx, batch in enumerate(batches):
            logger.info(f"Batch {batch_idx + 1}/{len(batches)}")

            jobs = self.process_batch(batch)

            # Update cache
            for job in jobs:
                if job.status == "completed":
                    section = batch[jobs.index(job)]
                    self._cache[job.section_id] = section.content_full[:100]  # pseudo-hash
                elif job.status == "failed":
                    failed += 1

            # Upsert to ChromaDB
            success = self.upsert_to_chroma(jobs, batch, collection_name)
            processed += success

            # Save cache periodically
            if (batch_idx + 1) % 10 == 0:
                self._save_cache()

        # Final cache save
        self._save_cache()

        elapsed = (datetime.now() - start_time).total_seconds()

        stats = {
            "status": "completed",
            "total_sections": total_sections,
            "processed": processed,
            "failed": failed,
            "batches": len(batches),
            "elapsed_seconds": elapsed,
            "sections_per_second": processed / elapsed if elapsed > 0 else 0
        }

        logger.info("=" * 60)
        logger.info("Pipeline Complete!")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)

        return stats

    def run_incremental(
        self,
        collection_name: str = "kb_sections"
    ) -> dict:
        """Incremental update (only new/changed sections)."""
        return self.run_full(force_reload=False, collection_name=collection_name)

    def run_full_reload(
        self,
        collection_name: str = "kb_sections"
    ) -> dict:
        """Full reload of all sections."""
        logger.warning("Full reload: clearing cache and re-embedding ALL sections")
        self._cache = {}
        return self.run_full(force_reload=True, collection_name=collection_name)


# =============================================================================
# Main: Pipeline Execution
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Pipeline for KB")
    parser.add_argument("--limit", type=int, default=None, help="Limit for testing")
    parser.add_argument("--reload", action="store_true", help="Full reload")
    parser.add_argument("--stats", action="store_true", help="Statistics only")
    parser.add_argument("--db-path", type=str, default="library/biblio.db")
    parser.add_argument("--chroma-path", type=str, default=None)

    args = parser.parse_args()

    pipeline = EmbeddingPipeline(
        db_path=args.db_path,
        chroma_path=args.chroma_path
    )

    if args.stats:
        print("=" * 60)
        print("Embedding Pipeline Statistics")
        print("=" * 60)

        pending = pipeline.count_pending_sections()
        total = pipeline.count_pending_sections(force_reload=True)

        chroma = get_chroma(chroma_path=args.chroma_path)
        coll_stats = chroma.get_collection_stats("kb_sections")

        print(f"Total Sections in DB: {total}")
        print(f"Sections needing update: {pending}")
        print(f"Already indexed in ChromaDB: {coll_stats['count']}")
        print(f"Cache entries: {len(pipeline._cache)}")

    elif args.reload:
        print("Starting FULL RELOAD...")
        result = pipeline.run_full_reload()
        print(json.dumps(result, indent=2))

    else:
        print("Starting INCREMENTAL update...")
        result = pipeline.run_incremental()
        print(json.dumps(result, indent=2))
