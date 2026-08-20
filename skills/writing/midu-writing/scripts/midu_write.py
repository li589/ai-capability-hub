#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Midu 写作工具（短信授权版）

调用写作接口，支持多轮对话（thread_id）。
鉴权用短信登录得到的 appSecret（MIDU_APP_SECRET）+ userId（MIDU_USER_ID）；
请求头必须带 Authorization / X-Skill-Code / X-User-Id。
缺凭证时引导走 scripts/midu_auth.py 短信验证码登录，禁止跳转官网取 Key。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

import requests


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


API_URL = "https://api.midu.com/ability/skill/write/info"
DEFAULT_TIMEOUT = 600
KEY_ENV = "MIDU_APP_SECRET"
USER_ID_ENV = "MIDU_USER_ID"
SKILL_CODE = "MIDU-WRITING"
KEYS_FILE = Path.home() / ".midu_keys"

AUTH_HINT = (
    f"缺少鉴权凭证（{KEY_ENV} / {USER_ID_ENV}）。请先用短信验证码登录获取：\n"
    "  1) python3 scripts/midu_auth.py --action send --mobile <手机号>\n"
    "  2) python3 scripts/midu_auth.py --action verify --mobile <手机号> --sms_code <验证码>\n"
    "verify 成功后会写入 ~/.midu_keys，业务脚本优先读环境变量，其次读该文件。"
)


class MiduWriteError(RuntimeError):
    pass


def load_keys_file(path: Path = KEYS_FILE) -> dict[str, str]:
    if not path.is_file():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def get_credential(name: str) -> str:
    """优先读环境变量，其次读 ~/.midu_keys（勿假设 export 跨会话仍有效）。"""
    value = os.environ.get(name, "").strip()
    if value:
        return value
    return load_keys_file().get(name, "").strip()


def load_api_key(explicit_key: Optional[str] = None) -> str:
    """读取 appSecret。优先级：显式 --api-key > 环境变量 > ~/.midu_keys。"""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()
    v = get_credential(KEY_ENV)
    if v:
        return v
    raise MiduWriteError(AUTH_HINT)


def load_user_id(explicit_user_id: Optional[str] = None) -> str:
    """读取 userId。优先级：显式 --user-id > 环境变量 > ~/.midu_keys。业务接口强制校验 X-User-Id。"""
    if explicit_user_id and explicit_user_id.strip():
        return explicit_user_id.strip()
    v = get_credential(USER_ID_ENV)
    if v:
        return v
    raise MiduWriteError(AUTH_HINT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="调用蜜度写作 API（短信授权版），支持多轮对话。"
    )
    parser.add_argument(
        "--user_input",
        required=True,
        help="写作指令或补充要求（必填）。",
    )
    parser.add_argument(
        "--thread_id",
        default="",
        help="多轮对话时传入上一次返回的 thread_id；首次可省略，脚本自动生成。",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=None,
        help="appSecret（覆盖环境变量 MIDU_APP_SECRET）",
    )
    parser.add_argument(
        "--user-id",
        dest="user_id",
        default=None,
        help="userId（覆盖环境变量 MIDU_USER_ID）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP 超时秒数，默认 {DEFAULT_TIMEOUT}。",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="格式化输出 JSON。",
    )
    return parser.parse_args()


def normalize_thread_id(thread_id: str) -> str:
    """校验并返回合法的 UUID thread_id；为空时自动生成。"""
    if thread_id:
        try:
            return str(uuid.UUID(thread_id))
        except ValueError as exc:
            raise ValueError(f"thread_id 格式不合法（需为 UUID）：{thread_id}") from exc
    return str(uuid.uuid4())


def build_payload(user_input: str, thread_id: str) -> dict[str, str]:
    user_input = user_input.strip().lstrip("\ufeff")
    if not user_input:
        raise ValueError("--user_input 不能为空。")
    return {"thread_id": thread_id, "user_input": user_input}


def build_headers(api_key: str, user_id: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Skill-Code": SKILL_CODE,
        "X-User-Id": user_id,
    }


def post_json(
    url: str,
    payload: dict[str, Any],
    timeout: int,
    api_key: str,
    user_id: str,
) -> dict[str, Any]:
    try:
        response = requests.post(
            url,
            json=payload,
            headers=build_headers(api_key, user_id),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise MiduWriteError(f"网络请求失败：{exc}") from exc

    if response.status_code in (401, 403):
        raise MiduWriteError(f"鉴权失败或凭证失效（HTTP {response.status_code}）。\n{AUTH_HINT}")
    if response.status_code == 429:
        raise MiduWriteError("请求过于频繁（HTTP 429）。请稍等片刻后重试。")
    if response.status_code >= 500:
        raise MiduWriteError(
            f"服务端错误（HTTP {response.status_code}）。服务暂时不可用，请稍后重试。"
        )
    if not response.ok:
        raise MiduWriteError(f"HTTP {response.status_code}：{response.text}")

    try:
        parsed = response.json()
    except ValueError as exc:
        raise MiduWriteError(f"响应不是合法 JSON：{response.text}") from exc

    if not isinstance(parsed, dict):
        raise MiduWriteError(f"响应 JSON 格式异常（非 object）：{parsed!r}")

    if parsed.get("error"):
        error_text = str(parsed["error"])
        if "api_key" in error_text.lower() or "unauthor" in error_text.lower():
            raise MiduWriteError(f"鉴权失败。\n{AUTH_HINT}")
        raise MiduWriteError(f"API 返回错误：{error_text}")

    return parsed


def print_result(data: dict[str, Any], pretty: bool) -> None:
    if pretty:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False))


def print_error(message: str, pretty: bool) -> int:
    print_result({"error": message}, pretty)
    return 1


def main() -> int:
    args = parse_args()

    try:
        api_key = load_api_key(args.api_key)
        user_id = load_user_id(args.user_id)
        thread_id = normalize_thread_id(args.thread_id)
        payload = build_payload(args.user_input, thread_id)
        response = post_json(API_URL, payload, args.timeout, api_key, user_id)
    except Exception as exc:
        return print_error(str(exc), args.pretty)

    output = dict(response)
    output["thread_id"] = thread_id

    print_result(output, args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
