# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Short-lived CLI controller for the local-realtime-translator server.

This skill is interactive and long-running: the server boots a full
microphone -> ASR -> translation -> TTS pipeline and serves a web UI. The
client's job is therefore NOT to fetch a one-shot result, but to *control*
that server:

    --start        ensure the pipeline server is up, print the web UI URL
    --status       report server state (and web URL once running)
    --stop         shut the server down (releases mic + GPU memory)
    --continue     resume waiting for a first-run model download

It talks to ``server.py`` over the Windows named pipe
``\\\\.\\pipe\\local-realtime-translator`` and uses the shared
``server-dog`` to spawn / lifecycle-manage that server.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from multiprocessing.connection import Client
from pathlib import Path

PIPE_ADDRESS = r"\\.\pipe\local-realtime-translator"
AUTHKEY = b"local-realtime-translator"
SKILL_NAME = "local-realtime-translator"
STATE_RUNNING_STR = "running"

DOG_PIPE_ADDRESS = r"\\.\pipe\skill-server-dog"
DOG_AUTHKEY = b"skill-server-dog"
DOG_BOOT_TIMEOUT = 30.0
DOG_BOOT_POLL_INTERVAL = 0.3
SERVER_BOOT_TIMEOUT = 60.0
SERVER_BOOT_POLL_INTERVAL = 0.3
DEFAULT_SHUTDOWN_TIMEOUT = 10.0

OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
PENDING_REQUEST_PATH = OPENVINO_ROOT / "rt-translator-pending-request.json"
# server-dog is a machine-wide singleton (one dog brokers ALL skills' servers
# with cross-skill memory eviction), so it + get_gpu_mem.py live at the canonical
# shared temp root — NOT a per-skill subdir. The skill's own server tree goes
# under TEMP_DIR (temp/local-realtime-translator/). See
# docs/superpowers/specs/2026-05-26-shared-server-dog-design.md.
TEMP_ROOT = OPENVINO_ROOT / "temp"
TEMP_DOG = TEMP_ROOT / "server-dog.py"
TEMP_GET_GPU_MEM = TEMP_ROOT / "get_gpu_mem.py"
TEMP_DIR = TEMP_ROOT / "local-realtime-translator"
TEMP_SCRIPTS = TEMP_DIR / "scripts"
TEMP_SERVER = TEMP_SCRIPTS / "server.py"
LEGACY_TEMP_SERVER_DOG = TEMP_DIR / "server-dog.py"

# Each run.ps1 invocation is capped below 10 min by the harness; leave headroom.
DOWNLOAD_WAIT_TIMEOUT = 9 * 60.0
STATUS_POLL_INTERVAL = 2.0

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
# Launch the server + dog from the temp copy (see _sync_runtime_scripts), so a
# skill upgrade can refresh on-disk scripts without disturbing a running server.
SERVER_PATH = TEMP_SERVER
DOG_PATH = TEMP_DOG

CLAW_MAP = {
    ".workbuddy": "WorkBuddy.exe",
    ".openclaw": "openclaw.mjs",
    "Marvis": "Marvis.exe",
    ".trae-cn": "TRAE SOLO CN.exe",
    "Coze": "Coze.exe",
}


def _configure_stream_encoding(stream) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


_configure_stream_encoding(sys.stdout)
_configure_stream_encoding(sys.stderr)


def _normalize_log_path(log_path: str | None) -> Path | None:
    if not log_path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = f"~/.openvino/log/rt-translator-client-py-{timestamp}.log"
    path = Path(log_path).expanduser()
    return path if path.is_absolute() else Path.cwd() / path


def _log_message(log_path: Path | None, message: str) -> None:
    if log_path is None:
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as stream:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            stream.write(f"[{timestamp}] [client pid={os.getpid()}] {message}\n")
    except OSError:
        pass


# ── pending-request (for --continue resume) ───────────────────────────
def _save_pending_request(src_lang: str, tgt_lang: str, log_path: Path | None) -> None:
    try:
        PENDING_REQUEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "log_path": str(log_path) if log_path is not None else None,
        }
        PENDING_REQUEST_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        _log_message(log_path, f"failed to save pending request: {exc}")


