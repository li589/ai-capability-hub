# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""Persistent realtime-translator server.

Unlike the one-shot skills (local-asr / local-tts), this server hosts a
*long-running interactive pipeline*: it opens the microphone, runs
VAD -> streaming ASR -> translation -> TTS, and pushes live results over a
WebSocket to a web UI. The server therefore does not answer per-call
"request" ops; instead it boots the whole ``LivePipeline`` once and keeps it
running until shutdown.

Listens on the Windows named pipe ``\\\\.\\pipe\\local-realtime-translator``
for control ops (``status`` / ``shutdown``) from ``client.py``.

State machine:

    starting -> downloading -> loading -> running
                                        |-> error
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import traceback
from multiprocessing.connection import Listener
from pathlib import Path

# --- make the bundled skill package importable ----------------------------
# server.py lives in <skill_root>/scripts/. The translator package and
# config.py sit at <skill_root>/. Put both scripts/ (for ensure_models,
# model_download) and the skill root (for `import config` / `import translator`)
# on sys.path.
_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
for _p in (str(_HERE), str(_SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Pre-import torch on the MAIN thread, as early as possible.
#
# Full investigation: docs/torch-winerror-1114调查.md (local-only, gitignored).
#
# Downstream, torch is first imported INDIRECTLY (`from modelscope import ...`
# -> `import torch`) on a background init thread. On some spawned-process
# environments that has surfaced as `WinError 1114` (c10.dll initialization
# routine failed) — a DLL whose DllMain failed to initialize, often tied to
# load order / thread context. The confirmed direct cause was an over-new torch
# (unbounded `torch>=2.0.0` resolved to 2.12.0, whose native DLLs failed to
# init on a clean conda-based venv); requirements.txt now pins torch==2.4.1.
# This main-thread pre-import is an ADDITIONAL defensive mitigation, not a
# verified root fix: it forces torch's native DLLs to initialize here, on the
# main thread before any heavy framework import, so a later worker-thread import
# just hits the cache. Best-effort: if it fails we swallow it and let the normal
# loading path surface the real error in the server log.
try:
    import torch  # noqa: F401  (imported for its DLL-init side effect)
except Exception:
    # torch failed to load even here on the main thread (e.g. WinError 1114).
    # Dump this process's REAL environment so the spawned-process failure can be
    # root-caused against a working shell. Costs nothing on the success path —
    # only runs when torch actually fails to import.
    def _diag_dump_env() -> None:
        import os as _os
        import sys as _sys
        import traceback as _tb
        try:
            diag_dir = Path(_os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino" / "log"
            diag_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            out = diag_dir / f"rt-translator-DIAG-env-{ts}.txt"
            lines = ["=== torch import FAILED on main thread ===", _tb.format_exc(),
                     "=== sys.executable ===", _sys.executable,
                     "=== sys.path ===", *_sys.path,
                     "=== PATH (split) ===", *(_os.environ.get("PATH", "").split(_os.pathsep)),
                     "=== full environ ==="]
            lines += [f"{k}={_os.environ[k]}" for k in sorted(_os.environ)]
            out.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass
    _diag_dump_env()

# Route HuggingFace downloads (MeloTTS, bert-base-uncased) through the CN mirror
# before any huggingface_hub import happens in the loading phase. Also register
# the bundled NLTK data dir before g2p_en/melo import (g2p_en downloads from
# GitHub at import time otherwise, which hangs on a blocked network).
import config  # noqa: E402
config.apply_hf_mirror()
config.ensure_bundled_nltk_data()

PIPE_ADDRESS = r"\\.\pipe\local-realtime-translator"
AUTHKEY = b"local-realtime-translator"
DEFAULT_SHUTDOWN_TIMEOUT = 10.0

STATE_STARTING = "starting"
STATE_DOWNLOADING = "downloading"
STATE_LOADING = "loading"
STATE_RUNNING = "running"
STATE_ERROR = "error"

for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            # errors="replace" so a stray non-GBK char never crashes logging.
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

LOG_LOCK = threading.Lock()


def _normalize_log_path(log_path: str | None) -> Path | None:
    if not log_path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = f"~/.openvino/log/rt-translator-server-py-{timestamp}.log"
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


class Server:
    def __init__(self, src_lang: str, tgt_lang: str, log_path: Path | None = None) -> None:
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.start_time = time.time()
        self.shutdown_event = threading.Event()
        self.shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
        self.listener: Listener | None = None
        self.runtime_lock = threading.Lock()
        self.pipeline = None
        self.log_path = log_path
        self.state: str = STATE_STARTING
        self.init_error: str = ""
        self.init_thread: threading.Thread | None = None
        self.pipeline_thread: threading.Thread | None = None

    def log(self, message: str) -> None:
        _log_message(self.log_path, message)

    # ── ports for the web UI (read from the skill's config) ───────────
    def _web_info(self) -> dict:
        try:
            import config
            return {
                "ws_url": f"ws://{config.WS_HOST}:{config.WS_PORT}",
                "web_url": f"http://{config.WS_HOST}:{config.WS_PORT + 1}",
            }
        except Exception:
            return {"ws_url": None, "web_url": None}

    # ── init worker: download -> load -> run ──────────────────────────
    def _init_runtime_worker(self) -> None:
        try:
            with self.runtime_lock:
                self.state = STATE_DOWNLOADING
            self.log("init: downloading models")

            import ensure_models

            def _dl_log(msg: str) -> None:
                print(f"[server] {msg}", flush=True)
                self.log(msg)

            ensure_models.download_all(_dl_log)

            with self.runtime_lock:
                self.state = STATE_LOADING
            self.log("init: loading pipeline models")

            from translator.live_pipeline import LivePipeline

            pipeline = LivePipeline(
                src_lang=self.src_lang,
                tgt_lang=self.tgt_lang,
                enable_ws=True,
            )
            pipeline.load_models()

            # LivePipeline.start() blocks in its main capture loop, so run it on
            # a dedicated thread. It brings up the WebSocket + HTTP servers and
            # begins listening to the microphone.
            def _run_pipeline() -> None:
                try:
                    pipeline.start()
                except Exception:
                    err = traceback.format_exc()
                    self.log(f"pipeline crashed:\n{err}")
                    with self.runtime_lock:
                        self.init_error = err
                        self.state = STATE_ERROR

            self.pipeline_thread = threading.Thread(
                target=_run_pipeline, name="live-pipeline", daemon=True
            )
            self.pipeline_thread.start()

            with self.runtime_lock:
                self.pipeline = pipeline
                self.state = STATE_RUNNING
            info = self._web_info()
            self.log(f"init: pipeline running ({info.get('web_url')})")
        except Exception:
            error_text = traceback.format_exc()
            with self.runtime_lock:
                self.init_error = error_text
                self.state = STATE_ERROR
            self.log(f"init failed:\n{error_text}")

    def _start_init_thread(self) -> None:
        if self.init_thread is not None and self.init_thread.is_alive():
            return
        self.init_thread = threading.Thread(
            target=self._init_runtime_worker, name="runtime-init", daemon=True
        )
        self.init_thread.start()
        self.log("init thread started")

    # ── control-op dispatch ───────────────────────────────────────────
    def dispatch(self, msg: dict) -> dict:
        op = msg.get("op")
        self.log(f"dispatching op={op!r}")

        if op == "status":
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
            reply = {
                "ok": True,
                "state": state,
                "pid": os.getpid(),
                "uptime_s": time.time() - self.start_time,
                "src_lang": self.src_lang,
                "tgt_lang": self.tgt_lang,
            }
            reply.update(self._web_info())
            if state == STATE_ERROR and init_error:
                reply["error"] = init_error
            return reply

        if op == "shutdown":
            timeout = msg.get("timeout", DEFAULT_SHUTDOWN_TIMEOUT)
            try:
                self.shutdown_timeout = float(timeout)
            except (TypeError, ValueError):
                self.shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
            self.log(f"shutdown requested (timeout={self.shutdown_timeout:.1f}s)")
            with self.runtime_lock:
                pipeline = self.pipeline
            if pipeline is not None:
                try:
                    pipeline.stop()
                except Exception:
                    self.log(f"pipeline.stop() error:\n{traceback.format_exc()}")
            self.shutdown_event.set()
            return {"ok": True, "state": "shutting_down"}

        self.log(f"unknown operation: {op!r}")
        return {"ok": False, "error": f"unknown op: {op!r}"}

    def serve_forever(self) -> None:
        assert self.listener is not None
        while not self.shutdown_event.is_set():
            try:
                conn = self.listener.accept()
            except OSError:
                if self.shutdown_event.is_set():
                    return
                raise
            try:
                msg = conn.recv()
                reply = self.dispatch(msg if isinstance(msg, dict) else {})
                conn.send(reply)
            except EOFError:
                self.log("client closed before full request")
            except Exception:
                error_text = traceback.format_exc()
                try:
                    conn.send({"ok": False, "error": error_text})
                except Exception:
                    pass
                self.log(f"accept-loop error:\n{error_text}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="persistent realtime-translator server")
    parser.add_argument("--from", dest="src_lang", default=os.environ.get("RT_SRC_LANG", "zh"))
    parser.add_argument("--to", dest="tgt_lang", default=os.environ.get("RT_TGT_LANG", "en"))
    parser.add_argument("--log", type=str, default=None)
    args = parser.parse_args()

    server = Server(
        src_lang=args.src_lang,
        tgt_lang=args.tgt_lang,
        log_path=_normalize_log_path(args.log),
    )
    server.log(f"server starting with argv={sys.argv[1:]}")
    try:
        server.listener = Listener(PIPE_ADDRESS, family="AF_PIPE", authkey=AUTHKEY)
    except OSError as e:
        server.log(f"bind failed: {e}")
        print(f"[server] bind failed: {e}", flush=True)
        return 2

    server.log(f"listener ready on {PIPE_ADDRESS}")
    server._start_init_thread()
    print(f"rt-translator server listening on {PIPE_ADDRESS} (pid={os.getpid()})", flush=True)

    worker = threading.Thread(target=server.serve_forever, name="accept-loop", daemon=True)
    worker.start()

    try:
        while not server.shutdown_event.wait(timeout=0.5):
            if not worker.is_alive():
                server.log("accept-loop exited unexpectedly")
                return 1
    finally:
        try:
            if server.listener is not None:
                server.listener.close()
        except Exception:
            pass

    worker.join(timeout=server.shutdown_timeout)
    server.log("server exited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
