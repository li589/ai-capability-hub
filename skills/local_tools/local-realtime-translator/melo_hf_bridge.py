"""Route MeloTTS' hardcoded HuggingFace loads through ModelScope.

MeloTTS is the ONLY component in the pipeline that still pulls models straight
from HuggingFace. It does so in three hardcoded, library-internal places we
don't own:

  * ``melo/text/english.py``      → ``AutoTokenizer('bert-base-uncased')``      (import time)
  * ``melo/text/english_bert.py`` → ``bert-base-uncased`` tokenizer + weights    (runtime)
  * ``melo/text/chinese_mix.py``  → ``AutoTokenizer('bert-base-multilingual-uncased')`` (import time)
  * ``melo/download_utils.py``    → ``hf_hub_download(myshell-ai/MeloTTS-*)``    (TTS() init)

Everything else in the pipeline already comes from ModelScope. On a network
that reaches ModelScope but blocks the HF mirror (hf-mirror.com — common in CN
corporate environments) those four loads are exactly what stalls first-run: the
log shows every ModelScope download succeeding and then a
``We couldn't connect to 'https://hf-mirror.com'`` at MeloTTS' import.

This module fixes that WITHOUT editing the (reinstall-overwritten) melo source:

  1. ``prepare()`` pre-fetches the two BERT repos from ModelScope and installs a
     transformers ``from_pretrained`` shim that rewrites melo's bare HF ids
     (``bert-base-uncased`` / ``bert-base-multilingual-uncased``) to the local
     ModelScope snapshot dirs. It also flips on HuggingFace offline mode, which
     is REQUIRED: transformers 4.57.x makes its own ``model_info()`` network
     probe (an ``is_base_mistral`` check) during tokenizer init even when handed
     a local dir, and offline mode is what short-circuits it.

  2. ``melotts_voice_paths(lang)`` resolves the MeloTTS voice ``config.json`` and
     ``checkpoint.pth`` from ModelScope so callers can pass them to
     ``melo.api.TTS(config_path=..., ckpt_path=...)``, bypassing the HF download
     in melo's download_utils entirely.

``prepare()`` MUST be called before ``import melo.api`` (english.py /
chinese_mix.py touch HF at import). It is idempotent and cheap on repeat calls
(cached snapshots resolve offline in ~0ms).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional, Tuple

import config

# melo's bare HuggingFace ids -> their ModelScope mirror ids. Kept here (not just
# read from config) so the set of ids the shim rewrites is explicit and local.
_BERT_HF_TO_MS = {
    "bert-base-uncased": config.MODELSCOPE_MIRRORS["bert-base-uncased"],
    "bert-base-multilingual-uncased": config.MODELSCOPE_MIRRORS[
        "bert-base-multilingual-uncased"
    ],
}

_prepared = False
_id_to_local_dir: dict[str, str] = {}


def _noop(_msg: str) -> None:
    pass


def _resolve_ms_dir(ms_id: str, download: bool, log: Callable[[str], None]) -> str:
    """Return the local snapshot dir for a ModelScope id.

    Prefers the per-model directory ensure_models downloaded into MODELS_ROOT
    (see config.local_model_dir); otherwise tries the ModelScope cache first
    (offline, instant) and only hits the network when the snapshot is missing
    AND ``download`` is allowed. Raises the real ModelScope error otherwise —
    never silently degrades."""
    local = config.local_model_dir(ms_id)
    if os.path.isdir(local):
        return local

    from modelscope import snapshot_download

    try:
        return snapshot_download(ms_id, local_files_only=True)
    except Exception:
        if not download:
            raise
        log(f"Fetching {ms_id} from ModelScope...")
        return snapshot_download(ms_id)


def _install_transformers_shim(log: Callable[[str], None]) -> None:
    """Wrap AutoTokenizer / AutoModelForMaskedLM .from_pretrained so melo's bare
    BERT ids resolve to the local ModelScope dirs. Idempotent (marks the wrapped
    function so a second call is a no-op)."""
    import transformers

    for cls_name in ("AutoTokenizer", "AutoModelForMaskedLM"):
        cls = getattr(transformers, cls_name)
        orig = cls.from_pretrained
        if getattr(orig, "_melo_bridge_wrapped", False):
            continue

        def _make(orig_fn):
            def _wrapped(pretrained_model_name_or_path, *args, **kwargs):
                local = _id_to_local_dir.get(str(pretrained_model_name_or_path))
                if local is not None:
                    pretrained_model_name_or_path = local
                return orig_fn(pretrained_model_name_or_path, *args, **kwargs)

            _wrapped._melo_bridge_wrapped = True
            return _wrapped

        cls.from_pretrained = staticmethod(_make(orig))
    log("transformers from_pretrained shim installed.")


def prepare(download: bool = True, log: Optional[Callable[[str], None]] = None) -> None:
    """Make MeloTTS' HuggingFace loads resolve from ModelScope.

    Call BEFORE importing melo. ``download=True`` fetches missing snapshots
    (the server's download phase); ``download=False`` requires them cached and
    raises if not (fast runtime path)."""
    global _prepared
    emit = log or _noop
    if _prepared:
        return

    for hf_id, ms_id in _BERT_HF_TO_MS.items():
        _id_to_local_dir[hf_id] = _resolve_ms_dir(ms_id, download, emit)

    _install_transformers_shim(emit)
    _force_hf_offline(emit)

    _prepared = True
    emit("MeloTTS HF->ModelScope bridge ready.")


def _force_hf_offline(log: Callable[[str], None]) -> None:
    """Force huggingface_hub / transformers into offline mode, hard.

    Setting only the env vars is NOT enough: by the time the bridge runs, the
    server's download phase has already imported huggingface_hub, which read
    HF_HUB_OFFLINE ONCE at import and baked it into a module constant. We set the
    env vars (for any not-yet-imported consumer) AND overwrite the already-baked
    constants so every consumer sees offline = True.

    This matters beyond the BERT loads we remap: melo's patched cleaner.py does
    ``try: import french/spanish/korean``, and those modules run
    ``AutoTokenizer.from_pretrained('dbmdz/bert-base-french-europeana-cased')``
    (etc.) at IMPORT time. We never use those languages, but without offline mode
    each one hits the (blocked) HF mirror and either burns ~40s on retries or —
    on a machine with no cache — raises OSError, which cleaner's ``except
    ImportError`` does NOT catch, crashing ``import melo.api`` outright. Offline
    mode makes those lookups fail fast with a cache-miss that cleaner tolerates."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    try:
        import huggingface_hub.constants as _hc
        _hc.HF_HUB_OFFLINE = True
    except Exception:
        pass
    try:
        import huggingface_hub as _h
        _h.constants.HF_HUB_OFFLINE = True
    except Exception:
        pass
    try:
        import transformers.utils.hub as _th
        _th._is_offline_mode = True
    except Exception:
        pass
    log("HuggingFace offline mode forced.")


def melotts_voice_paths(
    lang: str, download: bool = True, log: Optional[Callable[[str], None]] = None
) -> Tuple[str, str]:
    """Resolve (config_path, checkpoint_path) for a MeloTTS voice from ModelScope.

    ``lang`` is a melo language code (``EN`` / ``ZH``). Pass the returned paths to
    ``melo.api.TTS(config_path=..., ckpt_path=...)`` to skip its HF download."""
    emit = log or _noop
    hf_repo = config.MELOTTS_HF_REPOS.get(lang.upper())
    if hf_repo is None:
        raise KeyError(f"no MeloTTS repo mapped for language {lang!r}")
    ms_id = config.MODELSCOPE_MIRRORS.get(hf_repo, hf_repo)
    voice_dir = Path(_resolve_ms_dir(ms_id, download, emit))
    cfg = voice_dir / "config.json"
    ckpt = voice_dir / "checkpoint.pth"
    if not cfg.exists() or not ckpt.exists():
        raise FileNotFoundError(
            f"MeloTTS voice files missing in {voice_dir} "
            f"(config.json={cfg.exists()}, checkpoint.pth={ckpt.exists()})"
        )
    return str(cfg), str(ckpt)
