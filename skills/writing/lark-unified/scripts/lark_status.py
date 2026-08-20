#!/usr/bin/env python3
"""
lark_status.py - Idempotent configuration check for lark-cli.

WHY THIS EXISTS
---------------
The previous skill checked configuration with:

    lark-cli config show2>&1 | grep -q "app_id"

That is wrong. `lark-cli config show` prints JSON whose field is `appId`
(camelCase, see internal/core/config.go: `AppId string \\`json:"appId"\\``).
The snake_case string "app_id" never appears, so the grep always failed and
the agent re-ran the whole authorization flow on every single invocation.

This script replaces that grep with a real JSON parse. It is the single
source of truth for "is lark-cli usable right now?".

USAGE
    python3 lark_status.py            # human + machine readable summary
    python3 lark_status.py --json     # JSON only, for scripting
    python3 lark_status.py --quiet    # no output, exit code only

EXIT CODES
    0  configured   - appId present, ready to run commands
    3  not_installed- lark-cli binary not found
    4  not_config   - installed but no appId (setup required)
    5  unknown      - installed, but output could not be parsed
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

EXIT_OK = 0
EXIT_NOT_INSTALLED = 3
EXIT_NOT_CONFIGURED = 4
EXIT_UNKNOWN = 5

# Silence update/skills notifiers so stdout stays parseable JSON.
QUIET_ENV = {
    "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
    "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1",
}


def run(args, timeout=25):
    """Run lark-cli and return (returncode, stdout, stderr)."""
    env = dict(os.environ)
    env.update(QUIET_ENV)
    try:
        p = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, env=env
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "lark-cli not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def extract_json(text):
    """
    Pull the first top-level JSON object out of mixed output.

    lark-cli may prepend/append human notices, so a bare json.loads() on the
    whole stream is not reliable. Scan for a balanced brace region instead.
    """
    if not text:
        return None
    # Fast path.
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


def pick(d, *names):
    """
    Read the first present key among names.

    Accepts both camelCase and snake_case so the check keeps working if the
    CLI output contract ever shifts. This tolerance is the actual fix for the
    appId / app_id class of bug — never hard-code one spelling.
    """
    if not isinstance(d, dict):
        return None
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return None


def detect_workspace():
    """
    Mirror core.DetectWorkspaceFromEnv. Determines whether setup should use
    `config init` (local) or `config bind` (agent workspace).
    """
    g = os.environ.get
    openclaw = [
        "OPENCLAW_HOME",
        "OPENCLAW_STATE_DIR",
        "OPENCLAW_CONFIG_PATH",
        "OPENCLAW_SERVICE_MARKER",
        "OPENCLAW_SERVICE_VERSION",
        "OPENCLAW_GATEWAY_PORT",
        "OPENCLAW_SHELL",
    ]
    if g("OPENCLAW_CLI") == "1" or any(g(k) for k in openclaw):
        return "openclaw"
    if (
        g("HERMES_HOME")
        or g("HERMES_QUIET") == "1"
        or g("HERMES_EXEC_ASK") == "1"
        or g("HERMES_GATEWAY_TOKEN")
        or g("HERMES_SESSION_KEY")
    ):
        return "hermes"
    if g("LARK_CHANNEL") == "1":
        return "lark-channel"
    return "local"


def check_config():
    """Parse `lark-cli config show`. Returns a dict describing config state."""
    code, out, err = run(["lark-cli", "config", "show"])
    if code == 127:
        return {"state": "not_installed"}

    combined = out if out.strip() else err
    data = extract_json(combined)

    # Error envelope: {"ok": false, "error": {"subtype": "not_configured"}}
    if isinstance(data, dict) and data.get("ok") is False:
        sub = pick(data.get("error") or {}, "subtype") or ""
        return {
            "state": "not_configured",
            "reason": sub or "error envelope from config show",
        }

    # Success payload is a flat map: workspace/profile/appId/brand/users.
    payload = data if isinstance(data, dict) else {}
    if isinstance(payload.get("data"), dict):
        payload = payload["data"]

    app_id = pick(payload, "appId", "app_id", "AppId")
    if app_id:
        return {
            "state": "configured",
            "appId": app_id,
            "brand": pick(payload, "brand") or "",
            "profile": pick(payload, "profile") or "",
            "workspace": pick(payload, "workspace") or "",
            "users": pick(payload, "users") or "",
        }

    if data is None:
        return {"state": "unknown", "reason": "could not parse config show output"}
    return {"state": "not_configured", "reason": "no appId field in output"}


def check_auth():
    """
    Best-effort user login check. Never fatal: a configured app with no user
    login is still valid for `--as bot` work.
    """
    code, out, err = run(["lark-cli", "auth", "status", "--json"], timeout=30)
    data = extract_json(out) or extract_json(err) or {}
    body = data.get("data") if isinstance(data.get("data"), dict) else data
    if not isinstance(body, dict):
        return {"userLoggedIn": False}
    ids = body.get("identities") or {}
    user = ids.get("user") if isinstance(ids, dict) else {}
    user = user if isinstance(user, dict) else {}
    status = (pick(user, "status", "tokenStatus") or "").lower()
    return {
        "userLoggedIn": status in ("valid", "active", "ok", "logged_in"),
        "userName": pick(user, "userName") or "",
        "identity": pick(body, "identity") or "",
        "authStatusRaw": status,
    }


def cli_version():
    code, out, err = run(["lark-cli", "--version"], timeout=15)
    if code == 127:
        return ""
    return (out or err).strip().splitlines()[0] if (out or err).strip() else ""


def main():
    ap = argparse.ArgumentParser(description="Check lark-cli install/config state")
    ap.add_argument("--json", action="store_true", help="print JSON only")
    ap.add_argument("--quiet", action="store_true", help="no output, exit code only")
    args = ap.parse_args()

    installed = shutil.which("lark-cli") is not None
    result = {"installed": installed, "workspace": detect_workspace()}

    if not installed:
        result["state"] = "not_installed"
        result["nextStep"] = "npx -y @larksuite/cli@latest install"
        exit_code = EXIT_NOT_INSTALLED
    else:
        result["version"] = cli_version()
        cfg = check_config()
        result.update(cfg)
        state = cfg.get("state")
        if state == "configured":
            result.update(check_auth())
            exit_code = EXIT_OK
            result["nextStep"] = (
                "ready"
                if result.get("userLoggedIn")
                else "bot-ready; run `lark-cli auth login --domain <d> --no-wait --json` for user-identity work"
            )
        elif state == "not_installed":
            exit_code = EXIT_NOT_INSTALLED
            result["state"] = "not_installed"
            result["nextStep"] = "npx -y @larksuite/cli@latest install"
        elif state == "not_configured":
            exit_code = EXIT_NOT_CONFIGURED
            result["nextStep"] = (
                "lark-cli config bind   (agent workspace detected)"
                if result["workspace"] != "local"
                else "python3 lark_setup.py"
            )
        else:
            exit_code = EXIT_UNKNOWN
            result["nextStep"] = "inspect `lark-cli config show` output manually"

    if args.quiet:
        return exit_code
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return exit_code

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(
        f"\n[lark-status] state={result.get('state')} "
        f"workspace={result.get('workspace')} exit={exit_code}",
        file=sys.stderr,
    )
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
