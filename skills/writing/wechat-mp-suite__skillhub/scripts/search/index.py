#!/usr/bin/env python3
"""
index.py — CLI 入口 / 主流程编排

微信公众号文章搜索工具。
替代原 search_wechat.js，使用 fetcher.py 和 parser.py。

用法:
    python index.py <关键词> [选项]

选项:
    -n, --num <数量>       返回结果数量（默认10，最大50）
    -o, --output <文件>    输出 JSON 文件路径
    -r, --resolve-url      解析真实的微信文章 URL（会额外请求每个链接）
    -c, --fetch-content    抓取文章正文内容（自动启用 -r）

示例:
    python index.py "人工智能" -n 20
    python index.py "ChatGPT" -n 10 -o result.json
    python index.py "人工智能" -n 5 -r
    python index.py "人工智能" -n 3 -c
"""

import argparse
import json
import math
import random
import sys
from typing import Any, Dict, List

from fetcher import fetch_html, get_sogou_cookie, sleep
from parser import (
    fetch_article_content,
    fetch_articles_content,
    get_real_url,
    parse_articles,
)


# ─── URL 解析编排 ────────────────────────────────────────────────────────────


def resolve_real_urls(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """批量获取文章的真实 URL。

    对每篇文章的搜狗跳转链接调用 ``get_real_url``，并标记是否成功解析。

    Args:
        articles: 文章列表（来自 ``parse_articles``）。

    Returns:
        包含 ``url_resolved`` 字段的文章列表。
    """
    cookie_data = get_sogou_cookie()
    cookie_obj = cookie_data.get('cookie_obj', {})
    total = len(articles)

    print(f'获取到 {total} 篇文章，开始解析真实URL...', file=sys.stderr)
    print('注意：搜狗微信有严格的反爬虫机制，可能无法获取真实URL', file=sys.stderr)

    results: List[Dict[str, Any]] = []
    success_count = 0
    fail_count = 0

    for i, article in enumerate(articles):
        title_preview = article.get('title', '')[:30]
        try:
            print(f'[{i + 1}/{total}] 解析: {title_preview}...', file=sys.stderr)
            real_url = get_real_url(article['url'], cookie_obj=cookie_obj)

            is_success = (
                'weixin.sogou.com' not in real_url
                and 'antispider' not in real_url
            )

            results.append({
                **article,
                'url': real_url if is_success else article['url'],
                'url_resolved': is_success,
            })

            if is_success:
                success_count += 1
            else:
                fail_count += 1

            if i < total - 1:
                sleep(0.5 + random.random() * 1.0)

        except Exception as e:
            print(f'  解析失败: {e}', file=sys.stderr)
            fail_count += 1
            results.append({**article, 'url': article['url'], 'url_resolved': False})

    print(f'\n解析完成: 成功 {success_count}, 失败 {fail_count}', file=sys.stderr)
    return results


# ─── 主搜索流程 ──────────────────────────────────────────────────────────────


def search_wechat_articles(
    query: str,
    max_results: int = 10,
    resolve_real_url: bool = False,
    fetch_content: bool = False,
) -> List[Dict[str, Any]]:
    """搜索微信公众号文章。

    分页爬取搜狗微信搜索结果页，每页最多 10 条；
    可选的 URL 解析和正文抓取在搜索结果收集完毕后执行。

    Args:
        query: 搜索关键词。
        max_results: 最大返回结果数（上限 50）。
        resolve_real_url: 是否解析真实微信文章 URL。
        fetch_content: 是否抓取文章正文（自动启用 ``resolve_real_url``）。

    Returns:
        文章信息字典列表。
    """
    max_results = min(max_results, 50)

    articles: List[Dict[str, Any]] = []
    page = 1
    pages_needed = math.ceil(max_results / 10)

    while len(articles) < max_results and page <= pages_needed:
        try:
            cookie_data = get_sogou_cookie()
            cookie_str = cookie_data.get('cookie_str', '')

            from urllib.parse import quote

            encoded_query = quote(query, safe='')
            url = (
                f'https://weixin.sogou.com/weixin'
                f'?query={encoded_query}&s_from=input&_sug_=n&type=2&page={page}&ie=utf8'
            )

            html = fetch_html(url, cookie_str=cookie_str)

            remaining = max_results - len(articles)
            parsed = parse_articles(html, remaining)
            if not parsed:
                break
            articles.extend(parsed)

            page += 1

            if page <= pages_needed:
                sleep(0.5 + random.random() * 1.0)

        except Exception as e:
            print(f'请求第{page}页失败: {e}', file=sys.stderr)
            break

    result = articles[:max_results]

    # 如果需要抓取正文，必须先解析真实 URL
    if fetch_content:
        resolve_real_url = True

    if resolve_real_url and result:
        print('正在解析真实URL...', file=sys.stderr)
        result = resolve_real_urls(result)

    if fetch_content and result:
        print('正在抓取文章正文...', file=sys.stderr)
        result = fetch_articles_content(result)

    return result


# ─── CLI 主函数 ──────────────────────────────────────────────────────────────


def main() -> None:
    """CLI 入口函数。"""
    parser = argparse.ArgumentParser(
        description='微信公众号文章搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python index.py "人工智能" -n 20\n'
            '  python index.py "ChatGPT" -n 10 -o result.json\n'
            '  python index.py "人工智能" -n 5 -r\n'
            '  python index.py "人工智能" -n 3 -c\n'
        ),
    )
    parser.add_argument('query', nargs='?', default='', help='搜索关键词')
    parser.add_argument(
        '-n', '--num',
        type=int,
        default=10,
        help='返回结果数量（默认10，最大50）',
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='',
        help='输出 JSON 文件路径',
    )
    parser.add_argument(
        '-r', '--resolve-url',
        action='store_true',
        dest='resolve_url',
        help='解析真实的微信文章 URL（会额外请求每个链接）',
    )
    parser.add_argument(
        '-c', '--fetch-content',
        action='store_true',
        dest='fetch_content',
        help='抓取文章正文内容（自动启用 -r）',
    )

    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        sys.exit(0)

    try:
        print(f'正在搜索: "{args.query}"...', file=sys.stderr)

        articles = search_wechat_articles(
            query=args.query,
            max_results=args.num,
            resolve_real_url=args.resolve_url,
            fetch_content=args.fetch_content,
        )

        result = {
            'query': args.query,
            'total': len(articles),
            'articles': articles,
        }

        json_output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f'结果已保存到: {args.output}', file=sys.stderr)

        print(json_output)
    except Exception as e:
        print(f'搜索失败: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
