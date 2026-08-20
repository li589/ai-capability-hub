"""
Office Pro - Core Module

Combined module containing:
- Exception system and error codes
- Utility functions for file handling and validation
- Abstract base class for document processors
"""

from __future__ import annotations

import json
import hashlib
import time
from abc import ABC, abstractmethod
from functools import wraps, lru_cache
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Union, Callable, TypeVar

# =============================================================================
# Error Codes
# =============================================================================

class ErrorCode:
    """OpenClaw Skill Standard Error Codes"""
    
    SUCCESS = "SKILL_000"
    
    INVALID_PARAMS = "SKILL_101"
    MISSING_REQUIRED_PARAM = "SKILL_102"
    INVALID_TEMPLATE_NAME = "SKILL_103"
    INVALID_OUTPUT_PATH = "SKILL_104"
    INVALID_DATA_FORMAT = "SKILL_105"
    
    TEMPLATE_NOT_FOUND = "SKILL_201"
    TEMPLATE_INVALID = "SKILL_202"
    TEMPLATE_RENDER_ERROR = "SKILL_203"
    
    DATA_PARSE_ERROR = "SKILL_301"
    DATA_VALIDATION_ERROR = "SKILL_302"
    DATA_FILE_NOT_FOUND = "SKILL_303"
    DATA_ENCODING_ERROR = "SKILL_304"
    
    FILE_NOT_FOUND = "SKILL_401"
    FILE_ACCESS_DENIED = "SKILL_402"
    FILE_WRITE_ERROR = "SKILL_403"
    PATH_TRAVERSAL_DETECTED = "SKILL_404"
    
    DEPENDENCY_MISSING = "SKILL_501"
    DEPENDENCY_VERSION_MISMATCH = "SKILL_502"
    
    INTERNAL_ERROR = "SKILL_999"
    NOT_IMPLEMENTED = "SKILL_998"


# =============================================================================
# Exceptions
# =============================================================================

class OfficeProError(Exception):
    """Base exception for Office Pro"""
    
    def __init__(self, message: str, error_code: str = ErrorCode.INTERNAL_ERROR):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code
        }


class ParameterError(OfficeProError):
    """Parameter validation error"""
    
    def __init__(self, message: str, error_code: str = ErrorCode.INVALID_PARAMS):
        super().__init__(message, error_code)


class TemplateError(OfficeProError):
    """Template related error"""
    
    def __init__(self, message: str, error_code: str = ErrorCode.TEMPLATE_INVALID):
        super().__init__(message, error_code)


class TemplateNotFoundError(TemplateError):
    """Template file not found"""
    
    def __init__(self, template_path: str):
        super().__init__(
            f"Template not found: {template_path}",
            ErrorCode.TEMPLATE_NOT_FOUND
        )
        self.template_path = template_path


class TemplateRenderError(TemplateError):
    """Template rendering error"""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.TEMPLATE_RENDER_ERROR)


class DataError(OfficeProError):
    """Data processing error"""
    
    def __init__(self, message: str, error_code: str = ErrorCode.DATA_PARSE_ERROR):
        super().__init__(message, error_code)


class DataFileNotFoundError(DataError):
    """Data file not found"""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Data file not found: {file_path}",
            ErrorCode.DATA_FILE_NOT_FOUND
        )
        self.file_path = file_path


