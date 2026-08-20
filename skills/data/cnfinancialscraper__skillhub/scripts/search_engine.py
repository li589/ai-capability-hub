# -*- coding: utf-8 -*-
"""
search_engine.py v1.0 — 多搜索引擎聚合（零依赖）
====================================================
支持的搜索引擎（按优先级）：
1. BingAPISearch      — 有 BING_API_KEY 时启用（最稳定）
2. GoogleAPISearch    — 有 GOOGLE_API_KEY + GOOGLE_CSE_ID 时启用
3. DuckDuckGoHTML     — html.duckduckgo.com/html/（零依赖默认）
4. SearXNGSearch      — 公共实例列表（零依赖但可用性看实例）
5. BingHTML / GoogleHTML — 解析 SERP HTML（易反爬，仅 fallback）

用法:
    from search_engine import MultiEngineSearch
    s = MultiEngineSearch(engines=["duckduckgo"])
    results = s.search("贵州茅台 2024 年报", limit=10)
    for r in results:
        print(r.title, r.url)
"""
from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Any


# ============== 数据模型 ==============

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source_engine: str
    rank: int = 0
    fetched_at: str = ""
    credibility: int = 5  # 0-10

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============== 基类 ==============

class SearchEngineBase:
    """搜索引擎基类。"""
    name: str = "base"
    credibility: int = 5
    needs_api_key: bool = False

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def search(self, query: str, limit: int = 10,
               **kwargs) -> List[SearchResult]:
        raise NotImplementedError

    def _http_get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """HTTP GET，返回 text/None。"""
        req = urllib.request.Request(url)
        req.add_header("User-Agent",
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/131.0.0.0 Safari/537.36")
        req.add_header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                # 解码
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                try:
                    return raw.decode(charset, errors="replace")
                except (LookupError, TypeError):
                    return raw.decode("utf-8", errors="replace")
        except Exception:
            return None


# ============== DuckDuckGo HTML（零依赖默认） ==============

class DuckDuckGoHTML(SearchEngineBase):
    """DuckDuckGo HTML 端点解析（无需 API key）。"""
    name = "duckduckgo"
    credibility = 7

    BASE_URL = "https://html.duckduckgo.com/html/"

    # UA 轮换池
    _UA_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    ]

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")

        # 最多重试 3 次，每次换 UA
        for attempt in range(3):
            if results:
                break
            req = urllib.request.Request(self.BASE_URL, data=data, method="POST")
            ua = random.choice(self._UA_POOL)
            req.add_header("User-Agent", ua)
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
                results = _parse_ddg_html(html, self.name, self.credibility, limit)
            except Exception:
                if attempt < 2:
                    time.sleep(random.uniform(0.5, 1.5))
                continue
        return results


def _parse_ddg_html(html: str, engine: str, credibility: int,
                    limit: int) -> List[SearchResult]:
    """解析 DuckDuckGo HTML 结果。"""
    results: List[SearchResult] = []
    # DDG 的结果结构：<a class="result__a" href="...">title</a> + <a class="result__snippet">...</a>
    # 用正则简单提取
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
        r'.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL | re.IGNORECASE
    )
    fetched_at = datetime.now().isoformat()
    for i, m in enumerate(pattern.finditer(html)):
        if i >= limit:
            break
        url = _unescape_html(m.group(1))
        title = _strip_tags(m.group(2)).strip()
        snippet = _strip_tags(m.group(3)).strip()
        results.append(SearchResult(
            title=title, url=url, snippet=snippet,
            source_engine=engine, rank=i + 1,
            fetched_at=fetched_at, credibility=credibility,
        ))
    return results


# ============== Bing HTML / Google HTML（fallback） ==============

