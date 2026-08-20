# -*- coding: utf-8 -*-
"""
实时动态页面监控器
监控不断更新的页面（如实时行情、公告列表等）
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

try:
    from scrapling.fetchers import StealthyFetcher, DynamicFetcher
    from scrapling.parser import Selector
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class PageSnapshot:
    """页面快照"""
    url: str
    timestamp: str
    content_hash: str  # 内容哈希，用于检测变化
    content: str  # 原始内容
    items: List[Dict] = field(default_factory=list)  # 提取的条目
    metadata: Dict = field(default_factory=dict)


@dataclass
class ChangeEvent:
    """变化事件"""
    event_type: str  # new, updated, removed
    item: Dict
    timestamp: str
    previous_state: Optional[Dict] = None


class RealtimePageMonitor:
    """实时页面监控器"""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "data" / "page_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.fetcher = None
        if SCRAPLING_AVAILABLE:
            self.fetcher = StealthyFetcher()

        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

        self.last_snapshot: Optional[PageSnapshot] = None
        self.snapshots: List[PageSnapshot] = []

    def fetch_page(self, url: str, use_dynamic: bool = False) -> Optional[PageSnapshot]:
        """
        获取页面快照

        Args:
            url: 页面URL
            use_dynamic: 是否使用动态渲染

        Returns:
            PageSnapshot对象
        """
        try:
            if use_dynamic and SCRAPLING_AVAILABLE:
                page = DynamicFetcher.fetch(url, headless=True, network_idle=True)
                if hasattr(page, 'html_content'):
                    page.html = page.html_content
                elif hasattr(page, 'body') and isinstance(page.body, str):
                    page.html = page.body
                content = page.html
            elif self.fetcher:
                page = self.fetcher.fetch(url, headless=True)
                if hasattr(page, 'html_content'):
                    page.html = page.html_content
                elif hasattr(page, 'body') and isinstance(page.body, str):
                    page.html = page.body
                content = page.html
            elif self.session:
                resp = self.session.get(url, timeout=30)
                content = resp.text
            else:
                return None

            # 计算内容哈希
            content_hash = hashlib.md5(content[:10000].encode()).hexdigest()

            snapshot = PageSnapshot(
                url=url,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                content_hash=content_hash,
                content=content[:50000]  # 限制长度
            )

            self.last_snapshot = snapshot
            return snapshot

        except Exception as e:
            print(f"[错误] 获取页面失败: {e}")
            return None

    def extract_items(self, snapshot: PageSnapshot,
                     selectors: List[str] = None,
                     item_pattern: str = None) -> List[Dict]:
        """
        从快照中提取条目

        Args:
            snapshot: 页面快照
            selectors: CSS选择器列表
            item_pattern: 条目匹配正则

        Returns:
            提取的条目列表
        """
        items = []

        if not snapshot.content:
            return items

        # 使用选择器
        if selectors and self.fetcher:
            try:
                page = Selector(snapshot.content)
                for sel in selectors:
                    elements = page.css(sel)
                    for el in elements:
                        text = el.text().strip()
                        href = el.get_attribute("href") or ""
                        if text:
                            items.append({
                                "text": text,
                                "href": href,
                                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    if items:
                        break
            except Exception as e:
                print(f"[错误] 选择器提取失败: {e}")

        # 使用正则模式
        elif item_pattern:
            try:
                import re
                matches = re.findall(item_pattern, snapshot.content)
                for match in matches:
                    if isinstance(match, tuple):
                        items.append({"match": match, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                    else:
                        items.append({"text": match, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            except Exception as e:
                print(f"[错误] 正则提取失败: {e}")

        snapshot.items = items
        return items

    def detect_changes(self, new_snapshot: PageSnapshot) -> List[ChangeEvent]:
        """
        检测页面变化

        Args:
            new_snapshot: 新快照

        Returns:
            变化事件列表
        """
        events = []

        if not self.last_snapshot:
            self.last_snapshot = new_snapshot
            return events

        # 内容哈希变化
        if new_snapshot.content_hash != self.last_snapshot.content_hash:
            print(f"[监控] 检测到页面变化: {new_snapshot.url}")

            # 提取新条目
            new_items = new_snapshot.items or self.extract_items(new_snapshot)
            old_items = self.last_snapshot.items or []

            # 对比
            old_texts = {item.get('text', '') for item in old_items}
            old_hrefs = {item.get('href', '') for item in old_items}

            for item in new_items:
                text = item.get('text', '')
                href = item.get('href', '')

                if text and text not in old_texts:
                    events.append(ChangeEvent(
                        event_type="new",
                        item=item,
                        timestamp=new_snapshot.timestamp
                    ))
                elif href and href not in old_hrefs and href.startswith('http'):
                    events.append(ChangeEvent(
                        event_type="new",
                        item=item,
                        timestamp=new_snapshot.timestamp
                    ))

        self.last_snapshot = new_snapshot
        return events

    def monitor_loop(self, url: str,
                    interval: int = 60,
                    duration: int = 3600,
                    on_change: Callable[[ChangeEvent], None] = None,
                    selectors: List[str] = None) -> List[ChangeEvent]:
        """
        监控循环

        Args:
            url: 监控URL
            interval: 检查间隔（秒）
            duration: 监控时长（秒）
            on_change: 变化回调函数
            selectors: 条目选择器

        Returns:
            所有变化事件
        """
        all_events = []
        start_time = time.time()

        print(f"[监控] 开始监控: {url}")
        print(f"[监控] 间隔: {interval}秒, 时长: {duration}秒")

        while time.time() - start_time < duration:
            snapshot = self.fetch_page(url)
            if snapshot:
                if selectors:
                    self.extract_items(snapshot, selectors)

                changes = self.detect_changes(snapshot)
                for change in changes:
                    all_events.append(change)
                    if on_change:
                        on_change(change)
                    print(f"[变化] {change.event_type}: {change.item.get('text', '')[:50]}")

            time.sleep(interval)

        print(f"[监控] 结束，共检测到{len(all_events)}个变化")
        return all_events

    def save_snapshot(self, snapshot: PageSnapshot):
        """保存快照到缓存"""
        cache_file = self.cache_dir / f"{hashlib.md5(snapshot.url.encode()).hexdigest()}_{snapshot.timestamp.replace(':', '-')}.json"

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'url': snapshot.url,
                'timestamp': snapshot.timestamp,
                'content_hash': snapshot.content_hash,
                'items': snapshot.items,
                'metadata': snapshot.metadata
            }, f, ensure_ascii=False, indent=2)

    def load_latest_snapshot(self, url: str) -> Optional[PageSnapshot]:
        """加载最新的缓存快照"""
        url_hash = hashlib.md5(url.encode()).hexdigest()

        cache_files = list(self.cache_dir.glob(f"{url_hash}_*.json"))
        if not cache_files:
            return None

        latest = max(cache_files, key=lambda p: p.stat().st_mtime)

        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return PageSnapshot(
            url=data['url'],
            timestamp=data['timestamp'],
            content_hash=data['content_hash'],
            content='',
            items=data.get('items', []),
            metadata=data.get('metadata', {})
        )


class AnnouncementMonitor(RealtimePageMonitor):
    """公告监控器 - 专门用于监控新公告"""

    def __init__(self):
        super().__init__()
        self.announcement_selectors = [
            '.news-list li a',
            '.notice-list li a',
            '[class*="notice"] li a',
            '.announcement tr a'
        ]

    def check_new_announcements(self, fund_code: str) -> List[ChangeEvent]:
        """
        检查新公告

        Args:
            fund_code: 基金代码

        Returns:
            新公告列表
        """
        url = f"https://fund.eastmoney.com/Notice/{fund_code}.html"
        snapshot = self.fetch_page(url)

        if not snapshot:
            return []

        self.extract_items(snapshot, self.announcement_selectors)
        changes = self.detect_changes(snapshot)

        # 只返回新的公告
        return [c for c in changes if c.event_type == 'new']

    def monitor_fund_announcements(self, fund_code: str,
                                  interval: int = 300,
                                  duration: int = 7200) -> List[ChangeEvent]:
        """
        监控基金公告

        Args:
            fund_code: 基金代码
            interval: 检查间隔（秒）
            duration: 监控时长（秒）

        Returns:
            新公告列表
        """
        url = f"https://fund.eastmoney.com/Notice/{fund_code}.html"

        def on_change(event: ChangeEvent):
            print(f"[新公告] {event.item.get('text', '')[:60]}")

        return self.monitor_loop(url, interval, duration, on_change,
                                self.announcement_selectors)


class MarketNewsMonitor(RealtimePageMonitor):
    """市场新闻监控器"""

    def __init__(self):
        super().__init__()
        self.news_selectors = [
            '.news-list li a',
            '[class*="news"] li a',
            '.headline-list li a'
        ]

    def check_market_news(self) -> List[ChangeEvent]:
        """检查市场新闻"""
        url = "https://fund.eastmoney.com/news.html"

        snapshot = self.fetch_page(url)
        if not snapshot:
            return []

        self.extract_items(snapshot, self.news_selectors)
        return self.detect_changes(snapshot)


# CLI入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python realtime_monitor.py check <URL>           # 检查页面")
        print("  python realtime_monitor.py monitor <URL>          # 持续监控")
        print("  python realtime_monitor.py announcements <代码>   # 监控公告")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        url = sys.argv[2] if len(sys.argv) > 2 else "https://fund.eastmoney.com/000001.html"
        monitor = RealtimePageMonitor()
        snapshot = monitor.fetch_page(url)
        if snapshot:
            print(f"获取成功: {snapshot.url}")
            print(f"时间戳: {snapshot.timestamp}")
            print(f"内容哈希: {snapshot.content_hash}")

    elif cmd == "monitor":
        url = sys.argv[2] if len(sys.argv) > 2 else "https://fund.eastmoney.com/news.html"
        monitor = RealtimePageMonitor()
        events = monitor.monitor_loop(url, interval=60, duration=300)
        print(f"\n共检测到{len(events)}个变化")

    elif cmd == "announcements":
        fund_code = sys.argv[2] if len(sys.argv) > 2 else "000001"
        monitor = AnnouncementMonitor()
        events = monitor.monitor_fund_announcements(fund_code, interval=60, duration=300)
        print(f"\n共检测到{len(events)}个新公告")

    else:
        print(f"未知命令: {cmd}")
