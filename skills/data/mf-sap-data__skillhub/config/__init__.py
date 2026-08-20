"""
配置模块
"""

from .settings import load_config, get_default_config
from .bapi_mapping import BAPI_MAPPING
from .table_mapping import TABLE_MAPPING

__all__ = [
    "load_config",
    "get_default_config",
    "BAPI_MAPPING",
    "TABLE_MAPPING"
]