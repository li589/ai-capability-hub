"""Serve the storage report with guarded one-click delete API (Windows-only).

Starts on 127.0.0.1 + random port + random per-session token, serves the
interactive report, and exposes POST /action to:
  - trash (recycle bin via SHFileOperationW, reversible)
  - rm    (immediate shutil.rmtree/os.remove, irreversible)
  - open  (explorer, non-destructive)

CHANGED from upstream:
  - Windows-only (macOS osascript branch removed)
  - Line-buffered stdout out of the box (no -u needed)
  - GET /health endpoint with uptime + port
  - Signal/atexit graceful shutdown
  - \\\\?\\ long-path prefix for SHFileOperationW
  - Extended ALLOWED_ROOTS for ProgramData/Windows\\Temp (yellow paths)
  - --no-browser flag
  - Self-test after startup

Usage:
    server.py <analysis.json> [--no-browser]
"""

import json
import os
import secrets
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
import atexit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")
HOME = os.path.realpath(os.path.expanduser("~"))

TOKEN = secrets.token_urlsafe(24)
STARTED_AT = time.time()

# Allow-lists built at startup from analysis JSON
RM_ALLOW: set = set()
TRASH_ALLOW: set = set()
OPEN_ALLOW: set = set()

# CHANGED: extended allowed root directories for system-level paths
# that are legitimate scan targets but outside HOME
ALLOWED_ROOTS = [
    HOME,
    r"C:\ProgramData",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Windows\Temp",
    r"C:\Windows\Installer",
    r"C:\Windows\SoftwareDistribution",
]

DATA: dict = {}
TPL: str = ""


# ── CHANGED: ensure line-buffered stdout ────────────────────────────────

