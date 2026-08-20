# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Honest-verdict sidecar contract.

``server.py`` calls ``write_sidecar(output_path)`` after each successful generate,
producing ``<output_path>.verdict.json`` — an HMAC-signed receipt proving the
output is a genuine product of this skill (the host can verify before declaring a
product). Pure-stdlib: importable without OpenVINO.

The runtime-root slug is ``screenshot-qa`` (kept in sync with ``capture.py`` so
nonce, captures, and outputs all live under one tree); the reported ``skill_name``
field is the conforming skill name ``local-screenshot-qa``.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

SKILL_NAME = "local-screenshot-qa"
RUNTIME_SLUG = "screenshot-qa"
SKILL_VERSION = "1.0.0"
SCHEMA_VERSION = 1


def runtime_root() -> Path:
    base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return Path(base) / ".openvino" / RUNTIME_SLUG


def nonce_path() -> Path:
    return runtime_root() / "runtime" / "install_nonce.bin"


def load_or_create_nonce() -> bytes:
    p = nonce_path()
    if p.exists():
        data = p.read_bytes()
        if len(data) == 32:
            return data
    p.parent.mkdir(parents=True, exist_ok=True)
    new_nonce = secrets.token_bytes(32)
    # Atomic: write to tmp, replace, only if still missing.
    tmp = p.with_suffix(".bin.tmp")
    tmp.write_bytes(new_nonce)
    try:
        os.replace(tmp, p)
    except OSError:
        # Race lost — re-read whatever's there.
        try:
            tmp.unlink()
        except OSError:
            pass
        data = p.read_bytes()
        if len(data) == 32:
            return data
        raise
    # Make user-readable, read-only (best effort on Windows; ACLs are coarser).
    try:
        os.chmod(p, 0o400)
    except OSError:
        pass
    return new_nonce


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sidecar(
    output_path: str | Path,
    *,
    model_id: str = "snake7gun/Qwen3-VL-4B-Instruct-int4-ov",
) -> Path:
    """Write ``<output_path>.verdict.json`` for a successful generate.

    Returns the path of the sidecar. Raises FileNotFoundError if the output is
    missing. Idempotent — overwriting an existing sidecar is allowed because
    the HMAC always re-derives from the on-disk output's sha256.
    """
    out = Path(output_path)
    if not out.exists():
        raise FileNotFoundError(out)
    nonce = load_or_create_nonce()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "skill_name": SKILL_NAME,
        "output_path": str(out),
        "output_sha256": _sha256_of_file(out),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill_version": SKILL_VERSION,
        "model_id": model_id,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["hmac_sha256"] = hmac.new(nonce, canonical, hashlib.sha256).hexdigest()
    side = Path(str(out) + ".verdict.json")
    side.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return side


def verify_output(output_path: str | Path) -> dict:
    """Return a dict ready to JSON-dump per the verdict contract."""
    out = Path(output_path)
    side = Path(str(out) + ".verdict.json")
    if not side.exists():
        return {
            "ok": False,
            "reason": "verdict_missing",
            "output_path": str(out),
            "verdict_path": str(side),
        }
    try:
        verdict = json.loads(side.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "reason": f"verdict_unreadable:{exc}"}
    if not out.exists():
        return {
            "ok": False,
            "reason": "output_missing",
            "output_path": str(out),
            "verdict_path": str(side),
        }
    actual_sha = _sha256_of_file(out)
    if actual_sha != verdict.get("output_sha256"):
        return {
            "ok": False,
            "reason": "sha256_mismatch",
            "output_path": str(out),
            "verdict_path": str(side),
        }
    np = nonce_path()
    if not np.exists():
        return {"ok": False, "reason": "nonce_missing"}
    nonce = np.read_bytes()
    expected = verdict.get("hmac_sha256", "")
    payload = {k: v for k, v in verdict.items() if k != "hmac_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    computed = hmac.new(nonce, canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, expected):
        return {
            "ok": False,
            "reason": "hmac_mismatch",
            "output_path": str(out),
            "verdict_path": str(side),
        }
    return {
        "ok": True,
        "output_path": str(out),
        "verdict_path": str(side),
        "skill_name": SKILL_NAME,
    }
