#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""东方财富 v2 数据源 (v6.0 新增)

修复并扩展天天基金接口用法：
- data/rankhandler.aspx: 全量基金排名一次拉取（规模/费率/经理/评级）
- api.fund.eastmoney.com/f10/lsjz: 历史净值
- fundf10.eastmoney.com/yddj_{code}.html: 评级变动
免费、国内直连。作为 akshare 的备用源与评级补充。
"""
from __future__ import annotations
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, List
from .base import DataSource, SourceResponse

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://fund.eastmoney.com/",
}


def _http_get(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _safe_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A", "null"):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


class EastmoneyV2Provider(DataSource):
    """东方财富 v2 源"""

    name = "东方财富"
    capabilities = ["fund_nav", "fund_ratings", "fund_holdings"]

    def fetch_fund_nav(self, code: str) -> SourceResponse:
        """历史净值（最近若干日）via api.fund.eastmoney.com/f10/lsjz"""
        try:
            url = (f"https://api.fund.eastmoney.com/f10/lsjz?callback=jQuery"
                   f"&fundCode={code}&pageIndex=1&pageSize=20")
            text = _http_get(url, timeout=8)
            m = re.search(r"jQuery\((.*)\)$", text, re.DOTALL)
            if not m:
                return SourceResponse.fail(self.name, f"{code} lsjz 解析失败")
            data = json.loads(m.group(1))
            lsjz = data.get("Data", {}).get("LSJZList", [])
            if not lsjz:
                return SourceResponse.fail(self.name, f"{code} 无历史净值")
            latest = lsjz[0]
            return SourceResponse.ok(self.name, {
                "nav": _safe_float(latest.get("DWJZ")),
                "nav_date": (latest.get("FSRQ", "") or "")[:10],
                "change_pct": _safe_float(latest.get("JZZZL")),
                "history_count": len(lsjz),
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 净值获取失败: {e}")

    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        """评级变动 via fundf10.eastmoney.com/yddj_{code}.html"""
        try:
            url = f"https://fundf10.eastmoney.com/yddj_{code}.html"
            text = _http_get(url, timeout=8)
            # 解析最新评级行（机构/评级/日期）
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.DOTALL)
            ratings = []
            for row in rows[:10]:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
                if len(cells) >= 3:
                    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
                    ratings.append({
                        "org": cells[0], "rating": cells[1], "date": cells[2][:10],
                    })
            if not ratings:
                return SourceResponse.fail(self.name, f"{code} 无评级数据")
            # 取最新一份评级作为星级近似（东财评级文字->分）
            rating_map = {"5星": 5, "4星": 4, "3星": 3, "2星": 2, "1星": 1,
                          "买入": 5, "增持": 4, "中性": 3, "减持": 2, "卖出": 1}
            latest = ratings[0]
            star = None
            for k, v in rating_map.items():
                if k in latest["rating"]:
                    star = v
                    break
            return SourceResponse.ok(self.name, {
                "source_detail": "东方财富",
                "latest_rating": latest["rating"],
                "star": star,
                "rating_date": latest["date"],
                "history": ratings[:5],
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 评级获取失败: {e}")

    def fetch_fund_holdings(self, code: str) -> SourceResponse:
        """十大重仓 via fundf10.eastmoney.com FundArchivesDatas"""
        try:
            url = (f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?"
                   f"type=jjcc&code={code}&topline=10&year=&month=")
            text = _http_get(url, timeout=8)
            # 解析重仓股代码/名称/占比
            stocks = []
            for m in re.finditer(r"<a[^>]+>([^<]+)</a>.*?(\d+\.\d+)%", text, re.DOTALL):
                stocks.append({"name": m.group(1).strip(), "ratio": _safe_float(m.group(2))})
                if len(stocks) >= 10:
                    break
            if not stocks:
                return SourceResponse.fail(self.name, f"{code} 无重仓数据")
            return SourceResponse.ok(self.name, stocks)
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 重仓获取失败: {e}")


def main():
    print("=== 东方财富 v2 测试 ===")
    p = EastmoneyV2Provider()
    r = p.fetch_fund_nav("110022")
    print(f"净值 110022: available={r.available}", r.data if r.available else r.error)
    r2 = p.fetch_fund_ratings("110022")
    print(f"评级 110022: available={r2.available}", (r2.data or {}).get("latest_rating") if r2.available else r2.error)


if __name__ == "__main__":
    main()
