#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""券商研究报告 / 机构评级 / 一致预期 / 目标价 (v4.0.0 新增)

数据来源：东方财富 reportapi 研报检索接口（免费、国内直连、无需 API Key）
  https://reportapi.eastmoney.com/report/list?...&code={code}&rptType=SECURITIES_RESEARCH_REPORT

该接口单次返回即可覆盖：
  - emRatingName        机构评级（买入/增持/持有/...）
  - predict{This,Next,NextTwo}YearEps/Pe   一致预期 EPS / PE
  - indvAimPriceT/L     个股目标价（高/低）
  - title/orgSName/researcher/publishDate   研报明细

设计原则：
  - 单一可靠数据源，逐字段解析，任一缺失不影响其余。
  - 不编造数据：接口失败时返回空结构并标注 source_status。
  - 评级统一映射到 1~5 分，便于下游融合。
"""
from __future__ import annotations

import sys
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "pkg"))
from crawl_utils import fetch_json  # noqa: E402

# ── 评级映射（统一到 1~5 分）─────────────────────────────────
RATING_SCORE_MAP = {
    "买入": 5, "强烈推荐": 5, "强推": 5, "推荐": 4, "增持": 4, "加仓": 4,
    "优于大市": 4, "超配": 4, "谨慎增持": 4, "中性": 3, "持有": 3, "同步": 3,
    "标配": 3, "观望": 3, "减持": 2, "谨慎": 2, "谨慎推荐": 3, "卖出": 1,
    "回避": 1, "跑输大市": 1, "低配": 2,
}
RATING_LEVELS = ["买入", "增持", "中性", "减持", "卖出"]


def _rating_to_score(name: str) -> Optional[int]:
    if not name:
        return None
    name = name.strip()
    if name in RATING_SCORE_MAP:
        return RATING_SCORE_MAP[name]
    for k, v in RATING_SCORE_MAP.items():
        if k in name:
            return v
    return None


def _score_to_label(score: float) -> str:
    if score >= 4.5:
        return "买入"
    elif score >= 3.5:
        return "增持"
    elif score >= 2.5:
        return "中性"
    elif score >= 1.5:
        return "减持"
    else:
        return "卖出"


def _to_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A", "null", "0", "0.00", "0.0000"):
            # "0" 视为无效（评级/目标价/EPS 不会真为0）
            return default
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _date_days_ago(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


class BrokerResearcher:
    """券商研究数据采集器（东方财富 reportapi）"""

    def __init__(self, recent_days: int = 365):
        self.recent_days = recent_days

    # ── 抓取研报列表（含评级/预期/目标价全部字段）──────────────
    def fetch_research_reports(self, code: str, limit: int = 50) -> List[Dict]:
        code = str(code).zfill(6)
        url = (
            "https://reportapi.eastmoney.com/report/list?"
            f"industryCode=*&pageSize={limit}&industry=*&rating=*&ratingChange=*&"
            f"beginTime={_date_days_ago(self.recent_days)}&"
            f"endTime={datetime.now().strftime('%Y-%m-%d')}&"
            f"pageNo=1&fields=&qType=0&orgCode=&code={code}&"
            "rptType=SECURITIES_RESEARCH_REPORT"
        )
        try:
            data = fetch_json(url, timeout=10)
        except Exception:
            data = None
        reports = []
        if not data or not isinstance(data, dict):
            return reports
        for r in (data.get("data") or [])[:limit]:
            try:
                rating_name = r.get("emRatingName") or r.get("sRatingName") or ""
                reports.append({
                    "title": r.get("title") or "",
                    "org": r.get("orgSName") or r.get("orgName") or "",
                    "researcher": r.get("researcher") or r.get("author") or "",
                    "date": (r.get("publishDate") or "")[:10],
                    "rating": rating_name,
                    "score": _rating_to_score(rating_name),
                    "target_price": _to_float(r.get("indvAimPriceT")),
                    "industry": r.get("industryName") or r.get("indvInduName") or "",
                    # 一致预期 EPS / PE
                    "eps_this_year": _to_float(r.get("predictThisYearEps")),
                    "eps_next_year": _to_float(r.get("predictNextYearEps")),
                    "eps_next_two_year": _to_float(r.get("predictNextTwoYearEps")),
                    "pe_this_year": _to_float(r.get("predictThisYearPe")),
                    "pe_next_year": _to_float(r.get("predictNextYearPe")),
                    "rating_change": r.get("ratingChange") or "",
                    "url": f"https://data.eastmoney.com/report/zw_stock.jshtml?encodeUrl={r.get('encodeUrl','')}",
                })
            except Exception:
                continue
        return reports

    # ── 评级分布 ─────────────────────────────────────────────
    def rating_distribution(self, reports: List[Dict]) -> Dict:
        dist = {k: 0 for k in RATING_LEVELS}
        scores, targets = [], []
        for r in reports:
            s = r.get("score")
            if s is not None:
                scores.append(s)
                dist[_score_to_label(s)] = dist.get(_score_to_label(s), 0) + 1
            tp = r.get("target_price")
            if tp and tp > 0:
                targets.append(tp)
        avg_score = sum(scores) / len(scores) if scores else 3.0
        return {
            "distribution": dist,
            "total_ratings": len(scores),
            "avg_score": round(avg_score, 2),
            "consensus": _score_to_label(avg_score),
            "target_price_min": round(min(targets), 2) if targets else None,
            "target_price_max": round(max(targets), 2) if targets else None,
            "target_price_mean": round(sum(targets) / len(targets), 2) if targets else None,
            "target_price_count": len(targets),
        }

    # ── 一致预期 EPS/PE（取所有研报的中位数，更稳健）──────────
    def consensus_forecast(self, reports: List[Dict]) -> Dict:
        def _median(vals):
            vals = sorted(v for v in vals if v is not None and v > 0)
            if not vals:
                return None
            n = len(vals)
            return round(vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2, 4)

        return {
            "available": bool(reports),
            "eps_this_year": _median([r.get("eps_this_year") for r in reports]),
            "eps_next_year": _median([r.get("eps_next_year") for r in reports]),
            "eps_next_two_year": _median([r.get("eps_next_two_year") for r in reports]),
            "pe_this_year": _median([r.get("pe_this_year") for r in reports]),
            "pe_next_year": _median([r.get("pe_next_year") for r in reports]),
            "sample_count": len(reports),
        }

    # ── 综合分析 ─────────────────────────────────────────────
    def analyze(self, code: str, limit: int = 50) -> Dict:
        code = str(code).zfill(6)
        reports = self.fetch_research_reports(code, limit=limit)
        dist = self.rating_distribution(reports)
        forecast = self.consensus_forecast(reports)

        # 券商面得分：avg_score 1~5 -> 中心3为0 映射 -100~+100
        avg = dist["avg_score"]
        broker_score = max(-100.0, min(100.0, (avg - 3.0) * 50.0))

        # 目标价隐含空间（用最近一份研报的目标价与最近一份的现价近似）
        # reportapi 不直接返回现价；隐含空间由调用方结合实时行情计算，这里仅给目标价
        return {
            "code": code,
            "name": reports[0].get("industry") if reports else "",
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "consensus_rating": dist["consensus"],
            "avg_rating_score": dist["avg_score"],
            "rating_distribution": dist["distribution"],
            "total_ratings": dist["total_ratings"],
            "target_price": {
                "min": dist["target_price_min"],
                "max": dist["target_price_max"],
                "mean": dist["target_price_mean"],
                "count": dist["target_price_count"],
            },
            "consensus_forecast": forecast,
            "recent_reports": [
                {k: r[k] for k in ("title", "org", "researcher", "date", "rating", "url")}
                for r in reports[:10]
            ],
            "broker_score": round(broker_score, 1),  # -100~+100，供融合用
            "source_status": "ok" if reports else "empty",
        }


# ── 模块级便捷函数 ──────────────────────────────────────────
def analyze_broker_research(code: str) -> Dict:
    """便捷入口：综合券商研究分析"""
    return BrokerResearcher().analyze(code)


def implied_upside(target_price_mean: Optional[float], current_price: Optional[float]) -> Optional[float]:
    """目标价隐含上涨空间 %"""
    if not target_price_mean or not current_price or current_price <= 0:
        return None
    return round((target_price_mean - current_price) / current_price * 100, 2)


def format_broker_report(result: Dict) -> str:
    """格式化为可读文本"""
    lines = []
    hr = "=" * 70
    lines.append(hr)
    lines.append(f"  📑 券商研究报告  |  {result.get('code')}")
    lines.append(hr)
    lines.append(f"  一致评级: {result.get('consensus_rating')}  "
                 f"(平均分 {result.get('avg_rating_score')}/5, "
                 f"共 {result.get('total_ratings')} 份研报)")
    dist = result.get("rating_distribution", {})
    if any(dist.values()):
        lines.append("  评级分布: " + "  ".join(f"{k}{v}" for k, v in dist.items() if v))
    tp = result.get("target_price", {})
    if tp.get("mean"):
        lines.append(f"  目标价: 最低 {tp.get('min')} / 均值 {tp.get('mean')} / 最高 {tp.get('max')}"
                     f"  ({tp.get('count')} 份给出)")
    fc = result.get("consensus_forecast", {})
    if fc.get("available"):
        lines.append(f"  一致预期 EPS: 今年 {fc.get('eps_this_year')} / 明年 {fc.get('eps_next_year')}"
                     f" / 后年 {fc.get('eps_next_two_year')}  (基于 {fc.get('sample_count')} 份研报中位数)")
        if fc.get("pe_this_year"):
            lines.append(f"  一致预期 PE: 今年 {fc.get('pe_this_year')} / 明年 {fc.get('pe_next_year')}")
    reports = result.get("recent_reports", [])
    if reports:
        lines.append("  近期研报:")
        for r in reports[:5]:
            lines.append(f"    · [{r.get('date')}] {r.get('title','')[:40]}  -- {r.get('org')}({r.get('rating')})")
    lines.append(f"  券商面得分: {result.get('broker_score'):+.1f}  (映射 -100~+100)")
    lines.append(f"  数据源: {result.get('source_status')}")
    lines.append(hr)
    return "\n".join(lines)


def main():
    print("=== 券商研究测试：贵州茅台 600519 ===")
    r = analyze_broker_research("600519")
    print(format_broker_report(r))


if __name__ == "__main__":
    main()
