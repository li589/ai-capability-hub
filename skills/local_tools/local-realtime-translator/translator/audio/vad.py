"""Voice Activity Detection using FunASR FSMN-VAD for endpoint detection."""

import enum
import numpy as np
import torch
from typing import Optional, List

import config
from translator.messages import SentenceAudio


class VadState(enum.IntEnum):
    SILENCE = 0
    SPEECH = 1
    TRAILING_SILENCE = 2


class VadEngine:
    """FunASR FSMN-VAD with built-in endpoint detection.

    Uses a neural network (Deep-FSMN) trained on speech/silence classification,
    providing more intelligent sentence boundary detection than simple energy
    or probability thresholds.
    """

    # Samples per FSMN-VAD chunk (chunk_size is declared in ms).
    _CHUNK_SAMPLES = int(config.SAMPLE_RATE * config.FSMN_VAD_CHUNK_MS / 1000)

    def __init__(self):
        from funasr import AutoModel
        from translator.utils.models import resolve_local_model
        # Prefer the local cache dir to avoid ModelScope's network check at
        # startup (stalls/fails when offline once the model is cached).
        self._model = AutoModel(
            model=resolve_local_model(config.FSMN_VAD_MODEL),
            disable_update=True,
            disable_log=True,
        )
        self._cache = {}
        self._is_speaking = False
        self._buf: List[np.ndarray] = []
        self._buf_len = 0

    def process_chunk(self, samples: np.ndarray, is_final: bool = False) -> List[List[int]]:
        """Process audio chunk through FSMN-VAD.

        Callers feed small (e.g. 32ms) chunks, but FSMN-VAD is configured for
        FSMN_VAD_CHUNK_MS blocks. We accumulate samples and only run a forward
        pass once a full chunk is available (or on is_final), so the feed
        granularity matches the declared chunk_size instead of invoking the
        model ~6x more often than intended.

        Returns list of segments: [[start_ms, end_ms], ...]
        - [start_ms, -1] means speech started but not yet ended
        - [-1, end_ms] means speech ended (continuation of previous start)
        - [start_ms, end_ms] means complete segment detected
        - [] means no event
        """
        if len(samples) > 0:
            self._buf.append(samples)
            self._buf_len += len(samples)

        if not is_final and self._buf_len < self._CHUNK_SAMPLES:
            return []

        if self._buf_len == 0:
            return []

        block = np.concatenate(self._buf) if len(self._buf) > 1 else self._buf[0]
        self._buf = []
        self._buf_len = 0

        result = self._model.generate(
            input=block,
            cache=self._cache,
            is_final=is_final,
            chunk_size=config.FSMN_VAD_CHUNK_MS,
            max_end_silence_time=config.FSMN_VAD_MAX_END_SILENCE_MS,
            # FunASR's streaming FSMN-VAD defaults dynamic_silence=True, which
            # IGNORES max_end_silence_time and instead overrides the endpoint
            # threshold every chunk from a built-in schedule that grows with how
            # long the speaker has been talking (<=10s speech -> 2000ms silence
            # required, <=20s -> 1000ms, ...). On a continuous monologue this
            # pushed the endpoint to ~2000ms, so a 70s clip whose true boundaries
            # give 11 sentences was merged into just 3 giant (27s/11s/22s)
            # blobs. That both inflated the accurate-pass latency (Qwen3 cannot
            # finalize until a whole blob ends) and fed glued-together sentences
            # to translation/TTS. Disabling it lets max_end_silence_time (800ms)
            # actually take effect, which restores the 11-sentence segmentation
            # without over-splitting (500ms was measured to over-split into 21).
            dynamic_silence=False,
        )
        if result and len(result) > 0:
            item = result[0]
            if isinstance(item, dict):
                segments = item.get("value", [])
            elif hasattr(item, "value"):
                segments = item.value
            else:
                segments = []
            return segments if segments else []
        return []

    def reset(self):
        """Reset VAD state for new session."""
        self._cache = {}
        self._is_speaking = False
        self._buf = []
        self._buf_len = 0


