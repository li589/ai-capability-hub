# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Persistent Screenshot Q&A (VLM) server.

Listens on the Windows named pipe ``\\\\.\\pipe\\local-screenshot-qa`` via
``multiprocessing.connection.Listener`` and dispatches image-question requests
sent by ``client.py``. Keeps the Qwen3-VL model loaded across invocations so the
CLI avoids paying the cold-start cost every time.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import traceback
import uuid
from multiprocessing.connection import Listener
from pathlib import Path

from model_download import (
    ModelInfo,
    ensure_models,
    load_model_infos,
    validate_model_dir,
)

PIPE_ADDRESS = r"\\.\pipe\local-screenshot-qa"
AUTHKEY = b"local-screenshot-qa"
DEFAULT_SHUTDOWN_TIMEOUT = 10.0
DEFAULT_MAX_NEW_TOKENS = 512
STATE_STARTING = "starting"
STATE_DOWNLOADING = "downloading"
STATE_LOADING = "loading"
STATE_RUNNING = "running"
STATE_ERROR = "error"

OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
MODELS_ROOT = OPENVINO_ROOT / "models"
RUNTIME_ROOT = OPENVINO_ROOT / "screenshot-qa"

_HERE = Path(__file__).resolve().parent
INFO_JSON = _HERE / "info.json" if (_HERE / "info.json").exists() else _HERE.parent / "info.json"
MODEL_INFOS = load_model_infos(INFO_JSON)
MODEL_INFO = MODEL_INFOS[0]
MODEL_DIR = MODELS_ROOT / MODEL_INFO.dir_name

IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

LOG_LOCK = threading.Lock()


def _normalize_log_path(log_path: str | None) -> Path | None:
    if not log_path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = f"~/.openvino/log/screenshot-qa-server-py-{timestamp}.log"
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


def _validate_model_dir(local_dir: Path):
    return validate_model_dir(local_dir, MODEL_INFO.required_files)


def _ensure_required_model(log_path: Path | None = None) -> None:
    if _validate_model_dir(MODEL_DIR).ok:
        return

    def _logger(message: str):
        print(f"[server] {message}", flush=True)
        _log_message(log_path, message)

    ensure_models(MODEL_INFOS, MODELS_ROOT, logger=_logger)

    final = _validate_model_dir(MODEL_DIR)
    if not final.ok:
        _log_message(log_path, f"model download did not complete: {final.reason}")
        raise RuntimeError(f"model download did not complete: {final.reason}")


def _pick_device(log_path: Path | None) -> str:
    import openvino as ov
    devices = ov.Core().available_devices
    _log_message(log_path, f"openvino devices: {devices}")
    for d in devices:
        if "GPU" in d:
            return d
    return "CPU"


def _outputs_dir() -> Path:
    return RUNTIME_ROOT / "outputs"


