# -*- coding: utf-8 -*-
"""
金融数据爬虫核心模块 v4.2
统一的爬取入口：Scrapling（高级反爬）→ Playwright（JS渲染）→ http_utils（标准请求）→ 本地缓存

v3.0 改进：
- 六级降级链：Scrapling(隐身) → Scrapling(移动) → Playwright(JS渲染) → http_utils(桌面) → http_utils(移动) → 过期缓存
- 多源数据降级：基金净值/股票行情/公告 支持自动切换备用数据源
- 域名健康检查与熔断：连续失败自动暂停，恢复后自动探测
- 整合 http_utils v4.0（UA 轮换、多策略重试、自适应限流、指纹随机化）

v2.1:
- 整合 http_utils 公共基础设施（统一限流/重试/会话复用）
- 三级降级链：Scrapling 隐身模式 → requests 标准请求 → 本地缓存
- 请求去重 + 缓存避免重复爬取
- 自动重试机制 + 断点续爬 + 失败记录
- 增强错误提示，提供详细排查步骤和解决方案
"""

from __future__ import annotations

import json
import re
import time
import hashlib
import threading
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
from enum import Enum

# Scrapling导入（可选增强）
try:
    from scrapling.fetchers import StealthyFetcher
    from scrapling.parser import Selector
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    if TYPE_CHECKING:
        Selector = Any  # type: ignore

# Playwright 导入（可选增强）
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# http_utils 公共基础设施（v4.0）
try:
    from .http_utils import (
        http_get, http_get_json, get_session, rate_limit, download_file, sanitize_filename,
        random_ua, get_best_ua_for_domain,
        report_request_result, get_adaptive_delay,
        clear_cache as clear_http_cache,
    )
except ImportError:
    from http_utils import (
        http_get, http_get_json, get_session, rate_limit, download_file, sanitize_filename,
        random_ua, get_best_ua_for_domain,
        report_request_result, get_adaptive_delay,
        clear_cache as clear_http_cache,
    )

# 数据目录
SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = SKILL_DATA_DIR / "scrape_cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# 请求限流（由 http_utils 管理，此处保留常量供参考）
DELAY_BETWEEN_REQUESTS = 2  # 秒
MAX_REQUESTS_PER_MINUTE = 30
DEFAULT_TIMEOUT = 30  # 秒

# 缓存有效期（按域名区分）
CACHE_TTL_HOURS = 24  # 默认：24小时内不重复爬取同一URL
CACHE_TTL_BY_DOMAIN = {
    "eastmoney.com": 2,   # 行情数据2小时刷新
    "10jqka.com.cn": 1,   # 实时数据1小时
    "sina.com.cn": 4,     # 新浪财经4小时
    "xueqiu.com": 6,      # 雪球6小时
    "default": CACHE_TTL_HOURS,
}
# 请求去重（防止同一 session 内重复请求同一 URL）
_requested_urls: set = set()

# ─── 降级策略枚举（v3.0） ──────────────────────────────────────────────────────

class FallbackLevel(Enum):
    """降级链级别"""
    SCRAPLING_STEALTH = 0    # Scrapling 隐身模式（最优先）
    SCRAPLING_MOBILE = 1     # Scrapling 移动端
    PLAYWRIGHT = 2           # Playwright JS 渲染
    HTTP_DESKTOP = 3         # http_utils 桌面 UA
    HTTP_MOBILE = 4          # http_utils 移动 UA
    EXPIRED_CACHE = 5        # 过期缓存（最后手段）

# ─── 多源数据降级映射（v3.0） ────────────────────────────────────────────────────

# 基金净值备用源
FUND_NAV_FALLBACKS: Dict[str, List[str]] = {
    "eastmoney.com": [
        # 天天基金 → 新浪基金 → 东方财富手机版 API → 蛋卷
        "https://fundgz.1234567.com.cn/js/{code}.js",          # 天天基金估算净值 API
        "https://hq.sinajs.cn/list=f_{code}",                   # 新浪基金行情
        "https://push2.eastmoney.com/api/qt/stock/get?secid=0.{code}&fields=f43,f44,f45,f46,f47,f48,f170",
    ],
}

