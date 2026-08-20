from __future__ import annotations

import datetime
import fcntl
import json
import os
import tempfile
from typing import Any, Callable

from state_path import resolve_state_dir

DEFAULT_AGENT_ID = "agt-tmpl-default"

_MAX_CONCURRENT_DEFAULT = 5

MAIN_HANDLE = "main"

def _now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")

def state_dir_of(state_dir: str | None) -> str:
    return state_dir or resolve_state_dir()

def _last_used_path(state_dir: str) -> str:
    return os.path.join(state_dir, "last_used_agent.json")

def _sessions_dir(state_dir: str) -> str:
    return os.path.join(state_dir, "sessions")

def _handle_path(state_dir: str, handle: str) -> str:
    if not handle or not all(c.isascii() and (c.isalnum() or c == "_") for c in handle):
        raise ValueError(f"非法 handle: {handle!r}（仅允许字母数字下划线）")
    return os.path.join(_sessions_dir(state_dir), f"{handle}.json")

def _read_json(path: str) -> dict[str, Any] | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None

def _atomic_write_json(path: str, data: dict[str, Any]) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp", prefix=".wr-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

class _FileLock:

    def __init__(self, path: str):
        self.lock_path = path + ".lock"
        self._lf = None

    def __enter__(self) -> "_FileLock":
        os.makedirs(os.path.dirname(os.path.abspath(self.lock_path)) or ".", exist_ok=True)
        self._lf = open(self.lock_path, "w")
        fcntl.flock(self._lf.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._lf is not None:
            try:
                fcntl.flock(self._lf.fileno(), fcntl.LOCK_UN)
            finally:
                self._lf.close()

def load_last_used(state_dir: str | None = None) -> dict[str, Any] | None:
    sd = state_dir_of(state_dir)
    data = _read_json(_last_used_path(sd))
    if not data or not data.get("agent_id"):
        return None
    return data

def save_last_used(state_dir: str | None, agent_id: str, name: str = "") -> None:
    if not agent_id or agent_id == DEFAULT_AGENT_ID:
        return
    sd = state_dir_of(state_dir)
    data = {"agent_id": agent_id, "name": name, "updated_at": _now_iso()}
    _atomic_write_json(_last_used_path(sd), data)

def clear_last_used(state_dir: str | None = None) -> bool:
    sd = state_dir_of(state_dir)
    path = _last_used_path(sd)
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False

def _new_session_record(
    handle: str,
    agent_id: str,
    name: str,
    session_id: str,
    run_id: str,
    title: str = "",
) -> dict[str, Any]:
    return {
        "handle": handle,
        "agent_id": agent_id,
        "name": name,
        "session_id": session_id,
        "run_id": run_id,
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "emitted_len": 0,
        "title": title,
    }

def claim_handle(state_dir: str | None, preferred: str | None = None) -> str:
    sd = state_dir_of(state_dir)
    os.makedirs(_sessions_dir(sd), exist_ok=True)
    candidates: list[str]
    if preferred:
        candidates = [preferred]
    else:
        candidates = [f"s{i}" for i in range(1, 1000)]
    for h in candidates:
        path = _handle_path(sd, h)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if preferred:
                raise FileExistsError(f"handle {preferred!r} 已存在")
            continue

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"handle": h, "status": "pending"}, f, ensure_ascii=False)
        return h
    raise RuntimeError("claim_handle: 候选 handle 耗尽")

def load_session(state_dir: str | None, handle: str) -> dict[str, Any] | None:
    sd = state_dir_of(state_dir)
    return _read_json(_handle_path(sd, handle))

def save_session(state_dir: str | None, handle: str, data: dict[str, Any]) -> None:
    sd = state_dir_of(state_dir)
    path = _handle_path(sd, handle)
    with _FileLock(path):
        _atomic_write_json(path, data)

def update_session(
    state_dir: str | None,
    handle: str,
    fn: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> dict[str, Any] | None:
    sd = state_dir_of(state_dir)
    path = _handle_path(sd, handle)
    with _FileLock(path):
        data = _read_json(path) or {}
        new = fn(dict(data))
        if new is not None:
            _atomic_write_json(path, new)
        return new

def delete_session(state_dir: str | None, handle: str) -> bool:
    sd = state_dir_of(state_dir)
    path = _handle_path(sd, handle)
    removed = False
    try:
        os.remove(path)
        removed = True
    except FileNotFoundError:
        pass
    try:
        os.remove(path + ".lock")
    except FileNotFoundError:
        pass
    return removed

def list_sessions(state_dir: str | None) -> list[dict[str, Any]]:
    sd = state_dir_of(state_dir)
    sdir = _sessions_dir(sd)
    if not os.path.isdir(sdir):
        return []
    out: list[dict[str, Any]] = []
    for name in os.listdir(sdir):
        if not name.endswith(".json") or name.startswith("."):
            continue
        data = _read_json(os.path.join(sdir, name))
        if isinstance(data, dict):
            data.setdefault("handle", name[:-5])
            out.append(data)
    out.sort(key=lambda d: d.get("started_at") or "", reverse=True)
    return out

def count_active(state_dir: str | None) -> int:
    active = {"running", "streaming", "pending"}
    return sum(1 for s in list_sessions(state_dir) if s.get("status") in active)

def max_concurrent() -> int:
    try:
        v = int(os.environ.get("TCOP_SRE_MAX_CONCURRENT", "") or _MAX_CONCURRENT_DEFAULT)
        return max(1, v)
    except ValueError:
        return _MAX_CONCURRENT_DEFAULT

def migrate_legacy_state(state_dir: str | None = None) -> None:
    sd = state_dir_of(state_dir)
    legacy = os.path.join(sd, "state.json")
    if not os.path.isfile(legacy):
        return
    data = _read_json(legacy)
    if not isinstance(data, dict):

        try:
            os.rename(legacy, legacy + ".corrupt")
        except OSError:
            pass
        return
    active = data.get("active_agent")
    if not isinstance(active, dict):

        try:
            os.rename(legacy, legacy + ".bak")
        except OSError:
            pass
        return

    agent_id = active.get("agent_id") or ""
    name = active.get("name") or ""
    session_id = active.get("session_id") or ""

    if agent_id and agent_id != DEFAULT_AGENT_ID and load_last_used(sd) is None:
        save_last_used(sd, agent_id, name)

    if session_id and load_session(sd, MAIN_HANDLE) is None:
        rec = _new_session_record(
            MAIN_HANDLE, agent_id, name, session_id, run_id="", title=""
        )

        rec["status"] = "completed"
        rec["finished_at"] = active.get("updated_at")
        save_session(sd, MAIN_HANDLE, rec)

    try:
        os.rename(legacy, legacy + ".bak")
    except OSError:
        pass
