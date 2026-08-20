#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财联社电报数据源 (v6.0 新增)

财联社实时电报，比东财快讯更快，适合政策/央行事件。
注意: 财联社 2024 起对 nodeapi/roll 接口加入请求签名(反爬)，无签名返回
      "签名错误"/"小财正在加载中"。本源为 best-effort：签名失败时优雅降级，
      新闻由华尔街见闻/东财快讯(Phase 2)等其他源覆盖，不影响整体可用性。
尝试端点: https://www.cls.cn/nodeapi/updateTelegraphList (历史)
         https://www.cls.cn/v3/roll/get_roll_list (当前，需签名)
"""
from __future__ import annotations
import json
import urllib.request
from datetime import datetime
from typing import Dict, List
from .base import DataSource, SourceResponse

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.cls.cn/telegraph",
}


def _http_get(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


class ClsProvider(DataSource):
    """财联社电报源"""

    name = "财联社"
    capabilities = ["news"]

    def fetch_news(self, limit: int = 20) -> SourceResponse:
        try:
            url = (f"https://www.cls.cn/nodeapi/updateTelegraphList?"
                   f"app=CailianpressWeb&os=web&sv=8.4.6&rn={limit}&last_time=")
            text = _http_get(url, timeout=8)
            data = json.loads(text)
            items = data.get("data", {}).get("roll_data", [])
            news = []
            for item in items:
                title = item.get("title", "") or item.get("content", "")[:40]
                if not title:
                    continue
                ctime = item.get("ctime", 0)
                news.append({
                    "title": title,
                    "content": (item.get("content", "") or "")[:200],
                    "time": datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M") if ctime else "",
                    "url": item.get("shareurl", ""),
                    "is_important": item.get("level", "") == "B" or item.get("is_important", False),
                    "source": "财联社",
                })
            if not news:
                return SourceResponse.fail(self.name, "财联社返回空")
            return SourceResponse.ok(self.name, news)
        except Exception as e:
            return SourceResponse.fail(self.name, f"财联社获取失败: {e}")


def main():
    print("=== 财联社电报测试 ===")
    p = ClsProvider()
    r = p.fetch_news(limit=10)
    print(f"available={r.available}, source={r.source}")
    if r.available:
        for n in r.data[:5]:
            print(f"  [{n['time']}] {n['title'][:50]}")


if __name__ == "__main__":
    main()
