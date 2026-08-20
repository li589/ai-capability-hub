# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Persistent luicore server.

Listens on the Windows named pipe ``\\\\.\\pipe\\luicore`` via
``multiprocessing.connection.Listener`` and dispatches requests sent by
``release/client.py``. Keeps luicore (classifier + toolfinder LLM) loaded
across invocations so the CLI avoids paying the cold-start cost every time.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import threading
import time
import traceback
from multiprocessing.connection import Listener
from pathlib import Path
from typing import Dict

from model_download import (
    ensure_models,
    load_model_infos,
    validate_model_dir,
)

os.environ["_LUICORE_PROTOCOL"] = "in"


PIPE_ADDRESS = r"\\.\pipe\luicore"
AUTHKEY = b"luicore-local"
DEFAULT_SHUTDOWN_TIMEOUT = 10.0
STATE_STARTING = "starting"
STATE_DOWNLOADING = "downloading"
STATE_LOADING = "loading"
STATE_RUNNING = "running"
STATE_ERROR = "error"

MODELS_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino" / "models"

_HERE = Path(__file__).resolve().parent
INFO_JSON = _HERE / "info.json" if (_HERE / "info.json").exists() else _HERE.parent / "info.json"
MODEL_INFOS = load_model_infos(INFO_JSON)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

LOG_LOCK = threading.Lock()


def _normalize_log_path(log_path: str | None) -> Path | None:
    if not log_path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = f"~/.openvino/log/computer-use-server-py-{timestamp}.log"
        
    path = Path(log_path).expanduser()
    return path if path.is_absolute() else Path.cwd() / path


def _log_message(log_path: Path | None, message: str) -> None:
    if log_path is None:
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG_LOCK:
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(f"[{timestamp}] [server pid={os.getpid()}] {message}\n")
    except OSError:
        pass


def _load_luicore_runtime() -> tuple[str, object]:
    try:
        from luicore import __version__ as luicore_version, handle_request
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from luicore import __version__ as luicore_version, handle_request
    return luicore_version, handle_request


def _report_download_message(log_path: Path | None, message: str) -> None:
    print(f"[server] {message}", flush=True)
    _log_message(log_path, message)


def _ensure_required_models(log_path: Path | None = None) -> None:
    all_valid = all(
        validate_model_dir(MODELS_ROOT / m.dir_name, m.required_files).ok
        for m in MODEL_INFOS
    )
    if all_valid:
        return

    def _logger(message: str):
        _report_download_message(log_path, message)

    ensure_models(MODEL_INFOS, MODELS_ROOT, logger=_logger)


def _extract_phase_timings() -> dict:
    try:
        from luicore.toolexecuter.protocols.tx_protocol import breadcrumbs
        return {
            "classifier": float(breadcrumbs.last_classifier_elapsed or 0.0),
            "toolfinder": float(breadcrumbs.last_toolfinder_elapsed or 0.0),
            "tool_exec":  float(breadcrumbs.last_tool_exec_elapsed or 0.0),
        }
    except ImportError:
        return {"classifier": 0.0, "toolfinder": 0.0, "tool_exec": 0.0}
    
def _extract_phase_tokens() -> dict:
    return {"input_tokens": 1234, "output_tokens": 5678}


def _extract_breadcrumbs() -> tuple[str | None, str | None, Dict | None]:
    try:
        from luicore.toolexecuter.protocols.base import breadcrumbs
        return breadcrumbs.last_feature, breadcrumbs.last_tool, breadcrumbs.last_tool_args
    except ImportError:
        return None, None, None


def _extract_result_from_messages(messages: list) -> object:
    for msg in reversed(messages):
        if msg.get("finished", False) and "result" in msg:
            return msg.get("result")
    return None


async def _run_handle_request(user_input: str, handle_request_func) -> dict:
    msg_queue: asyncio.Queue = asyncio.Queue()
    messages: list = []

    async def drain():
        while True:
            m = await msg_queue.get()
            if m.get("finished", False):
                messages.append(m)
                return

    consumer = asyncio.create_task(drain())
    t0 = time.time()
    success = await handle_request_func(user_input, msg_queue)
    t1 = time.time()
    await consumer

    timings = _extract_phase_timings()
    timings["total"] = t1 - t0

    tokens = _extract_phase_tokens()

    actual_skill, actual_tool, actual_tool_args = _extract_breadcrumbs()
    actual_result = _extract_result_from_messages(messages)

    return {
        "ok": True,
        "input": user_input,
        "success": bool(success),
        "result_passed": actual_result is True,
        "actual_result": actual_result,
        "actual_skill": actual_skill,
        "actual_tool": actual_tool,
        "actual_tool_args": actual_tool_args,
        "messages": messages,
        "timing": timings,
        "local_tokens": tokens,
    }


