# -*- coding: utf-8 -*-
"""
量化因子库 - 多因子模型基础组件

因子分类：
1. 价值因子：PE、PB、PS、PCF、EV/EBITDA
2. 成长因子：营收增长率、净利润增长率、ROE变化
3. 质量因子：ROE、ROA、毛利率、资产负债率
4. 动量因子：过去N日收益率、相对强弱
5. 波动因子：历史波动率、Beta、特异性波动率
6. 流动性因子：换手率、Amihud非流动性
7. 情绪因子：分析师一致预期变化、资金流向

使用示例：
```python
from quantitative.factors import FactorLibrary

library = FactorLibrary()

# 计算单个因子
pe_score = library.calc_value_factor(pe=15, pb=1.8, ps=3.2)

# 计算多因子综合评分
result = library.calc_composite_score({
    'pe': 15, 'pb': 1.8, 'roe': 0.18,
    'revenue_growth': 0.25, 'volatility': 0.35
})
```
"""

import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FactorResult:
    """因子计算结果"""
    name: str
    value: float
    z_score: float = 0.0       # 标准化分数
    percentile: float = 0.0    # 百分位排名
    weight: float = 1.0        # 权重
    category: str = ""         # 因子类别
    description: str = ""      # 描述


@dataclass
class CompositeScore:
    """多因子综合评分"""
    total_score: float         # 综合得分（0-100）
    factors: Dict[str, FactorResult]  # 各因子结果
    recommendation: str        # 投资建议
    confidence: float          # 置信度
    details: Dict = field(default_factory=dict)


