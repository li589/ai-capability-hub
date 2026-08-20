# -*- coding: utf-8 -*-
"""
策略回测模块 - 轻量级回测引擎

功能：
1. 历史数据回测：基于OHLCV数据验证交易策略
2. 绩效指标计算：夏普比率、最大回撤、胜率等
3. 策略对比：多个策略在同一时间段的表现对比
4. 风险调整收益：Sortino、Calmar、信息比率

使用示例：
```python
from quantitative.backtest import Backtester, Strategy

# 定义策略
class MyStrategy(Strategy):
    def should_buy(self, data, index):
        return data['rsi'][index] < 30

    def should_sell(self, data, index):
        return data['rsi'][index] > 70

# 运行回测
backtester = Backtester(initial_capital=100000)
result = backtester.run(
    strategy=MyStrategy(),
    data=ohlcv_data,
    start_date='2024-01-01',
    end_date='2024-12-31'
)

print(result.summary())
```
"""

import math
import logging
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """交易记录"""
    entry_date: str
    entry_price: float
    exit_date: str = ""
    exit_price: float = 0.0
    quantity: int = 0
    direction: str = "long"  # long or short
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_days: int = 0


@dataclass
class BacktestResult:
    """回测结果"""
    # 绩效指标
    total_return: float = 0.0          # 总收益率
    annual_return: float = 0.0         # 年化收益率
    sharpe_ratio: float = 0.0          # 夏普比率
    sortino_ratio: float = 0.0         # Sortino比率
    calmar_ratio: float = 0.0          # Calmar比率
    max_drawdown: float = 0.0          # 最大回撤
    max_drawdown_duration: int = 0     # 最大回撤持续天数
    volatility: float = 0.0            # 波动率
    win_rate: float = 0.0              # 胜率
    profit_factor: float = 0.0         # 盈亏比
    avg_trade_return: float = 0.0      # 平均交易收益
    avg_holding_days: float = 0.0      # 平均持仓天数

    # 交易统计
    total_trades: int = 0              # 总交易次数
    winning_trades: int = 0            # 盈利交易次数
    losing_trades: int = 0             # 亏损交易次数
    max_consecutive_wins: int = 0      # 最大连续盈利
    max_consecutive_losses: int = 0    # 最大连续亏损

    # 详细数据
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)

    # 元数据
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 0.0
    final_capital: float = 0.0
    strategy_name: str = ""

    def summary(self) -> Dict:
        """返回摘要字典"""
        return {
            'strategy': self.strategy_name,
            'period': f"{self.start_date} ~ {self.end_date}",
            'total_return': f"{self.total_return:.2%}",
            'annual_return': f"{self.annual_return:.2%}",
            'sharpe_ratio': f"{self.sharpe_ratio:.2f}",
            'max_drawdown': f"{self.max_drawdown:.2%}",
            'win_rate': f"{self.win_rate:.2%}",
            'total_trades': self.total_trades,
            'profit_factor': f"{self.profit_factor:.2f}",
        }


class Strategy:
    """
    交易策略基类

    子类需要实现 should_buy 和 should_sell 方法
    """

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__

    def should_buy(self, data: Dict, index: int) -> bool:
        """
        是否应该买入

        Args:
            data: 包含OHLCV和指标的字典
            index: 当前数据索引

        Returns:
            bool: 是否买入
        """
        raise NotImplementedError

    def should_sell(self, data: Dict, index: int) -> bool:
        """
        是否应该卖出

        Args:
            data: 包含OHLCV和指标的字典
            index: 当前数据索引

        Returns:
            bool: 是否卖出
        """
        raise NotImplementedError

    def position_size(self, data: Dict, index: int, capital: float) -> float:
        """
        计算仓位大小（占总资金比例）

        Args:
            data: 数据
            index: 当前索引
            capital: 当前资金

        Returns:
            float: 仓位比例（0-1）
        """
        return 1.0  # 默认满仓


