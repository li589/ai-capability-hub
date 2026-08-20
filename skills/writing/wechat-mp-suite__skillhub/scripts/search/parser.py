#!/usr/bin/env python3
"""
parser.py — HTML 解析层

封装：搜狗搜索结果解析、微信跳转链接提取、微信文章正文提取。

使用 ``beautifulsoup4`` + ``lxml`` 解析 HTML，核心函数：

    parse_articles(html, max_results)
        从搜狗搜索结果页 HTML 中解析文章列表。

    extract_redirect_url(html)
        从 HTML 中提取跳转 URL（meta refresh / location.href / url += 拼接）。

    get_real_url(url, cookie_obj=None, retries=3)
        获取搜狗跳转链接重定向后的真实微信文章 URL。

    fetch_article_content(url, max_length=0)
        从微信文章页面抓取正文内容（#js_content 区域）。

    fetch_articles_content(articles, max_length=0)
        批量抓取多篇文章正文。
"""

import logging
import random
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from fetcher import fetch_url, get_random_user_agent, sleep

logger = logging.getLogger(__name__)

# 中国时区 UTC+8
_CST = timezone(timedelta(hours=8))


# ─── 搜索结果页解析 ──────────────────────────────────────────────────────────


def _format_china_datetime(dt: datetime) -> str:
    """将 datetime 对象格式化为中国时区（UTC+8）的字符串。

    Args:
        dt: 原始 datetime 对象（视为 UTC 或本地时间）。

    Returns:
        形如 '2025-07-06 14:30:00' 的字符串。
    """
    china = dt.astimezone(_CST)
    return china.strftime('%Y-%m-%d %H:%M:%S')


def _parse_relative_time(time_text: str) -> Dict[str, str]:
    """解析相对时间为绝对时间字符串。

    Args:
        time_text: 如 '1天前'、'2小时前'、'2025-07-06'。

    Returns:
        {'datetime': 'YYYY-MM-DD HH:mm:ss', 'date_text': 'XXXX年XX月XX日'}。
        解析失败时 datetime 为空，date_text 为原始文本。
    """
    if not time_text:
        return {'datetime': '', 'date_text': ''}

    now = datetime.now()
    target = now

    day_match = re.search(r'(\d+)天前', time_text)
    hour_match = re.search(r'(\d+)小时前', time_text)
    minute_match = re.search(r'(\d+)分钟前', time_text)

    if day_match:
        target = now - timedelta(days=int(day_match.group(1)))
    elif hour_match:
        target = now - timedelta(hours=int(hour_match.group(1)))
    elif minute_match:
        target = now - timedelta(minutes=int(minute_match.group(1)))
    else:
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', time_text)
        if date_match:
            y, m, d = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
            target = datetime(y, m, d, tzinfo=now.tzinfo)
        else:
            # 纯文本，无法解析
            return {'datetime': '', 'date_text': time_text}

    datetime_str = target.strftime('%Y-%m-%d %H:%M:%S')
    date_text = f'{target.year}年{target.month:02d}月{target.day:02d}日'
    return {'datetime': datetime_str, 'date_text': date_text}


def _parse_single_article(soup: BeautifulSoup, element) -> Optional[Dict[str, Any]]:
    """解析单篇文章条目（内部函数）。

    Args:
        soup: BeautifulSoup 实例（用于后续查找）。
        element: li DOM 元素的 BeautifulSoup Tag。

    Returns:
        文章信息字典，或 None（无法解析时）。
    """
    try:
        # 获取标题和 URL
        title_link = element.select_one('h3 a')
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        url = title_link.get('href', '')

        # 处理相对 URL
        if url.startswith('/'):
            url = f'https://weixin.sogou.com{url}'

        # 获取概要
        summary_tag = element.select_one('p.txt-info')
        summary = summary_tag.get_text(strip=True) if summary_tag else ''

        # 获取日期和来源
        datetime_str = ''
        date_text = ''
        source = ''
        time_description = ''

        source_box = element.select_one('.s-p')
        if source_box:
            # 优先从 script 标签获取时间戳
            date_script = source_box.select_one('.s2 script')
            if date_script:
                script_text = date_script.get_text()
                ts_match = re.search(r'(\d{10})', script_text)
                if ts_match:
                    timestamp = int(ts_match.group(1))
                    article_dt = datetime.fromtimestamp(timestamp, tz=_CST)
                    datetime_str = _format_china_datetime(article_dt)
                    date_text = f'{article_dt.year}年{article_dt.month:02d}月{article_dt.day:02d}日'

            # 尝试从 .s2 区域获取时间描述
            time_elem = source_box.select_one('.s2')
            if time_elem:
                script_text = ''
                script_tag = time_elem.find('script')
                if script_tag:
                    script_text = script_tag.get_text()
                ts_match = re.search(r'(\d{10})', script_text)

                if ts_match:
                    timestamp = int(ts_match.group(1))
                    article_dt = datetime.fromtimestamp(timestamp, tz=_CST)
                    now = datetime.now(tz=_CST)
                    diff = now - article_dt
                    diff_hours = diff.total_seconds() / 3600
                    diff_days = diff.days

                    if diff_days > 0:
                        time_description = f'{diff_days}天前'
                    elif diff_hours > 0:
                        time_description = f'{int(diff_hours)}小时前'
                    else:
                        diff_minutes = int(diff.total_seconds() / 60)
                        time_description = f'{diff_minutes}分钟前' if diff_minutes > 0 else '刚刚'
                else:
                    # 没有时间戳，尝试从文本中提取
                    time_text = time_elem.get_text(separator=' ', strip=True)
                    # 移除 script 内容后的文本
                    if script_tag:
                        time_text = time_text.replace(script_tag.get_text(), '').strip()
                    if time_text and not datetime_str:
                        parsed = _parse_relative_time(time_text)
                        time_description = time_text
                        datetime_str = parsed['datetime']
                        date_text = parsed['date_text']

            # 获取来源公众号名称
            source_span = source_box.select_one('.all-time-y2')
            source_link = source_box.select_one('a.account')
            if source_span:
                source = source_span.get_text(strip=True)
            elif source_link:
                source = source_link.get_text(strip=True)

        return {
            'title': title,
            'url': url,
            'summary': summary,
            'datetime': datetime_str,
            'date_text': date_text,
            'date_description': time_description or date_text,
            'source': source,
        }
    except Exception as e:
        logger.error('解析文章失败: %s', e)
        return None


