"""Opus-MT translation using MarianMT from Hugging Face."""

import logging
import os
import torch
from typing import Dict, Tuple

import config
from translator.translation.base import BaseTranslator

logger = logging.getLogger(__name__)


class OpusMTTranslator(BaseTranslator):
    """Opus-MT translation model."""

    def __init__(self):
        self._models: Dict[Tuple[str, str], object] = {}
        self._tokenizers: Dict[Tuple[str, str], object] = {}

    def load(self, src_lang: str = "zh", tgt_lang: str = "en"):
        """Load translation model for a specific language pair.

        Resolves the model from ModelScope (stable in CN, no HuggingFace
        dependency): ``snapshot_download`` returns a local directory which
        MarianMT then loads from disk. Falls back to loading by the bare HF id
        if ModelScope is unavailable (in which case HF_ENDPOINT, set by
        config.apply_hf_mirror(), routes the download through the CN mirror).
        """
        from transformers import MarianMTModel, MarianTokenizer

        model_key = (src_lang, tgt_lang)
        if model_key in self._models:
            return

        model_name = config.TRANSLATION_MODELS.get(model_key)
        if not model_name:
            raise ValueError(f"No model for {src_lang} -> {tgt_lang}")

        load_ref = self._resolve_model_ref(model_name)
        logger.info(f"Loading Opus-MT: {model_name} (from {load_ref})")

        tokenizer = MarianTokenizer.from_pretrained(load_ref)
        model = MarianMTModel.from_pretrained(load_ref)
        model = model.to("cpu")
        model.eval()

        self._tokenizers[model_key] = tokenizer
        self._models[model_key] = model
        logger.info(f"Opus-MT loaded: {model_key}")

    @staticmethod
    def _resolve_model_ref(model_name: str) -> str:
        """Return the local MODELS_ROOT dir for *model_name*, else resolve it.

        Prefers the per-model directory ensure_models downloaded into
        ``%USERPROFILE%\.openvino\models\`` (see config.local_model_dir), which
        MarianMT loads straight from disk. Falls back to ModelScope's
        snapshot_download (which returns the cached path on subsequent calls)
        and finally to the bare id so transformers can resolve it from its own
        cache / HF (mirror) as a last resort.
        """
        local = config.local_model_dir(model_name)
        if os.path.isdir(local):
            return local
        ms_id = config.MODELSCOPE_MIRRORS.get(model_name, model_name)
        try:
            from modelscope import snapshot_download
            return snapshot_download(ms_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ModelScope download failed for %s (%s); falling back to '%s'",
                ms_id, exc, model_name,
            )
            return model_name

    def translate(self, text: str, src_lang: str = "zh", tgt_lang: str = "en") -> str:
        """Translate text between languages."""
        if not text or not text.strip():
            return ""

        model_key = (src_lang, tgt_lang)
        if model_key not in self._models:
            self.load(src_lang, tgt_lang)

        model = self._models[model_key]
        tokenizer = self._tokenizers[model_key]

        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=512)

        translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated.strip()