def _load_pending_request() -> dict | None:
    try:
        data = json.loads(PENDING_REQUEST_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _delete_pending_request(log_path: Path | None = None) -> None:
    try:
        PENDING_REQUEST_PATH.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        _log_message(log_path, f"failed to delete pending request: {exc}")


# ── pipe helpers ───────────────────────────────────────────────────────
def _try_connect():
    try:
        return Client(PIPE_ADDRESS, authkey=AUTHKEY)
    except (FileNotFoundError, OSError, EOFError):
        return None


def _try_dog_connect():
    try:
        return Client(DOG_PIPE_ADDRESS, authkey=DOG_AUTHKEY)
    except (FileNotFoundError, OSError, EOFError):
        return None


def _hidden_startupinfo():
    if os.name != "nt" or not hasattr(subprocess, "STARTUPINFO"):
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return startupinfo


def _pythonw_executable() -> str:
    python_exe = Path(sys.executable)
    pythonw_exe = python_exe.with_name("pythonw.exe")
    return str(pythonw_exe) if pythonw_exe.exists() else str(python_exe)


def _detect_claw_name() -> str | None:
    skill_root = str(_SKILL_ROOT)
    for key, exe in CLAW_MAP.items():
        if key in skill_root:
            return exe
    return None


def _needs_sync(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    return not filecmp.cmp(str(src), str(dst), shallow=False)


def _dircmp_differs(cmp: filecmp.dircmp) -> bool:
    if cmp.left_only or cmp.diff_files or cmp.funny_files:
        return True
    return any(_dircmp_differs(sub) for sub in cmp.subdirs.values())


def _dir_needs_sync(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    return _dircmp_differs(filecmp.dircmp(str(src), str(dst), ignore=["__pycache__"]))


def _copy_tree(src: Path, dst: Path, log_path: Path | None) -> None:
    """Replace dst with a fresh copy of src (ignoring __pycache__), retrying on
    transient Windows file locks."""
    last_err: Exception | None = None
    for _ in range(5):
        try:
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            last_err = None
            break
        except (PermissionError, OSError) as exc:
            last_err = exc
            time.sleep(0.3)
    if last_err is not None:
        raise RuntimeError(f"failed to copy tree to {dst} (still in use): {last_err}")
    _log_message(log_path, f"refreshed tree under {dst}")


def _terminate_legacy_dog(log_path: Path | None) -> None:
    """Kill any in-flight legacy per-skill server-dog from a previous release."""
    try:
        import psutil
    except ImportError:
        return
    target = str(LEGACY_TEMP_SERVER_DOG).casefold()
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if any(target in str(part).casefold() for part in cmdline):
                proc.terminate()
                _log_message(log_path, f"terminated legacy dog pid={proc.info.get('pid')}")
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue


def _sync_runtime_scripts(log_path: Path | None) -> None:
    """Copy server.py and everything it imports into TEMP_DIR, so the server
    runs from a stable location across skill upgrades.

    Flat files -> TEMP_SCRIPTS; package/data dirs + skill-root modules -> TEMP_DIR;
    shared dog + gpu probe -> TEMP_ROOT.
    """
    src_scripts = _HERE
    flat_files = [
        (src_scripts / "server.py", TEMP_SERVER),
        (src_scripts / "model_download.py", TEMP_SCRIPTS / "model_download.py"),
        (src_scripts / "ensure_models.py", TEMP_SCRIPTS / "ensure_models.py"),
        (src_scripts / "server-dog.py", TEMP_DOG),
        (src_scripts / "get_gpu_mem.py", TEMP_GET_GPU_MEM),
    ]
    root_files = [
        (_SKILL_ROOT / "config.py", TEMP_DIR / "config.py"),
        (_SKILL_ROOT / "melo_hf_bridge.py", TEMP_DIR / "melo_hf_bridge.py"),
        (_SKILL_ROOT / "info.json", TEMP_DIR / "info.json"),
    ]
    tree_dirs = [
        (_SKILL_ROOT / "translator", TEMP_DIR / "translator"),
        (_SKILL_ROOT / "nltk_data", TEMP_DIR / "nltk_data"),
        (_SKILL_ROOT / "bin", TEMP_DIR / "bin"),
    ]

    files = flat_files + root_files
    trees_outdated = any(_dir_needs_sync(s, d) for s, d in tree_dirs)
    files_outdated = any(_needs_sync(s, d) for s, d in files)
    if not trees_outdated and not files_outdated:
        return

    _log_message(log_path, "runtime tree outdated; refreshing")
    if _try_connect() is not None:
        _log_message(log_path, "shutting down existing server before refresh")
        _cmd_shutdown(DEFAULT_SHUTDOWN_TIMEOUT, log_path)
        deadline = time.time() + DEFAULT_SHUTDOWN_TIMEOUT
        while time.time() < deadline and _try_connect() is not None:
            time.sleep(0.2)
    _terminate_legacy_dog(log_path)

    TEMP_SCRIPTS.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    for src, dst in files:
        last_err: Exception | None = None
        for _ in range(5):
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                last_err = None
                break
            except PermissionError as exc:
                last_err = exc
                time.sleep(0.3)
        if last_err is not None:
            raise RuntimeError(f"failed to update {dst} (still in use): {last_err}")
    for src, dst in tree_dirs:
        if _dir_needs_sync(src, dst):
            _copy_tree(src, dst, log_path)
    _log_message(log_path, f"refreshed runtime tree under {TEMP_DIR}")


def _spawn_dog(log_path: Path | None) -> None:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("WORKBUDDY_") or k.startswith("CODEBUDDY_"))}
    OPENVINO_ROOT.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [_pythonw_executable(), str(DOG_PATH)],
        creationflags=creationflags,
        startupinfo=_hidden_startupinfo(),
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(OPENVINO_ROOT),
        env=env,
    )
    _log_message(log_path, f"spawned server-dog: {DOG_PATH}")


