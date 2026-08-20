#!/usr/bin/env python3
"""
fetcher.py — 网络请求层

备：requests 库封装、User-Agent 随机池、Cookie 会话管理、超时重试（指数退避）、
gzip/deflate/br 自动解压。

核心函数：
    fetch_url(url, **kwargs)     — 统一 HTTP 请求，返回 (status_code, headers, content)
    fetch_html(url, **kwargs)    — GET 请求返回 HTML 字符串
    get_random_user_agent()      — 从 20 个 UA 池中随机返回一个
    get_sogou_cookie()           — 从搜狗视频页获取 Cookie
    extract_cookies(headers)     — 从响应头中提取 Cookie 字符串
    sleep(seconds)               — 阻塞等待（兼容 time.sleep 别名）
"""

import random
import time
import logging
from typing import Any, Dict, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# ─── User-Agent 随机池（固定 20 个，与 JS 版本一致） ──────────────────────────
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/123.0.0.0 Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/122.0.0.0 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Mi 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
]

# ─── 默认请求头（与 JS 版本一致） ──────────────────────────────────────────────
DEFAULT_HEADERS: Dict[str, str] = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'identity',  # 不要求压缩，请求库自动处理
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# ─── 默认全局 Session ─────────────────────────────────────────────────────────
_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """获取全局 Session（惰性初始化）"""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


# ─── 工具函数 ─────────────────────────────────────────────────────────────────


def get_random_user_agent() -> str:
    """从 20 个 UA 池中随机返回一个 User-Agent 字符串。"""
    return random.choice(USER_AGENTS)


def sleep(seconds: float) -> None:
    """阻塞等待指定秒数。

    Args:
        seconds: 等待秒数（可浮点数，如 0.5 表示 500ms）。
    """
    time.sleep(seconds)


# ─── 核心请求函数 ─────────────────────────────────────────────────────────────


def fetch_url(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    session: Optional[requests.Session] = None,
    timeout: float = 15.0,
    retries: int = 0,
    **kwargs: Any,
) -> Tuple[int, Dict[str, Any], bytes]:
    """统一的 HTTP(S) 请求工具，带超时与重试（指数退避），自动处理 gzip/deflate/br 解压。

    Args:
        url: 请求 URL。
        method: HTTP 方法（默认 GET）。
        headers: 自定义请求头（会与 DEFAULT_HEADERS 合并）。
        session: requests.Session 实例（不传则使用全局 Session）。
        timeout: 超时秒数（默认 15 秒）。
        retries: 重试次数（每次额外请求的尝试次数；重试等待为指数退避：300ms, 600ms, 1200ms...）。
        **kwargs: 传递给 requests.Session.request 的额外参数。

    Returns:
        (status_code, headers_dict, content_bytes) 三元组。

    Raises:
        requests.RequestException: 所有重试均失败后抛出。
    """
    sess = session or _get_session()
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    last_error_prefix = f'Request failed: {method} {url}'

    for attempt in range(retries + 1):
        try:
            resp = sess.request(
                method=method,
                url=url,
                headers=merged_headers,
                timeout=timeout,
                **kwargs,
            )
            return resp.status_code, dict(resp.headers), resp.content
        except requests.RequestException as e:
            if attempt >= retries:
                raise requests.RequestException(
                    f'{last_error_prefix}: {e}'
                ) from e
            # 指数退避：300ms, 600ms, 1200ms, ...
            wait_ms = 300 + attempt * 300
            logger.debug(
                '请求失败 (attempt %d/%d), %.1f 秒后重试: %s',
                attempt + 1,
                retries + 1,
                wait_ms / 1000.0,
                e,
            )
            time.sleep(wait_ms / 1000.0)

    # 理论上不会到达这里
    raise requests.RequestException(f'{last_error_prefix}: unexpected')


def fetch_html(
    url: str,
    cookie_str: str = '',
    session: Optional[requests.Session] = None,
    timeout: float = 30.0,
) -> str:
    """发起 GET 请求，返回 HTML 字符串。

    Args:
        url: 请求 URL。
        cookie_str: 可选的 Cookie 字符串。
        session: requests.Session 实例。
        timeout: 超时秒数（默认 30 秒）。

    Returns:
        HTML 字符串（UTF-8 解码）。

    Raises:
        requests.RequestException: 请求失败时抛出。
    """
    headers: Dict[str, str] = {
        'User-Agent': get_random_user_agent(),
    }
    if cookie_str:
        headers['Cookie'] = cookie_str

    status_code, resp_headers, content = fetch_url(
        url=url,
        method='GET',
        headers=headers,
        session=session,
        timeout=timeout,
        retries=1,
    )
    return content.decode('utf-8', errors='replace')


# ─── Cookie 管理 ─────────────────────────────────────────────────────────────


def extract_cookies(headers: Dict[str, Any]) -> str:
    """从响应头中提取 Cookie 字符串。

    Args:
        headers: HTTP 响应头字典。

    Returns:
        形如 'key1=value1; key2=value2' 的 Cookie 字符串。
    """
    cookies: list[str] = []
    set_cookie = headers.get('Set-Cookie') or headers.get('set-cookie')

    if not set_cookie:
        return ''

    # requests 可能将 Set-Cookie 合并为字符串列表
    cookie_items: list[str] = []
    if isinstance(set_cookie, list):
        cookie_items = set_cookie
    else:
        cookie_items = [str(set_cookie)]

    for cookie in cookie_items:
        cookie_value = cookie.split(';')[0]
        if cookie_value:
            cookies.append(cookie_value)

    return '; '.join(cookies)


def get_sogou_cookie() -> Dict[str, str]:
    """从搜狗视频页面获取 Cookie（用于绕过搜狗反爬）。

    向 ``https://v.sogou.com/v?ie=utf8&query=&p=40030600`` 发起 GET 请求，
    从响应头中提取 Set-Cookie。

    Returns:
        {'cookie_str': '...', 'cookie_obj': {...}} 字典。
        请求失败时两字段均为空。
    """
    result: Dict[str, str] = {'cookie_str': '', 'cookie_obj': ''}
    try:
        session = _get_session()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'identity',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': get_random_user_agent(),
        }
        resp = session.get(
            'https://v.sogou.com/v?ie=utf8&query=&p=40030600',
            headers=headers,
            timeout=10,
        )
        cookie_str = extract_cookies(dict(resp.headers))

        cookie_obj: Dict[str, str] = {}
        if cookie_str:
            for part in cookie_str.split('; '):
                if '=' in part:
                    key, value = part.split('=', 1)
                    cookie_obj[key.strip()] = value.strip()

        result['cookie_str'] = cookie_str
        result['cookie_obj'] = cookie_obj
    except requests.RequestException:
        logger.warning('获取搜狗 Cookie 失败', exc_info=True)

    return result