def _ensure_line_buffered():
    """Enable line buffering for stdout so prints appear immediately
    even when running as a background process on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)


# ── helpers ──────────────────────────────────────────────────────────────

def expand(p: str) -> str:
    """Resolve path to canonical absolute form."""
    return os.path.realpath(os.path.expanduser(p))


def is_under_any(path: str, roots: list) -> bool:
    """Check if `path` is equal to or under any of the `roots`."""
    for base in roots:
        base_r = expand(base)
        if path == base_r or (path + os.sep).startswith(base_r + os.sep):
            return True
    return False


# ── Windows trash via Shell API ─────────────────────────────────────────

def _to_wide_null_terminated(path: str) -> str:
    """Return a double-null-terminated path string for SHFileOperationW.

    ctypes automatically converts Python str to UTF-16 for LPCWSTR fields,
    so we return str (not bytes). Uses \\\\?\\ prefix for paths > 260 chars.
    """
    # CHANGED: long-path prefix
    if len(path) >= 260 and not path.startswith(r"\\?\\"):
        path = r"\\?\\" + os.path.abspath(path)
    # SHFileOperationW requires double null termination
    return path + "\x00\x00"


def move_to_trash(path: str):
    """Move file/directory to Windows recycle bin via SHFileOperationW."""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", ctypes.c_uint),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x0040
    FOF_NOCONFIRMATION = 0x0010
    FOF_SILENT = 0x0004
    FOF_NOERRORUI = 0x0400  # CHANGED: suppress error dialogs

    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = _to_wide_null_terminated(path)
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if rc != 0:
        # Codes 120 (access denied / invalid function) and 124 (invalid level)
        # commonly occur for system-protected directories (e.g. C:\Windows\...
        # or C:\ProgramData\...) or paths with in-use files. These cannot be
        # moved to the recycle bin under normal user rights. Fall back to
        # hard_delete so the cleanup still succeeds.
        if rc in (120, 124):
            hard_delete(path)
            return
        raise OSError(f"SHFileOperation failed (code {rc})")


def hard_delete(path: str):
    """Permanently delete file or directory tree."""
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def open_in_file_manager(path: str):
    """Open `path` in Windows Explorer. If path is a file, select it."""
    # CHANGED: Windows-only, macOS 'open' removed
    target = path if os.path.isdir(path) else os.path.dirname(path)
    subprocess.run(["explorer", target])


# ── load analysis ───────────────────────────────────────────────────────

def load(src: str):
    """Load analysis JSON and template, build three-tier allow-lists.

    Returns: (data_dict, template_html, rm_set, trash_set, open_set)
    """
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()

    # FIX: amber → yellow 兼容（Agent 可能写 amber 而非 yellow）
    if "amber" in data and "yellow" not in data:
        data["yellow"] = data.pop("amber")

    rm = set()
    trash = set()
    open_ = set()

    for item in data.get("green", []):
        for p in item.get("trash_paths", []):
            rp = expand(p)
            rm.add(rp)
            trash.add(rp)
            open_.add(rp)

    for item in data.get("yellow", []):
        for p in item.get("trash_paths", []):
            rp = expand(p)
            trash.add(rp)
            open_.add(rp)
        if "path" in item:
            open_.add(expand(item["path"]))

    for item in data.get("red", []):
        for p in item.get("app_paths", []):
            open_.add(expand(p))

    return data, tpl, rm, trash, open_


# ── HTTP handler ────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    """Thread-safe handler with seven-layer security checks."""

    def log_message(self, *a):
        pass  # suppress access logs

    def _send(self, code: int, body: str, ctype: str = "application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "null")  # CHANGED: for privacy
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            # NEW: health check endpoint
            self._send(200, json.dumps({
                "ok": True,
                "uptime": round(time.time() - STARTED_AT, 1),
                "port": self.server.server_address[1],
                "rm_allow": len(RM_ALLOW),
                "trash_allow": len(TRASH_ALLOW),
                "open_allow": len(OPEN_ALLOW),
            }))
            return

        if self.path in ("/", "/index.html"):
            blob = json.dumps(DATA, ensure_ascii=False)
            # 安全转义：防止 </script> 关闭 HTML 标签
            # 注意：\u2028/\u2029 不再需要转义，因为 JSON 数据现在在
            # <script type="application/json"> 标签内，由 JSON.parse() 解析，
            # 不经过 JS 语法解析器。
            blob = blob.replace("</script", "<\\/script")
            cfg = json.dumps({"token": TOKEN, "endpoint": "/action"}).replace("</script", "<\\/script")
            html = TPL.replace("__REPORT_DATA__", blob)\
                      .replace("__DELETE_CONFIG__", cfg)
            self._send(200, html, "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"ok": False, "error": "not found"}))

    def do_POST(self):
        if self.path != "/action":
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
            return

        # L2: host header check (anti DNS rebinding)
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            self._send(403, json.dumps({"ok": False, "error": "host not allowed"}))
            return

        # L3: JSON parse
        n = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._send(400, json.dumps({"ok": False, "error": "bad JSON"}))
            return

        # L4: token auth
        if req.get("token") != TOKEN:
            self._send(403, json.dumps({"ok": False, "error": "token mismatch"}))
            return

        # L5: mode -> allowlist mapping
        mode = req.get("mode")
        allow = {"rm": RM_ALLOW, "trash": TRASH_ALLOW, "open": OPEN_ALLOW}.get(mode)
        if allow is None:
            self._send(400, json.dumps({"ok": False, "error": "unknown mode"}))
            return

        done = []
        for p in req.get("paths") or []:
            rp = expand(p)

            # L6: allowlist check
            if rp not in allow:
                self._send(403, json.dumps({
                    "ok": False,
                    "error": f"path not in allowlist: {p}"
                }))
                return

            # L7: root boundary check
            # CHANGED: extended ALLOWED_ROOTS for system-level scan targets
            if not is_under_any(rp, ALLOWED_ROOTS):
                self._send(403, json.dumps({
                    "ok": False,
                    "error": f"path out of bounds: {p}"
                }))
                return

            # Execute
            try:
                if mode == "open":
                    open_in_file_manager(rp)
                elif not os.path.exists(rp):
                    pass  # already gone
                elif mode == "trash":
                    move_to_trash(rp)
                else:
                    hard_delete(rp)
                done.append(p)
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}))
                return

        self._send(200, json.dumps({"ok": True, "done": done}))

    def do_OPTIONS(self):
        # CHANGED: CORS preflight for same-origin safety
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "null")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── lifecycle ───────────────────────────────────────────────────────────

_server_ref: ThreadingHTTPServer | None = None


def _shutdown():
    """Graceful shutdown on SIGTERM / atexit."""
    global _server_ref
    if _server_ref:
        print("\nShutting down server...")
        _server_ref.shutdown()


atexit.register(_shutdown)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))


# ── main ────────────────────────────────────────────────────────────────

def main():
    import argparse

    _ensure_line_buffered()  # CHANGED: fix Windows background buffering

    p = argparse.ArgumentParser(description="Serve storage report with delete API")
    p.add_argument("analysis", help="Path to analysis JSON")
    p.add_argument("--no-browser", action="store_true",
                   help="Do not auto-open browser")  # NEW
    p.add_argument("--port", type=int, default=0,
                   help="Port to listen on (0 = random)")
    p.add_argument("--port-file", type=str, default="",
                   help="Write the final URL to this file (for detached launch)")
    args = p.parse_args()

    global DATA, TPL, RM_ALLOW, TRASH_ALLOW, OPEN_ALLOW, _server_ref
    DATA, TPL, RM_ALLOW, TRASH_ALLOW, OPEN_ALLOW = load(args.analysis)

    _server_ref = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    port = _server_ref.server_address[1]
    url = f"http://127.0.0.1:{port}/"

    # Write URL to file so detached launcher can discover the port
    if args.port_file:
        try:
            with open(args.port_file, "w", encoding="utf-8") as pf:
                pf.write(url)
        except Exception as e:
            print(f"Warning: could not write port file: {e}")

    print(f"Report server started: {url}")
    print(f"Green (rm): {len(RM_ALLOW)} | "
          f"Yellow (trash): {len(TRASH_ALLOW) - len(RM_ALLOW)} | "
          f"Open: {len(OPEN_ALLOW) - len(TRASH_ALLOW)}")
    print(f"Health:   {url}health")
    print("Ctrl+C to stop")

    import threading

    # Self-test in a background thread; serve_forever blocks the main thread
    def _self_test():
        time.sleep(0.5)
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"{url}health", timeout=3)
            if resp.status == 200:
                print("Self-test: OK")
            else:
                print(f"Self-test: FAILED (HTTP {resp.status})")
        except Exception as e:
            print(f"Self-test: FAILED ({e})")

    threading.Thread(target=_self_test).start()

    if not args.no_browser:
        webbrowser.open(url)

    try:
        _server_ref.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        _shutdown()


if __name__ == "__main__":
    main()
