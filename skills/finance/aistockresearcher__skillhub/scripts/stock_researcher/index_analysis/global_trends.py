#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全球指数与商品趋势分析 (v6.1 新增)

覆盖 A股/港股/美股/亚太/欧洲主要指数 + 黄金白银原油期货 + 美元指数，
基于东方财富免费接口（国内直连、无需 API Key）：

  - fetch_index_data:     quote + kline（东财，节流>=1.5s + 退避重试<=3次 + 镜像主机轮换）
  - analyze_index:        单指数趋势（12项技术指标复用 scripts/stock_predict.py 的 calc_*，
                          均线多空排列、动量、近5/20日涨跌幅、波动率、关键位）
  - global_market_outlook: 全球全景（强弱排名 + 近60日收益相关性提示，逐个节流，失败跳过）
  - index_forecast:       T+1/T+3/T+5 蒙特卡洛预判（借鉴 fusion/multi_horizon_forecaster 思路，自包含实现）
  - sector_trend_report:  板块趋势报告（调用现有 sector_analysis，叠加政策受益板块）

实测网络结论（2026-07）：
  - 东财限流激进：连续快速请求会临时封 IP 数分钟，务必节流 + 退避。
  - kline 主站 push2his.eastmoney.com 被封时轮换镜像 push2hisdelay.eastmoney.com
    （镜像响应带 UTF-8 BOM；被 WAF 拦截时返回 HTML 首页而非 JSON，需校验）。
  - quote 批量接口 push2delay.eastmoney.com ulist.np/get 稳定，
    fltt=2 时价格已按小数位缩放，无需 f59 处理。
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 复用 scripts/stock_predict.py 的技术指标纯函数 ──────────
SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
try:
    from stock_predict import (
        calc_rsi, calc_macd, calc_boll, calc_kdj, calc_wr, calc_cci,
        calc_mfi, calc_atr, calc_adx, calc_obv,
    )
    _HAS_STOCK_PREDICT = True
except ImportError:   # 内置简化实现兜底
    _HAS_STOCK_PREDICT = False

    def calc_rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50.0
        g = l = 0.0
        for i in range(len(closes) - period, len(closes)):
            d = closes[i] - closes[i - 1]
            if d > 0:
                g += d
            else:
                l += abs(d)
        if l == 0:
            return 50.0 if g == 0 else 100.0
        return 100 - 100 / (1 + g / l)

    def calc_macd(closes, fast=12, slow=26, sig=9):
        if len(closes) < slow + sig:
            return {"dif": 0, "dea": 0, "hist": 0}
        def ema(d, p):
            r = [sum(d[:p]) / p]; m = 2 / (p + 1)
            for i in range(p, len(d)):
                r.append(d[i] * m + r[-1] * (1 - m))
            return r
        ef = ema(closes, fast); es = ema(closes, slow)
        n = min(len(ef), len(es))
        dif = [ef[-n + i] - es[-n + i] for i in range(n)]
        dea = ema(dif, sig)
        return {"dif": round(dif[-1], 4), "dea": round(dea[-1], 4),
                "hist": round((dif[-1] - dea[-1]) * 2, 4)}

    def calc_boll(closes, period=20):
        if len(closes) < period:
            return {"up": 0, "mid": 0, "lo": 0, "w": 0, "pos": 50}
        r = closes[-period:]; mid = sum(r) / period
        std = math.sqrt(sum((x - mid) ** 2 for x in r) / period)
        up = mid + 2 * std; lo = mid - 2 * std
        pos = (closes[-1] - lo) / (up - lo) * 100 if up != lo else 50
        return {"up": round(up, 2), "mid": round(mid, 2), "lo": round(lo, 2),
                "w": round((up - lo) / mid * 100, 2) if mid else 0,
                "pos": round(pos, 1)}

    def calc_kdj(highs, lows, closes, period=9):
        return {"k": 50, "d": 50, "j": 50} if len(closes) < period else \
            {"k": 50.0, "d": 50.0, "j": 50.0}

    def calc_wr(highs, lows, closes, period=14):
        return -50.0

    def calc_cci(highs, lows, closes, period=20):
        return 0.0

    def calc_mfi(highs, lows, closes, volumes, period=14):
        return 50.0

    def calc_atr(highs, lows, closes, period=14):
        return 0.0

    def calc_adx(highs, lows, closes, period=14):
        return {"adx": 0, "pdi": 0, "ndi": 0}

    def calc_obv(closes, volumes):
        return [0.0]


