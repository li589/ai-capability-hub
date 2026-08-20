"""Persistent local-tts server.

Listens on the Windows named pipe ``\\\\.\\pipe\\tts`` via
``multiprocessing.connection.Listener`` and dispatches text-to-speech
requests from ``client.py``. Keeps an OpenVINO Qwen3-TTS pipeline
resident across invocations so each generate avoids cold-start cost.

State machine (same shape as local-txt2img server.py):

    starting -> downloading -> loading -> running
                                        |-> error
"""

from __future__ import annotations

import argparse
import gc
import os
import random
import sys
import threading
import time
import traceback
import uuid
from multiprocessing.connection import Listener
from pathlib import Path
from typing import Any, Optional

import numpy as np
from scipy.io import wavfile

from model_download import (
    ensure_models,
    load_model_infos,
    validate_model_dir,
)
from voices import get_voice_info

PIPE_ADDRESS = r"\\.\pipe\tts"
AUTHKEY = b"tts-local"
DEFAULT_SHUTDOWN_TIMEOUT = 10.0
STATE_STARTING = "starting"
STATE_DOWNLOADING = "downloading"
STATE_LOADING = "loading"
STATE_RUNNING = "running"
STATE_ERROR = "error"

OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"
MODELS_ROOT = OPENVINO_ROOT / "models"
MUSIC_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Music"

_HERE = Path(__file__).resolve().parent
INFO_JSON = _HERE / "info.json" if (_HERE / "info.json").exists() else _HERE.parent / "info.json"
MODEL_INFOS = load_model_infos(INFO_JSON)
MODEL_INFO = MODEL_INFOS[0]
MODEL_ID = MODEL_INFO.model_id
MODEL_DIR = MODELS_ROOT / MODEL_INFO.dir_name
REQUIRED_MODEL_FILES = MODEL_INFO.required_files

# Reference audio lives in the skill directory (static asset), not in .openvino.
# The server process is run from TEMP_DIR; the skill directory is found via the
# SKILL_ROOT environment variable that client.py sets before spawning.
SKILL_ROOT = Path(os.environ.get("LOCAL_TTS_SKILL_ROOT", str(Path(__file__).resolve().parent.parent)))
REF_BASE_DIR = SKILL_ROOT / "assets" / "ref"

DEFAULT_VOICE = "default"
DEFAULT_LANGUAGE = "Chinese"
_INTEL_VENDOR_ID = "0x8086"

SERVER_VERSION = "0.1.0"

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
        log_path = f"~/.openvino/log/tts-server-py-{timestamp}.log"

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
    validation = validate_model_dir(MODEL_DIR, REQUIRED_MODEL_FILES)
    if validation.ok:
        return

    def _logger(message: str):
        _report_download_message(log_path, message)

    ensure_models(MODEL_INFOS, MODELS_ROOT, logger=_logger)

    validation = validate_model_dir(MODEL_DIR, REQUIRED_MODEL_FILES)
    if not validation.ok:
        raise RuntimeError(
            f"required model download did not complete: {MODEL_DIR} ({validation.reason})"
        )


def _resolve_device() -> str:
    try:
        from openvino import Core  # type: ignore
    except ImportError:
        return "CPU"
    try:
        core = Core()
        available = list(core.available_devices)
    except Exception:
        return "CPU"

    for dev in available:
        if dev != "GPU" and not dev.startswith("GPU."):
            continue
        try:
            arch = str(core.get_property(dev, "DEVICE_ARCHITECTURE"))
        except Exception:
            continue
        if _INTEL_VENDOR_ID in arch:
            return dev
    return "CPU"


