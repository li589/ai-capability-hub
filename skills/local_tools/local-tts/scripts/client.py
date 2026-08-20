"""Short-lived CLI client for the local-tts server.

Talks to ``server.py`` over the Windows named pipe ``\\\\.\\pipe\\tts``.
Starts a detached server in the background if one is not already running.

Same ``--continue`` / pending-request protocol as local-txt2img: when the
first run needs to download the model, the request is persisted and the
caller re-invokes with ``--continue`` until the model is ready.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from multiprocessing.connection import Client
from pathlib import Path

import psutil

try:
    from colorama import Fore, Style, init as colorama_init
except ImportError:
    print("** Please run 'scripts\\install-env.ps1' to install the local-tts python environment firstly. **")
    sys.exit(1)

PIPE_ADDRESS = r"\\.\pipe\tts"
AUTHKEY = b"tts-local"
SKILL_NAME = "local-tts"
DOG_PIPE_ADDRESS = r"\\.\pipe\skill-server-dog"
DOG_AUTHKEY = b"skill-server-dog"
DOG_BOOT_TIMEOUT = 30.0
DOG_BOOT_POLL_INTERVAL = 0.3
SERVER_BOOT_TIMEOUT = 60.0
SERVER_BOOT_POLL_INTERVAL = 0.3
DEFAULT_SHUTDOWN_TIMEOUT = 10.0
OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
PENDING_REQUEST_PATH = OPENVINO_ROOT / "tts-pending-request.json"
TEMP_ROOT = OPENVINO_ROOT / "temp"
TEMP_DOG = TEMP_ROOT / "server-dog.py"
TEMP_GET_GPU_MEM = TEMP_ROOT / "get_gpu_mem.py"
TEMP_DIR = TEMP_ROOT / "tts"
TEMP_SERVER = TEMP_DIR / "server.py"
TEMP_MODEL_DOWNLOAD = TEMP_DIR / "model_download.py"
TEMP_INFO_JSON = TEMP_DIR / "info.json"
TEMP_QWEN_HELPER = TEMP_DIR / "qwen_3_tts_helper.py"
TEMP_VOICES = TEMP_DIR / "voices.py"
LEGACY_TEMP_SERVER_DOG = TEMP_DIR / "server-dog.py"
DOWNLOAD_WAIT_TIMEOUT = 9 * 60.0
STATUS_POLL_INTERVAL = 2.0
ERROR_RETRY_MAX = 3
ERROR_RETRY_GAP = 5.0
# Workaround for the server occasionally pegging all CPU cores while producing a
# bogus result: watch the system CPU while a generate is in flight, and if it
# stays saturated for the whole window, force-restart the server and retry.
CPU_WATCH_THRESHOLD = 85.0
CPU_WATCH_DURATION_S = 30.0
CPU_WATCH_MAX_ATTEMPTS = 3
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
        log_path = f"~/.openvino/log/tts-client-py-{timestamp}.log"

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


def _save_pending_request(payload: dict, log_path: Path | None) -> None:
    try:
        PENDING_REQUEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "input": payload,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "log_path": str(log_path) if log_path is not None else None,
        }
        PENDING_REQUEST_PATH.write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
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


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent




def _detect_claw_name() -> str | None:
    skill_root = str(_skill_root())
    for key, exe in CLAW_MAP.items():
        if key in skill_root:
            return exe
    return None


def _needs_sync(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    return not filecmp.cmp(str(src), str(dst), shallow=False)


def _terminate_legacy_dog(log_path: Path | None) -> None:
    """Kill any in-flight legacy per-skill server-dog from a previous release."""
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
    src_server = Path(__file__).with_name("server.py")
    src_model_download = Path(__file__).with_name("model_download.py")
    src_info_json = Path(__file__).resolve().parent.parent / "info.json"
    src_helper = Path(__file__).with_name("qwen_3_tts_helper.py")
    src_voices = Path(__file__).with_name("voices.py")
    src_dog = Path(__file__).with_name("server-dog.py")
    src_get_gpu_mem = Path(__file__).with_name("get_gpu_mem.py")
    runtime_scripts = [
        (src_server, TEMP_SERVER),
        (src_model_download, TEMP_MODEL_DOWNLOAD),
        (src_info_json, TEMP_INFO_JSON),
        (src_helper, TEMP_QWEN_HELPER),
        (src_voices, TEMP_VOICES),
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
    venv_name = env.get("venv_name", "tts")
    mem_need_gb = float(env.get("mem_need_gb", 9.0))
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
        "extra_env": {"LOCAL_TTS_SKILL_ROOT": str(_skill_root())},
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
    raise RuntimeError(f"tts server did not come up within {SERVER_BOOT_TIMEOUT:.0f}s")


def _wait_for_running(log_path: Path | None, deadline: float) -> tuple[str, str]:
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


def _format_timing(t: dict) -> str:
    parts = []
    if "infer_s" in t:
        parts.append(f"推理: {t.get('infer_s', 0.0):.3f}秒")
    if "save_s" in t:
        parts.append(f"保存: {t.get('save_s', 0.0):.3f}秒")
    total = t.get("total_s", t.get("total", 0.0))
    rtf = t.get("rtf")
    if isinstance(rtf, (int, float)):
        parts.append(f"RTF: {float(rtf):.2f}x")
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"耗时: {float(total):.3f} 秒{detail}"


def _print_request_reply(reply: dict) -> int:
    if not reply.get("ok", False):
        print(Fore.RED + "❌ 服务器处理失败:" + Style.RESET_ALL)
        print(reply.get("error", "<unknown error>"))
        return 1

    if not reply.get("success", False):
        print(Fore.RED + "❌ 音频生成失败:" + Style.RESET_ALL)
        print(reply.get("error", reply.get("error_code", "<unknown error>")))
        return 1

    audio_path = reply.get("audio_path")
    if audio_path:
        print(Style.BRIGHT + Fore.GREEN + "✅ 音频已生成: " + Style.RESET_ALL + str(audio_path))
    prompt = reply.get("prompt")
    if prompt:
        print(f"  提示词: {prompt}")
    voice = reply.get("voice")
    if voice:
        print(f"  音色:   {voice}")
    language = reply.get("language")
    if language:
        print(f"  语言:   {language}")
    device = reply.get("device")
    if device:
        print(f"  设备:   {device}")
    duration = reply.get("duration_s")
    if isinstance(duration, (int, float)):
        print(f"  时长:   {float(duration):.2f}s")

    timing = dict(reply.get("timing", {}))
    if "rtf" in reply:
        timing["rtf"] = reply["rtf"]
    print(_format_timing(timing))
    return 0


def _cmd_status(log_path: Path | None = None) -> int:
    _log_message(log_path, "checking server status")
    conn = _try_connect()
    if conn is None:
        print("server not running")
        return 0
    reply = _send(conn, {"op": "status"}, log_path)
    if not reply.get("ok", False):
        print(Fore.RED + "status failed:" + Style.RESET_ALL, reply.get("error", "<unknown>"))
        return 1
    print(
        f"state:   {reply.get('state')}\n"
        f"pid:     {reply.get('pid')}\n"
        f"uptime:  {reply.get('uptime_s', 0.0):.1f}s\n"
        f"model:   {reply.get('loaded_model_id') or 'not_loaded'}\n"
        f"device:  {reply.get('loaded_device') or 'none'}"
    )
    return 0


def _cmd_shutdown(timeout: float, log_path: Path | None = None) -> int:
    _log_message(log_path, f"requesting server shutdown with timeout={timeout:.1f}s")
    conn = _try_connect()
    if conn is None:
        print("server not running")
        return 0
    reply = _send(conn, {"op": "shutdown", "timeout": timeout}, log_path)
    if not reply.get("ok", False):
        print(Fore.RED + "shutdown failed:" + Style.RESET_ALL, reply.get("error", "<unknown>"))
        return 1
    print(f"server shutting down (grace period: {timeout:.1f}s)")
    return 0


def _kill_server(log_path: Path | None) -> None:
    """Force-kill a stuck server process.

    The server handles requests synchronously in a single accept loop, so a
    runaway inference cannot be interrupted by a graceful ``shutdown`` message.
    We kill the OS process directly; the server-dog notices the stale pid on the
    next ``start_server`` and respawns a fresh server.
    """
    target = str(TEMP_SERVER).casefold()
    killed = False
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if any(target in str(part).casefold() for part in cmdline):
                proc.kill()
                killed = True
                _log_message(log_path, f"killed stuck server pid={proc.info.get('pid')}")
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    if not killed:
        _log_message(log_path, "no stuck server matched; trying graceful shutdown")
        _cmd_shutdown(DEFAULT_SHUTDOWN_TIMEOUT, log_path)
    deadline = time.time() + DEFAULT_SHUTDOWN_TIMEOUT
    while time.time() < deadline and _try_connect() is not None:
        time.sleep(0.2)


def _send_generate_with_cpu_watch(request: dict, log_path: Path | None):
    """Send a generate request while watching system CPU for the runaway bug.

    Returns ``(reply, stuck)``. When ``stuck`` is True the server kept total CPU
    utilization above ``CPU_WATCH_THRESHOLD`` for ``CPU_WATCH_DURATION_S`` seconds
    and ``reply`` is None; the caller should restart the server and retry.
    """
    conn = _try_connect()
    if conn is None:
        return {"ok": False, "error": "lost connection to server"}, False

    result: dict = {}

    def _worker() -> None:
        try:
            result["reply"] = _send(conn, request, log_path)
        except Exception as exc:  # pragma: no cover - defensive
            result["reply"] = {"ok": False, "error": str(exc)}

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()

    sustained = 0.0
    while worker.is_alive():
        pct = psutil.cpu_percent(interval=1)
        if not worker.is_alive():
            break
        if pct > CPU_WATCH_THRESHOLD:
            sustained += 1.0
            if sustained >= CPU_WATCH_DURATION_S:
                _log_message(
                    log_path,
                    f"CPU watchdog tripped: {pct:.0f}% sustained {sustained:.0f}s",
                )
                return None, True
        else:
            sustained = 0.0

    worker.join()
    return result.get("reply"), False


def _cmd_request(payload: dict, log_path: Path | None = None) -> int:
    _log_message(log_path, f"processing request: prompt={payload.get('prompt')!r}")

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
        _save_pending_request(payload, log_path)
        print(Fore.YELLOW + "模型正在下载, 请用命令`scripts\\run.ps1 --continue`继续运行" + Style.RESET_ALL)
        _log_message(log_path, "exiting with code 3: download still in progress")
        return 3

    if outcome == "error":
        print(Fore.RED + "❌ 服务器初始化失败:" + Style.RESET_ALL)
        print(detail)
        _delete_pending_request(log_path)
        return 1

    request = {"op": "generate"}
    request.update({k: v for k, v in payload.items() if v is not None})
    try:
        for attempt in range(1, CPU_WATCH_MAX_ATTEMPTS + 1):
            reply, stuck = _send_generate_with_cpu_watch(request, log_path)
            if not stuck:
                if reply is None:
                    print(Fore.RED + "lost connection to server" + Style.RESET_ALL)
                    return 2
                return _print_request_reply(reply)

            _log_message(
                log_path,
                f"CPU runaway detected (attempt {attempt}/{CPU_WATCH_MAX_ATTEMPTS})",
            )
            if attempt >= CPU_WATCH_MAX_ATTEMPTS:
                print(Fore.RED + "❌ 音频生成失败: TTS服务无法正常工作" + Style.RESET_ALL)
                return 1

            _kill_server(log_path)
            try:
                _ensure_server(log_path)
            except RuntimeError as exc:
                print(Fore.RED + str(exc) + Style.RESET_ALL)
                return 2
            outcome, detail = _wait_for_running(log_path, time.time() + DOWNLOAD_WAIT_TIMEOUT)
            if outcome == "error":
                print(Fore.RED + "❌ 服务器初始化失败:" + Style.RESET_ALL)
                print(detail)
                return 1
            if outcome == "timeout":
                _save_pending_request(payload, log_path)
                print(Fore.YELLOW + "模型正在下载, 请用命令`scripts\\run.ps1 --continue`继续运行" + Style.RESET_ALL)
                return 3
        return 1
    finally:
        _delete_pending_request(log_path)


def _cmd_continue(log_path: Path | None = None) -> int:
    pending = _load_pending_request()
    if pending is None:
        print(Fore.RED + "无待处理请求, 请先使用 `scripts\\run.ps1 \"<prompt>\"` 发起请求" + Style.RESET_ALL)
        return 1
    saved_input = pending.get("input", {})
    if isinstance(saved_input, str):  # legacy format, treat as prompt-only
        saved_input = {"prompt": saved_input}
    saved_log = _normalize_log_path(pending.get("log_path")) or log_path
    return _cmd_request(saved_input, saved_log)


def main() -> int:
    parser = argparse.ArgumentParser(description="local-tts CLI client")
    parser.add_argument("-i", "--input", type=str, default=None, help="prompt text to synthesize")
    parser.add_argument("--voice", type=str, default=None, help="preset voice key (default/dongbei/sichuan)")
    parser.add_argument("--language", type=str, default=None, help="Chinese/English/Japanese/Korean/Auto")
    parser.add_argument("--ref-audio", type=str, default=None, help="path to a custom reference WAV/MP3")
    parser.add_argument("--ref-text", type=str, default=None, help="transcript of --ref-audio")
    parser.add_argument("--x-vector-only", action="store_true", help="x-vector-only synthesis mode")
    parser.add_argument("--output", type=str, default=None, help="output WAV path (default: ~/Music/tts_*.wav)")
    parser.add_argument("--log", type=str, default=None, help="append debug logs to this file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--server-status", action="store_true", help="query server status")
    group.add_argument("--server-shutdown", action="store_true", help="request server shutdown")
    group.add_argument("--continue", dest="cont", action="store_true", help="resume the last pending request")
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
        if args.input is None:
            print(Fore.RED + "usage: client.py -i \"<prompt>\" [--voice ...] | --continue" + Style.RESET_ALL)
            return 3
        payload = {
            "prompt": args.input,
            "voice": args.voice,
            "language": args.language,
            "ref_audio": args.ref_audio,
            "ref_text": args.ref_text,
            "x_vector_only": bool(args.x_vector_only),
            "output": args.output,
        }
        exit_code = _cmd_request(payload, log_path)

    _log_message(log_path, f"client exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
