# -*- coding: utf-8 -*-
"""RSS 数据源（rss_feeds.py，v4.9.0 新增）

设计目标：
- RSS 是公开订阅协议，无需登录、无反爬
- 即使主数据源（cls/sina/jisilu/eastmoney）全部被封，RSS 仍能稳定获取内容
- 内置国内主流金融 RSS 源（财经垂直媒体）

调用方式：
    from scripts.rss_feeds import RssFetcher, list_financial_feeds

    feeds = list_financial_feeds(category="media")
    fetcher = RssFetcher()
    items = fetcher.fetch(feeds[0]["url"])
"""
from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


@dataclass
class RssItem:
    """RSS 单条条目标准格式。"""
    title: str
    link: str
    description: str = ""
    content: str = ""
    pub_date: str = ""
    author: str = ""
    categories: List[str] = field(default_factory=list)
    source: str = ""
    guid: str = ""
    fetch_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 内置金融 RSS 源（精选高可用站点）
# ============================================================================


FINANCIAL_RSS_FEEDS = {
    "media": [
        {
            "name": "东方财富资讯",
            "url": "https://rsstohome.eastmoney.com/rss/news/zx.xml",
            "lang": "zh-CN",
            "desc": "东方财富网综合资讯",
        },
        {
            "name": "东方财富股票",
            "url": "https://rsstohome.eastmoney.com/rss/news/stock.xml",
            "lang": "zh-CN",
            "desc": "东方财富股票频道",
        },
        {
            "name": "36氪",
            "url": "https://36kr.com/feed",
            "lang": "zh-CN",
            "desc": "36氪创投与商业资讯",
        },
        {
            "name": "虎嗅",
            "url": "https://www.huxiu.com/rss/0.xml",
            "lang": "zh-CN",
            "desc": "虎嗅商业与科技资讯",
        },
        {
            "name": "网易财经",
            "url": "https://news.163.com/special/00011K6L/rss_newstop.xml",
            "lang": "zh-CN",
            "desc": "网易新闻要闻（含财经）",
        },
    ],
}


