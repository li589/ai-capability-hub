"""
Hybrid Search for Knowledge Base
=================================

Phase 1: Vector Search Foundation
Combines SQLite (Keywords) + ChromaDB (Vector) search.

Unified Query Interface for:
- Semantic similarity search (ChromaDB)
- Keyword/LIKE search (SQLite)
- Importance score ranking

Source: KB_Erweiterungs_Plan.md (Phase 1)
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Union
from dataclasses import dataclass

from .chroma_integration import ChromaIntegration, get_chroma
from .fts5_setup import check_fts5_available
from .synonyms import SynonymExpander, get_expander
from .reranker import Reranker, get_reranker

# Provide default if config not available
try:
    from kb.base.config import KBConfig
    _default_chroma_path = str(KBConfig.get_instance().chroma_path)
except ImportError:
    _default_chroma_path = str(Path.home() / ".openclaw" / "kb" / "chroma_db")

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result with combined scoring."""
    section_id: str
    file_id: str
    file_path: str
    section_header: str
    content_preview: str
    content_full: str
    section_level: int
    importance_score: float
    keywords: list[str]
    
    # Combined scores
    semantic_score: float = 0.0   # ChromaDB similarity
    keyword_score: float = 0.0    # SQLite keyword match
    combined_score: float = 0.0    # Weighted combination
    
    # Source info
    source: str = ""  # "chroma", "sqlite", "hybrid"


@dataclass
class SearchConfig:
    """Configuration for hybrid search."""
    # Weights for score combination
    semantic_weight: float = 0.60   # 60% semantic
    keyword_weight: float = 0.40     # 40% keyword
    
    # ChromaDB settings - more results for better results
    semantic_limit: int = 100        # Top N from semantic search
    keyword_limit: int = 100       # Top N from keyword search
    
    # Final results
    final_limit: int = 20
    
    # Minimum scores - lower for more results
    min_combined_score: float = 0.05
    
    # Boost factors
    importance_boost: bool = True    # Boost by importance_score
    recency_boost: bool = False       # Boost recent content
    keyword_exact_boost: float = 1.5 # Boost exact keyword matches
    
    # Score normalization
    normalize_scores: bool = True    # Normalize scores to 0-1 range


