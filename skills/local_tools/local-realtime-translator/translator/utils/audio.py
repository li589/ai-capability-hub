"""Audio utility functions."""

import numpy as np
import soundfile as sf
from pathlib import Path


def save_audio(audio: np.ndarray, path: str, sample_rate: int = 44100):
    """Save audio array to wav file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, audio, sample_rate)


def normalize_audio(audio: np.ndarray, target_peak: float = 0.95,
                    silence_rms: float = 1e-4) -> np.ndarray:
    """Peak-normalize audio toward target_peak to help ASR on quiet input.

    Boosts (or attenuates) the signal so its loudest sample sits at
    ``target_peak``, which makes recognition more robust to low microphone
    gain. Near-silent input (RMS below ``silence_rms``) is returned unchanged
    so we don't amplify pure noise or divide by ~zero.

    Returns a float32 array; the input is never mutated.
    """
    if audio is None or len(audio) == 0:
        return audio

    audio = audio.astype(np.float32, copy=False)
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms < silence_rms:
        return audio

    peak = float(np.max(np.abs(audio)))
    if peak <= 0.0:
        return audio

    return (audio * (target_peak / peak)).astype(np.float32)
