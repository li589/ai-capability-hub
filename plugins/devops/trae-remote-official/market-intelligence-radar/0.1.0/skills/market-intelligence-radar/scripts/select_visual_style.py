#!/usr/bin/env python3
"""Select one complete Radar visual style with uniform probability."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = SKILL_DIR / "assets" / "radar-visual-kit" / "styles.json"
COMPANION_MANIFEST_PATH = (
    SKILL_DIR
    / "assets"
    / "radar-visual-kit"
    / "dynamic-ui-companions"
    / "manifest.json"
)
EXPECTED_STYLE_IDS = {
    "verdict-sheet",
    "evidence-object",
    "swiss-trace",
    "decision-mosaic",
    "signal-stage",
    "alert-cut",
}
VALID_FRAMEWORKS = {"exhibit-path", "index-gate", "reading-rail"}
COMPANION_FIELDS = {
    "style_id",
    "id",
    "asset",
    "composition",
    "geometry",
    "focal_slot",
    "support_slot",
    "interaction",
    "ink_family",
    "token_map",
}


def load_styles(manifest_path: Path = MANIFEST_PATH) -> list[dict[str, str]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    styles = data.get("styles")
    if data.get("selection") != "uniform-random":
        raise ValueError("manifest selection must be uniform-random")
    expected_companion_manifest = COMPANION_MANIFEST_PATH.relative_to(SKILL_DIR).as_posix()
    if data.get("dynamic_ui_companion_manifest") != expected_companion_manifest:
        raise ValueError("style manifest must reference the companion manifest")
    if data.get("pool_size") != 6 or not isinstance(styles, list) or len(styles) != 6:
        raise ValueError("manifest must contain exactly six styles")

    ids = {style.get("id") for style in styles}
    if ids != EXPECTED_STYLE_IDS:
        raise ValueError("manifest style IDs do not match the required six-style pool")

    for style in styles:
        required = {"id", "name", "framework", "page_background", "asset"}
        if set(style) != required:
            raise ValueError(f"style {style.get('id', '?')} has invalid fields")
        if style["framework"] not in VALID_FRAMEWORKS:
            raise ValueError(f"style {style['id']} has an invalid framework")
        asset_path = SKILL_DIR / style["asset"]
        if not asset_path.is_file():
            raise ValueError(f"style {style['id']} is missing asset {style['asset']}")
    return styles


def load_companions(
    manifest_path: Path = COMPANION_MANIFEST_PATH,
) -> dict[str, dict[str, Any]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    companions = data.get("companions")
    if data.get("selection") != "inherit-uniform-random-style":
        raise ValueError("companion selection must inherit the uniform random style")
    if data.get("pool_size") != 6 or not isinstance(companions, list):
        raise ValueError("companion manifest must contain exactly six entries")

    by_style = {companion.get("style_id"): companion for companion in companions}
    if set(by_style) != EXPECTED_STYLE_IDS or len(companions) != 6:
        raise ValueError("companions must pair one-to-one with the six style IDs")

    for companion in companions:
        if set(companion) != COMPANION_FIELDS:
            raise ValueError(
                f"companion {companion.get('id', '?')} has invalid fields"
            )
        asset_path = SKILL_DIR / companion["asset"]
        if not asset_path.is_file():
            raise ValueError(
                f"companion {companion['id']} is missing asset {companion['asset']}"
            )
        token_map = companion["token_map"]
        if set(token_map) != {"light", "dark"}:
            raise ValueError(f"companion {companion['id']} needs light/dark tokens")
        for mode in ("light", "dark"):
            if set(token_map[mode]) != {
                "brand",
                "chart_series_1",
                "optional_accent",
            }:
                raise ValueError(
                    f"companion {companion['id']} has invalid {mode} token mapping"
                )
    return by_style


def select_style(
    styles: list[dict[str, str]],
    seed: str | None = None,
    companions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if seed is None:
        index = secrets.randbelow(len(styles))
        selection_id = secrets.token_hex(8)
    else:
        rng = random.Random(seed)
        index = rng.randrange(len(styles))
        selection_id = hashlib.sha256(
            f"{seed}:{styles[index]['id']}".encode("utf-8")
        ).hexdigest()[:16]

    result = {
        "selection": "uniform-random",
        "probability": "1/6",
        "pool_size": len(styles),
        "selection_id": selection_id,
        **styles[index],
    }
    if companions is not None:
        result["dynamic_ui_companion"] = companions[result["id"]]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select one of six complete Radar styles with uniform probability."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = select_style(load_styles(), companions=load_companions())
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
