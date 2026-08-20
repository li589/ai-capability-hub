#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业结构分析（v5.0 新增）

基于波特五力模型 + 行业生命周期 + 竞争结构（HHI）：
- Porter 五力: 供应商议价权 / 客户议价权 / 新进入者威胁 / 替代品威胁 / 竞争强度
- 行业生命周期: 新兴 / 成长 / 成熟 / 衰退
- 竞争结构: HHI 指数（用行业内公司市值计算）
- 行业吸引力: 0-100 综合评分

输出: attractiveness_score + lifecycle_stage + porter_5_forces + key_drivers + risks
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..data.financial_statements import fetch_income_statement, filter_recent_n_years
from ..data.market import MarketData
from ..data.batch import fetch_batch_concurrent


# 申万一级行业成分股（简化版，每个行业取代表性公司）
# 复用 recommendation_engine.py 的 SECTOR_CODES 思路
SECTOR_REPS: Dict[str, List[str]] = {
    "银行": ["600036", "601398", "601288", "601939", "601318", "600000", "601166", "600016"],
    "白酒": ["600519", "000858", "000568", "002304", "000596", "600779", "000799", "603369"],
    "半导体": ["688981", "688012", "002049", "300760", "300142", "603501", "300661", "688036"],
    "医药生物": ["600276", "300760", "000538", "600436", "300015", "600196", "000963", "300003"],
    "新能源": ["300750", "002594", "601012", "601877", "300274", "600438", "002129", "688005"],
    "消费电子": ["002241", "300433", "002475", "000725", "603160", "300124", "002384", "300054"],
    "食品饮料": ["600887", "603288", "603899", "000876", "002714", "603345", "600872", "000895"],
    "家电": ["000333", "000651", "600690", "002508", "000100", "002032", "600859", "002959"],
    "汽车": ["600104", "601633", "000625", "600006", "601238", "000550", "600741", "600686"],
    "化工": ["600309", "002493", "600143", "000830", "600486", "000703", "002648", "300285"],
    "建材": ["600585", "000877", "600720", "601636", "600801", "000935", "002233", "603077"],
    "房地产": ["001979", "600048", "000002", "600340", "000069", "600376", "000671", "600208"],
    "钢铁": ["600019", "600010", "000709", "600022", "601899", "600282", "000761", "600507"],
    "有色金属": ["601899", "600547", "600489", "601600", "603993", "000831", "002460", "600516"],
    "计算机": ["000063", "002230", "600271", "000977", "002415", "300033", "600845", "002296"],
}


@dataclass
class IndustryResult:
    """行业分析结果"""
    code: str
    industry: str = ""
    attractiveness_score: float = 0.0
    lifecycle_stage: str = "成熟"  # 新兴/成长/成熟/衰退
    porter_5_forces: Dict[str, float] = field(default_factory=dict)
    hhi: float = 0.0
    industry_growth_rate: float = 0.0
    industry_avg_roe: float = 0.0
    key_drivers: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    insufficient_data: bool = False


def _safe(val, default=0.0) -> float:
    try:
        f = float(val) if val is not None else default
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _guess_industry_by_code(code: str) -> str:
    """根据代码所属常见板块推断行业（简化版，完整推断需要 SW 行业分类）"""
    code = str(code).zfill(6)
    for industry, codes in SECTOR_REPS.items():
        if code in codes:
            return industry
    return ""


