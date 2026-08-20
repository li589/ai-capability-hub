#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场数据 (v6.0.0)
=====================
美股全市场列表、GICS 行业分类、腾讯行情字段解析。

数据源：
  - 腾讯财经 qt.gtimg.cn（实时行情）
  - 东方财富 push2 API（全市场列表）
"""

import json
import ssl
import time
import urllib.request
from typing import Dict, List, Optional

from .errors import safe_float, make_result


# ── GICS 行业分类 → 美股代表股 ──────────────────────
US_SECTOR_MAP = {
    "信息技术": {
        "name_cn": "信息技术",
        "name_en": "Information Technology",
        "representatives": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "CSCO"],
    },
    "金融": {
        "name_cn": "金融",
        "name_en": "Financials",
        "representatives": ["JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP"],
    },
    "医疗保健": {
        "name_cn": "医疗保健",
        "name_en": "Healthcare",
        "representatives": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT"],
    },
    "可选消费": {
        "name_cn": "可选消费",
        "name_en": "Consumer Discretionary",
        "representatives": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "BKNG"],
    },
    "必需消费": {
        "name_cn": "必需消费",
        "name_en": "Consumer Staples",
        "representatives": ["WMT", "PG", "KO", "PEP", "COST", "PM", "MDLZ", "CL"],
    },
    "能源": {
        "name_cn": "能源",
        "name_en": "Energy",
        "representatives": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY"],
    },
    "工业": {
        "name_cn": "工业",
        "name_en": "Industrials",
        "representatives": ["CAT", "GE", "BA", "UPS", "RTX", "HON", "LMT", "DE"],
    },
    "通信服务": {
        "name_cn": "通信服务",
        "name_en": "Communication Services",
        "representatives": ["GOOGL", "META", "NFLX", "DIS", "T", "VZ", "TMUS", "CHTR"],
    },
    "公用事业": {
        "name_cn": "公用事业",
        "name_en": "Utilities",
        "representatives": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"],
    },
    "房地产": {
        "name_cn": "房地产",
        "name_en": "Real Estate",
        "representatives": ["PLD", "AMT", "CCI", "EQIX", "SPG", "PSA", "O", "WELL"],
    },
    "原材料": {
        "name_cn": "原材料",
        "name_en": "Materials",
        "representatives": ["LIN", "SHW", "APD", "ECL", "FCX", "NEM", "DOW", "NUE"],
    },
}


# ── 美股主要指数成分股 ──────────────────────
US_INDEX_COMPONENTS = {
    "DJIA": ["AAPL", "MSFT", "JPM", "JNJ", "WMT", "V", "PG", "HD", "UNH",
             "BAC", "DIS", "CSCO", "KO", "MRK", "CRM", "AXP", "MCD", "NKE",
             "IBM", "HON", "GS", "CAT", "MMM", "AMGN", "BA", "TRV", "CVX",
             "DOW", "WBA", "INTC"],
    "NASDAQ100": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA",
                  "AVGO", "COST", "NFLX", "ADBE", "PEP", "CSCO", "TMUS",
                  "INTC", "CMCSA", "QCOM", "TXN", "AMGN", "INTU", "AMD",
                  "AMAT", "HON", "LRCX", "BKNG", "ADI", "REGN", "VRTX",
                  "MU", "KLAC"],
    "SP500_TOP": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA",
                  "BRK.B", "JPM", "UNH", "V", "JNJ", "WMT", "MA", "XOM",
                  "PG", "HD", "LLY", "COST", "ABBV", "NFLX", "BAC", "MRK",
                  "CVX", "KO", "PEP", "ADBE", "CRM", "ORCL", "TMO"],
}


class UsMarketData:
    """
    美股市场数据获取。

    使用腾讯 qt.gtimg.cn 的 t_us 前缀获取实时行情。
    使用东方财富 push2 API 获取全市场列表。
    """

    @staticmethod
    def parse_realtime(code: str, raw_fields: list) -> Dict:
        """
        解析腾讯美股行情字段。

        腾讯美股响应格式（~ 分隔）：
          [0]=市场, [1]=名称, [3]=现价, [4]=昨收, [5]=今开,
          [6]=成交量, [31]=涨跌额, [32]=涨跌幅, [33]=最高, [34]=最低,
          [38]=成交额, [47]=货币, [53]=市值

        Note: 美股字段位置与 A 股/港股略有不同。
        """
        try:
            return {
                "code": code,
                "name": raw_fields[1] if len(raw_fields) > 1 else "",
                "price": safe_float(raw_fields[3]) if len(raw_fields) > 3 else 0,
                "prev_close": safe_float(raw_fields[4]) if len(raw_fields) > 4 else 0,
                "open": safe_float(raw_fields[5]) if len(raw_fields) > 5 else 0,
                "volume": safe_float(raw_fields[6]) if len(raw_fields) > 6 else 0,
                "high": safe_float(raw_fields[33]) if len(raw_fields) > 33 else 0,
                "low": safe_float(raw_fields[34]) if len(raw_fields) > 34 else 0,
                "amount": safe_float(raw_fields[38]) if len(raw_fields) > 38 else 0,
                "change": safe_float(raw_fields[31]) if len(raw_fields) > 31 else 0,
                "change_pct": safe_float(raw_fields[32]) if len(raw_fields) > 32 else 0,
                "market_cap": safe_float(raw_fields[53]) if len(raw_fields) > 53 else 0,
                "currency": raw_fields[47] if len(raw_fields) > 47 else "USD",
                "market": "us",
            }
        except Exception as e:
            return make_result(ok=False, error=f"美股行情解析失败: {e}", code=code)

    @staticmethod
    def fetch_all_us_stocks(force_update: bool = False) -> List[Dict]:
        """
        获取美股全市场列表。

        数据源: 东方财富 push2 美股板
        m:105+t:3 (美股), m:106+t:3 (NASDAQ), m:107+t:3 (NYSE)
        """
        all_stocks = []
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }

        # 三个主要美股板
        boards = [
            "m:105+t:3",   # 美股综合
            "m:106+t:3",   # NASDAQ
            "m:107+t:3",   # NYSE
        ]

        # v8.0: 每板分页拉全（此前每板只取第一页 1000 只）
        def _fetch_page(board: str, pn: int, pz: int = 5000):
            url = (
                "https://push2.eastmoney.com/api/qt/clist/get?"
                f"fid=f3&po=1&pz={pz}&pn={pn}&np=1&fltt=2&invt=2&"
                f"fs={board}"
                "&fields=f2,f3,f12,f14,f15,f16,f17,f18,f20,f21"
            )
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))

        for board in boards:
            try:
                data = _fetch_page(board, 1)
                total = (data.get("data") or {}).get("total", 0) or 0
                for item in (data.get("data") or {}).get("diff", []) or []:
                    all_stocks.append({
                        "code": item.get("f12", ""),
                        "name": item.get("f14", ""),
                        "price": safe_float(item.get("f2", 0)),
                        "change_pct": safe_float(item.get("f3", 0)),
                    })
                pz = 5000
                total_pages = (total + pz - 1) // pz if total else 1
                for pn in range(2, total_pages + 1):
                    try:
                        d = _fetch_page(board, pn, pz)
                        for item in (d.get("data") or {}).get("diff", []) or []:
                            all_stocks.append({
                                "code": item.get("f12", ""),
                                "name": item.get("f14", ""),
                                "price": safe_float(item.get("f2", 0)),
                                "change_pct": safe_float(item.get("f3", 0)),
                            })
                        time.sleep(0.3)
                    except Exception:
                        break
            except Exception as e:
                print(f"[UsMarketData] 获取 {board} 失败: {e}")

        return all_stocks

    @staticmethod
    def get_sector_map() -> Dict:
        """返回美股 GICS 行业分类映射"""
        return US_SECTOR_MAP

    @staticmethod
    def get_sector_representatives(sector_name: str) -> List[str]:
        """获取指定行业的代表股"""
        sector = US_SECTOR_MAP.get(sector_name, {})
        return sector.get("representatives", [])

    @staticmethod
    def get_index_components(index: str) -> List[str]:
        """获取指数成分股"""
        return US_INDEX_COMPONENTS.get(index, [])

    @staticmethod
    def get_all_sectors() -> List[str]:
        """返回所有行业名称"""
        return list(US_SECTOR_MAP.keys())