class HybridSearch:
    """
    Hybrid Search Interface: SQLite + ChromaDB.
    
    Combines:
    - Semantic search via ChromaDB (embeddings)
    - Keyword search via SQLite (full-text LIKE)
    - Ranking via combined weighted scores
    
    Phase 3.1: Wing/Room/Hall Filter implemented
    Phase 3.2: Query Caching
    """
    
    # -------------------------------------------------------------------------
    # Keyword Parsing (handles both JSON arrays and comma-separated strings)
    # -------------------------------------------------------------------------

    def _parse_keywords(self, keywords_str):
        """
        Parse keywords from DB - handles both JSON arrays and comma-separated strings.
        
        Problem: 2.353 rows have comma-separated strings like
        'Lazarus_Physik, Simulation, Matrix, 666, 888...' instead of JSON arrays.
        """
        if not keywords_str or keywords_str.strip() in ('', 'null', '[]'):
            return []
        
        # Try JSON first
        try:
            return json.loads(keywords_str)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback: comma-separated
        return [k.strip() for k in keywords_str.split(',') if k.strip()]

    def __init__(
        self,
        db_path: str = "library/biblio.db",
        chroma_path: str = None,
        config: Optional[SearchConfig] = None
    ):
        """
        Initialize Hybrid Search.
        
        Args:
            db_path: Path to knowledge.db
            chroma_path: Path for ChromaDB
            config: SearchConfig (or default)
        """
        self.db_path = Path(db_path).expanduser()
        if chroma_path is None:
            try:
                self.chroma_path = Path(CHROMA_PATH)
            except NameError:
                self.chroma_path = Path(_default_chroma_path)
        else:
            self.chroma_path = Path(chroma_path)
        self.config = config or SearchConfig()
        
        self.chroma = ChromaIntegration(chroma_path=str(self.chroma_path))
        self._db_conn: Optional[sqlite3.Connection] = None
        self._fts5_available: bool = False
        
        # Phase 3.2: Query Cache (LRU)
        self._query_cache: dict = {}
        self._cache_max_size: int = 100
        
        # Phase 2: Synonym Expander
        self._expander: Optional[SynonymExpander] = None
        self._synonym_expansion_enabled: bool = True
        
        # Phase 6: Re-Ranker
        self._reranker: Optional[Reranker] = None
        self._reranking_enabled: bool = False  # Off by default (adds latency)
        
        logger.info(f"HybridSearch init: db={self.db_path}")
    
    # -------------------------------------------------------------------------
    # Database Connection
    # -------------------------------------------------------------------------
    
    @property
    def db_conn(self) -> sqlite3.Connection:
        """Lazy SQLite connection."""
        if self._db_conn is None:
            self._db_conn = sqlite3.connect(str(self.db_path))
            self._db_conn.row_factory = sqlite3.Row
        return self._db_conn
    
    def close(self):
        """Close database connection."""
        if self._db_conn:
            self._db_conn.close()
            self._db_conn = None
    
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Phase 2: Synonym Expansion
    # -------------------------------------------------------------------------
    
    @property
    def expander(self) -> SynonymExpander:
        """Lazy-load SynonymExpander."""
        if self._expander is None:
            self._expander = get_expander()
        return self._expander
    
    def enable_synonym_expansion(self, enabled: bool) -> None:
        """Enable or disable synonym expansion."""
        self._synonym_expansion_enabled = enabled
    
    def expand_query(self, query: str) -> str:
        """
        Expand query with synonyms for better recall.
        
        Phase 2: Synonym expansion before search.
        
        Args:
            query: Original query string
            
        Returns:
            Expanded query string with synonyms
        """
        if not self._synonym_expansion_enabled:
            return query
        return self.expander.expand_query(query)

    # -------------------------------------------------------------------------
    # Phase 6: Re-Ranking
    # -------------------------------------------------------------------------
    
    @property
    def reranker(self) -> Reranker:
        """Lazy-load Reranker."""
        if self._reranker is None:
            self._reranker = get_reranker()
        return self._reranker
    
    def enable_reranking(self, enabled: bool) -> None:
        """Enable or disable re-ranking (adds latency but improves quality)."""
        self._reranking_enabled = enabled
        logger.info(f"Re-ranking {'enabled' if enabled else 'disabled'}")
    
    def rerank_results(self, query: str, results: list) -> list:
        """
        Re-rank results using Cross-Encoder.
        
        Phase 6: Cross-Encoder re-ranking after hybrid search.
        
        Args:
            query: Original search query
            results: Initial search results
            
        Returns:
            Re-ranked results (adds rerank_score to each result)
        """
        if not self._reranking_enabled or not results:
            return results
        
        # Convert SearchResult to dict for reranker
        result_dicts = []
        for r in results:
            result_dicts.append({
                'section_id': r.section_id,
                'file_id': r.file_id,
                'file_path': r.file_path,
                'section_header': r.section_header,
                'content_preview': r.content_preview,
                'content_full': r.content_full,
                'section_level': r.section_level,
                'importance_score': r.importance_score,
                'keywords': r.keywords,
                'semantic_score': r.semantic_score,
                'keyword_score': r.keyword_score,
                'combined_score': r.combined_score,
                'source': r.source,
            })
        
        # Re-rank
        reranked_dicts = self.reranker.rerank(query, result_dicts)
        
        # Convert back to SearchResult
        reranked_results = []
        for rd in reranked_dicts:
            reranked_results.append(SearchResult(**rd))
        
        return reranked_results


    def _semantic_search(
        self, 
        query: str, 
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Semantic search via ChromaDB.
        
        Args:
            query: Natural language query
            limit: Max results
            
        Returns:
            List of results with scores
        """
        limit = limit or self.config.semantic_limit
        
        collection = self.chroma.sections_collection
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                include=["metadatas", "distances"]
            )
        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}")
            return []
        
        search_results = []
        
        if not results or not results['ids']:
            return []
        
        for i, section_id in enumerate(results['ids'][0]):
            # Distance to similarity (ChromaDB: cosine distance, 0 = perfect)
            distance = results['distances'][0][i] if results['distances'] else 0.0
            semantic_score = max(0.0, 1.0 - distance)  # Convert to similarity
            
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            
            search_results.append({
                "section_id": section_id,
                "semantic_score": semantic_score,
                "file_id": metadata.get("file_id", ""),
                "file_path": metadata.get("file_path", ""),
                "section_header": metadata.get("section_header", ""),
                "importance_score": metadata.get("importance_score", 0.5),
                "keywords": self._parse_keywords(metadata.get("keywords", "[]"))
            })
        
        return search_results
    
    # -------------------------------------------------------------------------
    # Keyword Search (FTS5 with BM25)
    # -------------------------------------------------------------------------
    
    def _keyword_search_fts(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Keyword search via SQLite FTS5 with BM25 ranking.
        
        Uses BM25 (Best Match 25) algorithm for relevance ranking instead of LIKE.
        Falls back to LIKE search if FTS5 is not available.
        
        Args:
            query: Query string
            limit: Max results
            
        Returns:
            List of results with BM25 keyword match scores
        """
        limit = limit or self.config.keyword_limit
        
        # Check FTS5 availability (cache the result)
        if not hasattr(self, '_fts5_checked'):
            self._fts5_available = check_fts5_available(self.db_conn)
            self._fts5_checked = True
            logger.info(f"FTS5 availability: {self._fts5_available}")
        
        if not self._fts5_available:
            # Fallback to LIKE search
            return self._keyword_search(query, limit)
        
        # Check if FTS5 table exists
        try:
            cursor = self.db_conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name='file_sections_fts' AND type='table'"
            )
            if not cursor.fetchone()[0]:
                logger.warning("FTS5 table not found, falling back to LIKE")
                return self._keyword_search(query, limit)
        except Exception as e:
            logger.warning(f"FTS5 table check failed: {e}, falling back to LIKE")
            return self._keyword_search(query, limit)
        
        # Build FTS5 query - convert simple terms to FTS5 query syntax
        # FTS5 supports AND, OR, NOT operators and prefix matching with *
        terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
        
        if not terms:
            return []
        
        # Build FTS5 query string
        # Use quoted phrases for multi-word terms, simple terms for single words
        fts5_query_parts = []
        for term in terms:
            if ' ' in term:
                fts5_query_parts.append(f'"{term}"')
            else:
                fts5_query_parts.append(term)
        
        fts5_query = ' AND '.join(fts5_query_parts)
        
        try:
            # Execute BM25 query
            # BM25 returns negative values (closer to 0 = better match)
            # We convert to a positive score: higher = better
            sql = """
                SELECT 
                    section_id,
                    file_id,
                    file_path,
                    section_header,
                    content_preview,
                    content_full,
                    importance_score,
                    keywords,
                    bm25(file_sections_fts) as bm25_rank
                FROM file_sections_fts
                WHERE file_sections_fts MATCH ?
                ORDER BY bm25_rank
                LIMIT ?
            """
            cursor = self.db_conn.execute(sql, (fts5_query, limit))
            
            results = []
            row_num = 0
            total_rows = cursor.fetchall()  # Get all rows first
            total = len(total_rows)
            
            for row in total_rows:
                row_num += 1
                section_id, file_id, file_path, section_header, \
                content_preview, content_full, importance_score, \
                keywords_str, bm25_rank = row
                
                # BM25 rank is negative (closer to 0 = better match)
                # Convert to positive score where higher = better
                # 
                # Since BM25 values can be negative or near-zero with low document frequency,
                # we use a combined approach:
                # 1. Position-based score (results are ordered by BM25)
                # 2. BM25 magnitude boost (if significantly negative = better match)
                
                # Position score: 1.0 for first, decreasing for later results
                position_score = (total - row_num) / total if total > 0 else 0.5
                
                if bm25_rank is not None and bm25_rank < -0.001:
                    # Significant negative BM25 = good match
                    # The more negative, the better the match
                    # Scale: -0.001 to -10 maps to 0.5 to 1.0
                    bm25_boost = min(1.0, max(0.0, 0.5 + abs(bm25_rank) / 20.0))
                    # Blend: 70% position, 30% BM25 boost
                    bm25_score = 0.7 * position_score + 0.3 * bm25_boost
                else:
                    # Near-zero or positive BM25 - rely on position scoring
                    bm25_score = position_score
                
                results.append({
                    "section_id": str(section_id),
                    "keyword_score": bm25_score,
                    "file_id": str(file_id) if file_id else "",
                    "file_path": file_path or "",
                    "section_header": section_header or "",
                    "content_preview": content_preview or "",
                    "content_full": content_full or "",
                    "section_level": 0,
                    "importance_score": importance_score or 0.5,
                    "keywords": self._parse_keywords(keywords_str)
                })
            
            logger.info(f"FTS5 BM25 search for '{query}': {len(results)} results")
            return results
            
        except Exception as e:
            logger.warning(f"FTS5 BM25 query failed: {e}, falling back to LIKE")
            return self._keyword_search(query, limit)
    
    # -------------------------------------------------------------------------
    # Keyword Search (SQLite)
    # -------------------------------------------------------------------------
    
    def _keyword_search(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Keyword search via SQLite LIKE.
        
        Args:
            query: Query string
            limit: Max results
            
        Returns:
            List of results with keyword match scores
        """
        limit = limit or self.config.keyword_limit
        
        # Build query terms (simple tokenization)
        terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
        
        if not terms:
            return []
        
        # Build LIKE clauses
        like_clauses = []
        params = []
        
        for term in terms:
            like_clauses.append("(section_content LIKE ? OR section_header LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        
        sql = f"""
            SELECT 
                id, file_id, section_header, section_content, section_level
            FROM file_sections
            WHERE {' AND '.join(like_clauses)}
            ORDER BY COALESCE(section_level, 0) DESC, id
            LIMIT ?
        """
        params.append(limit)
        
        cursor = self.db_conn.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            section_id, file_id, section_header, section_content, section_level = row
            
            # Calculate keyword score
            all_text = f"{section_header} {section_content}".lower()
            matches = sum(1 for term in terms if term in all_text)
            keyword_score = matches / len(terms)  # 0.0 to 1.0
            
            # Exact match bonus
            exact_matches = sum(1 for term in terms if term in all_text.split())
            if exact_matches == len(terms):
                keyword_score *= self.config.keyword_exact_boost
            
            # Get file_path from files table
            file_path = ""
            try:
                cursor2 = self.db_conn.execute(
                    "SELECT file_path FROM files WHERE id = ?", (file_id,)
                )
                row2 = cursor2.fetchone()
                if row2:
                    file_path = row2[0]
            except:
                pass
            
            results.append({
                "section_id": str(section_id),
                "keyword_score": min(keyword_score, 1.0),
                "file_id": str(file_id) if file_id else "",
                "file_path": file_path or "",
                "section_header": section_header or "",
                "content_preview": section_content[:500] if section_content else "",
                "content_full": section_content or "",
                "section_level": section_level or 0,
                "importance_score": 0.5,  # Default for file_sections without importance_score
                "keywords": []
            })
        
        return results
    
    # -------------------------------------------------------------------------
    # Result Merging & Ranking
    # -------------------------------------------------------------------------
    
    def _merge_and_rank(
        self,
        semantic_results: list[dict],
        keyword_results: list[dict]
    ) -> list[SearchResult]:
        """
        Merges results from both searches and ranks.
        
        Scoring:
        - Semantic: from ChromaDB similarity
        - Keyword: from SQLite LIKE match
        - Combined: weighted average + boosts
        """
        
        # Build unified result set (deduplicate by section_id)
        result_map: dict[str, dict] = {}
        
        for r in semantic_results:
            result_map[r['section_id']] = {
                'section_id': r['section_id'],
                'file_id': r.get('file_id', ''),
                'file_path': r.get('file_path', ''),
                'section_header': r.get('section_header', ''),
                'content_preview': '',
                'content_full': '',
                'section_level': 0,
                'importance_score': r.get('importance_score', 0.5),
                'keywords': r.get('keywords', []),
                'semantic_score': r.get('semantic_score', 0.0),
                'keyword_score': 0.0,
                'source': 'chroma'
            }
        
        for r in keyword_results:
            sid = r['section_id']
            if sid in result_map:
                result_map[sid]['keyword_score'] = r.get('keyword_score', 0.0)
                result_map[sid]['content_preview'] = r.get('content_preview', '')
                result_map[sid]['content_full'] = r.get('content_full', '')
                result_map[sid]['section_level'] = r.get('section_level', 0)
                result_map[sid]['source'] = 'hybrid'
            else:
                r['semantic_score'] = 0.0
                r['source'] = 'sqlite'
                result_map[sid] = r
        
        # Calculate combined scores with optional normalization
        results = []
        max_semantic = max((r['semantic_score'] for r in result_map.values()), default=1.0)
        max_keyword = max((r['keyword_score'] for r in result_map.values()), default=1.0)
        
        for sid, data in result_map.items():
            semantic = data['semantic_score']
            keyword = data['keyword_score']
            
            # Normalize scores if enabled
            if self.config.normalize_scores:
                semantic = semantic / max_semantic if max_semantic > 0 else 0
                keyword = keyword / max_keyword if max_keyword > 0 else 0
            
            # Weighted combination
            combined = (
                semantic * self.config.semantic_weight +
                keyword * self.config.keyword_weight
            )
            
            # Apply importance boost
            if self.config.importance_boost:
                combined *= (0.5 + data['importance_score'])
            
            # Apply recency boost (future enhancement)
            # ...
            
            data['combined_score'] = combined
            results.append(SearchResult(**data))
        
        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Limit final results
        return results[:self.config.final_limit]
    
    # -------------------------------------------------------------------------
    # Main Search Interface (with Cache - Phase 3.2)
    # -------------------------------------------------------------------------
    
    def _get_cached(self, cache_key: str):
        """Retrieve result from cache."""
        return self._query_cache.get(cache_key)
    
    def _set_cached(self, cache_key: str, result: list) -> None:
        """Store result in cache (LRU)."""
        if len(self._query_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest = next(iter(self._query_cache))
            del self._query_cache[oldest]
        self._query_cache[cache_key] = result
    
    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        semantic_only: bool = False,
        keyword_only: bool = False
    ) -> list[SearchResult]:
        """
        Main search interface.
        
        Args:
            query: Natural language or keyword query
            limit: Override default result limit (default: 20)
            semantic_only: Only semantic search (skip SQLite)
            keyword_only: Only keyword search (skip ChromaDB)
            
        Returns:
            List of SearchResult ranked by combined score
        """
        if not query or not query.strip():
            return []
        
        query = query.strip()
        limit = limit or self.config.final_limit
        
        # Phase 2: Synonym expansion for better recall
        expanded_query = self.expand_query(query)
        
        # Phase 3.2: Cache check
        cache_key = f"{expanded_query}:{limit}:{semantic_only}:{keyword_only}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.info(f"Cache HIT for query: '{query}'")
            return cached
        
        logger.info(f"HybridSearch query: '{query}' → expanded:'{expanded_query}' (semantic_only={semantic_only}, keyword_only={keyword_only})")
        
        # Execute searches
        semantic_results = []
        keyword_results = []
        
        if not keyword_only:
            semantic_results = self._semantic_search(query)
        
        if not semantic_only:
            # Use FTS5 BM25 search if available, fallback to LIKE
            keyword_results = self._keyword_search_fts(query)
        
        # Merge and rank
        results = self._merge_and_rank(semantic_results, keyword_results)
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        # Filter by minimum score
        results = [
            r for r in results 
            if r.combined_score >= self.config.min_combined_score
        ]
        
        logger.info(f"  -> {len(results)} results")
        
        # Phase 6: Re-ranking (optional, adds latency)
        results = self.rerank_results(query, results)
        
        # Cache result
        self._set_cached(cache_key, results)
        
        return results
    
    def search_with_filters(
        self,
        query: str,
        limit: Optional[int] = None,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        hall: Optional[str] = None,
        file_types: Optional[list[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> list[SearchResult]:
        """
        Hybrid Search with Wing/Room/Hall metadata filter.
        
        Phase 3.1: Full implementation
        
        Wing/Room/Hall are virtual categories:
        - wing: Main area (e.g., 'health', 'agent', 'project')
        - room: Sub-area (e.g., 'documentation', 'workflow')
        - hall: Specific topic (e.g., 'kb-optimization', 'treechat')
        
        Filters are interpreted as keywords or content markers.
        
        Args:
            query: Natural language or keyword query
            limit: Override default result limit
            wing: Filter by wing (category area)
            room: Filter by room (subcategory)
            hall: Filter by hall (specific topic)
            file_types: Filter by file extensions (e.g., ['md', 'pdf'])
            date_from: Filter by last_modified >= date (ISO format)
            date_to: Filter by last_modified <= date (ISO format)
            
        Returns:
            List of SearchResult ranked by combined score
        """
        if not query or not query.strip():
            return []
        
        query = query.strip()
        limit = limit or self.config.final_limit
        
        # Build filter keywords from wing/room/hall
        filter_keywords = []
        if wing:
            filter_keywords.append(f"wing:{wing}")
        if room:
            filter_keywords.append(f"room:{room}")
        if hall:
            filter_keywords.append(f"hall:{hall}")
        
        # Enhance query with filter keywords
        enhanced_query = query
        if filter_keywords:
            enhanced_query = f"{query} {' '.join(filter_keywords)}"
        
        # Get more results initially to account for filtering
        results = self.search(enhanced_query, limit=limit * 3)
        
        # Apply post-filters
        filtered = []
        for r in results:
            # File type filter
            if file_types:
                file_ext = Path(r.file_path).suffix.lstrip('.').lower()
                if not any(ft.lower() == file_ext for ft in file_types):
                    continue
            
            # Date filter
            if date_from or date_to:
                # Get file last_modified from DB
                try:
                    cursor = self.db_conn.execute(
                        "SELECT last_modified FROM files WHERE id = ?",
                        (r.file_id,)
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        file_date_str = row[0]
                        # Parse date (handle various formats)
                        from datetime import datetime
                        try:
                            # Try ISO format first
                            file_date = datetime.fromisoformat(file_date_str.replace('Z', '+00:00'))
                        except ValueError:
                            try:
                                # Try simple date format
                                file_date = datetime.strptime(file_date_str, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                continue  # Skip if can't parse date
                        
                        if date_from:
                            from_dt = datetime.fromisoformat(date_from)
                            if file_date < from_dt:
                                continue
                        if date_to:
                            to_dt = datetime.fromisoformat(date_to)
                            if file_date > to_dt:
                                continue
                        
                except Exception:
                    pass  # Skip date filter if error
            
            filtered.append(r)
            if len(filtered) >= limit:
                break
        
        logger.info(f"search_with_filters: {len(results)} -> {len(filtered)} after filtering")
        return filtered
    
    def search_semantic(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> list[SearchResult]:
        """
        Semantic-only search using ChromaDB embeddings.
        
        Best for: Natural language queries, conceptual matches.
        
        Args:
            query: Natural language query
            limit: Max results (default: 20)
            
        Returns:
            List of SearchResult with semantic_score populated
        """
        return self.search(query, limit=limit, semantic_only=True)
    
    def search_keyword(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> list[SearchResult]:
        """
        Keyword-only search using SQLite LIKE.
        
        Best for: Exact term matches, known identifiers.
        
        Args:
            query: Keyword query string
            limit: Max results (default: 20)
            
        Returns:
            List of SearchResult with keyword_score populated
        """
        return self.search(query, limit=limit, keyword_only=True)
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> dict:
        """Returns search system statistics."""
        chroma = self.chroma
        
        # ChromaDB stats
        try:
            chroma_stats = chroma.get_collection_stats("kb_sections")
        except Exception:
            chroma_stats = {"count": 0, "name": "kb_sections"}
        
        # SQLite stats
        db_conn = self.db_conn
        cursor = db_conn.execute("SELECT COUNT(*) FROM file_sections")
        total_sections = cursor.fetchone()[0]
        
        cursor = db_conn.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]
        
        return {
            "chroma_sections": chroma_stats.get("count", 0),
            "sqlite_sections": total_sections,
            "sqlite_files": total_files,
            "config": {
                "semantic_weight": self.config.semantic_weight,
                "keyword_weight": self.config.keyword_weight
            }
        }
    
    def suggest_refinements(self, query: str) -> list[str]:
        """
        Suggests query refinements based on keyword analysis.
        
        Future enhancement for query expansion.
        """
        # Simple implementation: extract keywords from top SQLite results
        keyword_results = self._keyword_search(query, limit=5)
        
        suggestions = []
        for r in keyword_results[:3]:
            suggestions.extend(r.get('keywords', [])[:3])
        
        # Deduplicate and return top suggestions
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen and s not in query.lower():
                seen.add(s)
                unique.append(s)
        
        return unique[:5]


# =============================================================================
# Convenience Functions
# =============================================================================

# Lazy global instance
_global_search: Optional[HybridSearch] = None

def get_search(**kwargs) -> HybridSearch:
    """Get or create global HybridSearch instance."""
    global _global_search
    if _global_search is None:
        _global_search = HybridSearch(**kwargs)
    return _global_search

def search(query: str, **kwargs) -> list[SearchResult]:
    """Quick search convenience function."""
    return get_search().search(query, **kwargs)


# =============================================================================
# Main: Quick Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Hybrid Search - Quick Test")
    print("=" * 60)
    
    searcher = HybridSearch()
    
    print("\n[1] System Stats:")
    stats = searcher.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n[2] Testing Keyword Search:")
    keyword_results = searcher.search_keyword("MTHFR Genmutation", limit=5)
    print(f"   Found {len(keyword_results)} results")
    for r in keyword_results[:3]:
        print(f"   - [{r.section_id[:8]}...] score={r.keyword_score:.2f} header={r.section_header[:50]}")
    
    print("\n[3] Testing Semantic Search:")
    semantic_results = searcher.search_semantic("genetische Methylierung Behandlung", limit=5)
    print(f"   Found {len(semantic_results)} results")
    for r in semantic_results[:3]:
        print(f"   - [{r.section_id[:8]}...] score={r.semantic_score:.2f} header={r.section_header[:50]}")
    
    print("\n[4] Testing Hybrid Search:")
    hybrid_results = searcher.search("MTHFR Genmutation Methylierung", limit=10)
    print(f"   Found {len(hybrid_results)} results")
    print(f"   {'Source':<10} {'Semantic':<10} {'Keyword':<10} {'Combined':<10} Header")
    print(f"   {'-'*60}")
    for r in hybrid_results[:5]:
        print(f"   {r.source:<10} {r.semantic_score:<10.3f} {r.keyword_score:<10.3f} {r.combined_score:<10.3f} {r.section_header[:40]}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    # Don't forget to close DB connection
    searcher.close()
