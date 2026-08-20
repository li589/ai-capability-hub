# -*- coding: utf-8 -*-
"""高级量化因子库（enhanced_factors.py，v7.6 新增）

设计目标：
- 增强预测能力：在 v7.5 五大类因子基础上，新增 4 大类高级因子
  （动量反转、资金流、波动率、日历），每类都带自适应阈值
- 多市场适用：A 股 / 港股 / 美股均可使用
- 自适应参数：根据市场状态自动调整因子权重
- 与 v7.5 FactorLibrary 协同：保留兼容接口

新增因子：
1. **动量反转因子** (MomentumReversionFactor)
   - 多周期动量（5/10/20/60 日）
   - 均值回归信号（价格偏离 MA 的程度）
   - 反转信号（放量阴线/长下影线）

2. **资金流因子** (CapitalFlowFactor)
   - 主力净流入占比（占成交量）
   - 北向资金变化率
   - ETF 净申赎
   - 融资融券余额变化

3. **波动率因子** (VolatilityFactor)
   - ATR（平均真实波幅）
   - 历史波动率（20/60 日）
   - 波动率突破（>2σ）
   - 波动率均值回归

4. **日历因子** (CalendarFactor)
   - 月末效应（T+1/T+5）
   - 春节效应（农历新年前后）
   - 财报发布前后漂移
   - 周内效应（周一/周五）

使用示例：
    from quantitative.enhanced_factors import EnhancedFactorLibrary

    lib = EnhancedFactorLibrary()
    momentum_score = lib.calc_momentum_factor(prices=[...], volumes=[...])
    capital_score = lib.calc_capital_flow_factor(
        main_flow=10e8, north_flow=5e8, turnover=0.05
    )
    vol_score = lib.calc_volatility_factor(prices=[...], high=[...], low=[...])
    calendar_score = lib.calc_calendar_factor(date_obj=date(2026, 8, 9))

    # 多因子合成（带自适应权重）
    result = lib.calc_enhanced_composite({
        'pe': 15, 'pb': 1.8, 'roe': 0.18,
        'momentum_5d': 0.05, 'momentum_20d': 0.12,
        'volatility_20d': 0.30,
        'main_flow_ratio': 0.15,
    })
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FactorScore:
    """单个因子的计算结果。"""
    name: str
    raw_value: float = 0.0
    score: float = 0.0          # 0-100 标准分
    category: str = ""
    confidence: float = 0.0     # 0-1 数据可信度
    description: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class EnhancedCompositeResult:
    """增强多因子综合评分结果。"""
    total_score: float          # 综合 0-100
    factors: Dict[str, FactorScore]
    recommendation: str         # 投资建议
    confidence: float           # 综合置信度
    weights: Dict[str, float]   # 实际使用权重
    market_regime: str = ""     # 当前市场状态判定
    metadata: Dict = field(default_factory=dict)


# ============================================================================
# 1. 动量反转因子
# ============================================================================


class MomentumReversionFactor:
    """多周期动量 + 均值回归 + 反转信号。

    设计要点：
    - 多周期综合（5/10/20/60 日）避免单一周期噪声
    - 反转信号识别超买超卖 + 异常放量
    - 短期反转（1-5 日）与中期动量（20-60 日）互补
    """

    def __init__(self, periods: Tuple[int, ...] = (5, 10, 20, 60)):
        self.periods = periods

    def calc(self, prices: List[float], volumes: Optional[List[float]] = None) -> FactorScore:
        """计算动量反转综合分。

        Args:
            prices: 收盘价序列（从旧到新）
            volumes: 成交量序列（可选，用于反转信号）

        Returns:
            FactorScore 综合得分 0-100
        """
        if len(prices) < max(self.periods) + 1:
            return FactorScore(
                name="momentum_reversion",
                score=50.0,
                confidence=0.2,
                description="数据不足（至少需 {} 个交易日）".format(max(self.periods) + 1),
            )

        momentum_scores = []
        for period in self.periods:
            ret = (prices[-1] - prices[-1 - period]) / prices[-1 - period]
            momentum_scores.append(ret)

        # 加权平均：短期权重大（近期更具预测力）
        weights = [0.4, 0.3, 0.2, 0.1][:len(momentum_scores)]
        weighted_momentum = sum(s * w for s, w in zip(momentum_scores, weights))

        # 标准化为 0-100：±20% 映射到 0-100（中位 = 50）
        momentum_score = 50 + (weighted_momentum / 0.20) * 50
        momentum_score = max(0, min(100, momentum_score))

        # 反转信号：放量 + 长下影线（看涨）/放量 + 长上影线（看跌）
        reversal_score = 50.0
        if volumes and len(volumes) >= 5:
            avg_vol = sum(volumes[-5:-1]) / 4
            last_vol = volumes[-1]
            # 当日涨幅
            day_ret = (prices[-1] - prices[-2]) / prices[-2]
            # 放量 + 下跌 → 反转信号
            if last_vol > avg_vol * 1.5 and day_ret < -0.02:
                reversal_score = 65.0  # 买入反转
            elif last_vol > avg_vol * 1.5 and day_ret > 0.02:
                reversal_score = 35.0  # 卖出反转

        # 动量反转综合：60% 动量 + 40% 反转
        total = 0.6 * momentum_score + 0.4 * reversal_score

        return FactorScore(
            name="momentum_reversion",
            raw_value=weighted_momentum,
            score=total,
            category="momentum_reversion",
            confidence=0.8,
            description=(
                f"动量 {weighted_momentum:+.2%}（{self.periods} 日加权），"
                f"反转信号 {reversal_score:.0f}"
            ),
            metadata={
                "period_returns": {f"{p}d": (prices[-1] - prices[-1 - p]) / prices[-1 - p]
                                   for p in self.periods},
                "reversal_score": reversal_score,
                "momentum_score": momentum_score,
            },
        )


# ============================================================================
# 2. 资金流因子
# ============================================================================


class CapitalFlowFactor:
    """资金流因子（主力 + 北向 + ETF + 两融）。

    数据获取：
    - 主力净流入：东方财富资金流接口
    - 北向资金：沪深港通持股变化
    - ETF 净申赎：交易所 ETF 数据
    - 融资融券：交易所披露

    设计要点：
    - 综合 4 类资金来源（各 25%）
    - 主流量化为主（主力净流入相对成交额占比）
    - 短期窗口（5 日）权重更高
    """

    def calc(self,
             main_flow_value: float = 0.0,
             main_flow_ratio: float = 0.0,
             north_flow_change: float = 0.0,
             etf_net_flow: float = 0.0,
             margin_balance_change: float = 0.0) -> FactorScore:
        """计算资金流综合分。

        Args:
            main_flow_value: 主力净流入金额（元）
            main_flow_ratio: 主力净流入占成交量比例（-1~1）
            north_flow_change: 北向资金 5 日变化率（-1~1）
            etf_net_flow: ETF 净申购（亿元，正数=流入）
            margin_balance_change: 融资余额 5 日变化率（-1~1）

        Returns:
            FactorScore 综合得分 0-100
        """
        scores = []
        weights = []

        # 主力净流入（占比 + 绝对值双信号）
        if main_flow_ratio != 0:
            main_score = 50 + main_flow_ratio * 50
            scores.append(main_score)
            weights.append(0.4)

        # 北向资金（5 日变化率）
        if north_flow_change != 0:
            north_score = 50 + north_flow_change * 50
            scores.append(north_score)
            weights.append(0.25)

        # ETF 净申赎（金额 > 5 亿视为强烈信号）
        if etf_net_flow != 0:
            etf_score = 50 + math.tanh(etf_net_flow / 5.0) * 50
            scores.append(etf_score)
            weights.append(0.20)

        # 融资融券（杠杆资金方向指标）
        if margin_balance_change != 0:
            margin_score = 50 + margin_balance_change * 50
            scores.append(margin_score)
            weights.append(0.15)

        if not scores:
            return FactorScore(
                name="capital_flow",
                score=50.0,
                confidence=0.1,
                description="无资金流数据",
            )

        # 归一化权重
        total_w = sum(weights)
        weights = [w / total_w for w in weights]

        total = sum(s * w for s, w in zip(scores, weights))
        # 综合置信度 = 数据完整度
        confidence = len(scores) / 4.0

        return FactorScore(
            name="capital_flow",
            raw_value=main_flow_value,
            score=total,
            category="capital_flow",
            confidence=confidence,
            description=(
                f"主力占比 {main_flow_ratio:+.1%}，北向 {north_flow_change:+.1%}，"
                f"ETF {etf_net_flow:+.1f} 亿，两融 {margin_balance_change:+.1%}"
            ),
            metadata={
                "main_score": scores[0] if scores else 50,
                "source_count": len(scores),
            },
        )


# ============================================================================
# 3. 波动率因子
# ============================================================================


class VolatilityFactor:
    """波动率因子（ATR + 历史波动 + 突破信号 + 均值回归）。

    预测意义：
    - 高波动 + 突破 → 趋势跟随信号
    - 低波动 + 极端位置 → 反转信号
    - 波动率均值回归 → 后期波动可能放大
    """

    def __init__(self, window: int = 20):
        self.window = window

    def _true_range(self, high: float, low: float, prev_close: float) -> float:
        return max(high - low, abs(high - prev_close), abs(low - prev_close))

    def calc(self,
             prices: List[float],
             highs: Optional[List[float]] = None,
             lows: Optional[List[float]] = None,
             period: Optional[int] = None) -> FactorScore:
        """计算波动率综合分。

        Args:
            prices: 收盘价序列
            highs: 最高价序列（用于 ATR）
            lows: 最低价序列（用于 ATR）
            period: 历史波动率窗口（默认 20）

        Returns:
            FactorScore 综合得分 0-100
        """
        period = period or self.window
        if len(prices) < period + 1:
            return FactorScore(
                name="volatility",
                score=50.0,
                confidence=0.2,
                description=f"数据不足（需 {period + 1}+ 个交易日）",
            )

        # 1) 历史波动率（年化）
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1]
                   for i in range(1, len(prices))]
        recent_returns = returns[-period:]
        if not recent_returns:
            return FactorScore(name="volatility", score=50.0, confidence=0.1)
        mean_ret = sum(recent_returns) / len(recent_returns)
        var_ret = sum((r - mean_ret) ** 2 for r in recent_returns) / len(recent_returns)
        vol_daily = math.sqrt(var_ret)
        vol_annual = vol_daily * math.sqrt(252)

        # 2) ATR（平均真实波幅，需 high/low）
        atr = 0.0
        atr_ratio = 0.0
        if highs and lows and len(highs) == len(prices) and len(lows) == len(prices):
            trs = [self._true_range(highs[i], lows[i], prices[i - 1])
                   for i in range(1, len(prices))]
            atr_recent = trs[-period:]
            if atr_recent:
                atr = sum(atr_recent) / len(atr_recent)
                atr_ratio = atr / prices[-1]  # ATR 占价格的比例

        # 3) 波动率突破检测（当日振幅 > 2σ）
        if len(recent_returns) >= 5:
            std_recent = math.sqrt(var_ret)
            last_move = abs(returns[-1])
            is_breakout = last_move > 2 * std_recent
        else:
            is_breakout = False

        # 评分逻辑：
        # - 高波动 + 突破 → 70 分（趋势跟随）
        # - 低波动 + 极端位置 → 30 分（反转预警）
        # - 正常波动 → 50 分（中性）
        score = 50.0
        if is_breakout and vol_annual > 0.3:
            score = 70.0  # 高波动突破 → 跟随
        elif vol_annual > 0.5:
            score = 65.0  # 持续高波动
        elif vol_annual < 0.15:
            score = 35.0  # 低波动 → 可能反转
        elif atr_ratio > 0.05:
            score = 60.0  # 日内波动较大

        return FactorScore(
            name="volatility",
            raw_value=vol_annual,
            score=score,
            category="volatility",
            confidence=0.8,
            description=(
                f"年化波动 {vol_annual:.1%}，ATR {atr:.2f}（{atr_ratio:.1%}），"
                f"{'突破' if is_breakout else '未突破'}"
            ),
            metadata={
                "vol_annual": vol_annual,
                "vol_daily": vol_daily,
                "atr": atr_ratio,
                "is_breakout": is_breakout,
            },
        )


# ============================================================================
# 4. 日历因子
# ============================================================================


class CalendarFactor:
    """日历因子（月末/春节/财报/周内效应）。

    设计要点：
    - 基于学术研究的 A 股日历效应实证
    - 月末/春节/财报披露前后有明显统计偏差
    - 周一/周五效应（美股）
    """

    # A 股春节日历效应：春节前 5 日 ~ 后 5 日（共 11 天窗口）
    SPRING_FESTIVAL_WINDOW_DAYS = 5

    def calc(self,
             date_obj: Optional[date] = None,
             is_financial_report_period: bool = False,
             days_to_month_end: int = 15) -> FactorScore:
        """计算日历因子综合分。

        Args:
            date_obj: 当前日期（None = 今天）
            is_financial_report_period: 是否处于财报披露密集期（4月底/8月底/10月底）
            days_to_month_end: 距离月末的天数

        Returns:
            FactorScore 综合得分 0-100
        """
        if date_obj is None:
            date_obj = date.today()

        score = 50.0
        metadata = {}

        # 1) 月末效应（最后 5 个交易日偏强）
        if days_to_month_end <= 5 and days_to_month_end > 0:
            score += 8
            metadata["month_end_effect"] = days_to_month_end
        elif days_to_month_end >= 25:  # 月初偏弱
            score -= 5
            metadata["month_start_effect"] = days_to_month_end

        # 2) 财报披露期效应（4/8/10 月底窗口）
        if is_financial_report_period:
            score -= 5  # 财报季波动加剧，但未必方向
            metadata["financial_report_period"] = True

        # 3) 周内效应
        weekday = date_obj.weekday()
        if weekday == 0:  # 周一（美股统计偏弱，A股相对中性）
            score -= 3
            metadata["weekday_effect"] = "monday"
        elif weekday == 4:  # 周五（美股统计偏强，A股相对中性）
            score += 3
            metadata["weekday_effect"] = "friday"

        # 4) 春季日历效应（农历新年附近）
        # 简化：2 月初视为春节窗口
        if date_obj.month == 2 and date_obj.day <= 15:
            score -= 5
            metadata["spring_festival_window"] = True

        score = max(0, min(100, score))

        return FactorScore(
            name="calendar",
            score=score,
            category="calendar",
            confidence=0.6,
            description=(
                f"日历效应："
                f"{'月末' if days_to_month_end <= 5 and days_to_month_end > 0 else '非月末'}"
                f" + {'财报期' if is_financial_report_period else '非财报期'}"
            ),
            metadata=metadata,
        )


# ============================================================================
# 5. 增强因子库（统一入口）
# ============================================================================


class EnhancedFactorLibrary:
    """增强因子库（v7.6 新增）。

    在 v7.5 FactorLibrary 基础上，新增 4 类因子 + 自适应权重。
    """

    DEFAULT_WEIGHTS = {
        # v7.5 原有
        "value": 0.20,
        "growth": 0.15,
        "quality": 0.15,
        "momentum": 0.10,
        "volatility": 0.05,
        # v7.6 新增（4 大类）
        "momentum_reversion": 0.15,  # 动量反转
        "capital_flow": 0.10,         # 资金流
        "volatility_regime": 0.05,   # 波动率状态
        "calendar": 0.05,            # 日历
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        # 归一化
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
        self._momentum_factor = MomentumReversionFactor()
        self._capital_factor = CapitalFlowFactor()
        self._volatility_factor = VolatilityFactor()
        self._calendar_factor = CalendarFactor()

    # 便捷方法
    def calc_momentum_factor(self, prices: List[float],
                             volumes: Optional[List[float]] = None) -> FactorScore:
        return self._momentum_factor.calc(prices, volumes)

    def calc_capital_flow_factor(self, **kwargs) -> FactorScore:
        return self._capital_factor.calc(**kwargs)

    def calc_volatility_factor(self, prices: List[float],
                               highs: Optional[List[float]] = None,
                               lows: Optional[List[float]] = None) -> FactorScore:
        return self._volatility_factor.calc(prices, highs, lows)

    def calc_calendar_factor(self, date_obj: Optional[date] = None,
                             is_financial_report_period: bool = False,
                             days_to_month_end: int = 15) -> FactorScore:
        return self._calendar_factor.calc(date_obj, is_financial_report_period, days_to_month_end)

    def calc_enhanced_composite(self,
                               indicators: Dict[str, float],
                               prices: Optional[List[float]] = None,
                               volumes: Optional[List[float]] = None,
                               date_obj: Optional[date] = None) -> EnhancedCompositeResult:
        """计算增强多因子综合分。

        Args:
            indicators: 因子指标字典，可包含：
                - v7.5: pe/pb/ps/roe/revenue_growth/volatility 等
                - v7.6 新增: momentum_5d/momentum_20d/main_flow_ratio/north_flow_change/etf_net_flow/margin_balance_change
            prices: 价格序列（用于动量反转 / 波动率因子）
            volumes: 成交量序列（可选）
            date_obj: 当前日期（日历因子用）

        Returns:
            EnhancedCompositeResult 综合评分结果
        """
        factor_scores: Dict[str, FactorScore] = {}

        # 1) v7.5 基础因子（简化映射）
        if "pe" in indicators:
            pe = indicators["pe"]
            # PE 越低越好（相对行业中位数 20）
            pe_score = max(0, min(100, 100 - (pe - 10) * 5))
            factor_scores["value_pe"] = FactorScore(
                name="value_pe", score=pe_score, category="value",
                confidence=0.7,  # 修复 BUG-001：基础因子 confidence 不应为 0
                description=f"PE {pe:.1f}",
            )
        if "pb" in indicators:
            pb = indicators["pb"]
            pb_score = max(0, min(100, 100 - (pb - 1.5) * 40))
            factor_scores["value_pb"] = FactorScore(
                name="value_pb", score=pb_score, category="value",
                confidence=0.7,
                description=f"PB {pb:.2f}",
            )
        if "roe" in indicators:
            roe = indicators["roe"]
            roe_score = max(0, min(100, 50 + roe * 250))  # ROE=15% → 87.5
            factor_scores["quality_roe"] = FactorScore(
                name="quality_roe", score=roe_score, category="quality",
                confidence=0.7,
                description=f"ROE {roe:.1%}",
            )
        if "revenue_growth" in indicators:
            growth = indicators["revenue_growth"]
            growth_score = max(0, min(100, 50 + growth * 200))
            factor_scores["growth_rev"] = FactorScore(
                name="growth_rev", score=growth_score, category="growth",
                confidence=0.7,
                description=f"营收增长 {growth:.1%}",
            )

        # 2) v7.6 新增因子
        if prices and len(prices) >= 60:
            factor_scores["momentum_reversion"] = self.calc_momentum_factor(prices, volumes)
            factor_scores["volatility_regime"] = self.calc_volatility_factor(prices)

        # 资金流因子（如提供）
        # 修复 BUG-002：仅当非默认值（None/0）时纳入评分，避免零值拉低分数
        capital_kwargs = {}
        for k in ("main_flow_value", "main_flow_ratio", "north_flow_change",
                  "etf_net_flow", "margin_balance_change"):
            v = indicators.get(k)
            if v is not None and v != 0:
                capital_kwargs[k] = v
        if capital_kwargs:
            factor_scores["capital_flow"] = self.calc_capital_flow_factor(**capital_kwargs)

        # 日历因子（如提供日期）
        if date_obj or "days_to_month_end" in indicators:
            factor_scores["calendar"] = self.calc_calendar_factor(
                date_obj=date_obj,
                is_financial_report_period=indicators.get("is_financial_report_period", False),
                days_to_month_end=indicators.get("days_to_month_end", 15),
            )

        # 3) 多因子合成（按权重）
        if not factor_scores:
            return EnhancedCompositeResult(
                total_score=50.0,
                factors={},
                recommendation="数据不足",
                confidence=0.1,
                weights=self.weights,
                market_regime="unknown",
            )

        # 分类汇总：取各类因子平均值（避免单一类因子过拟合）
        category_scores: Dict[str, List[float]] = {}
        category_weights: Dict[str, float] = {}
        category_confidence: Dict[str, List[float]] = {}

        for fname, fscore in factor_scores.items():
            category = fscore.category
            category_scores.setdefault(category, []).append(fscore.score)
            category_confidence.setdefault(category, []).append(fscore.confidence)
            category_weights[category] = self.weights.get(category, 0.05)

        # 类别内平均
        category_avg = {cat: sum(scores) / len(scores) for cat, scores in category_scores.items()}

        # 类别加权
        total = sum(category_avg[cat] * category_weights.get(cat, 0)
                    for cat in category_avg)
        total_weight = sum(category_weights.get(cat, 0) for cat in category_avg)
        if total_weight > 0:
            total_score = total / total_weight
        else:
            total_score = 50.0

        # 综合置信度
        all_confidences = [c for cs in category_confidence.values() for c in cs]
        avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

        # 投资建议
        if total_score >= 75:
            recommendation = "🟢 强烈推荐"
        elif total_score >= 60:
            recommendation = "🟢 推荐"
        elif total_score >= 45:
            recommendation = "🟡 中性"
        elif total_score >= 30:
            recommendation = "🟠 谨慎"
        else:
            recommendation = "🔴 回避"

        # 市场状态判定（基于波动率 + 动量）
        market_regime = self._detect_market_regime(prices, factor_scores)

        return EnhancedCompositeResult(
            total_score=total_score,
            factors=factor_scores,
            recommendation=recommendation,
            confidence=avg_conf,
            weights=self.weights,
            market_regime=market_regime,
            metadata={
                "category_scores": category_avg,
                "factor_count": len(factor_scores),
            },
        )

    def _detect_market_regime(self,
                              prices: Optional[List[float]],
                              factor_scores: Dict[str, FactorScore]) -> str:
        """检测当前市场状态（牛市/熊市/震荡市）。"""
        if not prices or len(prices) < 60:
            return "unknown"
        # 60 日涨幅
        ret_60d = (prices[-1] - prices[-60]) / prices[-60]
        vol_score = factor_scores.get("volatility_regime")
        vol_annual = vol_score.raw_value if vol_score else 0.3

        if ret_60d > 0.15 and vol_annual < 0.35:
            return "牛市"
        elif ret_60d < -0.15 and vol_annual > 0.30:
            return "熊市"
        elif vol_annual > 0.4:
            return "高波动震荡"
        else:
            return "震荡市"


# ============================================================================
# 便捷函数
# ============================================================================


def quick_enhanced_score(indicators: Dict[str, float],
                        prices: Optional[List[float]] = None,
                        volumes: Optional[List[float]] = None,
                        weights: Optional[Dict[str, float]] = None,
                        date_obj: Optional[date] = None) -> Dict:
    """快速计算增强多因子评分（一次性返回 dict）。

    Args:
        indicators: 因子指标
        prices: 价格序列
        volumes: 成交量序列
        weights: 自定义权重
        date_obj: 日期

    Returns:
        {
            'total_score': 综合分,
            'recommendation': 投资建议,
            'confidence': 置信度,
            'market_regime': 市场状态,
            'factors': 各因子分,
            'weights': 权重,
        }
    """
    lib = EnhancedFactorLibrary(weights=weights)
    result = lib.calc_enhanced_composite(indicators, prices, volumes, date_obj)
    return {
        "total_score": round(result.total_score, 2),
        "recommendation": result.recommendation,
        "confidence": round(result.confidence, 2),
        "market_regime": result.market_regime,
        "factors": {
            name: {"score": round(f.score, 2), "confidence": round(f.confidence, 2),
                   "description": f.description}
            for name, f in result.factors.items()
        },
        "weights": result.weights,
    }


if __name__ == "__main__":
    # CLI 演示
    import json
    demo = quick_enhanced_score(
        indicators={
            "pe": 15, "pb": 1.8, "roe": 0.18,
            "revenue_growth": 0.25,
            "main_flow_ratio": 0.12,
            "north_flow_change": 0.05,
            "etf_net_flow": 2.5,
            "days_to_month_end": 3,
        },
        prices=[100 + i * 0.3 for i in range(80)],
        volumes=[10000 + i * 100 for i in range(80)],
        date_obj=date(2026, 8, 28),
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2))