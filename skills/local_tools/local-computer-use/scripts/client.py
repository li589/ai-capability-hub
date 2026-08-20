# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Short-lived CLI client for the luicore server.

Talks to ``release/server.py`` over the Windows named pipe
``\\\\.\\pipe\\luicore``. Starts a detached server in the background if one
is not already running.
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
from multiprocessing.connection import Client
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init
except ImportError:
    print("** Please run 'scripts\\install-env.ps1' to install the intel-luicore python environment firstly. **")
    sys.exit(1)

PIPE_ADDRESS = r"\\.\pipe\luicore"
AUTHKEY = b"luicore-local"
SKILL_NAME = "local-computer-use"
DOG_PIPE_ADDRESS = r"\\.\pipe\skill-server-dog"
DOG_AUTHKEY = b"skill-server-dog"
DOG_BOOT_TIMEOUT = 30.0
DOG_BOOT_POLL_INTERVAL = 0.3
SERVER_BOOT_TIMEOUT = 60.0
SERVER_BOOT_POLL_INTERVAL = 0.3
DEFAULT_SHUTDOWN_TIMEOUT = 10.0
OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
PENDING_REQUEST_PATH = OPENVINO_ROOT / "computer-use-pending-request.json"
TEMP_ROOT = OPENVINO_ROOT / "temp"
TEMP_DOG = TEMP_ROOT / "server-dog.py"
TEMP_GET_GPU_MEM = TEMP_ROOT / "get_gpu_mem.py"
TEMP_DIR = TEMP_ROOT / "computer-use"
TEMP_SERVER = TEMP_DIR / "server.py"
TEMP_MODEL_DOWNLOAD = TEMP_DIR / "model_download.py"
TEMP_INFO_JSON = TEMP_DIR / "info.json"
DOWNLOAD_WAIT_TIMEOUT = 9 * 60.0
STATUS_POLL_INTERVAL = 2.0
ERROR_RETRY_MAX = 3
ERROR_RETRY_GAP = 5.0
CLAW_MAP = {
    # Map unique substrings of skill root paths to their corresponding Claw executables, if any.
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
colorama_init()


def _normalize_log_path(log_path: str | None) -> Path | None:
    if not log_path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = f"~/.openvino/log/computer-use-client-py-{timestamp}.log"

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


def _save_pending_request(user_input: str, log_path: Path | None) -> None:
    try:
        PENDING_REQUEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "input": user_input,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "log_path": str(log_path) if log_path is not None else None,
        }
        PENDING_REQUEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _log_message(log_path, f"saved pending request to {PENDING_REQUEST_PATH}")
    except OSError as exc:
        _log_message(log_path, f"failed to save pending request: {exc}")


def _load_pending_request() -> dict | None:
    try:
        text = PENDING_REQUEST_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "input" not in data:
        return None
    return data


def _delete_pending_request(log_path: Path | None = None) -> None:
    try:
        PENDING_REQUEST_PATH.unlink()
        _log_message(log_path, f"deleted pending request at {PENDING_REQUEST_PATH}")
    except FileNotFoundError:
        pass
    except OSError as exc:
        _log_message(log_path, f"failed to delete pending request: {exc}")


def _try_connect():
    try:
        return Client(PIPE_ADDRESS, authkey=AUTHKEY)
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


def _get_windows_system_user_persistent_env() -> dict:
    """Get Windows system/user persistent environment variables from the registry."""
    env = {}
    if os.name != "nt":
        return env
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
            for i in range(0, winreg.QueryInfoKey(key)[1]):
                name, value, _ = winreg.EnumValue(key, i)
                env[name] = value

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            for i in range(0, winreg.QueryInfoKey(key)[1]):
                name, value, _ = winreg.EnumValue(key, i)
                if name.upper() == "PATH":
                    if name in env:
                        env[name] = env[name] + ";" + value
                    else:
                        env[name] = value
                else:
                    env[name] = value

        env_python = {
            k: v for k, v in os.environ.items() if k.startswith('PYTHON')
        }
        env.update(env_python)            
    except OSError:
        pass
    return env




