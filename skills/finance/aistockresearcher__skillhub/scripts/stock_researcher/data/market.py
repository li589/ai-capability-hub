#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据获取
Market Data Fetching
腾讯财经行情API
"""

import re
import ssl
import time
import json
import urllib.request
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from .market_classifier import MarketClassifier, TENCENT_FIELD_MAP
from .errors import safe_float

# 尝试导入crawl_utils
try:
    from crawl_utils import safe_request
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False


def _retry_request(url: str, headers: dict = None, timeout: int = 8,
                   max_retries: int = 3, ctx: ssl.SSLContext = None) -> bytes:
    """带重试和指数退避的网络请求"""
    headers = headers or {}
    last_err = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait)
    raise last_err


class MarketData:
    """
    市场数据获取

    数据来源：腾讯财经
    - 实时行情: https://qt.gtimg.cn/q=sh600519
    - 历史K线: https://web.ifzq.gtimg.cn/appstock/app/fqkline/get
    """

    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def safe_float(self, v, default=0.0):
        """安全浮点数转换 — 委托到统一的 safe_float"""
        return safe_float(v, default)

    def fetch_realtime(self, codes: List[str]) -> Dict[str, Dict]:
        """
        获取实时行情

        Args:
            codes: 股票代码列表，如 ["600519", "000858"]

        Returns:
            Dict[code, data]: 股票代码 -> 数据字典
        """
        if not codes:
            return {}

        # 构建腾讯行情URL（v6.0: 支持多市场）
        ts_list = []
        code_market_map = {}  # tencent_code -> original_code
        for c in codes:
            try:
                tc = MarketClassifier.to_tencent_code(c)
                ts_list.append(tc)
                code_market_map[tc] = str(c)
            except ValueError:
                # 回退到旧的 A 股逻辑（兼容）
                c = str(c).zfill(6)
                if c.startswith(("6", "5", "9")):
                    tc = f"sh{c}"
                else:
                    tc = f"sz{c}"
                ts_list.append(tc)
                code_market_map[tc] = c

        ts = ",".join(ts_list)
        url = f"https://qt.gtimg.cn/q={ts}&_={int(time.time()*1000)}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://gu.qq.com/"
        }

        try:
            raw = _retry_request(url, headers=headers, timeout=8, ctx=self.ctx)
        except Exception as e:
            print(f"[MarketData] 请求失败: {e}")
            return {}

        try:
            text = raw.decode("gbk", errors="replace")
        except Exception:
            text = raw.decode("utf-8", errors="ignore")

        result = {}
        for line in text.strip().split("\n"):
            m = re.search(r"v_(\w+)=\"(.+?)\"", line)
            if not m:
                continue

            code_with_prefix = m.group(1)
            fields = m.group(2).split("~")

            if len(fields) < 32:
                continue

            # 解析代码（v6.0: 支持多市场格式 sh/sz/r_hk/t_us）
            code = code_market_map.get(code_with_prefix, "")
            if not code:
                # 回退到旧逻辑
                if code_with_prefix.startswith("sh") or code_with_prefix.startswith("sz"):
                    code = code_with_prefix[2:]
                elif code_with_prefix.startswith("r_hk"):
                    code = code_with_prefix[4:]
                elif code_with_prefix.startswith("t_us"):
                    code = code_with_prefix[4:]
                else:
                    code = code_with_prefix

            # 使用市场专属字段映射，避免 A股/港股/美股字段位置错位。
            try:
                market, _, _ = MarketClassifier.classify(code)
            except ValueError:
                market = "cn"
            fmap = TENCENT_FIELD_MAP.get(market, TENCENT_FIELD_MAP["cn"])

            def _field(name: str, default: float = 0.0) -> float:
                idx = fmap.get(name)
                if idx is None or idx >= len(fields):
                    return default
                return self.safe_float(fields[idx])

            result[code] = {
                "name": fields[1] if len(fields) > 1 else "",
                "price": _field("price"),
                "prev_close": _field("prev_close"),
                "open": _field("open"),
                "volume": _field("volume"),
                "amount": _field("amount"),
                "change": _field("change"),
                "change_pct": _field("change_pct"),
                "high": _field("high"),
                "low": _field("low"),
                "turnover": _field("turnover"),
                "pe": _field("pe_ttm"),
                "mkt_cap": _field("market_cap"),
                # 腾讯简易行情不提供主力净流入，置 0 避免把 PE 误读成资金流。
                "main_net_flow": 0.0,
                "source": "tencent",
            }

        return result

    def fetch_history(
        self,
        code: str,
        days: int = 120,
        prefix: str = None
    ) -> Dict[str, List]:
        """
        获取历史K线数据

        Args:
            code: 股票代码，如 "600519"
            days: 获取天数
            prefix: 代码前缀（如 "sh" 或 "sz"）

        Returns:
            Dict: {"dates": [...], "opens": [...], "highs": [...], "lows": [...], "closes": [...], "volumes": [...]}
        """
        # 自动判断前缀（v6.0: 支持多市场）
        if prefix is None:
            try:
                market, exchange, norm = MarketClassifier.classify(code)
                tc = MarketClassifier.to_kline_code(code)
                # K线 API 用完整腾讯代码
                prefix_url = tc
                code_for_key = tc
            except ValueError:
                # 回退到旧 A 股逻辑
                code = str(code).zfill(6)
                if code.startswith(("6", "5", "9")):
                    prefix = "sh"
                else:
                    prefix = "sz"
                prefix_url = f"{prefix}{code}"
                code_for_key = f"{prefix}{code}"
            url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={code_for_key},day,,,{days},qfq&r=0.1"
        else:
            prefix_url = f"{prefix}{str(code).zfill(6)}"
            code_for_key = f"{prefix}{str(code).zfill(6)}"
            url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={code_for_key},day,,,{days},qfq&r=0.1"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://gu.qq.com/"
        }

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, headers=headers, timeout=8)
                if isinstance(raw, tuple):
                    raw = raw[0]
            else:
                raw = _retry_request(url, headers=headers, timeout=8, ctx=self.ctx)

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[MarketData] 获取历史数据失败: {e}")
            return {}

        # 解析K线数据
        try:
            # 解析K线：直接匹配所有["2026-xx-xx",open,close,high,low,vol]格式
            kline_matches = re.findall(
                r'\["(\d{4}-\d{2}-\d{2})",\s*"([\d.]+)",\s*"([\d.]+)",\s*"([\d.]+)",\s*"([\d.]+)",\s*"([\d.]+)"\]',
                raw
            )
            if not kline_matches:
                return {}

            dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
            for m in kline_matches:
                dates.append(m[0])
                opens.append(self.safe_float(m[1]))
                highs.append(self.safe_float(m[2]))
                lows.append(self.safe_float(m[3]))
                closes.append(self.safe_float(m[4]))
                volumes.append(self.safe_float(m[5]))

            return {
                "dates": dates,
                "opens": opens,
                "highs": highs,
                "lows": lows,
                "closes": closes,
                "volumes": volumes
            }
        except Exception as e:
            print(f"[MarketData] 解析K线失败: {e}")
            return {}

    def fetch_histories(
        self,
        codes: List[str],
        days: int = 120
    ) -> Dict[str, Dict]:
        """
        批量获取历史K线（v5.0 升级：并发替代顺序 sleep）

        Args:
            codes: 股票代码列表
            days: 获取天数

        Returns:
            Dict[code, kline_data]
        """
        # v5.0: 使用并发批量获取（max_workers=5 + 0.2s 节流）
        try:
            from .batch import fetch_batch_concurrent
            results = fetch_batch_concurrent(
                self.fetch_history,
                codes,
                max_workers=5,
                sleep_between=0.2,
                timeout=30.0,
                days=days,
            )
            # fetch_batch_concurrent 返回 {code: kline_dict}，已包含成功的结果
            return {k: v for k, v in results.items() if v}
        except ImportError:
            # fallback：原顺序模式（保留作为兜底）
            result = {}
            for code in codes:
                code_str = str(code).zfill(6)
                kline = self.fetch_history(code_str, days)
                if kline:
                    result[code_str] = kline
                time.sleep(0.2)  # 避免请求过快
            return result

    def get_stock_info(self, code: str) -> Dict:
        """
        获取股票基本信息

        Args:
            code: 股票代码

        Returns:
            Dict: 基本信息
        """
        code_str = str(code).zfill(6)
        rt = self.fetch_realtime([code_str])

        if code_str in rt:
            return rt[code_str]

        return {}

    def get_price_volume(self, code: str, days: int = 120) -> Tuple[List[float], List[float]]:
        """
        获取价格和成交量序列（用于技术分析）

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            (closes, volumes)
        """
        kline = self.fetch_history(code, days)
        if kline:
            return kline.get("closes", []), kline.get("volumes", [])
        return [], []
