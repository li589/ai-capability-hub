from __future__ import annotations

from pathlib import Path
from typing import Any

from .specs import build_excalidraw_spec, render_excalidraw


def export_excalidraw(blueprint: dict[str, Any], target: Path) -> None:
    spec = build_excalidraw_spec(blueprint)
    content = render_excalidraw(spec)
    target.write_text(content, encoding="utf-8")
