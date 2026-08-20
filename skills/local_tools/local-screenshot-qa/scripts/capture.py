# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Primary-screen capture helper for the screenshot-qa skill.

Single responsibility: grab the primary screen, save a timestamped PNG under the
per-install runtime root, and return its absolute path. Used by client.py when a
question arrives without an image path.

The `_grab` parameter is a private test seam: callers never pass it; tests inject
a fake grabber so they need neither a real display nor Pillow.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Optional


class CaptureError(Exception):
    """Raised when the primary screen cannot be captured."""


def _runtime_root() -> Path:
    base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return Path(base) / ".openvino" / "screenshot-qa"


def capture_screen(dest_dir: Optional[Path] = None, _grab: Optional[Callable] = None) -> str:
    """Grab the primary screen, save a PNG, return its absolute path.

    Raises CaptureError on any failure (e.g. headless / RDP session with no
    interactive desktop, unwritable directory, or save failure).
    """
    if dest_dir is None:
        dest_dir = _runtime_root() / "captures"

    if _grab is None:
        try:
            from PIL import ImageGrab  # local import: keeps module importable without a display
        except Exception as exc:  # pragma: no cover - pillow is a hard dependency
            raise CaptureError(f"Pillow/ImageGrab unavailable: {exc}") from exc
        _grab = ImageGrab.grab

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CaptureError(f"cannot create capture dir {dest_dir}: {exc}") from exc

    try:
        img = _grab()
    except Exception as exc:
        raise CaptureError(f"screen grab failed (headless / no desktop?): {exc}") from exc
    if img is None:
        raise CaptureError("screen grab returned no image")

    ts = time.strftime("%Y%m%d-%H%M%S")
    out = dest_dir / f"screen-{ts}.png"
    n = 1
    while out.exists():
        out = dest_dir / f"screen-{ts}-{n}.png"
        n += 1

    try:
        img.save(out, format="PNG")
    except Exception as exc:
        raise CaptureError(f"failed to save capture to {out}: {exc}") from exc

    return str(out.resolve())