class RSIStrategy(Strategy):
    """RSI超买超卖策略"""

    def __init__(self, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI策略")
        self.oversold = oversold
        self.overbought = overbought

    def should_buy(self, data: Dict, index: int) -> bool:
        rsi = data.get('rsi', [])
        if index < len(rsi):
            return rsi[index] < self.oversold
        return False

    def should_sell(self, data: Dict, index: int) -> bool:
        rsi = data.get('rsi', [])
        if index < len(rsi):
            return rsi[index] > self.overbought
        return False


class MACDStrategy(Strategy):
    """MACD金叉死叉策略"""

    def __init__(self):
        super().__init__("MACD策略")

    def should_buy(self, data: Dict, index: int) -> bool:
        macd = data.get('macd_hist', [])
        if index >= 1 and index < len(macd):
            return macd[index] > 0 and macd[index - 1] <= 0
        return False

    def should_sell(self, data: Dict, index: int) -> bool:
        macd = data.get('macd_hist', [])
        if index >= 1 and index < len(macd):
            return macd[index] < 0 and macd[index - 1] >= 0
        return False


class DualMAStrategy(Strategy):
    """双均线策略"""

    def __init__(self, fast: int = 5, slow: int = 20):
        super().__init__("双均线策略")
        self.fast = fast
        self.slow = slow

    def should_buy(self, data: Dict, index: int) -> bool:
        ma_fast = data.get(f'ma{self.fast}', [])
        ma_slow = data.get(f'ma{self.slow}', [])
        if index >= 1 and index < len(ma_fast) and index < len(ma_slow):
            return ma_fast[index] > ma_slow[index] and ma_fast[index - 1] <= ma_slow[index - 1]
        return False

    def should_sell(self, data: Dict, index: int) -> bool:
        ma_fast = data.get(f'ma{self.fast}', [])
        ma_slow = data.get(f'ma{self.slow}', [])
        if index >= 1 and index < len(ma_fast) and index < len(ma_slow):
            return ma_fast[index] < ma_slow[index] and ma_fast[index - 1] >= ma_slow[index - 1]
        return False


class Backtester:
    """
    回测引擎

    支持：
    - 多空交易
    - 手续费和滑点
    - 仓位管理
    - 绩效指标计算
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission: float = 0.001,  # 手续费率0.1%
        slippage: float = 0.001,    # 滑点0.1%
        risk_free_rate: float = 0.03  # 无风险利率3%
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_free_rate = risk_free_rate

    def run(
        self,
        strategy: Strategy,
        data: Dict,
        start_idx: int = 0,
        end_idx: int = None
    ) -> BacktestResult:
        """
        运行回测

        Args:
            strategy: 交易策略
            data: 包含OHLCV和指标的字典，每个字段是列表
            start_idx: 起始索引
            end_idx: 结束索引

        Returns:
            BacktestResult: 回测结果
        """
        closes = data.get('close', [])
        if not closes:
            return BacktestResult(strategy_name=strategy.name)

        if end_idx is None:
            end_idx = len(closes) - 1

        # 初始化
        capital = self.initial_capital
        position = 0  # 持仓数量
        entry_price = 0
        entry_date = ""
        trades = []
        equity_curve = []
        daily_returns = []

        # 模拟交易
        for i in range(start_idx, end_idx + 1):
            current_price = closes[i]

            # 检查卖出信号
            if position > 0 and strategy.should_sell(data, i):
                # 计算卖出收益
                exit_price = current_price * (1 - self.slippage)
                proceeds = position * exit_price * (1 - self.commission)
                pnl = proceeds - position * entry_price
                pnl_pct = (exit_price - entry_price) / entry_price

                trades.append(Trade(
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=str(i),
                    exit_price=exit_price,
                    quantity=position,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    holding_days=i - int(entry_date) if entry_date.isdigit() else 0
                ))

                capital += proceeds
                position = 0

            # 检查买入信号
            elif position == 0 and strategy.should_buy(data, i):
                # 计算仓位
                position_pct = strategy.position_size(data, i, capital)
                buy_price = current_price * (1 + self.slippage)
                max_shares = int(capital * position_pct / buy_price)

                if max_shares > 0:
                    cost = max_shares * buy_price * (1 + self.commission)
                    capital -= cost
                    position = max_shares
                    entry_price = buy_price
                    entry_date = str(i)

            # 记录权益
            equity = capital + position * current_price
            equity_curve.append(equity)

            # 计算日收益率
            if len(equity_curve) > 1:
                daily_ret = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2]
                daily_returns.append(daily_ret)

        # 计算绩效指标
        result = self._calculate_metrics(
            trades=trades,
            equity_curve=equity_curve,
            daily_returns=daily_returns,
            strategy_name=strategy.name
        )

        return result

    def _calculate_metrics(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        daily_returns: List[float],
        strategy_name: str
    ) -> BacktestResult:
        """计算绩效指标"""
        result = BacktestResult(
            strategy_name=strategy_name,
            initial_capital=self.initial_capital,
            final_capital=equity_curve[-1] if equity_curve else self.initial_capital,
            trades=trades,
            equity_curve=equity_curve,
            daily_returns=daily_returns,
        )

        if not equity_curve:
            return result

        # 总收益率
        result.total_return = (result.final_capital - self.initial_capital) / self.initial_capital

        # 年化收益率（假设252个交易日）
        n_days = len(equity_curve)
        if n_days > 0:
            result.annual_return = (1 + result.total_return) ** (252 / n_days) - 1

        # 波动率（支持无numpy环境）
        if daily_returns:
            try:
                import numpy as np
                returns = np.array(daily_returns)
                result.volatility = float(np.std(returns) * np.sqrt(252))

                # 夏普比率
                excess_return = result.annual_return - self.risk_free_rate
                if result.volatility > 0:
                    result.sharpe_ratio = excess_return / result.volatility

                # Sortino比率（只考虑下行波动）
                downside_returns = returns[returns < 0]
                if len(downside_returns) > 0:
                    downside_vol = float(np.std(downside_returns) * np.sqrt(252))
                    if downside_vol > 0:
                        result.sortino_ratio = excess_return / downside_vol
            except ImportError:
                # 纯Python实现（无numpy时）
                mean_ret = sum(daily_returns) / len(daily_returns)
                variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
                result.volatility = (variance ** 0.5) * (252 ** 0.5)

                excess_return = result.annual_return - self.risk_free_rate
                if result.volatility > 0:
                    result.sharpe_ratio = excess_return / result.volatility

        # 最大回撤
        result.max_drawdown, result.max_drawdown_duration = self._calc_max_drawdown(equity_curve)

        # Calmar比率
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annual_return / abs(result.max_drawdown)

        # 交易统计
        result.total_trades = len(trades)
        if trades:
            winning = [t for t in trades if t.pnl > 0]
            losing = [t for t in trades if t.pnl <= 0]

            result.winning_trades = len(winning)
            result.losing_trades = len(losing)
            result.win_rate = len(winning) / len(trades) if trades else 0

            # 盈亏比
            avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0
            avg_loss = abs(sum(t.pnl for t in losing) / len(losing)) if losing else 1
            result.profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

            # 平均交易收益
            result.avg_trade_return = sum(t.pnl_pct for t in trades) / len(trades)

            # 平均持仓天数
            result.avg_holding_days = sum(t.holding_days for t in trades) / len(trades)

            # 最大连续盈亏
            result.max_consecutive_wins = self._max_consecutive(trades, True)
            result.max_consecutive_losses = self._max_consecutive(trades, False)

        return result

    def _calc_max_drawdown(self, equity_curve: List[float]) -> Tuple[float, int]:
        """计算最大回撤和持续天数"""
        if not equity_curve:
            return 0.0, 0

        max_dd = 0
        max_dd_duration = 0
        peak = equity_curve[0]
        dd_start = 0

        for i, equity in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                dd_start = i

            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_duration = i - dd_start

        return max_dd, max_dd_duration

    def _max_consecutive(self, trades: List[Trade], winning: bool) -> int:
        """计算最大连续盈/亏次数"""
        max_count = 0
        current_count = 0

        for trade in trades:
            if (winning and trade.pnl > 0) or (not winning and trade.pnl <= 0):
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count


# ============================================================
# 便捷函数
# ============================================================

def quick_backtest(
    strategy: Strategy,
    prices: List[float],
    indicators: Dict[str, List[float]] = None,
    initial_capital: float = 100000
) -> Dict:
    """
    快速回测（简化版）

    Args:
        strategy: 交易策略
        prices: 价格序列
        indicators: 指标字典
        initial_capital: 初始资金

    Returns:
        Dict: 回测结果摘要
    """
    data = {'close': prices}
    if indicators:
        data.update(indicators)

    backtester = Backtester(initial_capital=initial_capital)
    result = backtester.run(strategy, data)

    return result.summary()
