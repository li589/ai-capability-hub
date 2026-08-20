#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金经理新闻/采访采集器（manager_news_collector.py，v10.0 新增）
================================================================
采集基金经理的公开新闻、采访与公告动态，供「经理人设卡」与「经理对话」使用：

  1. 东财官方搜索 API（search-api-web.eastmoney.com，主源，v10.0.1 调优）
     → 按「经理名 基金经理」检索 cmsArticleWebOld 文章（标题/日期/URL/摘要）
  2. 天天基金公告接口 api.fund.eastmoney.com/f10/JJGG（经理现任基金）
     → 含「基金经理」字样或经理姓名的 变更/增聘/离任 公告（经理变动监控用）
  3. 东财经理档案页 fund.eastmoney.com/manager/{id}.html（best effort 补充，
     反爬壳页时静默跳过）

输出 data/manager_news.json：
  {"news": [{manager_id, manager_name, title, date, source, url, type, summary}],
   "meta": {"total", "last_update", "source", "managers_scanned"}}

零依赖（stdlib urllib）。

用法:
  python manager_news_collector.py --limit 200      # 前 200 位经理（默认全部有效经理）
  python manager_news_collector.py --names 张坤,葛兰
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from fund_advisor_paths import DATA_DIR, load_json_data  # noqa: E402

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 新闻标题过滤：不含这些词的不算经理相关新闻
_TITLE_KEYWORDS = ('基金', '投资', '市场', '业绩', '持仓', '风格', '经理', '观点',
                   '展望', '访谈', '专访', '对话', '调仓', '管理', '赛道', '板块',
                   '回报', '净值', '规模', '策略', '研判', '公募', '申购', '赎回')
_INTERVIEW_KEYWORDS = ('访谈', '专访', '对话', '面对面', '实录', '问答')
_ANNOUNCE_KEYWORDS = ('基金经理', '变更', '离任', '增聘', '任职')

_HTTP_TIMEOUT = 12
_SEARCH_API = 'https://search-api-web.eastmoney.com/search/jsonp?cb=cb&param={param}'


