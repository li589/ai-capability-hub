#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球市场数据层 (v6.1.0)
========================
在 A股/港股/美股（腾讯接口）之外，扩展全球主流市场与商品期货行情。

数据源：东方财富 push2 系列 API（免费、无需 Key）
  - 实时行情: push2.eastmoney.com / push2delay.eastmoney.com（多主机轮换）
  - K线历史: push2his.eastmoney.com

覆盖范围（secid 均经实测，2026-07）：
  - 全球指数: 日经225(100.N225) 韩国KOSPI(100.KS11) 英国富时100(100.FTSE)
    德国DAX(100.GDAXI) 法国CAC40(100.FCHI) 澳洲ASX200(100.AS51)
    台湾加权(100.TWII) 印度SENSEX(100.SENSEX) 加拿大TSX(100.TSX)
    恒生(100.HSI) 国企指数(100.HSCEI) 标普/纳指/道指 A股三大指数
  - 商品期货: COMEX黄金(101.GC00Y) COMEX白银(101.SI00Y)
    NYMEX WTI原油(102.CL00Y) 沪金主连(113.aum) 沪银主连(113.agm)

已实测不可用的 secid（勿再尝试）：
  - 100.TWSE（台湾加权正确 secid 是 100.TWII）
  - 101.CL00Y / 102.B00Y（WTI 正确 secid 是 102.CL00Y，布伦特无免费源）
  - 113.sc0 / 112.sc0 / 113.scm（INE 原油主连免费接口无数据）

个股限制（重要）：
  东财免费接口对非美个股覆盖极有限。实测 105./116./155. 前缀查询
  日本 7203 均返回空数据。因此对 jp:/kr:/uk: 等个股代码，本模块会
  运行时探测候选前缀，均无数据时返回带明确错误说明的 dict：
      {"error": "该市场暂不支持个股行情，可使用指数: idx:N225"}
  指数与期货不受此限制。

限流注意：东财限流激进，连续快速请求会临时封 IP。本模块内置
  多主机轮换 + 全局节流(≥1.2s) + 指数退避重试(3次, 1/2/4s)。
