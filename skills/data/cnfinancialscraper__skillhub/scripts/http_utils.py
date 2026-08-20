# -*- coding: utf-8 -*-
"""
HTTP 公共基础设施 v7.2 — 零外部依赖纯标准库实现
所有 scraper 模块共用，消除重复代码。

v7.2.0: 软拦截检测接线（200 反爬页面自动识别并重试）、Retry-After 遵从、
      修复空 POST 退化为 GET / download_file 保存错误页 / 熔断 sleep 持锁等 bug。

v4.0: 增强反爬能力 — UA 轮换池、多策略重试、自适应限流、指纹随机化、
      编码检测增强、代理支持。全部向后兼容，零破坏性变更。

v3.0: requests → urllib 标准库，零 pip 依赖即可运行核心爬虫功能。
      optional: scrapling/playwright 用户可选安装用于动态渲染。

兼容接口（与旧 requests 版完全一致）：
  http_get(), http_post(), fetch_text(), http_get_json(),
  download_file(), get_session(), rate_limit(), clear_cache()

v2.2 遗留 API（保留）：
  DEFAULT_UA, DEFAULT_HEADERS, DEFAULT_TIMEOUT, DOWNLOAD_TIMEOUT,
  sanitize_filename(), LRUCache
"""
from __future__ import annotations

import os
import re
import time
import json
import random
import logging
import hashlib
import threading
import urllib.request
import urllib.error
import urllib.parse
from enum import Enum, auto
from collections import OrderedDict
import socket
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple
from http.cookiejar import CookieJar

# ─── 可选依赖 ──────────────────────────────────────────────────────────────────
try:
    import chardet as _chardet
    HAS_CHARDET = True
except ImportError:
    _chardet = None  # type: ignore
    HAS_CHARDET = False

# v7.2: 软拦截检测（anti_block_utils 纯函数，导入失败时静默降级关闭）
try:
    from anti_block_utils import detect_block as _detect_block
except ImportError:
    try:
        from scripts.anti_block_utils import detect_block as _detect_block
    except ImportError:
        _detect_block = None  # type: ignore

# ─── 日志 ────────────────────────────────────────────────────────────────────
log = logging.getLogger("http_utils")

# ─── 常量 ────────────────────────────────────────────────────────────────────

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

# ─── UA 轮换池（v4.0 — 10+ 种真实浏览器 UA） ─────────────────────────────────────

