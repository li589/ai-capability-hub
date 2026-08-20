"""Message types passed between pipeline stages."""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class SentenceAudio:
    """A complete sentence's audio, bounded by VAD."""
    samples: np.ndarray
    start_ms: int
    end_ms: int


@dataclass
class AsrResult:
    """ASR output."""
    text: str
    is_final: bool
    speaker_id: int = -1  # -1 = unknown, reserved for future CAM++
    start_ms: int = 0
    end_ms: int = 0


@dataclass
class TranslationResult:
    """Translation output."""
    source_text: str
    translated_text: str
    src_lang: str
    tgt_lang: str
    sentence_id: int = 0


@dataclass
class TtsResult:
    """TTS output."""
    audio_path: str
    sentence_id: int = 0
    sample_rate: int = 44100
