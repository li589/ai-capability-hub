"""WebSocket server for pushing results to clients + HTTP server for web UI."""

import os
import json
import socket
import threading
import queue
import asyncio
from pathlib import Path
from typing import Set

os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + ",127.0.0.1,localhost"
os.environ["no_proxy"] = os.environ.get("no_proxy", "") + ",127.0.0.1,localhost"

import config

_WEB_DIR = Path(__file__).parent / "web"
_OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


class WsServer:
    """WebSocket server that broadcasts results + HTTP server for web UI."""

    def __init__(self):
        self._output_queue: queue.Queue = queue.Queue()
        self._thread = None
        self._running = False
        self._clients: Set = set()
        self._clients_lock = threading.Lock()

    def push(self, msg: dict):
        """Push a message dict to all connected clients."""
        self._output_queue.put(msg)

    def push_asr(self, text: str, is_final: bool, speaker_id: int = -1,
                 start_ms: int = 0, end_ms: int = 0,
                 stage: str = "fast", sentence_id: int = 0):
        """Push ASR result.

        stage distinguishes the two ASR streams for the same sentence:
          - "fast"     — Paraformer streaming (rendered greyish-white)
          - "accurate" — Qwen3-ASR (rendered yellow, streamed then finalized)
        sentence_id ties a sentence's fast partials, accurate partials and final
        together so the UI can update one line in place instead of relying on a
        single global "current partial" element (which races across the two
        streams once the next sentence starts).
        """
        self.push({
            "type": "final" if is_final else "partial",
            "text": text,
            "speaker": f"Speaker_{speaker_id + 1}" if speaker_id >= 0 else None,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "stage": stage,
            "sentence_id": sentence_id,
        })

    def push_translation(self, text: str, src_lang: str, tgt_lang: str,
                         sentence_id: int = 0):
        """Push final translation result."""
        self.push({
            "type": "translation_final",
            "text": text,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "sentence_id": sentence_id,
        })

    def push_translation_partial(self, text: str, src_lang: str, tgt_lang: str,
                                 sentence_id: int = 0):
        """Push partial (streaming) translation result."""
        self.push({
            "type": "translation_partial",
            "text": text,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "sentence_id": sentence_id,
        })

    def push_tts(self, audio_filename: str, sentence_id: int = 0):
        """Push TTS completion notification. audio_filename is just the filename, not full path."""
        self.push({
            "type": "tts_ready",
            "audio_url": f"/audio/{audio_filename}",
            "sentence_id": sentence_id,
        })

    @staticmethod
    def _check_port_free(host: str, port: int, label: str) -> None:
        """Fail fast with a clear (Chinese) message if a port is already taken.

        The WS / HTTP servers bind inside daemon threads where an OSError would
        be swallowed, leaving the server falsely reporting "running" with a dead
        web_url. We probe synchronously here so the collision surfaces up through
        LivePipeline.start() and reaches the user as an init error instead.
        """
        # NOTE: probe WITHOUT SO_REUSEADDR. On Windows SO_REUSEADDR behaves like
        # POSIX SO_REUSEPORT and lets a second socket bind an in-use port, which
        # would hide the very collision we are trying to detect. A plain bind
        # raises WSAEADDRINUSE when the port is actively held by another process.
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind((host, port))
        except OSError as exc:
            raise RuntimeError(
                f"端口 {host}:{port} 已被占用, 无法启动{label}。"
                f"请关闭占用该端口的程序后重试 (scripts\\run.ps1 --stop 可停止旧实例)。"
                f" / port {host}:{port} is already in use ({exc})."
            ) from exc
        finally:
            probe.close()

    def start(self):
        """Start the WebSocket server in a background thread."""
        # Probe both ports before launching the daemon threads so a collision
        # is reported as an init error rather than silently swallowed.
        self._check_port_free(config.WS_HOST, config.WS_PORT, "WebSocket 服务")
        self._check_port_free(config.WS_HOST, config.WS_PORT + 1, "网页服务")

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._http_thread = threading.Thread(target=self._run_http, daemon=True)
        self._http_thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        asyncio.run(self._async_run())

    async def _async_run(self):
        import websockets

        async def handler(websocket):
            with self._clients_lock:
                self._clients.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                with self._clients_lock:
                    self._clients.discard(websocket)

        async def broadcaster():
            while self._running:
                messages = []
                while True:
                    try:
                        messages.append(self._output_queue.get_nowait())
                    except queue.Empty:
                        break

                if messages:
                    with self._clients_lock:
                        clients_snapshot = list(self._clients)
                    for msg in messages:
                        payload = json.dumps(msg, ensure_ascii=False)
                        for ws in clients_snapshot:
                            try:
                                await ws.send(payload)
                            except Exception:
                                with self._clients_lock:
                                    self._clients.discard(ws)

                await asyncio.sleep(0.02)

        server = await websockets.serve(handler, config.WS_HOST, config.WS_PORT)
        await broadcaster()
        server.close()

    def _run_http(self):
        """HTTP server for web UI + audio files."""
        import http.server
        import urllib.parse

        web_dir = str(_WEB_DIR)
        output_dir = str(_OUTPUT_DIR)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                path = urllib.parse.unquote(urllib.parse.urlparse(path).path)
                if path.startswith("/audio/"):
                    filename = path[len("/audio/"):]
                    return os.path.join(output_dir, filename)
                # Default: serve from web dir
                if path == "/":
                    path = "/index.html"
                return os.path.join(web_dir, path.lstrip("/"))

            def log_message(self, format, *args):
                pass  # suppress noisy logs

        port = config.WS_PORT + 1
        # ThreadingHTTPServer, not the single-threaded HTTPServer: the web UI is
        # opened automatically in the user's browser, whose connection(s) can sit
        # idle/half-open. A single-threaded server serves one connection at a
        # time (httpd.timeout only bounds the accept wait, not an in-flight
        # handler), so one wedged browser connection makes every later request —
        # page reloads, audio/*.wav fetches — hang until it times out. A
        # threaded server handles each connection independently. Daemon threads
        # so they never block process shutdown.
        httpd = http.server.ThreadingHTTPServer((config.WS_HOST, port), Handler)
        httpd.daemon_threads = True
        httpd.timeout = 1
        while self._running:
            httpd.handle_request()
