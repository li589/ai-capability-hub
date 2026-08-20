#!/usr/bin/env python3
"""ChromaDB Sync Tool - Synchronizes SQLite with ChromaDB."""

import argparse
import sqlite3
import sys
from pathlib import Path

# Add kb to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.knowledge_base.chroma_integration import ChromaIntegration
from config import CHROMA_PATH, DB_PATH


def get_sqlite_sections(conn):
    """Get all section IDs from SQLite."""
    # file_sections has: id (INTEGER), file_id (INTEGER), section_header, section_content
    cursor = conn.execute(
        "SELECT id, file_id FROM file_sections"
    )
    return {str(row[0]): str(row[1]) for row in cursor.fetchall()}


def get_chroma_sections(chroma_path):
    """Get all section IDs from ChromaDB."""
    try:
        chroma = ChromaIntegration(chroma_path=chroma_path)
        results = chroma.sections_collection.get(include=[])
        return set(results['ids'])
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")
        return set()


def sync_stats(conn, chroma_path):
    """Show sync statistics."""
    sqlite_sections = get_sqlite_sections(conn)
    chroma_sections = get_chroma_sections(chroma_path)
    
    sqlite_count = len(sqlite_sections)
    chroma_count = len(chroma_sections)
    
    missing_from_chroma = set(sqlite_sections.keys()) - chroma_sections
    orphans_in_chroma = chroma_sections - set(sqlite_sections.keys())
    
    print(f"📊 Sync Statistics")
    print(f"  SQLite Sections:   {sqlite_count}")
    print(f"  ChromaDB Sections: {chroma_count}")
    print(f"  Coverage:          {chroma_count/max(sqlite_count,1)*100:.1f}%")
    print(f"  Missing:           {len(missing_from_chroma)}")
    print(f"  Orphans:           {len(orphans_in_chroma)}")
    
    return missing_from_chroma, orphans_in_chroma


def sync_dry_run(conn, chroma_path):
    """Show what would be synchronized."""
    missing, orphans = sync_stats(conn, chroma_path)
    
    if missing:
        print(f"\n📥 Would add to ChromaDB: {len(missing)} sections")
    
    if orphans:
        print(f"\n🗑️  Would remove from ChromaDB: {len(orphans)} orphans")
    
    if not missing and not orphans:
        print(f"\n✅ All synchronized!")


def sync_execute(conn, chroma_path):
    """Execute the synchronization."""
    missing, orphans = sync_stats(conn, chroma_path)
    
    if missing:
        print(f"\n📥 Adding {len(missing)} sections to ChromaDB...")
        # TODO: Use EmbeddingPipeline to embed missing sections
        print(f"   (Here EmbeddingPipeline.embed_sections() would be called)")
    
    if orphans:
        print(f"\n🗑️  Removing {len(orphans)} orphans from ChromaDB...")
        chroma = ChromaIntegration(chroma_path=chroma_path)
        chroma.sections_collection.delete(ids=list(orphans))
        print(f"   ✅ {len(orphans)} orphans removed")
    
    if not missing and not orphans:
        print(f"\n✅ Already synchronized!")


def main():
    parser = argparse.ArgumentParser(description='ChromaDB Sync Tool')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    parser.add_argument('--dry-run', action='store_true', help='Simulation without changes')
    parser.add_argument('--execute', action='store_true', help='Execute synchronization')
    
    args = parser.parse_args()
    
    if not any([args.stats, args.dry_run, args.execute]):
        parser.print_help()
        return
    
    # Connect to DB
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        if args.stats:
            sync_stats(conn, CHROMA_PATH)
        elif args.dry_run:
            sync_dry_run(conn, CHROMA_PATH)
        elif args.execute:
            sync_execute(conn, CHROMA_PATH)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