class BingHTML(SearchEngineBase):
    """Bing SERP HTML 解析（易反爬）。"""
    name = "bing_html"
    credibility = 6

    BASE_URL = "https://www.bing.com/search"

    # UA 轮换池（模拟真实浏览器）
    _UA_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    ]

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        url = f"{self.BASE_URL}?q={urllib.parse.quote(query)}&count={limit}"
        # 限制搜索中文内容
        url += "&setlang=zh-Hans&cc=cn"

        for attempt in range(3):
            if results:
                break
            ua = random.choice(self._UA_POOL)
            headers = {
                "User-Agent": ua,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.bing.com/",
            }
            html = self._http_get(url, headers=headers)
            if not html:
                if attempt < 2:
                    time.sleep(random.uniform(1.0, 2.5))
                continue

            # Bing 结果：<li class="b_algo"><h2><a href="...">title</a></h2>...<p>snippet</p>
            pattern = re.compile(
                r'<li[^>]+class="b_algo"[^>]*>.*?<h2>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
                r'.*?<p[^>]*>(.*?)</p>',
                re.DOTALL | re.IGNORECASE
            )
            # 备用模式：Bing 有时使用不同结构
            alt_pattern = re.compile(
                r'<a[^>]+class="[^"]*tilk[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                re.DOTALL | re.IGNORECASE
            )

            fetched_at = datetime.now().isoformat()
            for i, m in enumerate(pattern.finditer(html)):
                if i >= limit:
                    break
                results.append(SearchResult(
                    title=_strip_tags(m.group(2)),
                    url=m.group(1),
                    snippet=_strip_tags(m.group(3)),
                    source_engine=self.name,
                    rank=i + 1,
                    fetched_at=fetched_at,
                    credibility=self.credibility,
                ))

            # 主模式没匹配到，尝试备用模式
            if not results:
                for i, m in enumerate(alt_pattern.finditer(html)):
                    if i >= limit:
                        break
                    results.append(SearchResult(
                        title=_strip_tags(m.group(2)),
                        url=m.group(1),
                        snippet="",
                        source_engine=self.name,
                        rank=i + 1,
                        fetched_at=fetched_at,
                        credibility=self.credibility,
                    ))

            if results or attempt >= 2:
                break
            time.sleep(random.uniform(1.0, 2.5))

        return results


class BaiduHTML(SearchEngineBase):
    """百度 SERP HTML 解析（v5.0.0 新增）— 中文财经召回最佳，大陆可达性最优。"""
    name = "baidu_html"
    credibility = 8

    BASE_URL = "https://www.baidu.com/s"

    _UA_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    ]

    @staticmethod
    def _resolve_baidu_url(href: str) -> str:
        """还原百度 /link?url= 跳转链接为真实目标 URL。"""
        if "/link?url=" in href:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            real = qs.get("url")
            if real:
                return real[0]
        return href

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        url = f"{self.BASE_URL}?wd={urllib.parse.quote(query)}&rn={limit}&ie=utf-8"

        for attempt in range(3):
            if results:
                break
            ua = random.choice(self._UA_POOL)
            headers = {
                "User-Agent": ua,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.baidu.com/",
            }
            html = self._http_get(url, headers=headers)
            if not html:
                if attempt < 2:
                    time.sleep(random.uniform(1.0, 2.5))
                continue

            # 主模式：<h3 ...><a href="...">标题</a></h3>
            pattern = re.compile(
                r'<h3[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*</h3>',
                re.DOTALL | re.IGNORECASE
            )
            # 摘要：c-abstract / content-right_8Zs40 等容器
            snip_pattern = re.compile(
                r'<div[^>]+class="[^"]*(?:c-abstract|content-right_8Zs40)[^"]*"[^>]*>(.*?)</div>',
                re.DOTALL | re.IGNORECASE
            )
            snippets = [_strip_tags(m.group(1)) for m in snip_pattern.finditer(html)]

            fetched_at = datetime.now().isoformat()
            for i, m in enumerate(pattern.finditer(html)):
                if i >= limit:
                    break
                title = _strip_tags(m.group(2)).strip()
                if not title:
                    continue
                results.append(SearchResult(
                    title=title,
                    url=self._resolve_baidu_url(m.group(1)),
                    snippet=snippets[i] if i < len(snippets) else "",
                    source_engine=self.name,
                    rank=i + 1,
                    fetched_at=fetched_at,
                    credibility=self.credibility,
                ))

            if results or attempt >= 2:
                break
            time.sleep(random.uniform(1.0, 2.5))

        return results