class Server:
    def __init__(self, log_path: Path | None = None) -> None:
        self.start_time = time.time()
        self.shutdown_event = threading.Event()
        self.shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
        self.listener: Listener | None = None
        self.runtime_lock = threading.Lock()
        self.luicore_version: str | None = None
        self.handle_request = None
        self.log_path = log_path
        self.state: str = STATE_STARTING
        self.init_error: str = ""
        self.init_thread: threading.Thread | None = None

    def log(self, message: str) -> None:
        _log_message(self.log_path, message)
    
    def _init_runtime_worker(self) -> None:
        try:
            with self.runtime_lock:
                self.state = STATE_DOWNLOADING
            self.log("init thread: downloading required models")
            _ensure_required_models(self.log_path)

            with self.runtime_lock:
                self.state = STATE_LOADING
            self.log("init thread: loading luicore runtime")
            version, handler = _load_luicore_runtime()

            with self.runtime_lock:
                self.luicore_version = version
                self.handle_request = handler
                self.state = STATE_RUNNING
            self.log(f"init thread: runtime ready (version={version})")
        except Exception:
            error_text = traceback.format_exc()
            with self.runtime_lock:
                self.init_error = error_text
                self.state = STATE_ERROR
            self.log(f"init thread failed:\n{error_text}")

    def _start_init_thread(self) -> None:
        if self.init_thread is not None and self.init_thread.is_alive():
            return
        self.init_thread = threading.Thread(
            target=self._init_runtime_worker,
            name="runtime-init",
            daemon=True,
        )
        self.init_thread.start()
        self.log("init thread started")

    def dispatch(self, msg: dict) -> dict:
        op = msg.get("op")
        self.log(f"dispatching op={op!r}")
        if op == "request":
            user_input = msg.get("input", "")
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                handler = self.handle_request
            if state != STATE_RUNNING or handler is None:
                self.log(f"request rejected: state={state}")
                reply = {
                    "ok": False,
                    "state": state,
                    "input": user_input,
                    "error": f"runtime not ready: {state}",
                }
                if state == STATE_ERROR and init_error:
                    reply["error"] = init_error
                return reply
            try:
                reply = asyncio.run(_run_handle_request(user_input, handler))
                reply["state"] = STATE_RUNNING
                self.log(
                    "request completed: "
                    f"success={reply.get('success')} actual_skill={reply.get('actual_skill')} "
                    f"actual_tool={reply.get('actual_tool')} actual_tool_args={reply.get('actual_tool_args')}"
                )
                return reply
            except Exception:
                error_text = traceback.format_exc()
                self.log(f"request failed:\n{error_text}")
                return {
                    "ok": False,
                    "state": STATE_RUNNING,
                    "input": user_input,
                    "error": error_text,
                }
        if op == "status":
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                luicore_version = self.luicore_version
            self.log(f"status requested: state={state}")
            reply = {
                "ok": True,
                "state": state,
                "pid": os.getpid(),
                "uptime_s": time.time() - self.start_time,
                "luicore_version": luicore_version or "not_loaded",
            }
            if state == STATE_ERROR and init_error:
                reply["error"] = init_error
            return reply
        if op == "shutdown":
            timeout = msg.get("timeout", DEFAULT_SHUTDOWN_TIMEOUT)
            try:
                self.shutdown_timeout = float(timeout)
            except (TypeError, ValueError):
                self.shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
            self.log(f"shutdown requested with timeout={self.shutdown_timeout:.1f}s")
            self.shutdown_event.set()
            return {"ok": True, "state": "shutting_down"}
        self.log(f"unknown operation received: {op!r}")
        return {"ok": False, "error": f"unknown op: {op!r}"}

    def serve_forever(self) -> None:
        assert self.listener is not None
        while not self.shutdown_event.is_set():
            try:
                conn = self.listener.accept()
                self.log("accepted client connection")
            except OSError:
                if self.shutdown_event.is_set():
                    self.log("listener stopped after shutdown was requested")
                    return
                raise
            
            try:
                msg = conn.recv()
                self.log(f"client request: {msg!r}")
            
                reply = self.dispatch(msg if isinstance(msg, dict) else {})
                conn.send(reply)
                
                self.log(f"server reply: {reply!r}")
            except EOFError:
                self.log("client connection closed before a full request was received")
                pass
            except Exception:
                error_text = traceback.format_exc()
                try:
                    conn.send({"ok": False, "error": error_text})
                except Exception:
                    pass
                self.log(f"accept-loop error:\n{error_text}")
                print(f"[server] accept-loop error:\n{error_text}", flush=True)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="persistent luicore server")
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="append debug logs to this file",
    )
    args = parser.parse_args()

    server = Server(log_path=_normalize_log_path(args.log))
    server.log(f"server starting with argv={sys.argv[1:]}")
    try:
        server.listener = Listener(PIPE_ADDRESS, family="AF_PIPE", authkey=AUTHKEY)
    except OSError as e:
        # Pipe already exists → another server is running. Exit 2 so the client
        # interprets this as "server is up" and connects to the existing one.
        server.log(f"bind failed: {e}")
        print(f"[server] bind failed: {e}", flush=True)
        return 2

    server.log(f"listener ready on {PIPE_ADDRESS}")
    server.log("kicking off background runtime init")
    server._start_init_thread()
    print(
        f"luicore server listening on {PIPE_ADDRESS} (pid={os.getpid()}, "
        "version=not_loaded)",
        flush=True,
    )

    worker = threading.Thread(target=server.serve_forever, name="accept-loop", daemon=True)
    worker.start()

    try:
        # Wait until shutdown is requested by a client.
        while not server.shutdown_event.wait(timeout=0.5):
            if not worker.is_alive():
                # Accept loop died unexpectedly.
                server.log("accept-loop thread exited unexpectedly")
                return 1
    finally:
        try:
            if server.listener is not None:
                server.listener.close()
        except Exception:
            pass

    # Graceful shutdown with timeout. The worker may still be finishing an
    # in-flight request or replying to the shutdown op.
    worker.join(timeout=server.shutdown_timeout)
    if worker.is_alive():
        server.log(
            f"worker did not finish within {server.shutdown_timeout:.1f}s; forcing exit"
        )
        print(
            f"[server] worker did not finish within {server.shutdown_timeout:.1f}s; forcing exit",
            flush=True,
        )
        os._exit(1)
    server.log("server exited cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
