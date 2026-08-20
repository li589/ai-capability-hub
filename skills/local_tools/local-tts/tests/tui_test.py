"""TUI test program for local-tts server.

Usage:
    pip install textual
    python tui_test.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from multiprocessing.connection import Client
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Log, Static
from textual.reactive import reactive


PIPE_ADDRESS = r"\\.\pipe\tts"
AUTHKEY = b"tts-local"
SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
OPENVINO_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".openvino"


def _try_connect():
    try:
        return Client(PIPE_ADDRESS, authkey=AUTHKEY)
    except (FileNotFoundError, OSError, EOFError):
        return None


def _send_op(op: dict) -> dict | None:
    conn = _try_connect()
    if conn is None:
        return None
    try:
        conn.send(op)
        return conn.recv()
    except (EOFError, OSError):
        return None
    finally:
        conn.close()


class ServerPanel(Static):
    status = reactive("unknown")
    pid = reactive("N/A")
    uptime = reactive("N/A")
    device = reactive("N/A")

    def compose(self) -> ComposeResult:
        yield Static("Server Control", classes="panel-title")
        yield Static(id="status-display")
        yield Horizontal(
            Button("Start", id="btn-start", variant="success"),
            Button("Stop", id="btn-stop", variant="error"),
            Button("Refresh", id="btn-refresh", variant="primary"),
        )

    def watch_status(self, value: str) -> None:
        display = self.query_one("#status-display", Static)
        display.update(
            f"Status: {value}\nPID: {self.pid}\nUptime: {self.uptime}\nDevice: {self.device}"
        )


class TTSApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr 1fr;
        grid-columns: 1fr 2fr;
    }
    .panel-title { text-style: bold; padding: 0 1; }
    #server-panel { row-span: 1; border: solid green; padding: 1; }
    #request-panel { border: solid blue; padding: 1; }
    #log-panel { column-span: 2; border: solid yellow; padding: 1; }
    """

    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh Status")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="server-panel"):
            yield ServerPanel()
        with Vertical(id="request-panel"):
            yield Static("TTS Request", classes="panel-title")
            yield Input(placeholder="Text to synthesize", id="prompt-input")
            yield Input(placeholder="Voice (default)", id="voice-input", value="default")
            yield Input(placeholder="Language (Chinese)", id="lang-input", value="Chinese")
            yield Button("Generate Speech", id="btn-send", variant="primary")
            yield Static("", id="response-display")
        with Vertical(id="log-panel"):
            yield Static("Server Log", classes="panel-title")
            yield Log(id="log-view", max_lines=200)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self._start_server()
        elif event.button.id == "btn-stop":
            self._stop_server()
        elif event.button.id == "btn-refresh":
            self._refresh_status()
        elif event.button.id == "btn-send":
            self._send_request()

    def action_refresh(self) -> None:
        self._refresh_status()

    def _start_server(self) -> None:
        log = self.query_one("#log-view", Log)
        server_py = SCRIPTS_DIR / "server.py"
        if not server_py.exists():
            log.write_line(f"[ERROR] server.py not found at {server_py}")
            return

        venv_python = OPENVINO_ROOT / "venv" / "tts" / "Scripts" / "pythonw.exe"
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        log.write_line(f"[INFO] Starting server: {venv_python} {server_py}")
        try:
            subprocess.Popen(
                [str(venv_python), str(server_py)],
                cwd=str(SCRIPTS_DIR),
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            log.write_line("[INFO] Server process launched")
            time.sleep(1)
            self._refresh_status()
        except Exception as exc:
            log.write_line(f"[ERROR] Failed to start: {exc}")

    def _stop_server(self) -> None:
        log = self.query_one("#log-view", Log)
        reply = _send_op({"op": "shutdown", "timeout": 5.0})
        if reply is None:
            log.write_line("[WARN] Server not reachable")
        else:
            log.write_line(f"[INFO] Shutdown response: {json.dumps(reply)}")
        self._refresh_status()

    def _refresh_status(self) -> None:
        panel = self.query_one(ServerPanel)
        log = self.query_one("#log-view", Log)
        reply = _send_op({"op": "status"})
        if reply is None:
            panel.status = "offline"
            panel.pid = "N/A"
            panel.uptime = "N/A"
            panel.device = "N/A"
            log.write_line("[INFO] Server is offline")
        else:
            panel.status = reply.get("state", "unknown")
            panel.pid = str(reply.get("pid", "N/A"))
            uptime = reply.get("uptime_s", 0)
            panel.uptime = f"{uptime:.1f}s"
            panel.device = reply.get("loaded_device", "N/A")
            log.write_line(f"[INFO] Status: {json.dumps(reply)}")

    def _send_request(self) -> None:
        prompt_input = self.query_one("#prompt-input", Input)
        voice_input = self.query_one("#voice-input", Input)
        lang_input = self.query_one("#lang-input", Input)
        response_display = self.query_one("#response-display", Static)
        log = self.query_one("#log-view", Log)

        prompt = prompt_input.value.strip()
        voice = voice_input.value.strip() or "default"
        language = lang_input.value.strip() or "Chinese"

        if not prompt:
            log.write_line("[WARN] No text specified")
            return

        log.write_line(f"[INFO] Sending: prompt={prompt}, voice={voice}, lang={language}")
        reply = _send_op({
            "op": "generate",
            "prompt": prompt,
            "voice": voice,
            "language": language,
        })
        if reply is None:
            response_display.update("[red]Server not reachable[/red]")
            log.write_line("[ERROR] Server not reachable")
        else:
            formatted = json.dumps(reply, indent=2, ensure_ascii=False)
            response_display.update(formatted)
            log.write_line(f"[INFO] Response: ok={reply.get('ok')} success={reply.get('success')}")


if __name__ == "__main__":
    app = TTSApp()
    app.run()
