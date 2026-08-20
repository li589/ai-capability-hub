#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产业链上下游格局分析引擎
Industry Chain Analysis Engine

支持两种模式：
1. 通用产业链分析（6层递进框架）
2. A股专版产业链分析（含国产替代、A股标的推荐）
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


# ==================== 数据结构 ====================

@dataclass
class ChainNode:
    """产业链节点"""
    name: str  # 节点名称
    level: str  # upstream / midstream / downstream
    function: str = ""  # 核心功能
    product_form: str = ""  # 主要产品形态
    global_players: List[str] = field(default_factory=list)  # 全球Top3
    cn_players: List[str] = field(default_factory=list)  # 中国Top3
    ashare_players: List[Dict] = field(default_factory=list)  # A股公司 [{code, name, market_share}]
    ashare_participation: str = "🟡"  # 🟢有竞争力 / 🟡有布局 / 🔴基本空白
    gross_margin_range: str = ""  # 毛利率区间
    ashare_gross_margin: float = 0  # A股企业实际毛利率
    pricing_power_source: str = ""  # 议价能力来源
    cr3: float = 0  # 国内CR3集中度


@dataclass
class CompetitorProfile:
    """竞争者画像"""
    name: str
    code: str = ""  # 股票代码（A股才有）
    tech_score: int = 0  # 技术 ★(1-3)
    cost_score: int = 0  # 成本
    scale_score: int = 0  # 规模
    customer_score: int = 0  # 客户资源
    fund_score: int = 0  # 资金/政策支持
    substitution_progress: str = ""  # 国产替代进度
    overall_rating: str = ""  # 总评：强/中/弱
    moat_type: str = ""  # 护城河类型


@dataclass
class SubstitutionProgress:
    """国产替代进度"""
    node_name: str
    current_rate: float = 0  # 当前国产化率 %
    target_rate: float = 0  # 目标国产化率 %
    market_size_billion: float = 0  # 总市场规模（亿元）
    replaceable_size: float = 0  # 可替代规模（亿元）
    stage: str = ""  # 🚀突破期 / 📈加速期 / ✅成熟期 / ⏳攻坚期
    barriers: List[str] = field(default_factory=list)  # 替代障碍


@dataclass
class StockRecommendation:
    """股票推荐"""
    name: str
    code: str
    chain_position: str  # 产业链定位
    core_logic: str  # 核心投资逻辑
    revenue_growth: str = ""  # 营收增速
    net_profit_growth: str = ""  # 净利润增速
    gross_margin: str = ""  # 毛利率
    order_validation: str = ""  # 订单/产能验证
    valuation: str = ""  # 估值参考
    main_risk: str = ""  # 主要风险
    stage: str = ""  # 📌早期布局 / 🚀成长加速 / 💰成熟收割
    is_caution: bool = False  # 是否为警惕标的


@dataclass
class ASignals:
    """A股特有信号"""
    # 积极信号
    big_fund_increase: bool = False  # 国家大基金增持
    institution调研_increase: bool = False  # 机构调研密度上升
    major_customer_entry: bool = False  # 大客户进入/扩大采购
    capacity_utilization_high: bool = False  # 产能利用率>90%
    rd_expense_rising: bool = False  # 研发费用率提升

    # 风险信号
    major_shareholder减持: bool = False  # 大股东减持
    customer_concentration_high: bool = False  # 前五大客户集中度>70%
    dense_ipo_or_fundraising: bool = False  # 同行密集上市/定增
    gross_margin_declining: bool = False  # 毛利率连续下滑
    ar_growth_faster: bool = False  # 应收账款增速>营收增速


@dataclass
class DynamicAnalysis:
    """动态演化分析"""
    demand_catalysts: List[str] = field(default_factory=list)  # 需求侧催化
    supply_changes: List[str] = field(default_factory=list)  # 供给侧变化
    policy_factors: List[str] = field(default_factory=list)  # 政策与监管
    competition_evolution: List[str] = field(default_factory=list)  # 竞争格局演变
    # 通用模式额外
    tech_disruption: List[str] = field(default_factory=list)  # 技术替代
    vertical_integration: List[str] = field(default_factory=list)  # 纵向整合
    geopolitical: List[str] = field(default_factory=list)  # 地缘与政策
    cost_curve: List[str] = field(default_factory=list)  # 成本曲线演变


