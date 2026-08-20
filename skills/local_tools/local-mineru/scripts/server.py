"""Persistent local-mineru server.

Listens on the Windows named pipe ``\\\\.\\pipe\\local-mineru`` via
``multiprocessing.connection.Listener`` and dispatches document-parsing
requests from ``client.py``. Keeps an OpenVINO MinerU2.5-Pro pipeline resident
across invocations so each parse avoids cold-start cost.

State machine (same shape as ``skills/local-img2img/src/scripts/server.py``)::

    starting -> downloading -> loading -> running
                                        |-> error

Supported ops::

    status   -> {ok, state, pid, uptime_s, loaded_model_id, loaded_device}
    shutdown -> {ok, state: "shutting_down"}
    parse    -> {ok, success, markdown, pages, md_file, output_dir, parse_time_s}

Environment:
    LOCAL_MINERU_OV_PATH   absolute path to the ``mineru_ov`` package (set by
                           the client when the dog spawns the server).
"""

from __future__ import annotations

import argparse
import gc
import os
import sys
import threading
import time
import traceback
from multiprocessing.connection import Listener
from pathlib import Path
from typing import Any


# --- Make the package dir importable, then resolve the mineru_ov package ----
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _resolve_mineru_ov_path() -> str:
    """Resolve the ``mineru_ov`` package directory.

    Priority:
      1. env ``LOCAL_MINERU_OV_PATH`` (set by client when spawning via the dog)
      2. ``mineru_ov/`` alongside this server.py
    """
    env_path = os.environ.get("LOCAL_MINERU_OV_PATH", "").strip()
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path(__file__).resolve().parent / "mineru_ov")

    for p in candidates:
        if p.is_dir() and (p / "__init__.py").exists():
            return str(p)

    raise FileNotFoundError(
        "mineru_ov package not found. Tried: "
        + ", ".join(str(p) for p in candidates)
        + ". Set LOCAL_MINERU_OV_PATH or ensure mineru_ov/ is alongside server.py."
    )


try:
    MINERU_OV_PATH = _resolve_mineru_ov_path()
    sys.path.insert(0, str(Path(MINERU_OV_PATH).parent))
except FileNotFoundError as e:
    print(f"Fatal: {e}", file=sys.stderr)
    sys.exit(1)

from model_download import (
    ensure_models,
    load_model_infos,
    validate_model_dir,
)

PIPE_ADDRESS = r"\\.\pipe\local-mineru"
AUTHKEY = b"local-mineru"
DEFAULT_SHUTDOWN_TIMEOUT = 10.0
STATE_STARTING = "starting"
STATE_DOWNLOADING = "downloading"
STATE_LOADING = "loading"
STATE_RUNNING = "running"
STATE_ERROR = "error"

OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
MODELS_ROOT = OPENVINO_ROOT / "models"

_HERE = Path(__file__).resolve().parent
INFO_JSON = _HERE / "info.json" if (_HERE / "info.json").exists() else _HERE.parent / "info.json"
MODEL_INFOS = load_model_infos(INFO_JSON)
MODEL_INFO = MODEL_INFOS[0]
MODEL_ID = MODEL_INFO.model_id
# info.json's required_files are nested under the top-level model dir; the
# pipeline's models_dir is that top-level dir (e.g. .../mineru-ov-models).
MODEL_BASE_DIR = MODELS_ROOT / MODEL_INFO.dir_name
REQUIRED_MODEL_FILES = MODEL_INFO.required_files

DEFAULT_DEVICE = "GPU"
DEFAULT_PRECISION = "int4"

SERVER_VERSION = "1.0.0"

os.environ.setdefault("OPENVINO_TELEMETRY_OPT_OUT", "1")