def http_get(url: str, timeout: int = _HTTP_TIMEOUT, encoding: str = 'utf-8') -> str:
    """带 UA 的 HTTP GET（失败返回空串）"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT,
            'Referer': 'https://so.eastmoney.com/',
            'Accept': 'text/html,application/json,*/*',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return raw.decode(encoding, errors='replace')
    except Exception:
        return ''


def _strip_html(html: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()


def _classify(title: str) -> str:
    if any(kw in title for kw in _INTERVIEW_KEYWORDS):
        return '访谈'
    # 仅真正的变更/离任/增聘/任职类公告才算「公告」（标题仅含「基金经理」是新闻）
    if '基金经理' in title and any(kw in title for kw in ('变更', '离任', '增聘', '任职', '更换')):
        return '公告'
    return '新闻'


class ManagerNewsCollector:
    """基金经理新闻采集器"""

    def __init__(self, delay: float = 0.15, max_per_manager: int = 6):
        self.delay = delay
        self.max_per_manager = max_per_manager

    def load_managers(self) -> List[dict]:
        """加载经理库（列式透明解码）"""
        try:
            data = load_json_data('fund_managers_distilled.json')
            mgrs = data.get('items') or data.get('managers') or []
            if mgrs:
                return mgrs
        except Exception:
            pass
        return []

    # ── 源1：东财官方搜索 API（主源） ──────────────────────────

    def _fetch_from_search_api(self, manager: dict, page_size: int = 8) -> List[dict]:
        """按「经理名 基金经理」检索 cmsArticleWebOld 文章（官方 JSONP API）"""
        name = str(manager.get('name', ''))
        mid = str(manager.get('manager_id') or manager.get('code') or '')
        if not name:
            return []
        param = json.dumps({
            'uid': '', 'keyword': f'{name} 基金经理',
            'type': ['cmsArticleWebOld'],
            'client': 'web', 'clientType': 'web', 'clientVersion': 'curr',
            'param': {'cmsArticleWebOld': {
                'searchScope': 'default', 'sort': 'default',
                'pageIndex': 1, 'pageSize': page_size,
                'preTag': '', 'postTag': ''}},
        }, ensure_ascii=False)
        text = http_get(_SEARCH_API.format(param=urllib.parse.quote(param)))
        m = re.search(r'cb\((.*)\)\s*;?\s*$', text, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            return []
        items: List[dict] = []
        seen: set = set()
        for row in (data.get('result') or {}).get('cmsArticleWebOld') or []:
            title = str(row.get('title', '')).strip()
            url = str(row.get('url', ''))
            date = str(row.get('date', ''))[:10]
            if not title or title in seen:
                continue
            if not any(kw in title for kw in _TITLE_KEYWORDS):
                continue
            seen.add(title)
            items.append({
                'manager_id': mid,
                'manager_name': name,
                'title': title,
                'date': date,
                'source': f"东方财富-资讯（{row.get('mediaName') or '网络'}）",
                'url': url,
                'type': _classify(title),
                'summary': str(row.get('content', ''))[:80],
            })
            if len(items) >= self.max_per_manager:
                break
        return items

    # ── 源2：天天基金公告接口（经理现任基金） ──────────────────

    def _fetch_from_announcements(self, manager: dict) -> List[dict]:
        """从基金公告中找含「基金经理」/经理姓名的公告标题"""
        code = str(manager.get('current_fund_code', '')).zfill(6)
        name = str(manager.get('name', ''))
        mid = str(manager.get('manager_id') or manager.get('code') or '')
        if not (code and code.isdigit()):
            return []
        url = ('http://api.fund.eastmoney.com/f10/JJGG'
               f'?fundcode={code}&pageIndex=1&pageSize=50&type=1&_={int(time.time()*1000)}')
        text = http_get(url)
        items: List[dict] = []
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return items
        for row in (data.get('Data') or []):
            title = str(row.get('TITLE', ''))
            date = str(row.get('PUBLISHDATEDesc') or row.get('PUBLISHDATE', ''))[:10]
            if not title:
                continue
            hit = ('基金经理' in title) or (name and name in title)
            if not hit:
                continue
            items.append({
                'manager_id': mid,
                'manager_name': name,
                'title': title,
                'date': date,
                'source': '天天基金-公告',
                'url': '',
                'type': '公告',
            })
            if len(items) >= self.max_per_manager:
                break
        return items

    # ── 源3：东财经理档案页（best effort 补充，反爬壳页静默跳过） ──

    def _fetch_from_manager_page(self, manager: dict) -> List[dict]:
        """从 fund.eastmoney.com/manager/{id}.html 提取经理新闻"""
        mid = str(manager.get('manager_id') or manager.get('code') or '')
        name = str(manager.get('name', ''))
        if not mid:
            return []
        html = http_get(f'https://fund.eastmoney.com/manager/{mid}.html')
        if not html or len(html) < 5000:
            return []  # 反爬壳页/空页
        items: List[dict] = []
        seen: set = set()
        for m in re.finditer(r'<a\s+href=["\'](https?://[^"\']+)["\'][^>]*>\s*([^<]{8,60}?)\s*</a>',
                             html):
            url, title = m.group(1), _strip_html(m.group(2))
            if not url or not title or title in seen:
                continue
            if not any(kw in title for kw in _TITLE_KEYWORDS):
                continue
            seen.add(title)
            items.append({
                'manager_id': mid,
                'manager_name': name,
                'title': title,
                'date': '',
                'source': '东方财富-经理档案页',
                'url': url,
                'type': _classify(title),
                'summary': '',
            })
            if len(items) >= self.max_per_manager:
                break
        return items

    # ── 批量 ───────────────────────────────────────────────────

    def collect(self, managers: List[dict], limit: Optional[int] = None,
                with_search: bool = True) -> List[dict]:
        """批量采集（主源搜索 API + 公告补充；with_search=True 追加档案页 best effort）"""
        valid = []
        for m in managers:
            try:
                scale = float(str(m.get('total_scale', '0')).replace('亿', '').replace('元', '') or 0)
            except (ValueError, TypeError):
                scale = 0.0
            valid.append((scale, m))
        valid.sort(key=lambda x: -x[0])
        targets = [m for _, m in valid][:limit] if limit else [m for _, m in valid]

        all_news: List[dict] = []
        for i, m in enumerate(targets):
            news = self._fetch_from_search_api(m)
            if len(news) < 2:
                news += self._fetch_from_announcements(m)
            if with_search and len(news) < 3:
                news += self._fetch_from_manager_page(m)
            all_news.extend(news)
            time.sleep(self.delay)
            if (i + 1) % 100 == 0 or i == len(targets) - 1:
                print(f"  进度: {i+1}/{len(targets)} 已采 {len(all_news)} 条")
        return all_news

    # ── 保存 ───────────────────────────────────────────────────

    @staticmethod
    def save(news: List[dict], scanned: int = 0) -> Path:
        path = DATA_DIR / 'manager_news.json'
        payload = {
            'news': news,
            'meta': {
                'total': len(news),
                'managers_scanned': scanned,
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '东方财富搜索API + 天天基金公告 + 经理档案页',
            },
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return path


def main():
    parser = argparse.ArgumentParser(description='基金经理新闻/采访采集')
    parser.add_argument('--limit', type=int, default=None, help='采集经理数上限（默认全部）')
    parser.add_argument('--names', type=str, default='', help='指定经理姓名，逗号分隔')
    parser.add_argument('--no-page', action='store_true', help='跳过经理档案页补充源')
    parser.add_argument('--delay', type=float, default=0.15, help='请求间隔秒数')
    args = parser.parse_args()

    collector = ManagerNewsCollector(delay=args.delay)
    managers = collector.load_managers()
    if args.names:
        names = [n.strip() for n in args.names.split(',') if n.strip()]
        managers = [m for m in managers if m.get('name', '') in names]
    if not managers:
        print('[ERROR] 经理库为空或未找到指定经理，请先运行 update_data.py full')
        sys.exit(1)

    print(f"开始采集 {len(managers)} 位经理的新闻/采访...")
    news = collector.collect(managers, limit=args.limit, with_search=not args.no_page)
    path = collector.save(news, scanned=len(managers))
    print(f"完成: {len(news)} 条新闻 → {path}")
    types: Dict[str, int] = {}
    for n in news:
        types[n['type']] = types.get(n['type'], 0) + 1
    print(f"类型分布: {types}")


if __name__ == '__main__':
    main()
