"""Streaming ASR using Paraformer Online + Offline fallback."""

import numpy as np
import threading
from typing import Optional

import config
from translator.messages import AsrResult, SentenceAudio


class StreamingAsr:
    """Paraformer Online for streaming partial + Offline as fallback for final."""

    def __init__(self):
        self._online_model = None
        self._offline_model = None
        self._cache = {}
        self._chunk_buffer = np.array([], dtype=np.float32)
        self._accumulated_text = ""
        self._sentence_start_ms = 0
        self._lock = threading.Lock()
        # Sentence-head display fix. The streaming cache drops/holds back the
        # first sentence's head (the cold first chunk emits empty or only the
        # first character, with char 2 held until the next chunk). We recover a
        # clean head by decoding the FIRST chunk once on a throwaway cache with
        # is_final=True (after trimming its leading silence) and showing that
        # while the real streaming string catches up. The real cache path is
        # left completely untouched, so mid-sentence accuracy is unchanged.
        self._head_flush = ""
        self._first_chunk_pending = True
        # Whether the offline Paraformer fallback may be loaded at all. When
        # Qwen3-ASR is available it produces the final transcription, so the
        # offline model is pure dead weight (~1.4GB resident). The pipeline
        # calls disable_offline() in that case so it is never loaded. Default
        # True so standalone use (no Qwen3) still falls back correctly.
        self._offline_enabled = True
        # Punctuation restorer for the offline fallback's raw output. Lazily
        # loaded on first use; see translator/asr/punctuation.py.
        from translator.asr.punctuation import Punctuator
        self._punctuator = Punctuator()

    def disable_offline(self):
        """Permanently disable the offline Paraformer fallback.

        Called by the pipeline when Qwen3-ASR is available, so the redundant
        ~1.4GB offline model is never lazily loaded. Safe to call before or
        after load(); if an offline model was somehow already loaded it is
        dropped to free its memory.
        """
        with self._lock:
            self._offline_enabled = False
            self._offline_model = None

    def load(self):
        """Load the streaming (online) Paraformer model.

        Only the online model — needed for live partials — is loaded eagerly.
        The offline model is a fallback used solely when Qwen3-ASR is
        unavailable, so it is loaded lazily on first use (see
        ``finalize_offline``). On machines where Qwen3-ASR is present (the
        common case) this avoids holding a second ~1GB Paraformer in memory and
        shortens startup.
        """
        import warnings
        import logging
        warnings.filterwarnings('ignore')
        logging.getLogger('modelscope').setLevel(logging.ERROR)
        logging.getLogger('funasr').setLevel(logging.ERROR)

        from funasr import AutoModel
        from translator.utils.models import resolve_local_model, is_local_path

        # Prefer the local cache dir so startup doesn't stall on ModelScope's
        # revision check (and works offline once the model is cached). Only
        # pass model_revision when loading by ID — a local path has none.
        online_ref = resolve_local_model(config.PARAFORMER_ONLINE_MODEL)
        online_kw = dict(model=online_ref, disable_update=True, disable_log=True)
        if not is_local_path(online_ref):
            online_kw["model_revision"] = "v2.0.4"
        self._online_model = AutoModel(**online_kw)

        # Warm the punctuation model on a background thread so live partials get
        # punctuated as soon as possible, without blocking startup or the
        # capture loop. Until it's ready, partials show as raw text.
        self._punctuator.preload()

    def _ensure_offline(self):
        """Lazily load the offline Paraformer model on first fallback use."""
        if not self._offline_enabled:
            return
        if self._offline_model is not None:
            return
        with self._lock:
            if not self._offline_enabled:
                return
            if self._offline_model is not None:
                return
            from funasr import AutoModel
            from translator.utils.models import resolve_local_model
            from translator.utils import memdiag
            memdiag.stamp("LAZY-LOADING Paraformer-Offline (Qwen3 fallback path hit)")
            self._offline_model = AutoModel(
                model=resolve_local_model(config.PARAFORMER_OFFLINE_MODEL),
                disable_update=True,
                disable_log=True,
            )
            memdiag.stamp("after Paraformer-Offline lazy load")

    def start_sentence(self, timestamp_ms: int):
        """Signal the start of a new sentence."""
        with self._lock:
            self._cache = {}
            self._chunk_buffer = np.array([], dtype=np.float32)
            self._accumulated_text = ""
            self._sentence_start_ms = timestamp_ms
            self._head_flush = ""
            self._first_chunk_pending = True

    def feed(self, samples: np.ndarray, timestamp_ms: int) -> Optional[AsrResult]:
        """Feed audio for streaming partial output."""
        with self._lock:
            self._chunk_buffer = np.concatenate([self._chunk_buffer, samples])

            if len(self._chunk_buffer) < config.PARAFORMER_CHUNK_SIZE:
                return None

            chunk = self._chunk_buffer[:config.PARAFORMER_CHUNK_SIZE]
            self._chunk_buffer = self._chunk_buffer[config.PARAFORMER_CHUNK_SIZE:]
            first_chunk = self._first_chunk_pending
            self._first_chunk_pending = False

        # On the very first chunk of the sentence, recover a clean head with a
        # display-only flush: decode the leading-silence-trimmed chunk once on a
        # throwaway cache with is_final=True. This pulls the head char(s) the
        # cold streaming chunk drops or holds back. The real streaming cache
        # (self._cache) below is fed the RAW chunk exactly as before, so its
        # state — and thus mid-sentence accuracy — is unchanged.
        if first_chunk:
            self._head_flush = self._compute_head_flush(chunk)

        result = self._online_model.generate(
            input=chunk,
            cache=self._cache,
            is_final=False,
            chunk_size=config.PARAFORMER_CHUNK_LOOK,
            encoder_chunk_look_back=config.PARAFORMER_ENCODER_LOOK_BACK,
            decoder_chunk_look_back=config.PARAFORMER_DECODER_LOOK_BACK,
        )

        text = self._extract_text(result)
        if text:
            self._accumulated_text += text
        # Choose what to display: while the real streaming string is still
        # shorter than the head-flush (the early head window), show the flush;
        # once it catches up, the real string takes over so the final display
        # equals the real string (no regression, no head duplication). Note we
        # return even when the cold first chunk produced no text, so the flush
        # head still appears immediately.
        from translator.utils.text_audio import head_flush_display
        shown = head_flush_display(self._head_flush, self._accumulated_text)
        if shown:
            # Punctuate the live partial. Non-blocking: until the ct-punc model
            # finishes loading this returns the raw text, so the hot path is
            # never stalled by the model download/load.
            display = self._punctuator.restore(shown)
            return AsrResult(
                text=display,
                is_final=False,
                start_ms=self._sentence_start_ms,
                end_ms=timestamp_ms,
            )
        return None

    def _compute_head_flush(self, chunk: np.ndarray) -> str:
        """Display-only head recovery for the first chunk of a sentence.

        Decodes the leading-silence-trimmed first chunk once on a fresh,
        throwaway cache with is_final=True, returning its text. Uses the online
        model only (no offline model) and never touches self._cache. Any failure
        degrades to an empty string so the normal streaming display is used.
        """
        try:
            from translator.utils.text_audio import trim_leading_silence
            trimmed = trim_leading_silence(chunk, sample_rate=config.SAMPLE_RATE)
            if trimmed is None or len(trimmed) == 0:
                return ""
            result = self._online_model.generate(
                input=trimmed,
                cache={},
                is_final=True,
                chunk_size=config.PARAFORMER_CHUNK_LOOK,
                encoder_chunk_look_back=config.PARAFORMER_ENCODER_LOOK_BACK,
                decoder_chunk_look_back=config.PARAFORMER_DECODER_LOOK_BACK,
            )
            return (self._extract_text(result) or "").strip()
        except Exception:
            return ""

    def end_sentence(self, timestamp_ms: int) -> Optional[AsrResult]:
        """End streaming session. Returns accumulated partial text.

        Flushes any residual audio (shorter than one streaming chunk) through
        the online model with is_final=True so the tail of the sentence is not
        dropped. Without this, up to PARAFORMER_CHUNK_MS of trailing audio per
        sentence would never be transcribed.
        """
        with self._lock:
            residual = self._chunk_buffer
            self._chunk_buffer = np.array([], dtype=np.float32)

        if len(residual) > 0:
            result = self._online_model.generate(
                input=residual,
                cache=self._cache,
                is_final=True,
                chunk_size=config.PARAFORMER_CHUNK_LOOK,
                encoder_chunk_look_back=config.PARAFORMER_ENCODER_LOOK_BACK,
                decoder_chunk_look_back=config.PARAFORMER_DECODER_LOOK_BACK,
            )
            tail_text = self._extract_text(result)
            if tail_text:
                self._accumulated_text += tail_text

        self._cache = {}
        final_text = self._accumulated_text
        self._accumulated_text = ""
        if final_text:
            # Final partial of the sentence: punctuate (non-blocking) for a
            # clean last update before the accurate-ASR result replaces it.
            final_text = self._punctuator.restore(final_text)
            return AsrResult(
                text=final_text,
                is_final=False,
                start_ms=self._sentence_start_ms,
                end_ms=timestamp_ms,
            )
        return None

    def finalize_offline(self, sentence: SentenceAudio) -> Optional[AsrResult]:
        """Run Paraformer Offline on complete sentence. Used as Qwen3 fallback."""
        from translator.utils.audio import normalize_audio
        self._ensure_offline()
        if self._offline_model is None:
            # Offline disabled (Qwen3 path active) or load failed: no fallback.
            return None
        samples = normalize_audio(sentence.samples)
        result = self._offline_model.generate(input=samples)
        text = self._extract_text(result)
        if text:
            # Paraformer returns unpunctuated text; restore punctuation so the
            # fallback reads like a finished sentence (Qwen3 already does this).
            # block=True: this runs on Thread 2 (off the capture loop), so it
            # can afford to wait for the ct-punc model to finish loading.
            text = self._punctuator.restore(text, block=True)
            return AsrResult(
                text=text,
                is_final=True,
                start_ms=sentence.start_ms,
                end_ms=sentence.end_ms,
            )
        return None

    def _extract_text(self, result) -> str:
        if not result:
            return ""
        if isinstance(result, list) and len(result) > 0:
            item = result[0]
            if isinstance(item, dict):
                return item.get("text", "")
            if hasattr(item, 'text'):
                return item.text
        return ""
