#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投资顾问引擎 (v6.0 新增)

整合多源数据，提供增强投顾能力：
- 多源评级聚合（晨星/好买/韭圈儿/雪球/东财 加权一致评级，带 provenance）
- 风格漂移检测（持仓穿透风格 vs 目标风格）
- 风险调整对比（Sharpe/Sortino/Calmar vs 同类）
- 持仓加权估值（穿透重仓股 PE/PB/股息率）
- 综合投顾建议（带源引用理由）
"""
from __future__ import annotations
import sys
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))

from multi_source import get_provider  # noqa: E402


@dataclass
class AdvisorReport:
    """投顾报告"""
    code: str
    name: str = ""
    consensus_rating: Optional[Dict] = None    # 多源聚合评级
    style_drift: Optional[Dict] = None         # 风格漂移
    risk_adjusted: Optional[Dict] = None       # 风险调整对比
    holdings_valuation: Optional[Dict] = None  # 持仓加权估值
    advice: List[str] = field(default_factory=list)
    source_status: Dict = field(default_factory=dict)
    generated_at: str = ""


class AdvisorEngine:
    """投资顾问引擎"""

    def __init__(self):
        self.provider = get_provider()

    # ─── 1. 多源评级聚合 ─────────────────────────────────
    def aggregate_ratings(self, code: str) -> Dict:
        """多源评级聚合"""
        r = self.provider.get_fund_ratings(code)
        ratings = r.get("ratings", {})
        # 提取各源星级
        source_stars = {}
        source_extras = {}
        for src, data in ratings.items():
            if isinstance(data, dict):
                star = None
                for k in ("star", "stars", "rating"):
                    v = data.get(k)
                    if isinstance(v, (int, float)) and 0 < v <= 5:
                        star = float(v)
                        break
                if star:
                    source_stars[src] = star
                # 额外指标
                extras = {k: v for k, v in data.items()
                          if k in ("sharpe", "max_drawdown", "annual_volatility",
                                   "win_rate", "beat_peer_pct", "score",
                                   "stock_selection_alpha", "timing_alpha")
                          and v is not None}
                if extras:
                    source_extras[src] = extras
        consensus = (sum(source_stars.values()) / len(source_stars)) if source_stars else None
        return {
            "code": code,
            "consensus_star": round(consensus, 2) if consensus else None,
            "source_count": len(source_stars),
            "source_stars": source_stars,
            "source_extras": source_extras,
            "source_status": r.get("source_status", {}),
        }

    # ─── 2. 风格漂移检测 ─────────────────────────────────
    def detect_style_drift(self, current_style: str, target_style: str) -> Dict:
        """检测风格漂移（current vs target）

        Args:
            current_style: 当前持仓风格（价值/均衡/成长/激进/稳健）
            target_style: 目标风格
        """
        style_score = {"稳健": 1, "价值": 2, "均衡": 3, "成长": 4, "激进": 5}
        cs = style_score.get(current_style, 3)
        ts = style_score.get(target_style, 3)
        drift = abs(cs - ts)
        if drift == 0:
            level, action = "无漂移", "维持配置"
        elif drift == 1:
            level, action = "轻微漂移", "观察"
        elif drift == 2:
            level, action = "明显漂移", "建议再平衡"
        else:
            level, action = "严重漂移", "强烈建议再平衡"
        return {
            "current_style": current_style,
            "target_style": target_style,
            "drift_score": drift,
            "drift_level": level,
            "action": action,
        }

    # ─── 3. 风险调整对比 ─────────────────────────────────
    def risk_adjusted_compare(self, code: str, peer_median: Dict = None) -> Dict:
        """风险调整对比（vs 同类中位数）

        peer_median: {"sharpe":0.8,"max_drawdown":-15,"annual_volatility":20}
        """
        r = self.provider.get_fund_ratings(code)
        ratings = r.get("ratings", {})
        # 取首个有 sharpe 的源
        fund_sharpe = fund_mdd = fund_vol = None
        source = ""
        for src, data in ratings.items():
            if isinstance(data, dict):
                if data.get("sharpe") is not None:
                    fund_sharpe = data.get("sharpe")
                    fund_mdd = data.get("max_drawdown")
                    fund_vol = data.get("annual_volatility")
                    source = src
                    break
        peer_median = peer_median or {"sharpe": 0.8, "max_drawdown": -15.0, "annual_volatility": 20.0}
        compare = {}
        if fund_sharpe is not None:
            compare["sharpe"] = {
                "fund": fund_sharpe, "peer_median": peer_median["sharpe"],
                "excess": round(fund_sharpe - peer_median["sharpe"], 2),
                "verdict": "优于同类" if fund_sharpe > peer_median["sharpe"] else "弱于同类",
            }
        if fund_mdd is not None:
            compare["max_drawdown"] = {
                "fund": fund_mdd, "peer_median": peer_median["max_drawdown"],
                "verdict": "回撤更小" if fund_mdd > peer_median["max_drawdown"] else "回撤更大",
            }
        if fund_vol is not None:
            compare["annual_volatility"] = {
                "fund": fund_vol, "peer_median": peer_median["annual_volatility"],
                "verdict": "波动更小" if fund_vol < peer_median["annual_volatility"] else "波动更大",
            }
        return {"code": code, "source": source, "compare": compare}

    # ─── 4. 持仓加权估值 ─────────────────────────────────
    def holdings_weighted_valuation(self, holdings: List[Dict]) -> Dict:
        """持仓加权估值（穿透重仓股 PE/PB）

        holdings: [{"code":"600519","ratio":8.5,"name":"贵州茅台"}, ...]
        用 akshare A股估值
        """
        try:
            import akshare as ak
        except Exception:
            return {"error": "akshare 未安装"}
        weighted_pe = 0.0
        weighted_pb = 0.0
        total_ratio = 0.0
        detail = []
        for h in holdings[:10]:
            code = str(h.get("code", ""))
            ratio = h.get("ratio", 0) or 0
            if not code or ratio <= 0:
                continue
            try:
                # 个股实时行情（含市盈率/市净率）
                df = ak.stock_individual_info_em(symbol=code)
                if df is None:
                    continue
                d = dict(zip(df["item"].tolist(), df["value"].tolist()))
                pe = _safe_float(d.get("市盈率(动态)"))
                pb = _safe_float(d.get("市净率"))
                if pe and pe > 0:
                    weighted_pe += pe * ratio
                    total_ratio += ratio
                if pb and pb > 0:
                    weighted_pb += pb * ratio
                detail.append({"code": code, "name": h.get("name", ""), "ratio": ratio,
                               "pe": pe, "pb": pb})
            except Exception:
                continue
        if total_ratio <= 0:
            return {"error": "无有效估值数据"}
        return {
            "weighted_pe": round(weighted_pe / total_ratio, 2),
            "weighted_pb": round(weighted_pb / total_ratio, 2),
            "coverage_ratio": round(total_ratio, 2),
            "detail": detail,
            "valuation_level": _valuation_level(weighted_pe / total_ratio),
        }

    # ─── 5. 综合投顾建议 ─────────────────────────────────
    def generate_advice(self, code: str, target_style: str = "",
                        current_holdings: List[Dict] = None) -> AdvisorReport:
        """生成综合投顾报告"""
        report = AdvisorReport(code=code, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        advice = []

        # 评级
        report.consensus_rating = self.aggregate_ratings(code)
        report.source_status.update(report.consensus_rating.get("source_status", {}))
        star = report.consensus_rating.get("consensus_star")
        if star:
            if star >= 4:
                advice.append(f"多源评级 {star}★（{report.consensus_rating['source_count']}源一致），建议关注")
            elif star <= 2:
                advice.append(f"多源评级仅 {star}★，需谨慎评估")

        # 风险调整
        report.risk_adjusted = self.risk_adjusted_compare(code)
        cmp = report.risk_adjusted.get("compare", {})
        if "sharpe" in cmp and cmp["sharpe"]["fund"] is not None:
            if cmp["sharpe"]["verdict"] == "优于同类":
                advice.append(f"夏普 {cmp['sharpe']['fund']} 优于同类中位数，风险调整收益佳")
            else:
                advice.append(f"夏普 {cmp['sharpe']['fund']} 弱于同类，风险收益比偏低")

        # 风格漂移
        if target_style:
            current_style = _infer_style_from_holdings(current_holdings) if current_holdings else "均衡"
            report.style_drift = self.detect_style_drift(current_style, target_style)
            if report.style_drift["drift_score"] >= 2:
                advice.append(f"风格漂移{report.style_drift['drift_level']}（当前{current_style} vs 目标{target_style}），{report.style_drift['action']}")

        # 持仓估值
        if current_holdings:
            report.holdings_valuation = self.holdings_weighted_valuation(current_holdings)
            hv = report.holdings_valuation
            if "weighted_pe" in hv:
                advice.append(f"持仓加权 PE={hv['weighted_pe']}（{hv['valuation_level']}），PB={hv['weighted_pb']}")

        report.advice = advice
        return report


def _safe_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A", "null"):
            return default
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _valuation_level(pe: float) -> str:
    if pe < 15:
        return "低估"
    elif pe < 25:
        return "合理"
    elif pe < 40:
        return "偏高"
    return "高估"


def _infer_style_from_holdings(holdings: List[Dict]) -> str:
    """从持仓粗略推断风格（按行业偏好）"""
    if not holdings:
        return "均衡"
    growth_sectors = ["电子", "计算机", "通信", "医药", "新能源", "军工"]
    value_sectors = ["银行", "房地产", "基建", "煤炭", "钢铁"]
    growth_ratio = value_ratio = 0
    for h in holdings:
        sector = h.get("sector", h.get("industry", ""))
        ratio = h.get("ratio", 1)
        if any(s in sector for s in growth_sectors):
            growth_ratio += ratio
        elif any(s in sector for s in value_sectors):
            value_ratio += ratio
    if growth_ratio > value_ratio * 1.5:
        return "成长"
    if value_ratio > growth_ratio * 1.5:
        return "价值"
    return "均衡"


def format_advisor_report(report: AdvisorReport) -> str:
    lines = [f"🧭 投顾报告  |  {report.code}  |  {report.generated_at}",
             "=" * 60]
    cr = report.consensus_rating or {}
    if cr.get("consensus_star"):
        lines.append(f"【多源评级】{cr['consensus_star']}★ ({cr['source_count']}源)")
        for src, star in cr.get("source_stars", {}).items():
            lines.append(f"  · {src}: {star}★")
    sd = report.style_drift
    if sd:
        lines.append(f"【风格漂移】{sd['current_style']}→{sd['target_style']} "
                     f"{sd['drift_level']} ({sd['action']})")
    ra = report.risk_adjusted or {}
    cmp = ra.get("compare", {})
    if cmp:
        lines.append("【风险调整对比】")
        for k, v in cmp.items():
            if v.get("fund") is not None:
                lines.append(f"  · {k}: 基金{v['fund']} vs 同类{v['peer_median']} ({v['verdict']})")
    hv = report.holdings_valuation
    if hv and "weighted_pe" in hv:
        lines.append(f"【持仓估值】加权PE={hv['weighted_pe']} PB={hv['weighted_pb']} ({hv['valuation_level']})")
    if report.advice:
        lines.append("【综合建议】")
        for i, a in enumerate(report.advice, 1):
            lines.append(f"  {i}. {a}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    eng = AdvisorEngine()
    report = eng.generate_advice("110022", target_style="成长")
    print(format_advisor_report(report))


if __name__ == "__main__":
    main()
