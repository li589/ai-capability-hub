# KB Framework – Deterministic Context Mapping

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> Line numbers, not paragraphs.

## The Problem

RAG systems dump context into your agent's prompt — but you can't verify where it came from. When an agent says "According to your notes...", you're trusting fuzzy similarity search with no way to check.

**Lost-in-the-Middle:** Context gets buried. You're never sure which lines actually informed the answer.

The result: Hallucinations, outdated context, agents that can't trace their own reasoning.

## The Solution

KB Framework tracks **exact source locations** — not just documents, but line numbers:

```
📄 GESUNDHEITS_RATGEBER.md:142
📄 GESUNDHEITS_RATGEBER.md:156
📄 GESUNDHEITS_RATGEBER.md:189
```

Every search returns **pointers**, not paragraphs. The agent can cite, verify, and trace back every piece of context.

**What you get:**
- Line-level precision (not document-level)
- Verifiable citations with `file:line` format
- ChromaDB embeddings indexed by source location
- SQLite for metadata + relationship tracking

## Demo

```bash
$ kb search "Vitamin D Mangel"

Found 3 context pointers:
📄 GESUNDHEITS_RATGEBER.md:142 [0.87] - "Vitamin D Mangel: Ursachen..."
📄 GESUNDHEITS_RATGEBER.md:156 [0.82] - "Laborwerte: 25-OH-D3..."
📄 GESUNDHEITS_RATGEBER.md:189 [0.79] - "Supplementierung: 2000IU..."

$ kb audit
{
  "total_entries": 2847,
  "with_line_refs": 2847,
  "orphaned": 0,
  "last_sync": "2026-04-15T08:00:00Z"
}
```

The agent receives pointers it can cite directly:
> "According to line 142 of your health notes, Vitamin D deficiency..."

You can verify: open the file, go to line 142, read the source.

## Features

### 🎯 Precision over Recall
- **Line-level indexing** — Store embeddings with exact source locations
- **Pointer output** — Every search returns `file:line` citations
- **Verifiable context** — Agents can cite, humans can verify

### 🔗 Obsidian Integration
- Parse WikiLinks, Tags, Frontmatter, Embeds
- Backlink index with bidirectional linking
- Vault-wide search with source tracking

### 🔄 Always in Sync
- ChromaDB ↔ SQLite synchronization
- Orphan detection (entries in vector DB without source file)
- Audit reports with CSV export

### 🚀 Agent-Ready
- Drop-in Python API for your agents
- Context pointers work with any LLM
- No more "according to your notes... (unverified)"

## Installation

```bash
git clone https://github.com/Minenclown/kb-framework.git ~/.openclaw/kb
cd ~/.openclaw/kb && pip install -r requirements.txt
```

For CLI access, add to your `.bashrc`:
```bash
echo 'alias kb="~/.openclaw/kb/kb.sh"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

```bash
kb sync                    # Sync ChromaDB with SQLite
kb sync --dry-run          # Preview changes without applying
kb sync --stats            # Show sync statistics

kb audit                   # Full KB audit (summary)
kb audit -v                # Verbose output
kb audit --csv report.csv  # Export as CSV

kb ghost                   # Find orphaned entries (in ChromaDB but no source file)
kb ghost --scan-dirs ~/docs,~/notes   # Scan additional directories
kb ghost --purge           # Remove orphaned entries

kb warmup                  # Preload embedding model
kb warmup --model <name>   # Specify model to load
```

### Python API

#### Search (HybridSearch)

```python
from kb.library.knowledge_base import HybridSearch

# Initialize search
search = HybridSearch()

# Search with line-level precision
results = search.search("Vitamin D Mangel", limit=5)

for r in results:
    print(f"{r.file_path}:{r.section_id} [{r.score:.2f}]")
    print(f"  → {r.content_preview[:80]}...")
```

#### ChromaDB Integration

```python
from kb.library.knowledge_base import ChromaIntegration, embed_text

# Get singleton instance
chroma = ChromaIntegration()

# Embed text directly
vector = embed_text("Your text here")

# Query with filters
results = chroma.query(
    collection_name="kb_sections",
    query_texts=["query"],
    n_results=5,
    where={"file_path": {"$contains": "health"}}
)
```

#### Text Chunking

```python
from kb.library.knowledge_base import SentenceChunker, chunk_file

# Configure chunker
chunker = SentenceChunker(max_chunk_size=500, overlap=50)

# Chunk a single text
chunks = chunker.chunk("Long text content here...")

# Chunk an entire file
file_chunks = chunk_file("/path/to/document.md", chunker=chunker)
```

#### Obsidian Vault

```python
from kb.obsidian import ObsidianVault

vault = ObsidianVault("/path/to/vault")
vault.index()

# Find backlinks
backlinks = vault.find_backlinks("Notes/Meeting.md")

# Full-text search
results = vault.search("Project X")
```

#### Module Hierarchy

```python
# Top-level access
from kb import KBConfig, KBLogger, KBConnection

# Knowledge base library
from kb.library.knowledge_base import HybridSearch
from kb.library import ChromaIntegration

# Base modules
from kb.base.config import KBConfig
from kb.base.logger import KBLogger
from kb.base.db import KBConnection

# Obsidian integration
from kb.obsidian import ObsidianVault
from kb.obsidian.parser import extract_wikilinks, extract_tags
```

## Structure

```
~/.openclaw/kb/
├── kb/                     # Core Python modules
│   ├── commands/           # CLI commands (sync, audit, ghost, warmup)
│   ├── obsidian/           # Obsidian integration
│   └── base/               # Core components
├── library/                # Your content (markdown, PDFs)
├── chroma_db/              # ChromaDB vector database
└── knowledge.db            # SQLite metadata database
```

## License

MIT License