class Server:
    def __init__(self, log_path: Path | None = None) -> None:
        self.start_time = time.time()
        self.shutdown_event = threading.Event()
        self.shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
        self.listener: Listener | None = None
        self.runtime_lock = threading.Lock()
        self.vlm_model = None
        self.device: str | None = None
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
            self.log("init thread: downloading required model")
            try:
                import beacon
                beacon.emit("download", "ensuring model present")
            except Exception:
                pass
            _ensure_required_model(self.log_path)

            with self.runtime_lock:
                self.state = STATE_LOADING
            self.log("init thread: loading VLM model")

            device = _pick_device(self.log_path)

            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from vlm_engine import OVQwen3VLModel

            try:
                import beacon
                beacon.emit("load", f"loading model on {device}")
            except Exception:
                pass
            model = OVQwen3VLModel.from_pretrained(str(MODEL_DIR), device=device)

            with self.runtime_lock:
                self.vlm_model = model
                self.device = device
                self.state = STATE_RUNNING
            self.log(f"init thread: VLM model ready (device={device})")
            try:
                import beacon
                beacon.emit("server", "listening", terminal=False)
            except Exception:
                pass
        except Exception:
            error_text = traceback.format_exc()
            with self.runtime_lock:
                self.init_error = error_text
                self.state = STATE_ERROR
            self.log(f"init thread failed:\n{error_text}")
            try:
                import beacon
                beacon.emit("error", "model init failed", terminal=True)
            except Exception:
                pass

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

    def _do_generate(self, question: str, image: str) -> dict:
        image_path = Path(image).expanduser()
        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")
        suffix = image_path.suffix.lower()
        if suffix not in IMAGE_FORMATS:
            raise ValueError(f"Unsupported image format: {suffix}")

        question = question or "Describe this image."

        try:
            import beacon
            beacon.emit("generate", f"answering {image_path.name}")
        except Exception:
            pass

        answer = self.vlm_model.generate(
            question=question,
            image_path=str(image_path),
            max_new_tokens=DEFAULT_MAX_NEW_TOKENS,
        )

        # Persist the answer + an honest-verdict sidecar (preserved from the
        # source skill — the receipt is part of the contract).
        verdict_path = None
        try:
            import verdict
            out_dir = _outputs_dir()
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{uuid.uuid4().hex}.answer.json"
            out_file.write_text(
                json.dumps(
                    {"question": question, "answer": answer, "image_path": str(image_path)},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            side = verdict.write_sidecar(out_file, model_id=MODEL_INFO.model_id)
            verdict_path = str(side)
            try:
                import beacon
                beacon.emit("done", f"wrote {out_file.name}", terminal=True)
            except Exception:
                pass
        except Exception:
            # Sidecar is best-effort; never fail the answer over a receipt.
            self.log(f"verdict sidecar failed:\n{traceback.format_exc()}")

        return {
            "answer": answer,
            "source_image": str(image_path),
            "verdict_path": verdict_path,
        }

    def dispatch(self, msg: dict) -> dict:
        op = msg.get("op")
        self.log(f"dispatching op={op!r}")

        if op == "request":
            question = msg.get("question", "")
            image = msg.get("image", "")
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                model = self.vlm_model
                device = self.device
            if state != STATE_RUNNING or model is None:
                self.log(f"request rejected: state={state}")
                reply = {
                    "ok": False,
                    "state": state,
                    "error": f"runtime not ready: {state}",
                }
                if state == STATE_ERROR and init_error:
                    reply["error"] = init_error
                return reply
            try:
                t0 = time.time()
                result = self._do_generate(question, image)
                total_time = time.time() - t0
                reply = {
                    "ok": True,
                    "state": STATE_RUNNING,
                    "answer": result["answer"],
                    "source_image": result["source_image"],
                    "verdict_path": result.get("verdict_path"),
                    "device": device or "unknown",
                    "timing": {"total": round(total_time, 3)},
                }
                self.log(f"request completed in {total_time:.3f}s")
                return reply
            except Exception:
                error_text = traceback.format_exc()
                self.log(f"request failed:\n{error_text}")
                return {
                    "ok": False,
                    "state": STATE_RUNNING,
                    "error": error_text,
                }

        if op == "status":
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                device = self.device
            self.log(f"status requested: state={state}")
            reply = {
                "ok": True,
                "state": state,
                "pid": os.getpid(),
                "uptime_s": time.time() - self.start_time,
                "device": device or "not_loaded",
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
                self.log(f"server reply ok={reply.get('ok')}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="persistent screenshot-qa VLM server")
    parser.add_argument("--log", type=str, default=None, help="append debug logs to this file")
    args = parser.parse_args()

    server = Server(log_path=_normalize_log_path(args.log))
    server.log(f"server starting with argv={sys.argv[1:]}")
    try:
        server.listener = Listener(PIPE_ADDRESS, family="AF_PIPE", authkey=AUTHKEY)
    except OSError as e:
        server.log(f"bind failed: {e}")
        print(f"[server] bind failed: {e}", flush=True)
        return 2

    server.log(f"listener ready on {PIPE_ADDRESS}")
    server.log("kicking off background runtime init")
    server._start_init_thread()
    print(
        f"screenshot-qa server listening on {PIPE_ADDRESS} (pid={os.getpid()})",
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
        print(f"[server] worker did not finish within {server.shutdown_timeout:.1f}s; forcing exit", flush=True)
        os._exit(1)
    server.log("server exited cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
