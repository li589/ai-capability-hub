#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""晨星中国数据源 (v6.0 新增)

晨星按周期星级 + 晨星分类 + 风险调整收益。
接口: https://www.morningstar.cn/handler/quicktake.ashx (需 FCLID)
      https://www.morningstar.cn/quicktake/ (HTML)
免费、国内直连。best-effort：晨星 FCLID 映射复杂，失败优雅降级，
评级由东方财富/雪球/好买等其他源覆盖。
"""
from __future__ import annotations
import re
import urllib.request
from typing import Dict
from .base import DataSource, SourceResponse

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.morningstar.cn/"}


def _http_get(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


class MorningstarProvider(DataSource):
    """晨星中国源"""

    name = "晨星中国"
    capabilities = ["fund_ratings"]

    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        """尝试从晨星 quicktake HTML 解析星级"""
        try:
            # 晨星基金页 URL（多种格式尝试）
            for url_tmpl in [
                f"https://www.morningstar.cn/quicktake/fund/F00000{code}",
                f"https://www.morningstar.cn/quicktake/f{code}.aspx",
                f"https://www.morningstar.cn/handler/quicktake.ashx?command=rating&fcid={code}",
            ]:
                try:
                    text = _http_get(url_tmpl, timeout=8)
                    if "晨星" not in text and "morningstar" not in text.lower():
                        continue
                    # 解析星级（1-5星，通常是 ★ 图标或数字）
                    star_m = re.search(r"晨星星级[^0-9]*([1-5])", text)
                    cat_m = re.search(r"晨星分类[^<]*<[^>]*>([^<]+)", text)
                    if star_m:
                        return SourceResponse.ok(self.name, {
                            "source_detail": "晨星中国",
                            "star": int(star_m.group(1)),
                            "category": cat_m.group(1).strip() if cat_m else None,
                        })
                except Exception:
                    continue
            return SourceResponse.fail(self.name, f"{code} 晨星页不可达或需 FCLID")
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 晨星获取失败: {e}")


def main():
    p = MorningstarProvider()
    r = p.fetch_fund_ratings("110022")
    print(r.source, r.available, r.data if r.available else r.error)


if __name__ == "__main__":
    main()
