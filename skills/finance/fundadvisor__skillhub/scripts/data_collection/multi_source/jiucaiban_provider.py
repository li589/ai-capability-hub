#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""韭圈儿(funddb.cn)数据源 (v6.0 新增)

基金经理胜率/跑赢同类占比/持有人盈亏分布。
接口: https://funddb.cn/fund/{code} (HTML)
免费、国内直连。best-effort：页面变动时优雅降级。
"""
from __future__ import annotations
import re
import urllib.request
from typing import Dict
from .base import DataSource, SourceResponse

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://funddb.cn/"}


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


class JiucaibanProvider(DataSource):
    """韭圈儿源"""

    name = "韭圈儿"
    capabilities = ["fund_ratings", "fund_holder_structure"]

    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        try:
            url = f"https://funddb.cn/fund/{code}"
            text = _http_get(url, timeout=8)
            win_rate_m = re.search(r"胜率[^0-9]*([\d.]+)%", text)
            beat_m = re.search(r"跑赢同类[^0-9]*([\d.]+)%", text)
            score_m = re.search(r"评分[^0-9]*([\d.]+)", text)
            if not win_rate_m and not beat_m:
                return SourceResponse.fail(self.name, f"{code} 韭圈儿解析失败")
            return SourceResponse.ok(self.name, {
                "source_detail": "韭圈儿",
                "win_rate": _safe_float(win_rate_m.group(1)) if win_rate_m else None,
                "beat_peer_pct": _safe_float(beat_m.group(1)) if beat_m else None,
                "score": _safe_float(score_m.group(1)) if score_m else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 韭圈儿获取失败: {e}")

    def fetch_fund_holder_structure(self, code: str) -> SourceResponse:
        """持有人结构（机构/个人/内部占比）"""
        try:
            url = f"https://funddb.cn/fund/{code}"
            text = _http_get(url, timeout=8)
            inst_m = re.search(r"机构持有[^0-9]*([\d.]+)%", text)
            indiv_m = re.search(r"个人持有[^0-9]*([\d.]+)%", text)
            if not inst_m:
                return SourceResponse.fail(self.name, f"{code} 持有人结构解析失败")
            return SourceResponse.ok(self.name, {
                "source_detail": "韭圈儿",
                "institutional_pct": _safe_float(inst_m.group(1)),
                "individual_pct": _safe_float(indiv_m.group(1)) if indiv_m else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 持有人结构获取失败: {e}")


def main():
    p = JiucaibanProvider()
    r = p.fetch_fund_ratings("110022")
    print(r.source, r.available, r.data if r.available else r.error)


if __name__ == "__main__":
    main()