def _safe_seed() -> int:
    return random.SystemRandom().randint(0, 2**31 - 1)


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
            _ensure_required_model(self.log_path)

            with self.runtime_lock:
                self.state = STATE_LOADING
            self.log("init thread: loading OpenVINO Qwen3-TTS pipeline")

            # TEMP_DIR is where client.py syncs qwen_3_tts_helper.py next to server.py.
            here = Path(__file__).resolve().parent
            if str(here) not in sys.path:
                sys.path.insert(0, str(here))
            from qwen_3_tts_helper import OVQwen3TTSModel  # type: ignore

            device = _resolve_device()
            self.log(f"init thread: resolved device={device}")

            pipeline = OVQwen3TTSModel.from_pretrained(str(MODEL_DIR), device=device)

            with self.runtime_lock:
                self.pipeline = pipeline
                self.loaded_model_id = MODEL_ID
                self.loaded_device = device
                self.state = STATE_RUNNING
            self.log(f"init thread: pipeline ready on device={device}")
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

    def _do_generate(self, prompt: str, voice: str | None, language: str,
                     x_vector_only: bool, ref_audio: str | None,
                     ref_text: str | None, output: str | None, seed: int) -> dict:
        t0 = time.time()

        # Reference resolution.
        if ref_audio and ref_text:
            if not Path(ref_audio).exists():
                return {
                    "ok": True,
                    "success": False,
                    "error_code": "BAD_REF",
                    "error": f"ref_audio not found: {ref_audio}",
                    "prompt": prompt,
                }
            ref_audio_path = ref_audio
            ref_text_content = ref_text
            used_voice = "custom"
        else:
            try:
                ref_audio_path, ref_text_content, used_voice = get_voice_info(
                    REF_BASE_DIR, voice if voice else DEFAULT_VOICE
                )
            except ValueError as exc:
                return {
                    "ok": True,
                    "success": False,
                    "error_code": "GENERATION_FAILED",
                    "error": str(exc),
                    "prompt": prompt,
                }

        # Output path.
        if output:
            output_path = Path(output).expanduser()
            if not output_path.is_absolute():
                output_path = MUSIC_ROOT / output_path
        else:
            output_path = MUSIC_ROOT / f"tts_{int(seed)}_{uuid.uuid4().hex[:8]}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Inference.
        infer_start = time.time()
        try:
            wrapped_text = "......," + prompt + ",......"
            wavs, sr = self.pipeline.generate_voice_clone(
                text=wrapped_text + "……",
                ref_audio=ref_audio_path,
                ref_text=ref_text_content,
                language=language,
                x_vector_only_mode=x_vector_only,
            )
        except Exception as exc:
            return {
                "ok": True,
                "success": False,
                "error_code": "GENERATION_FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "prompt": prompt,
                "timing": {"infer_s": time.time() - infer_start, "save_s": 0.0, "total_s": time.time() - t0},
            }
        infer_s = time.time() - infer_start

        if not wavs:
            return {
                "ok": True,
                "success": False,
                "error_code": "GENERATION_FAILED",
                "error": "pipeline returned no audio",
                "prompt": prompt,
                "timing": {"infer_s": infer_s, "save_s": 0.0, "total_s": time.time() - t0},
            }

        # Save.
        save_start = time.time()
        try:
            wav = np.asarray(wavs[0], dtype=np.float32)
            audio_duration = len(wav) / sr if sr else 0.0
            wav_int16 = np.clip(wav * 32767, -32768, 32767).astype(np.int16)
            wavfile.write(str(output_path), int(sr), wav_int16)
        except Exception as exc:
            return {
                "ok": True,
                "success": False,
                "error_code": "SAVE_FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "prompt": prompt,
                "timing": {"infer_s": infer_s, "save_s": time.time() - save_start, "total_s": time.time() - t0},
            }
        save_s = time.time() - save_start

        total_s = time.time() - t0
        rtf = infer_s / audio_duration if audio_duration > 0 else 0.0

        return {
            "ok": True,
            "success": True,
            "audio_path": str(output_path),
            "prompt": prompt,
            "voice": used_voice,
            "language": language,
            "device": self.loaded_device,
            "model_id": self.loaded_model_id,
            "sample_rate": int(sr) if sr else 0,
            "duration_s": float(audio_duration),
            "rtf": float(rtf),
            "timing": {"infer_s": infer_s, "save_s": save_s, "total_s": total_s},
        }

    def dispatch(self, msg: dict) -> dict:
        op = msg.get("op")
        self.log(f"dispatching op={op!r}")

        if op == "generate":
            prompt = msg.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                return {
                    "ok": False,
                    "success": False,
                    "error_code": "BAD_PROMPT",
                    "error": "prompt must be a non-empty string",
                }

            ref_audio = msg.get("ref_audio")
            ref_text = msg.get("ref_text")
            if (ref_audio is None) ^ (ref_text is None):
                return {
                    "ok": True,
                    "success": False,
                    "error_code": "BAD_REF",
                    "error": "--ref-audio and --ref-text must be provided together",
                    "prompt": prompt,
                }

            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                pipeline = self.pipeline
            if state != STATE_RUNNING or pipeline is None:
                self.log(f"generate rejected: state={state}")
                reply = {
                    "ok": False,
                    "success": False,
                    "state": state,
                    "prompt": prompt,
                    "error": f"runtime not ready: {state}",
                }
                if state == STATE_ERROR and init_error:
                    reply["error"] = init_error
                return reply

            voice = msg.get("voice")
            language = msg.get("language") or DEFAULT_LANGUAGE
            x_vector_only = bool(msg.get("x_vector_only", False))
            output = msg.get("output")
            seed = msg.get("seed")
            if not isinstance(seed, int) or isinstance(seed, bool):
                seed = _safe_seed()

            try:
                reply = self._do_generate(prompt, voice, language, x_vector_only,
                                           ref_audio, ref_text, output, seed)
                reply["state"] = STATE_RUNNING
                self.log(
                    f"generate completed: success={reply.get('success')} "
                    f"audio_path={reply.get('audio_path')}"
                )
                return reply
            except Exception:
                error_text = traceback.format_exc()
                self.log(f"generate failed:\n{error_text}")
                return {
                    "ok": False,
                    "success": False,
                    "state": STATE_RUNNING,
                    "prompt": prompt,
                    "error": error_text,
                }

        if op == "status":
            with self.runtime_lock:
                state = self.state
                init_error = self.init_error
                loaded_model_id = self.loaded_model_id
                loaded_device = self.loaded_device
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
            try:
                with self.runtime_lock:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="persistent local-tts server")
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
        f"local-tts server listening on {PIPE_ADDRESS} (pid={os.getpid()}, "
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
