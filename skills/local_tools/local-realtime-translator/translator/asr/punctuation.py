"""Punctuation restoration for raw ASR text (FunASR ct-punc).

Paraformer (streaming online and offline) emits unpunctuated text. On
benchmarks, the bulk of its CER gap vs Qwen3-ASR was missing punctuation, not
wrong characters. This wraps FunASR's ct-punc model so the live partial
subtitles (and the offline fallback) read like finished sentences
(commas / periods / question marks).

Design for the live hot path:
  - Background preload: preload() loads the ~290MB model on a daemon thread, so
    the capture/VAD/ASR main loop never blocks on the download or load.
  - Non-blocking restore: restore(text) returns the RAW text immediately while
    the model is still loading; once loaded, it punctuates. So partials degrade
    gracefully to unpunctuated text until the model is ready.
  - Blocking restore: restore(text, block=True) is for off-loop callers (the
    offline fallback runs on a background thread) that can afford to wait.
  - Fail-safe: any load/inference error degrades to returning the input text.
  - Toggleable via config.PUNC_ENABLED.
"""

import threading
from typing import Optional

import config
from translator.utils.models import resolve_local_model


class Punctuator:
    """Lazily/background-loaded FunASR ct-punc wrapper. Thread-safe."""

    def __init__(self):
        self._model = None
        self._load_failed = False
        self._loading = False
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def preload(self):
        """Kick off model loading on a daemon thread (idempotent, non-blocking)."""
        if not config.PUNC_ENABLED:
            return
        with self._lock:
            if self._model is not None or self._load_failed or self._loading:
                return
            self._loading = True
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        """Build the ct-punc model (runs on preload's background thread)."""
        try:
            from funasr import AutoModel
            # Prefer the local cache dir to skip FunASR's online revision check;
            # falls back to the model ID (triggers download) if not cached.
            model = AutoModel(
                model=resolve_local_model(config.PUNC_MODEL),
                disable_update=True,
                disable_log=True,
            )
            with self._lock:
                self._model = model
        except Exception:
            # Network/model unavailable: remember and never retry-spam.
            with self._lock:
                self._load_failed = True
        finally:
            with self._lock:
                self._loading = False

    def _load_sync(self):
        """Load synchronously if not already loaded/failed (blocking callers)."""
        if self._model is not None or self._load_failed:
            return
        # Reuse _load on the calling thread.
        self._load()

    def restore(self, text: str, block: bool = False) -> str:
        """Return ``text`` with punctuation; unchanged on any miss/failure.

        block=False (default, hot path): if the model isn't ready yet, start a
        background load and return the raw text NOW — never stall the caller.
        block=True (off-loop callers): load synchronously and wait.
        """
        if not config.PUNC_ENABLED:
            return text
        if not text or not text.strip():
            return text

        if self._model is None:
            if block:
                self._load_sync()
            else:
                self.preload()  # start loading; this call returns raw text
        if self._model is None:
            return text

        try:
            result = self._model.generate(input=text)
            return self._extract_text(result) or text
        except Exception:
            return text

    @staticmethod
    def _extract_text(result) -> Optional[str]:
        if isinstance(result, list) and result:
            item = result[0]
            if isinstance(item, dict):
                return item.get("text")
            if hasattr(item, "text"):
                return item.text
        return None
