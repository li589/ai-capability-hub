#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


KNOWN_VECTORS = {
    462116040: "47445B6B8",
    462116041: "47445B6B9",
    3: "ROXC",
}


def encode_que_id(value: int, width: int = 4) -> str:
    negative = value < 0
    absolute = abs(value)
    state = 17 * absolute
    digits = str(absolute)
    inserts: list[int] = []
    insert_sum = 0

    for _ in range(width - len(digits)):
        insert = state % 20 + 71
        state = 17 * (state + 13) % 1000013
        insert_sum += insert
        inserts.append(insert)

    encoded: list[int] = []
    for index, digit in enumerate(digits):
        encoded.append((insert_sum + index + int(digit, 16)) % 15)

    for insert in inserts:
        index = (state + insert) % len(encoded)
        state = 17 * (state + 13) % 1000013
        encoded.insert(index, insert)

    result = "".join(
        chr(item) if item > 15 else format(item, "x") for item in encoded
    ).upper()
    return ("-" if negative else "") + result


def make_placeholder(title: str, que_id: int, parent: str | None = None) -> str:
    field_title = f"{parent} · {title}" if parent else title
    return f"{{{field_title}$${encode_que_id(que_id)}$$}}"


def run_self_test() -> None:
    failures = {
        value: (expected, encode_que_id(value))
        for value, expected in KNOWN_VECTORS.items()
        if encode_que_id(value) != expected
    }
    if failures:
        raise SystemExit(f"Self-test failed: {failures}")
    print("Self-test passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Encode a Qingflow que_id and optionally build a Word placeholder."
    )
    parser.add_argument("--que-id", type=int, help="Numeric que_id from Builder MCP")
    parser.add_argument("--title", help="Qingflow field title")
    parser.add_argument("--parent", help="Parent subtable title")
    parser.add_argument(
        "--token-only",
        action="store_true",
        help="Print only the encoded token",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--self-test", action="store_true", help="Run known vectors")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return
    if args.que_id is None:
        raise SystemExit("--que-id is required unless --self-test is used")

    token = encode_que_id(args.que_id)
    placeholder = None
    if args.title:
        placeholder = make_placeholder(args.title, args.que_id, args.parent)

    if args.json:
        print(
            json.dumps(
                {
                    "que_id": args.que_id,
                    "token": token,
                    "title": args.title,
                    "parent": args.parent,
                    "placeholder": placeholder,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.token_only or not placeholder:
        print(token)
    else:
        print(placeholder)


if __name__ == "__main__":
    main()

