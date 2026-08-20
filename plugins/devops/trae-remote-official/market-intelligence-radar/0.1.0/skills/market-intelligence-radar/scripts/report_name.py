#!/usr/bin/env python3
"""Generate a dated basename for a Market Intelligence Radar deliverable."""

from __future__ import annotations

import argparse
import re
import unicodedata
from datetime import date


DATE_SUFFIX_RE = re.compile(r"-\d{4}-\d{2}-\d{2}(?:-w\d{2})?$", re.I)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    slug = DATE_SUFFIX_RE.sub("", slug).strip("-")
    return slug or "market-intelligence"


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def build_name(topic: str, run_date: date, cadence: str) -> str:
    basename = f"{slugify(topic)}-{run_date.isoformat()}"
    if cadence == "weekly":
        basename += f"-w{run_date.isocalendar().week:02d}"
    return basename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a required dated report basename."
    )
    parser.add_argument("topic", help="Short report topic or slug.")
    parser.add_argument(
        "--cadence",
        choices=("alert", "daily", "weekly", "monthly", "one-off"),
        default="one-off",
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        default=date.today(),
        dest="run_date",
        help="Run date in the report timezone (YYYY-MM-DD). Defaults to local today.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(build_name(args.topic, args.run_date, args.cadence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
