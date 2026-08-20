"""Hunyuan-1.8B-Instruct translation on Intel iGPU via OpenVINO.

Uses the OpenVINO INT4 quantized model from ModelScope:
    snake7gun/Hunyuan-1.8B-Instruct-ov-int4

Loaded via optimum.intel.OVModelForCausalLM and runs on the iGPU (Intel
integrated GPU) through OpenVINO runtime. Falls back gracefully when the
model is unavailable, leaving the caller to try Opus-MT or another fallback.
"""

import logging
import queue
import threading
import re
from pathlib import Path
from typing import Generator, List, Optional

import config
from translator.translation.base import BaseTranslator

logger = logging.getLogger(__name__)

# Default generation parameters.
# Greedy decoding (do_sample=False) is significantly faster than sampling and
# produces equally good results for straightforward translation. Sampling
# parameters (top_k, top_p, temperature) are omitted since they only apply
# when do_sample=True.
_GEN_KWARGS = {
    "do_sample": False,
    "repetition_penalty": 1.05,
    "max_new_tokens": 128,
}

# Language names used in the translation prompt.
_LANG_NAMES = {
    "zh": "Chinese",
    "en": "English",
}


def _extract_answer(text: str) -> str:
    """Extract the content from <answer>...</answer> tags if present.

    Hunyuan uses thinking mode by default and wraps its final response in
    <answer> tags. When thinking is disabled it may still emit them, so
    we strip any <think>/<answer> blocks to get the clean translation.

    Streaming-aware: if only the opening ``<answer>`` tag is present (the
    closing tag hasn't been generated yet), the content after it is returned
    so the UI can show progressive text without visible markup.
    """
    # Try to extract complete <answer>...</answer> block first.
    m = re.search(r"<answer>\s*(.*?)\s*</answer>", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Streaming: opening <answer> tag present but not yet closed.
    m = re.search(r"<answer>\s*(.*)", text, re.DOTALL)
    if m:
        inner = m.group(1).strip()
        if inner:
            return inner

    # Remove any remaining <think> blocks, <answer> tags, and special tokens
    # that weren't cleaned above.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"</?answer>", "", text)
    text = re.sub(r"<\|?hy?_?\w*\|?>", "", text)
    result = text.strip()
    # If only markup remained (empty after stripping tags), return empty.
    return result if result else ""


def _clean_partial(full_raw: str) -> str:
    """Best-effort clean text for an in-progress (streaming) generation.

    Prefers the <answer> content via _extract_answer; if no answer markup is
    present yet, falls back to the raw accumulated text with any stray tags
    stripped. Returns "" when nothing displayable is available yet.
    """
    visible = _extract_answer(full_raw)
    if visible:
        return visible
    raw = full_raw.strip()
    if not raw:
        return ""
    clean = re.sub(r"</?answer>", "", raw)
    clean = re.sub(r"<\|?hy?_?\w*\|?>", "", clean)
    return clean.strip()


class HunyuanOVTranslator(BaseTranslator):
    """Hunyuan-1.8B-Instruct on iGPU for zh↔en translation.

    Thread-safe: a per-instance lock serialises generate() calls.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._lock = threading.Lock()
        self._available = False

    # ── public properties ────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self._available

    # ── prompt construction ──────────────────────────────────────────

    @staticmethod
    def _build_messages(text: str, src_lang: str, tgt_lang: str) -> List[dict]:
        """Build the chat messages for a translation request.

        Shared by translate() and translate_stream() so the prompt never
        drifts between the blocking and streaming paths.
        """
        src_name = _LANG_NAMES.get(src_lang, src_lang)
        tgt_name = _LANG_NAMES.get(tgt_lang, tgt_lang)
        return [
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate the user's text "
                    f"from {src_name} to {tgt_name}. Output ONLY the translated text, "
                    "nothing else — no explanations, no notes, no tags."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ]

    # ── load ─────────────────────────────────────────────────────────

    def load(self, src_lang: str = "zh", tgt_lang: str = "en"):
        """Download (if needed) and load the Hunyuan OV model on iGPU."""
        if self._available:
            return

        model_dir = self._resolve_model_dir()
        logger.info("Loading Hunyuan-OV from %s", model_dir)

        from optimum.intel import OVModelForCausalLM
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        model = OVModelForCausalLM.from_pretrained(
            str(model_dir),
            device=config.HUNYUAN_DEVICE,
            ov_config={
                "PERFORMANCE_HINT": "LATENCY",
                # NOTE: INFERENCE_PRECISION_HINT deliberately omitted so that
                # OpenVINO selects the optimal compute precision automatically.
                # For this INT4-quantized model, forcing f32 would dequantize
                # weights to f32, quadrupling memory bandwidth demand and
                # crippling iGPU throughput.
            },
        )

        self._tokenizer = tokenizer
        self._model = model
        self._available = True
        logger.info(
            "Hunyuan-OV loaded on %s (%s)",
            config.HUNYUAN_DEVICE,
            model_dir,
        )

    # ── translate (blocking) ─────────────────────────────────────────

    def translate(self, text: str, src_lang: str = "zh", tgt_lang: str = "en") -> str:
        """Translate *text* with Hunyuan via chat-template prompt.

        Returns the translated string, or an empty string on failure (the
        caller should fall back to Opus-MT).
        """
        if not text or not text.strip():
            return ""
        if not self._available:
            logger.warning("Hunyuan not available, returning empty")
            return ""

        messages = self._build_messages(text, src_lang, tgt_lang)

        try:
            # Apply the model's chat template (fast mode, no thinking).
            tokenized = self._tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                enable_thinking=False,  # fast translation mode
            )

            with self._lock:
                outputs = self._model.generate(tokenized, **_GEN_KWARGS)

            # Decode only the newly generated tokens (skip the prompt).
            prompt_len = tokenized.shape[-1]
            new_tokens = outputs[0, prompt_len:]
            decoded = self._tokenizer.decode(new_tokens, skip_special_tokens=True)

            result = _extract_answer(decoded)
            return result.strip()

        except Exception as e:
            logger.error("Hunyuan translation failed: %s", e)
            return ""

    # ── translate_stream ─────────────────────────────────────────────

    def translate_stream(self, text: str, src_lang: str = "zh", tgt_lang: str = "en"
                         ) -> Generator[str, None, None]:
        """Translate *text* with Hunyuan, yielding partial results as tokens
        are generated.

        Uses HuggingFace's ``TextIteratorStreamer`` on top of OpenVINO's
        ``generate()`` so that each decoded token fragment is yielded as it
        becomes available. The **last** yielded value is the authoritative,
        fully-cleaned translation.

        On any failure the generator yields nothing (the caller should fall
        back to Opus-MT).
        """
        if not text or not text.strip():
            return
        if not self._available:
            logger.warning("Hunyuan not available for streaming")
            return

        messages = self._build_messages(text, src_lang, tgt_lang)

        try:
            from transformers import TextIteratorStreamer

            tokenized = self._tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                enable_thinking=False,
            )

            # timeout bounds every text_queue.get() inside the streamer. The
            # streamer's stop signal is only emitted when generate() finishes
            # NORMALLY (in end()); if the background generate() raises or the
            # iGPU wedges, that signal never comes. Without a timeout the
            # `for ... in streamer` loop would block forever. On timeout the
            # queue raises queue.Empty, which we catch below and fall back.
            streamer = TextIteratorStreamer(
                self._tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
                timeout=config.HUNYUAN_STREAM_TIMEOUT_S,
            )

            gen_kwargs = {**_GEN_KWARGS, "streamer": streamer}

            full_raw = ""
            last_yielded = ""
            # Generation runs in a background thread; we hold the lock for the
            # WHOLE span (start → drain → join) so the OpenVINO model — whose
            # KV-cache is internal, stateful, and NOT safe to touch from two
            # threads — is never entered concurrently. The finally guarantees
            # the thread is joined before the lock is released.
            with self._lock:
                thread = threading.Thread(
                    target=self._model.generate,
                    kwargs=dict(input_ids=tokenized, **gen_kwargs),
                    daemon=True,
                )
                thread.start()
                try:
                    for new_text in streamer:
                        if not new_text:
                            continue
                        full_raw += new_text
                        visible = _clean_partial(full_raw)
                        if visible and visible != last_yielded:
                            yield visible
                            last_yielded = visible

                    # Final yield: fully cleaned authoritative result (the last
                    # streamed token may have been incomplete markup).
                    final = _extract_answer(full_raw) or full_raw.strip()
                    if final and final != last_yielded:
                        yield final
                finally:
                    # Always reclaim the worker before releasing the lock, so a
                    # still-running generate() can never overlap the next call.
                    thread.join(timeout=config.HUNYUAN_STREAM_TIMEOUT_S)
                    if thread.is_alive():
                        # generate() is genuinely wedged (iGPU/driver hang, not
                        # merely slow): the OV model is now in an unknown state
                        # and unsafe to reuse. Self-heal by permanently
                        # disabling Hunyuan so every future sentence cleanly
                        # falls back to Opus-MT instead of overlapping a hung
                        # request on a shared stateful model.
                        logger.error(
                            "Hunyuan generate() did not terminate within %.0fs; "
                            "disabling Hunyuan and falling back to Opus-MT.",
                            config.HUNYUAN_STREAM_TIMEOUT_S,
                        )
                        self._available = False

        except queue.Empty:
            # Streamer timed out waiting for the next token — generate() likely
            # raised in the worker (its exception cannot surface here) or hung.
            logger.error(
                "Hunyuan streaming stalled (>%.0fs with no new token); "
                "falling back to Opus-MT.",
                config.HUNYUAN_STREAM_TIMEOUT_S,
            )
            return
        except Exception as e:
            logger.error("Hunyuan streaming failed: %s", e)
            return

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _resolve_model_dir() -> Path:
        """Return the local path to the Hunyuan OV model.

        In the skill packaging the model is pre-downloaded (atomically, with
        file validation) by ``scripts\\ensure_models.py`` into the shared
        ``%USERPROFILE%\\.openvino\\models\\`` tree, which is where the
        server's "downloading" phase places every model. Prefer that location
        so the runtime never re-hits the network on a validated install.

        Falls back to ModelScope's ``snapshot_download`` (which downloads on
        first call and returns the cached path afterwards) when the
        pre-downloaded copy is absent — e.g. when running the package directly
        outside the skill harness.
        """
        local_dir = Path(config.local_model_dir(config.HUNYUAN_MODEL_ID))
        if (local_dir / "openvino_model.xml").is_file():
            return local_dir

        from modelscope import snapshot_download

        path = snapshot_download(
            config.HUNYUAN_MODEL_ID,
            cache_dir=str(Path.home() / ".cache" / "modelscope" / "hub"),
        )
        return Path(path)
