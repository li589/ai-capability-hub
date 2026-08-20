#!/usr/bin/env python3
"""Validate a portable WeChat article branding profile."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_profile(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("profile root must be an object")
    return data


def valid_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    brand = profile.get("brand")
    if not isinstance(brand, dict):
        errors.append("brand must be an object")
        brand = {}
    if not nonempty(brand.get("name")):
        errors.append("brand.name is required")
    if not valid_url(brand.get("site")):
        errors.append("brand.site must be an HTTP(S) URL")
    public_facts = brand.get("public_facts", [])
    if not isinstance(public_facts, list) or not all(nonempty(item) for item in public_facts):
        errors.append("brand.public_facts must be a list of non-empty strings")
    forbidden = brand.get("forbidden_context", [])
    if not isinstance(forbidden, list) or not all(nonempty(item) for item in forbidden):
        errors.append("brand.forbidden_context must be a list of non-empty strings")

    visual = profile.get("visual", {})
    if not isinstance(visual, dict):
        errors.append("visual must be an object")
        visual = {}
    color = visual.get("primary_color")
    if color is not None and (not isinstance(color, str) or not HEX_COLOR.fullmatch(color)):
        errors.append("visual.primary_color must use #RRGGBB")
    ratios = visual.get("cover_ratios", [])
    if not isinstance(ratios, list) or not all(nonempty(item) for item in ratios):
        errors.append("visual.cover_ratios must be a list of ratio strings")

    products = profile.get("products", [])
    if not isinstance(products, list):
        errors.append("products must be a list")
    else:
        for index, product in enumerate(products):
            if not isinstance(product, dict):
                errors.append(f"products[{index}] must be an object")
                continue
            if not nonempty(product.get("name")):
                errors.append(f"products[{index}].name is required")
            if not nonempty(product.get("promise")):
                errors.append(f"products[{index}].promise is required")
            if not valid_url(product.get("url")):
                errors.append(f"products[{index}].url must be an HTTP(S) URL")
    return errors


def self_test() -> int:
    profile = {
        "brand": {
            "name": "Example Studio",
            "site": "https://example.com",
            "public_facts": ["Builds useful software"],
            "forbidden_context": ["private note"],
        },
        "visual": {"primary_color": "#00B38A", "cover_ratios": ["2.35:1", "1:1"]},
        "products": [
            {"name": "Example Product", "promise": "A clear user result", "url": "https://example.com/product"}
        ],
    }
    errors = validate(profile)
    if errors:
        print("SELF-TEST FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    invalid = dict(profile)
    invalid["brand"] = {"name": "", "site": "not-a-url"}
    if not validate(invalid):
        print("SELF-TEST FAILED: invalid brand profile was accepted")
        return 1
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "brand.json"
        path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
        if validate(load_profile(path)):
            print("SELF-TEST FAILED: JSON round trip")
            return 1
    print("SELF-TEST PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.profile is None:
        parser.error("profile JSON is required")
    try:
        errors = validate(load_profile(args.profile))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAILED: {exc}")
        return 1
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASSED: brand profile is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