class SogouHTML(SearchEngineBase):
    """搜狗 SERP HTML 解析（v5.0.0 新增）— 微信公众号内容检索入口。"""
    name = "sogou_html"
    credibility = 7

    BASE_URL = "https://www.sogou.com/web"

    _UA_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    ]

    @staticmethod
    def _resolve_sogou_url(href: str) -> str:
        """还原搜狗 /link?url= 跳转链接为真实目标 URL。"""
        if "/link?url=" in href:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            real = qs.get("url")
            if real:
                return real[0]
        return href

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        url = f"{self.BASE_URL}?query={urllib.parse.quote(query)}"

        for attempt in range(3):
            if results:
                break
            ua = random.choice(self._UA_POOL)
            headers = {
                "User-Agent": ua,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.sogou.com/",
            }
            html = self._http_get(url, headers=headers)
            if not html:
                if attempt < 2:
                    time.sleep(random.uniform(1.0, 2.5))
                continue

            # 主模式：<h3 class="vr-title"><a href="...">标题</a></h3>
            pattern = re.compile(
                r'<h3[^>]*class="[^"]*vr-title[^"]*"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                re.DOTALL | re.IGNORECASE
            )
            # 摘要：star-wiki / txt-info / space-txt 等容器
            snip_pattern = re.compile(
                r'<p[^>]+class="[^"]*(?:star-wiki|txt-info|space-txt)[^"]*"[^>]*>(.*?)</p>',
                re.DOTALL | re.IGNORECASE
            )
            snippets = [_strip_tags(m.group(1)) for m in snip_pattern.finditer(html)]

            fetched_at = datetime.now().isoformat()
            for i, m in enumerate(pattern.finditer(html)):
                if i >= limit:
                    break
                title = _strip_tags(m.group(2)).strip()
                if not title:
                    continue
                results.append(SearchResult(
                    title=title,
                    url=self._resolve_sogou_url(m.group(1)),
                    snippet=snippets[i] if i < len(snippets) else "",
                    source_engine=self.name,
                    rank=i + 1,
                    fetched_at=fetched_at,
                    credibility=self.credibility,
                ))

            if results or attempt >= 2:
                break
            time.sleep(random.uniform(1.0, 2.5))

        return results


class GoogleHTML(SearchEngineBase):
    """Google SERP HTML 解析（最易反爬，仅作 fallback）。"""
    name = "google_html"
    credibility = 6

    BASE_URL = "https://www.google.com/search"

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        url = f"{self.BASE_URL}?q={urllib.parse.quote(query)}&num={limit}"
        html = self._http_get(url, headers={"Accept-Language": "en-US,en;q=0.9"})
        if not html:
            return results
        # Google 结果解析复杂，先用简化版本（可能不准确）
        pattern = re.compile(
            r'<a[^>]+href="([^"]+)"[^>]*>\s*<h3[^>]*>(.*?)</h3>',
            re.DOTALL | re.IGNORECASE
        )
        fetched_at = datetime.now().isoformat()
        for i, m in enumerate(pattern.finditer(html)):
            if i >= limit:
                break
            url_m = m.group(1)
            if url_m.startswith("/url?q="):
                url_m = urllib.parse.unquote(url_m[7:].split("&")[0])
            elif not url_m.startswith("http"):
                continue
            results.append(SearchResult(
                title=_strip_tags(m.group(2)),
                url=url_m,
                snippet="",
                source_engine=self.name,
                rank=i + 1,
                fetched_at=fetched_at,
                credibility=self.credibility,
            ))
        return results


# ============== SearXNG ==============

