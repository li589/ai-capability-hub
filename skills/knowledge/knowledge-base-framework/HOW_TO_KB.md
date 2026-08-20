# HOW_TO_KB.md – Knowledge Base Framework

**Letzte Änderung:** 2026-04-15  
** Zielgruppe:** Entwickler

---

## 1. Übersicht

Das KB Framework ist ein semantischer Dokumentenindex mit Hybrid Search.

| Komponente | Technologie |
|------------|-------------|
| Datenbank | SQLite (WAL Mode) |
| Vector Store | ChromaDB |
| Embedding Modell | `all-MiniLM-L6-v2` (384 Dimensionen) |
| Suchmethode | Hybrid: 60% Semantic + 40% Keyword |
| Indexierung | Markdown-Header-basiert |

**Architektur-Prinzip:** Delta-Indexierung via `file_hash` (MD5). Nur geänderte Dateien werden neuindexiert.

---

## 2. Quick Start

### Installation

```bash
# Bereits installiert in ~/.openclaw/kb/
# CLI verfügbar via:
cd ~/projects/kb-framework && ./kb.sh --help

# Oder direkt:
python -m kb --help
```

### Erste Schritte

```bash
# 1. Verzeichnis indexieren
kb index ~/knowledge/library --recursive

# 2. ChromaDB synchen (nach Indexierung)
kb sync --stats

# 3. Erstes Query
kb search "Python async patterns"

# 4. Audit machen
kb audit --verbose
```

---

## 3. Architektur

### 3.1 Datenbank-Layer (SQLite)

**Pfad:** `~/.openclaw/kb/knowledge.db`

**Kerntabellen:**

| Tabelle | Zweck |
|---------|-------|
| `files` | Datei-Metadaten (1:1 pro Datei) |
| `file_sections` | Header-basierte Sections (1:N pro Datei) |
| `embeddings` | ChromaDB-Sync-Tracking |

**Änderungsdetection:**

```python
file_hash = md5(file.read_bytes())
# Bei Hash-Änderung → Section löschen + neu einfügen
```

### 3.2 ChromaDB-Integration

**Pfad:** `~/.openclaw/kb/chroma_db/`

```python
# Lazy Loading beim ersten Zugriff
from kb.library.knowledge_base import ChromaIntegration
chroma = ChromaIntegration()
collection = chroma.sections_collection  # "kb_sections"
```

**Collection-Struktur:**

```python
{
    "ids": ["uuid-section-id"],
    "embeddings": [[0.123, -0.456, ...]],  # 384-dim
    "metadatas": [{
        "file_id": "uuid",
        "file_path": "/path/to/file.md",
        "section_header": "Header",
        "importance_score": 0.75
    }],
    "documents": ["Header | Content Preview"]  # max 2000 chars
}
```

### 3.3 Hybrid Search

```
Query
  ├─→ ChromaDB Semantic Search (60%)
  │     └─→ collection.query() → cosine distance
  └─→ SQLite LIKE Keyword Search (40%)
        └─→ content_full LIKE '%term%'
  └─→ Merge & Rank
        └─→ normalized_scores × weights
        └─→ importance_boost × combined_score
```

**Fallback:** Wenn ChromaDB fehlschlägt → reines Keyword-Search.

---

## 4. Commands

### 4.1 `kb index` – Indexieren

```bash
# Einzelne Datei
kb index ~/notes/meeting.md

# Verzeichnis rekursiv
kb index ~/knowledge/library --recursive

# Force-Reindex (auch bei unchanged hash)
kb index ~/notes/todo.md --force
```

**Return Codes:** 0 = Erfolg, 1 = Fehler

### 4.2 `kb search` – Suchen

```bash
# Standard Query
kb search "async await patterns"

# Mehr Results
kb search "database migrations" --limit 50

# Nur Semantic (ohne Keyword)
kb search "machine learning" --semantic-only

# Detailliertes Format
kb search "authentication" --format full
```

**Output (short):**
```
📄 auth.md:45 [0.87] JWT Token Validation
📄 oauth.md:120 [0.72] OAuth2 Flow
```

### 4.3 `kb sync` – ChromaDB Sync

```bash
# Statistiken anzeigen
kb sync --stats

# Dry-Run (was würde passieren)
kb sync --dry-run

# Delta-Sync (nur fehlende) – Default
kb sync --delta

# Mit Cleanup verwaister Einträge
kb sync --delete-orphans

# Einzelne Datei synchen
kb sync --file-id <UUID>

# Batch-Size anpassen
kb sync --batch-size 64
```

### 4.4 `kb audit` – Integritätscheck

```bash
# Voller Audit mit Details
kb audit --verbose

# Ohne ChromaDB-Check (schneller)
kb audit --skip-chroma

# CSV-Export
kb audit --export-csv issues.csv

# Bestimmte Checks
kb audit --checks db_integrity,library_paths
```

