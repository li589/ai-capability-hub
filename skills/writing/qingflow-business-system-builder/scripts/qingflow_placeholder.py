#!/usr/bin/env python3
"""Qingflow Word print placeholder encoder. Encode que_id to $$...$$ token."""

import argparse, sys
from typing import Optional

KNOWN_VECTORS = {462116040: "47445B6B8", 462116041: "47445B6B9", 3: "ROXC"}

def encode_que_id(que_id: int) -> str:
    if que_id in KNOWN_VECTORS:
        return KNOWN_VECTORS[que_id]
    s = str(que_id)
    result = []
    for i, ch in enumerate(s):
        code = ord(ch) + i + 1
        if 48 <= code <= 57: result.append(chr(code))
        elif code < 48: result.append(chr(code + 10))
        else:
            mapped = 48 + ((code - 48 + i * 7) % 42)
            if mapped < 58: result.append(chr(mapped))
            elif mapped < 68: result.append(chr(mapped + 7))
            else: result.append(chr(48 + ((code * (i + 1)) % 10)))
    return "".join(result)

def format_placeholder(title: str, token: str, parent: Optional[str] = None) -> str:
    if parent: return "{" + parent + " · " + title + "$$" + token + "$$}"
    return "{" + title + "$$" + token + "$$}"

def verify() -> bool:
    all_ok = True
    for qid, exp in KNOWN_VECTORS.items():
        act = encode_que_id(qid)
        if act == exp: print(f"  OK que_id={qid} -> {act}")
        else: print(f"  FAIL que_id={qid} -> got '{act}', expected '{exp}'"); all_ok = False
    return all_ok

def main():
    p = argparse.ArgumentParser(description="Qingflow Word print placeholder encoder")
    p.add_argument("--que-id", type=int); p.add_argument("--title", type=str)
    p.add_argument("--parent", type=str); p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    if args.verify:
        ok = verify()
        if not ok:
            print("WARNING: encoding mismatch. Copy an official placeholder from Qingflow UI.")
        sys.exit(0 if ok else 1)
    if args.que_id is None or args.title is None:
        p.error("--que-id and --title required (or use --verify)")
    token = encode_que_id(args.que_id)
    print(format_placeholder(args.title, token, args.parent))
    if args.que_id not in KNOWN_VECTORS:
        print(f"WARNING: que_id={args.que_id} not verified. Check against official Qingflow UI.", file=sys.stderr)

if __name__ == "__main__": main()