def _ensure_dog(log_path: Path | None):
    conn = _try_dog_connect()
    if conn is not None:
        return conn
    _spawn_dog(log_path)
    deadline = time.time() + DOG_BOOT_TIMEOUT
    while time.time() < deadline:
        conn = _try_dog_connect()
        if conn is not None:
            return conn
        time.sleep(DOG_BOOT_POLL_INTERVAL)
    raise RuntimeError("server-dog did not start")


def _read_info_json() -> dict:
    return json.loads((_SKILL_ROOT / "info.json").read_text(encoding="utf-8"))


def _request_server_start(dog_conn, src_lang: str, tgt_lang: str, log_path: Path | None) -> None:
    info = _read_info_json()
    venv_name = info.get("venv_name", "rt-translator")
    mem_need_gb = float(info.get("mem_need_gb", 6.0))
    server_alive_timeout = info.get("server_alive_timeout", -1)
    venv_python = str(
        OPENVINO_ROOT / "venv" / venv_name / "Scripts" / "pythonw.exe"
    )
    payload = {
        "op": "start_server",
        "skill_name": SKILL_NAME,
        "server_path": str(SERVER_PATH),
        "venv_python": venv_python,
        "pipe_address": PIPE_ADDRESS,
        "authkey": AUTHKEY.decode("latin-1"),
        "mem_need_gb": mem_need_gb,
        "server_alive_timeout": server_alive_timeout,
        "claw_name": _detect_claw_name(),
        "extra_env": {
            "RT_SRC_LANG": src_lang,
            "RT_TGT_LANG": tgt_lang,
            "OPENVINO_TELEMETRY_OPT_OUT": "1",
        },
    }
    _log_message(log_path, f"start_server -> dog (mem_need_gb={mem_need_gb})")
    reply = None
    try:
        dog_conn.send(payload)
        reply = dog_conn.recv()
    finally:
        try:
            dog_conn.close()
        except Exception:
            pass
    if not isinstance(reply, dict) or not reply.get("ok"):
        err = (reply or {}).get("error", "<unknown>")
        if err == "not_enough_memory":
            print("系统资源不足, 无法启动该技能", file=sys.stderr)
        raise RuntimeError(f"start_server failed: {err}")
    _log_message(log_path, f"dog spawned server pid={reply.get('pid')}")


def _send(conn, msg: dict, log_path: Path | None = None) -> dict:
    try:
        conn.send(dict(msg))
        reply = conn.recv()
    finally:
        conn.close()
    return reply if isinstance(reply, dict) else {}


