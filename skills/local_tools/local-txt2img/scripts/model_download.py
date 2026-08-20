"""Shared helpers for atomically downloading and validating local models.

Provides:
- ModelDownloadTemplate / download_required_model (backward-compatible)
- ModelInfo / load_skill_info / load_model_infos / ensure_models (new API)
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, NamedTuple, Sequence


class ModelValidation(NamedTuple):
    ok: bool
    reason: str = ""


@dataclass(frozen=True)
class ModelDownloadTemplate:
    models_root: Path
    required_files: tuple[str, ...]
    snapshot_target_kwarg: str = "local_dir"
    snapshot_kwargs: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "models_root", Path(self.models_root))
        object.__setattr__(self, "required_files", tuple(self.required_files))


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    dir_name: str
    required_files: tuple[str, ...]


def validate_model_dir(local_dir: Path, required_files: Sequence[str]) -> ModelValidation:
    if not local_dir.is_dir():
        return ModelValidation(ok=False, reason="directory missing")

    missing_files = [
        relative_path
        for relative_path in required_files
        if not (local_dir / relative_path).is_file()
    ]
    if missing_files:
        return ModelValidation(
            ok=False,
            reason=f"missing files: {', '.join(missing_files)}",
        )
    return ModelValidation(ok=True)


def _assert_under_models_root(path: Path, models_root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = models_root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise RuntimeError(
            f"refusing to touch path outside models root: {resolved}"
        ) from exc
    return resolved


def _remove_tree_safely(path: Path, models_root: Path) -> None:
    resolved = _assert_under_models_root(path, models_root)
    if resolved.exists():
        shutil.rmtree(resolved)


def _backup_invalid_model_dir(local_dir: Path, models_root: Path) -> Path:
    _assert_under_models_root(local_dir, models_root)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = f"{stamp}-{os.getpid()}"
    backup_dir = local_dir.with_name(f"{local_dir.name}.invalid-{suffix}")
    while backup_dir.exists():
        suffix = f"{suffix}-1"
        backup_dir = local_dir.with_name(f"{local_dir.name}.invalid-{suffix}")
    _assert_under_models_root(backup_dir, models_root)
    os.replace(local_dir, backup_dir)
    return backup_dir


def _emit(logger: Callable[[str], None] | None, message: str) -> None:
    if logger is not None:
        logger(message)


def download_required_model(
    model_id: str,
    local_dir: Path,
    snapshot_download,
    template: ModelDownloadTemplate,
    logger: Callable[[str], None] | None = None,
) -> None:
    partial_dir = local_dir.with_name(f"{local_dir.name}.partial")
    _remove_tree_safely(partial_dir, template.models_root)

    _emit(logger, f"downloading model {model_id} -> {partial_dir}")
    snapshot_kwargs = dict(template.snapshot_kwargs or {})
    snapshot_kwargs[template.snapshot_target_kwarg] = str(partial_dir)
    snapshot_download(model_id, **snapshot_kwargs)

    partial_validation = validate_model_dir(partial_dir, template.required_files)
    if not partial_validation.ok:
        raise RuntimeError(
            f"downloaded model {model_id} failed validation: {partial_validation.reason}"
        )

    current_validation = validate_model_dir(local_dir, template.required_files)
    if local_dir.exists() and not current_validation.ok:
        backup_dir = _backup_invalid_model_dir(local_dir, template.models_root)
        _emit(logger, f"backed up invalid model dir {local_dir} -> {backup_dir}")
    elif current_validation.ok:
        _remove_tree_safely(partial_dir, template.models_root)
        return

    try:
        os.replace(partial_dir, local_dir)
    except OSError as exc:
        raise RuntimeError(f"failed to install downloaded model {model_id}: {exc}") from exc

    _emit(logger, f"installed downloaded model {model_id} -> {local_dir}")


def load_skill_info(info_json_path: Path) -> dict:
    """Load the full info.json as a dict."""
    return json.loads(info_json_path.read_text(encoding="utf-8"))


def load_model_infos(info_json_path: Path) -> list[ModelInfo]:
    """Parse the 'models' array from info.json into ModelInfo objects."""
    data = load_skill_info(info_json_path)
    models_raw = data.get("models", [])
    return [
        ModelInfo(
            model_id=m["model_id"],
            dir_name=m["dir_name"],
            required_files=tuple(m["required_files"]),
        )
        for m in models_raw
    ]


def ensure_models(
    models: list[ModelInfo],
    models_root: Path,
    logger: Callable[[str], None] | None = None,
) -> None:
    """Validate and download all models that aren't already present."""
    missing = [
        m for m in models
        if not validate_model_dir(models_root / m.dir_name, m.required_files).ok
    ]
    if not missing:
        return

    try:
        from modelscope import snapshot_download
    except ImportError as exc:
        raise RuntimeError(
            "modelscope is required to download models. "
            "Please run 'scripts\\install-env.ps1' first."
        ) from exc

    models_root.mkdir(parents=True, exist_ok=True)

    for m in missing:
        local_dir = models_root / m.dir_name
        validation = validate_model_dir(local_dir, m.required_files)
        if validation.reason and validation.reason != "directory missing":
            _emit(logger, f"model {m.model_id} is incomplete: {validation.reason}; re-downloading")

        template = ModelDownloadTemplate(
            models_root=models_root,
            required_files=m.required_files,
        )
        download_required_model(
            model_id=m.model_id,
            local_dir=local_dir,
            snapshot_download=snapshot_download,
            template=template,
            logger=logger,
        )

    failed = [
        f"{m.model_id} ({validate_model_dir(models_root / m.dir_name, m.required_files).reason})"
        for m in missing
        if not validate_model_dir(models_root / m.dir_name, m.required_files).ok
    ]
    if failed:
        raise RuntimeError(f"model download did not complete: {', '.join(failed)}")


__all__ = [
    "ModelDownloadTemplate",
    "ModelInfo",
    "ModelValidation",
    "download_required_model",
    "ensure_models",
    "load_model_infos",
    "load_skill_info",
    "validate_model_dir",
]
