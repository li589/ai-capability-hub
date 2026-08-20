#!/usr/bin/env python3
"""SciencePal SDK 脚本公共函数。"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from sciencepal import SciencePal
from sciencepal.utils.constants import DEFAULT_BASE_URL

TERMINAL_STATUSES = {"completed", "failed", "stopped"}
SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_ENV_PATH = SKILL_ROOT / ".env"


def load_skill_env() -> None:
    """从 skill 目录加载 .env，不覆盖已有环境变量。"""
    if not SKILL_ENV_PATH.exists():
        return

    for raw_line in SKILL_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_access_token() -> str:
    """从环境变量读取 access token。"""
    load_skill_env()
    token = os.getenv("SCIENCEPAL_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            f"缺少 SCIENCEPAL_ACCESS_TOKEN，请在环境变量或 {SKILL_ENV_PATH} 中配置"
        )
    return token


def get_base_url() -> str:
    """从环境变量读取 base URL。"""
    load_skill_env()
    return os.getenv("SCIENCEPAL_BASE_URL", DEFAULT_BASE_URL)


def create_client() -> SciencePal:
    """创建 SDK 客户端。"""
    return SciencePal(access_token=get_access_token(), base_url=get_base_url())


def is_terminal_status(status: str | None) -> bool:
    """判断是否为终态。"""
    return status in TERMINAL_STATUSES


async def list_all_files(client: SciencePal, sandbox_id: str, root: str = "/"):
    """递归列出 sandbox 中的所有文件。"""
    pending = [root]
    files = []
    while pending:
        current = pending.pop()
        entries = await client.sandbox.list_files(sandbox_id, current)
        for entry in entries:
            if entry.is_dir:
                pending.append(entry.path)
            else:
                files.append(entry)
    return files


async def download_all_files(
    client: SciencePal, sandbox_id: str, output_dir: str, root: str = "/"
) -> list[str]:
    """下载 sandbox 中的所有文件。"""
    files = await list_all_files(client, sandbox_id, root=root)
    downloaded: list[str] = []
    base_path = Path(output_dir)
    for file_info in files:
        remote_path = file_info.path
        local_path = base_path / remote_path.lstrip("/")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        content = await client.sandbox.read_file(sandbox_id, remote_path)
        local_path.write_bytes(content)
        downloaded.append(str(local_path))
    return downloaded


async def poll_run_status(
    client: SciencePal,
    agent_run_id: str,
    poll_interval: float = 5.0,
    timeout_seconds: float | None = None,
):
    """轮询 agent run 状态直到终态。"""
    start = asyncio.get_running_loop().time()
    while True:
        run = await client.runs.get(agent_run_id)
        if is_terminal_status(run.status):
            return run
        if timeout_seconds is not None:
            elapsed = asyncio.get_running_loop().time() - start
            if elapsed >= timeout_seconds:
                raise TimeoutError(
                    f"轮询超时: agent_run_id={agent_run_id}, timeout={timeout_seconds}s"
                )
        await asyncio.sleep(poll_interval)
