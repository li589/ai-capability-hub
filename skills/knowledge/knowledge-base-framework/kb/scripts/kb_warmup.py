#!/usr/bin/env python3
"""
KB Warmup – Preloads ChromaDB model

Runtime: At server start (via systemd or OpenClaw init)
Purpose: First query should not be 8s slow
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".openclaw" / "kb"))

from kb.library.knowledge_base.chroma_integration import ChromaIntegration

def warmup():
    print("Warming up ChromaDB model...")
    chroma = ChromaIntegration()
    
    # Preload model
    _ = chroma.model
    print("Model loaded")
    
    # Get collection reference (initializes ChromaDB internally)
    _ = chroma.sections_collection
    print("ChromaDB Collection ready")
    
    print("KB Warmup complete")

if __name__ == "__main__":
    warmup()
