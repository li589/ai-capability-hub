#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""备用数据源（sources_fallback.py，v8.0 新增）

为 source_manager 提供新浪/东财备用源，输出形状与 MarketData 一致：
- fetch_realtime: {code: {name, price, change_pct, high, low, open, prev_close, volume, amount, source, ...}}
- fetch_history:  {dates, opens, highs, lows, closes, volumes}

全部纯 stdlib + try/except；失败返回空 dict/None，触发 source_manager 自动降级。
"""

import json
import re
from typing import Dict, List, Optional


def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 8):
    import urllib.request
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ─────────────────────────────────────────────────────
# 实时行情备用源
# ─────────────────────────────────────────────────────

def _tencent_market(code: str) -> str:
    """把 6 位 A 股代码转腾讯市场前缀。"""
    if code.startswith(("6", "5", "9")):
        return "sh"
    return "sz"


def sina_fetch_realtime(codes: List[str]) -> Dict[str, Dict]:
    """新浪实时行情（hq.sinajs.cn）— 备用源 1。"""
    try:
        sina_codes = []
        for c in codes:
            if c.isdigit() and len(c) == 6:
                sina_codes.append(f"{_tencent_market(c)}{c}")
            else:
                sina_codes.append(c)
        url = "https://hq.sinajs.cn/list=" + ",".join(sina_codes)
        raw = _http_get(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.sina.com.cn",
        }, timeout=8)
        text = raw.decode("gb18030", errors="ignore")
        result: Dict[str, Dict] = {}
        for m in re.finditer(r'hq_str_(\w+)="([^"]*)"', text):
            code_raw, payload = m.group(1), m.group(2)
            f = payload.split(",")
            if len(f) < 4:
                continue
            code = code_raw[2:] if code_raw.startswith(("sh", "sz")) else code_raw
            price = _safe(f, 3)
            result[code] = {
                "name": f[0],
                "price": price,
                "prev_close": _safe(f, 2),
                "open": _safe(f, 1),
                "high": _safe(f, 4),
                "low": _safe(f, 5),
                "volume": _safe(f, 8),
                "amount": _safe(f, 9),
                "change_pct": round((price - _safe(f, 2)) / _safe(f, 2) * 100, 2) if _safe(f, 2) else 0.0,
                "change": price - _safe(f, 2),
                "turnover": 0.0,
                "pe": 0.0,
                "mkt_cap": 0.0,
                "main_net_flow": 0.0,
                "source": "sina",
            }
        return result
    except Exception:
        return {}


def em_fetch_realtime(codes: List[str]) -> Dict[str, Dict]:
    """东财 push2 实时行情 — 备用源 2。"""
    try:
        secids = []
        for c in codes:
            mkt = "1" if str(c).startswith(("6", "5", "9")) else "0"
            secids.append(f"{mkt}.{c}")
        url = ("https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2"
               f"&secids={','.join(secids)}&fields=f12,f14,f2,f3,f4,f5,f6,f8,f15,f16,f17,f18,f20,f9")
        raw = _http_get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = json.loads(raw.decode("utf-8", errors="ignore"))
        result: Dict[str, Dict] = {}
        for item in (data.get("data") or {}).get("diff") or []:
            code = str(item.get("f12", ""))
            price = _to_float(item.get("f2"))
            prev = _to_float(item.get("f18"))
            result[code] = {
                "name": item.get("f14", ""),
                "price": price,
                "prev_close": prev,
                "open": _to_float(item.get("f17")),
                "high": _to_float(item.get("f15")),
                "low": _to_float(item.get("f16")),
                "volume": _to_float(item.get("f5")),
                "amount": _to_float(item.get("f6")),
                "change": _to_float(item.get("f4")),
                "change_pct": _to_float(item.get("f3")),
                "turnover": _to_float(item.get("f8")),
                "pe": _to_float(item.get("f9")),
                "mkt_cap": _to_float(item.get("f20")),
                "main_net_flow": 0.0,
                "source": "eastmoney",
            }
        return result
    except Exception:
        return {}


# ─────────────────────────────────────────────────────
# 历史 K 线备用源
# ─────────────────────────────────────────────────────

def _tencent_kline_code(code: str) -> str:
    if code.isdigit() and len(code) == 6:
        return f"{_tencent_market(code)}{code}"
    return code


def sina_fetch_history(code: str, days: int = 120) -> Optional[Dict[str, List]]:
    """新浪日 K 线 — 备用源 1。"""
    try:
        url = ("https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
               f"?symbol={_tencent_kline_code(code)}&scale=240&ma=no&datalen={days}")
        raw = _http_get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        rows = json.loads(raw.decode("utf-8", errors="ignore"))
        if not isinstance(rows, list) or not rows:
            return None
        return {
            "dates": [str(r.get("day", ""))[:10] for r in rows],
            "opens": [_to_float(r.get("open")) for r in rows],
            "highs": [_to_float(r.get("high")) for r in rows],
            "lows": [_to_float(r.get("low")) for r in rows],
            "closes": [_to_float(r.get("close")) for r in rows],
            "volumes": [_to_float(r.get("volume")) for r in rows],
            "source": "sina",
        }
    except Exception:
        return None


def em_fetch_history(code: str, days: int = 120) -> Optional[Dict[str, List]]:
    """东财 push2his 日 K 线 — 备用源 2。"""
    try:
        mkt = "1" if str(code).startswith(("6", "5", "9")) else "0"
        url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get"
               f"?secid={mkt}.{code}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57"
               f"&klt=101&fqt=1&end=20500101&lmt={days}")
        raw = _http_get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = json.loads(raw.decode("utf-8", errors="ignore"))
        klines = (data.get("data") or {}).get("klines") or []
        if not klines:
            return None
        dates, opens, closes, highs, lows, volumes = [], [], [], [], [], []
        for k in klines:
            p = str(k).split(",")
            if len(p) < 6:
                continue
            dates.append(p[0])
            opens.append(_to_float(p[1]))
            closes.append(_to_float(p[2]))
            highs.append(_to_float(p[3]))
            lows.append(_to_float(p[4]))
            volumes.append(_to_float(p[5]))
        return {"dates": dates, "opens": opens, "highs": highs, "lows": lows,
                "closes": closes, "volumes": volumes, "source": "eastmoney"}
    except Exception:
        return None


# ─────────────────────────────────────────────────────
# 工具
# ─────────────────────────────────────────────────────

def _to_float(v) -> float:
    try:
        if v is None:
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _safe(fields: List[str], idx: int) -> float:
    if idx < len(fields):
        try:
            return float(fields[idx])
        except (TypeError, ValueError):
            return 0.0
    return 0.0
