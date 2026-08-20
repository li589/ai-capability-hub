# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Progress beacon helpers — written by server.py.

The shape is:
{
  "phase":    "server|download|load|generate|done|error",
  "message":  "<human-friendly status>",
  "terminal": <bool>,
  "ts":       <unix seconds>,
  "pid":      <int>
}

Beacon file lives at ``<runtime>/progress.json``. Atomic-write via .tmp + replace.
Pure-stdlib and best-effort — never raises.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

RUNTIME_SLUG = "screenshot-qa"


def runtime_dir() -> Path:
    base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return Path(base) / ".openvino" / RUNTIME_SLUG / "runtime"


def emit(phase: str, message: str = "", terminal: bool = False) -> None:
    rt = runtime_dir()
    try:
        rt.mkdir(parents=True, exist_ok=True)
        payload = {
            "phase": phase,
            "message": message,
            "terminal": terminal,
            "ts": time.time(),
            "pid": os.getpid(),
        }
        tmp = rt / "progress.json.tmp"
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(rt / "progress.json")
    except Exception:
        # Beacons are best-effort. Never raise from here.
        pass


def read() -> dict:
    p = runtime_dir() / "progress.json"
    if not p.exists():
        return {"phase": "unknown", "message": "no beacon yet", "terminal": False}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"phase": "unreadable", "message": "beacon corrupt", "terminal": False}
