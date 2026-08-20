#!/usr/bin/env python3
"""SCRM 开放平台 API Client。"""
from __future__ import annotations

import json
import os
import ssl
from typing import Any, Optional
from urllib import error, parse, request

from utils import ApiError, ConfigError

DEFAULT_BASE_URL = "https://open.wshoto.com"

def _get_ssl_context() -> ssl.SSLContext:
    """获取 SSL 上下文，支持通过环境变量跳过验证。"""
    if os.getenv("SCRM_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_personal_access_token(app_key: str, *, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """通过 personal app_key 获取 Access Token 及当前用户身份。"""
    if not app_key or not str(app_key).strip():
        raise ConfigError(
            "缺少有效的 app_key，请确认 SCRM_APP_KEY 已配置或通过 --app-key 传入",
            details={"app_key": app_key},
        )
    query = parse.urlencode({"app_key": app_key})
    url = f"{base_url.rstrip('/')}/openapi/personal_access_token?{query}"
    ssl_context = _get_ssl_context()

    try:
        with request.urlopen(url, timeout=30, context=ssl_context) as response:
            status = response.status
            raw_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            raise ApiError(f"接口请求失败，HTTP {exc.code}", status=exc.code, response_body=raw_body) from exc
        raise ApiError(
            payload.get("msg") or f"接口请求失败，HTTP {exc.code}",
            code=payload.get("code"),
            status=exc.code,
            response_body=payload,
        ) from exc
    except error.URLError as exc:
        raise ApiError(f"接口请求失败：{exc.reason}") from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ApiError("接口返回了非 JSON 内容", status=status, response_body=raw_body) from exc

    if payload.get("code") != 0:
        raise ApiError(
            payload.get("msg") or "接口返回失败",
            code=payload.get("code"),
            status=status,
            response_body=payload,
        )
    return payload.get("data", {})


class SCRMClient:
    """封装开放平台接口调用。"""

    AUTH_ERROR_CODES = {10001, 10010, 10011}

    def __init__(self, access_token: str, *, base_url: str = DEFAULT_BASE_URL, timeout: int = 30, user_id: Optional[str] = None, token_manager: Optional[Any] = None) -> None:
        if not access_token.strip():
            raise ConfigError("缺少 Access Token，请检查 APP_KEY 配置")
        self.access_token = access_token.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_id = user_id
        self.token_manager = token_manager

    def build_url(self, path: str) -> str:
        """拼接完整请求地址并追加 access_token。"""
        clean_path = path if path.startswith("/") else f"/{path}"
        query = parse.urlencode({"access_token": self.access_token})
        return f"{self.base_url}{clean_path}?{query}"

    def get_json(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """发送 GET 请求，params 中的参数会追加到查询字符串。"""
        # Step 1: 构造请求工厂，便于 token 刷新后按新 token 重建 URL
        def request_factory() -> request.Request:
            url = self.build_url(path)
            if params:
                extra = parse.urlencode({k: v for k, v in params.items() if v is not None})
                url = f"{url}&{extra}"
            return request.Request(url, method="GET")

        # Step 2: 执行请求，遇到 token 失效时自动刷新并重试一次
        return self._execute_with_auth_retry(request_factory, retry_on_auth_error=True)

    def post_json(self, path: str, payload: dict[str, Any], *, retry_on_auth_error: bool = False) -> dict[str, Any]:
        """发送 JSON POST 请求。"""
        # Step 1: 构造请求工厂，便于 token 刷新后按新 token 重建 URL
        def request_factory() -> request.Request:
            url = self.build_url(path)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            return request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )

        # Step 2: 执行请求，遇到 token 失效时自动刷新并重试一次
        return self._execute_with_auth_retry(request_factory, retry_on_auth_error=retry_on_auth_error)

    def post_direct(self, path: str, payload: dict[str, Any], *, retry_on_auth_error: bool = False) -> dict[str, Any]:
        """不经 proxy/forward 代理的直接调用。

        语义上标识"直接调用"，内部复用 post_json()。

        Args:
            path: 接口路径。
            payload: 请求体。

        Returns:
            接口响应数据。
        """
        return self.post_json(path, payload, retry_on_auth_error=retry_on_auth_error)

    def post_multipart(self, path: str, body: bytes, *, content_type: str, retry_on_auth_error: bool = False) -> dict[str, Any]:
        """发送 multipart/form-data POST 请求。"""
        # Step 1: 构造请求工厂，便于 token 刷新后按新 token 重建 URL
        def request_factory() -> request.Request:
            url = self.build_url(path)
            return request.Request(
                url,
                data=body,
                headers={"Content-Type": content_type},
                method="POST",
            )

        # Step 2: 执行请求，遇到 token 失效时自动刷新并重试一次
        return self._execute_with_auth_retry(request_factory, retry_on_auth_error=retry_on_auth_error)

    def _execute_with_auth_retry(self, request_factory, *, retry_on_auth_error: bool) -> dict[str, Any]:
        """执行请求，在允许的场景下对 token 失效做一次刷新重试。"""
        # Step 1: 先用当前 token 执行请求
        auth_error: Optional[ApiError] = None
        try:
            return self._execute(request_factory())
        except ApiError as exc:
            if not self._should_refresh_token(exc):
                raise
            auth_error = exc

        # Step 2: 发生 token 失效时强制刷新，并更新 client 上下文
        self.access_token = self.token_manager.get_token(force_refresh=True)
        self.user_id = self.token_manager.get_user_id()

        # Step 3: 写请求禁止自动重放，只刷新 token 供用户显式重试
        if not retry_on_auth_error:
            raise auth_error

        # Step 4: 读请求使用新 token 重建请求并重试一次
        return self._execute(request_factory())

    def _should_refresh_token(self, exc: ApiError) -> bool:
        """判断当前异常是否适合自动刷新 token。"""
        return self.token_manager is not None and exc.code in self.AUTH_ERROR_CODES

    def _execute(self, req: request.Request) -> dict[str, Any]:
        ssl_context = _get_ssl_context()
        try:
            with request.urlopen(req, timeout=self.timeout, context=ssl_context) as response:
                status = response.status
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            raise self._build_http_error(exc.code, raw_body) from exc
        except error.URLError as exc:
            raise ApiError(f"接口请求失败：{exc.reason}") from exc

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ApiError("接口返回了非 JSON 内容", status=status, response_body=raw_body) from exc

        if payload.get("code") != 0:
            raise ApiError(
                payload.get("msg") or "接口返回失败",
                code=payload.get("code"),
                status=status,
                response_body=payload,
            )
        return payload

    def _build_http_error(self, status: int, raw_body: str) -> ApiError:
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return ApiError(
                f"接口请求失败，HTTP {status}",
                status=status,
                response_body=raw_body,
            )

        return ApiError(
            payload.get("msg") or f"接口请求失败，HTTP {status}",
            code=payload.get("code"),
            status=status,
            response_body=payload,
        )
