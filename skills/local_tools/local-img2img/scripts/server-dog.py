"""Shared server-dog process for AI skills.

A singleton process that brokers the lifecycle of per-skill ``server.py``
processes. Listens on ``\\\\.\\pipe\\skill-server-dog`` and accepts
``start_server`` / ``keepalive`` / ``status`` / ``shutdown`` requests.
See ``docs/superpowers/specs/2026-05-26-shared-server-dog-design.md``.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import Optional

import psutil

PIPE_ADDRESS = r"\\.\pipe\skill-server-dog"
AUTHKEY = b"skill-server-dog"
NO_EVICTION_ENV = "INTEL_SKILL_DOG_NO_EVICTION"
SYS_MEM_FLOOR_GB = 1.0
SERVER_BOOT_TIMEOUT = 60.0
SERVER_BOOT_POLL_INTERVAL = 1.0
SHUTDOWN_GRACE_S = 10.0
EVICTION_WAIT_S = 15.0
CLAW_POLL_INTERVAL_S = 30.0
STATE_RUNNING = "running"
log = logging.getLogger("server-dog")


DEFAULT_SERVER_ALIVE_TIMEOUT = 300.0
KEEPALIVE_CHECK_INTERVAL_S = 30.0


@dataclass
class ServerRecord:
    skill_name: str
    pid: int
    pipe_address: str
    authkey: bytes
    venv_python: str
    server_path: str
    mem_need_gb: float
    started_at: float
    last_used_at: float
    server_alive_timeout: float = DEFAULT_SERVER_ALIVE_TIMEOUT

    def to_dict(self) -> dict:
        d = asdict(self)
        d["authkey"] = self.authkey.decode("latin-1")
        return d


class Registry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, ServerRecord] = {}

    def put(self, record: ServerRecord) -> None:
        with self._lock:
            self._records[record.skill_name] = record

    def get(self, skill_name: str) -> Optional[ServerRecord]:
        with self._lock:
            return self._records.get(skill_name)

    def pop(self, skill_name: str) -> Optional[ServerRecord]:
        with self._lock:
            return self._records.pop(skill_name, None)

    def all(self) -> list[ServerRecord]:
        with self._lock:
            return list(self._records.values())

    def bump_last_used(self, skill_name: str) -> bool:
        with self._lock:
            record = self._records.get(skill_name)
            if record is None:
                return False
            record.last_used_at = time.monotonic()
            return True

    def pick_lru(self, exclude: str) -> Optional[ServerRecord]:
        with self._lock:
            candidates = [r for r in self._records.values() if r.skill_name != exclude]
            if not candidates:
                return None
            return min(candidates, key=lambda r: r.last_used_at)


def _read_memory() -> dict[str, float]:
    """Return free memory in GB. Imports get_gpu_mem lazily so tests can monkeypatch."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from get_gpu_mem import get_gpu_memory_win  # type: ignore
    info = get_gpu_memory_win()
    return {
        "gpu_mem_free": float(info["gpu_mem_free"]),
        "sys_mem_free": float(info["sys_mem_free"]),
    }


def _memory_budget_ok(mem_need_gb: float) -> tuple[bool, dict]:
    """Check whether memory budget admits a server needing ``mem_need_gb``.

    Returns (ok, detail). On probe failure, returns (False, {"probe_failed": True})
    so the caller can decide to evict and re-probe.
    """
    try:
        info = _read_memory()
    except Exception as exc:
        log.warning("memory probe failed: %s", exc)
        return False, {"probe_failed": True}
    gpu_ok = info["gpu_mem_free"] >= mem_need_gb
    sys_ok = info["sys_mem_free"] >= mem_need_gb + SYS_MEM_FLOOR_GB
    return (gpu_ok and sys_ok, info)


def _no_eviction_enabled() -> bool:
    return os.environ.get(NO_EVICTION_ENV) == "1"


def _hidden_startupinfo():
    if os.name != "nt" or not hasattr(subprocess, "STARTUPINFO"):
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
    info.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return info


def _cleaned_env() -> dict[str, str]:
    return {
        k: v
        for k, v in os.environ.items()
        if not (k.startswith("WORKBUDDY_") or k.startswith("CODEBUDDY_"))
    }


