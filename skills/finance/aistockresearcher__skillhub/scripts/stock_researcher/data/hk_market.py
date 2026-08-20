#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场数据 (v6.0.0)
=====================
港股全市场列表、行业分类、腾讯行情字段解析。

数据源：
  - 腾讯财经 qt.gtimg.cn（实时行情）
  - 东方财富 push2 API（全市场列表）
"""

import json
import time
from typing import Dict, List, Optional

from .market_classifier import MarketClassifier, TENCENT_FIELD_MAP
from .errors import safe_float, make_result, DataSourceError, handle_request


# ── 港股行业分类（恒生 + 申万混合）──────────────────────
HK_SECTOR_MAP = {
    "科技": {
        "name_cn": "科技",
        "name_en": "Technology",
        "representatives": ["00700", "09988", "03690", "01810", "09618", "09999", "09888", "02015"],
    },
    "金融": {
        "name_cn": "金融",
        "name_en": "Financials",
        "representatives": ["00005", "00388", "01299", "02318", "02628", "03968", "01398", "00939"],
    },
    "地产建筑": {
        "name_cn": "地产建筑",
        "name_en": "Property & Construction",
        "representatives": ["00016", "00017", "00688", "01109", "00101", "02007", "06098"],
    },
    "消费": {
        "name_cn": "消费",
        "name_en": "Consumer",
        "representatives": ["02020", "02331", "09633", "02313", "00291", "01876", "06862"],
    },
    "能源": {
        "name_cn": "能源",
        "name_en": "Energy",
        "representatives": ["00883", "00857", "00386", "02899", "01347", "01088"],
    },
    "医药": {
        "name_cn": "医药",
        "name_en": "Healthcare",
        "representatives": ["02269", "01177", "01801", "06185", "02162", "01093", "06160"],
    },
    "汽车": {
        "name_cn": "汽车",
        "name_en": "Automobiles",
        "representatives": ["01211", "00175", "02015", "09863", "09866", "02333"],
    },
    "电信": {
        "name_cn": "电信",
        "name_en": "Telecommunications",
        "representatives": ["00941", "00728", "00762", "00788", "06823"],
    },
    "公用事业": {
        "name_cn": "公用事业",
        "name_en": "Utilities",
        "representatives": ["00002", "00003", "00006", "00066", "01038"],
    },
    "原材料": {
        "name_cn": "原材料",
        "name_en": "Materials",
        "representatives": ["02899", "02600", "03993", "01208", "01818"],
    },
    "工业": {
        "name_cn": "工业",
        "name_en": "Industrials",
        "representatives": ["00175", "00388", "00669", "02338", "01138"],
    },
    "综合": {
        "name_cn": "综合企业",
        "name_en": "Conglomerates",
        "representatives": ["00001", "00019", "00267", "00027", "00656"],
    },
}


# ── 港股通标的（沪港通+深港通）──────────────────────
# 常用港股通标的
HK_STOCK_CONNECT = [
    # 科技
    "00700", "09988", "03690", "01810", "09618", "09999",
    "09888", "02015", "00136", "03888",
    # 金融
    "00388", "01299", "02318", "02628", "03968", "01398",
    "00939", "01288", "01339", "02601",
    # 消费
    "02020", "02331", "09633", "02313", "01876", "06862",
    "00291", "00168", "01044", "09698",
    # 医药
    "02269", "01177", "01801", "06185", "02162", "01093",
    "06160", "02196", "02005", "00013",
    # 能源
    "00883", "00857", "00386", "01088", "01171", "01898",
    # 汽车
    "01211", "00175", "09863", "09866", "02333", "00179",
    # 地产
    "00016", "00688", "01109", "02007", "06098",
    # 电信
    "00941", "00728", "00762", "00788",
    # 公用事业
    "00002", "00003", "00006", "01038", "00066",
    # 工业
    "00669", "02338", "01138", "02018", "00316",
]


class HkMarketData:
    """
    港股市场数据获取。

    使用腾讯 qt.gtimg.cn 的 r_hk 前缀获取实时行情。
    使用东方财富 push2 API 获取全市场列表。
    """

    @staticmethod
    def parse_realtime(code: str, raw_fields: list) -> Dict:
        """
        解析腾讯港股行情字段。

        腾讯港股响应格式（~ 分隔）：
          [0]=市场, [1]=名称, [3]=现价, [4]=昨收, [5]=今开,
          [6]=成交量, [31]=涨跌额, [32]=涨跌幅, [33]=最高, [34]=最低,
          [38]=成交额, [46]=货币, [47]=市值
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
                "market_cap": safe_float(raw_fields[47]) if len(raw_fields) > 47 else 0,
                "currency": raw_fields[46] if len(raw_fields) > 46 else "HKD",
                "market": "hk",
            }
        except Exception as e:
            return make_result(ok=False, error=f"港股行情解析失败: {e}", code=code)

    @staticmethod
    def fetch_all_hk_stocks(force_update: bool = False) -> List[Dict]:
        """
        获取港股全市场列表。

        数据源: 东方财富 push2 港股板 (m:128+t:3)
        v8.0: 加翻页循环（此前单页 pz=5000 可能拉不全）。
        """
        import urllib.request
        import ssl
        import time as _time

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }

        def _parse(diff):
            return [
                {
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": safe_float(item.get("f2", 0)),
                    "change_pct": safe_float(item.get("f3", 0)),
                }
                for item in (diff or [])
            ]

        def _fetch_page(pn: int, pz: int = 5000):
            url = (
                "https://push2.eastmoney.com/api/qt/clist/get?"
                f"fid=f3&po=1&pz={pz}&pn={pn}&np=1&fltt=2&invt=2&"
                "fs=m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2"
                "&fields=f2,f3,f12,f14,f15,f16,f17,f18,f20,f21"
            )
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))

        all_stocks = []
        try:
            data = _fetch_page(1)
            total = (data.get("data") or {}).get("total", 0) or 0
            all_stocks.extend(_parse((data.get("data") or {}).get("diff")))
            pz = 5000
            total_pages = (total + pz - 1) // pz if total else 1
            for pn in range(2, total_pages + 1):
                try:
                    d = _fetch_page(pn, pz)
                    all_stocks.extend(_parse((d.get("data") or {}).get("diff")))
                    _time.sleep(0.3)
                except Exception:
                    break
            return all_stocks
        except Exception as e:
            print(f"[HkMarketData] 获取港股列表失败: {e}")
            return []

    @staticmethod
    def get_connect_stocks() -> List[str]:
        """返回港股通标的列表"""
        return HK_STOCK_CONNECT

    @staticmethod
    def get_sector_map() -> Dict:
        """返回港股行业分类映射"""
        return HK_SECTOR_MAP

    @staticmethod
    def get_sector_representatives(sector_name: str) -> List[str]:
        """获取指定行业的代表股"""
        sector = HK_SECTOR_MAP.get(sector_name, {})
        return sector.get("representatives", [])
