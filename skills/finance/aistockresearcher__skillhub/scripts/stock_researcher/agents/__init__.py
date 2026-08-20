"""Investment大师 agents"""
from .buffett import BuffettAnalyzer
from .graham import GrahamAnalyzer
from .lynch import LynchAnalyzer
from .technical import TechnicalAgent
from .sentiment import SentimentAnalyzer

__all__ = ["BuffettAnalyzer", "GrahamAnalyzer", "LynchAnalyzer", "TechnicalAgent", "SentimentAnalyzer"]