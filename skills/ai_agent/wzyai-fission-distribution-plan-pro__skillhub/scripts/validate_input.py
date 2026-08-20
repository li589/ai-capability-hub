"""Validate the normalized fact payload before formal generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


CORE = ["产品/服务名称", "所属行业", "目标分销人群", "分销目标"]
FINANCE = ["产品售价或价格区间", "成本或毛利率", "激励预算"]


def _missing(payload: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if payload.get(field) in (None, "", [])]


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")
    conflicts = payload.get("_conflicts", [])
    if not isinstance(conflicts, list):
        raise TypeError("_conflicts must be a list")
    missing_core = _missing(payload, CORE)
    return {
        "missing_core": missing_core,
        "missing_finance": _missing(payload, FINANCE),
        "conflicts": conflicts,
        "ready_for_confirmation": not missing_core and not conflicts,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as stream:
        result = validate_payload(json.load(stream))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