@dataclass
class StrategicControlPoint:
    """战略控制点"""
    name: str
    controller: str  # 谁控制
    reason: str  # 为什么能控制
    breakthrough_path: str = ""  # 可能被突破的路径
    criteria: List[str] = field(default_factory=list)  # 满足的判断标准


@dataclass
class ChainAnalysisResult:
    """产业链分析完整结果"""
    industry: str  # 产业链名称
    analysis_mode: str  # "general" / "ashare"
    timestamp: str = ""

    # 第一层：产业链地图
    nodes: List[ChainNode] = field(default_factory=list)

    # 第二层：价值分布
    value_distribution: Dict = field(default_factory=dict)
    smile_curve_analysis: str = ""

    # 第三层：竞争格局
    competition_matrix: Dict = field(default_factory=dict)  # {node_name: [CompetitorProfile]}
    moat_analysis: Dict = field(default_factory=dict)

    # 第四层：战略控制点 / 国产替代
    control_points: List[StrategicControlPoint] = field(default_factory=list)
    substitution_progress: List[SubstitutionProgress] = field(default_factory=list)

    # 第五层：动态演化
    dynamics: Optional[DynamicAnalysis] = None

    # 第六层：投资判断
    recommendations: List[StockRecommendation] = field(default_factory=list)
    best_node: str = ""  # 最值得关注的节点
    caution_node: str = ""  # 需要警惕的节点
    biggest_risk: str = ""  # 最大风险
    structural_opportunity: str = ""  # 中长期结构性机会

    # A股特有
    a_signals: Optional[ASignals] = None
    best_layout_node: str = ""  # 当前A股布局最佳节点
    short_vs_medium_logic: str = ""  # 短期vs中期逻辑差异


# ==================== 通用产业链分析引擎 ====================

