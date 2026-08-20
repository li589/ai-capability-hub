"""Lightweight, numpy-free audio helpers.

Kept separate from ``audio.py`` (which depends on numpy/soundfile) so these
pure-stdlib helpers can be unit-tested in the host-side tests venv, which does
not install numpy. Used on the streaming ASR display path.
"""

import math
from typing import Sequence


def trim_leading_silence(
    samples: Sequence[float],
    sample_rate: int = 16000,
    win_ms: float = 30.0,
    lead_ms: float = 80.0,
    rel: float = 0.15,
    abs_floor: float = 3e-3,
):
    """Drop the leading low-energy run from a mono waveform.

    Splits the signal into ``win_ms`` frames, finds the first frame whose RMS
    crosses ``max(abs_floor, rel * peak_frame_rms)``, and returns the waveform
    from ``lead_ms`` before that frame onward. Returns the input unchanged when
    it is shorter than one frame, has fewer than two frames, or never crosses
    the threshold (e.g. pure silence).

    Returns the same sequence type as the input (list in, list out).

    This is display-only: it feeds the streaming ASR's head-flush so the first
    600ms chunk starts on real speech. It must NOT be applied to the audio fed
    into the real streaming cache (that regresses mid-sentence accuracy).
    """
    n = len(samples)
    w = int(sample_rate * win_ms / 1000)
    if w < 1 or n < w:
        return samples

    n_frames = n // w
    if n_frames < 2:
        return samples

    frame_rms = []
    for f in range(n_frames):
        base = f * w
        acc = 0.0
        for i in range(base, base + w):
            v = samples[i]
            acc += v * v
        frame_rms.append(math.sqrt(acc / w))

    peak = max(frame_rms)
    thr = max(abs_floor, rel * peak)

    onset_frame = -1
    for f, r in enumerate(frame_rms):
        if r >= thr:
            onset_frame = f
            break
    if onset_frame < 0:
        return samples

    lead = int(sample_rate * lead_ms / 1000)
    start = max(0, onset_frame * w - lead)
    return samples[start:]


def head_flush_display(flush: str, real: str) -> str:
    """Pick the partial text to display at the start of a sentence.

    While the live streaming string (``real``) is still shorter than the
    head-flush text (``flush``) — i.e. early in the sentence, before the real
    cache has caught up — show ``flush`` (which recovers the head the streaming
    cache drops/holds back). Once ``real`` is at least as long as ``flush``, it
    takes over, so the final displayed string equals ``real`` (no regression)
    and the head is never duplicated.
    """
    if flush and len(real) < len(flush):
        return flush
    return real


def to_processor_audio(samples):
    """Wrap a waveform for the Qwen3-ASR HF processor's ``audio=`` argument.

    The processor (WhisperFeatureExtractor) expects a list of BARE waveform
    arrays. Passing a ``(samples, sample_rate)`` tuple makes numpy raise
    ``ValueError: inhomogeneous shape`` — which, in transcribe_stream's
    ``except: return``, silently yields an empty transcription (the original
    Qwen3 "bad English" bug: it produced nothing and the UI showed Paraformer's
    Chinese-only output). Always pass bare samples; the sample rate is provided
    separately in the chat-template message, not here.
    """
    return [samples]
