"""Minimal example for reusing model_download_template.py from another program.

This example stays fully local by using a fake ``snapshot_download`` function.
In a real program, replace ``fake_snapshot_download`` with
``modelscope.snapshot_download`` or another downloader with the same calling
shape.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "scripts" / "model_download_template.py"
MODULE_SPEC = importlib.util.spec_from_file_location("model_download_template", MODULE_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError(f"failed to load model_download_template from {MODULE_PATH}")
model_download_template = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules.setdefault("model_download_template", model_download_template)
MODULE_SPEC.loader.exec_module(model_download_template)

ModelDownloadTemplate = model_download_template.ModelDownloadTemplate
download_required_model = model_download_template.download_required_model
validate_model_dir = model_download_template.validate_model_dir


REQUIRED_FILES = (
    "config.json",
    "weights.bin",
)


def fake_snapshot_download(model_id: str, local_dir: str) -> None:
    target_dir = Path(local_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "config.json").write_text(
        '{"model_id": "%s"}' % model_id,
        encoding="utf-8",
    )
    (target_dir / "weights.bin").write_bytes(b"demo-weights")


def main() -> int:
    with TemporaryDirectory(prefix="model-download-example-") as temp_dir:
        models_root = Path(temp_dir) / "models"
        local_dir = models_root / "demo-model"
        template = ModelDownloadTemplate(
            models_root=models_root,
            required_files=REQUIRED_FILES,
        )
        logs: list[str] = []

        download_required_model(
            model_id="demo/model",
            local_dir=local_dir,
            snapshot_download=fake_snapshot_download,
            template=template,
            logger=logs.append,
        )

        validation = validate_model_dir(local_dir, REQUIRED_FILES)
        if not validation.ok:
            raise RuntimeError(f"unexpected validation failure: {validation.reason}")

        print("download logs:")
        for message in logs:
            print(f"- {message}")
        print(f"installed model dir: {local_dir}")
        print(f"installed files: {[path.name for path in sorted(local_dir.iterdir())]}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())