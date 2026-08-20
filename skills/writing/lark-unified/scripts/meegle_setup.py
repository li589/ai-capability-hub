#!/usr/bin/env python3
"""
meegle_setup.py - Non-TTY login for the Meegle CLI (飞书项目 / Lark Project).

WHY THIS EXISTS
---------------
The official meegle skill tells the agent to run:

    meegle auth login --host $host

That opens a browser and blocks on a real TTY. In an agent harness there is no
TTY, so the command either hangs until timeout or renders an unusable prompt —
the same failure this suite already solved for lark-cli.

The CLI does support a headless path, but it is absent from the official skill:
`--device-code` can be split into two independent phases.

    meegle auth login --device-code --phase init --host <host>
    -> {"device_code","user_code","verification_uri",
        "verification_uri_complete","expires_in","interval","client_id"}

    meegle auth login --device-code --phase poll \
        --device-code-value <dc> --client-id <cid> [--once]

Because `init` returns and exits, the agent can print the URL, END THE TURN, and
poll later. That matters: in harnesses that hide intermediate output, showing a
URL and blocking in the same turn means the user never sees the link.

`--once` makes a single non-blocking attempt and prints {"status": ...}, so the
agent can poll without holding a turn open forten minutes.

USAGE
    # Turn 1 -- get the URL, then END THE TURN
    python3 meegle_setup.py --host project.feishu.cn --print-url-only

    # Turn 2 -- after the user confirms authorization
    python3 meegle_setup.py --resume --device-code <dc> --client-id <cid>

    # One-shot (only when blocking for a few minutes is acceptable)
    python3 meegle_setup.py --host project.feishu.cn

    python3 meegle_setup.py --status          # just report current state
    python3 meegle_setup.py --host<h> --force  # re-login even if authenticated

EXIT CODES
    0  authenticated (or URL issued successfully in --print-url-only)
    1  usage / unexpected error
    2  pending    - user has not authorized yet, poll again
    3  meegle not installed
    4  device flow failed (expired, denied, server error)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_PENDING = 2
EXIT_NOT_INSTALLED = 3
EXIT_FLOW_FAILED = 4

KNOWN_HOSTS = ("project.feishu.cn", "meegle.com")


def run(args, timeout=60):
    try:
        p = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, env=dict(os.environ)
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "meegle not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def extract_json(text):
    """Pull the first balanced top-level JSON object out of mixed output."""
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except Exception:
                        break
        start = text.find("{", start + 1)
    return None


def emit(payload, code):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def require_installed():
    if shutil.which("meegle") is None:
        emit(
            {
                "ok": False,
                "state": "not_installed",
                # --no-skills is mandatory: without it the official wizard also
                # runs `skills add`, dropping a second copy of the meegle skill
                # into the agent's global skill directory, which then competes
                # with the copy bundled in this suite. --no-auth keeps install
                # and login separate so login can use the split device-code
                # flow this script implements.
                "hint": "npx -y @lark-project/meegle@latest install "
                "--no-skills --no-auth --host <host> --lang zh",
                "note": "installs globally via `npm install -g`; tell the user before running it",
            },
            EXIT_NOT_INSTALLED,
        )
        sys.exit(EXIT_NOT_INSTALLED)


def auth_state():
    """Return (authenticated: bool, body: dict, exit_code: int)."""
    code, out, err = run(["meegle", "auth", "status", "--format", "json"], timeout=30)
    data = extract_json(out) or extract_json(err) or {}
    body = data.get("data") if isinstance(data.get("data"), dict) else data
    body = body if isinstance(body, dict) else {}
    return bool(body.get("authenticated")), body, code


def resolve_host(explicit):
    """Explicit flag wins, then whatever the profile already stores."""
    if explicit:
        return explicit
    _, body, _ = auth_state()
    if body.get("host"):
        return body["host"]
    code, out, err = run(["meegle", "config", "show", "--format", "json"], timeout=20)
    data = extract_json(out) or extract_json(err) or {}
    body = data.get("data") if isinstance(data.get("data"), dict) else data
    if isinstance(body, dict) and body.get("host"):
        return body["host"]
    return ""


def device_init(host):
    code, out, err = run(
        [
            "meegle",
            "auth",
            "login",
            "--device-code",
            "--phase",
            "init",
            "--host",
            host,
            "--format",
            "json",
        ],
        timeout=60,
    )
    data = extract_json(out) or extract_json(err)
    if code != 0 or not isinstance(data, dict) or not data.get("device_code"):
        return None, (err or out or "device code init failed").strip()
    return data, ""


def device_poll_once(device_code, client_id, host=""):
    """
    Single non-blocking poll. Returns (status, raw).

    status is the CLI's own string: "ok" on success, otherwise a pending or
    error state such as "authorization_pending" / "slow_down" / "expired_token".
    """
    args = [
        "meegle",
        "auth",
        "login",
        "--device-code",
        "--phase",
        "poll",
        "--device-code-value",
        device_code,
        "--client-id",
        client_id,
        "--once",
        "--format",
        "json",
    ]
    if host:
        args += ["--host", host]
    code, out, err = run(args, timeout=60)
    data = extract_json(out) or extract_json(err) or {}
    status = (data.get("status") or "").lower()
    if not status:
        status = "ok" if code == 0 else "error"
    return status, (out or err).strip()


# Poll states that mean "keep waiting" rather than "give up".
PENDING_STATES = {"authorization_pending", "pending", "slow_down", "waiting"}


def cmd_print_url(host):
    info, error = device_init(host)
    if info is None:
        return emit(
            {"ok": False, "state": "init_failed", "error": error}, EXIT_FLOW_FAILED
        )

    # verification_uri_complete already embeds the user_code -- prefer it so the
    # user does not have to type the code by hand. Treat it as an opaque string:
    # no re-encoding, no rebuilding query params.
    url = info.get("verification_uri_complete") or info.get("verification_uri") or ""
    dc = info.get("device_code", "")
    cid = info.get("client_id", "")
    return emit(
        {
            "ok": True,
            "state": "awaiting_authorization",
            "host": host,
            "verification_url": url,
            "user_code": info.get("user_code", ""),
            "device_code": dc,
            "client_id": cid,
            "expires_in": info.get("expires_in"),
            "interval": info.get("interval"),
            "resume_command": (
                f"python3 meegle_setup.py --resume "
                f"--device-code {dc} --client-id {cid}"
            ),
            "note": (
                "Show verification_url to the user and END THE TURN. "
                "Do not poll in this same turn."
            ),
        },
        EXIT_OK,
    )


def cmd_resume(device_code, client_id, host, attempts, interval):
    """Poll a device code that a previous --print-url-only turn handed out."""
    last = ""
    for i in range(max(1, attempts)):
        status, raw = device_poll_once(device_code, client_id, host)
        last = status
        if status == "ok":
            authed, body, _ = auth_state()
            return emit(
                {
                    "ok": True,
                    "state": "authenticated",
                    "host": body.get("host") or host,
                    "authenticated": authed,
                    "expires_in_minutes": body.get("expires_in_minutes"),
                },
                EXIT_OK,
            )
        if status not in PENDING_STATES:
            return emit(
                {"ok": False, "state": status or "error", "raw": raw},
                EXIT_FLOW_FAILED,
            )
        if i < attempts - 1:
            time.sleep(max(1, interval))

    return emit(
        {
            "ok": False,
            "state": "pending",
            "lastStatus": last,
            "hint": "user has not authorized yet; run the same --resume command again",
            "resume_command": (
                f"python3 meegle_setup.py --resume "
                f"--device-code {device_code} --client-id {client_id}"
            ),
        },
        EXIT_PENDING,
    )


def cmd_oneshot(host, attempts, interval):
    """init + poll in one call. Blocks; only use when that is acceptable."""
    info, error = device_init(host)
    if info is None:
        return emit(
            {"ok": False, "state": "init_failed", "error": error}, EXIT_FLOW_FAILED
        )
    url = info.get("verification_uri_complete") or info.get("verification_uri") or ""
    print(
        json.dumps(
            {
                "state": "awaiting_authorization",
                "verification_url": url,
                "user_code": info.get("user_code", ""),
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    poll_interval = interval or int(info.get("interval") or 5)
    return cmd_resume(
        info.get("device_code", ""),
        info.get("client_id", ""),
        host,
        attempts,
        poll_interval,
    )


def main():
    ap = argparse.ArgumentParser(
        description="Headless (device-code) login for the Meegle CLI"
    )
    ap.add_argument("--host", default="", help=f"site domain, e.g. {KNOWN_HOSTS[0]}")
    ap.add_argument(
        "--print-url-only",
        action="store_true",
        help="phase 1: emit the verification URL and exit (preferred for agents)",
    )
    ap.add_argument(
        "--resume", action="store_true", help="phase 2: poll an existing device code"
    )
    ap.add_argument("--device-code", default="", help="device_code from phase 1")
    ap.add_argument("--client-id", default="", help="client_id from phase 1")
    ap.add_argument(
        "--attempts", type=int, default=3, help="poll attempts (default 3)"
    )
    ap.add_argument(
        "--interval", type=int, default=5, help="seconds between polls (default 5)"
    )
    ap.add_argument("--status", action="store_true", help="report state and exit")
    ap.add_argument(
        "--force", action="store_true", help="log in again even if already authenticated"
    )
    args = ap.parse_args()

    require_installed()

    if args.status:
        authed, body, code = auth_state()
        return emit(
            {
                "ok": authed,
                "state": "authenticated" if authed else "not_logged_in",
                "host": body.get("host") or "",
                "reason": body.get("reason") or "",
                "authStatusExit": code,
            },
            EXIT_OK if authed else EXIT_ERROR,
        )

    if args.resume:
        if not args.device_code or not args.client_id:
            return emit(
                {
                    "ok": False,
                    "state": "usage_error",
                    "error": "--resume requires --device-code and --client-id "
                    "(both come from the --print-url-only output)",
                },
                EXIT_ERROR,
            )
        return cmd_resume(
            args.device_code,
            args.client_id,
            args.host,
            args.attempts,
            args.interval,
        )

    # Idempotent: an existing session is left alone unless --force.
    if not args.force:
        authed, body, _ = auth_state()
        if authed:
            return emit(
                {
                    "ok": True,
                    "state": "already_authenticated",
                    "host": body.get("host") or "",
                    "expires_in_minutes": body.get("expires_in_minutes"),
                },
                EXIT_OK,
            )

    host = resolve_host(args.host)
    if not host:
        return emit(
            {
                "ok": False,
                "state": "host_required",
                "error": "no host configured; pass --host",
                "knownHosts": list(KNOWN_HOSTS),
                "hint": "ask the user which site: 飞书项目 (project.feishu.cn), "
                "Meegle (meegle.com), or a self-hosted domain",
            },
            EXIT_ERROR,
        )

    if args.print_url_only:
        return cmd_print_url(host)
    return cmd_oneshot(host, args.attempts, args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_ERROR)
