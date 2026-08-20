"""Whisper ASR for English speech input - RESERVED for future implementation.

Will be integrated when English speech input is needed.
Interface matches AccurateAsr for drop-in routing.
"""

import numpy as np
from typing import Optional

import config
from translator.messages import SentenceAudio, AsrResult


class WhisperAsr:
    """Whisper ASR interface. Not implemented in this version."""

    def __init__(self):
        self._model = None
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def load(self):
        """Load Whisper model."""
        raise NotImplementedError("Whisper ASR not implemented in this version.")

    def transcribe(self, sentence: SentenceAudio) -> Optional[AsrResult]:
        """Transcribe English audio."""
        return None