def _ensure_server(src_lang: str, tgt_lang: str, log_path: Path | None):
    _sync_runtime_scripts(log_path)
    conn = _try_connect()
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        return
    _log_message(log_path, "server not running; asking dog to start it")
    dog = _ensure_dog(log_path)
    _request_server_start(dog, src_lang, tgt_lang, log_path)
    deadline = time.time() + SERVER_BOOT_TIMEOUT
    while time.time() < deadline:
        conn = _try_connect()
        if conn is not None:
            conn.close()
            return
        time.sleep(SERVER_BOOT_POLL_INTERVAL)
    raise RuntimeError(f"server did not come up within {SERVER_BOOT_TIMEOUT:.0f}s")


def _wait_for_running(log_path: Path | None, deadline: float) -> tuple[str, dict]:
    last_reply: dict = {}
    while True:
        if time.time() >= deadline:
            return ("timeout", last_reply)
        conn = _try_connect()
        if conn is None:
            time.sleep(STATUS_POLL_INTERVAL)
            continue
        reply = _send(conn, {"op": "status"}, log_path)
        last_reply = reply
        state = reply.get("state")
        _log_message(log_path, f"wait_for_running: state={state}")
        if state == STATE_RUNNING_STR:
            return ("running", reply)
        if state == "error":
            return ("error", reply)
        remaining = deadline - time.time()
        if remaining <= 0:
            return ("timeout", last_reply)
        time.sleep(min(STATUS_POLL_INTERVAL, remaining))


def _open_browser(reply: dict, log_path: Path | None) -> None:
    """Open the web UI in the default browser once the server is running."""
    web_url = reply.get("web_url")
    if not web_url:
        return
    try:
        webbrowser.open(web_url)
        _log_message(log_path, f"opened browser at {web_url}")
    except Exception as exc:  # never let browser launch failure break the flow
        _log_message(log_path, f"failed to open browser: {exc}")


def _print_running(reply: dict) -> None:
    web_url = reply.get("web_url")
    ws_url = reply.get("ws_url")
    src = reply.get("src_lang", "zh")
    tgt = reply.get("tgt_lang", "en")
    print("\n=== 实时语音翻译已就绪 / Realtime translator ready ===")
    print(f"  翻译方向 / direction: {src} → {tgt}")
    if web_url:
        print(f"  已自动打开浏览器, 如未打开请手动访问 / Browser opened; if not, visit:  {web_url}")
    if ws_url:
        print(f"  WebSocket: {ws_url}")
    print("  对着麦克风说话, 网页上会实时显示识别与译文。")
    print("  Speak into the microphone; the web page shows live transcript + translation.")
    print("  停止服务 / stop:  scripts\\run.ps1 --stop")


# ── commands ───────────────────────────────────────────────────────────
def _cmd_start(src_lang: str, tgt_lang: str, log_path: Path | None) -> int:
    deadline = time.time() + DOWNLOAD_WAIT_TIMEOUT
    try:
        _ensure_server(src_lang, tgt_lang, log_path)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    outcome, reply = _wait_for_running(log_path, deadline)

    if outcome == "timeout":
        _save_pending_request(src_lang, tgt_lang, log_path)
        print("模型正在下载, 请用命令 `scripts\\run.ps1 --continue` 继续运行")
        return 3
    if outcome == "error":
        print("[ERROR] 服务初始化失败 / Server initialization failed:", file=sys.stderr)
        print(reply.get("error", "<unknown init error>"), file=sys.stderr)
        _delete_pending_request(log_path)
        return 1

    _delete_pending_request(log_path)
    _print_running(reply)
    _open_browser(reply, log_path)
    return 0


def _cmd_continue(log_path: Path | None) -> int:
    pending = _load_pending_request()
    if pending is None:
        print("无待处理请求, 请先使用 `scripts\\run.ps1` 启动服务", file=sys.stderr)
        return 1
    src_lang = pending.get("src_lang", "zh")
    tgt_lang = pending.get("tgt_lang", "en")
    saved_log = pending.get("log_path")
    if saved_log:
        log_path = _normalize_log_path(saved_log)
    return _cmd_start(src_lang, tgt_lang, log_path)


