"""Minimal-dependency Jiandaoyun HTTP client."""

import json
import re
import time
import urllib.error
import urllib.request

from .errors import JiandaoyunError


RETRYABLE_CODES = {8303, 8304, 8309}
AUTH_CODES = {8301, 17018, 17052, 17053, 17054}


class APIClient:
    def __init__(self, api_key, *, timeout=30, opener=None):
        self.api_key = api_key
        self.timeout = timeout
        self.opener = opener or urllib.request.urlopen

    def call(self, schema, params, *, allow_read_retries=True):
        url, payload = build_request(schema, params)
        attempts = 3 if schema["risk"] == "read" and allow_read_retries else 1
        for attempt in range(attempts):
            try:
                result = self._post(url, payload)
            except JiandaoyunError as exc:
                if not exc.retryable or attempt + 1 >= attempts:
                    raise
                time.sleep(0.6 * (2 ** attempt))
                continue
            code = result.get("code") if isinstance(result, dict) else None
            if code in AUTH_CODES:
                raise JiandaoyunError(
                    "permission_denied",
                    result.get("msg", "API Key、应用权限或接口权限不足。"),
                    code=code,
                )
            if code in RETRYABLE_CODES:
                if attempt + 1 < attempts:
                    time.sleep(0.6 * (2 ** attempt))
                    continue
                raise JiandaoyunError(
                    "rate_limited",
                    result.get("msg", "简道云接口限流。"),
                    code=code,
                    retryable=True,
                )
            if isinstance(result, dict) and result.get("status") == "failure":
                raise JiandaoyunError(
                    "business_error",
                    result.get("message")
                    or result.get("msg")
                    or "简道云接口返回业务失败。",
                    code=code,
                    retryable=False,
                    details={"status": "failure"},
                )
            return result
        raise JiandaoyunError("request_failed", "请求未完成。")

    def _post(self, url, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "jiandaoyun-api-skill/0.1.0",
            },
        )
        try:
            response = self.opener(request, timeout=self.timeout)
            body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:1000]
            retryable = exc.code == 429
            message = _safe_error_message(body) or f"简道云接口返回 HTTP {exc.code}。"
            raise JiandaoyunError(
                "http_error",
                message,
                code=exc.code,
                retryable=retryable,
            ) from exc
        except urllib.error.URLError as exc:
            raise JiandaoyunError(
                "network_error",
                f"无法连接简道云 API：{exc.reason}",
                retryable=True,
            ) from exc
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise JiandaoyunError(
                "invalid_response",
                "简道云接口返回了无法解析的响应。",
            ) from exc


def build_request(schema, params):
    url = schema["endpoint"]
    path_params = set(re.findall(r"\{([A-Za-z0-9_]+)\}", url))
    for name in path_params:
        value = str(params[name])
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise JiandaoyunError("invalid_input", f"路径参数 {name} 格式不安全。")
        url = url.replace("{" + name + "}", value)
    client_only = set(schema.get("client_only_params", []))
    payload = {}
    for key, value in params.items():
        if key in path_params or key in client_only:
            continue
        definition = schema["params"].get(key, {})
        if value in ("", [], {}) and definition.get("default") == value:
            continue
        payload[key] = value
    return url, payload


def _safe_error_message(body):
    try:
        value = json.loads(body)
    except json.JSONDecodeError:
        return None
    if isinstance(value, dict):
        return value.get("msg") or value.get("message")
    return None
