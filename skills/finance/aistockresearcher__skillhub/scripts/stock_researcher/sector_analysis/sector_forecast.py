#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块趋势预测 (v7.0.0)
=======================
多周期（1M/3M/6M）板块走势趋势预测。
支持 A股/港股/美股板块，融合资金流向+政策驱动+宏观环境+代表股信号。

纯 Python 标准库，零依赖。

用法:
    from stock_researcher.sector_analysis.sector_forecast import SectorForecaster
    fc = SectorForecaster()
    result = fc.forecast("新能源", market="cn", horizons=["1M", "3M"])
    ranking = fc.rank_sectors(market="cn", horizon="1M")
"""

import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@dataclass
class SectorForecastResult:
    """板块预测结果"""
    sector: str
    market: str
    timestamp: str

    # 各周期预测
    horizons: Dict[str, dict] = field(default_factory=dict)

    # 综合评分
    momentum_score: float = 0      # 动量得分（近期涨跌）
    flow_score: float = 0          # 资金流向得分
    policy_score: float = 0        # 政策驱动得分
    macro_score: float = 0         # 宏观适配得分
    composite_score: float = 0     # 综合得分

    # 排名与推荐
    rank: int = 0
    recommendation: str = ""       # "强烈推荐"/"推荐"/"中性"/"回避"
    risk_factors: List[str] = field(default_factory=list)
    summary: str = ""


# ── 板块映射（跨市场） ──────────────────────
# 各市场板块 → 代表股列表
SECTOR_REPRESENTATIVES = {
    "cn": {
        "银行": ["600036", "601318", "600016"],
        "非银金融": ["601601", "600837", "601628"],
        "房地产": ["600048", "001979", "600383"],
        "医药生物": ["600276", "000538", "600196"],
        "食品饮料": ["600519", "000858", "002304"],
        "汽车": ["600104", "002594", "000625"],
        "电子": ["000725", "002241", "603986"],
        "计算机": ["000977", "002230", "601360"],
        "通信": ["600570", "000063", "002312"],
        "传媒": ["002027", "300058", "603444"],
        "军工": ["600760", "000768", "601989"],
        "新能源": ["300750", "002594", "600900"],
        "化工": ["600309", "000792", "002601"],
        "有色金属": ["600111", "000333", "601899"],
        "机械设备": ["601669", "600031", "002352"],
    },
    "hk": {
        "科技": ["00700", "09988", "03690"],
        "金融": ["00005", "00388", "01299"],
        "地产建筑": ["00016", "00017", "00688"],
        "消费": ["02020", "02331", "09633"],
        "能源": ["00883", "00857", "00386"],
        "医药": ["02269", "01177", "01801"],
        "汽车": ["01211", "00175", "09863"],
        "电信": ["00941", "00728", "00762"],
    },
    "us": {
        "信息技术": ["AAPL", "MSFT", "NVDA"],
        "金融": ["JPM", "BAC", "GS"],
        "医疗保健": ["JNJ", "UNH", "PFE"],
        "消费": ["AMZN", "TSLA", "HD"],
        "能源": ["XOM", "CVX", "COP"],
        "工业": ["CAT", "GE", "BA"],
        "通信服务": ["GOOGL", "META", "NFLX"],
    },
}

# 板块 → 关注的政策类别
SECTOR_POLICY_SENSITIVITY = {
    "新能源": ["能源政策", "碳中和", "补贴"],
    "银行": ["货币政策", "利率", "金融监管"],
    "房地产": ["房地产调控", "信贷政策", "土地政策"],
    "医药生物": ["医疗改革", "药品集采", "FDA审批"],
    "科技": ["科技监管", "反垄断", "数据安全"],
    "汽车": ["新能源汽车补贴", "排放标准", "贸易关税"],
    "电子": ["半导体政策", "出口管制", "技术制裁"],
    "军工": ["国防预算", "地缘政治", "军备"],
    "能源": ["OPEC+", "碳中和", "能源转型"],
    "消费": ["消费刺激", "居民收入", "零售政策"],
}


class SectorForecaster:
    """
    板块趋势预测器。

    评分维度：
      1. 动量面(25%): 代表股近期涨跌趋势
      2. 资金面(25%): 板块资金净流向
      3. 政策面(30%): 对板块影响最大的政策信号
      4. 宏观面(20%): 全球风险偏好适配度

    预测周期：1M(22日) / 3M(63日) / 6M(126日)
    """

    HORIZON_DAYS = {"1M": 22, "3M": 63, "6M": 126}
    HORIZON_LABELS = {"1M": "未来一个月", "3M": "未来三个月", "6M": "未来半年"}

    # 周期权重分配
    HORIZON_WEIGHTS = {
        "1M": {"momentum": 0.35, "flow": 0.30, "policy": 0.20, "macro": 0.15},
        "3M": {"momentum": 0.20, "flow": 0.20, "policy": 0.35, "macro": 0.25},
        "6M": {"momentum": 0.10, "flow": 0.15, "policy": 0.40, "macro": 0.35},
    }

    def __init__(self):
        pass

    def forecast(
        self, sector: str, market: str = "cn",
        horizons: List[str] = None,
    ) -> SectorForecastResult:
        """
        预测单个板块多周期走势。

        Args:
            sector: 板块名称
            market: 市场（cn/hk/us）
            horizons: 预测周期列表

        Returns:
            SectorForecastResult
        """
        horizons = horizons or list(self.HORIZON_DAYS.keys())
        reps = SECTOR_REPRESENTATIVES.get(market, {}).get(sector, [])

        # 1) 动量分析（v9.0：优先用真实多周期相对强度 RS，单日动量作降级）
        momentum = self._analyze_momentum(sector, reps, market)

        # 2) 资金流向分析
        flow = self._analyze_flow(sector, market, reps)

        # 3) 政策分析
        policy = self._analyze_policy(sector, market)

        # 4) 宏观适配分析
        macro = self._analyze_macro_fit(sector)

        # 各周期预测
        horizon_results = {}
        risk_factors = []

        for h in horizons:
            h_result = self._predict_horizon(
                momentum, flow, policy, macro, h, sector
            )
            horizon_results[h] = h_result
            risk_factors.extend(h_result.get("risks", []))

        risk_factors = list(dict.fromkeys(risk_factors))[:5]

        # 综合得分
        w = self.HORIZON_WEIGHTS.get("1M", {})
        composite = (
            momentum["score"] * w.get("momentum", 0.25) +
            flow["score"] * w.get("flow", 0.25) +
            policy["score"] * w.get("policy", 0.30) +
            macro["score"] * w.get("macro", 0.20)
        )

        # 推荐级别
        if composite > 30:
            recommendation = "强烈推荐"
        elif composite > 10:
            recommendation = "推荐"
        elif composite > -15:
            recommendation = "中性"
        else:
            recommendation = "回避"

        summary = f"{sector}板块综合得分{composite:+d}/100，{recommendation}。"

        return SectorForecastResult(
            sector=sector,
            market=market,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            horizons=horizon_results,
            momentum_score=momentum["score"],
            flow_score=flow["score"],
            policy_score=policy["score"],
            macro_score=macro["score"],
            composite_score=round(composite, 1),
            recommendation=recommendation,
            risk_factors=risk_factors,
            summary=summary,
        )

    def _analyze_momentum(self, sector: str, reps: List[str], market: str) -> dict:
        """板块动量分析（v9.0：优先真实多周期相对强度 RS，失败降级单日动量）。

        评分映射到 -100~+100：
          - Mansfield RPS（>0 强于基准，约 ±20 量级）→ ×5
          - 20 日相对收益（pct）→ ×2
          - 60 日相对收益（pct）→ ×0.8
          全部相对基准，识别中期强势/弱势，优于旧版「当日涨跌×20」。
        """
        if not reps:
            return {"score": 0, "note": "无代表股数据"}

        # 主路径：真实相对强度
        try:
            from stock_researcher.sector_analysis.relative_strength import (
                SectorRelativeStrength,
            )
            rs = SectorRelativeStrength().relative_strength(
                sector, market=market, lookups=(20, 60), days=130,
            )
            if rs.series_len >= 10:
                rps = rs.rps_score
                d20 = rs.rs_lookups.get("20d", 0.0)
                d60 = rs.rs_lookups.get("60d", 0.0)
                score = rps * 5 + d20 * 2 + d60 * 0.8
                score = max(-100.0, min(100.0, score))
                return {
                    "score": round(score, 1),
                    "rps": round(rps, 2),
                    "rs_trend": rs.rs_trend,
                    "data_mode": rs.data_mode,
                    "note": f"RS({rs.benchmark}) RPS{rps:+.1f} 20d{d20:+.1f}% 60d{d60:+.1f}%",
                }
        except Exception:
            pass

        # 降级：单日代表股动量（旧逻辑，保持可用）
        try:
            from stock_researcher.data.market import MarketData
            md = MarketData()
            rt = md.fetch_realtime(reps)
            scores = []
            for code in reps:
                if code in rt:
                    chg = rt[code].get("change_pct", 0)
                    # 涨跌幅映射到 -100~+100
                    score = max(-100, min(100, chg * 20))
                    scores.append(score)
            if scores:
                return {"score": round(sum(scores) / len(scores), 1),
                        "count": len(scores), "note": f"{len(scores)}只代表股单日动量(降级)"}
        except Exception:
            pass
        return {"score": 0, "note": "动量数据暂不可用"}

    def _analyze_flow(self, sector: str, market: str, reps: List[str]) -> dict:
        """资金流向分析"""
        if not reps or market != "cn":
            return {"score": 0, "note": "资金流向数据仅支持A股"}

        try:
            from stock_researcher.data.money_flow import MoneyFlowData
            mf = MoneyFlowData()
            flows = mf.get_money_flow(reps)
            total_score = 0
            count = 0
            for code, data in flows.items():
                score = data.get("score", 0) if isinstance(data, dict) else 0
                total_score += score
                count += 1
            if count > 0:
                return {"score": round(total_score / count, 1),
                        "note": f"{count}只代表股平均资金信号"}
        except Exception:
            pass
        return {"score": 0, "note": "资金数据暂不可用"}

    def _analyze_policy(self, sector: str, market: str) -> dict:
        """政策驱动分析"""
        try:
            from stock_researcher.policy.policy_analyzer import PolicyAnalyzer
            pa = PolicyAnalyzer()
            impact = pa.analyze_sector_impact(sector, market)
            return {
                "score": impact.get("score", 0),
                "direction": impact.get("direction", "中性"),
                "note": impact.get("summary", ""),
            }
        except Exception:
            pass

        # 回退：基于板块大类推断
        policy_keys = SECTOR_POLICY_SENSITIVITY.get(sector, [])
        return {"score": 0, "direction": "中性",
                "note": f"关注: {', '.join(policy_keys[:3])}" if policy_keys else "无特定政策驱动"}

    def _analyze_macro_fit(self, sector: str) -> dict:
        """宏观环境适配度"""
        # 不同板块在 risk-on / risk-off 环境下的表现不同
        # 防御型板块（银行/公用事业）：risk-off 时相对受益
        # 成长型板块（科技/新能源/医药）：risk-on 时更活跃
        defensive = {"银行", "公用事业", "消费", "医疗保健", "电信"}
        aggressive = {"科技", "新能源", "电子", "军工", "汽车", "信息技术"}

        try:
            from stock_researcher.data.global_market import get_global_risk_appetite
            risk = get_global_risk_appetite()
            risk_score = risk.get("score", 0)
            risk_label = risk.get("label", "neutral")

            if sector in defensive:
                # risk-off 时防御型受益
                fit_score = -risk_score * 0.3
                note = f"{'避险' if risk_score < -10 else '正常'}环境下防御属性{'受益' if risk_score < -10 else '一般'}"
            elif sector in aggressive:
                # risk-on 时成长型受益
                fit_score = risk_score * 0.3
                note = f"{'risk-on' if risk_score > 10 else '正常'}环境下成长属性{'受益' if risk_score > 10 else '一般'}"
            else:
                fit_score = 0
                note = "宏观敏感度适中"

            return {"score": round(fit_score, 1), "label": risk_label, "note": note}
        except Exception:
            pass
        return {"score": 0, "label": "neutral", "note": "宏观数据暂不可用"}

    def _predict_horizon(
        self, momentum: dict, flow: dict, policy: dict,
        macro: dict, horizon: str, sector: str,
    ) -> dict:
        """单周期预测"""
        w = self.HORIZON_WEIGHTS.get(horizon, self.HORIZON_WEIGHTS["1M"])
        composite = (
            momentum["score"] * w["momentum"] +
            flow["score"] * w["flow"] +
            policy["score"] * w["policy"] +
            macro["score"] * w["macro"]
        )

        if composite > 25:
            direction = "领涨"
        elif composite > 10:
            direction = "强于大盘"
        elif composite > -10:
            direction = "同步大盘"
        elif composite > -25:
            direction = "弱于大盘"
        else:
            direction = "领跌"

        confidence = min(0.9, 0.4 + abs(composite) / 100 * 0.5)

        risks = []
        if momentum["score"] < -30:
            risks.append("板块动量走弱")
        if flow["score"] < -20:
            risks.append("资金持续流出")
        if policy["score"] < -20:
            risks.append(f"政策面利空({sector})")

        return {
            "horizon": horizon,
            "horizon_label": self.HORIZON_LABELS.get(horizon, horizon),
            "direction": direction,
            "composite_score": round(composite, 1),
            "confidence": round(confidence, 2),
            "drivers": {
                "momentum": round(momentum["score"] * w["momentum"], 1),
                "flow": round(flow["score"] * w["flow"], 1),
                "policy": round(policy["score"] * w["policy"], 1),
                "macro": round(macro["score"] * w["macro"], 1),
            },
            "risks": risks,
        }

    def rank_sectors(
        self, market: str = "cn", horizon: str = "1M", top_n: int = 10
    ) -> List[SectorForecastResult]:
        """
        板块排名：按指定周期预测得分排序。

        Args:
            market: 市场（cn/hk/us）
            horizon: 排名周期
            top_n: 返回前N个

        Returns:
            List[SectorForecastResult] 按得分降序排列
        """
        sectors = SECTOR_REPRESENTATIVES.get(market, {})
        results = []
        for sector_name in sectors:
            try:
                result = self.forecast(sector_name, market, [horizon])
                result.composite_score = result.horizons.get(horizon, {}).get(
                    "composite_score", 0)
                results.append(result)
                time.sleep(0.1)  # 避免请求过快
            except Exception:
                pass

        results.sort(key=lambda r: r.composite_score, reverse=True)
        for i, r in enumerate(results[:top_n]):
            r.rank = i + 1

        return results[:top_n]

    def format_ranking(
        self, results: List[SectorForecastResult], market: str = "cn"
    ) -> str:
        """格式化板块排名报告"""
        market_labels = {"cn": "A股", "hk": "港股", "us": "美股"}
        lines = [
            f"\n{'='*60}",
            f"  📊 {market_labels.get(market, market)}板块趋势排名 v7.0",
            f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*60}",
            f"  {'排名':<6} {'板块':<12} {'方向':<12} {'得分':>6} {'推荐'}",
            f"  {'-'*50}",
        ]
        for r in results:
            h = r.horizons.get("1M", {})
            lines.append(
                f"  {r.rank:<6} {r.sector:<12} {h.get('direction', '--'):<12} "
                f"{r.composite_score:>+5.0f}  {r.recommendation}"
            )
        lines.append(f"{'='*60}")
        return "\n".join(lines)


# ── 便捷函数 ──

def forecast_sector(sector: str, market: str = "cn") -> SectorForecastResult:
    """便捷函数：预测板块趋势"""
    return SectorForecaster().forecast(sector, market)


def rank_sectors(market: str = "cn", horizon: str = "1M",
                 top_n: int = 10) -> List[SectorForecastResult]:
    """便捷函数：板块排名"""
    return SectorForecaster().rank_sectors(market, horizon, top_n)