class SearXNGSearch(SearchEngineBase):
    """SearXNG 元搜索 — 自动健康检查 + 故障转移。"""
    name = "searxng"
    credibility = 6

    DEFAULT_INSTANCES = [
        "https://searx.be",
        "https://search.disroot.org",
        "https://searx.tiekoetter.com",
        "https://search.sapti.me",
        "https://searx.work",
    ]

    # 类级别健康缓存
    _healthy_instance: Optional[str] = None
    _last_health_check: float = 0.0
    _health_check_ttl: float = 300.0  # 5 分钟

    def __init__(self, timeout: int = 8, instance: Optional[str] = None):
        super().__init__(timeout)
        self.instance = instance or self._get_healthy_instance()

    @classmethod
    def _get_healthy_instance(cls) -> str:
        """返回可用实例，优先使用缓存。"""
        now = time.time()
        if (cls._healthy_instance and
                now - cls._last_health_check < cls._health_check_ttl):
            return cls._healthy_instance

        # 探测所有实例
        for inst in cls.DEFAULT_INSTANCES:
            try:
                req = urllib.request.Request(
                    f"{inst}/search?q=test&format=json",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; cn-financial-scraper/4.5)"},
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.getcode() == 200:
                        cls._healthy_instance = inst
                        cls._last_health_check = now
                        return inst
            except Exception:
                continue

        # 全部失败，用第一个默认
        return cls.DEFAULT_INSTANCES[0]

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        # 尝试所有实例
        instances_to_try = [self.instance] + [
            i for i in self.DEFAULT_INSTANCES if i != self.instance
        ]

        for inst in instances_to_try:
            if results:
                break
            url = f"{inst}/search?q={urllib.parse.quote(query)}&format=json&language=zh-CN"
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "Mozilla/5.0 (compatible; cn-financial-scraper/4.5)")
                req.add_header("Accept", "application/json")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                fetched_at = datetime.now().isoformat()
                for i, r in enumerate(data.get("results", [])[:limit]):
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        snippet=r.get("content", ""),
                        source_engine=self.name,
                        rank=i + 1,
                        fetched_at=fetched_at,
                        credibility=self.credibility,
                    ))
                # 成功：更新健康实例
                if results:
                    SearXNGSearch._healthy_instance = inst
                    SearXNGSearch._last_health_check = time.time()
            except Exception:
                continue
        return results


# ============== 官方 Search API ==============

class BingAPISearch(SearchEngineBase):
    """Bing Search API v7（需 BING_API_KEY）。"""
    name = "bing_api"
    credibility = 9
    needs_api_key = True

    ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key: str, timeout: int = 8):
        super().__init__(timeout)
        self.api_key = api_key

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not self.api_key:
            return results
        params = urllib.parse.urlencode({"q": query, "count": limit, "mkt": "zh-CN"})
        url = f"{self.ENDPOINT}?{params}"
        try:
            req = urllib.request.Request(url)
            req.add_header("Ocp-Apim-Subscription-Key", self.api_key)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception:
            return results
        fetched_at = datetime.now().isoformat()
        for i, item in enumerate(data.get("webPages", {}).get("value", [])[:limit]):
            results.append(SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                source_engine=self.name,
                rank=i + 1,
                fetched_at=fetched_at,
                credibility=self.credibility,
            ))
        return results


class GoogleAPISearch(SearchEngineBase):
    """Google Custom Search JSON API（需 GOOGLE_API_KEY + GOOGLE_CSE_ID）。"""
    name = "google_api"
    credibility = 10
    needs_api_key = True

    ENDPOINT = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cse_id: str, timeout: int = 8):
        super().__init__(timeout)
        self.api_key = api_key
        self.cse_id = cse_id

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not (self.api_key and self.cse_id):
            return results
        params = urllib.parse.urlencode({
            "key": self.api_key, "cx": self.cse_id,
            "q": query, "num": min(limit, 10),
        })
        url = f"{self.ENDPOINT}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception:
            return results
        fetched_at = datetime.now().isoformat()
        for i, item in enumerate(data.get("items", [])[:limit]):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source_engine=self.name,
                rank=i + 1,
                fetched_at=fetched_at,
                credibility=self.credibility,
            ))
        return results


# ============== 聚合器 ==============

