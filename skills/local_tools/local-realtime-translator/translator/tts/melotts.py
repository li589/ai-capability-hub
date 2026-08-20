"""MeloTTS wrapper for speech synthesis."""

import logging
import numpy as np
from typing import Dict

import config
from translator.tts.base import BaseTTS

logger = logging.getLogger(__name__)


class MeloTTSModel(BaseTTS):
    """MeloTTS implementation."""

    def __init__(self):
        self._models: Dict[str, object] = {}
        self._sample_rate = config.TTS_SAMPLE_RATE

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def load(self, language: str = "en"):
        """Load MeloTTS model for specific language."""
        if language in self._models:
            return

        lang_map = {"zh": "ZH", "en": "EN"}
        melo_lang = lang_map.get(language, "EN")

        # MeloTTS is the only component that pulls from HuggingFace. Route those
        # loads through ModelScope BEFORE importing melo (english.py /
        # chinese_mix.py touch HF at import). Models were pre-fetched during the
        # server's download phase, so require the cache here (download=False).
        import config
        import melo_hf_bridge

        # melo's English frontend imports g2p_en, which calls nltk.download() at
        # import time if it can't find its data locally (hangs on a blocked
        # network). Register the bundled NLTK data here too so this load path is
        # self-sufficient, not reliant on an earlier import-time side effect.
        config.ensure_bundled_nltk_data()
        melo_hf_bridge.prepare(download=False)
        cfg, ckpt = melo_hf_bridge.melotts_voice_paths(melo_lang, download=False)

        from melo.api import TTS

        logger.info(f"Loading MeloTTS for {language}...")
        model = TTS(language=melo_lang, device="cpu", config_path=cfg, ckpt_path=ckpt)
        self._models[language] = model
        logger.info(f"MeloTTS loaded for {language}")

    def synthesize(self, text: str, language: str = "en", speed: float = 1.0) -> np.ndarray:
        """Synthesize speech from text."""
        if not text or not text.strip():
            return np.array([], dtype=np.float32)

        if language not in self._models:
            self.load(language)

        model = self._models[language]
        speaker_ids = model.hps.data.spk2id
        speaker_id = list(speaker_ids.values())[0] if speaker_ids else 0

        audio = model.tts_to_file(
            text=text,
            speaker_id=speaker_id,
            speed=speed,
            quiet=True,
            output_path=None,
        )

        if not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)

        return audio
