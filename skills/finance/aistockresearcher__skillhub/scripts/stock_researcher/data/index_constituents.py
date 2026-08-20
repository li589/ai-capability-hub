#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""指数成分股清单 (v9.0.0 新增)
==============================
为市场内含/宽度分析的「full 模式」提供指数成分股清单。

东财成分股接口（push2 clist 按板块 fs=BK 拉成分）best-effort 获取，
失败时回退到内置精选篮子（INDEX_BASKET，真实流通权重靠前标的）。
结果带缓存（@cached 30min），避免反复请求。

用法:
    from stock_researcher.data.index_constituents import IndexConstituents
    codes = IndexConstituents().get("sh000300")   # -> List[str]
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from typing import Dict, List, Optional

try:
    from stock_researcher.data.cache import cached
except Exception:  # pragma: no cover
    cached = lambda ttl=300, **kw: (lambda f: f)   # 无缓存时退化为直调

# 内置精选篮子（真实流通权重靠前标的；东财拉取失败时兜底）
FALLBACK_BASKET: Dict[str, List[str]] = {
    "sh000300": ["600519", "601318", "600036", "000858", "600276", "601012",
                 "300750", "000333", "600900", "601166", "002594", "601398",
                 "600030", "000002", "600887", "002415", "601899", "600809"],
    "sh000001": ["601398", "601939", "600519", "601288", "601988", "600036",
                 "601318", "601628", "600900", "601857"],
    "sz399006": ["300750", "300059", "300015", "300760", "300124", "300498",
                 "300142", "300033", "300012", "300274", "300413", "300782"],
    "sh000688": ["688981", "688041", "688256", "688111", "688599", "688036",
                 "688012", "688169", "688008", "688396"],
    "100.SPX": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK",
                "JPM", "V", "UNH", "XOM"],
    "100.NDX": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO",
                "COST", "NFLX"],
    "100.HSI": ["00700", "09988", "00005", "00939", "01299", "03690", "00388",
                "00002", "01810", "00941", "00883", "09618"],
}

# 指数代码 → 东财板块 fs 代码（用于拉取真实成分）
EM_BOARD: Dict[str, str] = {
    "sh000300": "b:BK0500",     # 沪深300（东财板块）
    "sz399006": "b:BK0704",     # 创业板指
    "sh000688": "b:BK1044",     # 科创50
}


class IndexConstituents:
    """指数成分股清单提供者。"""

    def __init__(self, use_network: bool = True):
        self._use_network = use_network

    def get(self, code: str) -> List[str]:
        """取指数成分股（东财优先，失败回退精选篮子）。"""
        if self._use_network:
            try:
                codes = self._fetch_em_constituents(code)
                if len(codes) >= 10:
                    return codes
            except Exception:
                pass
        return list(FALLBACK_BASKET.get(code, []))

    @cached(ttl=1800)
    def _fetch_em_constituents(self, code: str) -> List[str]:
        """东财 push2 clist 拉成分（fs=b:BKxxxx）。失败返回空。"""
        board = EM_BOARD.get(code)
        if not board:
            return []
        url = (
            "https://push2.eastmoney.com/api/qt/clist/get?"
            f"pn=1&pz=200&po=1&np=1&fltt=2&invt=2&fid=f3"
            f"&fs={board}&fields=f12"
        )
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            diff = (data.get("data") or {}).get("diff") or []
            codes = []
            for item in diff:
                c = str(item.get("f12", ""))
                if c:
                    codes.append(c)
            return codes
        except Exception:
            return []

    def provide(self, code: str) -> List[str]:
        """作为 constituents_provider 回调的兼容签名（market_internals 用）。"""
        return self.get(code)


def get_index_constituents(code: str) -> List[str]:
    """便捷函数：指数成分股。"""
    return IndexConstituents().get(code)