class MultiEngineSearch:
    """多引擎聚合搜索 + 去重 + 排序。"""

    ENGINE_REGISTRY = {
        "baidu_html": BaiduHTML,
        "sogou_html": SogouHTML,
        "duckduckgo": DuckDuckGoHTML,
        "bing_html": BingHTML,
        "google_html": GoogleHTML,
        "searxng": SearXNGSearch,
        "bing_api": "api",  # 特殊：需 API key
        "google_api": "api",
    }

    def __init__(self, engines: Optional[List[str]] = None,
                 api_keys: Optional[Dict[str, str]] = None,
                 timeout: int = 8,
                 max_workers: int = 3):
        """
        Args:
            engines: 启用的引擎列表（None → 按可用性自动选）
                可选: "duckduckgo", "bing_html", "google_html", "searxng",
                      "bing_api", "google_api"
            api_keys: API key 字典
                {"bing_api": "xxx", "google_api_key": "yyy", "google_cse_id": "zzz"}
            timeout: 单引擎超时（秒）
            max_workers: 并发线程数
        """
        self.api_keys = api_keys or {}
        self.timeout = timeout
        self.max_workers = max_workers
        self.engines: List[SearchEngineBase] = []

        if engines is None:
            engines = self._auto_detect_engines()
        for name in engines:
            engine = self._create_engine(name)
            if engine:
                self.engines.append(engine)

    def _auto_detect_engines(self) -> List[str]:
        """根据 API key 可用性自动选引擎。"""
        # v5.0.0: 国内引擎优先（大陆可达性最优），零依赖
        engines = ["baidu_html", "sogou_html", "duckduckgo"]
        if self.api_keys.get("bing_api"):
            engines.insert(0, "bing_api")
        if self.api_keys.get("google_api_key") and self.api_keys.get("google_cse_id"):
            engines.insert(0, "google_api")
        # SearXNG 作为补充
        engines.append("searxng")
        return engines

    def _create_engine(self, name: str) -> Optional[SearchEngineBase]:
        """根据名称创建引擎实例。"""
        if name == "baidu_html":
            return BaiduHTML(timeout=self.timeout)
        if name == "sogou_html":
            return SogouHTML(timeout=self.timeout)
        if name == "duckduckgo":
            return DuckDuckGoHTML(timeout=self.timeout)
        if name == "bing_html":
            return BingHTML(timeout=self.timeout)
        if name == "google_html":
            return GoogleHTML(timeout=self.timeout)
        if name == "searxng":
            return SearXNGSearch(timeout=self.timeout)
        if name == "bing_api" and self.api_keys.get("bing_api"):
            return BingAPISearch(self.api_keys["bing_api"], timeout=self.timeout)
        if name == "google_api" and self.api_keys.get("google_api_key") \
                and self.api_keys.get("google_cse_id"):
            return GoogleAPISearch(
                self.api_keys["google_api_key"],
                self.api_keys["google_cse_id"],
                timeout=self.timeout,
            )
        return None

    def search(self, query: str,
               engines: Optional[List[str]] = None,
               limit: int = 10,
               dedup: bool = True) -> List[SearchResult]:
        """跨引擎搜索。

        Args:
            query: 关键词
            engines: 临时覆盖启用的引擎
            limit: 每引擎返回条数
            dedup: 是否跨引擎去重

        Returns:
            合并去重后的 SearchResult 列表（按 credibility + rank 排序）
        """
        selected = self.engines
        if engines:
            selected = [e for e in self.engines if e.name in engines]

        all_results: List[SearchResult] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(selected))) as ex:
            futures = {ex.submit(_safe_search, eng, query, limit): eng
                       for eng in selected}
            for fut in as_completed(futures):
                try:
                    results = fut.result()
                    all_results.extend(results)
                except Exception:
                    continue

        if dedup:
            all_results = _dedup_results(all_results)

        # 排序：先按 credibility 降序，再按 rank
        all_results.sort(key=lambda r: (-r.credibility, r.rank))

        # 限制返回条数
        return all_results[:limit * 2]

    def list_engines(self) -> List[Dict[str, Any]]:
        """列出已启用引擎及其状态。"""
        return [{
            "name": e.name,
            "credibility": e.credibility,
            "needs_api_key": e.needs_api_key,
            "configured": bool(e),
        } for e in self.engines]

    def search_and_fetch(self, query: str,
                         engines: Optional[List[str]] = None,
                         limit: int = 5,
                         fetch_content: bool = True,
                         dedup: bool = True) -> List[Dict[str, Any]]:
        """搜索 → 获取 URL 列表 → 逐条爬取详情页内容。

        Args:
            query: 搜索关键词
            engines: 临时覆盖启用的引擎
            limit: 搜索返回条数
            fetch_content: 是否自动爬取详情页文本
            dedup: 是否去重

        Returns:
            结构化结果列表，每项含 {title, url, snippet, source_engine, content}
        """
        results = self.search(query, engines=engines, limit=limit, dedup=dedup)
        output: List[Dict[str, Any]] = []

        for r in results[:limit]:
            item = {
                "title": r.title, "url": r.url, "snippet": r.snippet,
                "source_engine": r.source_engine, "credibility": r.credibility,
                "content": "", "fetch_error": "",
            }
            if fetch_content:
                try:
                    fetched = self._fetch_page_text(r.url)
                    item["content"] = fetched.get("text", "")[:3000]
                    item["fetch_error"] = fetched.get("error", "")
                except Exception:
                    item["fetch_error"] = "fetch failed"
            output.append(item)
        return output

    def _fetch_page_text(self, url: str) -> Dict[str, str]:
        """爬取页面文本（轻量版，只提取文字）。"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; cn-financial-scraper/4.5)",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                try:
                    html = raw.decode(charset, errors="replace")
                except (LookupError, TypeError):
                    html = raw.decode("utf-8", errors="replace")
            # 提取文本：去掉 script/style 标签，保留文本
            html = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', '', html,
                          flags=re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return {"text": text[:3000]}
        except Exception as e:
            return {"text": "", "error": str(e)[:100]}


# ============== 辅助函数 ==============

def _safe_search(engine: SearchEngineBase, query: str,
                 limit: int) -> List[SearchResult]:
    """线程安全的单引擎搜索。"""
    try:
        return engine.search(query, limit=limit)
    except Exception:
        return []


def _dedup_results(results: List[SearchResult]) -> List[SearchResult]:
    """按 URL 标准化去重。"""
    seen: Dict[str, SearchResult] = {}
    for r in results:
        norm = _normalize_url(r.url)
        if not norm:
            continue
        if norm not in seen:
            seen[norm] = r
        else:
            # 保留 credibility 更高的
            if r.credibility > seen[norm].credibility:
                seen[norm] = r
    return list(seen.values())


def _normalize_url(url: str) -> str:
    """URL 标准化（去 utm 等）。"""
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return ""
        # 移除 tracking 参数
        params = urllib.parse.parse_qs(parsed.query)
        for k in list(params.keys()):
            if k.startswith("utm_") or k in ("ref", "source"):
                params.pop(k, None)
        new_query = urllib.parse.urlencode(params, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return url


def _strip_tags(html: str) -> str:
    """简单 HTML 标签剥离。"""
    text = re.sub(r"<[^>]+>", "", html)
    return _unescape_html(text)


def _unescape_html(s: str) -> str:
    """HTML 实体解码。"""
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    s = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)
    s = re.sub(r"&#x([0-9a-fA-F]+);",
               lambda m: chr(int(m.group(1), 16)), s)
    return s


# ============== 便捷函数 ==============

def quick_search(query: str, engines: Optional[List[str]] = None,
                 limit: int = 10) -> List[Dict[str, Any]]:
    """便捷函数：返回字典列表。"""
    api_keys = {
        "bing_api": os.environ.get("BING_API_KEY", ""),
        "google_api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "google_cse_id": os.environ.get("GOOGLE_CSE_ID", ""),
    }
    s = MultiEngineSearch(engines=engines, api_keys=api_keys)
    return [r.to_dict() for r in s.search(query, limit=limit)]


def search_and_fetch(query: str, engines: Optional[List[str]] = None,
                     limit: int = 5, fetch_content: bool = True) -> List[Dict[str, Any]]:
    """便捷函数：搜索 + 爬取详情内容。

    用法:
        results = search_and_fetch("贵州茅台 2026 年报")
        for r in results:
            print(r["title"], r["url"], len(r.get("content", "")))
    """
    api_keys = {
        "bing_api": os.environ.get("BING_API_KEY", ""),
        "google_api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "google_cse_id": os.environ.get("GOOGLE_CSE_ID", ""),
    }
    s = MultiEngineSearch(engines=engines, api_keys=api_keys)
    return s.search_and_fetch(query, limit=limit, fetch_content=fetch_content)