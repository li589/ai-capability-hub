# -*- coding: utf-8 -*-
"""
华尔街见闻内容爬虫模块

数据源: wallstreetcn.com
提供实时快讯、分类文章、搜索等功能。

主要函数:
    - get_live_news(limit=20)        — 获取实时快讯
    - get_articles(category, limit)  — 获取分类文章
    - get_article_detail(article_id) — 获取文章详情
    - search_articles(keyword)       — 搜索文章

API:
    - 快讯: https://api-one.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit={limit}
    - 文章列表: https://api-one.wallstreetcn.com/apiv1/content/articles/pc-list?channel=global-channel&limit={limit}
    - 文章详情: https://api-one.wallstreetcn.com/apiv1/content/articles/{article_id}
    - 搜索: https://api-one.wallstreetcn.com/apiv1/content/articles/search
"""

import logging
from typing import Optional, Dict, Any, List

from .http_utils import http_get_json, http_get, rate_limit

log = logging.getLogger(__name__)

# ==================== 常量 ====================

WALLSTREETCN_BASE_API = "https://api-one.wallstreetcn.com/apiv1"

# 快讯频道
LIVE_CHANNELS = {
    "global": "global-channel",       # 全球
    "china": "china-channel",         # 中国
    "us": "us-channel",               # 美国
    "a-stock": "a-stock-channel",     # A股
    "hk": "hk-channel",               # 港股
}

# 文章分类
ARTICLE_CATEGORIES = {
    "global": "global-channel",       # 全球
    "china": "china-channel",         # 中国
    "us": "us-channel",               # 美国
    "a-stock": "a-stock-channel",     # A股
    "hk": "hk-channel",               # 港股
    "forex": "forex-channel",         # 外汇
    "commodity": "commodity-channel", # 商品
    "bond": "bond-channel",           # 债券
    "realestate": "realestate-channel",  # 房地产
    "tech": "tech-channel",           # 科技
}

# 请求头
WSCN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://wallstreetcn.com",
    "Referer": "https://wallstreetcn.com/",
}

# ==================== 安全类型转换 ====================


def _safe_int(val, default=0):
    """安全转换为整数"""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    """安全转换为字符串"""
    if val is None:
        return default
    return str(val)


# ==================== 实时快讯 ====================


def _akshare_news_fallback(limit: int) -> Dict[str, Any]:
    """v5.0.0: 华尔街见闻 API 被封时降级到 akshare 经济新闻（尽力而为）。"""
    try:
        from scripts.akshare_fallback import fallback_akshare
        records = fallback_akshare(
            "news_economic_baidu", {"symbol": "全部"},
            {"title": ["新闻标题", "标题"], "content_text": ["新闻内容", "内容"],
             "display_time": ["发布时间"], "uri": ["新闻链接", "链接", "url"]},
        )[:limit]
        return {"items": records, "next_cursor": None, "total": len(records)}
    except Exception:
        return {"items": [], "next_cursor": None, "total": 0}


