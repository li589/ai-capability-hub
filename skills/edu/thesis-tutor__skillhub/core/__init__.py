"""
Thesis Tutor v4.0 - Core Package
"""

from .local_assistant import LocalAssistant, KnowledgeBase, IntentMatcher
from .api_client import UserConfig, DeepSeekClient

__version__ = "4.0.0"
__all__ = ["LocalAssistant", "KnowledgeBase", "IntentMatcher", "UserConfig", "DeepSeekClient"]