def _detect_claw_name() -> str | None:
    skill_root = str(Path(__file__).resolve().parent.parent)
    for key, exe in CLAW_MAP.items():
        if key in skill_root:
            return exe
    return None


def _needs_sync(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    return not filecmp.cmp(str(src), str(dst), shallow=False)


def _terminate_legacy_dog(log_path: Path | None) -> None:
    """Kill any in-flight legacy per-skill server-dog from a previous release.

    The old per-skill dog was launched with `--claw-name <claw>` arguments;
    the new shared dog has no such argument. We use that to distinguish
    them since both occupy the same path on disk.
    """
    try:
        import psutil
    except ImportError:
        return
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            joined = [str(part).casefold() for part in cmdline]
            if "server-dog.py" in " ".join(joined) and any("--claw-name" in p for p in joined):
                proc.terminate()
                _log_message(log_path, f"terminated legacy dog pid={proc.info.get('pid')}")
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue


def _try_dog_connect():
    try:
        return Client(DOG_PIPE_ADDRESS, authkey=DOG_AUTHKEY)
    except (FileNotFoundError, OSError, EOFError):
        return None


def _spawn_dog(log_path: Path | None) -> None:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    env = {k: v for k, v in os.environ.items() if not (k.startswith("WORKBUDDY_") or k.startswith("CODEBUDDY_"))}
    subprocess.Popen(
        [_pythonw_executable(), str(TEMP_DOG)],
        creationflags=creationflags,
        startupinfo=_hidden_startupinfo(),
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(OPENVINO_ROOT),
        env=env,
    )
    _log_message(log_path, f"spawned shared server-dog: {TEMP_DOG}")


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
    skill_root = Path(__file__).resolve().parent.parent
    info_json = skill_root / "info.json"
    return json.loads(info_json.read_text(encoding="utf-8"))


def _request_server_start(dog_conn, log_path: Path | None) -> None:
    env = _read_info_json()
    venv_name = env.get("venv_name", "computer-use")
    mem_need_gb = float(env.get("mem_need_gb", 4.0))
    server_alive_timeout = env.get("server_alive_timeout", 300)
    venv_python = str(
        Path(os.environ.get("USERPROFILE", str(Path.home())))
        / ".openvino" / "venv" / venv_name / "Scripts" / "pythonw.exe"
    )
    payload = {
        "op": "start_server",
        "skill_name": SKILL_NAME,
        "server_path": str(TEMP_SERVER),
        "venv_python": venv_python,
        "pipe_address": PIPE_ADDRESS,
        "authkey": AUTHKEY.decode("latin-1"),
        "mem_need_gb": mem_need_gb,
        "server_alive_timeout": server_alive_timeout,
        "claw_name": _detect_claw_name(),
    }
    _log_message(log_path, f"start_server -> dog (mem_need_gb={mem_need_gb})")
    reply: dict | None = None
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


def _send_keepalive(dog_conn, log_path: Path | None) -> None:
    try:
        dog_conn.send({"op": "keepalive", "skill_name": SKILL_NAME})
        try:
            dog_conn.recv()
        except Exception:
            pass
    except Exception as exc:
        _log_message(log_path, f"keepalive failed: {exc}")
    finally:
        try:
            dog_conn.close()
        except Exception:
            pass


def _sync_runtime_scripts(log_path: Path | None) -> None:
    src_server = Path(__file__).with_name("server.py")
    src_model_download = Path(__file__).with_name("model_download.py")
    src_info_json = Path(__file__).resolve().parent.parent / "info.json"
    src_dog = Path(__file__).with_name("server-dog.py")
    src_get_gpu_mem = Path(__file__).with_name("get_gpu_mem.py")
    runtime_scripts = [
        (src_server, TEMP_SERVER),
        (src_model_download, TEMP_MODEL_DOWNLOAD),
        (src_info_json, TEMP_INFO_JSON),
        (src_dog, TEMP_DOG),
        (src_get_gpu_mem, TEMP_GET_GPU_MEM),
    ]
    if not any(_needs_sync(src, dst) for src, dst in runtime_scripts):
        return

    _log_message(log_path, "runtime scripts outdated; refreshing")
    if _try_connect() is not None:
        _log_message(log_path, "shutting down existing server before refresh")
        _cmd_shutdown(DEFAULT_SHUTDOWN_TIMEOUT, log_path)
        deadline = time.time() + DEFAULT_SHUTDOWN_TIMEOUT
        while time.time() < deadline and _try_connect() is not None:
            time.sleep(0.2)
    _terminate_legacy_dog(log_path)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    for src, dst in runtime_scripts:
        last_err: Exception | None = None
        for _ in range(5):
            try:
                shutil.copy2(src, dst)
                last_err = None
                break
            except PermissionError as exc:
                last_err = exc
                time.sleep(0.3)
        if last_err is not None:
            raise RuntimeError(f"failed to update {dst} (still in use): {last_err}")
    _log_message(log_path, f"refreshed runtime scripts under {TEMP_ROOT}")


def _ensure_server(log_path: Path | None = None):
    _sync_runtime_scripts(log_path)
    conn = _try_connect()
    if conn is not None:
        _log_message(log_path, "connected to existing server")
        ka = _try_dog_connect()
        if ka is not None:
            _send_keepalive(ka, log_path)
        return conn
    _log_message(log_path, "server not running; asking dog to start it")
    dog = _ensure_dog(log_path)
    _request_server_start(dog, log_path)
    deadline = time.time() + SERVER_BOOT_TIMEOUT
    while time.time() < deadline:
        conn = _try_connect()
        if conn is not None:
            _log_message(log_path, "background server became ready")
            return conn
        time.sleep(SERVER_BOOT_POLL_INTERVAL)
    raise RuntimeError(f"luicore server did not come up within {SERVER_BOOT_TIMEOUT:.0f}s")


def _wait_for_running(log_path: Path | None, deadline: float) -> tuple[str, str]:
    """Poll server status until it reaches 'running', 'error', or the deadline.

    Returns (outcome, detail) where outcome ∈ {"running", "error", "timeout"}.
    """
    while True:
        now = time.time()
        if now >= deadline:
            _log_message(log_path, "wait_for_running: timed out")
            return ("timeout", "")
        conn = _try_connect()
        if conn is None:
            _log_message(log_path, "wait_for_running: no server; ensuring")
            try:
                _ensure_server(log_path)
            except RuntimeError as exc:
                return ("error", str(exc))
            time.sleep(STATUS_POLL_INTERVAL)
            continue
        reply = _send(conn, {"op": "status"}, log_path)
        state = reply.get("state") if isinstance(reply, dict) else None
        _log_message(log_path, f"wait_for_running: state={state}")
        if state == "running":
            return ("running", "")
        if state == "error":
            return ("error", reply.get("error", "<unknown init error>"))
        remaining = deadline - time.time()
        if remaining <= 0:
            return ("timeout", "")
        time.sleep(min(STATUS_POLL_INTERVAL, remaining))


def _send(conn, msg: dict, log_path: Path | None = None) -> dict:
    payload = dict(msg)
    _log_message(log_path, f"sending op={payload.get('op')!r}")
    try:
        conn.send(payload)
        reply = conn.recv()
    finally:
        conn.close()
    if isinstance(reply, dict):
        _log_message(log_path, f"received reply for op={payload.get('op')!r}: ok={reply.get('ok')}")
    else:
        _log_message(log_path, f"received non-dict reply for op={payload.get('op')!r}")
    return reply


def _format_extra_info(t: dict, s:dict) -> str:
    return (
        f"耗时: {t.get('total', 0.0):.3f} 秒, "
        f"节省token: {s.get('input_tokens', 0)+s.get('output_tokens', 0)} "
    )


def _print_request_reply(reply: dict) -> int:
    if not reply.get("ok", False):
        print(Fore.RED + "❌ 处理失败:" + Style.RESET_ALL)
        print(reply.get("error", "<unknown error>"))
        return 1

    for msg in reply.get("messages", []):
        print(Style.BRIGHT + Fore.BLUE + json.dumps(msg, indent=4, ensure_ascii=False) + Style.RESET_ALL)
    
    print(_format_extra_info(reply.get("timing", {}), reply.get("local_tokens", {})))
    return 0 if reply.get("success") else 1


def _cmd_status(log_path: Path | None = None) -> int:
    _log_message(log_path, "checking server status")
    conn = _try_connect()
    if conn is None:
        _log_message(log_path, "status check: server not running")
        print("server not running")
        return 0
    reply = _send(conn, {"op": "status"}, log_path)
    if not reply.get("ok", False):
        _log_message(log_path, f"status failed: {reply.get('error', '<unknown>')}")
        print(Fore.RED + "status failed:" + Style.RESET_ALL, reply.get("error", "<unknown>"))
        return 1
    _log_message(log_path, f"status ok: pid={reply.get('pid')} version={reply.get('luicore_version')}")
    print(
        f"state:   {reply.get('state')}\n"
        f"pid:     {reply.get('pid')}\n"
        f"uptime:  {reply.get('uptime_s', 0.0):.1f}s\n"
        f"version: {reply.get('luicore_version')}"
    )
    return 0


def _cmd_shutdown(timeout: float, log_path: Path | None = None) -> int:
    _log_message(log_path, f"requesting server shutdown with timeout={timeout:.1f}s")
    conn = _try_connect()
    if conn is None:
        _log_message(log_path, "shutdown request skipped: server not running")
        print("server not running")
        return 0
    reply = _send(conn, {"op": "shutdown", "timeout": timeout}, log_path)
    if not reply.get("ok", False):
        _log_message(log_path, f"shutdown failed: {reply.get('error', '<unknown>')}")
        print(Fore.RED + "shutdown failed:" + Style.RESET_ALL, reply.get("error", "<unknown>"))
        return 1
    _log_message(log_path, "shutdown request accepted by server")
    print(f"server shutting down (grace period: {timeout:.1f}s)")
    return 0


def _cmd_request(user_input: str, log_path: Path | None = None) -> int:
    cases = [c for c in user_input.split(";") if c.strip()]
    if not cases:
        cases = [user_input]

    _log_message(log_path, f"processing {len(cases)} request case(s)")

    deadline = time.time() + DOWNLOAD_WAIT_TIMEOUT
    try:
        _ensure_server(log_path)
    except RuntimeError as exc:
        _log_message(log_path, f"failed to ensure server: {exc}")
        print(Fore.RED + str(exc) + Style.RESET_ALL)
        return 2

    outcome, detail = _wait_for_running(log_path, deadline)
    for attempt in range(2, ERROR_RETRY_MAX + 1):
        if outcome != "error":
            break
        _log_message(
            log_path,
            f"init error on attempt {attempt - 1}/{ERROR_RETRY_MAX}; restarting server: {detail}",
        )
        print(Fore.YELLOW + f"server init failed (attempt {attempt - 1}/{ERROR_RETRY_MAX}), restarting..." + Style.RESET_ALL)
        _cmd_shutdown(DEFAULT_SHUTDOWN_TIMEOUT, log_path)
        pipe_deadline = min(time.time() + 5.0, deadline)
        while time.time() < pipe_deadline and _try_connect() is not None:
            time.sleep(0.2)
        if time.time() >= deadline:
            outcome = "timeout"
            break
        time.sleep(min(ERROR_RETRY_GAP, max(0.0, deadline - time.time())))
        if time.time() >= deadline:
            outcome = "timeout"
            break
        try:
            _ensure_server(log_path)
        except RuntimeError as exc:
            outcome, detail = "error", str(exc)
            continue
        outcome, detail = _wait_for_running(log_path, deadline)

    if outcome == "timeout":
        _save_pending_request(user_input, log_path)
        print(Fore.YELLOW + "模型正在下载, 请用命令`scripts\\run.ps1 --continue`继续运行" + Style.RESET_ALL)
        _log_message(log_path, "exiting with code 3: download still in progress")
        return 3

    if outcome == "error":
        _log_message(log_path, f"server reports init error after retries: {detail}")
        print(Fore.RED + "❌ 服务器初始化失败:" + Style.RESET_ALL)
        print(detail)
        _delete_pending_request(log_path)
        return 1

    # outcome == "running"
    try:
        conn = _try_connect()
        if conn is None:
            _log_message(log_path, "connection to server lost immediately after ready state")
            print(Fore.RED + "lost connection to server" + Style.RESET_ALL)
            return 2
        _log_message(log_path, f"request[1]={cases[0]}")
        rc = _print_request_reply(_send(conn, {"op": "request", "input": cases[0]}, log_path))
        _log_message(log_path, f"request[1] exit_code={rc}")
        for index, case in enumerate(cases[1:], start=2):
            conn = _try_connect()
            if conn is None:
                _log_message(log_path, "lost connection to server before sending follow-up request")
                print(Fore.RED + "lost connection to server" + Style.RESET_ALL)
                rc = rc or 2
                break
            _log_message(log_path, f"request[{index}]={case}")
            rc = _print_request_reply(_send(conn, {"op": "request", "input": case}, log_path)) or rc
            _log_message(log_path, f"request[{index}] cumulative_exit_code={rc}")
    finally:
        _delete_pending_request(log_path)
    return rc


def _cmd_continue(log_path: Path | None = None) -> int:
    pending = _load_pending_request()
    if pending is None:
        _log_message(log_path, "--continue invoked but no pending request file found")
        print(Fore.RED + "无待处理请求, 请先使用 `scripts\\run.ps1 \"<instruction>\"` 发起请求" + Style.RESET_ALL)
        return 1
    saved_input = pending.get("input", "")
    saved_log = _normalize_log_path(pending.get("log_path")) or log_path
    _log_message(saved_log, f"--continue resuming input={saved_input!r}")
    return _cmd_request(saved_input, saved_log)


def main() -> int:
    parser = argparse.ArgumentParser(description="luicore CLI client")
    parser.add_argument(
        "-i", "--input",
        type=str, default=None,
        help="user instruction (use ';' to separate multiple cases)",
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="append debug logs to this file",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--server-status", action="store_true", help="query server status")
    group.add_argument("--server-shutdown", action="store_true", help="request server shutdown")
    group.add_argument(
        "--continue",
        dest="cont",
        action="store_true",
        help="resume the last pending request (used after a download timeout exit)",
    )
    parser.add_argument(
        "--server-shutdown-timeout",
        type=float, default=DEFAULT_SHUTDOWN_TIMEOUT,
        help=f"grace period for in-flight work on shutdown (default: {DEFAULT_SHUTDOWN_TIMEOUT:.0f}s)",
    )
    args = parser.parse_args()
    log_path = _normalize_log_path(args.log)

    if log_path is not None:
        _log_message(log_path, f"client started with argv={sys.argv[1:]}")

    if args.server_status:
        exit_code = _cmd_status(log_path)
    elif args.server_shutdown:
        exit_code = _cmd_shutdown(args.server_shutdown_timeout, log_path)
    elif args.cont:
        exit_code = _cmd_continue(log_path)
    else:
        user_input = args.input if args.input is not None else "查询电脑制造日期"
        exit_code = _cmd_request(user_input, log_path)

    _log_message(log_path, f"client exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