def _cmd_status(log_path: Path | None) -> int:
    conn = _try_connect()
    if conn is None:
        print("server not running")
        return 0
    reply = _send(conn, {"op": "status"}, log_path)
    state = reply.get("state")
    print(
        f"state:   {state}\n"
        f"pid:     {reply.get('pid')}\n"
        f"uptime:  {reply.get('uptime_s', 0.0):.1f}s\n"
        f"web_url: {reply.get('web_url')}"
    )
    if state == STATE_RUNNING_STR:
        _print_running(reply)
    return 0


def _cmd_shutdown(timeout: float, log_path: Path | None) -> int:
    conn = _try_connect()
    if conn is None:
        print("server not running")
        return 0
    reply = _send(conn, {"op": "shutdown", "timeout": timeout}, log_path)
    if not reply.get("ok", False):
        print(f"shutdown failed: {reply.get('error', '<unknown>')}", file=sys.stderr)
        return 1
    print(f"server shutting down (grace period: {timeout:.1f}s)")
    return 0


def _wait_for_server_gone(deadline: float, log_path: Path | None) -> bool:
    """Poll until the server pipe stops answering (the old server has exited).

    Returns True once nothing is listening on the pipe, False if the deadline
    passes while a server is still reachable. A restart must wait for this:
    the new server binds the same WS/HTTP ports and pipe, so starting it before
    the old one releases them trips _check_port_free in ws_server.
    """
    while time.time() < deadline:
        conn = _try_connect()
        if conn is None:
            return True
        try:
            conn.close()
        except Exception:
            pass
        time.sleep(SERVER_BOOT_POLL_INTERVAL)
    return False


def _cmd_restart(src_lang: str, tgt_lang: str, timeout: float,
                 log_path: Path | None) -> int:
    """Force a clean restart: shut any running server down, wait for it to
    fully exit (freeing pipe + ports), then start fresh.

    Unlike the default start — which reuses a live server and so keeps running
    stale code after an upgrade — this guarantees the freshly-installed scripts
    are the ones loaded. Costs a full model reload (cold start).
    """
    conn = _try_connect()
    if conn is None:
        print("server not running; starting fresh")
        return _cmd_start(src_lang, tgt_lang, log_path)

    reply = _send(conn, {"op": "shutdown", "timeout": timeout}, log_path)
    if not reply.get("ok", False):
        print(f"shutdown failed: {reply.get('error', '<unknown>')}", file=sys.stderr)
        return 1
    print(f"restarting: old server shutting down (grace period: {timeout:.1f}s)...")

    # Give the old server the full grace period plus a margin to release the
    # pipe and the WS/HTTP ports before the new one tries to bind them.
    gone = _wait_for_server_gone(time.time() + timeout + 5.0, log_path)
    if not gone:
        print("[ERROR] old server did not exit in time; aborting restart "
              "(try `scripts\\run.ps1 --stop` then start again)", file=sys.stderr)
        return 1
    _log_message(log_path, "old server gone; starting fresh")
    return _cmd_start(src_lang, tgt_lang, log_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="local-realtime-translator CLI controller")
    parser.add_argument("--from", dest="src_lang", default="zh", choices=["zh", "en"])
    parser.add_argument("--to", dest="tgt_lang", default="en", choices=["zh", "en"])
    parser.add_argument("--log", type=str, default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--server-status", action="store_true")
    group.add_argument("--server-shutdown", action="store_true")
    group.add_argument("--continue", dest="cont", action="store_true")
    group.add_argument("--restart", action="store_true")
    parser.add_argument("--server-shutdown-timeout", type=float, default=DEFAULT_SHUTDOWN_TIMEOUT)
    args = parser.parse_args()
    log_path = _normalize_log_path(args.log)

    if args.server_status:
        return _cmd_status(log_path)
    if args.server_shutdown:
        return _cmd_shutdown(args.server_shutdown_timeout, log_path)
    if args.cont:
        return _cmd_continue(log_path)
    if args.restart:
        return _cmd_restart(args.src_lang, args.tgt_lang,
                            args.server_shutdown_timeout, log_path)
    return _cmd_start(args.src_lang, args.tgt_lang, log_path)


if __name__ == "__main__":
    sys.exit(main())