"""

import json
import re
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional

from .errors import create_ssl_context, make_headers, safe_float


# ── 全球市场配置 ──────────────────────────────
# 市场代码 → {名称, 币种, 主要指数 secid, Yahoo 风格代码示例}
GLOBAL_MARKETS: Dict[str, Dict[str, str]] = {
    "jp": {"name": "日本", "currency": "JPY", "index_secid": "100.N225",
           "yahoo_example": "7203.T"},
    "kr": {"name": "韩国", "currency": "KRW", "index_secid": "100.KS11",
           "yahoo_example": "005930.KS"},
    "uk": {"name": "英国", "currency": "GBP", "index_secid": "100.FTSE",
           "yahoo_example": "HSBA.L"},
    "de": {"name": "德国", "currency": "EUR", "index_secid": "100.GDAXI",
           "yahoo_example": "SAP.DE"},
    "fr": {"name": "法国", "currency": "EUR", "index_secid": "100.FCHI",
           "yahoo_example": "MC.PA"},
    "au": {"name": "澳大利亚", "currency": "AUD", "index_secid": "100.AS51",
           "yahoo_example": "BHP.AX"},
    "in": {"name": "印度", "currency": "INR", "index_secid": "100.SENSEX",
           "yahoo_example": "RELIANCE.NS"},
    "tw": {"name": "台湾", "currency": "TWD", "index_secid": "100.TWII",
           "yahoo_example": "2330.TW"},
    "ca": {"name": "加拿大", "currency": "CAD", "index_secid": "100.TSX",
           "yahoo_example": "RY.TO"},
    "gold": {"name": "黄金", "currency": "USD", "index_secid": "101.GC00Y",
             "yahoo_example": "GC=F"},
    "silver": {"name": "白银", "currency": "USD", "index_secid": "101.SI00Y",
               "yahoo_example": "SI=F"},
    "crude": {"name": "原油", "currency": "USD", "index_secid": "102.CL00Y",
              "yahoo_example": "CL=F"},
}


# ── 全球指数/期货别名表 ──────────────────────────
# 用户友好名（小写）→ 东财 secid
GLOBAL_INDICES: Dict[str, str] = {
    # A股指数
    "上证指数": "1.000001", "上证": "1.000001", "沪指": "1.000001",
    "sh000001": "1.000001",
    "深证成指": "0.399001", "深成指": "0.399001", "sz399001": "0.399001",
    "创业板指": "0.399006", "创业板": "0.399006", "sz399006": "0.399006",
    # 港股指数
    "恒生指数": "100.HSI", "恒生": "100.HSI", "hsi": "100.HSI",
    "国企指数": "100.HSCEI", "hscei": "100.HSCEI",
    # 美股指数
    "标普500": "100.SPX", "标普": "100.SPX", "spx": "100.SPX",
    "sp500": "100.SPX",
    "纳斯达克": "100.NDX", "纳指": "100.NDX", "ndx": "100.NDX",
    "nasdaq": "100.NDX",
    "道琼斯": "100.DJIA", "道指": "100.DJIA", "djia": "100.DJIA",
    "dow": "100.DJIA",
    # 亚太/欧洲/其他市场指数
    "日经225": "100.N225", "日经": "100.N225", "n225": "100.N225",
    "nikkei": "100.N225",
    "韩国kospi": "100.KS11", "kospi": "100.KS11", "ks11": "100.KS11",
    "英国富时100": "100.FTSE", "富时100": "100.FTSE", "ftse": "100.FTSE",
    "ftse100": "100.FTSE",
    "德国dax": "100.GDAXI", "dax": "100.GDAXI", "gdaxi": "100.GDAXI",
    "法国cac40": "100.FCHI", "cac40": "100.FCHI", "fchi": "100.FCHI",
    "澳洲asx200": "100.AS51", "asx200": "100.AS51", "as51": "100.AS51",
    "澳大利亚标普200": "100.AS51",
    "台湾加权": "100.TWII", "台股加权": "100.TWII", "twii": "100.TWII",
    "twse": "100.TWII",
    "印度sensex": "100.SENSEX", "sensex": "100.SENSEX",
    "孟买sensex": "100.SENSEX",
    "加拿大tsx": "100.TSX", "tsx": "100.TSX",
    # COMEX 商品期货
    "comex黄金": "101.GC00Y", "黄金": "101.GC00Y", "gold": "101.GC00Y",
    "gc": "101.GC00Y",
    "comex白银": "101.SI00Y", "白银": "101.SI00Y", "silver": "101.SI00Y",
    "si": "101.SI00Y",
    "nymex原油": "102.CL00Y", "wti原油": "102.CL00Y", "wti": "102.CL00Y",
    "crude": "102.CL00Y", "cl": "102.CL00Y",
    # 国内商品期货
    "沪金": "113.aum", "沪金主连": "113.aum", "aum": "113.aum",
    "沪银": "113.agm", "沪银主连": "113.agm", "agm": "113.agm",
}


# ── secid → 市场/币种 元数据（由别名表反推） ──────
_SECID_META: Dict[str, Dict[str, str]] = {
    "1.000001": {"market": "cn", "currency": "CNY"},
    "0.399001": {"market": "cn", "currency": "CNY"},
    "0.399006": {"market": "cn", "currency": "CNY"},
    "100.HSI": {"market": "hk", "currency": "HKD"},
    "100.HSCEI": {"market": "hk", "currency": "HKD"},
    "100.SPX": {"market": "us", "currency": "USD"},
    "100.NDX": {"market": "us", "currency": "USD"},
    "100.DJIA": {"market": "us", "currency": "USD"},
    "100.N225": {"market": "jp", "currency": "JPY"},
    "100.KS11": {"market": "kr", "currency": "KRW"},
    "100.FTSE": {"market": "uk", "currency": "GBP"},
    "100.GDAXI": {"market": "de", "currency": "EUR"},
    "100.FCHI": {"market": "fr", "currency": "EUR"},
    "100.AS51": {"market": "au", "currency": "AUD"},
    "100.TWII": {"market": "tw", "currency": "TWD"},
    "100.SENSEX": {"market": "in", "currency": "INR"},
    "100.TSX": {"market": "ca", "currency": "CAD"},
    "101.GC00Y": {"market": "gold", "currency": "USD"},
    "101.SI00Y": {"market": "silver", "currency": "USD"},
    "102.CL00Y": {"market": "crude", "currency": "USD"},
    "113.aum": {"market": "gold", "currency": "CNY"},
    "113.agm": {"market": "silver", "currency": "CNY"},
}


# ── 商品期货前缀 → secid 映射 ─────────────────────
_COMMODITY_VARIANTS: Dict[str, Dict[str, str]] = {
    "gold": {"comex": "101.GC00Y", "gc": "101.GC00Y", "": "101.GC00Y",
             "sh": "113.aum", "shfe": "113.aum", "aum": "113.aum"},
    "silver": {"comex": "101.SI00Y", "si": "101.SI00Y", "": "101.SI00Y",
               "sh": "113.agm", "shfe": "113.agm", "agm": "113.agm"},
    "crude": {"wti": "102.CL00Y", "cl": "102.CL00Y", "": "102.CL00Y"},
}

# 非美个股 secid 候选前缀（实测覆盖有限，运行时探测）
_STOCK_PREFIX_CANDIDATES = ("116.", "105.", "155.")

# 个股 secid 探测缓存: (market, code) → secid or None
_stock_secid_cache: Dict[tuple, Optional[str]] = {}


# ═══════════════ 东财统一请求客户端 ═══════════════

class EastMoneyClient:
    """
    东方财富 push2 API 统一客户端。

    特性：
      - 多主机轮换（push2delay ↔ push2），单主机故障自动切换
      - 全局节流：距上次请求 ≥1.2s（类级别，所有实例共享）
      - 指数退避重试：3 次，等待 1/2/4s
      - 自动缩放：按 f59（小数位数）还原真实价格
    """

    QUOTE_HOSTS = ("push2delay.eastmoney.com", "push2.eastmoney.com")
    # K线主机 + 编号镜像（push2his 限流封 IP 时自动切换）
    KLINE_HOSTS = ("push2his.eastmoney.com",
                   "92.push2his.eastmoney.com",
                   "1.push2his.eastmoney.com")
    MIN_INTERVAL = 1.2
    RETRIES = 3

    QUOTE_FIELDS = "f43,f44,f45,f46,f47,f57,f58,f59,f60,f170"

    _last_request_ts = 0.0  # 类级别节流时间戳

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._ctx = create_ssl_context()
        self._host_idx = 0

    # ── 内部工具 ──
    def _throttle(self):
        """全局限流：保证两次请求间隔 ≥ MIN_INTERVAL"""
        now = time.time()
        wait = EastMoneyClient._last_request_ts + self.MIN_INTERVAL - now
        if wait > 0:
            time.sleep(wait)
        EastMoneyClient._last_request_ts = time.time()

    def _next_host(self) -> str:
        """轮换行情主机"""
        host = self.QUOTE_HOSTS[self._host_idx % len(self.QUOTE_HOSTS)]
        self._host_idx += 1
        return host

    def _get_json(self, url: str, retries: int = None) -> dict:
        """带节流+重试的 GET JSON 请求，失败返回 {}"""
        if retries is None:
            retries = self.RETRIES
        last_err = None
        for attempt in range(retries):
            self._throttle()
            try:
                req = urllib.request.Request(
                    url, headers=make_headers("https://quote.eastmoney.com/"))
                with urllib.request.urlopen(req, timeout=self.timeout,
                                            context=self._ctx) as r:
                    return json.loads(r.read().decode("utf-8", errors="replace"))
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 1s, 2s, 4s
        return {"_error": str(last_err)}

    # ── 实时行情 ──
    def get_quote(self, secid: str) -> dict:
        """
        获取实时行情（自动按 f59 缩放）。

        Returns:
            dict: {name, code, price, prev_close, open, high, low, vol, chg_pct}
            失败或无数据返回 {}
        """
        host = self._next_host()
        url = (f"https://{host}/api/qt/stock/get?secid={secid}"
               f"&fields={self.QUOTE_FIELDS}")
        data = self._get_json(url).get("data")
        if not data or data.get("f43") in (None, "-"):
            return {}
        # f59 = 小数位数，缩放因子 = 10^f59（指数通常 f59=2，期货可能 0/1/3）
        try:
            scale = 10 ** int(data.get("f59", 2))
        except (TypeError, ValueError):
            scale = 100

        def scaled(key):
            v = data.get(key)
            return safe_float(v) / scale if v not in (None, "-") else 0.0

        return {
            "name": data.get("f58", "") or "",
            "code": data.get("f57", "") or secid,
            "price": scaled("f43"),
            "high": scaled("f44"),
            "low": scaled("f45"),
            "open": scaled("f46"),
            "prev_close": scaled("f60"),
            "vol": safe_float(data.get("f47")),
            "chg_pct": safe_float(data.get("f170")) / 100,  # f170=涨跌幅×100
        }

    # ── K线历史 ──
    def get_klines(self, secid: str, days: int = 120) -> List[dict]:
        """
        获取日K历史（前复权）。多主机轮换，单主机被封自动切换。

        Returns:
            [{date, open, close, high, low, vol}]，失败返回 []
        """
        data = None
        for host in self.KLINE_HOSTS:
            url = (f"https://{host}/api/qt/stock/kline/get"
                   f"?secid={secid}&fields1=f1,f2,f3"
                   f"&fields2=f51,f52,f53,f54,f55,f56"
                   f"&klt=101&fqt=1&end=20500101&lmt={days}")
            # 每主机只试 1 次（共 3 主机轮换），避免被封 IP 时雪上加霜
            data = self._get_json(url, retries=1).get("data")
            if data and data.get("klines"):
                break
        if not data:
            return []
        klines = data.get("klines") or []
        result = []
        for line in klines:
            parts = str(line).split(",")
            # f52=open f53=close f54=high f55=low f56=volume
            if len(parts) < 6:
                continue
            result.append({
                "date": parts[0],
                "open": safe_float(parts[1]),
                "close": safe_float(parts[2]),
                "high": safe_float(parts[3]),
                "low": safe_float(parts[4]),
                "vol": safe_float(parts[5]),
            })
        return result


# 模块级共享客户端（复用节流与缓存）
_CLIENT = EastMoneyClient()


# ═══════════════ 代码解析 ═══════════════

_RE_SECID = re.compile(r"^\d+\.[A-Za-z0-9]+$")
_RE_STOCK_PREFIX = re.compile(r"^(jp|kr|uk|de|fr|au|in|tw|ca):(.+)$",
                              re.IGNORECASE)


def _resolve_secid(code: str):
    """
    把用户输入解析为 (secid, market, currency) 或错误 dict。

    支持格式：
      - "idx:N225" / "idx:日经225" / "idx:gold"（别名表查询）
      - "gold:comex" / "gold:sh" / "silver:comex" / "crude:wti" / "fut:aum"
      - "jp:7203" 等非美个股（运行时探测候选前缀，覆盖有限）
      - "100.N225"（直接给出东财 secid）
      - 裸别名如 "日经225"、"spx"
    """
    code = str(code).strip()
    low = code.lower()

    # 1. idx: 别名
    if low.startswith("idx:"):
        alias = low[4:]
        secid = GLOBAL_INDICES.get(alias)
        if not secid:
            return {"error": f"未知指数别名: {alias}。可用示例: idx:N225, "
                             f"idx:SPX, idx:上证指数, idx:gold"}
        meta = _SECID_META.get(secid, {})
        return (secid, meta.get("market", "idx"), meta.get("currency", ""))

    # 2. 商品期货前缀
    for prefix in ("gold", "silver", "crude", "fut"):
        if low.startswith(prefix + ":"):
            variant = low[len(prefix) + 1:]
            if prefix == "fut":
                # fut:xxx 直接走别名表（fut:aum / fut:GC / fut:沪金）
                secid = GLOBAL_INDICES.get(variant)
                if not secid:
                    return {"error": f"未知期货代码: {variant}。可用示例: "
                                     f"gold:comex, silver:comex, crude:wti, "
                                     f"fut:aum, fut:agm"}
            else:
                secid = _COMMODITY_VARIANTS.get(prefix, {}).get(variant)
                if not secid:
                    return {"error": f"{prefix}:{variant} 暂不支持。可用: "
                                     f"gold:comex/gold:sh, silver:comex/silver:sh, "
                                     f"crude:wti（布伦特与INE原油无免费源）"}
            meta = _SECID_META.get(secid, {})
            return (secid, meta.get("market", prefix), meta.get("currency", ""))

    # 3. 非美市场个股
    m = _RE_STOCK_PREFIX.match(code)
    if m:
        market, stock_code = m.group(1).lower(), m.group(2).strip()
        secid = _probe_stock_secid(market, stock_code)
        if not secid:
            idx_alias = _market_index_alias(market)
            return {"error": f"{GLOBAL_MARKETS[market]['name']}市场暂不支持个股行情"
                             f"（东财免费接口未覆盖），可使用指数: idx:{idx_alias}"}
        meta = GLOBAL_MARKETS[market]
        return (secid, market, meta["currency"])

    # 4. 直接 secid
    if _RE_SECID.match(code):
        meta = _SECID_META.get(code, {})
        return (code, meta.get("market", "idx"), meta.get("currency", ""))

    # 5. 裸别名（"日经225"、"spx" 等）
    secid = GLOBAL_INDICES.get(low)
    if secid:
        meta = _SECID_META.get(secid, {})
        return (secid, meta.get("market", "idx"), meta.get("currency", ""))

    return {"error": f"无法识别的全球市场代码: {code}。支持格式: idx:指数名, "
                     f"gold:comex, silver:sh, crude:wti, jp:7203"}


def _market_index_alias(market: str) -> str:
    """市场代码 → 推荐的指数别名（用于错误提示）"""
    return {
        "jp": "N225", "kr": "KS11", "uk": "FTSE", "de": "GDAXI",
        "fr": "FCHI", "au": "AS51", "in": "SENSEX", "tw": "TWII",
        "ca": "TSX",
    }.get(market, "SPX")


def _probe_stock_secid(market: str, stock_code: str) -> Optional[str]:
    """
    运行时探测非美个股的可用 secid 前缀（带缓存）。
    实测东财免费接口对非美个股覆盖极有限，多数返回 None。
    """
    key = (market, stock_code.upper())
    if key in _stock_secid_cache:
        return _stock_secid_cache[key]
    for prefix in _STOCK_PREFIX_CANDIDATES:
        secid = f"{prefix}{stock_code}"
        if _CLIENT.get_quote(secid):
            _stock_secid_cache[key] = secid
            return secid
    _stock_secid_cache[key] = None
    return None


# ═══════════════ 对外接口 ═══════════════

def fetch_global_quote(code: str) -> dict:
    """
    全球市场实时行情。

    Args:
        code: "idx:N225" / "gold:comex" / "jp:7203" / "100.N225" / "日经225"

    Returns:
        与腾讯行情同形状的 dict:
        {name, code, market, price, prev_close, open, high, low, vol,
         chg_pct, currency}
        网络失败返回 {}，不支持的代码返回 {"error": "..."}，绝不抛异常。
    """
    try:
        resolved = _resolve_secid(code)
        if isinstance(resolved, dict):
            return resolved  # {"error": ...}
        secid, market, currency = resolved
        q = _CLIENT.get_quote(secid)
        if not q:
            return {}
        q["market"] = market
        q["currency"] = currency
        return q
    except Exception:
        return {}


def fetch_global_kline(code: str, days: int = 120) -> List[dict]:
    """
    全球市场日K历史。

    Returns:
        [{date, open, close, high, low, vol}]，任何失败返回 []。
    """
    try:
        resolved = _resolve_secid(code)
        if isinstance(resolved, dict):
            return []  # {"error": ...}
        secid, _, _ = resolved
        return _CLIENT.get_klines(secid, days=days)
    except Exception:
        return []


# ═══════════════ v7.0 全球风险偏好与黄金因子 ═══════════════

def get_global_risk_appetite() -> dict:
    """
    获取全球风险偏好评分（基于 VIX + 主要指数联动）。

    数据源：东方财富 push2 API（免费、无 Key）
    指标：VIX、标普500、日经225、恒生指数、美元指数

    Returns:
        {
            "score": -100~+100（正=risk-on，负=risk-off），
            "label": "risk_on"|"mild_risk_on"|"neutral"|"mild_risk_off"|"risk_off",
            "vix": float or None,
            "signals": [{name, chg_pct, contribution}, ...],
            "source_status": "ok"|"partial"|"error"
        }
    """
    # 关键观测指标及其对风险偏好的贡献方向
    indicators = [
        ("100.SPX", "标普500", +1.0, 0.25),     # 涨=risk-on
        ("100.N225", "日经225", +1.0, 0.15),     # 涨=risk-on
        ("100.HSI", "恒生指数", +1.0, 0.15),     # 涨=risk-on
        ("100.GDAXI", "DAX", +1.0, 0.10),        # 涨=risk-on
    ]

    signals = []
    total_score = 0.0
    total_weight = 0.0
    source_status = "ok"
    success_count = 0

    for secid, name, direction, weight in indicators:
        try:
            q = _CLIENT.get_quote(secid)
            if q and q.get("chg_pct", 0) != 0:
                chg = q["chg_pct"]
                # 标准化贡献：涨跌幅 → -100~+100 映射（±3% 映射到 ±100）
                contribution = max(-100, min(100, chg * 33 * direction))
                signals.append({
                    "name": name, "secid": secid, "chg_pct": round(chg, 2),
                    "contribution": round(contribution, 1), "weight": weight,
                })
                total_score += contribution * weight
                total_weight += weight
                success_count += 1
        except Exception:
            pass

    # VIX（恐慌指数，与风险偏好反向：VIX↑ → risk-off）
    vix_val = None
    try:
        vix_q = _CLIENT.get_quote("100.VIX")
        if vix_q:
            vix_val = vix_q.get("price", None)
            if vix_val:
                # VIX 越高 → 越恐慌 → 风险偏好越低
                # VIX<15: +30, 15-20: +10, 20-25: 0, 25-30: -20, >30: -40
                if vix_val < 15:
                    vix_contrib = 30
                elif vix_val < 20:
                    vix_contrib = 10
                elif vix_val < 25:
                    vix_contrib = 0
                elif vix_val < 30:
                    vix_contrib = -20
                else:
                    vix_contrib = -40
                signals.append({
                    "name": "VIX恐慌指数", "secid": "100.VIX",
                    "value": round(vix_val, 2),
                    "contribution": vix_contrib, "weight": 0.20,
                })
                total_score += vix_contrib * 0.20
                total_weight += 0.20
                success_count += 1
    except Exception:
        pass

    if total_weight == 0:
        source_status = "error"
        score = 0
    else:
        score = round(total_score / total_weight)
        if success_count < len(indicators):
            source_status = "partial"

    # 标签映射
    if score > 40:
        label = "risk_on"
    elif score > 15:
        label = "mild_risk_on"
    elif score > -15:
        label = "neutral"
    elif score > -40:
        label = "mild_risk_off"
    else:
        label = "risk_off"

    return {
        "score": score,
        "label": label,
        "vix": vix_val,
        "signals": signals,
        "source_status": source_status,
    }


def analyze_gold_factors() -> dict:
    """
    黄金专用因子分析（用于 gold_factor 预测维度）。

    分析维度：
    1. 美元指数(DXY) — 黄金与美元负相关
    2. 实际利率代理 — VIX 与避险需求
    3. COMEX黄金 vs 沪金价差 — 境内外价差反映人民币预期
    4. 黄金ETF持仓变化代理 — 价格动量

    Returns:
        {
            "score": -100~+100（正=看多黄金），
            "signal": "看多"|"中性"|"看空",
            "factors": [{name, value, contribution, note}, ...],
            "safe_haven_demand": 0~100（避险需求评分），
            "summary": str
        }
    """
    factors = []
    total_score = 0.0

    # 1. 美元指数（DXY，secid=100.DXY）
    try:
        dxy = _CLIENT.get_quote("100.DXY")
        if dxy and dxy.get("chg_pct", 0) != 0:
            dxy_chg = dxy["chg_pct"]
            # 美元涨 → 黄金承压（负相关）
            contrib = -dxy_chg * 20
            factors.append({
                "name": "美元指数", "value": round(dxy_chg, 2),
                "contribution": round(contrib, 1),
                "note": f"DXY {'涨' if dxy_chg > 0 else '跌'}{abs(dxy_chg):.2f}%，"
                        f"黄金{'承压' if dxy_chg > 0 else '受益'}"
            })
            total_score += contrib
    except Exception:
        factors.append({"name": "美元指数", "value": 0, "contribution": 0,
                       "note": "数据不可用"})

    # 2. 黄金自身动量（价格趋势）
    try:
        gold = fetch_global_quote("gold:comex")
        if gold and gold.get("chg_pct", 0) != 0:
            gold_chg = gold["chg_pct"]
            contrib = gold_chg * 5  # 近期涨跌动量
            factors.append({
                "name": "金价动量", "value": round(gold_chg, 2),
                "contribution": round(contrib, 1),
                "note": f"COMEX黄金今日{gold_chg:+.2f}%"
            })
            total_score += contrib
    except Exception:
        pass

    # 3. VIX（恐慌指数 → 避险需求）
    safe_haven = 50  # 默认中性
    try:
        vix_q = _CLIENT.get_quote("100.VIX")
        if vix_q and vix_q.get("price"):
            vix = vix_q["price"]
            # VIX 越高 → 避险需求越强 → 利好黄金
            if vix < 15:
                safe_haven = 20
                sh_contrib = -10
            elif vix < 20:
                safe_haven = 35
                sh_contrib = 0
            elif vix < 25:
                safe_haven = 55
                sh_contrib = 10
            elif vix < 30:
                safe_haven = 75
                sh_contrib = 25
            else:
                safe_haven = 95
                sh_contrib = 40
            factors.append({
                "name": "避险需求(VIX)", "value": round(vix, 2),
                "contribution": sh_contrib,
                "note": f"VIX={vix:.1f}，避险需求{'高' if vix > 25 else '低'}"
            })
            total_score += sh_contrib
    except Exception:
        factors.append({"name": "避险需求(VIX)", "value": 0, "contribution": 0,
                       "note": "数据不可用"})

    # 4. 沪金-COMEX 价差代理（人民币汇率预期）
    try:
        sh_gold = fetch_global_quote("gold:sh")
        comex_gold = fetch_global_quote("gold:comex")
        if sh_gold and comex_gold and sh_gold.get("chg_pct") and comex_gold.get("chg_pct"):
            spread = sh_gold["chg_pct"] - comex_gold["chg_pct"]
            if abs(spread) > 0.5:
                contrib = spread * 5
                note = f"沪金{'强于' if spread > 0 else '弱于'}COMEX，"
                note += "境内需求旺" if spread > 0 else "境外定价主导"
            else:
                contrib = 0
                note = "境内外金价走势一致"
            factors.append({
                "name": "沪金-COMEX价差", "value": round(spread, 2),
                "contribution": round(contrib, 1), "note": note,
            })
            total_score += contrib
    except Exception:
        pass

    # 最终评分
    score = max(-100, min(100, total_score))
    if score > 25:
        signal = "看多"
    elif score > -25:
        signal = "中性"
    else:
        signal = "看空"

    # 生成摘要
    top_factor = max(factors, key=lambda f: abs(f["contribution"])) if factors else None
    summary = f"黄金综合评分{score:+.0f}/100，"
    if top_factor and abs(top_factor["contribution"]) > 5:
        summary += f"主要驱动：{top_factor['note']}"

    return {
        "score": score,
        "signal": signal,
        "factors": factors,
        "safe_haven_demand": safe_haven,
        "summary": summary,
    }


def get_market_correlation(code1: str, code2: str, days: int = 60) -> dict:
    """
    计算两个全球市场标的的滚动相关性。

    Args:
        code1/code2: 全球市场代码（idx:xxx / gold:xxx 等）
        days: 计算窗口

    Returns:
        {"correlation": -1~1, "strength": "强正相关"/"弱正相关"/..., "sample_days": int}
    """
    import math

    k1 = fetch_global_kline(code1, days)
    k2 = fetch_global_kline(code2, days)

    if not k1 or not k2:
        return {"correlation": 0, "strength": "数据不足", "sample_days": 0}

    # 按日期对齐收盘价
    dates1 = {k["date"]: k["close"] for k in k1}
    dates2 = {k["date"]: k["close"] for k in k2}
    common = sorted(set(dates1) & set(dates2))

    if len(common) < 10:
        return {"correlation": 0, "strength": "样本不足", "sample_days": len(common)}

    # 计算日收益率
    rets1 = [dates1[d] / dates1[common[i-1]] - 1 for i, d in enumerate(common) if i > 0]
    rets2 = [dates2[d] / dates2[common[i-1]] - 1 for i, d in enumerate(common) if i > 0]

    n = len(rets1)
    if n < 5:
        return {"correlation": 0, "strength": "样本不足", "sample_days": n}

    # Pearson 相关系数
    mean1 = sum(rets1) / n
    mean2 = sum(rets2) / n
    cov = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(rets1, rets2)) / n
    std1 = math.sqrt(sum((r - mean1) ** 2 for r in rets1) / n)
    std2 = math.sqrt(sum((r - mean2) ** 2 for r in rets2) / n)

    if std1 == 0 or std2 == 0:
        correlation = 0
    else:
        correlation = cov / (std1 * std2)

    # 强度标签
    r = abs(correlation)
    if r > 0.7:
        direction = "强"
    elif r > 0.4:
        direction = "中等"
    elif r > 0.2:
        direction = "弱"
    else:
        direction = "极弱"

    label = f"{direction}{'正' if correlation > 0 else '负'}相关"

    return {
        "correlation": round(correlation, 3),
        "strength": label,
        "sample_days": n,
    }
