#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场分类器 (v6.0.0)
====================
统一的市场识别、代码标准化和腾讯 API 前缀映射。
所有多市场模块依赖此文件的分类逻辑。

支持格式：
  - A股: "600519" (6位数字), "sh600519", "cn:600519"
  - 港股: "00700" (5位数字), "hk:00700", "00700.HK"
  - 美股: "AAPL" (字母), "us:AAPL", "AAPL.US"
  - 全球市场 (v6.1): "jp:7203", "kr:005930", "uk:/de:/fr:/au:/in:/tw:/ca:"
  - 商品期货 (v6.1): "gold:comex", "silver:sh", "crude:wti", "fut:aum"
  - 全球指数 (v6.1): "idx:N225", "idx:日经225", "idx:SPX"
"""

import re
from typing import Dict, Optional, Tuple


# ── 腾讯 qt.gtimg.cn 行情字段映射 ──
# 不同市场的 ~ 分隔数据中，字段位置不同
TENCENT_FIELD_MAP: Dict[str, Dict[str, int]] = {
    "cn": {
        "name": 1, "price": 3, "prev_close": 4, "open": 5,
        "volume": 6, "high": 33, "low": 34, "amount": 37,
        "change": 31, "change_pct": 32, "turnover": 38,
        "market_cap": 45, "pe_ttm": 39,
    },
    "hk": {
        "name": 1, "price": 3, "prev_close": 4, "open": 5,
        "volume": 6, "high": 33, "low": 34, "amount": 38,
        "change": 31, "change_pct": 32, "turnover": 39,
        "market_cap": 47, "currency": 46,
    },
    "us": {
        "name": 1, "price": 3, "prev_close": 4, "open": 5,
        "volume": 6, "high": 33, "low": 34, "amount": 38,
        "change": 31, "change_pct": 32, "market_cap": 53,
        "currency": 47, "pe_ttm": 39,
    },
}


class MarketClassifier:
    """
    统一市场分类器。

    用法:
        mc = MarketClassifier
        market, exchange, norm = mc.classify("600519")  # ("cn", "sh", "600519")
        market, exchange, norm = mc.classify("00700")   # ("hk", "hk", "00700")
        market, exchange, norm = mc.classify("AAPL")    # ("us", "us", "AAPL")
        tc = mc.to_tencent_code("00700")                # "r_hk00700"
    """

    # ── 市场识别模式 ──
    # A股: 6位数字，1/2/3/4/6/8/9 开头
    RE_ASHARE = re.compile(r'^[12345689]\d{5}$')
    # A股带前缀: sh600xxx 或 sz000xxx
    RE_ASHARE_PREFIX = re.compile(r'^(sh|sz)(\d{6})$', re.IGNORECASE)
    # 港股: 5位数字（部分四位数需补零）
    RE_HK = re.compile(r'^\d{4,5}$')
    # 港股带后缀: 00700.HK
    RE_HK_SUFFIX = re.compile(r'^(\d{4,5})\.HK$', re.IGNORECASE)
    # 美股: 纯字母 1-5 位
    RE_US = re.compile(r'^[A-Z]{1,5}$', re.IGNORECASE)
    # 美股带后缀: AAPL.US
    RE_US_SUFFIX = re.compile(r'^([A-Z]{1,5})\.(US|NYSE|NASDAQ)$', re.IGNORECASE)
    # v6.1: 全球市场前缀: jp:/kr:/uk:/de:/fr:/au:/in:/tw:/ca:
    RE_GLOBAL_PREFIX = re.compile(
        r'^(jp|kr|uk|de|fr|au|in|tw|ca):(.+)$', re.IGNORECASE)
    # v6.1: 商品期货前缀: gold:/silver:/crude:/fut:
    RE_FUT_PREFIX = re.compile(r'^(gold|silver|crude|fut):(.+)$', re.IGNORECASE)
    # v6.1: 指数前缀: idx:
    RE_IDX_PREFIX = re.compile(r'^idx:(.+)$', re.IGNORECASE)

    # v6.1 新市场集合（走东方财富数据源）
    GLOBAL_MARKET_CODES = frozenset(
        ("jp", "kr", "uk", "de", "fr", "au", "in", "tw", "ca",
         "gold", "silver", "crude", "fut", "idx"))

    @staticmethod
    def classify(code: str) -> Tuple[str, str, str]:
        """
        识别市场类型。

        Args:
            code: 原始代码输入（支持多种格式）

        Returns:
            Tuple[str, str, str]: (market, exchange, normalized_code)
            market: "cn" | "hk" | "us" | "jp" | "kr" | "uk" | "de" | "fr"
                    | "au" | "in" | "tw" | "ca" | "gold" | "silver"
                    | "crude" | "fut" | "idx"
            exchange: "sh" | "sz" | "hk" | "us" | 市场码 | 期货品种(comex/sh/wti)
            normalized_code: 标准化后的代码

        Raises:
            ValueError: 无法识别市场
        """
        code = str(code).strip().upper()

        # 0. v6.1 全球市场显式前缀（必须在纯字母识别之前）
        m = MarketClassifier.RE_IDX_PREFIX.match(code)
        if m:
            # 指数别名: idx:N225 / idx:日经225 → ("idx", "em", "N225")
            return ("idx", "em", m.group(1).strip())
        m = MarketClassifier.RE_FUT_PREFIX.match(code)
        if m:
            # 商品期货: gold:comex → ("gold", "comex", "COMEX")
            fut_market = m.group(1).lower()
            variant = m.group(2).strip().upper()
            return (fut_market, variant.lower() or "main", variant)
        m = MarketClassifier.RE_GLOBAL_PREFIX.match(code)
        if m:
            # 非美个股: jp:7203 → ("jp", "jp", "7203")
            gmarket = m.group(1).lower()
            return (gmarket, gmarket, m.group(2).strip())

        # 1. 显式市场前缀: hk:xxx, us:xxx, cn:xxx
        if code.lower().startswith("hk:"):
            return MarketClassifier._parse_hk(code[3:])
        if code.lower().startswith("us:"):
            return MarketClassifier._parse_us(code[3:])
        if code.lower().startswith("cn:"):
            return MarketClassifier._parse_cn(code[3:])

        # 2. 带后缀格式: 00700.HK, AAPL.US
        m = MarketClassifier.RE_HK_SUFFIX.match(code)
        if m:
            return MarketClassifier._parse_hk(m.group(1))
        m = MarketClassifier.RE_US_SUFFIX.match(code)
        if m:
            return MarketClassifier._parse_us(m.group(1))

        # 3. A股带前缀: sh600519
        m = MarketClassifier.RE_ASHARE_PREFIX.match(code)
        if m:
            return MarketClassifier._parse_cn(code)

        # 4. 纯代码格式识别
        if MarketClassifier.RE_US.match(code):
            return MarketClassifier._parse_us(code)
        if MarketClassifier.RE_ASHARE.match(code):
            return MarketClassifier._parse_cn(code)
        if MarketClassifier.RE_HK.match(code):
            return MarketClassifier._parse_hk(code)

        raise ValueError(f"无法识别市场: {code}。支持格式: 600519, hk:00700, us:AAPL, "
                         f"idx:N225, gold:comex, jp:7203")

    @staticmethod
    def _parse_cn(code: str) -> Tuple[str, str, str]:
        """解析 A 股代码"""
        # 去掉 sh/sz 前缀
        code = re.sub(r'^(sh|sz)', '', code, flags=re.IGNORECASE)
        code = code.zfill(6)
        if code[0] in "5689":
            exchange = "sh"
        elif code[0] in "01234":
            exchange = "sz"
        else:
            exchange = "sh"  # fallback
        return ("cn", exchange, code)

    @staticmethod
    def _parse_hk(code: str) -> Tuple[str, str, str]:
        """解析港股代码"""
        code = code.zfill(5)
        return ("hk", "hk", code)

    @staticmethod
    def _parse_us(code: str) -> Tuple[str, str, str]:
        """解析美股代码"""
        code = code.upper().strip()
        return ("us", "us", code)

    @staticmethod
    def to_tencent_code(code: str) -> str:
        """
        转换为腾讯 qt.gtimg.cn 行情 API 格式。

        Examples:
            "600519" → "sh600519"
            "00700" → "r_hk00700"
            "AAPL" → "t_usAAPL"
        """
        market, exchange, norm = MarketClassifier.classify(code)
        if market == "cn":
            return f"{exchange}{norm}"
        elif market == "hk":
            return f"r_{exchange}{norm}"
        elif market == "us":
            return f"t_{exchange}{norm}"
        raise ValueError(f"Unknown market: {market}")

    @staticmethod
    def to_kline_code(code: str) -> str:
        """
        转换为腾讯 K 线 API 格式。

        注意：K线接口（web.ifzq.gtimg.cn）与行情接口（qt.gtimg.cn）前缀不同：
        行情用 r_hk/t_us，K线用 hk/us（实测 r_hk/t_us 在 K线接口返回 param error）。

        Examples:
            "600519" → "sh600519"
            "00700" → "hk00700"
            "AAPL" → "usAAPL"
        """
        market, exchange, norm = MarketClassifier.classify(code)
        if market == "cn":
            return f"{exchange}{norm}"
        elif market == "hk":
            return f"hk{norm}"
        elif market == "us":
            return f"us{norm}"
        return MarketClassifier.to_tencent_code(code)

    @staticmethod
    def to_eastmoney_secid(code: str) -> Optional[str]:
        """
        转换为东方财富 secid（v6.1 全球市场）。

        映射规则：
            - 美股: "AAPL" → "105.AAPL"
            - A股: "600519" → "1.600519", "000001" → "0.000001"
            - 指数: "idx:N225" → "100.N225"（别名表查询）
            - 商品期货: "gold:comex" → "101.GC00Y", "silver:sh" → "113.agm",
              "crude:wti" → "102.CL00Y", "fut:aum" → "113.aum"

        Returns:
            secid 字符串；港股（继续走腾讯）及无法映射时返回 None。
            非美个股（jp:7203 等）返回 None —— 东财免费接口覆盖有限，
            需由 global_market 运行时探测候选前缀。
        """
        from .global_market import GLOBAL_INDICES, _COMMODITY_VARIANTS  # 延迟导入避免循环
        market, exchange, norm = MarketClassifier.classify(code)
        if market == "us":
            return f"105.{norm}"
        if market == "cn":
            return f"1.{norm}" if exchange == "sh" else f"0.{norm}"
        if market == "idx":
            return GLOBAL_INDICES.get(norm.lower())
        if market in ("gold", "silver", "crude"):
            return _COMMODITY_VARIANTS.get(market, {}).get(norm.lower())
        if market == "fut":
            return GLOBAL_INDICES.get(norm.lower())
        return None  # hk / 非美个股

    @staticmethod
    def get_field(code: str, field_name: str, raw_fields: list) -> Optional[float]:
        """
        从腾讯行情原始字段列表中按市场提取指定字段。
        自动处理市场间字段位置差异。

        Args:
            code: 股票代码
            field_name: 字段名 (对应 TENCENT_FIELD_MAP)
            raw_fields: 腾讯 API 返回的 ~ 分隔字段列表

        Returns:
            float or None
        """
        try:
            market, _, _ = MarketClassifier.classify(code)
        except ValueError:
            market = "cn"

        field_map = TENCENT_FIELD_MAP.get(market, TENCENT_FIELD_MAP["cn"])
        idx = field_map.get(field_name)
        if idx is None or idx >= len(raw_fields):
            return None

        val = raw_fields[idx]
        if not val or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize(code: str) -> str:
        """
        标准化用户输入为规范格式。

        Returns:
            "market:code" 格式，如 "cn:600519", "hk:00700", "us:AAPL"
        """
        market, _, norm = MarketClassifier.classify(code)
        return f"{market}:{norm}"

    @staticmethod
    def get_market_config(code: str) -> dict:
        """
        获取市场配置信息（交易时间、币种、时区、推荐指数）。

        Args:
            code: 任何可识别的股票/指数/商品代码

        Returns:
            {"market": str, "name": str, "currency": str, "timezone": str,
             "trading_hours": str, "index_code": str}
        """
        from .global_market import GLOBAL_MARKETS as GM  # 延迟导入避免循环
        try:
            market, _, _ = MarketClassifier.classify(code)
        except ValueError:
            market = "cn"

        # 先从本模块的 MARKETS（基本三市场）
        if market in ("cn", "hk", "us"):
            cfg = dict(MARKETS.get(market, {}))
            cfg["market"] = market
            cfg["trading_hours"] = {
                "cn": "9:30-15:00", "hk": "9:30-16:00", "us": "9:30-16:00"
            }.get(market, "")
            cfg["index_code"] = {
                "cn": "sh000001", "hk": "100.HSI", "us": "100.SPX"
            }.get(market, "")
            return cfg

        # 再从 global_market 的 GLOBAL_MARKETS
        gm_cfg = GM.get(market, {})
        if gm_cfg:
            return {"market": market, **gm_cfg}

        return {"market": market, "name": market, "currency": "USD",
                "timezone": "UTC", "trading_hours": "", "index_code": ""}

    @staticmethod
    def is_valid(code: str) -> bool:
        """检查代码是否可被识别"""
        try:
            MarketClassifier.classify(code)
            return True
        except ValueError:
            return False


# ── 便捷函数 ──

def detect_market(code: str) -> str:
    """便捷函数：返回市场代码"""
    market, _, _ = MarketClassifier.classify(code)
    return market


def normalize_code(code: str) -> str:
    """便捷函数：标准化代码"""
    return MarketClassifier.normalize(code)