# ── 全球指数/商品全表：别名 -> (secid, 市场, 中文名) ─────────
# secid 均经 push2delay 批量报价实测（2026-07-27）；
# HSTECH 未实测返回，保留并依赖优雅降级。
GLOBAL_INDEX_UNIVERSE: Dict[str, Tuple[str, str, str]] = {
    # A股
    "SHCOMP":  ("1.000001",  "cn", "上证指数"),
    "SZCOMP":  ("0.399001",  "cn", "深证成指"),
    "CHINEXT": ("0.399006",  "cn", "创业板指"),
    "CSI300":  ("1.000300",  "cn", "沪深300"),
    # 港股
    "HSI":     ("100.HSI",   "hk", "恒生指数"),
    "HSCEI":   ("100.HSCEI", "hk", "国企指数"),
    "HSTECH":  ("100.HSTECH", "hk", "恒生科技"),
    # 美股
    "DJIA":    ("100.DJIA",  "us", "道琼斯"),
    "SPX":     ("100.SPX",   "us", "标普500"),
    "NDX":     ("100.NDX",   "us", "纳斯达克"),
    # 亚太
    "N225":    ("100.N225",  "jp", "日经225"),
    "KS11":    ("100.KS11",  "kr", "韩国KOSPI"),
    "TWII":    ("100.TWII",  "tw", "台湾加权"),
    "AS51":    ("100.AS51",  "au", "澳洲标普200"),
    "SENSEX":  ("100.SENSEX", "in", "印度SENSEX"),
    # 欧洲
    "FTSE":    ("100.FTSE",  "uk", "英国富时100"),
    "GDAXI":   ("100.GDAXI", "de", "德国DAX30"),
    "FCHI":    ("100.FCHI",  "fr", "法国CAC40"),
    # 商品期货
    "GOLD":    ("101.GC00Y", "comex", "COMEX黄金"),
    "GOLDCN":  ("113.aum",   "shfe", "沪金主连"),
    "SILVER":  ("101.SI00Y", "comex", "COMEX白银"),
    "OIL":     ("102.CL00Y", "nymex", "NYMEX原油"),
    # 汇率
    "UDI":     ("100.UDI",   "fx", "美元指数"),
}

# 黄金白银原油专题别名
COMMODITY_ALIASES = ["GOLD", "GOLDCN", "SILVER", "OIL"]

# 相关性提示的常用配对（近60日收益相关系数）
CORRELATION_PAIRS = [
    ("NDX", "HSTECH", "纳指 vs 恒生科技（科技联动）"),
    ("HSI", "SHCOMP", "恒生 vs 上证（港股A股联动）"),
    ("GOLD", "UDI", "黄金 vs 美元指数（通常反向）"),
    ("SPX", "N225", "标普 vs 日经（亚太跟随）"),
    ("OIL", "SENSEX", "原油 vs 印度（输入性通胀敏感）"),
]

# ── 东财请求基础设施（节流 + 退避重试 + 镜像主机轮换）───────
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/120.0.0.0 Safari/537.36")
_UT = "fa5fd1943c7b386f172d6893dbfba10b"   # 东财公开 token
_MIN_INTERVAL = 1.6
KLINE_HOSTS = ["push2his.eastmoney.com", "push2hisdelay.eastmoney.com"]
QUOTE_HOSTS = ["push2delay.eastmoney.com", "push2.eastmoney.com"]
_last_req = 0.0


def _throttle(interval: float = _MIN_INTERVAL):
    """请求节流：距上次请求至少 interval 秒（东财限流激进）"""
    global _last_req
    wait = interval - (time.time() - _last_req)
    if wait > 0:
        time.sleep(wait)
    _last_req = time.time()


