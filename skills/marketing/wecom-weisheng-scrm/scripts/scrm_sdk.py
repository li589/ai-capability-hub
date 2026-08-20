#!/usr/bin/env python3
"""SCRM Skill 的官方 Python 调用封装。

统一通过 subprocess 调用 `scripts/scrm.py`，并将失败结果转换为 Python 异常，
避免上层调用方手写 JSON 宽松解析后吞掉错误。

@author jzc
@date 2026-05-26 22:50
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


SCRIPT_PATH = Path(__file__).resolve().parent / "scrm.py"


class SCRMCommandError(RuntimeError):
    """SCRM 命令执行失败时抛出的统一异常。"""

    def __init__(
        self,
        message: str,
        *,
        action: str = "",
        error: str = "",
        details: Optional[dict[str, Any]] = None,
        exit_code: int = 1,
        payload: Optional[dict[str, Any]] = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.action = action
        self.error = error
        self.details = details or {}
        self.exit_code = exit_code
        self.payload = payload or {}
        self.stdout = stdout
        self.stderr = stderr


def _build_env(*, app_key: Optional[str], base_url: Optional[str]) -> dict[str, str]:
    """构造子进程环境变量。"""
    env = os.environ.copy()
    if app_key:
        env["SCRM_APP_KEY"] = app_key
    if base_url:
        env["SCRM_BASE_URL"] = base_url
    return env


def _parse_payload(stdout: str, action: str, exit_code: int, stderr: str) -> dict[str, Any]:
    """解析 scrm.py 的标准 JSON 输出。"""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SCRMCommandError(
            "SCRM 命令返回了非 JSON 输出",
            action=action,
            error="invalid_output",
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        ) from exc

    if not isinstance(payload, dict):
        raise SCRMCommandError(
            "SCRM 命令返回了非对象 JSON",
            action=action,
            error="invalid_output",
            exit_code=exit_code,
            payload={"raw": payload},
            stdout=stdout,
            stderr=stderr,
        )
    return payload


def run_scrm_command(
    action: str,
    *arguments: str,
    app_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """执行一个 scrm.py 子命令，失败时直接抛异常。"""
    # Step 1: 组装命令与环境变量
    command = [sys.executable, str(SCRIPT_PATH), action, *arguments]
    env = _build_env(app_key=app_key, base_url=base_url)

    # Step 2: 执行命令并捕获标准输出，避免上层手写 JSON 解析
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    # Step 3: 解析标准输出 JSON，并统一按 success / exit_code 判断是否失败
    payload = _parse_payload(result.stdout, action, result.returncode, result.stderr)
    if result.returncode != 0 or not payload.get("success"):
        raise SCRMCommandError(
            payload.get("message") or "SCRM 命令执行失败",
            action=payload.get("action", action),
            error=payload.get("error", "command_failed"),
            details=payload.get("details", {}),
            exit_code=result.returncode,
            payload=payload,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return payload


def run_scrm_data(
    action: str,
    *arguments: str,
    app_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """执行命令并直接返回 success payload 中的 data。"""
    payload = run_scrm_command(action, *arguments, app_key=app_key, base_url=base_url)
    data = payload.get("data", {})
    return data if isinstance(data, dict) else {"value": data}


def check_env(*, app_key: Optional[str] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """执行 check-env 并返回 data。"""
    return run_scrm_data("check-env", app_key=app_key, base_url=base_url)


def fetch_raw_doc(url: str, *, app_key: Optional[str] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """执行 fetch-raw-doc 并返回 data。"""
    return run_scrm_data("fetch-raw-doc", "--url", url, app_key=app_key, base_url=base_url)


def inspect_api_doc(url: str, *, app_key: Optional[str] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """执行 inspect-api-doc 并返回 data。"""
    return run_scrm_data("inspect-api-doc", "--url", url, app_key=app_key, base_url=base_url)


def check_identity(*, app_key: Optional[str] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """执行 check-identity 并返回 data。"""
    return run_scrm_data("check-identity", app_key=app_key, base_url=base_url)


def list_apis(keyword: str, *, app_key: Optional[str] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """执行 list-apis 并返回 data。"""
    return run_scrm_data("list-apis", "--keyword", keyword, app_key=app_key, base_url=base_url)


def call_api(
    doc_url: str,
    biz_params: Optional[dict[str, Any]] = None,
    *,
    app_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """执行 call-api 并返回 data。"""
    raw_biz_params = json.dumps(biz_params or {}, ensure_ascii=False)
    return run_scrm_data(
        "call-api",
        "--doc-url",
        doc_url,
        "--biz-params",
        raw_biz_params,
        app_key=app_key,
        base_url=base_url,
    )


def upload_image(path: str, *, app_key: Optional[str] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """执行 upload-image 并返回 data。"""
    return run_scrm_data("upload-image", "--path", path, app_key=app_key, base_url=base_url)
