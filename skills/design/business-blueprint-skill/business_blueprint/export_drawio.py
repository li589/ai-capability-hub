from __future__ import annotations

from pathlib import Path
from typing import Any

from .specs import build_drawio_spec, render_drawio


def export_drawio(blueprint: dict[str, Any], target: Path) -> None:
    spec = build_drawio_spec(blueprint)
    xml = render_drawio(spec)
    target.write_text(xml, encoding="utf-8")