UA_POOL_DESKTOP: List[str] = [
    # Chrome 133 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    # Chrome 132 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    # Chrome 131 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 130 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome 129 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    # Edge 133 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    # Edge 131 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    # Edge 130 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    # Firefox 134 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    # Firefox 133 Win
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Firefox 132 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Chrome 126 Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

UA_POOL_MOBILE: List[str] = [
    # iPhone Safari 17
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    # iPhone Safari 18
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    # Android Chrome (Samsung)
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.107 Mobile Safari/537.36",
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

# 合并池
UA_POOL_ALL: List[str] = UA_POOL_DESKTOP + UA_POOL_MOBILE

# ─── 请求指纹池（v4.0 — 每次请求随机组合） ──────────────────────────────────────────

ACCEPT_LANGUAGE_POOL: List[str] = [
    "zh-CN,zh;q=0.9",
    "zh-CN,zh;q=0.9,en;q=0.8",
    "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
    "zh-CN,zh;q=0.8,en;q=0.6",
]

ACCEPT_ENCODING_POOL: List[str] = [
    "gzip, deflate",
    "gzip, deflate, br",
]

SEC_CH_UA_POOL: List[str] = [
    '"Google Chrome";v="133", "Chromium";v="133", "Not=A?Brand";v="24"',
    '"Google Chrome";v="132", "Chromium";v="132", "Not=A?Brand";v="24"',
    '"Google Chrome";v="131", "Chromium";v="131", "Not=A?Brand";v="24"',
    '"Google Chrome";v="130", "Chromium";v="130", "Not=A?Brand";v="24"',
    '"Chromium";v="133", "Not A(Brand";v="24", "Microsoft Edge";v="133"',
    '"Chromium";v="131", "Not A(Brand";v="24", "Microsoft Edge";v="131"',
    '"Chromium";v="130", "Not A(Brand";v="24", "Microsoft Edge";v="130"',
]

SEC_CH_UA_PLATFORM_POOL: List[str] = [
    '"Windows"',
    '"macOS"',
]

DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": DEFAULT_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

DEFAULT_TIMEOUT = 30  # HTTP 请求超时（DNS 解析另由 socket.setdefaulttimeout 控制）
DOWNLOAD_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5
RATE_LIMIT_DELAY = 2.0
JITTER_FACTOR = 0.3

# ─── 重试策略枚举（v4.0） ──────────────────────────────────────────────────────

class RetryStrategy(Enum):
    """多策略重试 — 每次重试采用不同反爬策略"""
    UA_ROTATE = auto()        # 换一个 UA
    MOBILE_UA = auto()        # 模拟移动端
    FINGERPRINT = auto()      # 换 Accept-Language / Sec-Ch-Ua 指纹
    ADD_AJAX_HEADER = auto()  # 添加 X-Requested-With: XMLHttpRequest
    REFERRER_CHANGE = auto()  # 更换 Referer
    NO_CACHE = auto()         # 绕过缓存直接请求
    DELAY_INCREASE = auto()   # 增加延迟再试

# 默认重试策略序列
DEFAULT_RETRY_STRATEGIES: List[RetryStrategy] = [
    RetryStrategy.UA_ROTATE,
    RetryStrategy.FINGERPRINT,
    RetryStrategy.ADD_AJAX_HEADER,
    RetryStrategy.MOBILE_UA,
    RetryStrategy.DELAY_INCREASE,
]

# ─── UA 轮换与指纹随机化工具（v4.0） ────────────────────────────────────────────

def random_ua(mobile: bool = False) -> str:
    """从 UA 池随机选择一个"""
    pool = UA_POOL_MOBILE if mobile else UA_POOL_DESKTOP
    return random.choice(pool)


def random_fingerprint_headers(base_ua: Optional[str] = None) -> Dict[str, str]:
    """生成随机指纹 headers 集合（Accept-Language, Accept-Encoding, Sec-Ch-Ua 等）"""
    headers: Dict[str, str] = {
        "Accept-Language": random.choice(ACCEPT_LANGUAGE_POOL),
        "Accept-Encoding": random.choice(ACCEPT_ENCODING_POOL),
    }
    if base_ua:
        headers["User-Agent"] = base_ua
    # 对 Chrome/Edge UA 添加 Sec-Ch-Ua 系列 header
    ua = base_ua or ""
    if "Chrome" in ua or "Edg" in ua:
        headers["Sec-Ch-Ua"] = random.choice(SEC_CH_UA_POOL)
        headers["Sec-Ch-Ua-Platform"] = random.choice(SEC_CH_UA_PLATFORM_POOL)
        headers["Sec-Ch-Ua-Mobile"] = "?0"
    return headers


# 按域名记住最近成功的 UA（部分网站对特定 UA 更友好）
_successful_ua_by_domain: Dict[str, str] = {}
_ua_domain_lock = threading.Lock()


def record_successful_ua(domain: str, ua: str):
    """记录某域名下最近成功的 UA"""
    with _ua_domain_lock:
        _successful_ua_by_domain[domain] = ua
        # 限制字典大小
        if len(_successful_ua_by_domain) > 200:
            # 清理一半
            keys = list(_successful_ua_by_domain.keys())
            for k in keys[:100]:
                del _successful_ua_by_domain[k]


def get_best_ua_for_domain(domain: str, mobile: bool = False) -> str:
    """获取某域名下最佳 UA（有历史成功记录则用历史的，否则随机）"""
    with _ua_domain_lock:
        if domain in _successful_ua_by_domain:
            cached = _successful_ua_by_domain[domain]
            # 如果请求的是 mobile 但缓存的是 desktop，重新随机
            if mobile and "Mobile" not in cached and "Android" not in cached:
                return random_ua(mobile=True)
            return cached
    return random_ua(mobile=mobile)


# ─── StdlibResponse ───────────────────────────────────────────────────────────

class HTTPError(urllib.error.HTTPError):
    """requests 风格的 HTTPError（兼容 raise_for_status 用法）

    v7.2 修复：此前定义的 url property 与父类 addinfourl 的
    self.url 赋值冲突，导致 raise_for_status 抛 AttributeError。
    """
    def __init__(self, code: int, msg: str, hdrs: Dict, fp: Any, url: str = ""):
        super().__init__(url or "?", code, msg, hdrs, fp)
        self.code = code  # urllib.error.HTTPError uses .code internally

    @property
    def status_code(self) -> int:
        return self.code


def _auto_decompress(data: bytes, headers: Dict[str, str]) -> bytes:
    """v7.0.0: 自动解压 gzip/deflate 响应体（urllib 不解压，指纹头发了
    Accept-Encoding: gzip 时服务器会返回压缩流，导致 json()/text() 乱码）。"""
    if not data:
        return data
    ce = (headers.get("Content-Encoding")
          or headers.get("content-encoding") or "").lower()
    try:
        if "gzip" in ce or data[:2] == b"\x1f\x8b":
            import gzip
            return gzip.decompress(data)
        if "deflate" in ce:
            import zlib
            try:
                return zlib.decompress(data)
            except zlib.error:
                return zlib.decompress(data, -zlib.MAX_WBITS)
        if "br" in ce:
            try:
                import brotli
                return brotli.decompress(data)
            except ImportError:
                pass
    except Exception:
        return data
    return data


class StdlibResponse:
    """
    urllib.response 包装器，对标 requests.Response 接口。
    让调用方无感切换到 urllib。
    """
    __slots__ = ('_url', '_code', '_headers', '_data', '_encoding')

    def __init__(self, url: str, code: int, headers: Dict[str, str], data: bytes, encoding: str = "utf-8"):
        self._url = url
        self._code = code
        self._headers = headers
        self._data = _auto_decompress(data, headers)
        self._encoding = encoding

    @property
    def url(self) -> str:
        return self._url

    @property
    def code(self) -> int:
        return self._code

    @property
    def status_code(self) -> int:
        return self._code

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    @property
    def content(self) -> bytes:
        return self._data

    @property
    def text(self) -> str:
        return self._data.decode(self._encoding, errors="replace")

    def json(self) -> Any:
        return json.loads(self._data)

    def raise_for_status(self):
        if self._code >= 400:
            raise HTTPError(
                self._code,
                f"HTTP {self._code} error",
                self._headers,
                None,
                self._url
            )

    def __repr__(self):
        return f"<StdlibResponse [{self._code}]>"


# ─── StdlibSession ───────────────────────────────────────────────────────────

class StdlibSession:
    """
    对标 requests.Session 的标准库实现。
    内部使用 urllib.request.OpenerDirector + CookieJar。

    v4.0: 支持代理、UA 轮换、指纹随机化。
    """
    def __init__(self, headers: Optional[Dict[str, str]] = None,
                 proxy: Optional[str] = None,
                 rotate_ua: bool = False,
                 randomize_fingerprint: bool = False,
                 mobile: bool = False):
        self.headers = {**DEFAULT_HEADERS, **(headers or {})}
        self.cookies = CookieJar()
        self.proxy = proxy
        self.rotate_ua = rotate_ua
        self.randomize_fingerprint = randomize_fingerprint
        self.mobile = mobile

        # 如果启用 UA 轮换，随机选取初始 UA
        if rotate_ua and "User-Agent" not in (headers or {}):
            self.headers["User-Agent"] = random_ua(mobile=mobile)

        # 构建 opener（含代理）
        handlers: List[Any] = [urllib.request.HTTPCookieProcessor(self.cookies)]
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({
                "http": proxy,
                "https": proxy,
            })
            handlers.insert(0, proxy_handler)
        self._opener = urllib.request.build_opener(*handlers)

    def _apply_fingerprint(self, headers: Dict[str, str]) -> Dict[str, str]:
        """如果启用指纹随机化，为每次请求注入变化的指纹 headers"""
        if not self.randomize_fingerprint:
            return headers
        fp = random_fingerprint_headers()
        # 不覆盖调用方显式设置的 headers
        for k, v in fp.items():
            if k not in headers:
                headers[k] = v
        return headers

    def _rotate_ua_if_needed(self, headers: Dict[str, str]) -> Dict[str, str]:
        """如果启用 UA 轮换且调用方没显式设 UA，则随机换一个"""
        if not self.rotate_ua:
            return headers
        if "User-Agent" in headers:
            return headers
        base_ua = self.headers.get("User-Agent", "")
        # 从 URL host 获取域名以使用最佳 UA
        # （在 _build_request 中无法预知 URL，这里用默认随机）
        headers["User-Agent"] = random_ua(mobile=self.mobile)
        return headers

    def _build_request(self, url: str, headers: Dict,
                       data: Optional[bytes],
                       method: Optional[str] = None) -> urllib.request.Request:
        merged = {**self.headers, **headers}

        # v4.0: 指纹随机化
        merged = self._apply_fingerprint(merged)

        # v4.0: UA 轮换 + 域名最佳 UA
        if self.rotate_ua and "User-Agent" not in headers:
            domain = _extract_domain(url)
            merged["User-Agent"] = get_best_ua_for_domain(domain, mobile=self.mobile)

        # v7.2: 显式 method 优先（修复空 body POST 被误判为 GET）
        if method is None:
            method = "GET" if data is None else "POST"
        return urllib.request.Request(url, data=data, headers=merged, method=method)

    def _do_open(self, request: urllib.request.Request,
                 timeout: int,
                 response_cls: type = StdlibResponse) -> StdlibResponse:
        """执行请求并返回 StdlibResponse"""
        try:
            raw = self._opener.open(request, timeout=timeout)
            code = raw.getcode()
            # urllib 返回的是 email.message.Message 或类似对象
            hdrs = dict(raw.headers) if hasattr(raw.headers, '__iter__') else {}
            data = raw.read()
            url = request.full_url
            raw.close()

            # 编码检测
            encoding = self._detect_encoding(code, hdrs, data)
            return StdlibResponse(url, code, hdrs, data, encoding)

        except urllib.error.HTTPError as e:
            # 读取错误响应体（某些服务器在 4xx/5xx 时仍返回内容）
            code = e.code
            hdrs = dict(e.headers) if hasattr(e.headers, '__iter__') else {}
            data = b""
            try:
                if e.fp:
                    data = e.fp.read()
                    e.fp.close()
            except Exception:
                pass
            url = e.url or request.full_url
            encoding = self._detect_encoding(code, hdrs, data)
            return StdlibResponse(url, code, hdrs, data, encoding)

    def _detect_encoding(self, code: int, hdrs: Dict, data: bytes) -> str:
        """推断响应编码（v4.0 增强：Content-Type → HTML meta charset → chardet → 中文编码试探）"""
        ct = hdrs.get("Content-Type", "")
        # 1. 从 Content-Type header 的 charset= 取编码
        m = re.search(r'charset=([^\s;]+)', ct, re.IGNORECASE)
        if m:
            enc = m.group(1).strip('"\'')
            if enc.lower() in ("gbk", "gb2312", "gb18030", "utf-8", "utf8", "latin-1", "big5"):
                return enc

        # 2. 从 HTML <meta charset> 或 <meta http-equiv> 中检测
        if data and len(data) > 10:
            # 只检查前 4KB（meta 标签通常在头部）
            head_bytes = data[:4096]
            for enc_try in ("utf-8", "gbk", "gb18030", "latin-1"):
                try:
                    head_text = head_bytes.decode(enc_try, errors="replace")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                head_text = head_bytes.decode("latin-1", errors="replace")

            meta_enc = _extract_meta_charset(head_text)
            if meta_enc:
                return meta_enc

        # 3. 可选：chardet 高精度检测
        if HAS_CHARDET and data and len(data) > 20:
            try:
                detected = _chardet.detect(data[:16384])  # type: ignore[union-attr]
                if detected and detected.get("encoding") and detected.get("confidence", 0) > 0.7:
                    enc = detected["encoding"].lower()
                    # 统一 GB 系列编码
                    if enc in ("gb2312", "gbk", "gb18030"):
                        return "gb18030"
                    if enc == "ascii":
                        return "utf-8"
                    return enc
            except Exception:
                pass

        # 4. 中文编码优先试探（中国金融网站主流编码）
        for enc in ("utf-8", "gb18030", "gbk", "gb2312", "latin-1"):
            try:
                data.decode(enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return "utf-8"

    def get(self, url: str,
            headers: Optional[Dict[str, str]] = None,
            timeout: int = DEFAULT_TIMEOUT,
            **kwargs) -> StdlibResponse:
        """HTTP GET"""
        req = self._build_request(url, headers or {}, None)
        return self._do_open(req, timeout)

    def post(self, url: str,
             data: Optional[Any] = None,
             json_body: Optional[Dict] = None,
             headers: Optional[Dict[str, str]] = None,
             timeout: int = DEFAULT_TIMEOUT,
             **kwargs) -> StdlibResponse:
        """HTTP POST — data 或 json_body 二选一"""
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            h = {"Content-Type": "application/json; charset=utf-8"}
            if headers:
                h = {**headers, **h}
            headers = h
        elif data is not None:
            if isinstance(data, str):
                body_bytes = data.encode("utf-8")
            elif isinstance(data, dict):
                body_bytes = urllib.parse.urlencode(data).encode("utf-8")
            else:
                body_bytes = data
        else:
            body_bytes = None
        req = self._build_request(url, headers or {}, body_bytes, method="POST")
        return self._do_open(req, timeout)

    def request(self, method: str, url: str,
                headers: Optional[Dict[str, str]] = None,
                data: Optional[Any] = None,
                timeout: int = DEFAULT_TIMEOUT,
                **kwargs) -> StdlibResponse:
        """通用 request"""
        if method.upper() == "POST":
            return self.post(url, data=data, headers=headers, timeout=timeout, **kwargs)
        return self.get(url, headers=headers, timeout=timeout, **kwargs)


def _extract_meta_charset(html_head: str) -> Optional[str]:
    """从 HTML 头部提取 charset 声明"""
    # <meta charset="gbk">
    m = re.search(r'<meta[^>]+charset=["\']?\s*([^\s"\'/>]+)', html_head, re.IGNORECASE)
    if m:
        enc = m.group(1).strip().lower()
        if enc in ("gbk", "gb2312", "gb18030", "utf-8", "utf8", "big5"):
            if enc in ("gb2312", "gbk"):
                return "gb18030"
            return enc
    # <meta http-equiv="Content-Type" content="text/html; charset=gbk">
    m = re.search(r'http-equiv=["\']?Content-Type["\']?[^>]+charset=["\']?\s*([^\s"\'/>]+)',
                   html_head, re.IGNORECASE)
    if m:
        enc = m.group(1).strip().lower()
        if enc in ("gbk", "gb2312", "gb18030", "utf-8", "utf8", "big5"):
            if enc in ("gb2312", "gbk"):
                return "gb18030"
            return enc
    return None


# ─── 代理支持（v4.0） ──────────────────────────────────────────────────────────

_proxy_url: Optional[str] = None
_proxy_lock = threading.Lock()


def set_proxy(proxy_url: Optional[str]):
    """设置全局代理 URL（http://user:pass@host:port 或 socks5://host:port）

    Args:
        proxy_url: 代理 URL，传 None 清除代理设置
    """
    global _proxy_url
    with _proxy_lock:
        _proxy_url = proxy_url
    # 清除共享 session 以使用新代理重建
    clear_session_cache()
    if proxy_url:
        log.info(f"代理已设置: {proxy_url[:50]}...")
    else:
        log.info("代理已清除")


def get_proxy() -> Optional[str]:
    """获取当前全局代理 URL"""
    with _proxy_lock:
        return _proxy_url


def check_proxy(proxy_url: Optional[str] = None, test_url: str = "https://www.baidu.com",
                timeout: int = 10) -> Tuple[bool, str]:
    """检测代理是否可用

    Returns:
        (是否可用, 响应信息或错误描述)
    """
    proxy = proxy_url or _proxy_url
    if not proxy:
        return False, "未设置代理"

    try:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(test_url, headers={"User-Agent": DEFAULT_UA})
        resp = opener.open(req, timeout=timeout)
        code = resp.getcode()
        resp.close()
        if 200 <= code < 400:
            return True, f"代理可用 (HTTP {code})"
        return False, f"代理返回 HTTP {code}"
    except Exception as e:
        return False, f"代理检测失败: {str(e)[:100]}"


# ─── SSL 验证管理（v5.0） ─────────────────────────────────────────────────────

_ssl_verify_enabled: bool = True
_ssl_lock = threading.Lock()


def disable_ssl_verify():
    """⚠️ 仅调试用 — 关闭 SSL 证书验证（生产环境请安装代理 CA 证书）

    调用此函数会记录 WARNING 日志（含调用栈），便于安全审计。
    推荐替代方案：
    1. 安装代理 CA 证书到系统信任库
    2. 使用 requests 的 verify 参数指定 PEM 文件路径
    """
    global _ssl_verify_enabled
    import traceback
    stack = "".join(traceback.format_stack()[-4:-1])
    log.warning(
        "SSL 证书验证已关闭（仅调试用，生产环境请安装代理 CA 证书）\n"
        f"调用栈:\n{stack}"
    )
    with _ssl_lock:
        _ssl_verify_enabled = False


def enable_ssl_verify():
    """重新启用 SSL 证书验证（默认状态）"""
    global _ssl_verify_enabled
    with _ssl_lock:
        _ssl_verify_enabled = True
    log.info("SSL 证书验证已启用")


def get_ssl_status() -> Dict[str, Any]:
    """查询当前 SSL 验证状态

    Returns:
        {"enabled": bool, "status": str}
    """
    with _ssl_lock:
        enabled = _ssl_verify_enabled
    return {
        "enabled": enabled,
        "status": "正常（证书验证开启）" if enabled else "⚠️ 已关闭（仅调试模式）",
    }


def is_ssl_verify_enabled() -> bool:
    """返回当前 SSL 验证是否启用"""
    with _ssl_lock:
        return _ssl_verify_enabled


def clear_session_cache():
    """清除共享 session 缓存（代理变更后需要重建 session）"""
    global _shared_session, _shared_mobile_session
    _shared_session = None
    _shared_mobile_session = None


# ─── 全局会话（v4.0 增强） ────────────────────────────────────────────────────

_shared_session: Optional[StdlibSession] = None
_shared_mobile_session: Optional[StdlibSession] = None


def get_session(headers: Optional[Dict[str, str]] = None,
                reuse: bool = True,
                mobile: bool = False,
                rotate_ua: bool = True,
                randomize_fingerprint: bool = True) -> StdlibSession:
    """获取或创建 HTTP 会话

    Args:
        headers: 额外的请求 headers
        reuse: 是否复用共享 session
        mobile: 是否使用移动端 UA
        rotate_ua: 是否启用 UA 轮换（每次请求随机选 UA）
        randomize_fingerprint: 是否启用请求指纹随机化

    v4.0: 新增 rotate_ua 和 randomize_fingerprint 参数，
          默认开启以增强反爬能力。
    """
    global _shared_session, _shared_mobile_session

    proxy = get_proxy()

    if mobile:
        if reuse and _shared_mobile_session is not None and headers is None and not proxy:
            return _shared_mobile_session
        session = StdlibSession(
            {**DEFAULT_HEADERS, "User-Agent": MOBILE_UA, **(headers or {})},
            proxy=proxy, rotate_ua=rotate_ua,
            randomize_fingerprint=randomize_fingerprint, mobile=True
        )
        if reuse and headers is None and not proxy:
            _shared_mobile_session = session
        return session

    if reuse and _shared_session is not None and headers is None and not proxy:
        return _shared_session

    session = StdlibSession(
        {**DEFAULT_HEADERS, **(headers or {})},
        proxy=proxy, rotate_ua=rotate_ua,
        randomize_fingerprint=randomize_fingerprint, mobile=False
    )
    if reuse and headers is None and not proxy:
        _shared_session = session
    return session


# ─── 自适应限流（v4.0） ──────────────────────────────────────────────────────────

class AdaptiveRateLimiter:
    """根据服务器响应动态调整域名限流延迟

    - HTTP 429 / 503 → 加大该域名延迟（指数增长，最大 120 秒）
    - 连续成功 → 逐步恢复至基础延迟
    - 触发限流后短暂暂停该域名所有请求
    """

    def __init__(self, base_delays: Optional[Dict[str, float]] = None):
        # 延迟引用 _DOMAIN_RATE_LIMITS（在模块底部定义），避免循环依赖
        defaults = base_delays if base_delays else _DOMAIN_RATE_LIMITS
        self._base_delays: Dict[str, float] = dict(defaults)
        self._current_delays: Dict[str, float] = {}
        self._consecutive_ok: Dict[str, int] = {}
        self._consecutive_fail: Dict[str, int] = {}
        self._blocked_until: Dict[str, float] = {}
        self._lock = threading.Lock()
        # 配置
        self.max_delay = 120.0          # 最大延迟（秒）
        self.fail_threshold = 3          # 连续失败几次触发熔断
        self.ok_recovery_threshold = 5   # 连续成功几次开始恢复
        self.recovery_factor = 0.8       # 恢复因子（每次乘 0.8）

    def _get_base_delay(self, domain: str) -> float:
        """获取域名基础延迟"""
        for d, v in self._base_delays.items():
            if d in domain and d != "default":
                return v
        return self._base_delays.get("default", RATE_LIMIT_DELAY)

    def get_delay(self, domain: str) -> float:
        """获取当前域名的限流延迟"""
        with self._lock:
            # 检查是否在熔断期
            blocked = self._blocked_until.get(domain, 0)
            if blocked > time.time():
                remaining = blocked - time.time()
                return max(remaining, 5.0)
            return self._current_delays.get(domain, self._get_base_delay(domain))

    def report_success(self, domain: str):
        """报告一次成功的请求"""
        with self._lock:
            self._consecutive_fail[domain] = 0
            ok_count = self._consecutive_ok.get(domain, 0) + 1
            self._consecutive_ok[domain] = ok_count
            # 连续成功 N 次后逐步恢复延迟
            if ok_count >= self.ok_recovery_threshold:
                current = self._current_delays.get(domain, self._get_base_delay(domain))
                base = self._get_base_delay(domain)
                if current > base:
                    new_delay = max(base, current * self.recovery_factor)
                    self._current_delays[domain] = new_delay
                    log.debug(f"域名 {domain} 延迟恢复: {current:.1f}s → {new_delay:.1f}s")

    def report_failure(self, domain: str, status_code: int = 0) -> bool:
        """报告一次失败的请求

        Returns:
            是否触发熔断（该域名应暂时停止请求）
        """
        with self._lock:
            self._consecutive_ok[domain] = 0
            fail_count = self._consecutive_fail.get(domain, 0) + 1
            self._consecutive_fail[domain] = fail_count

            # HTTP 429 (Rate Limited) 或 503 (Service Unavailable) → 加大延迟
            if status_code in (429, 503):
                current = self._current_delays.get(domain, self._get_base_delay(domain))
                new_delay = min(current * 2.5, self.max_delay)
                self._current_delays[domain] = new_delay
                log.warning(f"域名 {domain} HTTP {status_code}，延迟增至 {new_delay:.1f}s")

            # 连续失败 → 熔断
            if fail_count >= self.fail_threshold:
                block_seconds = min(10 * (2 ** (fail_count - self.fail_threshold)), 300)
                self._blocked_until[domain] = time.time() + block_seconds
                log.warning(f"域名 {domain} 连续失败 {fail_count} 次，熔断 {block_seconds:.0f}s")
                return True
            return False

    def is_blocked(self, domain: str) -> bool:
        """检查域名是否在熔断期"""
        with self._lock:
            blocked = self._blocked_until.get(domain, 0)
            if blocked > time.time():
                return True
            # 熔断过期，半开恢复
            if blocked > 0 and blocked <= time.time():
                self._blocked_until[domain] = 0
            return False

    def reset_domain(self, domain: str):
        """重置某个域名的限流状态"""
        with self._lock:
            self._current_delays.pop(domain, None)
            self._consecutive_ok.pop(domain, None)
            self._consecutive_fail.pop(domain, None)
            self._blocked_until.pop(domain, None)

    def get_stats(self) -> Dict[str, Any]:
        """获取限流统计信息"""
        with self._lock:
            return {
                "blocked_domains": [
                    d for d, t in self._blocked_until.items() if t > time.time()
                ],
                "delays": dict(self._current_delays),
                "consecutive_fails": dict(self._consecutive_fail),
            }


# ── 全局自适应限流器（延迟创建，在 _DOMAIN_RATE_LIMITS 之后） ──
_adaptive_limiter: Optional[AdaptiveRateLimiter] = None


def _get_adaptive_limiter() -> AdaptiveRateLimiter:
    """延迟获取全局自适应限流器（确保 _DOMAIN_RATE_LIMITS 已定义）"""
    global _adaptive_limiter
    if _adaptive_limiter is None:
        _adaptive_limiter = AdaptiveRateLimiter()
    return _adaptive_limiter


def get_adaptive_delay(domain: str) -> float:
    """便捷函数：获取域名自适应延迟"""
    return _get_adaptive_limiter().get_delay(domain)


def report_request_result(url: str, success: bool, status_code: int = 0):
    """便捷函数：报告单次请求结果给自适应限流器"""
    domain = _extract_domain(url)
    if success:
        _get_adaptive_limiter().report_success(domain)
    else:
        _get_adaptive_limiter().report_failure(domain, status_code)


# ─── LRU 缓存 ────────────────────────────────────────────────────────────────

class LRUCache:
    def __init__(self, max_size: int = 128, ttl: float = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()

    def _key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def get(self, url: str) -> Optional[StdlibResponse]:
        key = self._key(url)
        with self._lock:
            if key in self._cache:
                entry_time, resp = self._cache[key]
                if time.time() - entry_time < self.ttl:
                    self._cache.move_to_end(key)
                    return resp
                del self._cache[key]
        return None

    def set(self, url: str, resp: StdlibResponse):
        key = self._key(url)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                self._cache[key] = (time.time(), resp)

    def clear(self):
        with self._lock:
            self._cache.clear()

    def __len__(self):
        return len(self._cache)


_response_cache = LRUCache(max_size=256, ttl=1800)


# ─── 按域名限流 ──────────────────────────────────────────────────────────────

_DOMAIN_RATE_LIMITS: Dict[str, float] = {
    "eastmoney.com": 1.0,
    "10jqka.com.cn": 2.0,
    "sina.com.cn": 1.5,
    "163.com": 1.5,
    "xueqiu.com": 3.0,
    "cls.cn": 2.0,
    "jisilu.cn": 3.0,
    "wallstreetcn.com": 2.0,
    "sse.com.cn": 3.0,
    "szse.cn": 3.0,
    # v6.0.0 新增媒体源
    "hexun.com": 2.0,
    "jrj.com.cn": 2.0,
    "ifeng.com": 1.5,
    "fx678.com": 2.0,
    "cngold.org": 2.0,
    "investing.com": 2.0,
    "zhitongcaijing.com": 2.0,
    "jiemian.com": 1.5,
    "lanjinger.com": 2.0,
    "futunn.com": 2.0,
    "aastocks.com": 2.0,
    "smm.cn": 2.0,
    "default": RATE_LIMIT_DELAY,
}

_domain_last_request: Dict[str, float] = {}
_domain_lock = threading.Lock()


def _extract_domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return "unknown"


def rate_limit(delay: float = RATE_LIMIT_DELAY, url: str = ""):
    """按域名限流（v4.0 增强：合并自适应限流器延迟；v7.2: sleep 移出锁外）"""
    global _domain_last_request
    wait_time = 0.0
    block_wait = 0.0
    blocked_domain = ""
    with _domain_lock:
        now = time.time()
        if url:
            domain = _extract_domain(url)
            # v4.0: 优先使用自适应限流延迟
            limiter = _get_adaptive_limiter()
            adaptive_delay = limiter.get_delay(domain)
            # 查找匹配域名配置（取自适应与静态配置的最大值）
            domain_delay = adaptive_delay
            for d, v in _DOMAIN_RATE_LIMITS.items():
                if d in domain and d != "default":
                    domain_delay = max(adaptive_delay, v)
                    break
            else:
                domain_delay = max(adaptive_delay, _DOMAIN_RATE_LIMITS.get("default", RATE_LIMIT_DELAY))

            # 检查是否熔断（v7.2: 只计算等待时长，sleep 在锁外执行，
            # 避免一个域名熔断阻塞所有域名的限流判断）
            if limiter.is_blocked(domain):
                block_wait = max(domain_delay, 5.0)
                blocked_domain = domain
            else:
                last_time = _domain_last_request.get(domain, 0)
                elapsed = now - last_time
                if elapsed < domain_delay:
                    wait_time = domain_delay - elapsed
                _domain_last_request[domain] = now + wait_time
                if len(_domain_last_request) > 100:
                    expired = [d for d, t in _domain_last_request.items() if now - t > 3600]
                    for d in expired:
                        del _domain_last_request[d]
    if block_wait > 0:
        log.warning(f"域名 {blocked_domain} 已熔断，等待 {block_wait:.1f}s")
        time.sleep(block_wait)
        # 不更新 last_request，让下次请求也等待
        return
    if wait_time > 0:
        time.sleep(wait_time)


class RatelimitedSession:
    """v5.0.0: requests.Session 的自适应限流代理。

    包装 requests.Session，使 self.session.get(...) 自动按域名限流 + 熔断，
    供 company_report / research_report / news 等以 requests 直连的 scraper 使用，
    使其与 http_utils 的限流策略保持一致（此前 requests 直连完全绕过 rate_limit）。
    属性访问透明代理到原 Session（如 headers.update / close）。
    """

    def __init__(self, session):
        self._session = session

    def get(self, url, **kwargs):
        rate_limit(url=url)
        return self._session.get(url, **kwargs)

    def post(self, url, **kwargs):
        rate_limit(url=url)
        return self._session.post(url, **kwargs)

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        return self._session.close()


# ─── 重试抖动 ────────────────────────────────────────────────────────────────

def _jitter(base: float, factor: float = JITTER_FACTOR) -> float:
    return base * (1 + random.uniform(-factor, factor))


def _apply_retry_strategy(strategy: RetryStrategy, headers: Dict[str, str],
                          session: Optional[StdlibSession], mobile: bool,
                          url: str) -> Tuple[Dict[str, str], bool]:
    """对单次重试应用指定策略，返回 (新headers, 是否切换为移动端session)"""
    h = {**headers}
    new_mobile = mobile

    if strategy == RetryStrategy.UA_ROTATE:
        h["User-Agent"] = random_ua(mobile=mobile)
    elif strategy == RetryStrategy.MOBILE_UA:
        h["User-Agent"] = random_ua(mobile=True)
        new_mobile = True
    elif strategy == RetryStrategy.FINGERPRINT:
        fp = random_fingerprint_headers(h.get("User-Agent"))
        for k, v in fp.items():
            if k not in h:
                h[k] = v
    elif strategy == RetryStrategy.ADD_AJAX_HEADER:
        h["X-Requested-With"] = "XMLHttpRequest"
    elif strategy == RetryStrategy.REFERRER_CHANGE:
        # 尝试设为同域根路径
        try:
            parsed = urllib.parse.urlparse(url)
            h["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
        except Exception:
            h["Referer"] = "https://www.google.com/"
    elif strategy == RetryStrategy.DELAY_INCREASE:
        # 增加静态延迟，在调用方处理
        pass
    elif strategy == RetryStrategy.NO_CACHE:
        # 在调用方处理
        pass

    return h, new_mobile


# ─── v7.2 重试/软拦截辅助 ────────────────────────────────────────────

def _header_ci(headers: Dict[str, str], name: str) -> str:
    """大小写不敏感取响应头"""
    if not headers:
        return ""
    lname = name.lower()
    for k, v in headers.items():
        if k.lower() == lname:
            return v or ""
    return ""


def _retry_after_seconds(resp: StdlibResponse, cap: float = 60.0) -> float:
    """解析 Retry-After 响应头（仅支持秒数格式），限幅 cap"""
    ra = _header_ci(resp.headers, "Retry-After").strip()
    if not ra:
        return 0.0
    try:
        return max(0.0, min(float(int(ra)), cap))
    except (ValueError, TypeError):
        return 0.0


def _is_soft_blocked(resp: StdlibResponse):
    """v7.2: 检测伪装成 200 的软拦截页面。

    保守策略：仅对短小（<8KB）的 HTML 响应做文本特征检测，
    避免误伤 JSON API 与正常长文章页。返回 BlockSignal 或 None。
    """
    if _detect_block is None or resp.code >= 300 or len(resp.content) > 8192:
        return None
    ct = _header_ci(resp.headers, "Content-Type").lower()
    body_start = resp.content[:64].lstrip().lower()
    if "html" not in ct and not body_start.startswith(b"<"):
        return None
    try:
        return _detect_block(resp.code, resp.headers, resp.text[:2000])
    except Exception:
        return None


def _prepare_next_attempt(strategies: List[RetryStrategy], attempt: int,
                          merged: Dict[str, str], s: Any, current_mobile: bool,
                          url: str, wait: float, use_cache: bool
                          ) -> Tuple[Dict[str, str], Any, bool, float, bool]:
    """对第 attempt 次失败应用重试策略。

    返回 (新headers, session, 是否移动端, 调整后wait, 调整后use_cache)。
    """
    if attempt >= len(strategies):
        return merged, s, current_mobile, wait, use_cache
    strat = strategies[attempt]
    if strat == RetryStrategy.DELAY_INCREASE:
        wait *= 2
    elif strat == RetryStrategy.NO_CACHE:
        use_cache = False
    merged, current_mobile = _apply_retry_strategy(strat, merged, s, current_mobile, url)
    if current_mobile and not getattr(s, 'mobile', False):
        s = get_session(mobile=True, rotate_ua=True, randomize_fingerprint=True)
    return merged, s, current_mobile, wait, use_cache


# ─── HTTP GET（v4.0: 多策略重试 + 自适应限流） ──────────────────────────────────

def http_get(url: str,
             headers: Optional[Dict[str, str]] = None,
             timeout: int = DEFAULT_TIMEOUT,
             retries: int = MAX_RETRIES,
             rate_limit_delay: float = 0,
             session: Optional[StdlibSession] = None,
             use_cache: bool = True,
             retry_strategies: Optional[List[RetryStrategy]] = None,
             detect_soft_block: bool = True,
             **kwargs) -> Optional[StdlibResponse]:
    """HTTP GET 请求（v4.0 多策略重试 + 自适应限流；v7.2 软拦截检测）

    Args:
        url: 目标 URL
        headers: 额外 headers
        timeout: 超时秒数
        retries: 最大重试次数
        rate_limit_delay: 最低限流延迟
        session: 复用已有 session
        use_cache: 是否使用 LRU 缓存
        retry_strategies: 重试策略序列，默认使用 DEFAULT_RETRY_STRATEGIES
        detect_soft_block: v7.2 是否检测 200 软拦截页面（短小反爬 HTML）

    Returns:
        StdlibResponse 或 None
    """
    # 缓存检查
    if use_cache:
        cached = _response_cache.get(url)
        if cached is not None:
            log.debug(f"Cache hit: {url[:80]}")
            return cached

    domain = _extract_domain(url)

    # 自适应限流 + 熔断检查
    rate_limit(rate_limit_delay, url)

    s = session or get_session()
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    current_mobile = False

    # 策略列表
    strategies = retry_strategies if retry_strategies is not None else DEFAULT_RETRY_STRATEGIES

    for attempt in range(retries):
        try:
            resp = s.get(url, headers=merged, timeout=timeout, **kwargs)

            if resp.code >= 400:
                # 报告失败给自适应限流器
                report_request_result(url, False, resp.code)

                wait = _jitter(RETRY_BACKOFF ** (attempt + 1))
                # v7.2: 遵从服务端 Retry-After 声明（429/503）
                if resp.code in (429, 503):
                    wait = max(wait, _retry_after_seconds(resp))

                # v7.2: 应用重试策略（统一辅助函数）
                merged, s, current_mobile, wait, use_cache = _prepare_next_attempt(
                    strategies, attempt, merged, s, current_mobile, url, wait, use_cache)

                log.warning(f"HTTP {resp.code} on {url[:80]}, retry {attempt+1}/{retries} "
                           f"in {wait:.1f}s")
                time.sleep(wait)
                continue

            # v7.2: 软拦截检测（伪装成 200 的反爬页面视为失败并重试）
            if detect_soft_block:
                sig = _is_soft_blocked(resp)
                if sig is not None:
                    report_request_result(url, False, 429)
                    wait = _jitter(RETRY_BACKOFF ** (attempt + 1))
                    merged, s, current_mobile, wait, use_cache = _prepare_next_attempt(
                        strategies, attempt, merged, s, current_mobile, url, wait, use_cache)
                    log.warning(f"Soft-block on {url[:80]} ({sig.reason}), "
                               f"retry {attempt+1}/{retries} in {wait:.1f}s")
                    time.sleep(wait)
                    continue

            # 成功：缓存、记录成功 UA、报告成功
            if use_cache:
                _response_cache.set(url, resp)
            report_request_result(url, True)
            # 记录成功 UA 供后续使用
            ua = merged.get("User-Agent", "")
            if ua:
                record_successful_ua(domain, ua)

            return resp

        except Exception as e:
            report_request_result(url, False)
            wait = _jitter(RETRY_BACKOFF ** (attempt + 1))
            merged, s, current_mobile, wait, use_cache = _prepare_next_attempt(
                strategies, attempt, merged, s, current_mobile, url, wait, use_cache)

            log.warning(f"Request failed on {url[:80]}: {e}, retry {attempt+1}/{retries} "
                       f"in {wait:.1f}s")
            time.sleep(wait)

    log.error(f"All {retries} retries exhausted for {url[:80]}")
    return None


def http_get_json(url: str,
                  timeout: int = DEFAULT_TIMEOUT,
                  session: Optional[StdlibSession] = None,
                  retry_strategies: Optional[List[RetryStrategy]] = None,
                  **kwargs) -> Optional[Dict]:
    resp = http_get(url, timeout=timeout, session=session,
                    headers={"Accept": "application/json, */*"},
                    retry_strategies=retry_strategies, **kwargs)
    if resp is not None:
        try:
            return resp.json()
        except Exception as e:
            log.warning(f"JSON parse failed for {url[:80]}: {e}")
    return None


# ─── HTTP POST（v4.0: 多策略重试 + 自适应限流） ──────────────────────────────────

def http_post(url: str,
              data: Optional[Any] = None,
              json_body: Optional[Dict] = None,
              headers: Optional[Dict[str, str]] = None,
              timeout: int = DEFAULT_TIMEOUT,
              retries: int = MAX_RETRIES,
              rate_limit_delay: float = 0,
              session: Optional[StdlibSession] = None,
              use_cache: bool = False,
              retry_strategies: Optional[List[RetryStrategy]] = None,
              **kwargs) -> Optional[StdlibResponse]:
    """HTTP POST 请求（v4.0 多策略重试 + 自适应限流）

    参数与 http_get 一致，额外支持 data/json_body。
    """
    cache_key = url if use_cache else None
    domain = _extract_domain(url)

    rate_limit(rate_limit_delay, url)

    s = session or get_session()
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    current_mobile = False
    strategies = retry_strategies if retry_strategies is not None else DEFAULT_RETRY_STRATEGIES

    for attempt in range(retries):
        try:
            resp = s.post(url, data=data, json_body=json_body,
                          headers=merged, timeout=timeout, **kwargs)

            if resp.code >= 400:
                report_request_result(url, False, resp.code)
                wait = _jitter(RETRY_BACKOFF ** (attempt + 1))
                # v7.2: 遵从服务端 Retry-After 声明（429/503）
                if resp.code in (429, 503):
                    wait = max(wait, _retry_after_seconds(resp))

                merged, s, current_mobile, wait, use_cache = _prepare_next_attempt(
                    strategies, attempt, merged, s, current_mobile, url, wait, use_cache)

                log.warning(f"HTTP {resp.code} on POST {url[:80]}, retry {attempt+1}/{retries} "
                           f"in {wait:.1f}s")
                time.sleep(wait)
                continue

            if use_cache and cache_key:
                _response_cache.set(cache_key, resp)
            report_request_result(url, True)
            ua = merged.get("User-Agent", "")
            if ua:
                record_successful_ua(domain, ua)
            return resp

        except Exception as e:
            report_request_result(url, False)
            wait = _jitter(RETRY_BACKOFF ** (attempt + 1))
            merged, s, current_mobile, wait, use_cache = _prepare_next_attempt(
                strategies, attempt, merged, s, current_mobile, url, wait, use_cache)

            log.warning(f"POST failed on {url[:80]}: {e}, retry {attempt+1}/{retries} "
                       f"in {wait:.1f}s")
            time.sleep(wait)

    log.error(f"All {retries} retries exhausted for POST {url[:80]}")
    return None


# ─── 便捷函数 ───────────────────────────────────────────────────────────────

def fetch_text(url: str,
               headers: Optional[Dict[str, str]] = None,
               timeout: int = DEFAULT_TIMEOUT,
               retries: int = MAX_RETRIES,
               use_cache: bool = True,
               **kwargs) -> Optional[str]:
    resp = http_get(url, headers=headers, timeout=timeout,
                    retries=retries, use_cache=use_cache, **kwargs)
    return resp.text if resp is not None else None


def clear_cache() -> int:
    _response_cache.clear()
    return len(_response_cache)


# ─── 文件下载 ────────────────────────────────────────────────────────────────

def download_file(url: str,
                  save_dir: str = ".",
                  filename: Optional[str] = None,
                  headers: Optional[Dict[str, str]] = None,
                  timeout: int = DOWNLOAD_TIMEOUT,
                  session: Optional[StdlibSession] = None) -> Optional[str]:
    s = session or get_session()
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    try:
        resp = s.get(url, headers=merged, timeout=timeout)
        # v7.2: 错误响应不落盘（此前 404 页面会被当文件保存）
        if resp.code >= 400:
            log.error(f"Download got HTTP {resp.code} from {url[:80]}, skip saving")
            return None
        # 解析文件名
        if not filename:
            filename = _extract_filename(resp, url)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        log.info(f"Downloaded: {save_path}")
        return save_path
    except Exception as e:
        log.error(f"Download failed from {url[:80]}: {e}")
        return None


def _extract_filename(resp: StdlibResponse, url: str) -> str:
    cd = resp.headers.get("Content-Disposition", "")
    if cd:
        m = re.search(r"filename\*=UTF-8''(.+?)(?:;|$)", cd, re.IGNORECASE)
        if m:
            return urllib.parse.unquote(m.group(1).strip())
        m = re.search(r'filename=["\']?([^"\';]+)', cd)
        if m:
            return m.group(1).strip()
    path = urllib.parse.urlparse(url).path
    name = os.path.basename(path)
    if name and '.' in name:
        return urllib.parse.unquote(name)
    return f"download_{int(time.time())}"


def sanitize_filename(name: str, max_len: int = 100) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > max_len:
        name = name[:max_len]
    # If the name is empty or only underscores after sanitization, use a default
    if not name or not name.strip('_'):
        return "unnamed"
    return name


# ─── 错误诊断 (v4.3.1 新增，针对 R 维度优化) ──────────────────────────────────

# 错误码 → 用户可读解释 + 建议（与 TROUBLESHOOTING.md §8 对齐）
_HTTP_DIAGNOSTIC_TABLE = {
    400: ("请求格式错误", "检查 URL 参数和请求头"),
    401: ("需要鉴权", "当前为公开接口无需登录；如错误持续，可能源站策略变更"),
    403: ("访问被拒（IP/UA/反爬触发）", "切换代理 IP 或降低频率，详见 TROUBLESHOOTING.md §3.1"),
    404: ("资源不存在", "检查 URL 是否拼写正确，或更新到机构列表最新版"),
    418: ("被反爬系统识别", "启用 UA 轮换 + 降低频率，详见 TROUBLESHOOTING.md §3.4"),
    429: ("请求过于频繁", "降低并发到 max_workers=3 或加长 request_delay"),
    500: ("源站内部错误", "稍后重试，源站可能临时异常"),
    502: ("网关错误（CDN 故障）", "切换代理或等待 5-15 分钟"),
    503: ("服务暂不可用", "稍后重试；可能是源站维护中"),
    521: ("CDN Web 服务器宕机", "切换代理或等待"),
    522: ("CDN 连接超时", "切换代理或降低并发"),
    523: ("CDN 不可达", "源站 CDN 故障，等待 1-30 分钟后重试"),
}


def get_diagnostic(code_or_exc, url: str = "") -> dict:
    """根据 HTTP 状态码或异常返回结构化诊断信息。

    用于标准化网络错误的展示，方便用户在 [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) 中查询。

    Args:
        code_or_exc: HTTP 状态码（int）/ 异常对象（urllib.error.HTTPError, ConnectionError 等）
        url: 触发该错误的 URL（用于日志）

    Returns:
        dict: {
            "code": int 或 None,
            "title": str,         # 简短说明
            "suggestion": str,    # 可执行建议
            "doc_link": str,      # TROUBLESHOOTING 锚点
            "url": str,           # 触发 URL
        }

    Examples:
        >>> get_diagnostic(403, "https://example.com")
        {'code': 403, 'title': '访问被拒（IP/UA/反爬触发）',
         'suggestion': '切换代理 IP 或降低频率，详见 TROUBLESHOOTING.md §3.1',
         'doc_link': '#31-ip-被封--一直-403',
         'url': 'https://example.com'}

        >>> try:
        ...     urllib.request.urlopen(url)
        ... except urllib.error.HTTPError as e:
        ...     print(get_diagnostic(e, url))
    """
    # 提取 code（兼容多种输入）
    if isinstance(code_or_exc, int):
        code = code_or_exc
    elif hasattr(code_or_exc, "code"):
        code = int(code_or_exc.code)
    elif hasattr(code_or_exc, "status_code"):
        code = int(code_or_exc.status_code)
    else:
        code = None

    if code is not None and code in _HTTP_DIAGNOSTIC_TABLE:
        title, suggestion = _HTTP_DIAGNOSTIC_TABLE[code]
        # 根据 code 选择对应的 §X.Y 锚点
        anchors = {
            400: "#81-错误码速查表",   # 占位，实际查看速查表
            401: "#81-错误码速查表",
            403: "#31-ip-被封--一直-403",
            404: "#81-错误码速查表",
            418: "#34-user-agent-失效--抓到的是请升级浏览器",
            429: "#81-错误码速查表",
            500: "#82-反复-504-502-网关错误",
            502: "#82-反复-504-502-网关错误",
            503: "#82-反复-504-502-网关错误",
            521: "#82-反复-504-502-网关错误",
            522: "#82-反复-504-502-网关错误",
            523: "#82-反复-504-502-网关错误",
        }
        doc_link = anchors.get(code, "#81-错误码速查表")
    else:
        title = "未知错误"
        suggestion = "查看完整堆栈后查阅 TROUBLESHOOTING.md 或提 issue"
        doc_link = "#9-如何提-issue"

    return {
        "code": code,
        "title": title,
        "suggestion": suggestion,
        "doc_link": doc_link,
        "url": url,
    }


def format_diagnostic(code_or_exc, url: str = "") -> str:
    """便捷函数：把 get_diagnostic() 格式化成可粘贴的多行字符串。"""
    d = get_diagnostic(code_or_exc, url)
    lines = []
    if d["code"] is not None:
        lines.append(f"❌ HTTP {d['code']}: {d['title']}")
    else:
        lines.append(f"❌ {d['title']}")
    if d["url"]:
        lines.append(f"   URL: {d['url']}")
    lines.append(f"   建议: {d['suggestion']}")
    lines.append(f"   文档: TROUBLESHOOTING.md{d['doc_link']}")
    return "\n".join(lines)

