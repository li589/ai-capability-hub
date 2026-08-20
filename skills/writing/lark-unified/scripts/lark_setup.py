#!/usr/bin/env python3
"""
lark_setup.py - Non-TTY app registration for lark-cli.

Reproduces the device flow of `lark-cli config init --new` for environments
without a usable TTY (WorkBuddy, CI, headless shells), where the interactive
command renders a broken QR code or hangs.

Aligned with larksuite/cli v1.0.82 (internal/auth/app_registration.go).

CHANGES vs the earlier version of this script
---------------------------------------------
1. Idempotency. Checks existing config by parsing the `appId` field from
   `config show` JSON instead of grepping for "app_id", which never matched
   and caused the flow to re-authorize on every run. Use --force to override.
2. The verification URL is now built client-side as `{open_host}/page/cli?user_code=`,
   matching v1.0.82. The server still returns `verification_uri_complete` pointing at
   `/page/launcher`, and the Go code deliberately ignores it (app_registration.go:159).
   Both pages return HTTP 200, but `/page/cli` is the one the official CLI sends users to.
3. Expiry is read as `expire_in` first, falling back to `expires_in`. Verified live: the
   server currently sends only `expires_in` (3600), so the fallback is what actually fires --
   do not remove it.
4. Cross-brand switch happens mid-poll (feishu -> lark) on the tenant_brand
   signal, immediately and without waiting, matching RegisterAppWithDiscovery.
   The old code only retried after the whole poll loop finished.
5. Agent workspaces (OPENCLAW_HOME / HERMES_HOME / LARK_CHANNEL) are detected
   and refused: `lark-cli config bind` is correct there, and `config init`
   would create a parallel app.
6. Polling continues on transient network/parse errors rather than aborting.

USAGE
    python3 lark_setup.py                  # feishu, opens browser
    python3 lark_setup.py --brand lark     # Lark international
    python3 lark_setup.py --no-browser     # print URL only
    python3 lark_setup.py --print-url-only # emit URL + device_code, no polling
    python3 lark_setup.py --device-code X# resume polling an existing code
    python3 lark_setup.py --force          # re-register even if configured

AGENT PATTERN (recommended)
    Step 1: python3 lark_setup.py --print-url-only
            -> send the URL to the user, end the turn
    Step 2: python3 lark_setup.py --device-code <code>
            -> run this yourself after the user confirms
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# --- Endpoints (mirrors internal/core/types.go ResolveEndpoints) ---
ENDPOINTS = {
    "feishu": {
        "accounts": "https://accounts.feishu.cn",
        "open": "https://open.feishu.cn",
    },
    "lark": {
        "accounts": "https://accounts.larksuite.com",
        "open": "https://open.larksuite.com",
    },
}

# Registration always bootstraps on the feishu accounts host regardless of the
# requested brand (registrationBootstrapBrand in app_registration.go).
BOOTSTRAP_BRAND = "feishu"

REGISTRATION_PATH = "/oauth/v1/app/registration"

DEFAULT_POLL_INTERVAL = 5
DEFAULT_EXPIRE_IN = 600
MAX_POLL_INTERVAL = 60
CLI_VERSION = "1.0.82"

QUIET_ENV = {
    "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
    "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1",
}


def log(msg):
    print(f"[lark-setup] {msg}", flush=True)


# ---------------------------------------------------------------- HTTP


def post_form(url, data):
    """POST form-encoded. OAuth errors arrive as HTTP 400 with a JSON body."""
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw)
        except Exception:
            raise RuntimeError(f"HTTP {e.code}: {raw.decode(errors='replace')[:300]}")


# ------------------------------------------------------- workspace / config


def detect_workspace():
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


def _extract_json(text):
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
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


def existing_app_id():
    """
    Return the configured appId, or None.

    THIS is the function that fixes the repeat-authorization bug. The field in
    `config show` output is `appId` (camelCase). Accept snake_case variants too
    so a future contract change cannot silently reintroduce the false negative.
    """
    env = dict(os.environ)
    env.update(QUIET_ENV)
    try:
        p = subprocess.run(
            ["lark-cli", "config", "show"],
            capture_output=True,
            text=True,
            timeout=25,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    data = _extract_json(p.stdout) or _extract_json(p.stderr)
    if not isinstance(data, dict):
        return None
    if data.get("ok") is False:
        return None
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    for key in ("appId", "app_id", "AppId"):
        val = payload.get(key)
        if val:
            return val
    return None


# ---------------------------------------------------------------- device flow


def begin_registration():
    """Step 1: request a device code. Always hits the feishu accounts host."""
    url = ENDPOINTS[BOOTSTRAP_BRAND]["accounts"] + REGISTRATION_PATH
    resp = post_form(
        url,
        {
            "action": "begin",
            "archetype": "PersonalAgent",
            "auth_method": "client_secret",
            "request_user_info": "open_id tenant_brand",
        },
    )
    if resp.get("error"):
        raise RuntimeError(
            f"Registration failed: {resp.get('error_description') or resp['error']}"
        )
    if not resp.get("device_code"):
        raise RuntimeError("Registration failed: response missing device_code")
    return resp


def build_verification_url(brand, user_code):
    """
    Construct the verification URL the way the Go code does:
    {open_host}/page/cli?user_code=<code>, then append CLI tracking params.

    The server's own verification_uri field is intentionally not used --
    v1.0.82 composes this client-side.
    """
    base = f"{ENDPOINTS[brand]['open']}/page/cli?user_code={urllib.parse.quote(user_code)}"
    return (
        base
        + "&lpv="
        + urllib.parse.quote(CLI_VERSION)
        + "&ocv="
        + urllib.parse.quote(CLI_VERSION)
        + "&from=cli"
    )


def poll_registration(device_code, brand, interval, expire_in):
    """
    Step 2: poll until the user authorizes.

    Handles the immediate cross-brand switch: if the tenant reports a different
    brand, re-target the accounts host at once without waiting, even when the
    signal arrives alongside authorization_pending.
    """
    interval = interval or DEFAULT_POLL_INTERVAL
    deadline = time.time() + (expire_in or DEFAULT_EXPIRE_IN)

    current_brand = BOOTSTRAP_BRAND if brand == "feishu" else brand
    effective_brand = current_brand
    switched = False
    wait_before_poll = False
    pending_logged = False

    while time.time() < deadline:
        if wait_before_poll:
            time.sleep(interval)
        wait_before_poll = True

        url = ENDPOINTS[current_brand]["accounts"] + REGISTRATION_PATH
        try:
            resp = post_form(url, {"action": "poll", "device_code": device_code})
        except Exception as e:
            # Transient failures must not abort the flow.
            log(f"  WARN poll error ({e}); retrying")
            interval = min(interval + 1, MAX_POLL_INTERVAL)
            continue

        # Cross-brand switch: immediate, at most once, regardless of status.
        if not switched:
            info = resp.get("user_info") or {}
            tb = (info.get("tenant_brand") or "").strip()
            if tb in ENDPOINTS and tb != current_brand:
                log(f"  Tenant brand is '{tb}'; switching accounts host")
                current_brand = tb
                effective_brand = tb
                switched = True
                wait_before_poll = False
                continue

        err = resp.get("error") or ""

        if not err:
            client_id = resp.get("client_id") or ""
            client_secret = resp.get("client_secret") or ""
            if client_id and client_secret:
                info = resp.get("user_info") or {}
                tb = (info.get("tenant_brand") or "").strip()
                if tb and tb in ENDPOINTS and tb != effective_brand:
                    raise RuntimeError(
                        f"Credentials returned with contradictory tenant brand '{tb}'"
                    )
                return client_id, client_secret, effective_brand
            # No error but incomplete credentials: keep polling.
            continue

        if err == "authorization_pending":
            if not pending_logged:
                log("  Waiting for browser authorization...")
                pending_logged = True
            continue
        if err == "slow_down":
            interval = min(interval + 5, MAX_POLL_INTERVAL)
            log(f"  slow_down; interval now {interval}s")
            continue
        if err == "access_denied":
            raise RuntimeError("Authorization denied by user.")
        if err in ("expired_token", "invalid_grant"):
            raise RuntimeError("Device code expired. Start over.")
        raise RuntimeError(f"Poll error: {resp.get('error_description') or err}")

    raise RuntimeError("Authorization timed out. Start over.")


def save_config(app_id, app_secret, brand):
    """Step 3: persist via non-interactive flags, secret through stdin."""
    env = dict(os.environ)
    env.update(QUIET_ENV)
    proc = subprocess.run(
        [
            "lark-cli",
            "config",
            "init",
            "--app-id",
            app_id,
            "--app-secret-stdin",
            "--brand",
            brand,
        ],
        input=app_secret,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"`lark-cli config init` failed (exit {proc.returncode}):\n"
            f"{(proc.stderr or proc.stdout).strip()[:500]}"
        )
    msg = (proc.stderr or "").strip()
    log(f"  {msg}" if msg else "  Config saved.")


def open_browser(url, no_browser):
    if no_browser:
        print(f"\n  Open this URL in your browser:\n  {url}\n", flush=True)
        return
    for cmd in (["open", url], ["xdg-open", url]):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  Browser opened. If not, visit:\n  {url}\n", flush=True)
            return
        except Exception:
            continue
    print(f"  Could not open a browser. Visit:\n  {url}\n", flush=True)


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description="lark-cli app registration (no TTY)")
    ap.add_argument("--brand", choices=["feishu", "lark"], default="feishu")
    ap.add_argument("--no-browser", action="store_true", help="print URL, do not open")
    ap.add_argument(
        "--print-url-only",
        action="store_true",
        help="emit URL + device_code and exit without polling (agent split-flow)",
    )
    ap.add_argument("--device-code", default="", help="resume polling an existing code")
    ap.add_argument("--force", action="store_true", help="re-register even if configured")
    args = ap.parse_args()

    ws = detect_workspace()
    if ws != "local":
        print(
            f"[lark-setup] Agent workspace detected ({ws}).\n"
            f"  `config init` would create a parallel app here.\n"
            f"  Use instead:  lark-cli config bind --identity bot-only\n"
            f"  (ask the user to confirm identity preset before binding)",
            file=sys.stderr,
        )
        return 2

    # Idempotency gate -- the actual fix for repeated authorization prompts.
    if not args.force and not args.device_code:
        app_id = existing_app_id()
        if app_id:
            log(f"Already configured (appId={app_id}). Nothing to do.")
            log("Use --force to register a different app.")
            return 0

    # Resume path: caller already holds a device_code.
    if args.device_code:
        log(f"Resuming poll for device_code={args.device_code[:12]}...")
        app_id, app_secret, brand = poll_registration(
            args.device_code, args.brand, DEFAULT_POLL_INTERVAL, DEFAULT_EXPIRE_IN
        )
        log(f"Authorized. App ID: {app_id}")
        save_config(app_id, app_secret, brand)
        log(f"Done. brand={brand}. Verify with `lark-cli config show`.")
        return 0

    log(f"Starting app registration (brand={args.brand})")

    log("Step 1/3: requesting device code")
    reg = begin_registration()
    device_code = reg["device_code"]
    user_code = reg.get("user_code", "")
    # expire_in is the protocol field; expires_in is a legacy spelling.
    expire_in = int(reg.get("expire_in") or reg.get("expires_in") or DEFAULT_EXPIRE_IN)
    interval = int(reg.get("interval") or DEFAULT_POLL_INTERVAL)
    url = build_verification_url(args.brand, user_code)

    if args.print_url_only:
        print(
            json.dumps(
                {
                    "verification_url": url,
                    "device_code": device_code,
                    "user_code": user_code,
                    "expire_in": expire_in,
                    "interval": interval,
                    "resume_command": f"python3 lark_setup.py --device-code {device_code}",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    log("Step 2/3: opening browser for authorization")
    open_browser(url, args.no_browser)

    log("Step 3/3: polling until you finish in the browser")
    app_id, app_secret, brand = poll_registration(
        device_code, args.brand, interval, expire_in
    )
    log(f"Authorized. App ID: {app_id}")
    save_config(app_id, app_secret, brand)

    log("Done.")
    print(f"\n  App ID: {app_id}\n  Brand:  {brand}")
    print("\n  Verify:  lark-cli config show")
    print('  Next:    lark-cli auth login --scope "<only what the task needs>" --no-wait --json')
    print("           Prefer --scope over --domain: --domain base asks for 40 scopes,")
    print("           reading one table needs 3. Never open with --domain all.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[lark-setup] Cancelled.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[lark-setup] Error: {e}", file=sys.stderr)
        sys.exit(1)