def _spawn_server(
    venv_python: str,
    server_path: str,
    pipe_address: str,
    authkey: bytes,
    extra_env: dict | None = None,
) -> subprocess.Popen:
    """Spawn the per-skill server.py and wait for its pipe to come up.

    Raises RuntimeError on timeout (after terminating the child process).
    """
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    cwd = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
    cwd.mkdir(parents=True, exist_ok=True)

    env = _cleaned_env()
    if extra_env:
        env.update({str(k): str(v) for k, v in extra_env.items()})

    proc = subprocess.Popen(
        [venv_python, server_path],
        creationflags=creationflags,
        startupinfo=_hidden_startupinfo(),
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(cwd),
        env=env,
    )

    deadline = time.monotonic() + SERVER_BOOT_TIMEOUT
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"server_died_during_boot (pipe={pipe_address}, exit={proc.returncode})"
            )
        try:
            conn = Client(pipe_address, authkey=authkey)
            conn.close()
            log.info("server up: pid=%s pipe=%s", proc.pid, pipe_address)
            return proc
        except (FileNotFoundError, OSError, EOFError):
            time.sleep(SERVER_BOOT_POLL_INTERVAL)

    log.warning("server pipe %s did not come up within %.1fs; terminating pid=%s",
                pipe_address, SERVER_BOOT_TIMEOUT, proc.pid)
    try:
        proc.terminate()
    except Exception:
        pass
    raise RuntimeError(f"server_did_not_start (pipe={pipe_address})")