# 股票行情备用源
STOCK_QUOTE_FALLBACKS: Dict[str, List[str]] = {
    "eastmoney.com": [
        "https://hq.sinajs.cn/list={market}{code}",             # 新浪股票行情
        "https://push2.eastmoney.com/api/qt/stock/get?secid={market_id}.{code}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f170",
        "https://qt.gtimg.cn/q={market}{code}",                 # 腾讯股票行情
    ],
    "sina.com.cn": [
        "https://push2.eastmoney.com/api/qt/stock/get?secid={market_id}.{code}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f170",
        "https://qt.gtimg.cn/q={market}{code}",                 # 腾讯股票行情
    ],
}

# 公告搜索备用源
ANNOUNCEMENT_FALLBACKS: Dict[str, str] = {
    "eastmoney.com": "http://www.cninfo.com.cn/new/disclosure/stock?stockCode={code}&orgId={org_id}",
    "cninfo.com.cn": "https://np-anotice-stock.eastmoney.com/api/security/ann?stockCode={code}&pageSize=30",
}


class ScrapingError(Exception):
    """爬取错误基类"""
    def __init__(self, message: str, error_type: str = "unknown", hint: str = ""):
        self.message = message
        self.error_type = error_type
        self.hint = hint
        super().__init__(self.message)


class NetworkError(ScrapingError):
    """网络相关错误"""
    def __init__(self, message: str, hint: str = "请检查网络连接，或稍后重试"):
        super().__init__(message, "network", hint)


class ScrapingTimeoutError(ScrapingError):
    """超时错误"""
    def __init__(self, message: str, hint: str = "目标网站响应较慢，可以尝试：1) 稍后重试 2) 使用动态渲染模式 3) 检查网络状况"):
        super().__init__(message, "timeout", hint)


class ParseError(ScrapingError):
    """解析错误"""
    def __init__(self, message: str, hint: str = "页面结构可能已变更，可以尝试更新选择器或使用动态渲染"):
        super().__init__(message, "parse", hint)


class DependencyError(ScrapingError):
    """依赖缺失错误"""
    def __init__(self, message: str, hint: str = "请运行: pip install scrapling playwright && playwright install chromium"):
        super().__init__(message, "dependency", hint)


# ─── 域名健康追踪与熔断（v3.0） ──────────────────────────────────────────────────

class DomainHealthTracker:
    """域名健康检查与熔断器

    追踪各域名的请求成功率，连续失败达到阈值后自动熔断，
    熔断期间返回缓存数据，半开后探测恢复。
    """

    def __init__(self, fail_threshold: int = 3, cooldown_seconds: float = 60.0,
                 half_open_probe_seconds: float = 30.0):
        self.fail_threshold = fail_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_probe_seconds = half_open_probe_seconds

        self._consecutive_fails: Dict[str, int] = {}
        self._blocked_until: Dict[str, float] = {}
        self._total_requests: Dict[str, int] = {}
        self._total_failures: Dict[str, int] = {}
        self._last_probe: Dict[str, float] = {}
        self._lock = threading.Lock()

    def record_success(self, domain: str):
        """记录一次成功"""
        with self._lock:
            self._consecutive_fails[domain] = 0
            self._total_requests[domain] = self._total_requests.get(domain, 0) + 1
            # 成功后清除熔断
            self._blocked_until.pop(domain, None)

    def record_failure(self, domain: str) -> bool:
        """记录一次失败

        Returns:
            是否触发熔断（调用方应暂停该域名请求）
        """
        with self._lock:
            fails = self._consecutive_fails.get(domain, 0) + 1
            self._consecutive_fails[domain] = fails
            self._total_requests[domain] = self._total_requests.get(domain, 0) + 1
            self._total_failures[domain] = self._total_failures.get(domain, 0) + 1

            if fails >= self.fail_threshold:
                self._blocked_until[domain] = time.time() + self.cooldown_seconds
                return True
            return False

    def is_blocked(self, domain: str) -> bool:
        """检查域名是否在熔断中"""
        with self._lock:
            blocked_until = self._blocked_until.get(domain, 0)
            if blocked_until > time.time():
                return True
            # 熔断已过期，进入半开状态
            if blocked_until > 0 and blocked_until <= time.time():
                # 半开状态：允许探测，但记录探测时间
                last_probe = self._last_probe.get(domain, 0)
                if time.time() - last_probe < self.half_open_probe_seconds:
                    return True  # 刚探测过不久，继续等待
                self._last_probe[domain] = time.time()
                self._blocked_until[domain] = 0
                return False
            return False

    def get_health(self, domain: str) -> Dict[str, Any]:
        """获取域名健康状态"""
        with self._lock:
            total = self._total_requests.get(domain, 0)
            failures = self._total_failures.get(domain, 0)
            return {
                "domain": domain,
                "blocked": self._blocked_until.get(domain, 0) > time.time(),
                "consecutive_fails": self._consecutive_fails.get(domain, 0),
                "success_rate": (total - failures) / total if total > 0 else 1.0,
                "total_requests": total,
            }

    def get_blocked_domains(self) -> List[str]:
        """获取当前熔断的域名列表"""
        with self._lock:
            now = time.time()
            return [d for d, t in self._blocked_until.items() if t > now]

    def reset(self, domain: Optional[str] = None):
        """重置健康状态（domain=None 则全部重置）"""
        with self._lock:
            if domain:
                for d in [domain]:
                    self._consecutive_fails.pop(d, None)
                    self._blocked_until.pop(d, None)
            else:
                self._consecutive_fails.clear()
                self._blocked_until.clear()
                self._total_requests.clear()
                self._total_failures.clear()
                self._last_probe.clear()


