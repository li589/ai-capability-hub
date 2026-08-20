# -*- coding: utf-8 -*-
"""
风险模型 - 风险管理模块
Risk Models - Risk Management Module

基于 QuantConnect Lean RiskFramework 架构

风险管理类型：
- MaximumDrawdownRiskModel: 最大回撤控制
- StopLossRiskModel: 止损风险管理
- TargetProfitRiskModel: 止盈风险管理
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskDecision(Enum):
    """风险决策"""
    NONE = 0          # 无动作
    REDUCE = -1       # 减仓
    EXIT = -2         # 清仓


@dataclass
class RiskReport:
    """
    风险报告
    """
    symbol: str
    decision: RiskDecision
    reason: str
    current_value: float = 0
    target_value: float = 0
    loss_percentage: float = 0
    metadata: Dict = field(default_factory=dict)


class RiskModel:
    """风险模型基类"""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__

    def assess(self, symbol: str, position: Dict, market_data: Dict) -> RiskReport:
        """
        评估风险

        Args:
            symbol: 股票代码
            position: 持仓信息 {'quantity', 'avg_price', 'current_price', 'PnL'}
            market_data: 市场数据 {'price', 'volatility', 'volume'}

        Returns:
            RiskReport: 风险报告
        """
        raise NotImplementedError


class MaximumDrawdownRiskModel(RiskModel):
    """
    最大回撤风险模型

    原理：
    - 当持仓亏损超过 max_drawdown 时触发风控
    - 可设置分批减仓或清仓

    参数：
    - max_drawdown: 最大回撤阈值（默认10%）
    - reduce_percent: 触发后的减仓比例（默认50%）
    """

    def __init__(self, max_drawdown: float = 0.10, reduce_percent: float = 0.5, name: str = ""):
        super().__init__(name or "MaxDrawdown")
        self.max_drawdown = max_drawdown
        self.reduce_percent = reduce_percent

    def assess(self, symbol: str, position: Dict, market_data: Dict) -> RiskReport:
        """评估回撤风险"""
        avg_price = position.get('avg_price', 0)
        current_price = market_data.get('price', 0)

        if avg_price <= 0 or current_price <= 0:
            return RiskReport(
                symbol=symbol,
                decision=RiskDecision.NONE,
                reason="无效价格数据"
            )

        # 计算亏损百分比
        loss_pct = (current_price - avg_price) / avg_price

        decision = RiskDecision.NONE
        reason = "回撤在容忍范围内"

        # 先判严重亏损(EXIT)，否则 1.5 倍阈值分支永远不可达
        if loss_pct < -self.max_drawdown * 1.5:
            decision = RiskDecision.EXIT
            reason = f"亏损{abs(loss_pct)*100:.1f}%严重超过阈值，强制清仓"
        elif loss_pct < -self.max_drawdown:
            decision = RiskDecision.REDUCE
            reason = f"亏损{abs(loss_pct)*100:.1f}%超过阈值{self.max_drawdown*100:.1f}%"

        current_value = position.get('quantity', 0) * current_price
        if decision == RiskDecision.EXIT:
            target_value = 0
        elif decision == RiskDecision.REDUCE:
            target_value = current_value * (1 - self.reduce_percent)
        else:
            target_value = current_value

        return RiskReport(
            symbol=symbol,
            decision=decision,
            reason=reason,
            current_value=current_value,
            target_value=target_value,
            loss_percentage=abs(loss_pct) * 100,
            metadata={
                'avg_price': avg_price,
                'current_price': current_price,
                'max_drawdown': self.max_drawdown,
                'reduce_percent': self.reduce_percent
            }
        )


class StopLossRiskModel(RiskModel):
    """
    止损风险模型

    原理：
    - 固定止损：亏损达到阈值立即止损
    - 跟踪止损：最高点回落超过阈值止损

    参数：
    - stop_loss_pct: 止损阈值（默认5%）
    - trailing_pct: 跟踪止损阈值（默认3%）
    - use_trailing: 是否使用跟踪止损（默认True）
    """

    def __init__(
        self,
        stop_loss_pct: float = 0.05,
        trailing_pct: float = 0.03,
        use_trailing: bool = True,
        name: str = ""
    ):
        super().__init__(name or "StopLoss")
        self.stop_loss_pct = stop_loss_pct
        self.trailing_pct = trailing_pct
        self.use_trailing = use_trailing
        self._high_prices: Dict[str, float] = {}

    def assess(self, symbol: str, position: Dict, market_data: Dict) -> RiskReport:
        """评估止损风险"""
        avg_price = position.get('avg_price', 0)
        current_price = market_data.get('price', 0)
        quantity = position.get('quantity', 0)

        if avg_price <= 0 or current_price <= 0 or quantity <= 0:
            return RiskReport(
                symbol=symbol,
                decision=RiskDecision.NONE,
                reason="无效数据"
            )

        # 更新最高价
        if symbol not in self._high_prices:
            self._high_prices[symbol] = current_price
        else:
            self._high_prices[symbol] = max(self._high_prices[symbol], current_price)

        high_price = self._high_prices[symbol]
        loss_pct = (current_price - avg_price) / avg_price
        drawdown_from_high = (current_price - high_price) / high_price

        decision = RiskDecision.NONE
        reason = "未触发止损"

        # 固定止损
        if loss_pct < -self.stop_loss_pct:
            decision = RiskDecision.EXIT
            reason = f"亏损{abs(loss_pct)*100:.1f}%触发固定止损{self.stop_loss_pct*100:.1f}%"

        # 跟踪止损
        elif self.use_trailing and drawdown_from_high < -self.trailing_pct:
            decision = RiskDecision.EXIT
            reason = f"从高点回落{abs(drawdown_from_high)*100:.1f}%触发跟踪止损{self.trailing_pct*100:.1f}%"

        current_value = quantity * current_price

        return RiskReport(
            symbol=symbol,
            decision=decision,
            reason=reason,
            current_value=current_value,
            target_value=0 if decision == RiskDecision.EXIT else current_value,
            loss_percentage=abs(loss_pct) * 100,
            metadata={
                'high_price': high_price,
                'avg_price': avg_price,
                'current_price': current_price,
                'drawdown_from_high': drawdown_from_high * 100,
                'stop_loss_pct': self.stop_loss_pct * 100,
                'trailing_pct': self.trailing_pct * 100
            }
        )


class TargetProfitRiskModel(RiskModel):
    """
    止盈风险模型

    原理：
    - 固定目标：盈利达到目标后分批止盈
    - 移动止盈：不断上移止损线

    参数：
    - target_profit_pct: 目标盈利（默认20%）
    - trailing_pct: 移动止盈回撤（默认8%）
    - exit_percent: 每次止盈比例（默认50%）
    """

    def __init__(
        self,
        target_profit_pct: float = 0.20,
        trailing_pct: float = 0.08,
        exit_percent: float = 0.5,
        name: str = ""
    ):
        super().__init__(name or "TargetProfit")
        self.target_profit_pct = target_profit_pct
        self.trailing_pct = trailing_pct
        self.exit_percent = exit_percent
        self._high_prices: Dict[str, float] = {}
        self._stop_prices: Dict[str, float] = {}

    def assess(self, symbol: str, position: Dict, market_data: Dict) -> RiskReport:
        """评估止盈风险"""
        avg_price = position.get('avg_price', 0)
        current_price = market_data.get('price', 0)
        quantity = position.get('quantity', 0)

        if avg_price <= 0 or current_price <= 0 or quantity <= 0:
            return RiskReport(
                symbol=symbol,
                decision=RiskDecision.NONE,
                reason="无效数据"
            )

        # 初始化/更新高价
        # 止盈线初始为 0（不启用）：未达 target_profit_pct 前不做移动止盈，
        # 否则初始线高于市价会导致新持仓第一次评估即误触发减仓
        if symbol not in self._high_prices:
            self._high_prices[symbol] = current_price
            self._stop_prices[symbol] = 0.0
        else:
            self._high_prices[symbol] = max(self._high_prices[symbol], current_price)

        high_price = self._high_prices[symbol]
        profit_pct = (current_price - avg_price) / avg_price
        drawdown_from_high = (current_price - high_price) / high_price

        # 更新止盈线
        if profit_pct >= self.target_profit_pct:
            self._stop_prices[symbol] = high_price * (1 - self.trailing_pct)

        decision = RiskDecision.NONE
        reason = "未触发止盈"
        target_reduction = 0

        # 触发止盈
        if current_price <= self._stop_prices.get(symbol, 0):
            decision = RiskDecision.REDUCE
            reason = f"价格跌破止盈线{self._stop_prices[symbol]:.2f}，减仓{self.exit_percent*100:.0f}%"
            target_reduction = self.exit_percent

        current_value = quantity * current_price
        target_value = current_value * (1 - target_reduction)

        return RiskReport(
            symbol=symbol,
            decision=decision,
            reason=reason,
            current_value=current_value,
            target_value=target_value,
            loss_percentage=0,  # 止盈不考虑亏损
            metadata={
                'high_price': high_price,
                'avg_price': avg_price,
                'stop_price': self._stop_prices.get(symbol, 0),
                'profit_pct': profit_pct * 100,
                'drawdown_from_high': drawdown_from_high * 100,
                'target_profit_pct': self.target_profit_pct * 100,
                'trailing_pct': self.trailing_pct * 100
            }
        )


class CompositeRiskModel(RiskModel):
    """
    组合风险模型

    组合多个风险模型进行综合评估
    """

    def __init__(self, models: List[RiskModel] = None, name: str = ""):
        super().__init__(name or "CompositeRisk")
        self.models = models or []

    def add_model(self, model: RiskModel):
        """添加风险模型"""
        self.models.append(model)

    def assess(self, symbol: str, position: Dict, market_data: Dict) -> RiskReport:
        """综合评估风险"""
        if not self.models:
            return RiskReport(
                symbol=symbol,
                decision=RiskDecision.NONE,
                reason="无风控模型"
            )

        # 执行所有风控模型
        reports = []
        for model in self.models:
            report = model.assess(symbol, position, market_data)
            reports.append(report)

        # 找最严格的风控决策
        # EXIT > REDUCE > NONE
        decisions = [r.decision for r in reports]
        if RiskDecision.EXIT in decisions:
            decision = RiskDecision.EXIT
            reason = next(r.reason for r in reports if r.decision == RiskDecision.EXIT)
        elif RiskDecision.REDUCE in decisions:
            decision = RiskDecision.REDUCE
            reason = next(r.reason for r in reports if r.decision == RiskDecision.REDUCE)
        else:
            decision = RiskDecision.NONE
            reason = "所有风控模型均未触发"

        return RiskReport(
            symbol=symbol,
            decision=decision,
            reason=reason,
            current_value=reports[0].current_value,
            target_value=reports[0].target_value,
            metadata={'sub_reports': [r.metadata for r in reports]}
        )


def create_risk_model(model_type: str, **kwargs) -> RiskModel:
    """
    工厂函数：创建风险模型

    Args:
        model_type: 模型类型
            - 'max_drawdown': 最大回撤模型
            - 'stop_loss': 止损模型
            - 'target_profit': 止盈模型
            - 'composite': 组合风控模型

    Returns:
        RiskModel: 实例化的模型
    """
    models = {
        'max_drawdown': MaximumDrawdownRiskModel,
        'stop_loss': StopLossRiskModel,
        'target_profit': TargetProfitRiskModel,
        'composite': CompositeRiskModel,
    }

    model_class = models.get(model_type.lower())
    if not model_class:
        raise ValueError(f"Unknown model type: {model_type}")

    return model_class(**kwargs)


# ============================================================
# v3.1.0 增量 — Cornish-Fisher VaR / Expected Shortfall
# ============================================================

def _norm_ppf(p: float) -> float:
    """标准正态分布逆 CDF（分位数函数）。

    Acklam 有理近似（无 scipy 环境的标准库实现），最大误差约 1e-9。
    参考: P. J. Acklam, "An algorithm for computing the inverse normal
    cumulative distribution function".
    """
    import math
    if p <= 0:
        return -float('inf')
    if p >= 1:
        return float('inf')
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > p_high:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def cornish_fisher_var(returns, alpha=0.05):
    """Cornish-Fisher 修正 VaR / Expected Shortfall — 考虑偏度/峰态。

    收益分布用 Cornish-Fisher 展开修正左尾分位数：
        z_cf = z + (z²-1)·S/6 + (z³-3z)·K/24 - (2z³-5z)·S²/36
    其中 z = Φ⁻¹(alpha)（由 alpha 计算，支持任意显著性水平）。

    符号约定：var 与 es 均为**正数损失**（如 var=0.03 表示 3% 损失）。

    Returns:
        dict: var, es, skew, kurt, z_cf, method
    """
    import numpy as _np
    r = _np.array(returns, dtype=float)
    r = r[~_np.isnan(r)]
    if len(r) < 30:
        return {'var': None, 'es': None,
                'method': 'cornish-fisher', 'error': '样本不足'}
    mu = float(_np.mean(r))
    sd = float(_np.std(r))
    sk = float(_np.mean(((r - mu) / sd) ** 3)) if sd > 0 else 0
    ku = float(_np.mean(((r - mu) / sd) ** 4) - 3) if sd > 0 else 0
    # 左尾分位数由 alpha 计算（修复：不再硬编码 5%）
    z = _norm_ppf(alpha)
    z_cf = (z + (z ** 2 - 1) * sk / 6.0 + (z ** 3 - 3 * z) * ku / 24.0
            - (2 * z ** 3 - 5 * z) * (sk ** 2) / 36.0)
    # 统一为正数损失：mu + sd*z_cf 是收益分位数（通常为负），取负得损失
    var = -(mu + sd * z_cf)
    es = float(-_np.mean(_np.sort(r)[:max(1, int(len(r) * alpha))]))
    return {
        'var': round(float(var), 4),
        'es': round(es, 4),
        'skew': round(sk, 4),
        'kurt': round(ku, 4),
        'z_cf': round(z_cf, 4),
        'method': 'cornish-fisher',
    }
