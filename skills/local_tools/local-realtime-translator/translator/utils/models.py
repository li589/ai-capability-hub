"""Helpers for loading FunASR/ModelScope models robustly (incl. offline)."""

import os

import config


def resolve_local_model(model_id: str) -> str:
    """Return the local MODELS_ROOT dir for ``model_id`` if it's present.

    Every model is pre-downloaded by scripts/ensure_models.py into a per-model
    directory under ``%USERPROFILE%\.openvino\models\`` (see
    config.local_model_dir). FunASR's AutoModel, given a bare model ID, contacts
    ModelScope to verify the revision even when the model is already on disk —
    which stalls for 60s+ and then fails when offline. Returning the local dir
    makes AutoModel load straight from disk and skip the network check.

    Falls back to the original ID when the local dir is absent, so a standalone
    run (outside the skill harness, before ensure_models has run) still
    downloads normally.

    A model is considered present only if its directory holds a ``model.pt``
    (the FunASR weights), guarding against half-populated folders.
    """
    local_dir = config.local_model_dir(model_id)
    if os.path.isdir(local_dir) and os.path.exists(os.path.join(local_dir, "model.pt")):
        return local_dir
    return model_id


def is_local_path(model_ref: str) -> bool:
    """True if ``model_ref`` is a filesystem path (vs a bare ModelScope ID)."""
    return os.path.isdir(model_ref)
