#!/usr/bin/env python3
"""Preflight check for the Meegle (Feishu Project) sub-skill.

Answers two questions with one call, as JSON plus an exit code:

  1. Is the `meegle` binary installed?
  2. Is it authenticated, and against which host?

Why this exists instead of a plain shell check: the Meegle CLI only registers
its business commands *after* login. An unauthenticated CLI answers
`unknown command "workitem" for "meegle"` -- byte-for-byte identical to what it
says about a command that does not exist. Probing with a business command
therefore cannot distinguish "not logged in" from "wrong command name". The
only reliable signal is `meegle auth status`, whose `authenticated` field this
script reads directly.

Exit codes
  0  installed and authenticated  -> proceed
  3  binary not installed         -> on-demand install (see lark-unified 0.3)
  4  installed, not authenticated -> run the device-code flow in auth-guard.md
  5  output could not be parsed   -> inspect `meegle auth status` by hand

Usage
  python3 meegle_status.py [--json]
"""

import json
import shutil
import subprocess
import sys

TIMEOUT = 20


def emit(payload, code):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


def main():
    binary = shutil.which("meegle")
    if not binary:
        emit(
            {
                "installed": False,
                "authenticated": False,
                "state": "not_installed",
                "hint": (
                    "Install on demand, binary only: "
                    "npx -y @lark-project/meegle@latest install "
                    "--no-skills --no-auth --host <host> --lang zh"
                ),
            },
            3,
        )

    version = None
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=TIMEOUT
        )
        if proc.returncode == 0:
            version = proc.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        pass

    try:
        proc = subprocess.run(
            [binary, "auth", "status", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        emit(
            {
                "installed": True,
                "version": version,
                "authenticated": False,
                "state": "unparseable",
                "error": str(exc),
                "hint": "Run `meegle auth status --format json` manually.",
            },
            5,
        )

    # `auth status` exits 1 when unauthenticated, so the exit code alone is not
    # a verdict -- the JSON body on stdout is. Fall back to stderr because some
    # error paths write there instead.
    raw = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    try:
        status = json.loads(raw)
    except (ValueError, TypeError):
        emit(
            {
                "installed": True,
                "version": version,
                "authenticated": False,
                "state": "unparseable",
                "raw": raw[:500],
                "hint": "Run `meegle auth status --format json` manually.",
            },
            5,
        )

    if not isinstance(status, dict):
        emit(
            {
                "installed": True,
                "version": version,
                "authenticated": False,
                "state": "unparseable",
                "raw": raw[:500],
            },
            5,
        )

    authenticated = status.get("authenticated") is True
    payload = {
        "installed": True,
        "version": version,
        "authenticated": authenticated,
        "host": status.get("host"),
        "state": "ready" if authenticated else "not_authenticated",
    }
    for key in ("source", "expires_in_minutes", "reason"):
        if status.get(key) is not None:
            payload[key] = status[key]

    if not authenticated:
        payload["hint"] = (
            "Run the split device-code flow in "
            "skills/meegle/references/auth-guard.md (STEP 2 then STEP 3). "
            "Do NOT run bare `meegle auth login` -- it needs a TTY."
        )
        emit(payload, 4)

    emit(payload, 0)


if __name__ == "__main__":
    main()