class DataParseError(DataError):
    """Data parsing error (JSON, CSV, etc.)"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorCode.DATA_PARSE_ERROR)
        self.original_error = original_error


class DataEncodingError(DataError):
    """Data encoding error"""
    
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        super().__init__(
            f"Encoding error reading {file_path}, expected {encoding}",
            ErrorCode.DATA_ENCODING_ERROR
        )


class FileError(OfficeProError):
    """File operation error"""
    
    def __init__(self, message: str, error_code: str = ErrorCode.FILE_WRITE_ERROR):
        super().__init__(message, error_code)


class PathTraversalError(FileError):
    """Path traversal attack detected"""
    
    def __init__(self, path: str):
        super().__init__(
            f"Path traversal detected: {path}",
            ErrorCode.PATH_TRAVERSAL_DETECTED
        )
        self.path = path


class FileAccessDeniedError(FileError):
    """File access denied"""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Access denied: {file_path}",
            ErrorCode.FILE_ACCESS_DENIED
        )


class DependencyError(OfficeProError):
    """Dependency error"""
    
    def __init__(self, message: str, error_code: str = ErrorCode.DEPENDENCY_MISSING):
        super().__init__(message, error_code)


class DocumentNotLoadedError(OfficeProError):
    """Document not loaded error"""
    
    def __init__(self, document_type: str = "document"):
        super().__init__(
            f"No {document_type} loaded. Call load_template() or create_document() first.",
            ErrorCode.INTERNAL_ERROR
        )


# =============================================================================
# Utility Functions
# =============================================================================

def validate_safe_path(file_path: str, allowed_base: Optional[str] = None) -> Path:
    """
    Validate file path security
    
    Args:
        file_path: File path to validate
        allowed_base: Optional base directory that the path must be within
        
    Returns:
        Resolved Path object
        
    Raises:
        PathTraversalError: If path traversal is detected
        FileAccessDeniedError: If path is outside allowed directory
    """
    path = Path(file_path)
    
    if '..' in file_path:
        raise PathTraversalError(file_path)
    
    try:
        resolved_path = path.resolve()
    except Exception as e:
        raise FileError(f"Invalid path: {file_path} - {e}")
    
    if allowed_base:
        base = Path(allowed_base).resolve()
        try:
            resolved_path.relative_to(base)
        except ValueError:
            raise FileAccessDeniedError(file_path)
    
    return resolved_path


def validate_file_exists(file_path: str, file_type: str = "File") -> Path:
    """
    Validate that a file exists
    
    Args:
        file_path: File path to validate
        file_type: Type description for error messages
        
    Returns:
        Path object if file exists
        
    Raises:
        DataFileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise DataFileNotFoundError(f"{file_type} not found: {file_path}")
    if not path.is_file():
        raise DataFileNotFoundError(f"{file_type} is not a file: {file_path}")
    return path


class TemplateCache:
    """
    Simple template cache with TTL support
    
    Caches template file metadata and modification times to avoid
    repeated filesystem checks.
    """
    _instance: Optional['TemplateCache'] = None
    _cache: Dict[str, Dict[str, Any]] = {}
    _ttl: int = 300
    
    def __new__(cls) -> 'TemplateCache':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() - entry['timestamp'] > self._ttl:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """Set cache value with current timestamp"""
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry"""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path]) -> str:
        """Get MD5 hash of file for cache key"""
        path = Path(file_path)
        if not path.exists():
            return ""
        
        hasher = hashlib.md5()
        hasher.update(str(path.resolve()).encode())
        hasher.update(str(path.stat().st_mtime).encode())
        return hasher.hexdigest()


def load_json_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    allowed_base: Optional[str] = None,
    validate_path: bool = True
) -> Dict[str, Any]:
    """
    Safely load a JSON file with comprehensive error handling
    
    Args:
        file_path: Path to JSON file
        encoding: File encoding (default: utf-8)
        allowed_base: Optional base directory restriction
        validate_path: Whether to validate path security
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        DataFileNotFoundError: If file does not exist
        DataParseError: If JSON parsing fails
        DataEncodingError: If file encoding is incorrect
        PathTraversalError: If path traversal is detected
    """
    if isinstance(file_path, Path):
        path = file_path
    else:
        path = Path(file_path)
    
    if validate_path:
        path = validate_safe_path(str(path), allowed_base)
    
    if not path.exists():
        raise DataFileNotFoundError(str(path))
    
    if not path.is_file():
        raise DataFileNotFoundError(f"Not a file: {path}")
    
    try:
        with open(path, 'r', encoding=encoding) as f:
            return json.load(f)
    except JSONDecodeError as e:
        raise DataParseError(
            f"Invalid JSON format in {path}: {e.msg} at line {e.lineno}, column {e.colno}",
            original_error=e
        )
    except UnicodeDecodeError as e:
        raise DataEncodingError(str(path), encoding)
    except PermissionError:
        raise DataFileNotFoundError(f"Permission denied: {path}")


def safe_resolve_path(
    file_path: str,
    base_dir: Optional[str] = None,
    must_exist: bool = False
) -> Path:
    """
    Safely resolve a file path
    
    Args:
        file_path: File path to resolve
        base_dir: Optional base directory
        must_exist: Whether the file must exist
        
    Returns:
        Resolved Path object
    """
    path = Path(file_path)
    
    if not path.is_absolute() and base_dir:
        path = Path(base_dir) / path
    
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    
    if must_exist and not resolved.exists():
        raise DataFileNotFoundError(str(resolved))
    
    return resolved


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, create if necessary
    
    Args:
        dir_path: Directory path
        
    Returns:
        Path object for the directory
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_template_dir(template_type: str = "word") -> Path:
    """
    Get default template directory
    
    Args:
        template_type: Type of template ('word' or 'excel')
        
    Returns:
        Path to template directory
    """
    skill_root = Path(__file__).parent
    return skill_root / "assets" / "templates" / template_type


def validate_template_path(
    template_name: str,
    template_type: str = "word",
    template_dir: Optional[str] = None
) -> Path:
    """
    Validate and resolve template path
    
    Args:
        template_name: Template filename
        template_type: Type of template ('word' or 'excel')
        template_dir: Custom template directory
        
    Returns:
        Resolved template Path
        
    Raises:
        DataFileNotFoundError: If template not found
    """
    if template_dir:
        base_dir = Path(template_dir)
    else:
        base_dir = get_template_dir(template_type)
    
    template_path = base_dir / template_name
    
    if not template_path.exists():
        raise DataFileNotFoundError(f"Template not found: {template_path}")
    
    return template_path


@lru_cache(maxsize=128)
def get_cached_template_list(template_dir: str, template_type: str) -> tuple:
    """
    Get cached list of templates in a directory
    
    Args:
        template_dir: Directory to search
        template_type: Type of template ('word' or 'excel')
        
    Returns:
        Tuple of template filenames
    """
    dir_path = Path(template_dir)
    if not dir_path.exists():
        return ()
    
    if template_type == 'word':
        pattern = '*.docx'
    elif template_type == 'excel':
        pattern = '*.xlsx'
    else:
        pattern = '*'
    
    return tuple(sorted(p.name for p in dir_path.glob(pattern)))


def invalidate_template_cache() -> None:
    """Invalidate the template list cache"""
    get_cached_template_list.cache_clear()


# =============================================================================
# Base Processor
# =============================================================================

DocumentType = TypeVar('DocumentType')
TemplateType = TypeVar('TemplateType')


def require_document(func):
    """
    Decorator to ensure document is loaded before method execution
    
    Usage:
        @require_document
        def some_method(self, ...):
            # self._document is guaranteed to be not None
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._document:
            raise DocumentNotLoadedError(self._document_type_name)
        return func(self, *args, **kwargs)
    return wrapper