class FactorLibrary:
    """
    量化因子库

    提供常用量化因子的计算方法和多因子综合评分
    """

    # 因子默认权重
    DEFAULT_WEIGHTS = {
        # 价值因子（30%）
        'value': 0.30,
        # 成长因子（25%）
        'growth': 0.25,
        # 质量因子（20%）
        'quality': 0.20,
        # 动量因子（15%）
        'momentum': 0.15,
        # 波动因子（10%）
        'volatility': 0.10,
    }

    # 行业中位数参考（用于标准化）
    INDUSTRY_MEDIAN = {
        'pe': 20.0,
        'pb': 2.5,
        'ps': 3.0,
        'roe': 0.12,
        'roa': 0.06,
        'gross_margin': 0.30,
        'debt_ratio': 0.50,
        'revenue_growth': 0.15,
        'earnings_growth': 0.15,
        'volatility': 0.30,
        'turnover': 0.03,
    }

    def __init__(self, weights: Dict[str, float] = None):
        """
        初始化因子库

        Args:
            weights: 自定义因子权重，None使用默认权重
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        # 归一化权重
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

    # ============================================================
    # 价值因子
    # ============================================================

    def calc_value_factor(
        self,
        pe: float = None,
        pb: float = None,
        ps: float = None,
        pcf: float = None,
        ev_ebitda: float = None
    ) -> FactorResult:
        """
        计算价值因子

        低估值股票得分高：
        - PE < 行业中位数 → 得分高
        - PB < 行业中位数 → 得分高

        Args:
            pe: 市盈率
            pb: 市净率
            ps: 市销率
            pcf: 市现率
            ev_ebitda: EV/EBITDA

        Returns:
            FactorResult: 价值因子结果
        """
        scores = []
        details = {}

        # PE得分（越低越好，负PE给低分）
        if pe is not None and pe > 0:
            pe_median = self.INDUSTRY_MEDIAN['pe']
            pe_score = max(0, min(100, 50 * (pe_median / pe)))
            scores.append(pe_score)
            details['pe'] = {'value': pe, 'score': pe_score}

        # PB得分（越低越好）
        if pb is not None and pb > 0:
            pb_median = self.INDUSTRY_MEDIAN['pb']
            pb_score = max(0, min(100, 50 * (pb_median / pb)))
            scores.append(pb_score)
            details['pb'] = {'value': pb, 'score': pb_score}

        # PS得分（越低越好）
        if ps is not None and ps > 0:
            ps_median = self.INDUSTRY_MEDIAN['ps']
            ps_score = max(0, min(100, 50 * (ps_median / ps)))
            scores.append(ps_score)
            details['ps'] = {'value': ps, 'score': ps_score}

        # 综合得分
        avg_score = sum(scores) / len(scores) if scores else 50

        return FactorResult(
            name="value",
            value=avg_score,
            z_score=(avg_score - 50) / 20,  # 简化Z-score
            category="价值因子",
            description=f"价值得分: {avg_score:.1f}",
        )

    # ============================================================
    # 成长因子
    # ============================================================

    def calc_growth_factor(
        self,
        revenue_growth: float = None,
        earnings_growth: float = None,
        roe_change: float = None,
        roa_change: float = None
    ) -> FactorResult:
        """
        计算成长因子

        高成长股票得分高

        Args:
            revenue_growth: 营收增长率（如0.25表示25%）
            earnings_growth: 净利润增长率
            roe_change: ROE变化（本期-上期）
            roa_change: ROA变化

        Returns:
            FactorResult: 成长因子结果
        """
        scores = []
        details = {}

        # 营收增长得分
        if revenue_growth is not None:
            # 20%增长得75分，30%得90分
            rev_score = min(100, 50 + revenue_growth * 150)
            scores.append(rev_score)
            details['revenue_growth'] = {'value': revenue_growth, 'score': rev_score}

        # 净利润增长得分
        if earnings_growth is not None:
            earn_score = min(100, 50 + earnings_growth * 150)
            scores.append(earn_score)
            details['earnings_growth'] = {'value': earnings_growth, 'score': earn_score}

        # ROE变化得分
        if roe_change is not None:
            roe_score = min(100, 50 + roe_change * 500)  # 10%变化得100分
            scores.append(roe_score)
            details['roe_change'] = {'value': roe_change, 'score': roe_score}

        avg_score = sum(scores) / len(scores) if scores else 50

        return FactorResult(
            name="growth",
            value=avg_score,
            z_score=(avg_score - 50) / 20,
            category="成长因子",
            description=f"成长得分: {avg_score:.1f}",
        )

    # ============================================================
    # 质量因子
    # ============================================================

    def calc_quality_factor(
        self,
        roe: float = None,
        roa: float = None,
        gross_margin: float = None,
        net_margin: float = None,
        debt_ratio: float = None,
        current_ratio: float = None
    ) -> FactorResult:
        """
        计算质量因子

        高质量公司得分高：高ROE、高毛利、低负债

        Args:
            roe: 净资产收益率
            roa: 总资产收益率
            gross_margin: 毛利率
            net_margin: 净利率
            debt_ratio: 资产负债率
            current_ratio: 流动比率

        Returns:
            FactorResult: 质量因子结果
        """
        scores = []
        details = {}

        # ROE得分（越高越好，15%得75分）
        if roe is not None:
            roe_score = min(100, roe * 500)
            scores.append(roe_score)
            details['roe'] = {'value': roe, 'score': roe_score}

        # ROA得分
        if roa is not None:
            roa_score = min(100, roa * 800)
            scores.append(roa_score)
            details['roa'] = {'value': roa, 'score': roa_score}

        # 毛利率得分
        if gross_margin is not None:
            gm_score = min(100, gross_margin * 200)
            scores.append(gm_score)
            details['gross_margin'] = {'value': gross_margin, 'score': gm_score}

        # 负债率得分（越低越好）
        if debt_ratio is not None:
            debt_score = max(0, 100 - debt_ratio * 150)
            scores.append(debt_score)
            details['debt_ratio'] = {'value': debt_ratio, 'score': debt_score}

        avg_score = sum(scores) / len(scores) if scores else 50

        return FactorResult(
            name="quality",
            value=avg_score,
            z_score=(avg_score - 50) / 20,
            category="质量因子",
            description=f"质量得分: {avg_score:.1f}",
        )

    # ============================================================
    # 动量因子
    # ============================================================

    def calc_momentum_factor(
        self,
        returns_5d: float = None,
        returns_20d: float = None,
        returns_60d: float = None,
        relative_strength: float = None
    ) -> FactorResult:
        """
        计算动量因子

        近期表现好的股票得分高（趋势延续）

        Args:
            returns_5d: 过去5日收益率
            returns_20d: 过去20日收益率
            returns_60d: 过去60日收益率
            relative_strength: 相对强弱（vs 指数）

        Returns:
            FactorResult: 动量因子结果
        """
        scores = []
        details = {}

        # 短期动量（5日）
        if returns_5d is not None:
            # 3%得75分，-3%得25分
            short_score = min(100, max(0, 50 + returns_5d * 800))
            scores.append(short_score)
            details['returns_5d'] = {'value': returns_5d, 'score': short_score}

        # 中期动量（20日）
        if returns_20d is not None:
            mid_score = min(100, max(0, 50 + returns_20d * 200))
            scores.append(mid_score)
            details['returns_20d'] = {'value': returns_20d, 'score': mid_score}

        # 长期动量（60日）
        if returns_60d is not None:
            long_score = min(100, max(0, 50 + returns_60d * 100))
            scores.append(long_score)
            details['returns_60d'] = {'value': returns_60d, 'score': long_score}

        # 相对强弱
        if relative_strength is not None:
            rs_score = min(100, max(0, 50 + relative_strength * 100))
            scores.append(rs_score)
            details['relative_strength'] = {'value': relative_strength, 'score': rs_score}

        avg_score = sum(scores) / len(scores) if scores else 50

        return FactorResult(
            name="momentum",
            value=avg_score,
            z_score=(avg_score - 50) / 20,
            category="动量因子",
            description=f"动量得分: {avg_score:.1f}",
        )

    # ============================================================
    # 波动因子
    # ============================================================

    def calc_volatility_factor(
        self,
        volatility_20d: float = None,
        beta: float = None,
        idiosyncratic_vol: float = None,
        max_drawdown: float = None
    ) -> FactorResult:
        """
        计算波动因子

        低波动股票得分高（风险调整后收益更好）

        Args:
            volatility_20d: 20日波动率
            beta: 市场Beta
            idiosyncratic_vol: 特异性波动率
            max_drawdown: 最大回撤

        Returns:
            FactorResult: 波动因子结果
        """
        scores = []
        details = {}

        # 波动率得分（越低越好）
        if volatility_20d is not None:
            vol_score = max(0, 100 - volatility_20d * 200)
            scores.append(vol_score)
            details['volatility_20d'] = {'value': volatility_20d, 'score': vol_score}

        # Beta得分（接近1得高分，过高或过低扣分）
        if beta is not None:
            beta_score = max(0, 100 - abs(beta - 1) * 50)
            scores.append(beta_score)
            details['beta'] = {'value': beta, 'score': beta_score}

        # 最大回撤得分（越小越好）
        if max_drawdown is not None:
            dd_score = max(0, 100 - abs(max_drawdown) * 200)
            scores.append(dd_score)
            details['max_drawdown'] = {'value': max_drawdown, 'score': dd_score}

        avg_score = sum(scores) / len(scores) if scores else 50

        return FactorResult(
            name="volatility",
            value=avg_score,
            z_score=(avg_score - 50) / 20,
            category="波动因子",
            description=f"波动得分: {avg_score:.1f}",
        )

    # ============================================================
    # 综合评分
    # ============================================================

    def calc_composite_score(
        self,
        data: Dict[str, float],
        custom_weights: Dict[str, float] = None
    ) -> CompositeScore:
        """
        计算多因子综合评分

        Args:
            data: 股票数据字典，包含各因子所需的字段
            custom_weights: 自定义权重，None使用默认权重

        Returns:
            CompositeScore: 综合评分结果
        """
        weights = custom_weights or self.weights
        factors = {}

        # 计算各因子
        if any(k in data for k in ['pe', 'pb', 'ps', 'pcf', 'ev_ebitda']):
            factors['value'] = self.calc_value_factor(
                pe=data.get('pe'),
                pb=data.get('pb'),
                ps=data.get('ps'),
                pcf=data.get('pcf'),
                ev_ebitda=data.get('ev_ebitda')
            )

        if any(k in data for k in ['revenue_growth', 'earnings_growth', 'roe_change']):
            factors['growth'] = self.calc_growth_factor(
                revenue_growth=data.get('revenue_growth'),
                earnings_growth=data.get('earnings_growth'),
                roe_change=data.get('roe_change'),
                roa_change=data.get('roa_change')
            )

        if any(k in data for k in ['roe', 'roa', 'gross_margin', 'debt_ratio']):
            factors['quality'] = self.calc_quality_factor(
                roe=data.get('roe'),
                roa=data.get('roa'),
                gross_margin=data.get('gross_margin'),
                net_margin=data.get('net_margin'),
                debt_ratio=data.get('debt_ratio'),
                current_ratio=data.get('current_ratio')
            )

        if any(k in data for k in ['returns_5d', 'returns_20d', 'returns_60d']):
            factors['momentum'] = self.calc_momentum_factor(
                returns_5d=data.get('returns_5d'),
                returns_20d=data.get('returns_20d'),
                returns_60d=data.get('returns_60d'),
                relative_strength=data.get('relative_strength')
            )

        if any(k in data for k in ['volatility_20d', 'beta', 'max_drawdown']):
            factors['volatility'] = self.calc_volatility_factor(
                volatility_20d=data.get('volatility_20d'),
                beta=data.get('beta'),
                idiosyncratic_vol=data.get('idiosyncratic_vol'),
                max_drawdown=data.get('max_drawdown')
            )

        # 计算加权综合得分
        total_score = 0
        total_weight = 0
        for name, factor in factors.items():
            weight = weights.get(name, 0)
            total_score += factor.value * weight
            total_weight += weight

        if total_weight > 0:
            composite = total_score / total_weight
        else:
            composite = 50

        # 生成投资建议
        if composite >= 75:
            recommendation = "强烈买入"
            confidence = 0.8
        elif composite >= 60:
            recommendation = "买入"
            confidence = 0.6
        elif composite >= 45:
            recommendation = "持有"
            confidence = 0.5
        elif composite >= 30:
            recommendation = "减仓"
            confidence = 0.6
        else:
            recommendation = "卖出"
            confidence = 0.8

        return CompositeScore(
            total_score=round(composite, 1),
            factors=factors,
            recommendation=recommendation,
            confidence=confidence,
            details={
                'weights_used': weights,
                'factors_count': len(factors),
            }
        )


# ============================================================
# 便捷函数
# ============================================================

def quick_score(pe: float, pb: float, roe: float, growth: float) -> Dict:
    """
    快速多因子评分（简化版）

    Args:
        pe: 市盈率
        pb: 市净率
        roe: 净资产收益率
        growth: 增长率

    Returns:
        Dict: 评分结果
    """
    library = FactorLibrary()
    result = library.calc_composite_score({
        'pe': pe,
        'pb': pb,
        'roe': roe,
        'revenue_growth': growth,
    })
    return {
        'score': result.total_score,
        'recommendation': result.recommendation,
        'confidence': result.confidence,
    }
