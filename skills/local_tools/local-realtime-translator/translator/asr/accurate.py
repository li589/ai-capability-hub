"""Accurate ASR using Qwen3-ASR on Intel iGPU via OpenVINO."""

import sys
import os
import json
import string
import threading
import importlib.util
import numpy as np
from pathlib import Path
from typing import Generator, Optional

import config
from translator.messages import SentenceAudio, AsrResult
from translator.utils.text import strip_asr_prefix


def _import_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class AccurateAsr:
    """Qwen3-ASR running on iGPU for accurate per-sentence transcription."""

    def __init__(self):
        self._model = None
        self._lock = threading.Lock()
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def load(self):
        """Load Qwen3-ASR OpenVINO model."""
        model_dir = self._find_model_dir()
        if model_dir is None:
            raise FileNotFoundError("Qwen3-ASR model not found.")

        engine_dir = self._find_engine_dir()
        if engine_dir is None:
            raise FileNotFoundError("asr_engine.py not found.")

        qwen_asr_pkg = engine_dir / "Qwen3-ASR"
        utils_file = qwen_asr_pkg / "qwen_asr" / "inference" / "utils.py"
        processor_file = qwen_asr_pkg / "qwen_asr" / "core" / "transformers_backend" / "processing_qwen3_asr.py"

        if utils_file.exists():
            _import_from_file("qwen_asr_utils_standalone", utils_file)

        if processor_file.exists():
            proc_mod = _import_from_file("qwen_asr_processor_standalone", processor_file)
            import types
            fake_pkg = types.ModuleType("qwen_asr")
            fake_pkg.core = types.ModuleType("qwen_asr.core")
            fake_pkg.core.transformers_backend = types.ModuleType("qwen_asr.core.transformers_backend")
            fake_pkg.core.transformers_backend.processing_qwen3_asr = proc_mod
            fake_pkg.inference = types.ModuleType("qwen_asr.inference")

            if "qwen_asr_utils_standalone" in sys.modules:
                fake_pkg.inference.utils = sys.modules["qwen_asr_utils_standalone"]
            else:
                fake_pkg.inference.utils = types.ModuleType("qwen_asr.inference.utils")

            sys.modules.setdefault("qwen_asr", fake_pkg)
            sys.modules.setdefault("qwen_asr.core", fake_pkg.core)
            sys.modules.setdefault("qwen_asr.core.transformers_backend", fake_pkg.core.transformers_backend)
            sys.modules.setdefault("qwen_asr.core.transformers_backend.processing_qwen3_asr", proc_mod)
            sys.modules.setdefault("qwen_asr.inference", fake_pkg.inference)
            sys.modules.setdefault("qwen_asr.inference.utils", fake_pkg.inference.utils)

        if str(engine_dir) not in sys.path:
            sys.path.insert(0, str(engine_dir))

        from asr_engine import OVQwen3ASRModel
        self._model = OVQwen3ASRModel.from_pretrained(str(model_dir), device=config.QWEN_DEVICE)
        self._available = True

    def transcribe(self, sentence: SentenceAudio) -> Optional[AsrResult]:
        """Transcribe a complete sentence. Thread-safe.

        Feeds the audio to Qwen3-ASR in memory as a ``(ndarray, sample_rate)``
        tuple. The model's ``transcribe()`` accepts that form directly, so we
        avoid writing each sentence to a temporary WAV and reading it back from
        disk on every utterance — a round-trip that added latency on the final
        ASR path for no benefit (Qwen resamples/normalizes internally anyway).
        """
        if self._model is None:
            return None

        from translator.utils.audio import normalize_audio

        try:
            samples = normalize_audio(sentence.samples)

            with self._lock:
                results = self._model.transcribe(audio=(samples, config.SAMPLE_RATE))

            if results and len(results) > 0:
                item = results[0]
                if isinstance(item, dict):
                    text = item.get('text', '')
                elif hasattr(item, 'text'):
                    text = item.text
                else:
                    text = str(item)
                text = text.strip()
                if text:
                    return AsrResult(
                        text=text,
                        is_final=True,
                        start_ms=sentence.start_ms,
                        end_ms=sentence.end_ms,
                    )
        except Exception:
            pass

        return None

    def transcribe_stream(self, sentence: SentenceAudio
                          ) -> Generator[str, None, None]:
        """Transcribe a sentence with streaming partial results.

        Yields progressively cleaner partial transcriptions as tokens are
        generated, then yields the final cleaned text. Thread-safe.
        """
        if self._model is None:
            return

        from translator.utils.audio import normalize_audio

        try:
            samples = normalize_audio(sentence.samples)
        except Exception:
            return

        with self._lock:
            pipeline = self._model.pipeline
            processor = self._model.processor
            if processor is None:
                return
            max_new = self._model.max_new_tokens
            tok = processor.tokenizer

            # Build chat template input
            msgs = [
                {"role": "system", "content": ""},
                {"role": "user", "content": [
                    {"type": "audio", "audio": (samples, config.SAMPLE_RATE)}
                ]},
            ]
            try:
                from translator.utils.text_audio import to_processor_audio
                prompt = processor.apply_chat_template(
                    msgs, add_generation_prompt=True, tokenize=False
                )
                # The processor's WhisperFeatureExtractor needs BARE waveform
                # arrays, not (samples, sr) tuples. A tuple raises a numpy
                # "inhomogeneous shape" ValueError that the except below
                # swallows, silently returning empty (the Qwen3 "bad English"
                # bug — it produced nothing and the UI kept Paraformer's
                # Chinese-only transcription). See to_processor_audio.
                inp = processor(
                    text=[prompt], audio=to_processor_audio(samples),
                    return_tensors="np", padding=True,
                )
            except Exception:
                return

            # Audio encoding
            af = pipeline._process_audio(
                inp["input_features"], inp["feature_attention_mask"]
            )
            # Text embedding
            emb = pipeline._embed(inp["input_ids"])
            # Patch audio tokens with encoded features
            amask = inp["input_ids"][0] == pipeline.audio_token_id
            na, nf = int(amask.sum()), af.shape[0]
            if na != nf:
                n = min(na, nf)
                emb[0, np.where(amask)[0][:n]] = af[:n]
            else:
                emb[0, amask] = af

            attn = inp["attention_mask"]
            pos = np.where(attn == 0, 0, np.cumsum(attn, axis=-1) - 1)

            # Prefill
            pipeline.lm_req.reset_state()
            logits = pipeline._prefill(emb, attn, pos)

            # EOS token set
            eos = set()
            if tok.eos_token_id is not None:
                eos.add(tok.eos_token_id)
            for sp in ["<|im_end|>", "<|endoftext|>"]:
                tid = tok.convert_tokens_to_ids(sp)
                if tid is not None and tid != tok.unk_token_id:
                    eos.add(tid)

            gen = []
            last_yield = ""
            cur_attn = attn.copy()

            for _ in range(max_new):
                raw_tok = int(np.argmax(logits[:, -1, :], axis=-1)[0])
                if raw_tok in eos:
                    break
                gen.append(raw_tok)

                # Decode partial text
                partial = tok.decode(gen, skip_special_tokens=True)
                for sp in ["<|im_end|>", "<|endoftext|>",
                           "<|im_start|>", "</asr_text>"]:
                    partial = partial.replace(sp, "")
                # Qwen3-ASR prefixes its output with metadata
                # ("language Chinese<asr_text>real text"). Mirror the final
                # parse_asr_output() so the streaming path never leaks the
                # "language X<asr_text>" prefix into the UI.
                partial = strip_asr_prefix(partial).strip()

                if partial and partial != last_yield:
                    last_yield = partial
                    yield partial

                # Prepare next step
                ne = pipeline._embed(np.array([[raw_tok]]))
                cur_attn = np.concatenate(
                    [cur_attn, np.ones((1, 1), dtype=np.int64)], axis=1
                )
                logits = pipeline._lm(
                    ne, cur_attn,
                    np.array([[cur_attn.shape[1] - 1]], dtype=np.int64),
                )

            # Final decode with proper parsing
            if gen:
                raw = tok.decode(gen, skip_special_tokens=True)
                clean = raw
                try:
                    from qwen_asr.inference.utils import parse_asr_output
                    _, clean = parse_asr_output(
                        raw, user_language=None
                    )
                except Exception:
                    for sp in ["<|im_end|>", "<|endoftext|>",
                               "<|im_start|>", "</asr_text>"]:
                        clean = clean.replace(sp, "")
                    clean = clean.strip()

                if clean and clean != last_yield:
                    yield clean

    def _configured_asr_dir(self) -> Optional[Path]:
        """Explicit engine dir from config.QWEN_ASR_DIR / QWEN_ASR_DIR env, if set.

        Returns the path only when it actually holds asr_engine.py, so a stale or
        mistyped setting transparently falls through to the drive scan rather than
        breaking discovery.
        """
        configured = getattr(config, "QWEN_ASR_DIR", "") or ""
        if configured:
            p = Path(configured)
            if (p / "asr_engine.py").exists():
                return p
        return None

    def _find_model_dir(self) -> Optional[Path]:
        username = os.environ.get("USERNAME", "user").lower()
        model_name = "Qwen3-ASR-0.6B-fp16-ov"

        configured = self._configured_asr_dir()
        if configured:
            p = configured / "models" / model_name
            if p.exists() and (p / "config.json").exists():
                return p

        state = self._find_state()
        if state and "MODEL_DIR" in state:
            p = Path(state["MODEL_DIR"]) / model_name
            if p.exists() and (p / "config.json").exists():
                return p

        for d in string.ascii_uppercase:
            p = Path(f"{d}:\\{username}_openvino") / "asr" / "models" / model_name
            if p.exists() and (p / "config.json").exists():
                return p
        return None

    def _find_engine_dir(self) -> Optional[Path]:
        username = os.environ.get("USERNAME", "user").lower()

        configured = self._configured_asr_dir()
        if configured:
            return configured

        state = self._find_state()
        if state and "ASR_DIR" in state:
            p = Path(state["ASR_DIR"])
            if (p / "asr_engine.py").exists():
                return p

        for d in string.ascii_uppercase:
            p = Path(f"{d}:\\{username}_openvino") / "asr"
            if (p / "asr_engine.py").exists():
                return p
        return None

    def _find_state(self) -> Optional[dict]:
        configured = self._configured_asr_dir()
        if configured:
            sf_path = configured / "state.json"
            if sf_path.exists():
                return json.loads(sf_path.read_text(encoding="utf-8"))

        username = os.environ.get("USERNAME", "user").lower()
        for d in string.ascii_uppercase:
            sf_path = Path(f"{d}:\\{username}_openvino") / "asr" / "state.json"
            if sf_path.exists():
                return json.loads(sf_path.read_text(encoding="utf-8"))
        return None
