"""Download every model the realtime-translator pipeline needs.

All models are fetched with the shared ``model_download`` helper (atomic
``snapshot_download`` into a per-model directory) under
``%USERPROFILE%\\.openvino\\models\\``, declared in info.json's ``models``
array:

  * Hunyuan-1.8B-OV-int4   — translation (iGPU, OpenVINO)
  * FSMN-VAD               — endpoint detection (FunASR)
  * Paraformer online      — streaming ASR (FunASR)
  * Paraformer offline     — fallback ASR (FunASR)
  * ct-punc                — punctuation restoration (FunASR)
  * Opus-MT zh-en / en-zh  — fallback translation (MarianMT)
  * bert-base-uncased      — MeloTTS English prosody BERT
  * bert-base-multilingual-uncased — MeloTTS Chinese prosody BERT
  * MeloTTS-English / -Chinese     — TTS voices

EVERYTHING is downloaded here, in the server's background "downloading" phase,
so the --continue resume window covers the entire first-run. Every consumer
then loads straight from MODELS_ROOT (see ``config.local_model_dir``), so no
model is left to be pulled lazily during the later "loading" phase, and the
runtime never re-hits the network on a validated install.

The repos that ship the same weights in several frameworks (BERT / Opus-MT)
declare an ``allow_patterns`` allowlist in info.json so only the PyTorch +
tokenizer files are fetched, not the redundant TF / Flax / Rust / ONNX / CoreML
copies.

NLTK g2p data (averaged_perceptron_tagger + cmudict) is bundled with the skill
(src/nltk_data/), not downloaded here. Qwen3-ASR is OPTIONAL and provided by a
separate setup; the pipeline auto-falls-back to Paraformer-Offline when it is
absent, so it is not downloaded here.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Callable

# Make the bundled common model_download + the skill's config importable.
_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
for _p in (str(_HERE), str(_SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Route HuggingFace through the CN mirror BEFORE huggingface_hub is imported by
# any downstream module (melo, transformers). Likewise register the bundled NLTK
# data dir before g2p_en/melo import (g2p_en calls nltk.download at import time
# if it can't find the tagger/cmudict locally — which hangs on a blocked
# network). Both must run at import, ahead of the first melo import below.
import config  # noqa: E402
config.apply_hf_mirror()
config.ensure_bundled_nltk_data()

OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
# Single source of truth for the per-model download root (see config).
MODELS_ROOT = Path(config.MODELS_ROOT)


def _quiet() -> None:
    warnings.filterwarnings("ignore")
    import logging
    for name in ("modelscope", "funasr", "transformers"):
        logging.getLogger(name).setLevel(logging.ERROR)


def ensure_all_models(log: Callable[[str], None]) -> None:
    """Download every model declared in info.json into MODELS_ROOT.

    All models — Hunyuan-OV, the FunASR ASR/VAD/punctuation models, the Opus-MT
    fallback, the MeloTTS voices and their prosody BERTs — are fetched with the
    shared atomic ``model_download`` helper (snapshot_download into a per-model
    directory, validated against required_files, renamed into place only when
    complete). Consumers then load straight from MODELS_ROOT
    (see config.local_model_dir), so nothing is pulled lazily at load time.
    """
    from model_download import ensure_models, load_model_infos

    info_json = _SKILL_ROOT / "info.json"
    infos = load_model_infos(info_json)
    if not infos:
        log("No models declared in info.json.")
        return
    ensure_models(infos, MODELS_ROOT, logger=log)
    log("All models present in MODELS_ROOT.")



def ensure_nltk(log: Callable[[str], None]) -> None:
    """Make NLTK's g2p data available WITHOUT touching the network.

    g2p_en (pulled in by melo's English text frontend) needs two NLTK packages
    (averaged_perceptron_tagger + cmudict). NLTK's nltk.download() fetches them
    from raw.githubusercontent.com, which on a CN/corporate network is blocked
    and — fatally — has NO timeout, so nltk.download() blocks forever. That is
    exactly what hung first-run after every model had already downloaded: the
    server sat in 'downloading' indefinitely and never reached 'running'.

    We instead ship the packages with the skill (src/nltk_data/) and just make
    that dir visible to NLTK. config.ensure_bundled_nltk_data() (called at import
    time, before melo/g2p_en import) registers it on nltk.data.path. Here we only
    confirm the data is resolvable; we never hit the network."""
    try:
        import nltk
    except ImportError:
        return

    config.ensure_bundled_nltk_data()

    # What must resolve, by the actual runtime consumer:
    #   - g2p_en's import-time check looks for the LEGACY tagger name
    #     'averaged_perceptron_tagger' + 'cmudict' (g2p_en/g2p.py).
    #   - BUT nltk>=3.9 renamed the tagger: pos_tag()/PerceptronTagger() (called
    #     by g2p_en at RUNTIME) loads 'averaged_perceptron_tagger_eng' and raises
    #     LookupError for it specifically. Verified: with only the legacy zip
    #     present, g2p('hello world') crashes with
    #     "Resource 'averaged_perceptron_tagger_eng' not found".
    # So all THREE must be present; checking only the legacy name would report
    # "ready" yet let English TTS crash later. (We bundle all three.)
    required = [
        ("taggers/averaged_perceptron_tagger.zip", "averaged_perceptron_tagger"),
        ("taggers/averaged_perceptron_tagger_eng.zip", "averaged_perceptron_tagger_eng"),
        ("corpora/cmudict.zip", "cmudict"),
    ]
    missing = []
    for find_path, pkg in required:
        try:
            nltk.data.find(find_path)
        except LookupError:
            missing.append(pkg)

    if not missing:
        log("NLTK data ready (bundled, offline).")
        return

    # Fallback: the bundled data wasn't found (unexpected). Try a time-bounded
    # download rather than hang; if it fails, log and continue — English G2P will
    # degrade but the server still reaches 'running' instead of stalling.
    #
    # Cap the socket timeout ONLY for the duration of this download, then restore
    # it. setdefaulttimeout is process-global; leaving it set would silently bound
    # every socket the server later creates (a "spooky action at a distance"). We
    # touch it only on this rare fallback path — the normal bundled path above
    # returns before this and never changes the global timeout.
    import socket
    prev_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(15)
    try:
        log(f"NLTK data not bundled for {missing}; attempting bounded download...")
        for pkg in missing:
            try:
                nltk.download(pkg, quiet=True)
            except Exception as exc:  # noqa: BLE001
                log(f"NLTK download of {pkg} failed ({exc}); continuing without it.")
    finally:
        socket.setdefaulttimeout(prev_timeout)
    log("NLTK data step done.")


# Order matters only loosely; each step is independent. Hunyuan first since it's
# the largest single download and the most likely to time out a first run.
STEPS = [
    ("models", ensure_all_models),
    ("NLTK", ensure_nltk),
]


def download_all(log: Callable[[str], None] | None = None) -> None:
    """Run every download step. Raises on the first hard failure."""
    _quiet()
    emit = log or (lambda m: print(f"[download] {m}", flush=True))
    for name, fn in STEPS:
        try:
            fn(emit)
        except Exception as exc:  # noqa: BLE001
            emit(f"ERROR downloading {name}: {exc}")
            raise


if __name__ == "__main__":
    download_all()