for stream_name in ("stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    if stream is not None and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

LOG_LOCK = threading.Lock()


def _normalize_log_path(log_path: str | None) -> Path | None:
    if not log_path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = f"~/.openvino/log/mineru-server-py-{timestamp}.log"

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


def _report_download_message(log_path: Path | None, message: str) -> None:
    print(f"[server] {message}", flush=True)
    _log_message(log_path, message)


def _ensure_required_model(log_path: Path | None = None) -> None:
    """Download the model to MODEL_BASE_DIR if not already valid."""
    validation = validate_model_dir(MODEL_BASE_DIR, REQUIRED_MODEL_FILES)
    if validation.ok:
        return

    def _logger(message: str):
        _report_download_message(log_path, message)

    ensure_models(MODEL_INFOS, MODELS_ROOT, logger=_logger)

    validation = validate_model_dir(MODEL_BASE_DIR, REQUIRED_MODEL_FILES)
    if not validation.ok:
        raise RuntimeError(
            f"required model download did not complete: {MODEL_BASE_DIR} ({validation.reason})"
        )


# ---------------------------------------------------------------------------
# MinerU OpenVINO pipeline helpers
# ---------------------------------------------------------------------------
def _load_pipeline(device: str, precision: str) -> Any:
    """Build a ``MinerUPipeline`` from the mineru_ov package on the given device.

    The ContinuousBatching backend is on by default; set
    ``LOCAL_MINERU_DISABLE_BATCH=1`` to fall back to the single-page backend.
    """
    from mineru_ov.config import OVConfig
    from mineru_ov.pipeline import MinerUPipeline

    use_batch = os.environ.get("LOCAL_MINERU_DISABLE_BATCH", "").strip() not in ("1", "true", "True")
    max_concurrent = int(os.environ.get("LOCAL_MINERU_MAX_CONCURRENT", "8"))

    cfg = OVConfig(
        device=device,
        precision=precision,
        models_dir=str(MODEL_BASE_DIR),
        backend_type="vlm",
        use_batch_backend=use_batch,
        max_concurrent=max_concurrent,
        performance_hint="LATENCY",
    )
    cfg.validate()
    return MinerUPipeline(cfg)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
class Server:
    def __init__(self, log_path: Path | None = None) -> None:
        self.start_time = time.time()
        self.shutdown_event = threading.Event()
        self.shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
        self.listener: Listener | None = None
        self.runtime_lock = threading.Lock()
        self.pipeline: Any = None
        self.loaded_model_id: str | None = None
        self.loaded_device: str | None = None
        self.download_progress: str = ""
        self.last_request_time = time.time()
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
                self.download_progress = "正在检查/下载模型..."
            self.log("init thread: downloading required model")
            _ensure_required_model(self.log_path)

            with self.runtime_lock:
                self.state = STATE_LOADING
                self.download_progress = "正在加载模型到内存..."
            self.log("init thread: loading OpenVINO MinerU pipeline")

            pipeline = _load_pipeline(DEFAULT_DEVICE, DEFAULT_PRECISION)

            with self.runtime_lock:
                self.pipeline = pipeline
                self.loaded_model_id = MODEL_ID
                self.loaded_device = DEFAULT_DEVICE
                self.download_progress = "模型加载完成"
                self.state = STATE_RUNNING
            self.log(f"init thread: pipeline ready on device={DEFAULT_DEVICE}")
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

    def _do_parse(self, input_path: str, output_dir: str) -> dict:
        t0 = time.time()
        in_path = Path(input_path).resolve()
        if not in_path.exists():
            return {
                "ok": True,
                "success": False,
                "error_code": "BAD_INPUT",
                "error": f"input path does not exist: {in_path}",
            }
        out_dir = Path(output_dir).resolve() if output_dir else (in_path.parent / "output")
        out_dir.mkdir(parents=True, exist_ok=True)

        self.log(f"parsing: {in_path} -> {out_dir}")
        markdown, page_count = self.pipeline.run(
            input_path=str(in_path),
            output_dir=str(out_dir),
        )
        parse_time_s = time.time() - t0
        self.log(f"parse done: {page_count} pages in {parse_time_s:.1f}s")

        return {
            "ok": True,
            "success": True,
            "markdown": markdown,
            "pages": page_count,
            "md_file": str(out_dir / f"{in_path.stem}.md"),
            "output_dir": str(out_dir),
            "parse_time_s": parse_time_s,
            "device": self.loaded_device,
            "model_id": self.loaded_model_id,
        }

    def dispatch(self, msg: dict) -> dict:
        op = msg.get("op")
        self.log(f"dispatching op={op!r}")
        if op == "parse":
            input_path = msg.get("input_path")
            if not isinstance(input_path, str) or not input_path.strip():
                return {
                    "ok": False,
                    "success": False,
                    "error_code": "BAD_INPUT",
                    "error": "input_path must be a non-empty string",
                }
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                pipeline = self.pipeline
            if state != STATE_RUNNING or pipeline is None:
                self.log(f"parse rejected: state={state}")
                reply = {
                    "ok": False,
                    "success": False,
                    "state": state,
                    "error": f"runtime not ready: {state}",
                }
                if state == STATE_ERROR and init_error:
                    reply["error"] = init_error
                return reply
            self.last_request_time = time.time()
            try:
                reply = self._do_parse(input_path, msg.get("output_dir", ""))
                reply["state"] = STATE_RUNNING
                self.last_request_time = time.time()
                self.log(
                    f"parse completed: success={reply.get('success')} "
                    f"md_file={reply.get('md_file')}"
                )
                return reply
            except Exception:
                error_text = traceback.format_exc()
                self.log(f"parse failed:\n{error_text}")
                return {
                    "ok": False,
                    "success": False,
                    "state": STATE_RUNNING,
                    "error": error_text,
                }
        if op == "status":
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                loaded_model_id = self.loaded_model_id
                loaded_device = self.loaded_device
                download_progress = self.download_progress
            self.log(f"status requested: state={state}")
            reply = {
                "ok": True,
                "state": state,
                "pid": os.getpid(),
                "uptime_s": time.time() - self.start_time,
                "loaded_model_id": loaded_model_id,
                "loaded_device": loaded_device,
                "server_version": SERVER_VERSION,
            }
            if state in (STATE_DOWNLOADING, STATE_LOADING) and download_progress:
                reply["download_progress"] = download_progress
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
            # Release the pipeline so GPU memory / DLL handles drop before exit.
            try:
                with self.runtime_lock:
                    if self.pipeline is not None:
                        try:
                            self.pipeline.unload()
                        except Exception:
                            pass
                    self.pipeline = None
                    self.loaded_model_id = None
                    self.loaded_device = None
                gc.collect()
            except Exception:
                pass
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
                self.log(f"client request: op={msg.get('op') if isinstance(msg, dict) else None}")

                reply = self.dispatch(msg if isinstance(msg, dict) else {})
                conn.send(reply)

                self.log(f"server reply: ok={reply.get('ok')} success={reply.get('success')}")
            except EOFError:
                self.log("client connection closed before a full request was received")
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

    def start_idle_watchdog(self) -> None:
        """Self-shutdown when idle beyond LOCAL_MINERU_IDLE_TIMEOUT seconds.

        Guards against a crashed/disconnected dog leaving the server resident.
        """
        idle_timeout = int(os.environ.get("LOCAL_MINERU_IDLE_TIMEOUT", "1200"))

        def _watch():
            while not self.shutdown_event.is_set():
                if self.shutdown_event.wait(60):
                    return
                with self.runtime_lock:
                    state = self.state
                if state != STATE_RUNNING:
                    continue
                idle = time.time() - self.last_request_time
                if idle > idle_timeout:
                    self.log(f"self-shutdown: idle for {idle:.0f}s > {idle_timeout}s, exiting")
                    os._exit(0)

        threading.Thread(target=_watch, name="idle-watchdog", daemon=True).start()
        self.log(f"idle watchdog started (timeout={idle_timeout}s)")


def _bind_listener(server: Server) -> Listener | None:
    """Bind the named pipe with a few retries (Windows may not have released it)."""
    max_retries = 15
    for attempt in range(max_retries):
        try:
            return Listener(PIPE_ADDRESS, family="AF_PIPE", authkey=AUTHKEY)
        except (PermissionError, OSError) as e:
            if attempt < max_retries - 1:
                server.log(f"bind {PIPE_ADDRESS} failed (attempt {attempt + 1}): {e}; retrying in 2s")
                print(f"[server] bind attempt {attempt + 1} failed: {e}; retrying", flush=True)
                time.sleep(2)
            else:
                server.log(f"bind {PIPE_ADDRESS} failed after {max_retries} attempts: {e}")
                print(f"[server] bind failed after {max_retries} attempts: {e}", flush=True)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="persistent local-mineru server")
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="append debug logs to this file",
    )
    args = parser.parse_args()

    server = Server(log_path=_normalize_log_path(args.log))
    server.log(f"server starting with argv={sys.argv[1:]}")

    server.listener = _bind_listener(server)
    if server.listener is None:
        return 2

    server.log(f"listener ready on {PIPE_ADDRESS}")
    server.log("kicking off background runtime init")
    server._start_init_thread()
    server.start_idle_watchdog()
    print(
        f"local-mineru server listening on {PIPE_ADDRESS} (pid={os.getpid()}, "
        f"version={SERVER_VERSION})",
        flush=True,
    )

    worker = threading.Thread(target=server.serve_forever, name="accept-loop", daemon=True)
    worker.start()

    try:
        while not server.shutdown_event.wait(timeout=0.5):
            if not worker.is_alive():
                server.log("accept-loop thread exited unexpectedly")
                return 1
    finally:
        try:
            if server.listener is not None:
                server.listener.close()
        except Exception:
            pass

    worker.join(timeout=server.shutdown_timeout)
    if worker.is_alive():
        server.log(f"worker did not finish within {server.shutdown_timeout:.1f}s; forcing exit")
        print(
            f"[server] worker did not finish within {server.shutdown_timeout:.1f}s; forcing exit",
            flush=True,
        )
        os._exit(1)
    server.log("server exited cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
