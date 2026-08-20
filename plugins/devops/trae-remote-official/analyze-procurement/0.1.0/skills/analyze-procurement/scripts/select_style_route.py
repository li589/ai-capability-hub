#!/usr/bin/env python3
"""Select one procurement visual route without a model-preference default."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from pathlib import Path


MANIFEST = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "procurement-visual-kit"
    / "style-routes.json"
)
ROUTES = tuple(json.loads(MANIFEST.read_text(encoding="utf-8")))


def select_route(seed: str | None) -> dict[str, object]:
    if seed is None:
        return ROUTES[secrets.randbelow(len(ROUTES))]
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return ROUTES[int.from_bytes(digest[:8], "big") % len(ROUTES)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed",
        help="Optional reproducible key for tests or intentional repeatability.",
    )
    parser.add_argument("--list", action="store_true", help="List all routes.")
    args = parser.parse_args()
    payload = ROUTES if args.list else select_route(args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