def get_live_news(channel: str = "global",
                  limit: int = 20,
                  cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    获取华尔街见闻实时快讯。

    Args:
        channel: 频道名称，可选值:
            - "global"  : 全球（默认）
            - "china"   : 中国
            - "us"      : 美国
            - "a-stock" : A股
            - "hk"      : 港股
        limit: 返回条数（默认 20，最大 100）
        cursor: 翻页游标（首次请求不传，后续从返回数据中获取）

    Returns:
        快讯数据字典，包含:
        - items: 快讯列表，每项含 id, title, content_text, display_time 等
        - next_cursor: 下一页游标（用于翻页）
        - total: 总数
        失败返回空列表
    """
    channel_code = LIVE_CHANNELS.get(channel, LIVE_CHANNELS["global"])
    url = f"{WALLSTREETCN_BASE_API}/content/lives"

    params = {
        "channel": channel_code,
        "limit": min(limit, 100),
    }
    if cursor is not None:
        params["cursor"] = cursor

    rate_limit(url=WALLSTREETCN_BASE_API)

    log.info(f"正在获取华尔街见闻快讯: channel={channel}, limit={limit}")
    data = http_get_json(url, headers=WSCN_HEADERS, params=params)

    if data is None:
        log.error("华尔街见闻快讯请求失败")
        return _akshare_news_fallback(limit)

    # 解析快讯列表
    raw_items = data.get("data", {}).get("items", [])
    if not raw_items:
        # 兼容不同返回格式
        raw_items = data.get("items", [])

    items = []
    for item in raw_items:
        news = {
            "id": _safe_int(item.get("id", 0)),
            "title": _safe_str(item.get("title", "")),
            "content_text": _safe_str(item.get("content_text", "")),
            "content": _safe_str(item.get("content", "")),
            "display_time": _safe_str(item.get("display_time", "")),
            "created_at": _safe_str(item.get("created_at", "")),
            "uri": _safe_str(item.get("uri", "")),
            "is_pushed": item.get("is_pushed", False),
            "tags": item.get("tags", []),
            "related_stocks": item.get("related_stocks", []),
            "channel": channel,
        }
        items.append(news)

    next_cursor = data.get("data", {}).get("next_cursor")
    total = _safe_int(data.get("data", {}).get("total", 0))

    log.info(f"成功获取 {len(items)} 条快讯")
    return {
        "items": items,
        "next_cursor": next_cursor,
        "total": total,
    }


def get_live_news_text(channel: str = "global",
                       limit: int = 20) -> List[str]:
    """
    获取实时快讯纯文本列表（简化版，仅返回内容文本）。

    Args:
        channel: 频道名称
        limit: 返回条数

    Returns:
        快讯文本列表，每条为 "时间: 内容" 格式
    """
    result = get_live_news(channel=channel, limit=limit)
    items = result.get("items", [])

    texts = []
    for item in items:
        time_str = item.get("display_time", "") or item.get("created_at", "")
        content = item.get("content_text", "") or item.get("title", "")
        if content:
            texts.append(f"[{time_str}] {content}")

    return texts


# ==================== 文章列表 ====================


def get_articles(category: str = "global",
                 limit: int = 10,
                 cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    获取华尔街见闻分类文章列表。

    Args:
        category: 文章分类，可选值:
            - "global"      : 全球
            - "china"       : 中国
            - "us"          : 美国
            - "a-stock"     : A股
            - "hk"          : 港股
            - "forex"       : 外汇
            - "commodity"   : 商品
            - "bond"        : 债券
            - "realestate"  : 房地产
            - "tech"        : 科技
        limit: 返回条数（默认 10，最大 50）
        cursor: 翻页游标

    Returns:
        文章数据字典，包含:
        - items: 文章列表
        - next_cursor: 下一页游标
        - total: 总数
        失败返回空字典
    """
    channel_code = ARTICLE_CATEGORIES.get(category, ARTICLE_CATEGORIES["global"])
    url = f"{WALLSTREETCN_BASE_API}/content/articles/pc-list"

    params = {
        "channel": channel_code,
        "limit": min(limit, 50),
    }
    if cursor is not None:
        params["cursor"] = cursor

    rate_limit(url=WALLSTREETCN_BASE_API)

    log.info(f"正在获取华尔街见闻文章: category={category}, limit={limit}")
    data = http_get_json(url, headers=WSCN_HEADERS, params=params)

    if data is None:
        log.error("华尔街见闻文章请求失败")
        return _akshare_news_fallback(limit)

    raw_items = data.get("data", {}).get("items", [])
    if not raw_items:
        raw_items = data.get("items", [])

    items = []
    for item in raw_items:
        article = {
            "id": _safe_int(item.get("id", 0)),
            "title": _safe_str(item.get("title", "")),
            "content_text": _safe_str(item.get("content_text", "")),
            "content_short": _safe_str(item.get("content_short", "")),
            "display_time": _safe_str(item.get("display_time", "")),
            "created_at": _safe_str(item.get("created_at", "")),
            "updated_at": _safe_str(item.get("updated_at", "")),
            "uri": _safe_str(item.get("uri", "")),
            "author": _safe_str(
                item.get("author", {}).get("display_name", "")
                if isinstance(item.get("author"), dict) else ""
            ),
            "tags": item.get("tags", []),
            "channels": item.get("channels", []),
            "related_stocks": item.get("related_stocks", []),
            "is_featured": item.get("is_featured", False),
            "content_type": _safe_str(item.get("content_type", "article")),
            "category": category,
        }
        items.append(article)

    next_cursor = data.get("data", {}).get("next_cursor")
    total = _safe_int(data.get("data", {}).get("total", 0))

    log.info(f"成功获取 {len(items)} 篇文章")
    return {
        "items": items,
        "next_cursor": next_cursor,
        "total": total,
    }


# ==================== 文章详情 ====================


def get_article_detail(article_id: int) -> Optional[Dict[str, Any]]:
    """
    获取华尔街见闻文章详情（含完整正文）。

    Args:
        article_id: 文章 ID

    Returns:
        文章详情字典，包含完整 content 字段，失败返回 None
    """
    url = f"{WALLSTREETCN_BASE_API}/content/articles/{article_id}"
    rate_limit(url=WALLSTREETCN_BASE_API)

    log.info(f"正在获取文章详情: id={article_id}")
    data = http_get_json(url, headers=WSCN_HEADERS)

    if data is None:
        log.error(f"文章 {article_id} 详情请求失败")
        return None

    article_data = data.get("data", data)
    if not article_data:
        return None

    detail = {
        "id": _safe_int(article_data.get("id", article_id)),
        "title": _safe_str(article_data.get("title", "")),
        "content": _safe_str(article_data.get("content", "")),
        "content_text": _safe_str(article_data.get("content_text", "")),
        "display_time": _safe_str(article_data.get("display_time", "")),
        "created_at": _safe_str(article_data.get("created_at", "")),
        "updated_at": _safe_str(article_data.get("updated_at", "")),
        "uri": _safe_str(article_data.get("uri", "")),
        "author": _safe_str(
            article_data.get("author", {}).get("display_name", "")
            if isinstance(article_data.get("author"), dict) else ""
        ),
        "source": _safe_str(article_data.get("source", "")),
        "tags": article_data.get("tags", []),
        "related_stocks": article_data.get("related_stocks", []),
        "related_articles": article_data.get("related_articles", []),
        "content_type": _safe_str(article_data.get("content_type", "article")),
    }

    log.info(f"成功获取文章详情: {detail['title'][:40]}")
    return detail


# ==================== 搜索 ====================


def search_articles(keyword: str,
                    limit: int = 20,
                    cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    搜索华尔街见闻文章。

    Args:
        keyword: 搜索关键词
        limit: 返回条数（默认 20）
        cursor: 翻页游标

    Returns:
        搜索结果字典，结构与 get_articles 类似
    """
    url = f"{WALLSTREETCN_BASE_API}/content/articles/search"
    params = {
        "query": keyword,
        "limit": min(limit, 50),
    }
    if cursor is not None:
        params["cursor"] = cursor

    rate_limit(url=WALLSTREETCN_BASE_API)

    log.info(f"正在搜索华尔街见闻: keyword={keyword}, limit={limit}")
    data = http_get_json(url, headers=WSCN_HEADERS, params=params)

    if data is None:
        log.error(f"华尔街见闻搜索请求失败: {keyword}")
        return {"items": [], "next_cursor": None, "total": 0}

    raw_items = data.get("data", {}).get("items", [])
    items = []
    for item in raw_items:
        article = {
            "id": _safe_int(item.get("id", 0)),
            "title": _safe_str(item.get("title", "")),
            "content_text": _safe_str(item.get("content_text", "")),
            "content_short": _safe_str(item.get("content_short", "")),
            "display_time": _safe_str(item.get("display_time", "")),
            "created_at": _safe_str(item.get("created_at", "")),
            "uri": _safe_str(item.get("uri", "")),
            "author": _safe_str(
                item.get("author", {}).get("display_name", "")
                if isinstance(item.get("author"), dict) else ""
            ),
            "tags": item.get("tags", []),
        }
        items.append(article)

    next_cursor = data.get("data", {}).get("next_cursor")
    total = _safe_int(data.get("data", {}).get("total", 0))

    log.info(f"搜索 '{keyword}' 找到 {total} 条结果")
    return {
        "items": items,
        "next_cursor": next_cursor,
        "total": total,
    }


# ==================== 便捷功能 ====================


def get_market_briefing() -> str:
    """
    获取市场简报：聚合最新快讯和主要文章摘要。

    Returns:
        格式化的市场简报文本
    """
    lines = []
    lines.append("=" * 60)
    lines.append("【华尔街见闻 - 市场简报】")
    lines.append("=" * 60)

    # 最新快讯
    lines.append("\n--- 最新快讯 ---")
    try:
        live_result = get_live_news(channel="global", limit=10)
        for i, item in enumerate(live_result.get("items", [])[:10], 1):
            time_str = item.get("display_time", "") or ""
            content = item.get("content_text", "") or item.get("title", "")
            if content:
                lines.append(f"  {i}. [{time_str}] {content[:80]}")
    except Exception as e:
        log.warning(f"获取快讯失败: {e}")
        lines.append("  (快讯获取失败)")

    # 头条文章
    lines.append("\n--- 全球头条 ---")
    try:
        article_result = get_articles(category="global", limit=5)
        for i, article in enumerate(article_result.get("items", [])[:5], 1):
            title = article.get("title", "")
            time_str = article.get("display_time", "") or ""
            if title:
                lines.append(f"  {i}. [{time_str}] {title[:80]}")
    except Exception as e:
        log.warning(f"获取文章失败: {e}")
        lines.append("  (文章获取失败)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


# ==================== 测试入口 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("华尔街见闻爬虫 - 功能测试")
    print("=" * 60)

    # 测试1: 获取实时快讯
    print("\n[测试1] 获取全球实时快讯（最近10条）...")
    live = get_live_news(channel="global", limit=10)
    items = live.get("items", [])
    print(f"获取到 {len(items)} 条快讯 (共 {live.get('total', '?')} 条)")
    for item in items[:5]:
        print(f"  [{item.get('display_time', '')}] {item.get('content_text', '')[:80]}")

    # 测试2: 获取 A 股频道快讯
    print("\n[测试2] 获取 A 股实时快讯...")
    live_a = get_live_news(channel="a-stock", limit=5)
    for item in live_a.get("items", [])[:3]:
        print(f"  [{item.get('display_time', '')}] {item.get('content_text', '')[:80]}")

    # 测试3: 获取全球频道文章
    print("\n[测试3] 获取全球频道文章（最近5篇）...")
    articles = get_articles(category="global", limit=5)
    for i, art in enumerate(articles.get("items", [])[:5], 1):
        print(f"  {i}. [{art.get('display_time', '')}] {art.get('title', '')[:80]}")

    # 测试4: 获取 A 股频道文章
    print("\n[测试4] 获取 A 股频道文章...")
    articles_a = get_articles(category="a-stock", limit=5)
    for i, art in enumerate(articles_a.get("items", [])[:3], 1):
        print(f"  {i}. [{art.get('display_time', '')}] {art.get('title', '')[:80]}")

    # 测试5: 获取文章详情
    if articles.get("items"):
        test_id = articles["items"][0].get("id")
        if test_id:
            print(f"\n[测试5] 获取文章详情: id={test_id}")
            detail = get_article_detail(test_id)
            if detail:
                print(f"  标题: {detail.get('title', '')[:80]}")
                print(f"  作者: {detail.get('author', '')}")
                print(f"  字数: {len(detail.get('content', ''))}")

    # 测试6: 搜索
    print("\n[测试6] 搜索 '美联储' 相关文章...")
    search_result = search_articles("美联储", limit=5)
    for i, art in enumerate(search_result.get("items", [])[:5], 1):
        print(f"  {i}. [{art.get('display_time', '')}] {art.get('title', '')[:80]}")

    # 测试7: 市场简报
    print("\n[测试7] 生成市场简报...")
    briefing = get_market_briefing()
    print(briefing)

    print("\n" + "=" * 60)
    print("测试完成")
