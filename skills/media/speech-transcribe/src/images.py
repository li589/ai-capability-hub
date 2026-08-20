"""
Modal image and infrastructure definitions - imported as: import src.images as images
"""

from pathlib import Path

import modal

import src.config as config


# ============================================================
# Volumes (shared by all pipelines — slug provides isolation)
# ============================================================
volume_data = modal.Volume.from_name(config.VOLUME_DATA_NAME, create_if_missing=True)
volume_models = modal.Volume.from_name(
    config.VOLUME_MODELS_NAME, create_if_missing=True
)


# ============================================================
# Image
# ============================================================
# Copy src/ into the container so `import src` works at runtime
_src_dir = str(Path(__file__).parent)

image_denoise = (
    modal.Image.debian_slim(python_version=config.PYTHON_VERSION)
    .apt_install("ffmpeg")
    .pip_install(
        [
            "clearvoice",
            "torch>=2.0.1",
            "torchaudio>=2.0.2",
        ]
    )
    .env({"TQDM_DISABLE": "1", "HF_HUB_DISABLE_PROGRESS": "1"})
    .add_local_dir(_src_dir, remote_path="/root/src", copy=True)
)

image_isolate = image_denoise.pip_install(
    [
        "demucs==4.0.1",
        "soundfile",
    ]
)

# ============================================================
# Whisper Image
# ============================================================
image_whisper = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .apt_install("ffmpeg")
    .pip_install("faster-whisper", "stable-ts")
    .env({"TQDM_DISABLE": "1", "HF_HUB_DISABLE_PROGRESS": "1"})
    .add_local_dir(_src_dir, remote_path="/root/src")
)


# ============================================================
# App Instances
# ============================================================
app = modal.App(config.APP_NAME)
app_isolate = modal.App(config.APP_NAME)
app_whisper = modal.App(config.APP_NAME)