**Checks:** `db_integrity`, `schema`, `library_paths`, `null_paths`, `embeddings_table`, `chroma_sync`, `orphaned_entries`

### 4.5 `kb ghost` – Neue Dateien finden

```bash
# Scan mit Defaults
kb ghost --scan-dirs ~/knowledge/library

# Nur PDFs und Textdateien
kb ghost --extensions .pdf,.txt,.md

# Dry-Run
kb ghost --scan-dirs ~/downloads --dry-run

# JSON Output für Scripting
kb ghost --scan-dirs ~/docs --json-output

# Größenfilter
kb ghost --min-size 1024 --max-size 104857600

# Bestimmte Verzeichnisse ausschließen
kb ghost --exclude-dirs node_modules,.git,temp
```

### 4.6 `kb warmup` – Model vorladen

```bash
# Model in RAM laden (braucht ~8s beim ersten Mal)
kb warmup

# Mit Memory-Check
kb warmup --verbose

# Bestimmtes Model
kb warmup --model all-MiniLM-L6-v2

# Check ob bereits geladen
kb warmup --check
```

---

## 5. Python API

### 5.1 Hybrid Search

```python
from kb.library.knowledge_base import HybridSearch
from kb.base.config import KBConfig

config = KBConfig()
searcher = HybridSearch(config.db_path, config.chroma_path)

results = searcher.search(
    query="async await patterns",
    limit=20,
    semantic_only=False,  # Hybrid-Search
    keyword_only=False
)

for r in results:
    print(f"{r.section_header} [Score: {r.combined_score:.2f}]")
    print(f"  → {r.file_path}:{r.line_start}")
```

### 5.2 Indexierung

```python
from kb.indexer import BiblioIndexer
from pathlib import Path

indexer = BiblioIndexer("~/.openclaw/kb/knowledge.db")
with indexer:
    result = indexer.index_file(Path("~/notes/meeting.md"))
    print(f"Indexed {result['sections']} sections")
```

### 5.3 ChromaDB Direct Access

```python
from kb.library.knowledge_base import ChromaIntegration

chroma = ChromaIntegration()
collection = chroma.sections_collection

# Direkte Query
results = collection.query(
    query_texts=["Python decorators"],
    n_results=10,
    include=["metadatas", "distances"]
)

for i, section_id in enumerate(results['ids'][0]):
    distance = results['distances'][0][i]
    similarity = max(0.0, 1.0 - distance)
    print(f"Match: {results['metadatas'][0][i]['section_header']} ({similarity:.2f})")
```

---

## 6. Troubleshooting

### ChromaDB Connection Failed

```bash
# Prüfe ob Verzeichnis existiert
ls -la ~/.openclaw/kb/chroma_db/

# Repair permissions
chmod 755 ~/.openclaw/kb/chroma_db/

# Full Re-Sync
kb sync --full
```

### Search Quality Issues

```bash
# Sync-Status prüfen
kb sync --stats

# Fehlende nachsynchen
kb sync --delta

# Embeddings-Tabelle checken
kb audit --checks embeddings_table,chroma_sync
```

### langsame erste Query (Cold Start)

```bash
# Model vorladen
kb warmup --verbose

# Prüfe Memory
free -m | grep MemAvailable

# Minimum: 500MB
```

### Ghost findet keine Dateien

```bash
# Dry-Run für Debugging
kb ghost --scan-dirs ~/documents --dry-run --verbose

# Extensions prüfen
kb ghost --extensions .pdf,.md,.txt

# Verzeichnis ausschließen
kb ghost --exclude-dirs .git,node_modules,temp
```

### Delta-Indexierung funktioniert nicht

```bash
# Force-Reindex
kb index ~/path/to/file.md --force

# Audit prüft Hash-Mismatch
kb audit --verbose
```

---

## 7. Konfiguration

**Environment Variables:**

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `KB_BASE_PATH` | `~/.openclaw/kb` | Root |
| `KB_DB_PATH` | `{base}/knowledge.db` | SQLite |
| `KB_CHROMA_PATH` | `{base}/chroma_db` | ChromaDB |
| `KB_LIBRARY_PATH` | `~/knowledge/library` | Library |

**Programmatisch:**

```python
from kb.base.config import KBConfig

config = KBConfig()
# Singleton – Änderungen global
config._base_path = Path("/custom/path")
```

---

## 8. Schema (Kurzreferenz)

```
knowledge.db
├── files (id, file_path, file_name, file_hash, index_status, ...)
├── file_sections (id, file_id, section_header, section_level, content_full, ...)
├── embeddings (id, section_id, chroma_id, embedding_hash, ...)
├── keywords, section_keywords (Many-to-Many)
└── entries, attachments, themen, kategorie, ...
```

---

*Quelle:* `~/.openclaw/agents/biblio/2026-04-15_kb_architecture_analysis.md`