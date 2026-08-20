"""Base interface for TTS models."""

from abc import ABC, abstractmethod
import numpy as np


class BaseTTS(ABC):
    """TTS model interface."""

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        ...

    @abstractmethod
    def load(self, language: str):
        """Load model for a language."""
        ...

    @abstractmethod
    def synthesize(self, text: str, language: str = "en", speed: float = 1.0) -> np.ndarray:
        """Synthesize speech. Returns float32 audio array."""
        ...