def list_financial_feeds(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出可用 RSS 源。

    Args:
        category: 类别筛选（media / None=全部）

    Returns:
        RSS 源信息列表，每项含 name/url/lang/desc。
    """
    if category is None:
        all_feeds = []
        for feeds in FINANCIAL_RSS_FEEDS.values():
            all_feeds.extend(feeds)
        return all_feeds
    return FINANCIAL_RSS_FEEDS.get(category, [])


# ============================================================================
# RSS 解析器
# ============================================================================


def _strip_html(html: str) -> str:
    """简单 HTML 标签剥离（不依赖 bs4，零依赖）。"""
    if not html:
        return ""
    # 移除 CDATA 包裹
    html = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", html, flags=re.DOTALL)
    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", html)
    # 解码 HTML 实体
    text = (text.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", "\"")
                .replace("&apos;", "'")
                .replace("&#39;", "'"))
    return text.strip()


def _parse_date(date_str: str) -> str:
    """规范化日期字符串到 ISO 8601。"""
    if not date_str:
        return ""
    # 常见格式：RFC 822 (RSS 2.0) / ISO 8601 (Atom)
    formats = (
        "%a, %d %b %Y %H:%M:%S %z",       # RFC 822 with tz
        "%a, %d %b %Y %H:%M:%S %Z",       # RFC 822 with name
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",            # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat(timespec="seconds")
        except ValueError:
            continue
    return date_str


def _parse_rss_xml(xml_bytes: bytes, source_name: str = "") -> List[RssItem]:
    """解析 RSS/Atom XML 为 RssItem 列表。"""
    items: List[RssItem] = []
    try:
        # 移除 BOM
        if xml_bytes.startswith(b"\xef\xbb\xbf"):
            xml_bytes = xml_bytes[3:]
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        log.warning(f"RSS XML 解析失败 ({source_name}): {e}")
        return items

    # RSS 2.0
    if root.tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return items
        for item in channel.findall("item"):
            title = _strip_html(item.findtext("title", ""))
            link = (item.findtext("link", "") or "").strip()
            description = _strip_html(item.findtext("description", ""))
            content_encoded = _strip_html(item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", ""))
            content = content_encoded or description
            pub_date = _parse_date(item.findtext("pubDate", ""))
            author = _strip_html(item.findtext("author", "") or
                                 item.findtext("{http://purl.org/dc/elements/1.1/}creator", ""))
            guid = (item.findtext("guid", "") or link).strip()
            categories = [_strip_html(c.text or "")
                          for c in item.findall("category") if c.text]
            items.append(RssItem(
                title=title, link=link, description=description,
                content=content, pub_date=pub_date, author=author,
                categories=categories, source=source_name, guid=guid,
                fetch_time=datetime.now().isoformat(timespec="seconds"),
            ))
    # Atom 1.0
    elif root.tag.endswith("feed"):
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", ns):
            title = _strip_html(entry.findtext("a:title", "", namespaces=ns))
            link_elem = entry.find("a:link", ns)
            link = (link_elem.get("href", "") if link_elem is not None else "")
            summary = _strip_html(entry.findtext("a:summary", "", namespaces=ns))
            content = _strip_html(entry.findtext("a:content", "", namespaces=ns))
            pub = _parse_date(entry.findtext("a:updated", "", namespaces=ns) or
                              entry.findtext("a:published", "", namespaces=ns))
            author = _strip_html(entry.findtext("a:author/a:name", "", namespaces=ns))
            guid = (entry.findtext("a:id", "", namespaces=ns) or link)
            categories = [_strip_html(c.get("term", ""))
                          for c in entry.findall("a:category", ns)]
            items.append(RssItem(
                title=title, link=link, description=summary,
                content=content, pub_date=pub, author=author,
                categories=categories, source=source_name, guid=guid,
                fetch_time=datetime.now().isoformat(timespec="seconds"),
            ))
    else:
        log.warning(f"未知 RSS 格式: root={root.tag}")

    return items


# ============================================================================
# RSS 抓取器
# ============================================================================


class RssFetcher:
    """RSS 抓取器（零依赖，仅用 stdlib + http_utils）。"""

    def __init__(self, timeout: int = 20, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch(self, feed: Dict[str, Any]) -> List[RssItem]:
        """抓取单个 RSS 源。

        Args:
            feed: {"name": str, "url": str, ...}

        Returns:
            RssItem 列表；失败返回 []。
        """
        url = feed.get("url", "")
        name = feed.get("name", "")
        if not url:
            log.warning(f"RSS 源无 url: {feed}")
            return []

        # 延迟 import（避免循环依赖）
        try:
            from scripts.http_utils import http_get
        except ImportError:
            from http_utils import http_get

        for attempt in range(self.max_retries + 1):
            try:
                resp = http_get(url, timeout=self.timeout)
                if resp is None:
                    log.warning(f"RSS 抓取失败 ({name}): http 返回 None")
                    continue
                if resp.status_code != 200:
                    log.warning(f"RSS 抓取 {resp.status_code} ({name}): {url}")
                    continue
                items = _parse_rss_xml(resp.content, source_name=name)
                log.info(f"RSS {name}: 成功解析 {len(items)} 条")
                return items
            except Exception as e:
                log.warning(f"RSS 抓取异常 {name} (第{attempt+1}次): {e}")
                if attempt < self.max_retries:
                    time.sleep(1.5 * (attempt + 1))
        return []

    def fetch_many(self, feeds: List[Dict[str, Any]],
                   max_total: int = 100) -> List[RssItem]:
        """批量抓取多个 RSS 源，统一去重。

        Args:
            feeds: 多个 RSS 源配置
            max_total: 最多返回条目数

        Returns:
            去重后的 RssItem 列表（按发布时间倒序）
        """
        all_items: List[RssItem] = []
        seen_guids: set = set()
        for feed in feeds:
            items = self.fetch(feed)
            for it in items:
                if it.guid and it.guid in seen_guids:
                    continue
                if it.guid:
                    seen_guids.add(it.guid)
                all_items.append(it)
                if len(all_items) >= max_total:
                    break
            if len(all_items) >= max_total:
                break

        # 按发布时间倒序（无法解析的排最后）
        def _sort_key(it):
            return it.pub_date or ""
        all_items.sort(key=_sort_key, reverse=True)
        return all_items[:max_total]


# ============================================================================
# CLI 测试入口
# ============================================================================


if __name__ == "__main__":
    import json
    import sys

    category = sys.argv[1] if len(sys.argv) > 1 else "authoritative"
    feeds = list_financial_feeds(category=category)
    print(f"📡 {category} RSS 源:")
    for f in feeds:
        print(f"  - {f['name']}: {f['url']}")

    if feeds:
        print(f"\n正在抓取 {feeds[0]['name']}...")
        fetcher = RssFetcher()
        items = fetcher.fetch(feeds[0])
        print(f"\n获取到 {len(items)} 条:")
        for it in items[:5]:
            print(f"  - [{it.pub_date[:10]}] {it.title[:60]}")
            print(f"    {it.link}")