#!/usr/bin/env python3
"""SCRM 开放平台机器人 App Key 客户端。

用于企微智能机器人对话场景：以机器人消息中的 sender_id + bot_id 直接向
SCRM 开放平台查询或创建该员工的个人级别 SCRM_APP_KEY。

调用接口：
  POST /openapi/claw/robot/personal/app-key

配置读取策略（与 scrm 主流程统一）：
  - base_url：读 SCRM_BASE_URL，默认 https://open.wshoto.com
  - SSL 跳过：读 SCRM_SKIP_SSL_VERIFY
  - 服务商主体 ID（sp_corp_id）：ROBOT_SCRM_PROVIDER_ID（scrm 侧无对应物，保留原名）
"""
from __future__ import annotations

import json
import os
import ssl
from typing import Any
from urllib import error, request as url_request

from utils import ApiError

DEFAULT_SCRM_BASE_URL = "https://open.wshoto.com"

# 服务商主体标识（sp_corp_id），即服务商企业 ID。可通过 ROBOT_SCRM_PROVIDER_ID 覆盖。
DEFAULT_SCRM_PROVIDER_ID = os.getenv("ROBOT_SCRM_PROVIDER_ID", "wx28adff7eb4c338ad")

_ENDPOINT_GET_OR_CREATE_APP_KEY = "/openapi/claw/robot/personal/app-key"


def resolve_base_url() -> str:
    """解析 SCRM 开放平台基础地址：读 SCRM_BASE_URL，默认官方地址。"""
    return os.getenv("SCRM_BASE_URL") or DEFAULT_SCRM_BASE_URL


def _skip_ssl_verify() -> bool:
    """是否跳过 SSL 校验：读 SCRM_SKIP_SSL_VERIFY。"""
    return os.getenv("SCRM_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes")


def _get_ssl_context() -> ssl.SSLContext:
    if _skip_ssl_verify():
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """向 SCRM 开放平台发送 JSON POST 请求。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = url_request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    ssl_context = _get_ssl_context()
    try:
        with url_request.urlopen(req, timeout=15, context=ssl_context) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise ApiError(f"SCRM 开放平台 HTTP {exc.code}: {raw[:300]}", status=exc.code) from exc
    except error.URLError as exc:
        raise ApiError(f"SCRM 开放平台请求失败: {exc.reason}") from exc

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApiError(f"SCRM 开放平台响应非 JSON: {raw[:200]}") from exc

    if result.get("code") != 0:
        raise ApiError(
            result.get("msg") or "SCRM 开放平台接口返回失败",
            code=result.get("code"),
            response_body=result,
        )

    return result


def get_or_create_app_key(
    open_user_id: str,
    source_botid: str,
    sp_corp_id: str = "",
    scrm_base_url: str = "",
) -> str:
    """查询或创建员工的个人级别 SCRM APP KEY。

    直接使用机器人消息中的 sender_id 和 bot_id 获取 APP KEY，无需预先进行 userid 转换。

    调用 POST /openapi/claw/robot/personal/app-key。

    Args:
        open_user_id: 服务商主体下的加密员工ID（即机器人消息中的 sender_id）
        source_botid: 企业智能机器人ID（即机器人消息中的 bot_id）
        sp_corp_id: 服务商主体标识（sp_corp_id），为空时使用 DEFAULT_SCRM_PROVIDER_ID
        scrm_base_url: SCRM 开放平台基础地址，为空时按 resolve_base_url() 解析

    Returns:
        员工的 SCRM APP KEY 字符串

    Raises:
        ApiError: 接口调用失败，或响应中缺少 app_key 字段
    """
    resolved_sp_corp_id = sp_corp_id or DEFAULT_SCRM_PROVIDER_ID
    resolved_base_url = scrm_base_url or resolve_base_url()
    url = f"{resolved_base_url.rstrip('/')}{_ENDPOINT_GET_OR_CREATE_APP_KEY}"
    payload = {
        "open_user_id": open_user_id,
        "source_botid": source_botid,
        "sp_corp_id": resolved_sp_corp_id,
    }
    result = _post_json(url, payload)

    app_key = result.get("data", {}).get("app_key")
    if not app_key:
        raise ApiError(
            "SCRM 开放平台响应中缺少 app_key 字段",
            response_body=result,
        )

    return app_key
