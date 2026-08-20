"""
KB Framework - Core Package
==========================

Deterministic Context Mapping for AI Agents.

The KB Framework tracks exact source locations in knowledge bases,
providing line-level precision instead of document-level similarity.
Agents can cite, verify, and trace back every piece of context.

Architecture:
-------------
- kb.base: Core components (Config, DB, Logging, Commands)
- kb.commands: CLI command implementations
- kb.library: Knowledge base library (search, embeddings, chunking)
- kb.obsidian: Obsidian vault integration

Usage:
------
    from kb import KBConfig, KBLogger, KBConnection
    
    config = KBConfig.get_instance()
    logger = KBLogger.get_logger(__name__)
    
    with KBConnection() as conn:
        conn.execute("SELECT ...")

Modules:
--------
- kb.base: Framework core
- kb.commands: CLI commands
- kb.library: Knowledge base library
- kb.obsidian: Obsidian integration
"""

__version__ = "1.1.0"

__all__ = [
    '__version__',
]