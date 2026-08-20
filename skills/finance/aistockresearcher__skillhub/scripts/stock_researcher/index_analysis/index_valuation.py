#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""指数估值分析 (v9.0.0 新增)
============================
指数级 PE/PB 估值与历史分位。

v8.0 已为「个股」做了真实 PE/PB 历史分位（fundamental.get_valuation），
但「指数」估值仍用粗阈值（PE<15 算低）。本模块补齐指数级真实估值：

数据获取（多级降级，绝不编造分位）：
  1. 东财数据中心「指数估值」报表 → 真实 PE/PB 历史序列 → 真实分位
  2. 指数实时行情中的 pe/pb 字段 → 真实快照（分位标注 unavailable）
  3. 成分股 PE 聚合（加权/中位）→ 真实代理（data_mode="aggregate"）

每条结果标注 data_mode：index_report | quote_snapshot | aggregate | unavailable。
分位仅在确有历史序列时计算，否则为 None（诚实优于编造）。

纯函数离线可测 + 优雅降级。

用法:
    from stock_researcher.index_analysis.index_valuation import IndexValuation
    v = IndexValuation().classify("sh000300")
    print(v.pe, v.pe_percentile, v.valuation_label)
"""

from __future__ import annotations

import json
import math
import ssl
import urllib.request
import urllib.parse
from typing import List, Optional, Sequence
from dataclasses import dataclass, field


@dataclass
class IndexValuationResult:
    """指数估值结果"""
    code: str = ""
    pe: Optional[float] = None
    pb: Optional[float] = None
    pe_percentile: Optional[float] = None    # 0-100，无历史时 None（不编造）
    pb_percentile: Optional[float] = None
    history_len: int = 0
    data_mode: str = "unavailable"           # index_report|quote_snapshot|aggregate|unavailable
    valuation_score: float = 0.0             # -100(极便宜)..+100(极贵)
    valuation_label: str = "未知"            # 极度低估/低估/合理/高估/极度高估/未知
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层
# ════════════════════════════════════════════════════════════

def percentile_of(value: float, history: Sequence[float]) -> Optional[float]:
    """value 在 history 中的百分位（竞争法，min→0/max→100）。数据不足返回 None。"""
    h = [float(x) for x in history if x is not None and math.isfinite(float(x)) and float(x) > 0]
    n = len(h)
    if n < 5 or value <= 0:
        return None
    less = sum(1 for v in h if v < value)
    equal = sum(1 for v in h if v == value)
    avg_pos = less + (equal - 1) / 2.0
    return avg_pos / (n - 1) * 100.0


def valuation_score_from_percentile(percentile: Optional[float]) -> float:
    """分位 → 估值分：分位越高越贵（+100），50 为合理。无分位返回 0。"""
    if percentile is None:
        return 0.0
    # percentile 0→-100(便宜), 50→0, 100→+100(贵)
    return (percentile - 50.0) * 2.0


def valuation_score_from_pe(pe: float, market: str = "cn") -> float:
    """无分位时，用市场特定 PE 阈值近似估值分（粗略，仅作 fallback）。"""
    if pe <= 0:
        return 0.0
    if market in ("us", "jp"):
        cheap, expensive = 15, 25
    elif market in ("hk", "uk", "de", "fr"):
        cheap, expensive = 9, 18
    else:
        cheap, expensive = 11, 22
    mid = (cheap + expensive) / 2.0
    # pe=cheap → -40, mid → 0, expensive → +40，外推封顶 ±60
    if pe <= mid:
        score = (pe - mid) / (mid - cheap) * 40 if mid > cheap else 0
    else:
        score = (pe - mid) / (expensive - mid) * 40 if expensive > mid else 0
    return max(-60.0, min(60.0, score))


def valuation_label_from_score(score: float) -> str:
    if score <= -60:
        return "极度低估"
    if score <= -25:
        return "低估"
    if score < 25:
        return "合理"
    if score < 60:
        return "高估"
    return "极度高估"


def aggregate_pe(pe_list: Sequence[float]) -> Optional[float]:
    """成分股 PE 中位数（剔除负值/None）。"""
    vals = sorted(float(x) for x in pe_list if x and float(x) > 0)
    if not vals:
        return None
    n = len(vals)
    return vals[n // 2] if n % 2 == 1 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class IndexValuation:
    """指数估值分析器（多级真实数据降级）。"""

    # 东财指数估值报表（best-effort；reportName 失败则降级）
    _DC_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    def classify(self, code: str, market: str = "cn") -> IndexValuationResult:
        # 1) 尝试真实历史序列
        series = self._fetch_index_valuation_series(code)
        if series and series.get("pe_history"):
            pe_hist = series["pe_history"]
            pb_hist = series.get("pb_history", [])
            pe = pe_hist[-1] if pe_hist else None
            pb = pb_hist[-1] if pb_hist else None
            pe_pct = percentile_of(pe, pe_hist) if pe else None
            pb_pct = percentile_of(pb, pb_hist) if pb and pb_hist else None
            score = valuation_score_from_percentile(pe_pct) if pe_pct is not None else 0.0
            return IndexValuationResult(
                code=code, pe=round(pe, 2) if pe else None,
                pb=round(pb, 2) if pb else None,
                pe_percentile=round(pe_pct, 1) if pe_pct is not None else None,
                pb_percentile=round(pb_pct, 1) if pb_pct is not None else None,
                history_len=len(pe_hist), data_mode="index_report",
                valuation_score=round(score, 1),
                valuation_label=valuation_label_from_score(score),
                note=f"真实历史分位(东财报表,{len(pe_hist)}期)",
            )

        # 2) 实时快照 PE/PB
        snap = self._fetch_quote_pe(code)
        if snap and (snap.get("pe") or snap.get("pb")):
            pe = snap.get("pe")
            pb = snap.get("pb")
            score = valuation_score_from_pe(pe or 0, market)
            return IndexValuationResult(
                code=code,
                pe=round(pe, 2) if pe else None,
                pb=round(pb, 2) if pb else None,
                pe_percentile=None,
                history_len=0, data_mode="quote_snapshot",
                valuation_score=round(score, 1),
                valuation_label=valuation_label_from_score(score) + "(无分位)",
                note="仅快照PE/PB，历史分位unavailable",
            )

        # 3) 成分股聚合
        agg_pe = self._aggregate_constituent_pe(code)
        if agg_pe:
            score = valuation_score_from_pe(agg_pe, market)
            return IndexValuationResult(
                code=code, pe=round(agg_pe, 2),
                pe_percentile=None, history_len=0, data_mode="aggregate",
                valuation_score=round(score, 1),
                valuation_label=valuation_label_from_score(score) + "(成分聚合)",
                note="成分股PE中位数代理，非指数官方PE",
            )

        return IndexValuationResult(
            code=code, data_mode="unavailable",
            note="指数估值数据不可用",
        )

    # ── 东财指数估值历史序列（best-effort） ──
    def _fetch_index_valuation_series(self, code: str) -> dict:
        secid = self._to_secid(code)
        if not secid:
            return {}
        params = {
            "sortColumns": "TRADE_DATE", "sortTypes": "-1",
            "pageSize": "250", "pageNumber": "1",
            "reportName": "RPT_INDEX_VALUATION",
            "filter": f'(SECURITY_CODE="{secid}")',
        }
        url = self._DC_URL + "?" + urllib.parse.urlencode(params)
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            rows = (data.get("result") or {}).get("data") or []
            if not rows:
                return {}
            rows = list(reversed(rows))  # 升序
            pe_hist = [float(r.get("PE", 0) or 0) for r in rows]
            pb_hist = [float(r.get("PB", 0) or 0) for r in rows]
            return {"pe_history": pe_hist, "pb_history": pb_hist}
        except Exception:
            return {}

    # ── 实时快照 pe/pb ──
    def _fetch_quote_pe(self, code: str) -> dict:
        try:
            from stock_researcher.data.global_market import _CLIENT
            secid = self._to_secid(code)
            if not secid:
                return {}
            q = _CLIENT.get_quote(secid) or {}
            pe = q.get("pe")
            pb = q.get("pb")
            if pe or pb:
                return {"pe": pe, "pb": pb}
        except Exception:
            pass
        return {}

    # ── 成分股 PE 聚合（真实个股 PE） ──
    def _aggregate_constituent_pe(self, code: str) -> Optional[float]:
        try:
            from stock_researcher.index_analysis.market_internals import INDEX_BASKET
            from stock_researcher.data.fundamental import FundamentalData
            basket = INDEX_BASKET.get(code, [])
            if not basket:
                return None
            fd = FundamentalData()
            pes = []
            for c in basket:
                v = fd.get_valuation(c, history_len=1) or {}
                pe = v.get("pe")
                if pe and float(pe) > 0:
                    pes.append(float(pe))
            return aggregate_pe(pes)
        except Exception:
            return None

    @staticmethod
    def _to_secid(code: str) -> str:
        c = str(code)
        if c.startswith("sh"):
            return "1." + c[2:]
        if c.startswith("sz"):
            return "0." + c[2:]
        if c.startswith("100."):
            return c
        return c

    @staticmethod
    def format(v: IndexValuationResult) -> str:
        pe_s = f"PE{v.pe:.1f}" if v.pe else "PE-"
        pct_s = f"(分位{v.pe_percentile:.0f}%)" if v.pe_percentile is not None else "(无分位)"
        return f"[{v.code}] {pe_s}{pct_s} {v.valuation_label} 分{v.valuation_score:+.0f} ({v.data_mode})"


def classify_index_valuation(code: str, market: str = "cn") -> IndexValuationResult:
    """便捷函数：指数估值。"""
    return IndexValuation().classify(code, market=market)
