# -*- coding: utf-8 -*-
"""反爬增强工具集（anti_block_utils.py，v4.9.0 新增，v7.2.0 增强）

设计目标：
- 提供更细粒度的反爬策略，避免触发目标站防护
- 不破坏现有 http_utils.py，所有功能可独立使用
- 缺失依赖（httpx / curl_cffi / tls-client）时自动降级到 stdlib

主要能力：
1. **域级别限速** — 针对不同域名设置不同的最小间隔
2. **Cookie 持久化** — 跨请求保持登录态/会话态
3. **错误码识别与降级** — 403/429/503 自动识别
4. **条件请求** — If-None-Match / If-Modified-Since 节省带宽
5. **HTTP/2 + TLS 指纹模拟**（可选，需要 curl_cffi）
6. **指数退避重试** — 失败时智能延长间隔
7. **域级状态机** — 自动从禁用域中恢复
8. **URL 去重器**（v7.2.0）— 批量爬取避免重复请求同一 URL

v7.2.0 修复：DomainRateLimiter.reset 裸域名归一化失效；
PersistentCookieStore.load 误保留已过期 cookie。
"""
from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

log = logging.getLogger(__name__)


# ============================================================================
# 1. 域级别限速器（DomainRateLimiter）
# ============================================================================


class DomainRateLimiter:
    """对每个域名独立限速。

    用法:
        limiter = DomainRateLimiter({
            "cls.cn": 2.0,        # 财联社：2 秒 1 次
            "jisilu.cn": 5.0,     # 集思录：5 秒 1 次（更严）
            "default": 1.0,        # 默认：1 秒 1 次
        })

        limiter.wait("https://www.cls.cn/api/sw")  # 自动识别域名 + 等候
    """

    def __init__(self, intervals: Optional[Dict[str, float]] = None,
                 default_interval: float = 1.0):
        # 域名（不含子域） -> 最小间隔（秒）
        self.intervals: Dict[str, float] = dict(intervals or {})
        self.default_interval = default_interval
        self._last_called: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _normalize_domain(self, url: str) -> str:
        s = url.strip()
        # v7.2: 兼容裸域名（无 scheme，如 reset("cls.cn")）
        if "://" in s:
            host = urlparse(s).netloc.lower()
        else:
            host = s.lower().split("/")[0].split(":")[0]
        # 取主域名（last 2 segments）: www.cls.cn → cls.cn
        parts = [p for p in host.split(".") if p]
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return host

    def get_interval(self, url: str) -> float:
        domain = self._normalize_domain(url)
        return self.intervals.get(domain, self.intervals.get("default", self.default_interval))

    def wait(self, url: str) -> None:
        """按域级别间隔等候（线程安全）。"""
        domain = self._normalize_domain(url)
        interval = self.get_interval(url)
        with self._lock:
            now = time.monotonic()
            last = self._last_called.get(domain, 0.0)
            elapsed = now - last
            wait_sec = max(0.0, interval - elapsed)
            self._last_called[domain] = now + wait_sec
        if wait_sec > 0:
            time.sleep(wait_sec)

    def reset(self, domain: Optional[str] = None) -> None:
        """重置限速状态（force=True 测试用）。"""
        with self._lock:
            if domain:
                self._last_called.pop(self._normalize_domain(domain), None)
            else:
                self._last_called.clear()


# ============================================================================
# 2. Cookie 持久化（CookieJar 跨调用保留）
# ============================================================================