# 全局域名健康追踪器
_health_tracker = DomainHealthTracker()


class _CachedPage:
    """缓存命中的轻量页面包装（替代每次动态 type() 重建对象）。
    统一暴露 html / text / html_content 属性，与 Scrapling/requests 返回对象对齐。
    """
    __slots__ = ('html', 'text', 'html_content')

    def __init__(self, content: str):
        self.html = content
        self.text = content
        self.html_content = content

    def css(self, *args, **kwargs):
        """兼容调用：缓存命中时不支持 CSS 选择器，返回空列表"""
        return []

    def prettify(self):
        return self.html


class ScraperHelpers:
    """爬虫辅助工具"""

    @staticmethod
    def classify_error(e: Exception, operation: str = "操作") -> tuple:
        """分类错误并返回用户友好的错误信息和诊断提示

        Returns:
            tuple: (user_message, diagnostic_hint, error_type, solution_steps)
        """
        error_str = str(e).lower()
        error_type = type(e).__name__

        # 网络相关错误
        network_keywords = ['timeout', 'connection', 'network', '网络', '连接', '超时', 'dns', 'socket',
                          'econnreset', 'etimedout', 'enotfound', 'eai_again']
        if any(kw in error_str for kw in network_keywords) or 'httperror' in error_type.lower():
            return (
                f"{operation}失败，网络连接出现问题",
                "请按以下步骤排查：\n1. 检查网络连接是否正常\n2. 尝试访问其他网站确认网络通畅\n3. 如果使用代理，请检查代理配置\n4. 稍后重试，可能是目标网站临时不可用",
                "network",
                ["检查网络连接", "尝试其他网站", "检查代理配置", "稍后重试"]
            )

        # 超时错误
        timeout_keywords = ['timed out', 'timeout', '超时']
        if any(kw in error_str for kw in timeout_keywords):
            return (
                f"{operation}超时，目标网站响应太慢",
                "可能原因：\n1. 目标网站服务器繁忙\n2. 网络延迟较高\n3. 页面内容过大\n\n建议操作：\n1. 稍后重试\n2. 使用缓存模式：`use_cache=True`\n3. 增加超时时间：`timeout=60`",
                "timeout",
                ["稍后重试", "使用缓存模式", "增加超时时间"]
            )

        # Cloudflare/反爬
        if 'cloudflare' in error_str or 'captcha' in error_str:
            return (
                f"{operation}失败，遇到网站防护机制",
                "目标网站检测到自动化访问并进行了拦截。\n\n建议操作：\n1. 降低爬取频率\n2. 使用动态渲染模式：`mode='realtime'`\n3. 稍后重试\n4. 检查是否有验证码需要处理",
                "anti_scraper",
                ["降低爬取频率", "使用动态渲染", "稍后重试", "检查验证码"]
            )

        # 依赖缺失
        if 'import' in error_str or 'no module' in error_str or 'not found' in error_str:
            module_match = re.search(r"module '(\w+)'", error_str) or re.search(r"'(\w+)'", error_str)
            module_name = module_match.group(1) if module_match else "未知模块"
            return (
                f"{operation}失败，缺少必要的 Python 模块",
                f"缺少模块：`{module_name}`\n\n请运行以下命令安装：\n```bash\npip install {module_name}\n```\n\n或者安装所有依赖：\n```bash\npip install -r requirements.txt\n```",
                "dependency",
                [f"pip install {module_name}", "pip install -r requirements.txt"]
            )

        # JSON/数据解析错误
        if 'json' in error_str or 'decode' in error_str:
            return (
                f"{operation}失败，数据格式异常",
                "目标网站返回的数据格式不符合预期。\n\n可能原因：\n1. 页面结构已变更\n2. 返回了错误页面（如登录页）\n3. 网络问题导致数据不完整\n\n建议：\n1. 检查 URL 是否正确\n2. 尝试使用动态渲染模式\n3. 查看缓存中是否有历史数据",
                "parse",
                ["检查 URL", "使用动态渲染", "查看缓存数据"]
            )

        # 元素未找到
        if 'no such' in error_str or 'not found' in error_str or 'none' in error_str:
            return (
                f"{operation}失败，页面中找不到目标内容",
                "可能原因：\n1. 页面结构已更新\n2. 内容需要登录才能查看\n3. 使用了错误的选择器\n\n建议：\n1. 检查 URL 是否可直接访问\n2. 尝试使用动态渲染模式\n3. 更新选择器配置",
                "parse",
                ["检查 URL", "使用动态渲染", "更新选择器"]
            )

        # 权限错误
        if 'permission' in error_str or 'access denied' in error_str or '403' in error_str:
            return (
                f"{operation}失败，访问被拒绝",
                "目标网站拒绝了访问请求。\n\n可能原因：\n1. 需要登录或授权\n2. IP 被临时封禁\n3. 请求频率过高\n\n建议：\n1. 检查是否需要登录\n2. 降低请求频率\n3. 稍后重试",
                "permission",
                ["检查登录需求", "降低请求频率", "稍后重试"]
            )

        # 默认错误
        return (
            f"{operation}失败：{str(e)[:100]}",
            "请按以下步骤排查：\n1. 检查网络连接\n2. 确认 URL 是否正确\n3. 稍后重试\n4. 如果问题持续，请查看详细日志",
            "unknown",
            ["检查网络", "确认 URL", "稍后重试", "查看日志"]
        )


