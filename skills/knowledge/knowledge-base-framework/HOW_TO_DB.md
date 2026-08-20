# KB Database Guide

**Understanding and optimizing the Knowledge Base reference system.**

---

## Overview

The KB stores three interconnected data layers for each document:

```
Document (file)
    ├── Sections (file_sections)
    │   ├── Keywords (section_keywords)
    │   └── Embeddings (chroma_db)
    └── Metadata (files table)
```

Search quality depends on the density and accuracy of these references.

---

## Data Structure

### 1. Files Table
Stores document metadata:
- `file_path`: Absolute path to source
- `file_hash`: SHA256 for change detection
- `last_indexed`: Timestamp
- `index_status`: indexed/pending/failed

### 2. File Sections
Splits documents at headers (`#`, `##`, etc.):
- `section_header`: The heading text
- `content_preview`: First 500 characters
- `content_full`: Complete section text
- `parent_section_id`: Hierarchy for nested headers
- `line_start`, `line_end`: Position in source

### 3. Section Keywords
Extracted terms for keyword search:
- Parsed from `content_preview`
- Stopwords filtered (der, die, das, und, etc.)
- Umlaut normalized (ä→ae, ö→oe, ü→ue, ß→ss)
- Cross-referenced with `keywords` table

### 4. Embeddings
Vector representations in ChromaDB:
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- Generated from: `section_header` + `content_preview`
- Enables semantic similarity search

---

## Reference Quality Factors

### Good References
| Factor | Impact |
|--------|--------|
| Clear headers | Sections align with document structure |
| Dense keywords | More terms for keyword matching |
| Relevant embeddings | Better semantic search results |
| Complete metadata | Accurate file tracking |

### Poor References
| Issue | Cause | Fix |
|-------|-------|-----|
| Orphaned sections | `file_id` is NULL | Re-index file |
| Missing keywords | Content too short | Check section length |
| Stale embeddings | File changed, not re-indexed | Run `kb reindex` |
| Duplicate keywords | Same term multiple times | Check `section_keywords` table |

---

## Maintenance Commands

### Check Quality
```bash
# Full audit
python3 kb/scripts/kb_full_audit.py

# Find orphaned entries
python3 kb/scripts/kb_ghost_scanner.py

# Check specific file
python3 -c "
import sqlite3
conn = sqlite3.connect('knowledge.db')
cursor = conn.execute('SELECT COUNT(*) FROM file_sections WHERE file_id IS NULL')
print(f'Orphaned sections: {cursor.fetchone()[0]}')
conn.close()
"
```

### Rebuild References
```bash
# Re-index single file
python3 kb/indexer.py /path/to/file.md

# Re-index directory
python3 kb/indexer.py /path/to/directory/

# Re-generate embeddings (ChromaDB)
python3 kb/scripts/reembed_all.py
```

---

## Best Practices

### For Document Authors
- Use descriptive headers (`## Workflow Analysis` not `## Section 3`)
- Keep sections focused (avoid 5000+ word sections)
- Include relevant terms naturally in text
- Structure documents hierarchically

### For Developers
- Check `index_status` after bulk operations
- Run `kb_full_audit.py` weekly
- Monitor ChromaDB size growth
- Validate embeddings after model updates

### For Agents
- Query both keyword and semantic search
- Weight results by `importance_score`
- Use `content_preview` for context, `content_full` for detail
- Check parent sections for context

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Search finds wrong results | Poor keyword extraction | Re-index with fresh extraction |
| Semantic search slow | Cold ChromaDB | Run `kb/scripts/kb_warmup.py` |
| Missing documents | Indexing failed | Check `index_status = 'failed'` |
| Outdated content | File changed, not re-indexed | Re-index changed files |

---

## Schema Details

```sql
-- Key relationships
files.id → file_sections.file_id
file_sections.id → section_keywords.section_id
file_sections.id → embeddings.section_id (via ChromaDB metadata)
```

**Foreign Keys:** Enabled (`PRAGMA foreign_keys = ON`)

**Cascading Deletes:** 
- Deleting file → deletes sections → deletes keywords
- ChromaDB entries cleaned separately (not automatic)

---

*For implementation details, see `kb/indexer.py` and `kb/library/knowledge_base/hybrid_search.py`*
