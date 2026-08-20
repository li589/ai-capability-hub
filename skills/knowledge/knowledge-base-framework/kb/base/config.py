#!/usr/bin/env python3
"""
KBConfig - Singleton für KB Konfiguration

Einmal laden, überall nutzen.
Environment Variables können Werte überschreiben.

Verbesserungen gegenüber Original:
- Thread-safe Initialization
- Lazy Loading mit Validation
- Path Existence Checks
- Type-Safe Property Access
"""

from pathlib import Path
from typing import Optional, Dict, Any
import os
import threading


class KBConfigError(Exception):
    """Configuration-related errors."""
    pass


class KBConfig:
    """
    Singleton für KB Konfiguration.
    
    Thread-safe implementation mit lazy loading.
    
    Usage:
        config = KBConfig.get_instance()
        db_path = config.db_path  # Auto-initialized
        
        # Force reload
        config = KBConfig.reload(base_path="/new/path")
    """
    
    _instance: Optional['KBConfig'] = None
    _lock = threading.Lock()
    _initialized: bool = False
    
    DEFAULT_BASE = Path.home() / ".openclaw" / "kb"
    
    def __init__(self, base_path: Optional[Path] = None, skip_validation: bool = False):
        if KBConfig._instance is not None:
            raise KBConfigError("Use KBConfig.get_instance() instead of constructor")
        
        self._base_path = self._resolve_base_path(base_path)
        self._env_overrides: Dict[str, str] = {}
        self._validated = False
        
        if not skip_validation:
            self._validate()
        
        KBConfig._instance = self
        KBConfig._initialized = True
    
    @staticmethod
    def _resolve_base_path(base_path: Optional[Path]) -> Path:
        """Resolve base path from parameter or environment."""
        if base_path is not None:
            return Path(base_path).resolve()
        
        env_base = os.getenv("KB_BASE_PATH")
        if env_base:
            return Path(env_base).resolve()
        
        return KBConfig.DEFAULT_BASE.resolve()
    
    def _validate(self) -> None:
        """Validate configuration paths. Fails fast on critical issues."""
        # Check base directory - should exist or be creatable
        if not self._base_path.exists():
            # Try to create it
            try:
                self._base_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise KBConfigError(f"Cannot create base path {self._base_path}: {e}")
        
        # Check if base_path is actually a directory
        if not self._base_path.is_dir():
            raise KBConfigError(f"Base path exists but is not a directory: {self._base_path}")
        
        self._validated = True
    
    @classmethod
    def get_instance(cls, base_path: Optional[Path] = None) -> 'KBConfig':
        """
        Returns singleton instance (lazy initialization).
        
        Thread-safe: Uses double-checked locking pattern.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(base_path)
        elif base_path is not None:
            # If a different base_path is requested, reload
            existing = cls._instance._base_path.resolve()
            requested = Path(base_path).resolve()
            if existing != requested:
                cls._instance = cls(base_path)
        
        return cls._instance
    
    @classmethod
    def reload(cls, base_path: Optional[Path] = None) -> 'KBConfig':
        """Forces reload of configuration."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
        return cls.get_instance(base_path)
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton (mainly for testing)."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
    
    # --- Path Properties with Environment Override Support ---
    
    @property
    def base_path(self) -> Path:
        """Root directory of KB installation."""
        return self._base_path
    
    @property
    def db_path(self) -> Path:
        env = os.getenv("KB_DB_PATH")
        if env:
            return Path(env).resolve()
        return self._base_path / "knowledge.db"
    
    @property
    def chroma_path(self) -> Path:
        env = os.getenv("KB_CHROMA_PATH")
        if env:
            return Path(env).resolve()
        return self._base_path / "chroma_db"
    
    @property
    def library_path(self) -> Path:
        env = os.getenv("KB_LIBRARY_PATH")
        if env:
            return Path(env).resolve()
        return Path.home() / "knowledge" / "library"
    
    @property
    def workspace_path(self) -> Path:
        env = os.getenv("KB_WORKSPACE_PATH")
        if env:
            return Path(env).resolve()
        return Path.home() / ".openclaw" / "workspace"
    
    @property
    def ghost_cache_path(self) -> Path:
        env = os.getenv("KB_GHOST_CACHE_PATH")
        if env:
            return Path(env).resolve()
        return Path.home() / ".knowledge" / "ghost_cache.json"
    
    @property
    def backup_dir(self) -> Path:
        env = os.getenv("KB_BACKUP_DIR")
        if env:
            return Path(env).resolve()
        return Path.home() / ".knowledge" / "backup"
    
    @property
    def index_roots(self) -> list[str]:
        """
        Root directories to index by default.
        
        Override via KB_INDEX_ROOTS env var (comma-separated):
            KB_INDEX_ROOTS=projektplanung,learnings,dokumentation
        """
        env = os.getenv("KB_INDEX_ROOTS")
        if env:
            return [p.strip() for p in env.split(",") if p.strip()]
        return ["projektplanung", "learnings"]
    
    # --- Utility Methods ---
    
    def ensure_dir(self, path: Path) -> Path:
        """Ensure directory exists, create if needed."""
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            'base_path': str(self.base_path),
            'db_path': str(self.db_path),
            'chroma_path': str(self.chroma_path),
            'library_path': str(self.library_path),
            'workspace_path': str(self.workspace_path),
            'ghost_cache_path': str(self.ghost_cache_path),
            'backup_dir': str(self.backup_dir),
        }
    
    def __repr__(self) -> str:
        return f"KBConfig(base={self._base_path}, validated={self._validated})"
    
    def __str__(self) -> str:
        return f"KBConfig at {self._base_path}"


# Convenience function for quick access
def get_config() -> KBConfig:
    """Get KBConfig singleton instance."""
    return KBConfig.get_instance()
