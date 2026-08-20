#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中证指数官网数据源 (v6.0 新增)

中证指数成分/权重/股息率/收益，用于基准构建与风格分析。
接口: https://www.csindex.com.cn (HTML + 部分 JSON)
免费、国内直连。best-effort：页面变动时优雅降级。
"""
from __future__ import annotations
import json
import re
import urllib.request
from typing import Dict
from .base import DataSource, SourceResponse

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.csindex.com.cn/"}


def _http_get(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


class CsindexProvider(DataSource):
    """中证指数源"""

    name = "中证指数"
    capabilities = ["index"]

    def fetch_index(self, index_code: str) -> SourceResponse:
        """获取指数基本信息（点数/涨跌/成分数）"""
        try:
            # 中证指数详情页
            url = f"https://www.csindex.com.cn/zh-CN/indices/index-detail/{index_code}"
            text = _http_get(url, timeout=10)
            # 解析最新点数与涨跌
            close_m = re.search(r"最新点数[^0-9-]*([\d.]+)", text)
            change_m = re.search(r"涨跌幅[^0-9-]*([-\d.]+)%", text)
            name_m = re.search(r"<title>([^<]+)</title>", text)
            if not close_m:
                return SourceResponse.fail(self.name, f"{index_code} 解析失败")
            return SourceResponse.ok(self.name, {
                "index_code": index_code,
                "name": name_m.group(1).split("-")[0].strip() if name_m else index_code,
                "close": float(close_m.group(1)),
                "change_pct": float(change_m.group(1)) if change_m else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{index_code} 获取失败: {e}")


def main():
    p = CsindexProvider()
    r = p.fetch_index("000300")
    print(r.source, r.available, r.data if r.available else r.error)


if __name__ == "__main__":
    main()