class IndustryChainAnalyzer:
    """
    通用产业链分析引擎

    实现六层递进分析框架：
    1. 产业链地图绘制
    2. 价值分布分析
    3. 竞争格局分析
    4. 战略控制点识别
    5. 动态演化分析
    6. 投资/战略价值判断
    """

    def __init__(self):
        pass

    def analyze(self, industry: str, nodes: List[Dict] = None,
                depth: str = "full") -> ChainAnalysisResult:
        """
        执行产业链分析

        Args:
            industry: 产业链名称
            nodes: 预置节点数据（可选，如不提供则需要外部搜索补充）
            depth: 分析深度 "brief" / "full"

        Returns:
            ChainAnalysisResult
        """
        result = ChainAnalysisResult(
            industry=industry,
            analysis_mode="general",
            timestamp=time.strftime("%Y-%m-%d %H:%M")
        )

        if nodes:
            result.nodes = [ChainNode(**n) if isinstance(n, dict) else n for n in nodes]

        return result

    def build_chain_map(self, industry: str, upstream: List[str],
                        midstream: List[str], downstream: List[str]) -> List[ChainNode]:
        """
        构建产业链地图骨架

        Args:
            industry: 产业名称
            upstream: 上游节点名称列表
            midstream: 中游节点名称列表
            downstream: 下游节点名称列表

        Returns:
            List[ChainNode]
        """
        nodes = []
        for name in upstream:
            nodes.append(ChainNode(name=name, level="upstream"))
        for name in midstream:
            nodes.append(ChainNode(name=name, level="midstream"))
        for name in downstream:
            nodes.append(ChainNode(name=name, level="downstream"))
        return nodes

    def evaluate_concentration(self, cr3: float) -> str:
        """根据CR3判断集中度类型"""
        if cr3 > 70:
            return "寡头垄断"
        elif cr3 >= 40:
            return "寡头竞争"
        else:
            return "分散竞争"

    def identify_control_points(self, nodes: List[ChainNode]) -> List[StrategicControlPoint]:
        """
        识别战略控制点

        判断标准（满足2条以上即为控制点）：
        - 替代品极少或不存在
        - 切换供应商成本极高
        - 掌握下游关键数据或标准制定权
        - 产能扩张周期远长于下游需求周期
        - 少数玩家垄断且有意维持稀缺
        """
        control_points = []
        for node in nodes:
            # 自动判断：CR3高 + 毛利率高的节点更可能是控制点
            if node.cr3 > 60 and "高" in node.gross_margin_range:
                cp = StrategicControlPoint(
                    name=node.name,
                    controller=", ".join(node.global_players[:2]) if node.global_players else "待分析",
                    reason=f"CR3={node.cr3}%，高集中度+高利润",
                    criteria=["少数玩家垄断", "高利润维持"]
                )
                control_points.append(cp)
        return control_points

    def analyze_smile_curve(self, nodes: List[ChainNode]) -> str:
        """分析微笑曲线"""
        if not nodes:
            return "节点数据不足，无法分析微笑曲线"

        upstream_margin = 0
        midstream_margin = 0
        downstream_margin = 0
        u_count, m_count, d_count = 0, 0, 0

        for node in nodes:
            if node.level == "upstream":
                upstream_margin += node.ashare_gross_margin
                u_count += 1
            elif node.level == "midstream":
                midstream_margin += node.ashare_gross_margin
                m_count += 1
            else:
                downstream_margin += node.ashare_gross_margin
                d_count += 1

        u_avg = upstream_margin / u_count if u_count else 0
        m_avg = midstream_margin / m_count if m_count else 0
        d_avg = downstream_margin / d_count if d_count else 0

        if u_avg > m_avg and d_avg > m_avg:
            return f"符合微笑曲线 — 上游({u_avg:.1f}%) > 中游({m_avg:.1f}%) < 下游({d_avg:.1f}%)"
        elif m_avg > u_avg and m_avg > d_avg:
            return f"倒微笑曲线 — 中游({m_avg:.1f}%)利润最高，上游({u_avg:.1f}%)和下游({d_avg:.1f}%)较低"
        else:
            return f"非典型曲线 — 上游({u_avg:.1f}%) 中游({m_avg:.1f}%) 下游({d_avg:.1f}%)"

    def format_report(self, result: ChainAnalysisResult) -> str:
        """格式化分析报告为文本"""
        lines = []

        lines.append(f"{'='*60}")
        lines.append(f"  {result.industry} — 产业链分析报告")
        lines.append(f"  {result.timestamp}")
        lines.append(f"{'='*60}")

        # 第一层：地图
        lines.append(f"\n▸ 第一层：产业链地图")
        for node in result.nodes:
            level_label = {"upstream": "上游", "midstream": "中游", "downstream": "下游"}
            lines.append(f"  [{level_label.get(node.level, node.level)}] {node.name} (参与度:{node.ashare_participation})")
            if node.global_players:
                lines.append(f"    全球龙头: {', '.join(node.global_players[:3])}")
            if node.ashare_players:
                for p in node.ashare_players[:3]:
                    code = p.get('code', '')
                    name = p.get('name', '')
                    share = p.get('market_share', '')
                    lines.append(f"    A股: {name}({code}) — {share}")

        # 第二层：价值分布
        lines.append(f"\n▸ 第二层：价值分布")
        if result.smile_curve_analysis:
            lines.append(f"  {result.smile_curve_analysis}")
        for node in result.nodes:
            if node.gross_margin_range:
                lines.append(f"  {node.name}: 毛利率{node.gross_margin_range} | 议价来源:{node.pricing_power_source}")

        # 第三层：竞争格局
        if result.competition_matrix:
            lines.append(f"\n▸ 第三层：竞争格局")
            for node_name, competitors in result.competition_matrix.items():
                lines.append(f"  【{node_name}】集中度:{self.evaluate_concentration(next((n.cr3 for n in result.nodes if n.name == node_name), 0))}")
                for c in competitors:
                    stars = lambda s: "★" * s + "☆" * (3 - s)
                    code_str = f"({c.code})" if c.code else ""
                    lines.append(f"    {c.name}{code_str} 技术{stars(c.tech_score)} 成本{stars(c.cost_score)} "
                                 f"规模{stars(c.scale_score)} 总评:{c.overall_rating}")

        # 第四层：战略控制点
        if result.control_points:
            lines.append(f"\n▸ 第四层：战略控制点")
            for cp in result.control_points:
                lines.append(f"  ● {cp.name} — 控制者:{cp.controller}")
                lines.append(f"    原因: {cp.reason}")
                if cp.breakthrough_path:
                    lines.append(f"    突破路径: {cp.breakthrough_path}")

        # 第五层：动态演化
        if result.dynamics:
            lines.append(f"\n▸ 第五层：动态演化")
            d = result.dynamics
            if d.demand_catalysts:
                lines.append(f"  需求催化: {'; '.join(d.demand_catalysts)}")
            if d.supply_changes:
                lines.append(f"  供给变化: {'; '.join(d.supply_changes)}")
            if d.policy_factors:
                lines.append(f"  政策因素: {'; '.join(d.policy_factors)}")
            if d.tech_disruption:
                lines.append(f"  技术替代: {'; '.join(d.tech_disruption)}")
            if d.vertical_integration:
                lines.append(f"  纵向整合: {'; '.join(d.vertical_integration)}")

        # 第六层：判断
        lines.append(f"\n▸ 第六层：投资/战略判断")
        if result.best_node:
            lines.append(f"  最值得关注: {result.best_node}")
        if result.caution_node:
            lines.append(f"  需要警惕: {result.caution_node}")
        if result.biggest_risk:
            lines.append(f"  最大风险: {result.biggest_risk}")
        if result.structural_opportunity:
            lines.append(f"  中长期机会: {result.structural_opportunity}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


# ==================== A股专版产业链分析引擎 ====================

class AShareChainAnalyzer:
    """
    A股专版产业链分析引擎

    六层递进框架（A股视角）：
    1. 产业链地图（A股参与度🟢🟡🔴）
    2. 价值分布（A股能拿到多少）
    3. A股竞争格局（谁在赢，能赢多久）
    4. 国产替代进度评估
    5. 动态演化（A股节奏判断）
    6. A股投资判断（明确标的）
    """

    def __init__(self):
        pass

    def analyze(self, industry: str, nodes: List[Dict] = None) -> ChainAnalysisResult:
        """
        执行A股产业链分析

        Args:
            industry: 产业链名称
            nodes: 预置节点数据

        Returns:
            ChainAnalysisResult
        """
        result = ChainAnalysisResult(
            industry=industry,
            analysis_mode="ashare",
            timestamp=time.strftime("%Y-%m-%d %H:%M")
        )

        if nodes:
            result.nodes = [ChainNode(**n) if isinstance(n, dict) else n for n in nodes]

        return result

    def build_chain_map(self, industry: str, upstream: List[Dict],
                        midstream: List[Dict], downstream: List[Dict]) -> List[ChainNode]:
        """
        构建A股产业链地图

        Args:
            upstream/midstream/downstream: 列表元素为 dict，格式：
                {"name": "节点名", "participation": "🟢", "ashare_players": [...]}
        """
        nodes = []
        for item in upstream:
            node = ChainNode(
                name=item.get("name", ""),
                level="upstream",
                ashare_participation=item.get("participation", "🟡"),
                ashare_players=item.get("ashare_players", []),
                global_players=item.get("global_players", [])
            )
            nodes.append(node)

        for item in midstream:
            node = ChainNode(
                name=item.get("name", ""),
                level="midstream",
                ashare_participation=item.get("participation", "🟡"),
                ashare_players=item.get("ashare_players", []),
                global_players=item.get("global_players", [])
            )
            nodes.append(node)

        for item in downstream:
            node = ChainNode(
                name=item.get("name", ""),
                level="downstream",
                ashare_participation=item.get("participation", "🟡"),
                ashare_players=item.get("ashare_players", []),
                global_players=item.get("global_players", [])
            )
            nodes.append(node)

        return nodes

    def evaluate_concentration(self, cr3: float) -> str:
        """A股视角集中度判断"""
        if cr3 > 60:
            return "龙头稳固"
        elif cr3 >= 30:
            return "差异化竞争"
        else:
            return "整合逻辑"

    def assess_substitution(self, node: ChainNode,
                            current_rate: float, target_rate: float,
                            total_market_billion: float,
                            stage: str = "",
                            barriers: List[str] = None) -> SubstitutionProgress:
        """
        评估国产替代进度

        Args:
            node: 产业链节点
            current_rate: 当前国产化率 (%)
            target_rate: 目标国产化率 (%)
            total_market_billion: 总市场规模（亿元）
            stage: 替代阶段
            barriers: 替代障碍列表
        """
        replaceable = total_market_billion * (target_rate - current_rate) / 100

        if not stage:
            if current_rate >= 50:
                stage = "✅成熟期"
            elif current_rate >= 20:
                stage = "📈加速期"
            elif current_rate >= 5:
                stage = "🚀突破期"
            else:
                stage = "⏳攻坚期"

        return SubstitutionProgress(
            node_name=node.name,
            current_rate=current_rate,
            target_rate=target_rate,
            market_size_billion=total_market_billion,
            replaceable_size=round(replaceable, 1),
            stage=stage,
            barriers=barriers or []
        )

    def build_competition_matrix(self, node_name: str,
                                  competitors: List[Dict]) -> List[CompetitorProfile]:
        """
        构建A股竞争矩阵

        Args:
            node_name: 节点名称
            competitors: 竞争者数据列表，每项格式：
                {"name": "公司", "code": "000XXX", "tech": 3, "cost": 2, ...}
        """
        profiles = []
        for c in competitors:
            tech = c.get("tech", 2)
            cost = c.get("cost", 2)
            scale = c.get("scale", 2)
            customer = c.get("customer", 2)
            fund = c.get("fund", 2)

            total = tech + cost + scale + customer + fund
            if total >= 12:
                overall = "强"
            elif total >= 8:
                overall = "中"
            else:
                overall = "弱"

            profile = CompetitorProfile(
                name=c.get("name", ""),
                code=c.get("code", ""),
                tech_score=tech,
                cost_score=cost,
                scale_score=scale,
                customer_score=customer,
                fund_score=fund,
                substitution_progress=c.get("substitution_progress", ""),
                overall_rating=overall,
                moat_type=c.get("moat_type", "")
            )
            profiles.append(profile)

        return profiles

    def evaluate_a_signals(self, signals: Dict) -> ASignals:
        """评估A股特有信号"""
        return ASignals(
            big_fund_increase=signals.get("big_fund_increase", False),
            institution调研_increase=signals.get("institution_research_increase", False),
            major_customer_entry=signals.get("major_customer_entry", False),
            capacity_utilization_high=signals.get("capacity_utilization_high", False),
            rd_expense_rising=signals.get("rd_expense_rising", False),
            major_shareholder减持=signals.get("major_shareholder减持", False),
            customer_concentration_high=signals.get("customer_concentration_high", False),
            dense_ipo_or_fundraising=signals.get("dense_ipo_or_fundraising", False),
            gross_margin_declining=signals.get("gross_margin_declining", False),
            ar_growth_faster=signals.get("ar_growth_faster", False),
        )

    def get_positive_signal_count(self, signals: ASignals) -> int:
        """统计积极信号数量"""
        return sum([
            signals.big_fund_increase,
            signals.institution调研_increase,
            signals.major_customer_entry,
            signals.capacity_utilization_high,
            signals.rd_expense_rising,
        ])

    def get_risk_signal_count(self, signals: ASignals) -> int:
        """统计风险信号数量"""
        return sum([
            signals.major_shareholder减持,
            signals.customer_concentration_high,
            signals.dense_ipo_or_fundraising,
            signals.gross_margin_declining,
            signals.ar_growth_faster,
        ])

    def format_report(self, result: ChainAnalysisResult) -> str:
        """格式化A股分析报告"""
        lines = []

        lines.append(f"{'='*60}")
        lines.append(f"  {result.industry} — A股产业链分析报告")
        lines.append(f"  {result.timestamp}")
        lines.append(f"{'='*60}")

        # 第一层：A股参与度地图
        lines.append(f"\n▸ 第一层：产业链地图（A股参与度）")
        level_labels = {"upstream": "上游", "midstream": "中游", "downstream": "下游"}
        for node in result.nodes:
            lines.append(f"  [{level_labels.get(node.level, node.level)}] {node.name} (参与度:{node.ashare_participation})")
            if node.global_players:
                lines.append(f"    全球龙头: {', '.join(node.global_players[:3])}")
            if node.ashare_players:
                for p in node.ashare_players[:3]:
                    code = p.get('code', '')
                    name = p.get('name', '')
                    share = p.get('market_share', '')
                    lines.append(f"    A股: {name}({code}) — {share}")

        # 第二层：价值分布（A股视角）
        lines.append(f"\n▸ 第二层：价值分布（A股能拿到多少）")
        for node in result.nodes:
            if node.gross_margin_range or node.ashare_gross_margin:
                margin_str = f"{node.ashare_gross_margin}%" if node.ashare_gross_margin else node.gross_margin_range
                lines.append(f"  {node.name}: A股毛利率 {margin_str} | 议价来源:{node.pricing_power_source}")

        # 第三层：A股竞争矩阵
        if result.competition_matrix:
            lines.append(f"\n▸ 第三层：A股竞争格局")
            for node_name, competitors in result.competition_matrix.items():
                node_cr3 = next((n.cr3 for n in result.nodes if n.name == node_name), 0)
                lines.append(f"  【{node_name}】集中度:{self.evaluate_concentration(node_cr3)} (CR3={node_cr3}%)")
                lines.append(f"  {'公司':<16s} {'技术':<6s} {'成本':<6s} {'规模':<6s} {'客户':<6s} {'总评'}")
                lines.append(f"  {'-'*50}")
                for c in competitors:
                    stars = lambda s: "★" * s + "☆" * (3 - s)
                    code_str = f"({c.code})" if c.code else ""
                    name_str = f"{c.name}{code_str}"
                    lines.append(f"  {name_str:<16s} {stars(c.tech_score):<6s} {stars(c.cost_score):<6s} "
                                 f"{stars(c.scale_score):<6s} {stars(c.customer_score):<6s} {c.overall_rating}")

        # 第四层：国产替代进度
        if result.substitution_progress:
            lines.append(f"\n▸ 第四层：国产替代进度")
            for sp in result.substitution_progress:
                lines.append(f"  {sp.node_name}: {sp.stage}")
                lines.append(f"    国产化率: {sp.current_rate}% → 目标{sp.target_rate}%")
                lines.append(f"    可替代空间: {sp.replaceable_size}亿 (总市场{sp.market_size_billion}亿)")
                if sp.barriers:
                    lines.append(f"    替代障碍: {'; '.join(sp.barriers)}")

        # 第五层：动态演化
        if result.dynamics:
            lines.append(f"\n▸ 第五层：动态演化")
            d = result.dynamics
            if d.demand_catalysts:
                lines.append(f"  需求催化: {'; '.join(d.demand_catalysts)}")
            if d.supply_changes:
                lines.append(f"  供给变化: {'; '.join(d.supply_changes)}")
            if d.policy_factors:
                lines.append(f"  政策因素: {'; '.join(d.policy_factors)}")
            if d.competition_evolution:
                lines.append(f"  竞争演变: {'; '.join(d.competition_evolution)}")

        # 第六层：A股投资判断
        lines.append(f"\n▸ 第六层：A股投资判断")

        # 核心标的
        core_recs = [r for r in result.recommendations if not r.is_caution]
        caution_recs = [r for r in result.recommendations if r.is_caution]

        if core_recs:
            lines.append(f"\n  【核心标的推荐】")
            for r in core_recs:
                lines.append(f"  ● {r.name}({r.code}) {r.stage}")
                lines.append(f"    定位: {r.chain_position}")
                lines.append(f"    逻辑: {r.core_logic}")
                if r.revenue_growth:
                    lines.append(f"    营收增速: {r.revenue_growth} | 净利润增速: {r.net_profit_growth}")
                if r.valuation:
                    lines.append(f"    估值: {r.valuation}")
                if r.main_risk:
                    lines.append(f"    风险: {r.main_risk}")

        if caution_recs:
            lines.append(f"\n  【警惕标的】")
            for r in caution_recs:
                lines.append(f"  ⚠ {r.name}({r.code})")
                lines.append(f"    {r.core_logic}")
                if r.main_risk:
                    lines.append(f"    弱点: {r.main_risk}")

        # A股信号
        if result.a_signals:
            sig = result.a_signals
            lines.append(f"\n  【A股信号检查】")
            positives = []
            risks = []
            if sig.big_fund_increase: positives.append("国家大基金/社保/北向增持")
            if sig.institution调研_increase: positives.append("机构调研密度上升")
            if sig.major_customer_entry: positives.append("大客户进入/扩大采购")
            if sig.capacity_utilization_high: positives.append("产能利用率>90%")
            if sig.rd_expense_rising: positives.append("研发费用率提升")
            if sig.major_shareholder减持: risks.append("大股东减持")
            if sig.customer_concentration_high: risks.append("前五大客户集中度>70%")
            if sig.dense_ipo_or_fundraising: risks.append("同行密集上市/定增")
            if sig.gross_margin_declining: risks.append("毛利率连续下滑")
            if sig.ar_growth_faster: risks.append("应收账款增速>营收增速")

            for p in positives:
                lines.append(f"    ✅ {p}")
            for r in risks:
                lines.append(f"    ⚠ {r}")

        # 综合判断
        if result.best_layout_node:
            lines.append(f"\n  最佳布局节点: {result.best_layout_node}")
        if result.short_vs_medium_logic:
            lines.append(f"  短期vs中期: {result.short_vs_medium_logic}")
        if result.biggest_risk:
            lines.append(f"  最大风险: {result.biggest_risk}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


# ==================== 产业链知识库（常用产业预设） ====================

INDUSTRY_PRESETS = {
    "半导体": {
        "upstream": ["半导体设备", "EDA工具", "半导体材料", "IP核"],
        "midstream": ["芯片设计", "晶圆制造", "封装测试"],
        "downstream": ["消费电子", "汽车电子", "工业控制", "通信设备", "AI算力"]
    },
    "新能源汽车": {
        "upstream": ["锂矿/碳酸锂", "正极材料", "负极材料", "电解液", "隔膜"],
        "midstream": ["动力电池", "电机电控", "热管理系统", "汽车电子"],
        "downstream": ["整车制造", "充电桩", "储能", "电池回收"]
    },
    "光伏": {
        "upstream": ["多晶硅/硅料", "硅片", "银浆", "光伏玻璃"],
        "midstream": ["电池片", "光伏组件", "逆变器", "胶膜"],
        "downstream": ["光伏电站", "分布式光伏", "BIPV", "光伏储能"]
    },
    "AI芯片": {
        "upstream": ["GPU/AI芯片设计", "先进封装", "HBM存储", "光模块"],
        "midstream": ["服务器整机", "AI框架/软件", "云计算平台"],
        "downstream": ["大模型训练", "AI应用", "智能驾驶", "机器人"]
    },
    "医药": {
        "upstream": ["原料药/API", "CRO/CDMO", "药用辅料", "医药包装"],
        "midstream": ["创新药", "仿制药", "生物药", "医疗器械"],
        "downstream": ["医院/医疗机构", "零售药店", "医药电商", "医保支付"]
    },
    "消费电子": {
        "upstream": ["芯片/SoC", "显示面板", "摄像头模组", "被动元件"],
        "midstream": ["ODM/OEM组装", "结构件", "连接器", "声学器件"],
        "downstream": ["智能手机", "PC/平板", "可穿戴设备", "AR/VR"]
    },
    "军工": {
        "upstream": ["特种材料", "军用电子元器件", "军用芯片"],
        "midstream": ["航空发动机", "导弹/弹药", "军用飞机", "舰船制造", "雷达/电子战"],
        "downstream": ["军队采购", "军贸出口", "军民融合"]
    },
    "机器人": {
        "upstream": ["减速器", "伺服电机", "控制器", "传感器", "力矩传感器"],
        "midstream": ["工业机器人本体", "协作机器人", "人形机器人"],
        "downstream": ["汽车制造", "3C电子", "物流仓储", "医疗", "家庭服务"]
    }
}


def get_preset_chain(industry: str) -> Optional[Dict]:
    """获取预设产业链结构"""
    return INDUSTRY_PRESETS.get(industry)


def list_presets() -> List[str]:
    """列出所有预设产业链"""
    return list(INDUSTRY_PRESETS.keys())