class FinancialPageScraper:
    """金融页面爬取器 v3.0

    六级降级链 + 自动重试 + 断点续爬 + 域名熔断：
    1. Scrapling 隐身模式（反反爬）→
    2. Scrapling 移动端模式 →
    3. Playwright JS 渲染 →
    4. http_utils 桌面 UA 请求 →
    5. http_utils 移动 UA 请求 →
    6. 本地过期缓存（离线可用）

    域名健康检查：连续失败 >=3 次自动熔断 60s。
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, use_cache: bool = True,
                 max_retries: int = 3, auto_recovery: bool = True,
                 enable_health_tracker: bool = True):
        self.timeout = timeout
        self.use_cache = use_cache
        self.max_retries = max_retries
        self.auto_recovery = auto_recovery
        self.enable_health_tracker = enable_health_tracker
        self._helpers = ScraperHelpers()
        self._fetcher = None
        self._failed_urls: List[Dict[str, str]] = []
        self._progress_file = SKILL_DATA_DIR / "crawl_progress.json"

    # ── 缓存 ──

    def _cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _cache_path(self, url: str) -> Path:
        return CACHE_DIR / f"{self._cache_key(url)}.html"

    def _cache_ttl(self, url: str) -> float:
        """根据域名获取缓存 TTL（秒）"""
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            domain = ""
        for pattern, ttl_hours in CACHE_TTL_BY_DOMAIN.items():
            if pattern in domain:
                return ttl_hours * 3600
        return CACHE_TTL_HOURS * 3600

    def _cache_get(self, url: str, allow_expired: bool = False) -> Optional[str]:
        """获取缓存内容

        Args:
            url: 目标 URL
            allow_expired: 是否允许返回过期缓存（用于网络失败时降级）

        Returns:
            缓存的 HTML 内容，无缓存返回 None
        """
        if not self.use_cache:
            return None
        p = self._cache_path(url)
        if not p.exists():
            return None
        age = time.time() - p.stat().st_mtime
        ttl = self._cache_ttl(url)

        # 正常模式：过期则删除
        if age > ttl and not allow_expired:
            p.unlink(missing_ok=True)
            return None

        # 降级模式：过期但仍可用
        if age > ttl and allow_expired:
            # 过期超过 7 天则不使用
            if age > ttl * 7:
                return None

        return p.read_text(encoding='utf-8')

    def _cache_set(self, url: str, html: str):
        if not self.use_cache or not html:
            return
        self._cache_path(url).write_text(html, encoding='utf-8')

    def cleanup_cache(self, max_size_mb: int = 500) -> Dict[str, Any]:
        """清理过期和超大缓存

        Args:
            max_size_mb: 缓存目录最大大小（MB）

        Returns:
            清理结果统计
        """
        cache_files = sorted(CACHE_DIR.glob("*.html"), key=lambda f: f.stat().st_mtime)
        total_size = sum(f.stat().st_size for f in cache_files)
        deleted_count = 0
        deleted_size = 0

        # 1. 删除过期文件（超过 2 倍 TTL）
        for f in cache_files:
            age = time.time() - f.stat().st_mtime
            if age > CACHE_TTL_HOURS * 3600 * 2:
                deleted_size += f.stat().st_size
                f.unlink(missing_ok=True)
                deleted_count += 1

        # 2. 如果仍然超限，按 LRU 删除最旧的文件
        remaining_files = sorted(CACHE_DIR.glob("*.html"), key=lambda f: f.stat().st_mtime)
        remaining_size = sum(f.stat().st_size for f in remaining_files)
        max_size_bytes = max_size_mb * 1024 * 1024

        if remaining_size > max_size_bytes:
            for f in remaining_files:
                if remaining_size <= max_size_bytes:
                    break
                file_size = f.stat().st_size
                remaining_size -= file_size
                deleted_size += file_size
                f.unlink(missing_ok=True)
                deleted_count += 1

        result = {
            "deleted_count": deleted_count,
            "deleted_size_mb": round(deleted_size / 1024 / 1024, 2),
            "remaining_count": len(list(CACHE_DIR.glob("*.html"))),
            "remaining_size_mb": round(remaining_size / 1024 / 1024, 2)
        }

        if deleted_count > 0:
            print(f"🧹 缓存清理完成: 删除 {deleted_count} 个文件，释放 {result['deleted_size_mb']} MB")

        return result

    # ── 爬取（v3.0 六级降级链） ──

    def scrape_url(self, url: str, use_dynamic: bool = False,
                   fallback_chain: Optional[List[FallbackLevel]] = None) -> Optional[Any]:
        """
        爬取URL页面（六级降级链）。

        Args:
            url: 目标 URL
            use_dynamic: 是否强制使用动态渲染
            fallback_chain: 自定义降级链，默认全部启用

        Returns:
            Scrapling Selector / StdlibResponse / _CachedPage / None
        """
        domain = urlparse(url).netloc.lower() if url else ""

        # 域名熔断检查
        if self.enable_health_tracker and _health_tracker.is_blocked(domain):
            cached = self._cache_get(url, allow_expired=True)
            if cached:
                return _CachedPage(cached)
            return None

        # 1. 查缓存
        cached = self._cache_get(url)
        if cached:
            return _CachedPage(cached)

        # 确定降级链
        if fallback_chain is None:
            if use_dynamic:
                fallback_chain = [FallbackLevel.PLAYWRIGHT, FallbackLevel.SCRAPLING_STEALTH,
                                  FallbackLevel.HTTP_DESKTOP, FallbackLevel.HTTP_MOBILE]
            else:
                fallback_chain = [FallbackLevel.SCRAPLING_STEALTH, FallbackLevel.SCRAPLING_MOBILE,
                                  FallbackLevel.PLAYWRIGHT, FallbackLevel.HTTP_DESKTOP,
                                  FallbackLevel.HTTP_MOBILE]

        # 逐级尝试
        for level in fallback_chain:
            try:
                result = self._try_fallback_level(url, level)
                if result is not None:
                    html = getattr(result, 'html', '') or getattr(result, 'html_content', '') or ''
                    if not html and hasattr(result, 'text'):
                        html = result.text
                    if html:
                        self._cache_set(url, html)
                    if self.enable_health_tracker:
                        _health_tracker.record_success(domain)
                    return result
            except Exception:
                pass

        # 全部失败 -> 尝试过期缓存
        if self.enable_health_tracker:
            _health_tracker.record_failure(domain)

        expired = self._cache_get(url, allow_expired=True)
        if expired:
            return _CachedPage(expired)

        return None

    def _try_fallback_level(self, url: str, level: FallbackLevel) -> Optional[Any]:
        """尝试降级链中的某个级别"""
        if level == FallbackLevel.SCRAPLING_STEALTH:
            if SCRAPLING_AVAILABLE:
                return self._scrape_scrapling(url, mobile=False)

        elif level == FallbackLevel.SCRAPLING_MOBILE:
            if SCRAPLING_AVAILABLE:
                return self._scrape_scrapling(url, mobile=True)

        elif level == FallbackLevel.PLAYWRIGHT:
            if PLAYWRIGHT_AVAILABLE:
                return self._scrape_playwright(url)

        elif level == FallbackLevel.HTTP_DESKTOP:
            resp = http_get(url, timeout=self.timeout, rate_limit_delay=1.0)
            if resp is not None:
                return resp

        elif level == FallbackLevel.HTTP_MOBILE:
            s = get_session(mobile=True, rotate_ua=True, randomize_fingerprint=True)
            resp = http_get(url, timeout=self.timeout, rate_limit_delay=1.0, session=s)
            if resp is not None:
                return resp

        elif level == FallbackLevel.EXPIRED_CACHE:
            cached = self._cache_get(url, allow_expired=True)
            if cached:
                return _CachedPage(cached)

        return None

    def _scrape_scrapling(self, url: str, mobile: bool = False) -> Optional[Any]:
        """Scrapling 隐身爬取（v3.0: 支持移动端模式）"""
        if self._fetcher is None:
            try:
                self._fetcher = StealthyFetcher()
            except Exception:
                return None

        try:
            if mobile:
                try:
                    mobile_fetcher = StealthyFetcher()
                    page = mobile_fetcher.fetch(url, timeout=self.timeout)
                except Exception:
                    page = self._fetcher.fetch(url, timeout=self.timeout)
            else:
                page = self._fetcher.fetch(url, timeout=self.timeout)

            # scrapling 0.2.x compat: .html_content → .html
            if hasattr(page, 'html_content') and not hasattr(page, 'html'):
                page.html = page.html_content
            elif hasattr(page, 'body') and isinstance(page.body, str) and not hasattr(page, 'html'):
                page.html = page.body
            return page
        except Exception:
            return None

    def _scrape_playwright(self, url: str) -> Optional[Any]:
        """Playwright JS 渲染爬取"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random_ua(mobile=False)
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                html = page.content()
                browser.close()
                if html:
                    return _CachedPage(html)
        except Exception:
            pass
        return None

    def scrape_url_with_retry(self, url: str, use_dynamic: bool = False) -> Optional[Any]:
        """
        带自动重试的爬取方法（v3.0: 内部调用六级降级链）

        Args:
            url: 目标 URL
            use_dynamic: 是否使用动态渲染

        Returns:
            爬取结果，失败返回 None
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = self.scrape_url(url, use_dynamic=use_dynamic)
                if result is not None:
                    # 成功，清除失败记录
                    self._remove_from_failed(url)
                    return result
            except Exception as e:
                last_error = e
                user_msg, hint, error_type, solutions = self._helpers.classify_error(e, "爬取")

                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待：2s, 4s, 6s...
                    print(f"⚠️ 第 {attempt + 1} 次尝试失败: {user_msg}")
                    print(f"   {hint}")
                    print(f"   {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ {self.max_retries} 次尝试均失败: {user_msg}")
                    print(f"   {hint}")
                    if solutions:
                        print(f"   建议操作: {', '.join(solutions[:3])}")
                    self._add_to_failed(url, str(e))

        # 所有重试失败后，尝试使用过期缓存降级
        expired = self._cache_get(url, allow_expired=True)
        if expired:
            print(f"⚠️ 网络请求失败，使用过期缓存数据: {url[:80]}")
            return _CachedPage(expired)

        return None

    def _add_to_failed(self, url: str, error: str):
        """记录失败的 URL"""
        self._failed_urls.append({
            "url": url,
            "error": error,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._save_progress()

    def _remove_from_failed(self, url: str):
        """从失败列表中移除"""
        self._failed_urls = [f for f in self._failed_urls if f["url"] != url]
        self._save_progress()

    def _save_progress(self):
        """保存进度到文件"""
        if self.auto_recovery and self._failed_urls:
            try:
                with open(self._progress_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "failed_urls": self._failed_urls,
                        "last_update": time.strftime("%Y-%m-%d %H:%M:%S")
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ 保存进度失败: {e}")

    def load_progress(self) -> List[str]:
        """加载未完成的 URL 列表"""
        if self._progress_file.exists():
            try:
                with open(self._progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [item["url"] for item in data.get("failed_urls", [])]
            except Exception:
                pass
        return []

    def retry_failed(self) -> Dict[str, Any]:
        """
        重试所有失败的 URL

        Returns:
            重试结果统计
        """
        failed_urls = self.load_progress()
        if not failed_urls:
            print("✅ 没有需要重试的 URL")
            return {"retried": 0, "success": 0, "failed": 0}

        print(f"🔄 重试 {len(failed_urls)} 个失败的 URL...")
        results = {"retried": len(failed_urls), "success": 0, "failed": 0}

        for url in failed_urls:
            result = self.scrape_url_with_retry(url)
            if result:
                results["success"] += 1
                print(f"  ✅ {url}")
            else:
                results["failed"] += 1
                print(f"  ❌ {url}")

        print(f"\n📊 重试结果: {results['success']}/{results['retried']} 成功")
        return results

    def clear_progress(self):
        """清除进度文件"""
        if self._progress_file.exists():
            self._progress_file.unlink(missing_ok=True)
            self._failed_urls.clear()
            print("✅ 已清除进度文件")

    def extract_fund_info(self, page: Selector, url: str) -> Dict[str, Any]:
        """
        从天天基金页面提取基金信息

        Args:
            page: Selector对象
            url: 原始URL

        Returns:
            基金信息字典
        """
        result = {
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": "",
            "product_code": "",
            "product_type": "",
            "company": "",
            "manager": "",
            "risk_level": "",
            "nav": {},
            "historical_nav": {},
            "holdings": {"stocks": [], "top_industry": ""},
            "risk_metrics": {},
            "fees": {}
        }

        try:
            # 提取基金代码（从URL或页面）
            code_match = re.search(r'fund\.eastmoney\.com/(\d{6})', url)
            if code_match:
                result["product_code"] = code_match.group(1)

            # 尝试多种选择器
            selectors_to_try = [
                # 基金名称
                ['.fundName', '.fund-title', '.fundname', '[class*="fundName"]', 'h1'],
                # 基金代码
                ['.fundCode', '.fundcode', '[class*="code"]', '.title .code'],
                # 基金类型
                ['.fundType', '.type', '[class*="type"]'],
                # 基金经理
                ['.manager a', '.基金经理', '[class*="manager"] a', '.fundManager a'],
            ]

            # 提取文本内容
            for sel_list in selectors_to_try:
                for sel in sel_list:
                    try:
                        elements = page.css(sel)
                        if elements and len(elements) > 0:
                            text = elements[0].text().strip()
                            if text:
                                if 'name' in str(sel).lower() or 'title' in str(sel).lower():
                                    result["product_name"] = text
                                elif 'code' in str(sel).lower():
                                    result["product_code"] = text
                                elif 'type' in str(sel).lower():
                                    result["product_type"] = text
                                elif 'manager' in str(sel).lower():
                                    result["manager"] = text
                                break
                    except:
                        continue

            # 提取净值数据
            nav_selectors = ['.nav', '.NAV', '[class*="nav"]', '.data .nav']
            for sel in nav_selectors:
                try:
                    elements = page.css(sel)
                    if elements:
                        text = elements[0].text()
                        # 尝试匹配净值数字
                        nav_match = re.search(r'(\d+\.\d+)', text)
                        if nav_match:
                            result["nav"]["current"] = float(nav_match.group(1))
                        break
                except:
                    continue

        except Exception as e:
            print(f"[警告] 解析过程出错: {e}")

        return result

    def extract_stock_info(self, page: Selector, url: str) -> Dict[str, Any]:
        """提取股票信息"""
        result = {
            "source_url": url,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stock_name": "",
            "stock_code": "",
            "price": {},
            "indicators": {},
            "financials": {}
        }

        try:
            # 股票代码
            code_match = re.search(r'(?:s[hz]|sh|sz|szse)\.(\d{6})', url.lower())
            if code_match:
                result["stock_code"] = code_match.group(1)

            # 股票名称
            name_sel = page.css('h1, .stock-name, [class*="name"]')
            if name_sel:
                result["stock_name"] = name_sel[0].text().strip()

            # 价格
            price_sel = page.css('.price, .current, [class*="price"]')
            if price_sel:
                price_text = price_sel[0].text()
                price_match = re.search(r'(\d+\.\d+)', price_text)
                if price_match:
                    result["price"]["current"] = float(price_match.group(1))

        except Exception as e:
            print(f"[警告] 股票解析出错: {e}")

        return result


def scrape_financial_product(url: str, product_type: str = "auto", use_retry: bool = True) -> Dict[str, Any]:
    """
    爬取金融产品信息

    Args:
        url: 产品URL
        product_type: 产品类型 ("fund", "stock", "auto")
        use_retry: 是否使用自动重试（默认 True）

    Returns:
        产品信息字典
    """
    scraper = FinancialPageScraper()

    # 自动检测类型
    if product_type == "auto":
        url_lower = url.lower()
        if 'eastmoney.com/fund' in url_lower or 'fund.eastmoney' in url_lower or 'fundf10' in url_lower:
            product_type = "fund"
        elif 'eastmoney.com/stock' in url_lower or 'stock.eastmoney' in url_lower:
            product_type = "stock"
        elif 'xueqiu.com' in url_lower:
            product_type = "stock"
        elif '10jqka.com.cn' in url_lower:
            product_type = "stock"
        elif 'danjuanapp' in url_lower or '蛋卷' in url:
            product_type = "fund"
        else:
            product_type = "fund"  # 默认

    # 决定是否使用动态渲染
    use_dynamic = '10jqka.com.cn' in url.lower() or 'tonghuashun' in url.lower() or 'xueqiu.com' in url.lower()

    # 使用带重试的爬取方法
    if use_retry:
        page = scraper.scrape_url_with_retry(url, use_dynamic=use_dynamic)
    else:
        page = scraper.scrape_url(url, use_dynamic=use_dynamic)

    if page is None:
        return {
            "error": "爬取失败",
            "hint": "请检查：1) 网络连接 2) URL是否正确 3) 目标网站是否可访问",
            "solutions": ["检查网络连接", "确认 URL 是否正确", "稍后重试", "使用动态渲染模式"]
        }

    # 根据类型提取
    if product_type == "fund":
        return scraper.extract_fund_info(page, url)
    elif product_type == "stock":
        return scraper.extract_stock_info(page, url)
    else:
        return {"error": f"未知产品类型: {product_type}", "hint": "支持类型: fund, stock"}


def save_to_cache(product_info: Dict[str, Any], cache_file: str = "scraped_products.json"):
    """保存到本地缓存"""
    cache_path = SKILL_DATA_DIR / cache_file
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有缓存
    existing = []
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            existing = []

    # 更新或添加
    code = product_info.get("product_code") or product_info.get("stock_code", "")
    if code:
        # 去除已存在的同代码记录
        existing = [x for x in existing if x.get("product_code") != code and x.get("stock_code") != code]
        existing.insert(0, product_info)

    # 写入
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return cache_path


# CLI入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python scraper.py <URL> [--retry-failed]")
        print("示例: python scraper.py https://fund.eastmoney.com/000001.html")
        print("重试失败: python scraper.py --retry-failed")
        sys.exit(1)

    # 重试失败的 URL
    if sys.argv[1] == "--retry-failed":
        scraper = FinancialPageScraper()
        results = scraper.retry_failed()
        sys.exit(0 if results["failed"] == 0 else 1)

    url = sys.argv[1]
    print(f"正在爬取: {url}")

    result = scrape_financial_product(url)
    print("\n结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 保存到缓存
    if "error" not in result:
        save_path = save_to_cache(result)
        print(f"\n已缓存到: {save_path}")