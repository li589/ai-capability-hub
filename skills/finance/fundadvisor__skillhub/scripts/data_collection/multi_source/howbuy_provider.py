#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""好买基金数据源 (v6.0 新增)

好买评级 + 基金经理能力归因(选股/择时 alpha)。
接口: https://www.howbuy.com/fund/{code}/ (HTML)
免费、国内直连。best-effort：页面变动时优雅降级。
"""
from __future__ import annotations
import re
import urllib.request
import urllib.parse
from typing import Dict
from .base import DataSource, SourceResponse

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.howbuy.com/"}


def _http_get(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _safe_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A"):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


class HowbuyProvider(DataSource):
    """好买基金源"""

    name = "好买基金"
    capabilities = ["fund_ratings", "manager_attribution"]

    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        try:
            url = f"https://www.howbuy.com/fund/{code}/"
            text = _http_get(url, timeout=8)
            # 好买评级（通常是数字 1-5 或星级图标）
            rating_m = re.search(r"好买评级[^0-9]*([1-5])", text)
            score_m = re.search(r"综合评分[^0-9]*([\d.]+)", text)
            if not rating_m and not score_m:
                return SourceResponse.fail(self.name, f"{code} 好买评级解析失败")
            return SourceResponse.ok(self.name, {
                "source_detail": "好买基金",
                "star": int(rating_m.group(1)) if rating_m else None,
                "score": _safe_float(score_m.group(1)) if score_m else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 好买获取失败: {e}")

    def fetch_manager_attribution(self, manager_name: str) -> SourceResponse:
        """经理能力归因（选股alpha/择时alpha）- best-effort HTML 解析"""
        try:
            url = f"https://www.howbuy.com/fund/manager/{urllib.parse.quote(manager_name)}/"
            text = _http_get(url, timeout=8)
            stock_sel = re.search(r"选股能力[^0-9-]*([-\d.]+)", text)
            timing = re.search(r"择时能力[^0-9-]*([-\d.]+)", text)
            if not stock_sel and not timing:
                return SourceResponse.fail(self.name, f"{manager_name} 归因解析失败")
            return SourceResponse.ok(self.name, {
                "source_detail": "好买基金",
                "stock_selection_alpha": _safe_float(stock_sel.group(1)) if stock_sel else None,
                "timing_alpha": _safe_float(timing.group(1)) if timing else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{manager_name} 归因获取失败: {e}")


def main():
    p = HowbuyProvider()
    r = p.fetch_fund_ratings("110022")
    print(r.source, r.available, r.data if r.available else r.error)


if __name__ == "__main__":
    main()
