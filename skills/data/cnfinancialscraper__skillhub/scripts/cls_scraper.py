# -*- coding: utf-8 -*-
"""
财联社数据爬虫 v1.0

提供 7x24 小时电报快讯、热门文章等。
数据源: cls.cn（中国最重要的金融实时快讯平台）

注意：
- 财联社有反爬机制，需设置合理的 User-Agent 和 Referer
- 建议请求频率不超过 2 次/秒（由 http_utils 自动限流）
"""

import json
import logging
from typing import Dict, List, Optional

try:
    from .http_utils import http_get, http_get_json, http_post
except ImportError:
    from http_utils import http_get, http_get_json, http_post

log = logging.getLogger(__name__)

CLS_BASE = "https://www.cls.cn"
CLS_API = "https://www.cls.cn/api"

DEFAULT_CLS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.cls.cn/telegraph",
    "Content-Type": "application/json",
}


def get_telegraph(limit: int = 20) -> List[Dict]:
    """获取财联社 7x24 电报快讯

    Args:
        limit: 返回条数，默认20，最多50

    Returns:
        [{id, title, content, ctime, level, type, ...}, ...]
        level: "A"(重要) / "B"(中等) / "C"(一般)
    """
    try:
        url = f"{CLS_API}/sw"
        payload = {
            "app": "CailianpressWeb",
            "os": "web",
            "sv": "8.4.6",
            "type": "telegram",
        }
        resp = http_post(url, json_body=payload, headers=DEFAULT_CLS_HEADERS, timeout=20)
        if resp is None:
            log.warning("财联社电报请求失败")
            return []

        data = resp.json()
        items = data.get("data", {}).get("roll_data", []) if isinstance(data, dict) else []

        results = []
        for item in items[:limit]:
            results.append({
                "id": item.get("id", ""),
                "title": item.get("title", "") or item.get("brief", ""),
                "content": item.get("content", "") or item.get("brief", ""),
                "ctime": item.get("ctime", 0),
                "level": item.get("level", "C"),
                "type": item.get("type", ""),
                "url": f"{CLS_BASE}/telegraph/detail/{item.get('id', '')}" if item.get("id") else "",
            })
        return results
    except Exception as e:
        log.error(f"获取财联社电报失败: {e}")
        # v5.0.0: 降级到 akshare 经济新闻（接口被封时不至于无数据）
        try:
            from scripts.akshare_fallback import fallback_akshare
            return fallback_akshare(
                "news_economic_cls", {"limit": limit},
                {"title": ["标题", "title"], "url": ["链接", "url", "link"],
                 "publish_time": ["发布时间", "time", "ctime"],
                 "content": ["摘要", "content"]},
            )
        except Exception:
            return []


def get_hot_articles(limit: int = 10) -> List[Dict]:
    """获取财联社热门文章

    Args:
        limit: 返回条数，默认10

    Returns:
        [{id, title, summary, url, publish_time, source}, ...]
    """
    try:
        url = f"{CLS_API}/sw"
        payload = {
            "app": "CailianpressWeb",
            "os": "web",
            "sv": "8.4.6",
            "type": "recommend",
        }
        resp = http_post(url, json_body=payload, headers=DEFAULT_CLS_HEADERS, timeout=20)
        if resp is None:
            return []

        data = resp.json()
        items = data.get("data", {}).get("roll_data", []) if isinstance(data, dict) else []

        results = []
        for item in items[:limit]:
            results.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "summary": item.get("brief", ""),
                "url": f"{CLS_BASE}/detail/{item.get('id', '')}" if item.get("id") else "",
                "publish_time": item.get("ctime", 0),
                "source": "财联社",
            })
        return results
    except Exception as e:
        log.error(f"获取财联社文章失败: {e}")
        # v5.0.0: 降级到 akshare 经济新闻
        try:
            from scripts.akshare_fallback import fallback_akshare
            return fallback_akshare(
                "news_economic_cls", {"limit": limit},
                {"title": ["标题", "title"], "url": ["链接", "url", "link"],
                 "publish_time": ["发布时间", "time", "ctime"],
                 "summary": ["摘要", "content"]},
            )
        except Exception:
            return []


def search_articles(keyword: str, limit: int = 10) -> List[Dict]:
    """按关键词搜索财联社文章

    Args:
        keyword: 搜索关键词，如 "降息"、"茅台"
        limit: 返回条数

    Returns:
        [{title, url, publish_time}, ...]
    """
    try:
        url = f"{CLS_API}/search"
        payload = {
            "app": "CailianpressWeb",
            "os": "web",
            "sv": "8.4.6",
            "keyword": keyword,
            "type": "article",
        }
        resp = http_post(url, json_body=payload, headers=DEFAULT_CLS_HEADERS, timeout=20)
        if resp is None:
            return []

        data = resp.json()
        items = data.get("data", {}).get("list", []) if isinstance(data, dict) else []

        results = []
        for item in items[:limit]:
            results.append({
                "id": item.get("article_id", item.get("id", "")),
                "title": item.get("title", ""),
                "url": f"{CLS_BASE}/detail/{item.get('article_id', '')}" if item.get("article_id") else "",
                "publish_time": item.get("time", ""),
                "source": "财联社",
            })
        return results
    except Exception as e:
        log.error(f"搜索财联社文章失败: {e}")
        # v5.0.0: akshare 无财联社搜索接口，降级到经济新闻近似
        try:
            from scripts.akshare_fallback import fallback_akshare
            return fallback_akshare(
                "news_economic_cls", {"limit": limit},
                {"title": ["标题", "title"], "url": ["链接", "url", "link"],
                 "publish_time": ["发布时间", "time", "ctime"]},
            )
        except Exception:
            return []


# ── CLI 测试入口 ──────────────────────────────────────

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "telegraph"

    if cmd == "telegraph":
        print("📡 财联社 7x24 电报快讯:\n")
        items = get_telegraph(limit=10)
        for i, item in enumerate(items, 1):
            level_icon = {"A": "🔴", "B": "🟡", "C": "🟢"}.get(item.get("level", "C"), "⚪")
            print(f"  {i}. {level_icon} {item.get('title', '')[:80]}")
    elif cmd == "search":
        keyword = sys.argv[2] if len(sys.argv) > 2 else "降息"
        print(f"🔍 搜索: {keyword}\n")
        articles = search_articles(keyword, limit=10)
        for i, a in enumerate(articles, 1):
            print(f"  {i}. {a.get('title', '')}")
    else:
        print("用法: python cls_scraper.py [telegraph|search <关键词>]")