class SentenceManager:
    """Collects audio chunks and detects sentence boundaries using FSMN-VAD endpoint detection.

    Unlike the previous SileroVAD approach (fixed 600ms silence threshold),
    FSMN-VAD uses a trained neural model to detect speech start/end points,
    providing more semantically aware sentence boundaries.
    """

    # Rolling pre-buffer length, in 32ms chunks. FSMN-VAD has a large detection
    # latency: it can emit the speech-start event well over a second after the
    # true onset, and the start_ms it reports can itself lag the true onset.
    # The previous 320ms pre-buffer was far too short to cover that gap, so the
    # first syllable(s) were discarded before speech was confirmed and never
    # reached either ASR (the live partial dropped/garbled the head). We keep a
    # ~2s rolling buffer instead, and on speech-start slice it back to the
    # reported start_ms (minus a safety margin) so the true sentence head is
    # recovered. See config.VAD_PRE_BUFFER_MS / VAD_ONSET_MARGIN_MS.
    _PRE_BUFFER_CHUNKS = int(round(config.VAD_PRE_BUFFER_MS / config.BLOCK_MS))
    _ONSET_MARGIN_CHUNKS = int(round(config.VAD_ONSET_MARGIN_MS / config.BLOCK_MS))

    def __init__(self, vad: VadEngine):
        self._vad = vad
        self._state = VadState.SILENCE
        self._sentence_chunks: List[np.ndarray] = []
        # Rolling buffer of (timestamp_ms, samples) so onset can be sliced by
        # the VAD-reported start_ms rather than a fixed count of recent chunks.
        self._pre_buffer: List[tuple] = []
        self._sentence_start_ms = 0
        self._current_ms = 0
        self._speech_chunk_count = 0
        # Onset audio (the leading audio recovered at speech-start) made
        # available for one read via ``take_onset``. The live streaming ASR
        # uses it to seed the sentence so the first syllable — spoken before
        # the VAD latched onto speech — is not dropped.
        self._onset_chunks: Optional[List[np.ndarray]] = None

    @property
    def state(self) -> VadState:
        return self._state

    def take_onset(self) -> Optional[List[np.ndarray]]:
        """Return (and clear) the onset audio recovered at speech start.

        Returns the list of audio chunks from the recovered sentence head
        (everything from the VAD-reported start_ms up to the detection chunk),
        or ``None`` if no sentence has started since the last call. Feeding
        these to the streaming ASR recovers the leading audio the VAD consumed
        while deciding it was speech.
        """
        chunks = self._onset_chunks
        self._onset_chunks = None
        return chunks

    def _slice_onset(self, start_ms: int) -> List[np.ndarray]:
        """Return buffered chunks at/after ``start_ms`` (minus a safety margin).

        The VAD-reported start_ms can itself lag the true onset, so we step a
        few extra chunks earlier (VAD_ONSET_MARGIN_MS). Chunks are matched by
        their stored timestamp; everything from that point to the current
        (detection) chunk is the recovered sentence head.
        """
        if not self._pre_buffer:
            return []
        margin_ms = self._ONSET_MARGIN_CHUNKS * config.BLOCK_MS
        cutoff = max(0, start_ms - margin_ms)
        sliced = [s for (t, s) in self._pre_buffer if t >= cutoff]
        # Guard: if the reported start_ms predates everything buffered (rare),
        # fall back to the whole buffer rather than returning nothing.
        return sliced if sliced else [s for (_, s) in self._pre_buffer]

    def feed(self, samples: np.ndarray, timestamp_ms: int) -> Optional[SentenceAudio]:
        """Feed a 32ms audio chunk. Returns SentenceAudio when endpoint detected."""
        self._current_ms = timestamp_ms
        segments = self._vad.process_chunk(samples)

        if self._state == VadState.SILENCE:
            self._pre_buffer.append((timestamp_ms, samples.copy()))
            if len(self._pre_buffer) > self._PRE_BUFFER_CHUNKS:
                self._pre_buffer.pop(0)

            for seg in segments:
                start_ms, end_ms = seg[0], seg[1]
                if start_ms >= 0:
                    self._state = VadState.SPEECH
                    # Recover the sentence head by slicing the rolling buffer
                    # back to the VAD-reported start_ms (with safety margin),
                    # instead of just the last few chunks.
                    onset = self._slice_onset(start_ms)
                    self._sentence_chunks = list(onset)
                    self._onset_chunks = list(onset)
                    self._sentence_start_ms = start_ms
                    self._pre_buffer = []
                    self._speech_chunk_count = len(self._sentence_chunks)

                    if end_ms >= 0:
                        return self._flush(end_ms)
            return None

        elif self._state == VadState.SPEECH:
            self._sentence_chunks.append(samples.copy())
            self._speech_chunk_count += 1

            for seg in segments:
                start_ms, end_ms = seg[0], seg[1]
                if end_ms >= 0:
                    return self._flush(end_ms)
                if start_ms >= 0 and end_ms < 0:
                    pass
            return None

        elif self._state == VadState.TRAILING_SILENCE:
            self._sentence_chunks.append(samples.copy())

            for seg in segments:
                start_ms, end_ms = seg[0], seg[1]
                if end_ms >= 0:
                    return self._flush(end_ms)
            return None

        return None

    def _flush(self, end_ms: int) -> Optional[SentenceAudio]:
        """Flush accumulated audio as a complete sentence."""
        speech_ms = self._speech_chunk_count * config.BLOCK_MS
        if speech_ms < config.VAD_MIN_SPEECH_MS:
            self._reset()
            return None

        all_samples = np.concatenate(self._sentence_chunks)
        result = SentenceAudio(
            samples=all_samples,
            start_ms=self._sentence_start_ms,
            end_ms=end_ms,
        )
        self._reset()
        return result

    def _reset(self):
        self._state = VadState.SILENCE
        self._sentence_chunks = []
        self._pre_buffer = []
        self._speech_chunk_count = 0
        self._vad.reset()
