"""
KB Utility Functions
===================

Shared utility functions for the knowledge base library.
"""

from typing import List


def build_embedding_text(
    header: str,
    content: str,
    keywords: List[str]
) -> str:
    """
    Builds optimal text for embedding.

    Structure:
    - Header as title (high weight via repetition)
    - Content preview (first 500 chars)
    - Keywords as bonus context

    Args:
        header: Section header/title
        content: Section content
        keywords: List of keywords to boost relevance

    Returns:
        Formatted text optimized for embedding
    """
    parts = []

    # Header bekommt.extra Weight durch Repetition
    if header:
        parts.append(header)
        parts.append(header)  # Doppelte Gewichtung

    # Content Preview (begrenzt für Performance)
    if content:
        preview = content[:500].strip()
        parts.append(preview)

    # Keywords als Kontext
    if keywords:
        parts.append(" ".join(keywords[:10]))

    return " | ".join(parts)