class IndustryAnalyzer:
    """行业结构分析器"""

    def __init__(self, years: int = 5):
        self.years = years
        self.market = MarketData()

    def _fetch_industry_data(self, codes: List[str]) -> List[Dict]:
        """批量获取行业内公司的基础数据（营收 + 市值）"""
        # 用实时行情获取市值
        rt = self.market.fetch_realtime(codes)
        # 用利润表获取营收（并发获取）
        from ..data.batch import fetch_batch_concurrent
        from ..data.financial_statements import fetch_income_statement, filter_recent_n_years

        def _get_one_income(code):
            try:
                inc = filter_recent_n_years(fetch_income_statement(code, 2), 2)
                if inc:
                    return inc
            except Exception:
                pass
            return []

        income_map = fetch_batch_concurrent(
            _get_one_income, codes, max_workers=3, sleep_between=0.3, timeout=20
        )

        results: List[Dict] = []
        for code in codes:
            code_str = str(code).zfill(6)
            info = rt.get(code_str, {})
            # 腾讯 mkt_cap 单位是亿元
            market_cap = _safe(info.get("mkt_cap")) * 1e8
            income = income_map.get(code_str, [])
            revenue = _safe(income[0].get("TOTAL_OPERATE_INCOME")) if income else 0
            prev_revenue = _safe(income[1].get("TOTAL_OPERATE_INCOME")) if len(income) > 1 else 0
            if market_cap > 0 or revenue > 0:
                results.append({
                    "code": code_str,
                    "name": info.get("name", ""),
                    "market_cap": market_cap,
                    "revenue": revenue,
                    "prev_revenue": prev_revenue,
                })
        return results

    # ─────────────────────────────────────────────
    # Porter 五力
    # ─────────────────────────────────────────────
    def _calc_porter_5_forces(self, industry_data: List[Dict],
                              target_market_cap: float = 0.0) -> Dict[str, float]:
        """
        计算 Porter 五力（每力 0-5 分，分数越高表示对在位企业越不利）。

        简化版（无供应商/客户集中度数据时用代理指标）:
        - 供应商议价权: 行业平均资产负债率代理（高负债 -> 议价权强）
        - 客户议价权: 行业内营收集中度代理（HHI 低 -> 客户分散 -> 议价权强）
        - 新进入者威胁: 行业平均资产规模门槛（规模大 -> 威胁低）
        - 替代品威胁: 默认中性 3，需外部输入
        - 竞争强度: HHI 指数（HHI 低 -> 竞争激烈）
        """
        forces = {
            "supplier_power": 3.0,
            "buyer_power": 3.0,
            "new_entrant_threat": 3.0,
            "substitute_threat": 3.0,
            "competitive_intensity": 3.0,
        }
        if len(industry_data) < 3:
            return forces

        # HHI（用市值计算）
        caps = [d["market_cap"] for d in industry_data if d["market_cap"] > 0]
        total_cap = sum(caps)
        if total_cap > 0 and len(caps) >= 3:
            shares = [c / total_cap for c in caps]
            hhi = sum(s * s for s in shares) * 10000  # 标准化到 0-10000
            # HHI <1500 低集中度（竞争激烈）；>2500 高集中度
            forces["competitive_intensity"] = max(1, min(5, (1500 - hhi) / 1500 * 5 + 1))
            # 客户议价权（HHI 低 -> 客户分散 -> 议价权强 -> 不利企业）
            forces["buyer_power"] = max(1, min(5, (1500 - hhi) / 1500 * 5 + 1))

        # 新进入者威胁：行业平均资产规模
        avg_cap = total_cap / max(len(caps), 1) if caps else 0
        # 100 亿以下 -> 威胁高；1000 亿以上 -> 威胁低
        if avg_cap < 1e10:
            forces["new_entrant_threat"] = 4.5
        elif avg_cap < 5e10:
            forces["new_entrant_threat"] = 3.5
        elif avg_cap < 1e11:
            forces["new_entrant_threat"] = 2.5
        else:
            forces["new_entrant_threat"] = 1.5

        return forces

    def _calc_hhi(self, industry_data: List[Dict]) -> float:
        """HHI 指数"""
        caps = [d["market_cap"] for d in industry_data if d["market_cap"] > 0]
        total = sum(caps)
        if total <= 0 or len(caps) < 2:
            return 0
        return sum((c / total) ** 2 for c in caps) * 10000

    def _calc_industry_growth(self, industry_data: List[Dict]) -> float:
        """行业营收增长率（中位数）"""
        growths = []
        for d in industry_data:
            if d["prev_revenue"] > 0 and d["revenue"] > 0:
                growths.append((d["revenue"] / d["prev_revenue"] - 1) * 100)
        if not growths:
            return 0
        growths.sort()
        n = len(growths)
        return growths[n // 2]  # 中位数

    def _determine_lifecycle(self, growth_rate: float, avg_roe: float) -> str:
        """判断行业生命周期（数据不足时默认成熟期，不轻易判衰退）"""
        if growth_rate == 0:
            # 无增长数据时默认成熟期（避免误判）
            return "成熟"
        if growth_rate > 20 and avg_roe > 15:
            return "新兴"
        if growth_rate > 10:
            return "成长"
        if growth_rate > 3:
            return "成熟"
        if growth_rate > -5:
            return "成熟"  # 微负增长仍视为成熟期
        return "衰退"

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────
    def analyze(self, code: str, industry: str = "",
                industry_data: Optional[List[Dict]] = None) -> IndustryResult:
        """
        Args:
            code: 股票代码（用于推断行业）
            industry: 指定行业名（如 "白酒"）；空则按代码推断
            industry_data: 预取的行业内公司数据；None 时自动获取
        """
        # 推断行业
        if not industry:
            industry = _guess_industry_by_code(code)
        if not industry or industry not in SECTOR_REPS:
            return IndustryResult(code=code, industry=industry or "未识别",
                                  insufficient_data=True)

        # 获取行业数据
        if industry_data is None:
            codes = SECTOR_REPS[industry]
            try:
                industry_data = self._fetch_industry_data(codes)
            except Exception:
                industry_data = []

        if len(industry_data) < 3:
            return IndustryResult(code=code, industry=industry,
                                  insufficient_data=True,
                                  risks=["行业数据不足，无法计算 HHI/五力"])

        # Porter 五力
        forces = self._calc_porter_5_forces(industry_data)

        # HHI
        hhi = self._calc_hhi(industry_data)

        # 行业增长率
        growth_rate = self._calc_industry_growth(industry_data)

        # 行业平均 ROE（简化：用营收/市值代理，完整版需取 ROE）
        avg_roe = 12.0  # 默认值，实际可扩展批量获取 ROE

        # 生命周期
        lifecycle = self._determine_lifecycle(growth_rate, avg_roe)

        # 行业吸引力评分（五力反向加权 + 增长率 + 集中度合理）
        # 五力越低（对在位企业越有利）-> 分数越高
        avg_force = sum(forces.values()) / len(forces)
        force_score = (5 - avg_force) / 5 * 100
        # 增长率 >15% 满分；<0% 低分
        growth_score = max(0, min(100, 50 + growth_rate * 3))
        # HHI 1500-2500 为合理集中度（既不垄断也不过度竞争）
        if 1500 <= hhi <= 2500:
            hhi_score = 80
        elif hhi < 1500:
            hhi_score = 50  # 过度竞争
        else:
            hhi_score = 60  # 高度集中，但可能面临反垄断

        # 生命周期调整
        lifecycle_adj = {"新兴": 1.1, "成长": 1.05, "成熟": 1.0, "衰退": 0.85}.get(lifecycle, 1.0)

        score = (force_score * 0.4 + growth_score * 0.4 + hhi_score * 0.2) * lifecycle_adj
        score = max(0, min(100, score))

        # 关键驱动因素与风险
        key_drivers: List[str] = []
        risks: List[str] = []
        if growth_rate > 10:
            key_drivers.append(f"行业营收增长 {growth_rate:.1f}%（高于 GDP 增速）")
        elif growth_rate < 0:
            risks.append(f"行业营收负增长 {growth_rate:.1f}%（行业收缩）")
        if hhi > 2500:
            key_drivers.append(f"行业集中度高（HHI={hhi:.0f}），龙头议价能力强")
        elif hhi < 1000:
            risks.append(f"行业过度分散（HHI={hhi:.0f}），竞争激烈")
        if forces["new_entrant_threat"] < 2.5:
            key_drivers.append("行业进入门槛高，新进入者威胁低")
        elif forces["new_entrant_threat"] > 3.5:
            risks.append("行业进入门槛低，新进入者威胁高")
        if lifecycle == "衰退":
            risks.append("行业处于衰退期")
        elif lifecycle == "新兴":
            key_drivers.append("行业处于新兴期，增长潜力大")

        return IndustryResult(
            code=code,
            industry=industry,
            attractiveness_score=round(score, 1),
            lifecycle_stage=lifecycle,
            porter_5_forces={k: round(v, 2) for k, v in forces.items()},
            hhi=round(hhi, 1),
            industry_growth_rate=round(growth_rate, 2),
            industry_avg_roe=round(avg_roe, 2),
            key_drivers=key_drivers,
            risks=risks,
            insufficient_data=False,
        )

    @staticmethod
    def format_report(result: IndustryResult) -> str:
        if result.insufficient_data:
            return f"【{result.code}】行业分析（{result.industry}）：数据不足，跳过"
        labels = {
            "supplier_power": "供应商议价权",
            "buyer_power": "客户议价权",
            "new_entrant_threat": "新进入者威胁",
            "substitute_threat": "替代品威胁",
            "competitive_intensity": "竞争强度",
        }
        hhi_label = "高度集中" if result.hhi > 2500 else "适度集中" if result.hhi > 1500 else "分散"
        lines = [
            f"【{result.code}】行业分析 - {result.industry}",
            f"■ 行业吸引力: {result.attractiveness_score}/100",
            f"■ 生命周期: {result.lifecycle_stage}",
            f"■ 行业增长率: {result.industry_growth_rate}%",
            f"■ HHI 指数: {result.hhi}（{hhi_label}）",
            "",
            "■ Porter 五力（分数越低越有利于在位企业）:",
        ]
        for k, v in result.porter_5_forces.items():
            lines.append(f"  • {labels.get(k, k)}: {v}/5")
        if result.key_drivers:
            lines.append("")
            lines.append("■ 关键驱动因素:")
            for d in result.key_drivers:
                lines.append(f"  • {d}")
        if result.risks:
            lines.append("")
            lines.append("■ 风险:")
            for r in result.risks:
                lines.append(f"  • {r}")
        return "\n".join(lines)
