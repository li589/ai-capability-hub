#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛情绪聚合 (v6.1.0)
=====================
统一入口聚合股吧/雪球论坛情绪，输出标准化结构：

  - A股 → 东方财富股吧(阅读/评论热度+情绪) + 雪球
  - 港股 → 东财港股吧 + 雪球
  - 美股 → 雪球美股频道(带 cookie 探测，失败优雅降级)

雪球反爬：先 GET https://xueqiu.com 拿 xq_a_token cookie 再请求接口；
实测未登录拿不到 token，search.json 返回 400016，按约定优雅降级。

股吧：新版页面 https://guba.eastmoney.com/list,{code}_{page}.html 内嵌
"article_list" JSON（含阅读/评论数），直接解析（旧 list/code,2_p.html 已 404）。

用法:
    from stock_researcher.sentiment.forum_sentiment import analyze_forum_sentiment
    r = analyze_forum_sentiment("600519", market="cn")
    print(r["heat"], r["bullish_ratio"], r["sentiment_score"], r["crowd_extreme"])
"""

import json
import re
import ssl
import time
import urllib.request
import urllib.parse
import http.cookiejar
from datetime import datetime
from typing import Dict, List, Optional

CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 请求间隔（东财限流激进，必须≥1.5s）
REQUEST_INTERVAL = 1.6

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

_last_request_ts = [0.0]


def _throttle():
    """保证请求间隔≥REQUEST_INTERVAL"""
    wait = REQUEST_INTERVAL - (time.time() - _last_request_ts[0])
    if wait > 0:
        time.sleep(wait)
    _last_request_ts[0] = time.time()


def _open_with_retry(opener, url, headers=None, timeout=10, retries=3):
    """
    指数退避重试 (1/2/4s，≤3次)。全部失败返回 None，绝不抛异常。
    """
    delay = 1.0
    for attempt in range(retries):
        try:
            _throttle()
            req = urllib.request.Request(url, headers=headers or {"User-Agent": CHROME_UA})
            if opener is not None:
                resp = opener.open(req, timeout=timeout)
            else:
                resp = urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx)
            with resp:
                return resp.read()
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
    return None


# ═══════════════════════════════════════════════════════════════
# 东方财富股吧（新版页面内嵌 article_list JSON）
# ═══════════════════════════════════════════════════════════════

def _extract_article_list(html: str) -> List[Dict]:
    """从股吧页面 HTML 中提取 "article_list" JSON 数组（字符串感知的括号匹配）"""
    idx = html.find('"article_list"')
    if idx < 0:
        return []
    start = html.find('[', idx)
    if start < 0:
        return []

    depth = 0
    in_str = False
    escape = False
    for i in range(start, min(len(html), start + 2_000_000)):
        c = html[i]
        if in_str:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(html[start:i + 1])
                    return data if isinstance(data, list) else []
                except Exception:
                    return []
    return []


def _parse_listitem_html(html: str) -> List[Dict]:
    """解析经典版股吧列表（<tr class="listitem"> 服务端渲染）"""
    posts = []
    pattern = re.compile(
        r'<tr class="listitem">.*?'
        r'<div class="read">(\d+)</div>.*?'
        r'<div class="reply">(\d+)</div>.*?'
        r'<div class="title"><a [^>]*>(.*?)</a>.*?'
        r'<div class="author"><a [^>]*>(.*?)</a>.*?'
        r'<div class="update">([^<]*)</div>',
        re.DOTALL,
    )
    for read, reply, title, author, update in pattern.findall(html):
        title = re.sub(r"<[^>]+>", "", title).strip()
        if not title:
            continue
        posts.append({
            "post_title": title,
            "user_nickname": re.sub(r"<[^>]+>", "", author).strip(),
            "post_comment_count": int(reply),
            "post_click_count": int(read),
            "post_publish_time": update.strip(),
        })
    return posts


def _extract_guba_items(html: str) -> List[Dict]:
    """股吧页面双模板解析：优先内嵌 article_list JSON，回退 listitem HTML"""
    items = _extract_article_list(html)
    if items:
        return items
    return _parse_listitem_html(html)


def _guba_bar_code(code: str, market: str) -> str:
    """股吧代码：A股 600519，港股 hk00700"""
    code = str(code).strip()
    if market == "hk":
        return "hk" + code.zfill(5)
    return code.zfill(6)


def fetch_guba_posts(code: str, market: str = "cn", pages: int = 2) -> List[Dict]:
    """
    抓取东方财富股吧帖子（含阅读/评论数）。

    Returns:
        List[Dict]: platform/title/author/reply_count/read_count/created_at/sentiment_score/type
    """
    posts: List[Dict] = []
    try:
        from stock_researcher.data.sentiment_forum_crawler import SentimentForumCrawler
        crawler = SentimentForumCrawler()
    except Exception:
        crawler = None

    bar = _guba_bar_code(code, market)
    headers = {
        "User-Agent": CHROME_UA,
        "Referer": "https://guba.eastmoney.com/",
    }

    for page in range(1, max(1, pages) + 1):
        url = (f"https://guba.eastmoney.com/list,{bar}.html" if page == 1
               else f"https://guba.eastmoney.com/list,{bar}_{page}.html")
        raw = _open_with_retry(None, url, headers=headers)
        if not raw:
            continue
        html = raw.decode("utf-8", errors="replace")
        for item in _extract_guba_items(html):
            if not isinstance(item, dict):
                continue
            title = str(item.get("post_title", "") or "").strip()
            if not title:
                continue
            posts.append({
                "code": bar,
                "platform": "eastmoney_guba",
                "title": title[:100],
                "author": str(item.get("user_nickname", "") or ""),
                "reply_count": int(item.get("post_comment_count", 0) or 0),
                "read_count": int(item.get("post_click_count", 0) or 0),
                "created_at": str(item.get("post_publish_time", "") or ""),
                "sentiment_score": crawler._calc_sentiment(title) if crawler else 0,
                "type": crawler._classify_post(title) if crawler else "其他",
            })
    return posts


# ═══════════════════════════════════════════════════════════════
# 雪球（带 cookie 探测，失败优雅降级）
# ═══════════════════════════════════════════════════════════════

def _xueqiu_opener() -> Optional[urllib.request.OpenerDirector]:
    """先 GET xueqiu.com 拿 xq_a_token cookie；失败返回 None"""
    try:
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=_ssl_ctx),
        )
        _throttle()
        req = urllib.request.Request(
            "https://xueqiu.com",
            headers={"User-Agent": CHROME_UA, "Accept": "text/html"},
        )
        with opener.open(req, timeout=10):
            pass
        return opener
    except Exception:
        return None


def _xueqiu_symbol(code: str, market: str) -> str:
    """转换为雪球代码格式"""
    code = str(code).strip().upper()
    if market == "hk":
        return "HK" + code.zfill(5)
    if market == "us":
        return code  # 美股直接用 ticker，如 AAPL
    code = code.zfill(6)
    return ("SH" if code.startswith(("6", "9")) else "SZ") + code


def fetch_xueqiu_discussions(symbol: str, count: int = 10) -> List[Dict]:
    """
    雪球个股讨论（带 cookie 探测，失败优雅降级返回 []）。

    Args:
        symbol: 雪球代码，如 SH600519 / HK00700 / AAPL
    """
    posts: List[Dict] = []
    try:
        opener = _xueqiu_opener()
        if opener is None:
            return []

        url = (f"https://xueqiu.com/statuses/search.json?count={count}"
               f"&comment=0&symbol={urllib.parse.quote(symbol)}")
        headers = {
            "User-Agent": CHROME_UA,
            "Referer": f"https://xueqiu.com/S/{symbol}",
            "Accept": "application/json",
        }
        raw = _open_with_retry(opener, url, headers=headers)
        if not raw:
            return []

        data = json.loads(raw.decode("utf-8", errors="replace"))
        items = data.get("list", []) or []
        if not isinstance(items, list):
            return []

        try:
            from stock_researcher.data.sentiment_forum_crawler import SentimentForumCrawler
            crawler = SentimentForumCrawler()
        except Exception:
            crawler = None

        for item in items:
            if not isinstance(item, dict):
                continue
            content = re.sub(r"<[^>]+>", "", str(item.get("text", "") or ""))
            title = re.sub(r"<[^>]+>", "", str(item.get("title", "") or ""))
            created_at = item.get("created_at", 0)
            posts.append({
                "code": symbol,
                "platform": "xueqiu",
                "title": (title or content)[:100],
                "author": (item.get("user") or {}).get("screen_name", ""),
                "reply_count": item.get("reply_count", 0) or 0,
                "like_count": item.get("like_count", 0) or 0,
                "read_count": item.get("view_count", 0) or 0,
                "created_at": (datetime.fromtimestamp(created_at / 1000).isoformat()
                               if created_at else ""),
                "sentiment_score": crawler._calc_sentiment(title + " " + content) if crawler else 0,
                "type": crawler._classify_post(content) if crawler else "其他",
            })
    except Exception:
        return []
    return posts


# ═══════════════════════════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════════════════════════

def _calc_heat(posts: List[Dict]) -> int:
    """热度 0-100：由帖子数、评论数、阅读数综合估算"""
    if not posts:
        return 0
    n = len(posts)
    replies = sum(int(p.get("reply_count", 0) or 0) for p in posts)
    reads = sum(int(p.get("read_count", 0) or 0) for p in posts)
    # 经验映射：帖子数为主，评论/阅读封顶加成
    heat = min(70.0, n * 1.0) + min(18.0, replies * 0.03) + min(12.0, reads / 50000.0)
    return int(max(0, min(100, heat)))


def analyze_forum_sentiment(code: str, market: str = "cn") -> Dict:
    """
    论坛情绪统一入口。

    Returns:
        {
            "available": bool,
            "heat": int,               # 0-100 热度
            "bullish_ratio": float,    # 看多占比 %
            "sentiment_score": float,  # -100 ~ +100
            "hot_posts": [标题x5],
            "crowd_extreme": bool,     # 情绪极端（≥85%或≤15%），反向风险信号
            "sources": list,
            "note": str,               # 中文说明
        }
    """
    result = {
        "available": False, "heat": 0, "bullish_ratio": 50.0,
        "sentiment_score": 0.0, "hot_posts": [], "crowd_extreme": False,
        "sources": [], "note": "",
    }

    try:
        posts: List[Dict] = []

        # ── 东方财富股吧（A股/港股；美股无股吧频道）──
        if market in ("cn", "hk"):
            try:
                guba_posts = fetch_guba_posts(code, market=market, pages=2)
                if guba_posts:
                    result["sources"].append("eastmoney_guba")
                    posts.extend(guba_posts)
            except Exception:
                pass

        # ── 雪球（三市场通用，带 cookie 探测，失败降级）──
        try:
            xq_posts = fetch_xueqiu_discussions(_xueqiu_symbol(code, market), count=10)
            if xq_posts:
                result["sources"].append("xueqiu")
                posts.extend(xq_posts)
        except Exception:
            pass

        if not posts:
            tried = "股吧+雪球" if market in ("cn", "hk") else "雪球"
            result["note"] = f"论坛数据不可用（{tried}均未取到帖子，已优雅降级）"
            return result

        # ── 聚合情绪（复用 crawler 的打分逻辑）──
        try:
            from stock_researcher.data.sentiment_forum_crawler import SentimentForumCrawler
            sentiment = SentimentForumCrawler().analyze_sentiment(posts)
        except Exception:
            # 兜底：直接按单帖 sentiment_score 聚合
            scores = [p.get("sentiment_score", 0) for p in posts]
            pos = sum(1 for s in scores if s >= 1)
            sentiment = {
                "bullish_ratio": pos / len(scores) * 100 if scores else 50,
                "sentiment_score": sum(scores) / len(scores) if scores else 0,
                "sentiment_label": "中性",
            }

        bullish = sentiment.get("bullish_ratio", 50.0)
        avg = sentiment.get("sentiment_score", 0.0)  # -3 ~ +3

        result["bullish_ratio"] = round(float(bullish), 1)
        result["sentiment_score"] = round(max(-100.0, min(100.0, float(avg) * 33.0)), 1)
        result["heat"] = _calc_heat(posts)
        result["crowd_extreme"] = bool(bullish >= 85 or bullish <= 15)
        result["available"] = True

        # 热门帖（按评论数排序取前5标题）
        hot = sorted(posts, key=lambda p: int(p.get("reply_count", 0) or 0), reverse=True)
        result["hot_posts"] = [p.get("title", "") for p in hot[:5] if p.get("title")]

        label = sentiment.get("sentiment_label", "中性")
        src = "+".join(result["sources"])
        result["note"] = (f"{src}共{len(posts)}帖，情绪{label}，看多占比{bullish:.0f}%"
                          + ("，情绪极端，警惕反向风险" if result["crowd_extreme"] else ""))
        if "xueqiu" not in result["sources"]:
            result["note"] += "（雪球反爬未通过，仅股吧数据）"

    except Exception as e:
        result["note"] = f"论坛情绪分析失败: {e}"

    return result


def main():
    """简单自测"""
    r = analyze_forum_sentiment("600519", market="cn")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