def _query_server_state(record: ServerRecord) -> Optional[str]:
    """Best-effort: ask the server for its state via its pipe.

    Returns the state string (e.g. ``"running"``) or ``None`` if the server is
    unreachable or the reply is malformed.
    """
    try:
        conn = Client(record.pipe_address, authkey=record.authkey)
    except (FileNotFoundError, OSError, EOFError) as exc:
        log.info("status %s: pipe unreachable: %s", record.skill_name, exc)
        return None
    try:
        conn.send({"op": "status"})
        if conn.poll(5.0):
            reply = conn.recv()
            if isinstance(reply, dict):
                return reply.get("state")
    except (EOFError, OSError) as exc:
        log.warning("status %s: handshake error: %s", record.skill_name, exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return None


def _send_shutdown(record: ServerRecord) -> None:
    """Best-effort: ask the server to shut down via its pipe."""
    try:
        conn = Client(record.pipe_address, authkey=record.authkey)
    except (FileNotFoundError, OSError, EOFError) as exc:
        log.info("evict %s: pipe unreachable, will force-kill: %s",
                 record.skill_name, exc)
        return
    try:
        conn.send({"op": "shutdown", "timeout": SHUTDOWN_GRACE_S})
        if conn.poll(5.0):
            try:
                conn.recv()
            except Exception:
                pass
    except (EOFError, OSError) as exc:
        log.warning("evict %s: shutdown handshake error: %s", record.skill_name, exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _evict_record(record: ServerRecord, poll_interval: float = 0.5) -> bool:
    """Shut down a server. Returns True once its pid is gone (or after force-kill)."""
    log.info("evicting %s pid=%s", record.skill_name, record.pid)
    _send_shutdown(record)

    deadline = time.monotonic() + EVICTION_WAIT_S
    while time.monotonic() < deadline:
        if not psutil.pid_exists(record.pid):
            log.info("evicted %s gracefully", record.skill_name)
            return True
        time.sleep(poll_interval)

    log.warning("evict %s: grace timeout, force-killing pid=%s",
                record.skill_name, record.pid)
    try:
        proc = psutil.Process(record.pid)
        proc.kill()
        proc.wait(timeout=5.0)
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        pass
    except Exception as exc:
        log.warning("evict %s: kill failed: %s", record.skill_name, exc)
    return True


class DogState:
    def __init__(self) -> None:
        self.registry = Registry()
        self.claw_name: Optional[str] = None
        self.claw_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()


def _validate_start_request(request: dict) -> Optional[str]:
    required = ("skill_name", "server_path", "venv_python", "pipe_address", "authkey")
    for key in required:
        if not request.get(key):
            return f"missing_{key}"
    if "mem_need_gb" not in request or not isinstance(request["mem_need_gb"], (int, float)):
        return "missing_mem_need_gb"
    return None


def _handle_start_server(state: DogState, request: dict) -> dict:
    err = _validate_start_request(request)
    if err is not None:
        return {"ok": False, "error": err}

    skill_name = request["skill_name"]
    mem_need_gb = float(request["mem_need_gb"])
    claw_name = request.get("claw_name")

    existing = state.registry.get(skill_name)
    if existing is not None:
        if psutil.pid_exists(existing.pid):
            state.registry.bump_last_used(skill_name)
            if state.claw_name is None and claw_name:
                state.claw_name = claw_name
            return {"ok": True, "pid": existing.pid}
        else:
            log.info("stale record for %s (pid=%s gone), respawning",
                     skill_name, existing.pid)
            state.registry.pop(skill_name)

    if _no_eviction_enabled():
        log.info("%s=1, skipping memory check and eviction", NO_EVICTION_ENV)
    else:
        for _ in range(8):  # max 8 evictions per request, defensive bound
            ok, _detail = _memory_budget_ok(mem_need_gb)
            if ok:
                break

            lru = state.registry.pick_lru(exclude=skill_name)
            if lru is None:
                break
            
            _evict_record(lru)
            state.registry.pop(lru.skill_name)
        else:
            return {"ok": False, "error": "not_enough_memory"}

    try:
        proc = _spawn_server(
            venv_python=request["venv_python"],
            server_path=request["server_path"],
            pipe_address=request["pipe_address"],
            authkey=_bytes_authkey(request["authkey"]),
            extra_env=request.get("extra_env") or None,
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    raw_timeout = request.get("server_alive_timeout", DEFAULT_SERVER_ALIVE_TIMEOUT)
    try:
        server_alive_timeout = float(raw_timeout)
    except (TypeError, ValueError):
        server_alive_timeout = DEFAULT_SERVER_ALIVE_TIMEOUT

    now = time.monotonic()
    state.registry.put(
        ServerRecord(
            skill_name=skill_name,
            pid=proc.pid,
            pipe_address=request["pipe_address"],
            authkey=_bytes_authkey(request["authkey"]),
            venv_python=request["venv_python"],
            server_path=request["server_path"],
            mem_need_gb=mem_need_gb,
            started_at=now,
            last_used_at=now,
            server_alive_timeout=server_alive_timeout,
        )
    )
    if state.claw_name is None and claw_name:
        state.claw_name = claw_name
        log.info("recorded claw_name=%s", claw_name)
    return {"ok": True, "pid": proc.pid}


def _handle_keepalive(state: DogState, request: dict) -> dict:
    skill_name = request.get("skill_name") or ""
    state.registry.bump_last_used(skill_name)
    return {"ok": True}


def _handle_status(state: DogState, request: dict) -> dict:
    return {
        "ok": True,
        "claw_name": state.claw_name,
        "servers": [r.to_dict() for r in state.registry.all()],
    }


def _handle_shutdown(state: DogState, request: dict) -> dict:
    state.shutdown_event.set()
    return {"ok": True}


def _dispatch(state: DogState, request: dict) -> dict:
    op = request.get("op")
    handler_name = {
        "start_server": "_handle_start_server",
        "keepalive": "_handle_keepalive",
        "status": "_handle_status",
        "shutdown": "_handle_shutdown",
    }.get(op)
    if handler_name is None:
        return {"ok": False, "error": "unknown_op"}
    handler = globals()[handler_name]
    try:
        return handler(state, request)
    except Exception as exc:
        log.exception("handler %s failed", op)
        return {"ok": False, "error": f"handler_error: {exc}"}


def _bytes_authkey(value: bytes | str) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("latin-1")
    raise TypeError(f"authkey must be bytes or str, got {type(value)}")


def _claw_is_running(claw_name: str) -> bool:
    keyword = claw_name.casefold()
    for proc in psutil.process_iter(["cmdline"], ad_value=None):
        try:
            cmdline = proc.info.get("cmdline")
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        if not cmdline:
            continue
        if isinstance(cmdline, str):
            joined = cmdline
        else:
            joined = " ".join(str(p) for p in cmdline if p)
        if keyword in joined.casefold():
            return True
    return False


def _claw_watch_once(state: DogState) -> None:
    """One iteration of the claw watcher. Tears down all servers and signals shutdown
    when the claw is no longer running."""
    if not state.claw_name:
        return
    if _claw_is_running(state.claw_name):
        return
    log.info("claw %s no longer running, evicting all servers", state.claw_name)
    for record in state.registry.all():
        try:
            _evict_record(record)
        except Exception as exc:
            log.warning("teardown error for %s: %s", record.skill_name, exc)
        state.registry.pop(record.skill_name)
    state.shutdown_event.set()


def _claw_watch_loop(state: DogState) -> None:
    while not state.shutdown_event.is_set():
        if state.claw_name:
            try:
                _claw_watch_once(state)
            except Exception:
                log.exception("claw watcher iteration failed")
        state.shutdown_event.wait(CLAW_POLL_INTERVAL_S)


def _keepalive_timeout_check(state: DogState) -> None:
    """Evict servers that have not received a keepalive within their timeout."""
    now = time.monotonic()
    for record in state.registry.all():
        if record.server_alive_timeout < 0:
            continue
        elapsed = now - record.last_used_at
        if elapsed > record.server_alive_timeout:
            server_state = _query_server_state(record)
            if server_state is not None and server_state != STATE_RUNNING:
                log.info(
                    "keepalive timeout for %s but state=%s (not running), "
                    "resetting last_used_at",
                    record.skill_name, server_state,
                )
                state.registry.bump_last_used(record.skill_name)
                continue
            log.info(
                "keepalive timeout for %s (%.1fs > %.1fs), shutting down",
                record.skill_name, elapsed, record.server_alive_timeout,
            )
            try:
                _evict_record(record)
            except Exception as exc:
                log.warning("keepalive eviction failed for %s: %s", record.skill_name, exc)
            state.registry.pop(record.skill_name)


def _keepalive_timeout_loop(state: DogState) -> None:
    while not state.shutdown_event.is_set():
        try:
            _keepalive_timeout_check(state)
        except Exception:
            log.exception("keepalive timeout check failed")
        state.shutdown_event.wait(KEEPALIVE_CHECK_INTERVAL_S)


def _accept_loop(listener: Listener, state: DogState) -> None:
    while not state.shutdown_event.is_set():
        try:
            conn = listener.accept()
        except OSError:
            return
        try:
            request = conn.recv()
            if not isinstance(request, dict):
                conn.send({"ok": False, "error": "bad_request"})
                continue
            reply = _dispatch(state, request)
            conn.send(reply)
        except (EOFError, OSError) as exc:
            log.info("client disconnected: %s", exc)
        finally:
            try:
                conn.close()
            except Exception:
                pass


def _serve(listener: Listener, state: DogState) -> None:
    """Accept loop. Stops when shutdown_event is set."""
    accept_thread = threading.Thread(
        target=_accept_loop, args=(listener, state), daemon=True, name="dog-accept"
    )
    accept_thread.start()

    state.claw_thread = threading.Thread(
        target=_claw_watch_loop, args=(state,), daemon=True, name="dog-claw"
    )
    state.claw_thread.start()

    if _no_eviction_enabled():
        log.info("%s=1, skipping keepalive timeout loop", NO_EVICTION_ENV)
    else:
        keepalive_thread = threading.Thread(
            target=_keepalive_timeout_loop, args=(state,), daemon=True, name="dog-keepalive"
        )
        keepalive_thread.start()

    state.shutdown_event.wait()
    log.info("shutdown_event set, closing listener")
    try:
        listener.close()
    except Exception:
        pass


def _setup_logging() -> None:
    log_dir = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = log_dir / f"server-dog-py-{timestamp}.log"

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.info("logging to %s", log_file)


def _try_bind_singleton() -> Optional[Listener]:
    """Bind the singleton pipe; return None if another dog already owns it."""
    try:
        return Listener(PIPE_ADDRESS, authkey=AUTHKEY)
    except OSError as exc:
        log.info("another server-dog appears to be running: %s", exc)
        return None


def main() -> int:
    _setup_logging()
    listener = _try_bind_singleton()
    if listener is None:
        return 0
    log.info("server-dog started, listening on %s", PIPE_ADDRESS)
    state = DogState()
    try:
        _serve(listener, state)
    finally:
        for record in state.registry.all():
            try:
                _evict_record(record)
            except Exception:
                pass
    log.info("server-dog exiting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