class PersistentCookieStore:
    """Cookie 跨调用/进程持久化（保存到 JSON 文件）。

    用法:
        store = PersistentCookieStore(Path("data/cookies/cls.json"))
        cookies = store.load()  # 启动时
        jar = CookieJar_from_dict(cookies)
        # ... 使用 jar 完成请求 ...
        store.save(jar)  # 退出前/定期保存
    """

    def __init__(self, file_path: Path, ttl_days: int = 30):
        self.file_path = Path(file_path)
        self.ttl_days = ttl_days
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def load(self) -> List[Dict[str, Any]]:
        """加载 cookie（自动剔除过期）。"""
        with self._lock:
            if not self.file_path.exists():
                return []
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"cookie 加载失败 {self.file_path}: {e}")
                return []
            if not isinstance(data, list):
                return []
        # v7.2 修复：已过期 cookie（expires 早于当前时间）必须剔除；
        # 此前误与 now-ttl_days 比较，导致刚过期的 cookie 仍被保留。
        now = datetime.now()
        valid = []
        for c in data:
            exp = c.get("expires")
            if exp is None:
                valid.append(c)
                continue
            try:
                if isinstance(exp, (int, float)):
                    exp_dt = datetime.fromtimestamp(exp)
                else:
                    exp_dt = datetime.fromisoformat(exp)
                if exp_dt > now:
                    valid.append(c)
            except Exception:
                valid.append(c)
        return valid

    def save(self, cookies: List[Dict[str, Any]]) -> None:
        """保存 cookie 到 JSON 文件。"""
        with self._lock:
            try:
                self.file_path.write_text(
                    json.dumps(cookies, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            except OSError as e:
                log.warning(f"cookie 保存失败 {self.file_path}: {e}")


# ============================================================================
# 3. 错误码识别（BlockDetector）
# ============================================================================


@dataclass
class BlockSignal:
    """被封信号。"""
    code: int
    reason: str
    cooldown: int = 300  # 默认冷却 5 分钟
    advice: str = ""


# 已知反爬响应模式
BLOCK_PATTERNS = [
    (403, "Forbidden", 600, "可能被 WAF / IP 黑名单拦截，建议 10 分钟后再试或换代理"),
    (429, "Too Many Requests", 120, "触发限速，自动延长间隔"),
    (503, "Service Unavailable", 60, "服务端临时不可用，建议 1 分钟后重试"),
    (451, "Unavailable For Legal Reasons", 1800,
     "可能因合规/法律原因被拒，建议换数据源（akshare / RSS）"),
]


def detect_block(status_code: int, headers: Optional[Dict[str, str]] = None,
                 body_sample: str = "") -> Optional[BlockSignal]:
    """检测是否被反爬封禁。

    Args:
        status_code: HTTP 状态码
        headers: 响应头
        body_sample: 响应正文前 500 字符（用于文本特征匹配）

    Returns:
        BlockSignal 实例；非封禁响应返回 None。
    """
    headers = headers or {}
    for code, reason, cooldown, advice in BLOCK_PATTERNS:
        if status_code == code:
            return BlockSignal(code=code, reason=reason, cooldown=cooldown, advice=advice)

    # 文本特征检测（某些站返回 200 但内容是反爬页面）
    body_lower = body_sample.lower() if body_sample else ""
    if status_code == 200 and body_lower:
        danger_signs = [
            # 中文站点常见反爬文案
            "访问频率过高", "请求过快", "请稍后再试", "访问过于频繁", "频繁访问",
            "请求过于频繁", "触发了安全机制", "异常流量", "安全检测", "安全验证",
            "滑动验证", "网站防火墙", "访问被拒绝", "请求被拒绝", "被禁止访问",
            "人机验证", "请输入验证码", "验证码", "拦截",
            # 英文站点常见反爬文案
            "access denied", "rate limit", "too many requests", "forbidden by",
            "captcha required", "unusual traffic", "attention required",
            "verify you are human", "automated access", "machine detected",
            "blocked by", "access denied by policy", "challenge",
        ]
        for sign in danger_signs:
            if sign in body_lower:
                return BlockSignal(
                    code=200, reason=f"软拦截：含「{sign}」",
                    cooldown=300, advice="检测到软拦截信号，建议切备用源",
                )

    # Cloudflare / 阿里云盾特征
    if "server" in headers:
        server = headers["server"].lower()
        if "aliyun" in server or "yundun" in server:
            if status_code in (403, 405, 503):
                return BlockSignal(code=status_code, reason="阿里云盾拦截",
                                    cooldown=600, advice="换代理或备用源")

    return None


# ============================================================================
# 4. 条件请求（If-None-Match / If-Modified-Since）
# ============================================================================


class ConditionalCache:
    """ETag / Last-Modified 缓存（节省重复请求的带宽）。

    用法:
        cache = ConditionalCache(Path("data/etag_cache.json"))
        headers = cache.get_request_headers(url)  # 增量 If-None-Match
        resp = http_get(url, headers=headers)
        if resp.status_code == 304:
            cached = cache.get_cached_body(url)
        else:
            cache.update(url, resp.headers.get("ETag"),
                        resp.headers.get("Last-Modified"),
                        resp.text)
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()
        self._lock = threading.Lock()

    def _load(self):
        if self.file_path.exists():
            try:
                self._data = json.loads(self.file_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self):
        try:
            self.file_path.write_text(
                json.dumps(self._data, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            log.warning(f"etag cache 保存失败: {e}")

    def get_request_headers(self, url: str) -> Dict[str, str]:
        """获取条件请求 headers（增量 If-None-Match / If-Modified-Since）。"""
        entry = self._data.get(url, {})
        headers = {}
        if entry.get("etag"):
            headers["If-None-Match"] = entry["etag"]
        if entry.get("last_modified"):
            headers["If-Modified-Since"] = entry["last_modified"]
        return headers

    def update(self, url: str, etag: Optional[str], last_modified: Optional[str],
               body: Optional[str] = None) -> None:
        """更新 URL 的 ETag/Last-Modified 记录。"""
        with self._lock:
            entry = self._data.setdefault(url, {})
            if etag:
                entry["etag"] = etag
            if last_modified:
                entry["last_modified"] = last_modified
            if body is not None:
                entry["body"] = body
                entry["cached_at"] = datetime.now().isoformat(timespec="seconds")
            # 限制大小（避免无界增长）
            if len(self._data) > 5000:
                # 清理最旧的 1000 条
                items = sorted(self._data.items(),
                               key=lambda kv: kv[1].get("cached_at", ""))
                for k, _ in items[:1000]:
                    del self._data[k]
            self._save()

    def get_cached_body(self, url: str) -> Optional[str]:
        return self._data.get(url, {}).get("body")


# ============================================================================
# 5. 指数退避重试（ExponentialBackoff）
# ============================================================================


def exponential_backoff(attempt: int,
                        base: float = 1.0,
                        max_delay: float = 60.0,
                        jitter: bool = True) -> float:
    """计算指数退避延迟。

    Args:
        attempt: 第 N 次尝试（从 1 开始）
        base: 基础延迟（秒）
        max_delay: 上限
        jitter: 是否加随机抖动（避免雷击）

    Returns:
        延迟秒数
    """
    delay = min(max_delay, base * (2 ** (attempt - 1)))
    if jitter:
        delay = delay * (0.5 + random.random())
    return delay


# ============================================================================
# 6. HTTP/2 + TLS 指纹（可选，需 curl_cffi）
# ============================================================================


class TLSFingerprintClient:
    """使用 curl_cffi 模拟真实浏览器 TLS 指纹（JA3）。

    用法:
        client = TLSFingerprintClient()
        resp = client.get("https://www.cls.cn/api/sw",
                          impersonate="chrome120")

    注意: 需要安装 curl_cffi（`pip install curl-cffi`）。
    未装时调用 get() 会抛 ImportError；调用方应捕获后降级到 stdlib。
    """

    def __init__(self):
        try:
            from curl_cffi import requests as cc_requests
            self._impl = cc_requests
            self._available = True
        except ImportError:
            self._impl = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get(self, url: str, impersonate: str = "chrome120",
            headers: Optional[Dict[str, str]] = None,
            timeout: int = 30, **kwargs) -> Any:
        if not self._available:
            raise ImportError("curl_cffi 未安装，请运行 `pip install curl-cffi`")
        return self._impl.get(
            url,
            impersonate=impersonate,
            headers=headers or {},
            timeout=timeout,
            **kwargs,
        )


# ============================================================================
# 7. 域级状态机（DomainHealth）
# ============================================================================


@dataclass
class DomainHealth:
    """域健康度追踪。"""
    domain: str
    enabled: bool = True
    last_success: Optional[str] = None  # ISO 时间
    last_failure: Optional[str] = None
    consecutive_failures: int = 0
    total_success: int = 0
    total_failure: int = 0
    last_block_reason: Optional[str] = None
    cooldown_until: Optional[str] = None  # ISO 时间


class DomainHealthTracker:
    """跟踪每个域名的健康度，自动禁用持续失败的域。"""

    def __init__(self, file_path: Optional[Path] = None,
                 disable_threshold: int = 5,
                 cooldown_seconds: int = 300):
        self.file_path = Path(file_path) if file_path else None
        self.disable_threshold = disable_threshold
        self.cooldown_seconds = cooldown_seconds
        self._domains: Dict[str, DomainHealth] = {}
        self._lock = threading.Lock()
        if self.file_path:
            self._load()

    def _load(self):
        if self.file_path and self.file_path.exists():
            try:
                raw = json.loads(self.file_path.read_text(encoding="utf-8"))
                self._domains = {k: DomainHealth(**v) for k, v in raw.items()}
            except (json.JSONDecodeError, OSError, TypeError):
                self._domains = {}

    def _save(self):
        if self.file_path:
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                self.file_path.write_text(
                    json.dumps({k: asdict(v) for k, v in self._domains.items()},
                              ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except OSError as e:
                log.warning(f"domain health 保存失败: {e}")

    def record_success(self, domain: str) -> None:
        with self._lock:
            h = self._domains.setdefault(domain, DomainHealth(domain=domain))
            h.last_success = datetime.now().isoformat(timespec="seconds")
            h.consecutive_failures = 0
            h.total_success += 1
            h.cooldown_until = None
            if not h.enabled:
                h.enabled = True
                log.info(f"域 {domain} 已恢复")
            self._save()

    def record_failure(self, domain: str, reason: str = "") -> None:
        with self._lock:
            h = self._domains.setdefault(domain, DomainHealth(domain=domain))
            h.last_failure = datetime.now().isoformat(timespec="seconds")
            h.consecutive_failures += 1
            h.total_failure += 1
            h.last_block_reason = reason
            if h.consecutive_failures >= self.disable_threshold:
                cooldown_dt = datetime.now() + timedelta(seconds=self.cooldown_seconds)
                h.cooldown_until = cooldown_dt.isoformat(timespec="seconds")
                if h.enabled:
                    log.warning(
                        f"域 {domain} 连续失败 {h.consecutive_failures} 次，"
                        f"禁用 {self.cooldown_seconds}s"
                    )
                    h.enabled = False
            self._save()

    def is_available(self, domain: str) -> bool:
        with self._lock:
            h = self._domains.get(domain)
            if not h:
                return True
            if not h.enabled:
                if h.cooldown_until:
                    try:
                        if datetime.fromisoformat(h.cooldown_until) < datetime.now():
                            h.enabled = True
                            h.consecutive_failures = 0
                            h.cooldown_until = None
                            self._save()
                            return True
                    except ValueError:
                        pass
                return h.enabled
            return True

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "domains": {k: asdict(v) for k, v in self._domains.items()},
                "disabled": [d for d, h in self._domains.items() if not h.enabled],
            }


# ============================================================================
# 8. URL 去重器（UrlDeduplicator，v7.2.0）
# ============================================================================


class UrlDeduplicator:
    """批量爬取 URL 去重（v7.2.0，可选文件持久化）。

    用法:
        dedup = UrlDeduplicator(Path("data/seen_urls.json"))  # 跨进程持久
        for url in candidate_urls:
            if not dedup.is_new(url):   # 首次见到返回 True 并记录
                continue
            crawl(url)

    归一化规则：host 小写、剔除默认端口（http:80 / https:443）、
    剔除 fragment、去尾部斜杠；query 保留原样（顺序可能影响服务端语义）。
    """

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = Path(file_path) if file_path else None
        self._seen: set = set()
        self._lock = threading.Lock()
        if self.file_path and self.file_path.exists():
            self._load()

    @staticmethod
    def normalize(url: str) -> str:
        """URL 归一化（去 fragment / 默认端口 / 尾斜杠，host 小写）"""
        try:
            p = urlparse(url.strip())
        except Exception:
            return url.strip()
        if not p.scheme or not p.netloc:
            return url.strip()
        host = p.netloc.lower()
        if p.scheme == "http" and host.endswith(":80"):
            host = host[:-3]
        elif p.scheme == "https" and host.endswith(":443"):
            host = host[:-4]
        path = p.path.rstrip("/") or "/"
        norm = f"{p.scheme}://{host}{path}"
        if p.query:
            norm += f"?{p.query}"
        return norm

    @staticmethod
    def _domain_of(url: str) -> str:
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return "unknown"
        parts = [s for s in host.split(".") if s]
        return ".".join(parts[-2:]) if len(parts) >= 2 else (host or "unknown")

    def is_new(self, url: str) -> bool:
        """首次见到该 URL 返回 True 并记录；已见过返回 False。"""
        key = self.normalize(url)
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            self._save_locked()
            return True

    def is_seen(self, url: str) -> bool:
        with self._lock:
            return self.normalize(url) in self._seen

    def mark(self, url: str) -> None:
        with self._lock:
            self._seen.add(self.normalize(url))
            self._save_locked()

    def stats(self) -> Dict[str, Any]:
        """返回总量与按主域名分布。"""
        with self._lock:
            by_domain: Dict[str, int] = {}
            for u in self._seen:
                d = self._domain_of(u)
                by_domain[d] = by_domain.get(d, 0) + 1
            return {"total": len(self._seen), "by_domain": by_domain}

    def clear(self) -> None:
        with self._lock:
            self._seen.clear()
            self._save_locked()

    def _load(self) -> None:
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self._seen = {str(u) for u in data}
        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"seen urls 加载失败 {self.file_path}: {e}")

    def _save_locked(self) -> None:
        """持久化（调用方需持锁）"""
        if not self.file_path:
            return
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(
                json.dumps(sorted(self._seen), ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            log.warning(f"seen urls 保存失败 {self.file_path}: {e}")


# ============================================================================
# 自检
# ============================================================================


def self_check() -> Dict[str, Any]:
    """返回反爬工具集健康度自检报告。"""
    return {
        "exponential_backoff": "OK（标准库实现）",
        "domain_rate_limiter": "OK（线程安全）",
        "persistent_cookie": "OK（文件持久化）",
        "block_detector": f"覆盖 {len(BLOCK_PATTERNS)} 种已知模式",
        "conditional_cache": "OK（ETag / Last-Modified）",
        "tls_fingerprint_client": "✅ 可用" if TLSFingerprintClient().available
                                   else "⚠️ curl_cffi 未装（pip install curl-cffi）",
        "domain_health_tracker": "OK",
        "url_deduplicator": "OK（v7.2.0，可选持久化）",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(self_check(), ensure_ascii=False, indent=2))