def _http_json(url: str, timeout: int = 10, retries: int = 3,
               interval: float = _MIN_INTERVAL) -> Optional[dict]:
    """GET 并解析 JSON；被 WAF 拦截返回 HTML 时视为失败；全部失败返回 None"""
    for attempt in range(retries):
        try:
            _throttle(interval)
            req = urllib.request.Request(url, headers={
                "User-Agent": _UA,
                "Referer": "https://quote.eastmoney.com/",
                "Accept": "*/*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            text = raw.decode("utf-8-sig", errors="replace").lstrip()
            if not text.startswith("{"):
                # WAF 拦截会返回 HTML 首页
                raise ValueError("non-JSON response (blocked?)")
            return json.loads(text)
        except Exception:
            if attempt < retries - 1:
                time.sleep(2.0 * (attempt + 1))
    return None


def _to_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A", "null"):
            return default
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


# ── 行情与K线获取 ──────────────────────────────────────────
def fetch_batch_quotes(secids: List[str]) -> Dict[str, Dict]:
    """批量实时报价（一次请求，东财 ulist.np/get，fltt=2 价格已缩放）。

    Returns:
        {secid: {name, price, change_pct, prev_close}}
    """
    if not secids:
        return {}
    out: Dict[str, Dict] = {}
    fields = "f12,f13,f14,f2,f3,f4,f59"
    for host in QUOTE_HOSTS:
        url = (f"https://{host}/api/qt/ulist.np/get?"
               f"secids={','.join(secids)}&fields={fields}&fltt=2&invt=2")
        data = _http_json(url)
        diff = ((data or {}).get("data") or {}).get("diff") or []
        if not diff:
            continue
        for it in diff:
            f13, f12 = it.get("f13"), it.get("f12")
            if f13 is None or not f12:
                continue
            secid = f"{f13}.{f12}"
            price = _to_float(it.get("f2"))
            if price is None:
                continue
            out[secid] = {
                "name": it.get("f14", "") or "",
                "price": price,
                "change_pct": _to_float(it.get("f3")),
                "prev_close": _to_float(it.get("f4")),
            }
        if out:
            break
    return out


def fetch_quote(secid: str) -> Optional[Dict]:
    """单只实时报价；失败时尝试 f59 缩放口径"""
    batch = fetch_batch_quotes([secid])
    if secid in batch:
        return batch[secid]
    # 回退：stock/get 单只接口 + f59 小数位缩放
    fields = "f43,f57,f58,f44,f45,f46,f60,f59,f170"
    for host in QUOTE_HOSTS:
        url = f"https://{host}/api/qt/stock/get?secid={secid}&fields={fields}"
        data = _http_json(url)
        d = (data or {}).get("data")
        if not d:
            continue
        f59 = _to_float(d.get("f59"), 2)
        scale = 10 ** int(f59) if f59 is not None else 100
        price = _to_float(d.get("f43"))
        if price is None:
            continue
        price = price / scale
        return {
            "name": d.get("f58", "") or "",
            "price": round(price, 4),
            "change_pct": (_to_float(d.get("f170")) or 0) / 100,
            "prev_close": (_to_float(d.get("f60")) or 0) / scale,
        }
    return None


def fetch_kline(secid: str, days: int = 120,
                interval: float = _MIN_INTERVAL) -> List[Dict]:
    """日K线（前复权），主站/镜像主机轮换。失败返回 []。

    Args:
        secid: 东财 secid
        days: 天数
        interval: 请求节流间隔（全景批量场景传 2.0）

    Returns:
        [{date, open, close, high, low, vol}, ...] 按日期升序
    """
    fields1, fields2 = "f1,f2,f3", "f51,f52,f53,f54,f55,f56"
    for host in KLINE_HOSTS:
        url = (f"https://{host}/api/qt/stock/kline/get?secid={secid}"
               f"&ut={_UT}&fields1={fields1}&fields2={fields2}"
               f"&klt=101&fqt=1&end=20500101&lmt={days}")
        data = _http_json(url, interval=interval)
        d = (data or {}).get("data")
        klines = (d or {}).get("klines") or []
        if not klines:
            continue
        out = []
        for row in klines:
            parts = row.split(",")
            if len(parts) < 6:
                continue
            out.append({
                "date": parts[0],
                "open": _to_float(parts[1], 0),
                "close": _to_float(parts[2], 0),
                "high": _to_float(parts[3], 0),
                "low": _to_float(parts[4], 0),
                "vol": _to_float(parts[5], 0),
            })
        if out:
            return out[-days:]
    return []


def fetch_index_data(secid: str, days: int = 120) -> Dict:
    """quote + kline 合并获取；任一失败优雅降级并标注 source_status"""
    quote = fetch_quote(secid) or {}
    kline = fetch_kline(secid, days=days)
    return {
        "secid": secid,
        "name": quote.get("name", ""),
        "price": quote.get("price", 0),
        "change_pct": quote.get("change_pct"),
        "prev_close": quote.get("prev_close"),
        "kline": kline,
        "source_status": {
            "quote": "ok" if quote else "empty",
            "kline": "ok" if kline else "empty",
        },
    }


def _resolve(alias_or_secid: str) -> Tuple[str, str, str, str]:
    """别名或 secid → (alias, secid, market, name)"""
    key = str(alias_or_secid).strip().upper()
    if key in GLOBAL_INDEX_UNIVERSE:
        secid, market, name = GLOBAL_INDEX_UNIVERSE[key]
        return key, secid, market, name
    # 直接传 secid
    for alias, (secid, market, name) in GLOBAL_INDEX_UNIVERSE.items():
        if str(alias_or_secid).strip() == secid:
            return alias, secid, market, name
    return key, str(alias_or_secid).strip(), "unknown", str(alias_or_secid)


def _ma(data: List[float], period: int) -> Optional[float]:
    if len(data) < period:
        return None
    return sum(data[-period:]) / period


# ── 单指数趋势分析 ─────────────────────────────────────────
def analyze_index(alias_or_secid: str, days: int = 120,
                  data: Optional[Dict] = None) -> Dict:
    """单指数趋势分析：12项技术指标 + 均线多空 + 动量 + 波动率 + 关键位。

    Args:
        alias_or_secid: GLOBAL_INDEX_UNIVERSE 别名或东财 secid
        days: K线天数
        data: 可选，预取的 fetch_index_data 结果（避免重复请求）

    Returns:
        {alias, secid, name, market, price, change_pct,
         trend(强势上涨/上涨/震荡/下跌/强势下跌), score(-100~+100),
         technical{...}, key_levels{支撑,压力}, signals[...],
         degraded(K线缺失时True), source_status}
    """
    alias, secid, market, name = _resolve(alias_or_secid)
    if data is None:
        data = fetch_index_data(secid, days=days)
    if data.get("name"):
        name = data["name"]
    kline = data.get("kline") or []
    price = data.get("price") or 0
    change_pct = data.get("change_pct")

    result = {
        "alias": alias, "secid": secid, "name": name, "market": market,
        "price": price, "change_pct": change_pct,
        "trend": "震荡", "score": 0.0,
        "technical": {}, "key_levels": {}, "signals": [],
        "degraded": False, "source_status": data.get("source_status", {}),
    }

    if not kline:
        # K线缺失：仅用当日涨跌粗略打分，标注降级
        result["degraded"] = True
        if change_pct is not None:
            score = max(-60.0, min(60.0, change_pct * 20))
            result["score"] = round(score, 1)
            result["trend"] = _trend_label(score)
            result["signals"].append("K线数据暂缺，仅基于当日涨跌粗略评估")
        else:
            result["signals"].append("数据暂缺")
        return result

    closes = [k["close"] for k in kline]
    highs = [k["high"] for k in kline]
    lows = [k["low"] for k in kline]
    vols = [k["vol"] for k in kline]
    last = price or closes[-1]

    # 均线
    ma5, ma10, ma20, ma60 = (_ma(closes, 5), _ma(closes, 10),
                             _ma(closes, 20), _ma(closes, 60))
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            ma_status = "多头排列"
        elif ma5 < ma10 < ma20:
            ma_status = "空头排列"
        else:
            ma_status = "混乱"
    else:
        ma_status = "数据不足"

    # 12 项技术指标（复用 stock_predict.calc_*）
    macd = calc_macd(closes)
    boll = calc_boll(closes)
    kdj = calc_kdj(highs, lows, closes)
    adx = calc_adx(highs, lows, closes)
    tech = {
        "ma5": round(ma5, 2) if ma5 else None,
        "ma10": round(ma10, 2) if ma10 else None,
        "ma20": round(ma20, 2) if ma20 else None,
        "ma60": round(ma60, 2) if ma60 else None,
        "ma_status": ma_status,
        "rsi": round(calc_rsi(closes), 1),
        "macd": macd,
        "boll": boll,
        "kdj": kdj,
        "wr": calc_wr(highs, lows, closes),
        "cci": calc_cci(highs, lows, closes),
        "mfi": calc_mfi(highs, lows, closes, vols),
        "atr": calc_atr(highs, lows, closes),
        "adx": adx,
        "obv": round(calc_obv(closes, vols)[-1], 0) if vols else 0,
    }

    # 动量：近5/20日涨跌幅
    pct5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 else None
    pct20 = (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 else None

    # 波动率：近20日日收益标准差（%）
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    vol20 = statistics.stdev(rets[-20:]) * 100 if len(rets) >= 20 else None

    tech["pct5"] = round(pct5, 2) if pct5 is not None else None
    tech["pct20"] = round(pct20, 2) if pct20 is not None else None
    tech["volatility20"] = round(vol20, 2) if vol20 is not None else None

    # ── 综合评分 (-100~+100) ──
    score = 0.0
    signals: List[str] = []

    # 均线多空 ±30
    if ma_status == "多头排列":
        score += 30
        signals.append("均线多头排列，趋势向上")
    elif ma_status == "空头排列":
        score -= 30
        signals.append("均线空头排列，趋势向下")

    # 价格与 MA20 关系 ±10
    if ma20:
        if last > ma20:
            score += 10
        else:
            score -= 10
            signals.append("指数位于MA20下方，中短期偏弱")

    # RSI ±15
    rsi = tech["rsi"]
    if rsi >= 75:
        score -= 10
        signals.append(f"RSI {rsi:.0f} 超买，谨防回调")
    elif rsi >= 55:
        score += 12
    elif rsi <= 25:
        score += 8
        signals.append(f"RSI {rsi:.0f} 超卖，或有反弹")
    elif rsi <= 45:
        score -= 12

    # MACD ±15
    if macd.get("hist", 0) > 0:
        score += 15
    else:
        score -= 15
        signals.append("MACD柱线为负，动能偏空")

    # ADX 趋势强度 ±10
    adx_v = adx.get("adx", 0) if isinstance(adx, dict) else 0
    if adx_v > 25:
        score += 10 if score > 0 else -10
        signals.append(f"ADX {adx_v:.0f}，趋势强度较高")

    # 动量 ±20
    if pct20 is not None:
        if pct20 > 5:
            score += 15
            signals.append(f"近20日上涨{pct20:.1f}%，动量强劲")
        elif pct20 < -5:
            score -= 15
            signals.append(f"近20日下跌{pct20:.1f}%，动量疲弱")
    if pct5 is not None:
        if pct5 > 2:
            score += 5
        elif pct5 < -2:
            score -= 5

    # 布林位置 ±10
    bpos = boll.get("pos", 50)
    if bpos > 90:
        score -= 5
        signals.append("接近布林上轨，短线偏热")
    elif bpos < 10:
        score += 5
        signals.append("接近布林下轨，短线超卖")

    score = max(-100.0, min(100.0, score))
    result["score"] = round(score, 1)
    result["trend"] = _trend_label(score)
    result["technical"] = tech
    result["signals"] = signals
    result["key_levels"] = {
        "支撑": round(min(lows[-20:]), 2) if len(lows) >= 5 else None,
        "压力": round(max(highs[-20:]), 2) if len(highs) >= 5 else None,
        "MA20": round(ma20, 2) if ma20 else None,
        "布林上轨": boll.get("up"),
        "布林下轨": boll.get("lo"),
    }
    return result


def _trend_label(score: float) -> str:
    if score >= 60:
        return "强势上涨"
    if score >= 20:
        return "上涨"
    if score > -20:
        return "震荡"
    if score > -60:
        return "下跌"
    return "强势下跌"


# ── 相关性 ────────────────────────────────────────────────
def _returns(closes: List[float], n: int = 60) -> List[float]:
    tail = closes[-(n + 1):] if len(closes) > n else closes
    return [tail[i] / tail[i - 1] - 1 for i in range(1, len(tail))]


def _pearson(a: List[float], b: List[float]) -> Optional[float]:
    n = min(len(a), len(b))
    if n < 20:
        return None
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0 or vb <= 0:
        return None
    return cov / math.sqrt(va * vb)


# ── 全球市场全景 ───────────────────────────────────────────
def global_market_outlook(include_correlation: bool = True,
                          days: int = 120) -> Dict:
    """批量分析全部指数，输出全球市场全景。

    节流策略：先用一次批量报价拿全部当日涨跌，再逐个抓K线（间隔>=2s），
    失败的跳过并在输出标注"数据暂缺"。

    Returns:
        {timestamp, indices[{alias,name,price,change_pct,trend,score,degraded}],
         ranking{top,bottom}, correlations[{pair,label,corr,note}],
         missing[alias], source_status}
    """
    aliases = list(GLOBAL_INDEX_UNIVERSE.keys())
    secid_map = {a: GLOBAL_INDEX_UNIVERSE[a][0] for a in aliases}

    # 一次批量报价（最省请求）
    quotes = fetch_batch_quotes(list(secid_map.values()))

    indices: List[Dict] = []
    closes_map: Dict[str, List[float]] = {}
    missing: List[str] = []
    status: Dict[str, str] = {}

    for i, alias in enumerate(aliases):
        secid, market, name = GLOBAL_INDEX_UNIVERSE[alias]
        quote = quotes.get(secid)
        # 逐个抓K线，节流间隔 >=2s（全景批量场景，防限流）
        kline = fetch_kline(secid, days=days, interval=2.0)
        if kline:
            closes_map[alias] = [k["close"] for k in kline]
        if quote is None and not kline:
            missing.append(alias)
            indices.append({
                "alias": alias, "name": name, "market": market,
                "price": None, "change_pct": None,
                "trend": "数据暂缺", "score": None, "degraded": True,
            })
            status[alias] = "empty"
            continue

        # 有K线则完整分析；否则仅报价降级
        if kline:
            # 复用 analyze_index 的评分逻辑，但避免重复请求：内联计算
            entry = _analyze_from_kline(alias, secid, market,
                                        (quote or {}).get("name") or name,
                                        quote, kline)
        else:
            chg = (quote or {}).get("change_pct")
            score = max(-60.0, min(60.0, (chg or 0) * 20))
            entry = {
                "alias": alias, "name": (quote or {}).get("name") or name,
                "market": market,
                "price": (quote or {}).get("price"),
                "change_pct": chg,
                "trend": _trend_label(score) if chg is not None else "数据暂缺",
                "score": round(score, 1) if chg is not None else None,
                "degraded": True,
            }
        indices.append(entry)
        status[alias] = "ok" if kline else "partial"

    # 强弱排名（只看有评分的）
    scored = [x for x in indices if x.get("score") is not None]
    ranked = sorted(scored, key=lambda x: x["score"], reverse=True)

    # 相关性提示（近60日收益相关系数）
    correlations = []
    if include_correlation:
        for a, b, label in CORRELATION_PAIRS:
            ca, cb = closes_map.get(a), closes_map.get(b)
            if not ca or not cb:
                correlations.append({"pair": f"{a}/{b}", "label": label,
                                     "corr": None, "note": "数据暂缺"})
                continue
            corr = _pearson(_returns(ca), _returns(cb))
            if corr is None:
                note = "数据不足"
            elif corr > 0.6:
                note = "强正相关，联动明显"
            elif corr > 0.3:
                note = "中等正相关"
            elif corr < -0.4:
                note = "明显负相关（反向）"
            elif corr < -0.15:
                note = "弱负相关"
            else:
                note = "相关性弱"
            correlations.append({
                "pair": f"{a}/{b}", "label": label,
                "corr": round(corr, 2) if corr is not None else None,
                "note": note,
            })

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "indices": indices,
        "ranking": {
            "top": [{"alias": x["alias"], "name": x["name"],
                     "score": x["score"]} for x in ranked[:5]],
            "bottom": [{"alias": x["alias"], "name": x["name"],
                        "score": x["score"]} for x in ranked[-5:]],
        },
        "correlations": correlations,
        "missing": missing,
        "source_status": status,
    }


def _analyze_from_kline(alias: str, secid: str, market: str, name: str,
                        quote: Optional[Dict], kline: List[Dict]) -> Dict:
    """从已有 quote+kline 计算趋势评分（global_market_outlook 内联版，
    与 analyze_index 同一套规则，避免重复网络请求）"""
    closes = [k["close"] for k in kline]
    highs = [k["high"] for k in kline]
    lows = [k["low"] for k in kline]
    last = (quote or {}).get("price") or closes[-1]

    ma5, ma10, ma20 = _ma(closes, 5), _ma(closes, 10), _ma(closes, 20)
    if ma5 and ma10 and ma20 and ma5 > ma10 > ma20:
        ma_status = "多头排列"
    elif ma5 and ma10 and ma20 and ma5 < ma10 < ma20:
        ma_status = "空头排列"
    else:
        ma_status = "混乱"

    score = 0.0
    if ma_status == "多头排列":
        score += 30
    elif ma_status == "空头排列":
        score -= 30
    if ma20:
        score += 10 if last > ma20 else -10
    rsi = calc_rsi(closes)
    if rsi >= 75:
        score -= 10
    elif rsi >= 55:
        score += 12
    elif rsi <= 25:
        score += 8
    elif rsi <= 45:
        score -= 12
    macd = calc_macd(closes)
    score += 15 if macd.get("hist", 0) > 0 else -15
    adx = calc_adx(highs, lows, closes)
    if isinstance(adx, dict) and adx.get("adx", 0) > 25:
        score += 10 if score > 0 else -10
    pct20 = (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 else 0
    if pct20 > 5:
        score += 15
    elif pct20 < -5:
        score -= 15
    pct5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 else 0
    if pct5 > 2:
        score += 5
    elif pct5 < -2:
        score -= 5
    boll = calc_boll(closes)
    if boll.get("pos", 50) > 90:
        score -= 5
    elif boll.get("pos", 50) < 10:
        score += 5
    score = max(-100.0, min(100.0, score))

    return {
        "alias": alias, "name": name, "market": market,
        "price": last,
        "change_pct": (quote or {}).get("change_pct"),
        "trend": _trend_label(score),
        "score": round(score, 1),
        "ma_status": ma_status,
        "rsi": round(rsi, 1),
        "pct5": round(pct5, 2),
        "pct20": round(pct20, 2),
        "degraded": False,
    }


# ── T+1/T+3/T+5 蒙特卡洛预判 ───────────────────────────────
def index_forecast(alias_or_secid: str, sims: int = 500,
                   seed: Optional[int] = None,
                   data: Optional[Dict] = None) -> Dict:
    """指数 T+1/T+3/T+5 预判：技术打分 + 近120日蒙特卡洛模拟。

    借鉴 fusion/multi_horizon_forecaster._monte_carlo 思路（自包含实现）：
    综合评分 score(-100~+100) 映射为日收益 μ 调整项，封上限 ±0.25σ/日。

    Args:
        data: 可选，预取的 fetch_index_data 结果（避免重复请求）

    Returns:
        {alias, name, price, score, trend,
         "1d"/"3d"/"5d": {direction, predicted_pct, prob_up, p10, p90}}
    """
    alias, secid, _, _ = _resolve(alias_or_secid)
    # quote+kline 一次抓取，分析与 MC 共用（避免重复请求触发限流）
    if data is None:
        data = fetch_index_data(secid, days=120)
    analysis = analyze_index(alias_or_secid, data=data)
    kline = data.get("kline") or []
    closes = [k["close"] for k in kline] if kline else []
    price = analysis.get("price") or (closes[-1] if closes else 0)
    score = analysis.get("score") or 0.0

    rng = random.Random(seed if seed is not None else f"{alias}-{time.strftime('%Y%m%d')}")
    out = {
        "alias": alias, "name": analysis.get("name", alias),
        "price": price, "score": score, "trend": analysis.get("trend"),
        "degraded": analysis.get("degraded", False),
    }

    for horizon, hdays in (("1d", 1), ("3d", 3), ("5d", 5)):
        if len(closes) >= 30 and price > 0:
            rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
            mu = sum(rets) / len(rets)
            variance = sum((r - mu) ** 2 for r in rets) / len(rets)
            sigma = math.sqrt(max(variance, 1e-12))
            # 技术评分 → μ 调整（封 ±0.25σ）
            adj = max(-0.25, min(0.25, score / 100 * 0.5))
            mu_adj = mu + adj * sigma
            results = []
            for _ in range(sims):
                p = 1.0
                for _ in range(hdays):
                    p *= (1 + rng.gauss(mu_adj, sigma))
                results.append(p - 1.0)
            results.sort()
            n = len(results)
            predicted_pct = sum(results) / n * 100
            p10 = results[int(n * 0.1)] * 100
            p90 = results[int(n * 0.9)] * 100
            prob_up = sum(1 for r in results if r > 0) / n * 100
        else:
            # 数据不足：仅用评分粗略推断
            predicted_pct = score * 0.05 * math.sqrt(hdays)
            lo, hi = sorted((predicted_pct - 1.5 * math.sqrt(hdays),
                             predicted_pct + 1.5 * math.sqrt(hdays)))
            p10, p90 = lo, hi
            prob_up = 50 + score / 4
            prob_up = max(5, min(95, prob_up))

        if prob_up > 55:
            direction = "看多"
        elif prob_up < 45:
            direction = "看空"
        else:
            direction = "震荡"
        out[horizon] = {
            "direction": direction,
            "predicted_pct": round(predicted_pct, 2),
            "prob_up": round(prob_up, 1),
            "p10": round(p10, 2),
            "p90": round(p90, 2),
        }
    return out


# ── 板块趋势报告（叠加政策受益板块）────────────────────────
def sector_trend_report(market: str = "cn") -> Dict:
    """板块趋势报告：领涨/领跌、轮动信号、政策受益板块叠加。

    调用现有 sector_analysis 模块；政策面来自 macro.policy_analyzer。
    """
    from ..sector_analysis.sectors import SectorAnalyzer
    from ..macro.policy_analyzer import policy_score, fetch_policy_news, \
        analyze_policy_impact

    analyzer = SectorAnalyzer()
    sector_map = analyzer.get_sector_map(market)

    sectors_out: List[Dict] = []
    for sector_name, codes in sector_map.items():
        try:
            if market == "cn":
                r = analyzer.analyze_sector(sector_name)
                sectors_out.append({
                    "name": r.name, "avg_change_pct": r.avg_change_pct,
                    "up_count": r.up_count, "down_count": r.down_count,
                    "total_net_flow": r.total_net_flow,
                    "score": r.score, "signal": r.signal,
                    "rotation": r.rotation_signal,
                })
            else:
                # hk/us：用对应板块映射做轻量统计
                rt = analyzer.market.fetch_realtime(codes)
                if not rt:
                    sectors_out.append({"name": sector_name, "avg_change_pct": None,
                                        "signal": "数据暂缺"})
                    continue
                chgs = [d.get("change_pct", 0) for d in rt.values()
                        if d.get("price", 0) > 0]
                avg_chg = sum(chgs) / len(chgs) if chgs else 0
                flow = sum(d.get("main_net_flow", 0) for d in rt.values())
                sectors_out.append({
                    "name": sector_name, "avg_change_pct": round(avg_chg, 2),
                    "up_count": sum(1 for c in chgs if c > 0),
                    "down_count": sum(1 for c in chgs if c < 0),
                    "total_net_flow": round(flow, 2),
                    "score": round(avg_chg * 10, 1),
                    "signal": "强于大盘" if avg_chg > 1 else
                              ("弱于大盘" if avg_chg < -1 else "中性"),
                    "rotation": "流入" if flow > 0 else "流出" if flow < 0 else "中性",
                })
        except Exception:
            sectors_out.append({"name": sector_name, "avg_change_pct": None,
                                "signal": "数据暂缺"})
        time.sleep(0.3)

    ranked = sorted(
        [s for s in sectors_out if s.get("avg_change_pct") is not None],
        key=lambda x: x["avg_change_pct"], reverse=True)

    # 政策受益板块叠加
    policy = policy_score(market=market if market in ("cn", "hk", "us") else "cn")
    news = fetch_policy_news(days=7)
    analysis = analyze_policy_impact(news)
    benefited: Dict[str, str] = {}
    for ev in analysis:
        if ev["direction"] != "利多":
            continue
        for s in ev.get("affected_sectors", []):
            if s not in benefited:
                benefited[s] = ev["category"]

    for s in sectors_out:
        if s["name"] in benefited:
            s["policy_boost"] = benefited[s["name"]]

    # 轮动信号
    inflow = [s["name"] for s in sectors_out
              if s.get("total_net_flow", 0) and s["total_net_flow"] > 10000]
    rotation_note = ""
    if ranked:
        top_names = "、".join(s["name"] for s in ranked[:3])
        bottom_names = "、".join(s["name"] for s in ranked[-3:])
        rotation_note = f"领涨: {top_names}；领跌: {bottom_names}"

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "market": market,
        "sectors": sectors_out,
        "top": ranked[:3],
        "bottom": ranked[-3:] if len(ranked) >= 3 else [],
        "rotation_note": rotation_note,
        "policy_score": policy,
        "policy_benefited_sectors": benefited,
    }
