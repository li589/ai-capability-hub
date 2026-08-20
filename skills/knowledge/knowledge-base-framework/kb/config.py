"""
KB Framework Configuration

Configuration module for the knowledge base framework.
"""

import os
from pathlib import Path

# Database
DB_PATH = os.getenv("KB_DB_PATH", "library/biblio.db")
CHROMA_PATH = os.getenv("KB_CHROMA_PATH", "library/chroma_db/")

# Library
LIBRARY_PATH = os.getenv("KB_LIBRARY_PATH", "library/")

# Search parameters
DEFAULT_LIMIT = 20
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

# OCR (for image-based PDFs)
OCR_LANGUAGES = ["de", "en"]
OCR_GPU = False  # True if GPU available


# Registry metadata for ClawHub and tooling
__version__ = "0.2.0"

__registry__ = {
    "name": "kb-framework",
    "version": __version__,
    "description": "Hybrid Knowledge Base with Markdown/PDF/OCR, SQLite + ChromaDB, Obsidian integration",
    "requirements": [
        "chromadb>=0.4.0",
        "sentence-transformers>=2.0.0",
        "PyMuPDF>=1.23.0",
        "torch>=2.0.0",
        "numpy",
        "tqdm",
    ],
    "optional": [
        "easyocr>=1.7.0",
        "obsidian-api",
    ],
    "env": {
        "KB_CHROMA_PATH": {
            "description": "Path to ChromaDB directory",
            "default": "library/chroma_db/",
            "required": False,
        },
        "KB_DB_PATH": {
            "description": "Path to SQLite database",
            "default": "library/biblio.db",
            "required": False,
        },
        "KB_LIBRARY_PATH": {
            "description": "Path to library directory",
            "default": "library/",
            "required": False,
        },
    },
    "config_paths": {
        "config": "kb/config.py",
        "db": "library/biblio.db",
        "chroma": "library/chroma_db/",
        "library": "library/",
    },
}