def parse_articles(html: str, max_results: int) -> List[Dict[str, Any]]:
    """从搜狗搜索结果页 HTML 中解析文章列表。

    Args:
        html: 搜狗搜索结果页面 HTML。
        max_results: 最大返回结果数。

    Returns:
        文章信息字典列表。
    """
    articles: List[Dict[str, Any]] = []
    soup = BeautifulSoup(html, 'lxml')

    news_list = soup.select_one('ul.news-list')
    if not news_list:
        return []

    for li in news_list.select('li'):
        if len(articles) >= max_results:
            break
        article = _parse_single_article(soup, li)
        if article:
            articles.append(article)

    return articles


# ─── 微信跳转链接提取 ──────────────────────────────────────────────────────


def extract_redirect_url(html: str) -> Optional[str]:
    """从 HTML 中提取跳转 URL。

    处理三种模式（按优先级）：
    1. ``<meta http-equiv="refresh" content="0; url=...">``
    2. JavaScript ``location.href = '...'`` 或 ``location = '...'`` 或 ``window.location = '...'``
    3. JavaScript ``url += '...'`` 拼接方式（结果包含 ``mp.weixin.qq.com`` 时返回）

    Args:
        html: HTML 内容。

    Returns:
        跳转 URL 或 None。
    """
    # 模式 1: meta refresh
    meta_match = re.search(
        r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']\d+;\s*url=([^"\']+)["\'][^>]*>',
        html,
        re.IGNORECASE,
    )
    if meta_match:
        return meta_match.group(1)

    # 模式 2: JavaScript 跳转
    js_match = (
        re.search(r"""location\.href\s*=\s*['"]([^'"]+)['"]""", html, re.IGNORECASE)
        or re.search(r"""location\s*=\s*['"]([^'"]+)['"]""", html, re.IGNORECASE)
        or re.search(r"""window\.location\s*=\s*['"]([^'"]+)['"]""", html, re.IGNORECASE)
    )
    if js_match:
        return js_match.group(1)

    # 模式 3: url += '...' 拼接方式
    url_parts: List[str] = []
    for m in re.finditer(r"""url\s*\+=\s*'([^']*)'""", html, re.IGNORECASE):
        url_parts.append(m.group(1))
    for m in re.finditer(r'''url\s*\+=\s*"([^"]*)"''', html, re.IGNORECASE):
        url_parts.append(m.group(1))
    if url_parts:
        joined = ''.join(url_parts)
        if 'mp.weixin.qq.com' in joined:
            return joined

    return None


# ─── URL 跳转解析 ─────────────────────────────────────────────────────────


