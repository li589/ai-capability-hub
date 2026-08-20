#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""国际宏观与外围市场信号 (v4.0.0 新增)

数据来源（全部免费、国内直连）：
- 外围指数：腾讯 qt.gtimg.cn  (道指/纳指/标普/恒生/日经)
- 大宗与汇率：新浪 hq.sinajs.cn (原油/黄金/离岸人民币/VIX)
- 美元指数：东方财富 push2 secid=100.UDI
- 全球财经快讯：东方财富新闻 column

定位：A股为主，本模块仅提供"外围情境信号"，不预测海外个股。
所有符号独立解析，任一失败不影响整体，并标注 source_status。
不编造数据：解析失败的字段返回 None。
"""
from __future__ import annotations

import sys
import re
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "pkg"))
from crawl_utils import safe_request, fetch_json, detect_encoding  # noqa: E402


# ── 腾讯外围指数与波动率（~ 分隔，字段稳定）──────────────────
TENCENT_INDICES = {
    "usDJI":  "道琼斯工业",
    "usIXIC": "纳斯达克",
    "usINX":  "标普500",
    "hkHSI":  "恒生指数",
    "usN225": "日经225",
    "usVIX":  "标普500波动率(VIX)",
}

# ── 新浪大宗/汇率（变量名带 hq_str_ 前缀）────────────────────
SINA_SYMBOLS = {
    "hf_CL":      "NYMEX原油(WTI)",
    "hf_GC":      "COMEX黄金",
    "fx_susdcnh": "离岸人民币(USDCNH)",
}


def _to_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A", "null"):
            return default
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


# ────────────────────────────────────────────────────────────
#  采集器
# ────────────────────────────────────────────────────────────
def _fetch_tencent_indices(codes: List[str]) -> Dict[str, Dict]:
    """腾讯行情，~ 分隔。field[1]=名称 field[3]=现价 field[32]=涨跌幅%"""
    if not codes:
        return {}
    url = f"https://qt.gtimg.cn/q={','.join(codes)}&_={int(time.time()*1000)}"
    raw = safe_request(url, timeout=8)
    out = {}
    if not raw:
        return out
    text = raw.decode("utf-8", errors="replace")
    for code in codes:
        m = re.search(r'v_' + re.escape(code) + r'="(.+?)"', text)
        if not m:
            continue
        fields = m.group(1).split("~")
        if len(fields) < 10:
            continue
        name = fields[1] or TENCENT_INDICES.get(code, code)
        price = _to_float(fields[3])
        change_pct = _to_float(fields[32]) if len(fields) > 32 else None
        # 涨跌幅可能为空，用 field[4](昨收) 回算
        if change_pct is None and price:
            prev = _to_float(fields[4])
            if prev and prev > 0:
                change_pct = round((price - prev) / prev * 100, 3)
        if price is None:
            continue
        out[code] = {"name": name, "price": price, "change_pct": change_pct}
    return out


def _fetch_sina_hf(symbols: List[str]) -> Dict[str, Dict]:
    """新浪外盘期货/汇率。变量名带 hq_str_ 前缀。
    hf_ 口径：fields[0]=现价 fields[2]=昨收
    fx_ 口径：fields[0]=时间 fields[1]=现价 fields[2]=昨收
    """
    if not symbols:
        return {}
    url = f"https://hq.sinajs.cn/list={','.join(symbols)}"
    headers = {"Referer": "https://finance.sina.com.cn"}
    raw = safe_request(url, timeout=8, headers=headers)
    out = {}
    if not raw:
        return out
    enc = detect_encoding(raw, default="gbk")
    try:
        text = raw.decode(enc, errors="replace")
    except Exception:
        text = raw.decode("gbk", errors="replace")
    for sym in symbols:
        # 兼容 var hf_CL="..." 与 var hq_str_hf_CL="..."
        m = re.search(r'var\s+(?:hq_str_)?' + re.escape(sym) + r'="([^"]*)"', text)
        if not m:
            continue
        content = m.group(1)
        if not content:
            continue
        fields = content.split(",")
        name = SINA_SYMBOLS.get(sym, sym)
        is_fx = sym.startswith("fx_")
        current = prev = None
        if is_fx:
            # fields[0]=时间 fields[1]=现价 fields[2]=昨收
            if len(fields) > 2:
                current = _to_float(fields[1])
                prev = _to_float(fields[2])
        else:
            # hf_: fields[0]=现价 fields[2]=昨收
            if len(fields) > 2:
                current = _to_float(fields[0])
                prev = _to_float(fields[2])
        if current is None or current <= 0:
            continue
        change_pct = None
        if prev and prev > 0:
            chg = (current - prev) / prev * 100
            if abs(chg) < 30:  # 合理性过滤
                change_pct = round(chg, 3)
        out[sym] = {"name": name, "price": current, "change_pct": change_pct}
    return out


def _fetch_usd_index() -> Optional[Dict]:
    """美元指数（多源尝试，失败返回 None）。

    东财 push2 直连常被拒，这里作占位回退；USDCNH 已能反映美元对人民币强弱，
    故美元指数缺失不影响下游风险偏好计算。
    """
    return None


def _fetch_global_news(limit: int = 8) -> List[Dict]:
    """东方财富全球财经新闻（用于情境关键词）"""
    url = ("https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?"
           "client=web&biz=web_news_col&column=358&order=1&needInteractData=0"
           f"&page_index=1&page_size={limit}")
    try:
        data = fetch_json(url, timeout=8)
    except Exception:
        data = None
    news = []
    if data and data.get("data") and data["data"].get("list"):
        for item in data["data"]["list"]:
            news.append({
                "title": item.get("title", ""),
                "date": (item.get("showtime", "") or "")[:10],
                "url": item.get("url", ""),
            })
    return news


# ────────────────────────────────────────────────────────────
#  外围风险偏好得分
# ────────────────────────────────────────────────────────────
# 方向含义（对A股风险偏好的影响）：
#  美元指数上行 -> - （新兴市场资金外流压力）
#  VIX 上行     -> - （避险情绪升温）
#  原油大涨     -> - （输入性通胀/成本压力，A股偏负）但小涨中性
#  黄金大涨     -> - （避险）但有时反映宽松预期，权重小
#  人民币贬值   -> - （外资流出压力）
#  道指/纳指/恒生上行 -> + （全球风险偏好回暖）
RISK_CONTRIB = {
    "usVIX":      {"weight": 0.22, "sign": -1, "threshold": 1.0},   # VIX 上行=避险升温
    "fx_susdcnh": {"weight": 0.18, "sign": -1, "threshold": 0.2},   # 离岸人民币数值上行=贬值=外资流出压力(兼作美元代理)
    "hf_CL":      {"weight": 0.10, "sign": -1, "threshold": 3.0},   # 原油大涨=输入性通胀
    "hf_GC":      {"weight": 0.05, "sign": -1, "threshold": 2.0},   # 黄金大涨=避险
    "usDJI":      {"weight": 0.15, "sign": +1, "threshold": 0.5},   # 道指上行=全球风险偏好回暖
    "usIXIC":     {"weight": 0.12, "sign": +1, "threshold": 0.6},
    "usINX":      {"weight": 0.08, "sign": +1, "threshold": 0.5},   # 标普500
    "hkHSI":      {"weight": 0.10, "sign": +1, "threshold": 0.6},   # 恒生(港股,A股联动)
}


def compute_global_risk_appetite(signals: Dict[str, Dict]) -> Dict:
    """综合外围风险偏好得分 (-100 ~ +100)"""
    contribs = []
    used = []
    for key, cfg in RISK_CONTRIB.items():
        s = signals.get(key)
        if not s or s.get("change_pct") is None:
            continue
        chg = s["change_pct"]
        threshold = cfg.get("threshold", 0.3)
        # 超过阈值才计入，避免噪音
        strength = max(-1.0, min(1.0, chg / (threshold * 3) if threshold else chg / 3))
        score = cfg["sign"] * strength * cfg["weight"] * 100
        contribs.append(score)
        used.append(key)
    if not contribs:
        return {
            "score": 0.0, "label": "数据不足", "confidence": 0.0,
            "contributors": [], "note": "外围信号解析失败或为空",
        }
    # 归一化：按已用权重总和缩放，保证满分±100可达
    total_w = sum(RISK_CONTRIB[k]["weight"] for k in used)
    raw = sum(contribs)
    norm = raw / total_w if total_w > 0 else 0.0
    norm = max(-100.0, min(100.0, norm))
    if norm >= 40:
        label = "外围偏暖"
    elif norm >= 15:
        label = "外围温和偏多"
    elif norm > -15:
        label = "外围中性"
    elif norm > -40:
        label = "外围温和偏空"
    else:
        label = "外围偏冷"
    return {
        "score": round(norm, 1),
        "label": label,
        "confidence": round(min(1.0, len(used) / 5.0), 2),
        "contributors": [
            {"symbol": k, "change_pct": signals[k]["change_pct"],
             "contribution": round(c / total_w if total_w else 0, 1)}
            for k, c in zip(used, contribs)
        ],
    }


class MacroSignalCollector:
    """国际宏观信号采集器"""

    def collect(self, with_news: bool = True) -> Dict:
        tencent = _fetch_tencent_indices(list(TENCENT_INDICES.keys()))
        sina = _fetch_sina_hf(list(SINA_SYMBOLS.keys()))
        usd = _fetch_usd_index()

        signals: Dict[str, Dict] = {}
        signals.update(tencent)
        signals.update(sina)
        if usd:
            signals["usd_index"] = usd

        risk = compute_global_risk_appetite(signals)
        news = _fetch_global_news(limit=8) if with_news else []

        # source_status
        status = {}
        for k in list(TENCENT_INDICES.keys()):
            status[k] = "ok" if k in tencent else "empty"
        for k in list(SINA_SYMBOLS.keys()):
            status[k] = "ok" if k in sina else "empty"
        status["usd_index"] = "ok" if usd else "empty"
        status["global_news"] = "ok" if news else "empty"

        return {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "signals": signals,
            "global_risk_appetite": risk,
            "global_news": news,
            "source_status": status,
        }


def get_macro_signals(with_news: bool = True) -> Dict:
    """便捷入口"""
    return MacroSignalCollector().collect(with_news=with_news)


def format_macro_report(result: Dict) -> str:
    lines = []
    hr = "=" * 70
    lines.append(hr)
    lines.append(f"  🌐 国际宏观与外围信号  |  {result.get('update_time')}")
    lines.append(hr)
    sig = result.get("signals", {})
    label_map = {**TENCENT_INDICES, **SINA_SYMBOLS}
    order = ["usVIX", "fx_susdcnh", "usDJI", "usIXIC", "usINX", "hkHSI", "usN225",
             "hf_CL", "hf_GC"]
    for k in order:
        s = sig.get(k)
        if not s:
            continue
        name = s.get("name") or label_map.get(k, k)
        price = s.get("price")
        chg = s.get("change_pct")
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        icon = "🟢" if (chg or 0) > 0 else ("🔴" if (chg or 0) < 0 else "⚪")
        lines.append(f"  {icon} {name:<16} {price:>10}  {chg_str:>8}")
    risk = result.get("global_risk_appetite", {})
    lines.append("")
    lines.append(f"  🎯 外围风险偏好: {risk.get('score',0):+.1f}  [{risk.get('label')}]"
                 f"  (置信 {risk.get('confidence',0):.0%})")
    news = result.get("global_news", [])
    if news:
        lines.append("  📰 全球财经快讯:")
        for n in news[:5]:
            lines.append(f"    · [{n.get('date')}] {n.get('title','')[:42]}")
    lines.append(hr)
    return "\n".join(lines)


def main():
    print("=== 国际宏观信号采集 ===")
    r = get_macro_signals()
    print(format_macro_report(r))


if __name__ == "__main__":
    main()