def require_template(func):
    """Decorator to ensure template is loaded before method execution"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._template:
            raise DocumentNotLoadedError("template")
        return func(self, *args, **kwargs)
    return wrapper


class DocumentProcessor(ABC, Generic[DocumentType, TemplateType]):
    """
    Abstract base class for document processors
    
    Provides common interface for Word and Excel processing
    """
    
    _document_type_name: str = "document"
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize processor
        
        Args:
            template_dir: Custom template directory path
        """
        self.template_dir = template_dir or self._get_default_template_dir()
        self._document: Optional[DocumentType] = None
        self._template: Optional[TemplateType] = None
    
    @abstractmethod
    def _get_default_template_dir(self) -> str:
        """Get default template directory"""
        pass
    
    @abstractmethod
    def create_document(self) -> DocumentType:
        """Create new document"""
        pass
    
    @abstractmethod
    def load_document(self, path: str) -> DocumentType:
        """Load existing document"""
        pass
    
    @abstractmethod
    def load_template(self, template_name: str) -> TemplateType:
        """Load template file"""
        pass
    
    @abstractmethod
    def render_template(self, data: Dict[str, Any]) -> DocumentType:
        """Render template with data"""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save document to file"""
        pass
    
    def render_and_save(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Render template and save to file
        
        Args:
            data: Template data dictionary
            output_path: Output file path
            
        Returns:
            Saved file path
        """
        self.render_template(data)
        self.save(output_path)
        return output_path
    
    def _validate_template_path(self, template_name: str) -> Path:
        """
        Validate template path exists
        
        Args:
            template_name: Template filename
            
        Returns:
            Resolved template path
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        template_path = Path(self.template_dir) / template_name
        if not template_path.exists():
            raise TemplateNotFoundError(str(template_path))
        return template_path
    
    def _ensure_output_dir(self, path: str) -> None:
        """Ensure output directory exists"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def document(self) -> Optional[DocumentType]:
        """Get current document object"""
        return self._document
    
    @property
    def template(self) -> Optional[TemplateType]:
        """Get current template object"""
        return self._template
    
    def __enter__(self) -> 'DocumentProcessor':
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - cleanup resources"""
        self._document = None
        self._template = None
        return False
