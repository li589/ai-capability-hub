# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 核心基础设施 · 统一 HTTP 客户端
=====================================================

功能概览:
  - HttpResponse: 模拟 requests 库的最小化响应接口
  - http_get / http_post: 基于 urllib 的无外部依赖 HTTP 请求
  - 双 SSL 上下文: 标准验证优先, 失败后降级为未验证
  - 自动重试: 429/5xx 指数退避, 403/4xx 直接返回(ok=False)
  - 连接复用: 优先使用 urllib3 连接池, 不可用时回退到 urllib

零外部依赖 — 仅使用 Python 标准库。
"""

from __future__ import annotations

import json as _json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

__all__ = ["HttpResponse", "http_get", "http_post"]

# ---------------------------------------------------------------------------
# SSL 上下文
# ---------------------------------------------------------------------------

def _make_ssl_context(verify: bool = True) -> ssl.SSLContext:
    """创建 SSL 上下文。

    Args:
        verify: 是否验证证书。True 使用系统默认 CA,
                False 则跳过验证(仅作为最终降级手段)。
    """
    if verify:
        ctx = ssl.create_default_context()
    else:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


_SSL_VERIFIED = _make_ssl_context(verify=True)
_SSL_UNVERIFIED = _make_ssl_context(verify=False)

# ---------------------------------------------------------------------------
# 连接复用 — 尝试使用 urllib3
# ---------------------------------------------------------------------------

_pool_manager: Any = None

try:
    import urllib3  # type: ignore

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _pool_manager = urllib3.PoolManager(
        num_pools=20,
        maxsize=10,
        retries=False,  # 重试由我们自行控制
        timeout=urllib3.Timeout(connect=10, read=30),
    )
    _USE_URLLIB3 = True
except ImportError:
    _USE_URLLIB3 = False

# ---------------------------------------------------------------------------
# 重试配置
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # 指数退避基数(秒)
_RETRIABLE_STATUS = {429, 500, 502, 503, 504}

# ---------------------------------------------------------------------------
# HttpResponse 响应包装
# ---------------------------------------------------------------------------


class HttpResponse:
    """模拟 requests.Response 的最小化接口。

    Attributes:
        status_code: HTTP 状态码
        text: 响应体文本
        ok: 状态码是否在 2xx 范围内
    """

    def __init__(self, status_code: int, text: str, headers: Optional[Dict[str, str]] = None):
        self.status_code: int = status_code
        self.text: str = text
        self.headers: Dict[str, str] = headers or {}
        self.ok: bool = 200 <= status_code < 300

    def json(self) -> Any:
        """将响应体解析为 JSON。

        Returns:
            解析后的 Python 对象(dict / list / 基本类型)。

        Raises:
            json.JSONDecodeError: 响应体不是合法 JSON。
        """
        return _json.loads(self.text)

    def __repr__(self) -> str:
        return f"<HttpResponse [{self.status_code}]>"


# ---------------------------------------------------------------------------
# 内部请求实现
# ---------------------------------------------------------------------------


def _request_urllib3(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[bytes],
    timeout: float,
    encoding: str = "utf-8",
) -> HttpResponse:
    """通过 urllib3 连接池发送请求(如果可用)。

    注意：urllib3 PoolManager 的 redirect=True 不跟随跨域 301/302，
    因此这里手动检测 3xx 并跟随 Location header（最多 5 次）。
    """
    assert _pool_manager is not None
    max_redirects = 5
    current_url = url
    for _ in range(max_redirects):
        resp = _pool_manager.request(
            method,
            current_url,
            headers=headers,
            body=body,
            timeout=timeout,
            redirect=False,
        )
        if resp.status in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            if not location:
                break
            # 相对路径处理
            if location.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(current_url)
                location = f"{parsed.scheme}://{parsed.netloc}{location}"
            current_url = location
            # 303 强制 GET
            if resp.status == 303:
                method = "GET"
                body = None
            continue
        break
    text = resp.data.decode(encoding, errors="replace")
    resp_headers = dict(resp.headers) if resp.headers else {}
    return HttpResponse(status_code=resp.status, text=text, headers=resp_headers)


def _request_urllib(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[bytes],
    timeout: float,
    encoding: str = "utf-8",
) -> HttpResponse:
    """通过标准库 urllib 发送请求, 具备双 SSL 上下文降级能力。"""
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    for ctx in (_SSL_VERIFIED, _SSL_UNVERIFIED):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read()
                text = raw.decode(encoding, errors="replace")
                resp_headers = dict(resp.headers)
                return HttpResponse(
                    status_code=resp.status, text=text, headers=resp_headers
                )
        except urllib.error.HTTPError as e:
            # HTTPError 也是一个响应, 我们可以读取 body
            raw = e.read() if e.fp else b""
            text = raw.decode(encoding, errors="replace")
            resp_headers = dict(e.headers) if e.headers else {}
            return HttpResponse(
                status_code=e.code, text=text, headers=resp_headers
            )
        except (ssl.SSLError, urllib.error.URLError):
            # SSL 验证失败 → 降级到未验证上下文重试
            if ctx is _SSL_UNVERIFIED:
                raise
            continue

    # 理论上不可达
    raise RuntimeError("请求失败: 所有 SSL 上下文均不可用")


def _do_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[bytes] = None,
    timeout: float = 30.0,
    encoding: str = "utf-8",
) -> HttpResponse:
    """底层请求调度: 优先 urllib3, 降级 urllib, 带自动重试。

    重试策略:
      - 429 / 5xx: 指数退避后重试, 最多 _MAX_RETRIES 次
      - 403 / 其他 4xx: 不重试, 直接返回 HttpResponse(ok=False)
    """
    last_resp: Optional[HttpResponse] = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            if _USE_URLLIB3:
                resp = _request_urllib3(method, url, headers, body, timeout, encoding)
            else:
                resp = _request_urllib(method, url, headers, body, timeout, encoding)
        except Exception:
            if attempt == _MAX_RETRIES:
                raise
            time.sleep(_BACKOFF_BASE * (2 ** attempt))
            continue

        # 可重试状态码 (429/5xx)
        if resp.status_code in _RETRIABLE_STATUS:
            last_resp = resp
            if attempt < _MAX_RETRIES:
                time.sleep(_BACKOFF_BASE * (2 ** attempt))
                continue

        # 403 及其他 4xx: 不重试, 直接返回（调用方通过 resp.ok 判断）
        return resp

    # 所有重试用完, 返回最后一次响应
    if last_resp is not None:
        return last_resp
    raise RuntimeError(f"请求失败且无有效响应: {url}")


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def http_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    encoding: str = "utf-8",
) -> HttpResponse:
    """发送 HTTP GET 请求。

    Args:
        url: 目标 URL。
        params: 查询参数字典, 会被编码追加到 URL。
        headers: 自定义请求头, 会与默认头合并。
        timeout: 超时时间(秒)。
        encoding: 响应体解码编码, 默认 utf-8。

    Returns:
        HttpResponse 实例。状态码 4xx 时 resp.ok=False。

    Raises:
        Exception: 重试耗尽后抛出底层异常。
    """
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{query}"

    merged_headers = {**_DEFAULT_HEADERS, **(headers or {})}
    return _do_request("GET", url, merged_headers, timeout=timeout, encoding=encoding)


def http_post(
    url: str,
    data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
    json_data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> HttpResponse:
    """发送 HTTP POST 请求。

    Args:
        url: 目标 URL。
        data: 表单数据或原始 body。字典会被 url-encoded。
        json_data: JSON 数据, 会被序列化并设置 Content-Type。
              与 data 互斥, json_data 优先。
        headers: 自定义请求头。
        timeout: 超时时间(秒)。

    Returns:
        HttpResponse 实例。
    """
    merged_headers = {**_DEFAULT_HEADERS, **(headers or {})}
    body: Optional[bytes] = None

    if json_data is not None:
        body = _json.dumps(json_data, ensure_ascii=False).encode("utf-8")
        merged_headers.setdefault("Content-Type", "application/json; charset=utf-8")
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
            merged_headers.setdefault(
                "Content-Type", "application/x-www-form-urlencoded"
            )
        elif isinstance(data, str):
            body = data.encode("utf-8")
        else:
            body = data

    return _do_request("POST", url, merged_headers, body=body, timeout=timeout)
