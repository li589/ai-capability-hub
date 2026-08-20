#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""蛋卷基金数据源 (v6.0 新增)

蛋卷基金详情/持有人结构/第三方评分。
接口: https://danjuanfunds.com/djapi/fund/detail/{code} (JSON)
免费、国内直连。best-effort：接口变动时优雅降级。
"""
from __future__ import annotations
import json
import urllib.request
from typing import Dict
from .base import DataSource, SourceResponse

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://danjuanfunds.com/"}


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


class DanjuanProvider(DataSource):
    """蛋卷基金源"""

    name = "蛋卷基金"
    capabilities = ["fund_nav", "fund_ratings", "fund_holder_structure"]

    def _fetch_detail(self, code: str) -> Dict:
        url = f"https://danjuanfunds.com/djapi/fund/detail/{code}"
        text = _http_get(url, timeout=8)
        data = json.loads(text)
        return data.get("data", {}) if isinstance(data, dict) else {}

    def fetch_fund_nav(self, code: str) -> SourceResponse:
        try:
            d = self._fetch_detail(code)
            if not d:
                return SourceResponse.fail(self.name, f"{code} 蛋卷无数据")
            return SourceResponse.ok(self.name, {
                "nav": _safe_float(d.get("unit_nav") or d.get("dwjz")),
                "nav_date": (d.get("net_value_date") or d.get("jzrq") or "")[:10],
                "change_pct": _safe_float(d.get("net_value_gr") or d.get("gszzl")),
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 蛋卷净值失败: {e}")

    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        try:
            d = self._fetch_detail(code)
            if not d:
                return SourceResponse.fail(self.name, f"{code} 蛋卷无数据")
            return SourceResponse.ok(self.name, {
                "source_detail": "蛋卷基金",
                "rating": d.get("rating_level") or d.get("star"),
                "sharpe": _safe_float(d.get("sharpe")),
                "max_drawdown": _safe_float(d.get("max_drawdown")),
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 蛋卷评级失败: {e}")

    def fetch_fund_holder_structure(self, code: str) -> SourceResponse:
        try:
            d = self._fetch_detail(code)
            if not d:
                return SourceResponse.fail(self.name, f"{code} 蛋卷无数据")
            return SourceResponse.ok(self.name, {
                "source_detail": "蛋卷基金",
                "institutional_pct": _safe_float(d.get("institutional_holding") or d.get("inst_holding")),
                "individual_pct": _safe_float(d.get("retail_holding")),
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 蛋卷持有人失败: {e}")


def main():
    p = DanjuanProvider()
    r = p.fetch_fund_nav("110022")
    print(r.source, r.available, r.data if r.available else r.error)


if __name__ == "__main__":
    main()