def get_real_url(
    url: str,
    cookie_obj: Optional[Dict[str, str]] = None,
    retries: int = 3,
) -> str:
    """获取搜狗跳转链接重定向后的真实微信文章 URL。

    向目标 URL 发起请求，检测：
    - HTTP 3xx 重定向（``Location`` 响应头）
    - 200 响应中 HTML 里的跳转链接（通过 ``extract_redirect_url``）

    Args:
        url: 搜狗跳转 URL。
        cookie_obj: Cookie 字典（如 ``{'SNUID': '...'}``）。
        retries: 最大尝试次数（默认 3）。

    Returns:
        真实的微信文章 URL。如果无法解析，返回原始 URL。
    """
    # 如果不是搜狗链接，直接返回
    if 'weixin.sogou.com' not in url:
        return url

    base_cookies = (
        'ABTEST=7|1716888919|v1; IPLOC=CN5101; '
        'ariaDefaultTheme=default; ariaFixed=true; '
        'ariaReadtype=1; ariaStatus=false'
    )
    cookie_obj = cookie_obj or {}
    snuid = cookie_obj.get('SNUID', '')
    cookie_str = f'{base_cookies}; SNUID={snuid}' if snuid else base_cookies

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'identity',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cookie': cookie_str,
        'User-Agent': get_random_user_agent(),
    }

    for attempt in range(retries):
        try:
            status_code, resp_headers, content = fetch_url(
                url=url,
                method='GET',
                headers=headers,
                timeout=5.0,
                retries=0,
                allow_redirects=False,
            )

            # 检查 3xx 重定向
            if 300 <= status_code < 400:
                location = resp_headers.get('Location') or resp_headers.get('location', '')
                if location:
                    return location if 'mp.weixin.qq.com' in location else url

            # 200 响应 — 尝试从 HTML 中提取跳转 URL
            if status_code == 200:
                html = content.decode('utf-8', errors='replace')
                logger.info('获取到HTML内容(长度: %d)，尝试解析跳转URL...', len(html))
                redirect_url = extract_redirect_url(html)
                if redirect_url and 'mp.weixin.qq.com' in redirect_url:
                    return redirect_url
                return url

        except Exception:
            logger.debug('get_real_url 尝试 %d/%d 失败', attempt + 1, retries, exc_info=True)

        if attempt < retries - 1:
            sleep(1.0)

    return url


# ─── 微信文章正文提取 ──────────────────────────────────────────────────────


def fetch_article_content(
    url: str,
    max_length: int = 0,
) -> Dict[str, Any]:
    """从微信文章页面抓取正文内容。

    使用 ``#js_content`` 选择器定位文章正文区域（微信文章的标准容器）。

    Args:
        url: 微信文章真实 URL（须为 ``mp.weixin.qq.com`` 域名）。
        max_length: 正文最大字符数（0 表示不限制）。

    Returns:
        {
            'content': str,       # 正文文本
            'word_count': int,    # 字符数
            'success': bool,      # 是否成功
            'error': str,         # 错误信息（仅失败时）
        }
    """
    if 'mp.weixin.qq.com' not in url:
        return {'content': '', 'word_count': 0, 'success': False, 'error': '非微信文章链接'}

    try:
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',
        }
        status_code, _, content = fetch_url(
            url=url,
            method='GET',
            headers=headers,
            timeout=30.0,
            retries=1,
        )

        if status_code != 200:
            return {
                'content': '',
                'word_count': 0,
                'success': False,
                'error': f'HTTP {status_code}',
            }

        html = content.decode('utf-8', errors='replace')
        soup = BeautifulSoup(html, 'lxml')

        content_elem = soup.select_one('#js_content')
        if not content_elem:
            return {
                'content': '',
                'word_count': 0,
                'success': False,
                'error': '未找到文章正文元素',
            }

        text = content_elem.get_text(separator=' ', strip=True)
        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        if max_length > 0 and len(text) > max_length:
            text = text[:max_length] + '...(已截断)'

        return {
            'content': text,
            'word_count': len(text),
            'success': True,
        }
    except Exception as e:
        return {
            'content': '',
            'word_count': 0,
            'success': False,
            'error': str(e),
        }


# ─── 批量操作 ──────────────────────────────────────────────────────────────


def fetch_articles_content(
    articles: List[Dict[str, Any]],
    max_length: int = 0,
) -> List[Dict[str, Any]]:
    """批量抓取文章正文。

    Args:
        articles: 文章列表（需已包含解析后的真实 URL 在 ``url`` 字段中）。
        max_length: 正文最大字符数（0 表示不限制）。

    Returns:
        包含 ``content`` / ``word_count`` / ``content_fetched`` 字段的文章列表。
    """
    results: List[Dict[str, Any]] = []
    success_count = 0
    fail_count = 0
    total = len(articles)

    for i, article in enumerate(articles):
        article_url = article.get('url', '')
        title_preview = article.get('title', '')[:30]
        logger.info('[%d/%d] 抓取正文: %s...', i + 1, total, title_preview)

        if 'mp.weixin.qq.com' not in article_url:
            logger.info('  跳过: 非微信文章链接')
            results.append({**article, 'content': '', 'content_fetched': False})
            fail_count += 1
            continue

        result = fetch_article_content(article_url, max_length=max_length)

        if result['success']:
            logger.info('  成功: %d 字', result['word_count'])
            success_count += 1
            results.append({
                **article,
                'content': result['content'],
                'word_count': result['word_count'],
                'content_fetched': True,
            })
        else:
            logger.info('  失败: %s', result.get('error', ''))
            fail_count += 1
            results.append({**article, 'content': '', 'content_fetched': False})

        if i < total - 1:
            sleep(0.8 + random.random() * 1.2)

    logger.info('\n正文抓取完成: 成功 %d, 失败 %d', success_count, fail_count)
    return results
