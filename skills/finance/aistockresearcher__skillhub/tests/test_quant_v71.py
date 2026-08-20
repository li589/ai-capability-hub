# -*- coding: utf-8 -*-
"""
量化模块 v7.1.0 测试

测试内容：
1. 数据源管理器（多源冗余 + 自动降级）
2. 因子库（多因子模型）
3. 策略回测引擎
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


# ============================================================
# 数据源管理器测试
# ============================================================

class TestDataSourceManager:
    """数据源管理器测试"""

    def test_source_registration(self):
        """测试数据源注册"""
        from stock_researcher.data.source_manager import DataSourceManager, DataSource

        manager = DataSourceManager()

        # 注册数据源
        source = DataSource(
            name="test_source",
            fetch_func=lambda codes: {"600519": {"price": 1800}},
            priority=1,
        )
        manager.register_source("realtime", source)

        assert "realtime" in manager._sources
        assert len(manager._sources["realtime"]) == 1
        assert manager._sources["realtime"][0].name == "test_source"

    def test_source_priority_order(self):
        """测试数据源优先级排序"""
        from stock_researcher.data.source_manager import DataSourceManager, DataSource

        manager = DataSourceManager()

        # 注册多个数据源（不同优先级）
        manager.register_source("realtime", DataSource(
            name="low_priority",
            fetch_func=lambda: {},
            priority=2,
        ))
        manager.register_source("realtime", DataSource(
            name="high_priority",
            fetch_func=lambda: {},
            priority=1,
        ))

        # 验证排序
        assert manager._sources["realtime"][0].name == "high_priority"
        assert manager._sources["realtime"][1].name == "low_priority"

    def test_fetch_with_fallback(self):
        """测试自动降级获取"""
        from stock_researcher.data.source_manager import DataSourceManager, DataSource

        manager = DataSourceManager()

        # 主数据源（会失败）
        def failing_fetch(**kwargs):
            raise Exception("主数据源失败")

        # 备用数据源（成功）
        def backup_fetch(**kwargs):
            return {"600519": {"price": 1800}}

        manager.register_source("realtime", DataSource(
            name="primary",
            fetch_func=failing_fetch,
            priority=1,
            max_retries=0,
        ))
        manager.register_source("realtime", DataSource(
            name="backup",
            fetch_func=backup_fetch,
            priority=2,
        ))

        # 应该自动降级到备用源
        result = manager.fetch("realtime")
        assert result is not None
        assert "600519" in result

    def test_cache_mechanism(self):
        """测试缓存机制"""
        from stock_researcher.data.source_manager import DataSourceManager, DataSource

        manager = DataSourceManager()

        call_count = 0

        def fetch_func(**kwargs):
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        manager.register_source("test", DataSource(
            name="test",
            fetch_func=fetch_func,
            priority=1,
            cache_ttl=60,
        ))

        # 第一次调用
        result1 = manager.fetch("test", use_cache=True)
        assert call_count == 1

        # 第二次调用（应该使用缓存）
        result2 = manager.fetch("test", use_cache=True)
        assert call_count == 1  # 没有再次调用
        assert result1 == result2

    def test_health_report(self):
        """测试健康报告"""
        from stock_researcher.data.source_manager import DataSourceManager, DataSource

        manager = DataSourceManager()

        manager.register_source("test", DataSource(
            name="test_source",
            fetch_func=lambda: {},
            priority=1,
        ))

        report = manager.get_health_report()
        assert "test" in report
        assert len(report["test"]) == 1
        assert report["test"][0]["name"] == "test_source"


# ============================================================
# 因子库测试
# ============================================================

class TestFactorLibrary:
    """因子库测试"""

    def test_value_factor_calculation(self):
        """测试价值因子计算"""
        from stock_researcher.quantitative.factors import FactorLibrary

        library = FactorLibrary()

        # 低估值股票（PE=10, PB=1.5）
        result = library.calc_value_factor(pe=10, pb=1.5)

        assert result.name == "value"
        assert result.value > 50  # 应该高于平均分
        assert result.category == "价值因子"

    def test_growth_factor_calculation(self):
        """测试成长因子计算"""
        from stock_researcher.quantitative.factors import FactorLibrary

        library = FactorLibrary()

        # 高成长股票
        result = library.calc_growth_factor(
            revenue_growth=0.3,
            earnings_growth=0.4
        )

        assert result.name == "growth"
        assert result.value > 60  # 高成长应该得高分

    def test_quality_factor_calculation(self):
        """测试质量因子计算"""
        from stock_researcher.quantitative.factors import FactorLibrary

        library = FactorLibrary()

        # 高质量公司
        result = library.calc_quality_factor(
            roe=0.20,
            gross_margin=0.40,
            debt_ratio=0.30
        )

        assert result.name == "quality"
        assert result.value > 60

    def test_momentum_factor_calculation(self):
        """测试动量因子计算"""
        from stock_researcher.quantitative.factors import FactorLibrary

        library = FactorLibrary()

        # 上涨趋势
        result = library.calc_momentum_factor(
            returns_5d=0.05,
            returns_20d=0.15
        )

        assert result.name == "momentum"
        assert result.value > 50

    def test_volatility_factor_calculation(self):
        """测试波动因子计算"""
        from stock_researcher.quantitative.factors import FactorLibrary

        library = FactorLibrary()

        # 低波动股票
        result = library.calc_volatility_factor(
            volatility_20d=0.20,
            beta=0.9
        )

        assert result.name == "volatility"
        assert result.value > 50

    def test_composite_score(self):
        """测试综合评分"""
        from stock_researcher.quantitative.factors import FactorLibrary

        library = FactorLibrary()

        # 优质股票数据
        result = library.calc_composite_score({
            'pe': 12,
            'pb': 1.5,
            'roe': 0.18,
            'revenue_growth': 0.25,
            'volatility_20d': 0.25,
        })

        assert result.total_score > 60
        assert result.recommendation in ["强烈买入", "买入"]
        assert result.confidence > 0

    def test_quick_score(self):
        """测试快速评分函数"""
        from stock_researcher.quantitative.factors import quick_score

        result = quick_score(pe=15, pb=2.0, roe=0.15, growth=0.20)

        assert "score" in result
        assert "recommendation" in result
        assert "confidence" in result


# ============================================================
# 策略回测测试
# ============================================================

class TestBacktester:
    """策略回测测试"""

    def test_rsi_strategy_buy_signal(self):
        """测试RSI策略买入信号"""
        from stock_researcher.quantitative.backtest import RSIStrategy

        strategy = RSIStrategy(oversold=30, overbought=70)

        # RSI < 30 应该触发买入
        data = {'rsi': [50, 40, 25, 35]}
        assert strategy.should_buy(data, 2) == True
        assert strategy.should_buy(data, 3) == False

    def test_rsi_strategy_sell_signal(self):
        """测试RSI策略卖出信号"""
        from stock_researcher.quantitative.backtest import RSIStrategy

        strategy = RSIStrategy(oversold=30, overbought=70)

        # RSI > 70 应该触发卖出
        data = {'rsi': [50, 60, 75, 65]}
        assert strategy.should_sell(data, 2) == True
        assert strategy.should_sell(data, 3) == False

    def test_macd_strategy_signals(self):
        """测试MACD策略信号"""
        from stock_researcher.quantitative.backtest import MACDStrategy

        strategy = MACDStrategy()

        # MACD金叉（从负转正）
        data = {'macd_hist': [-0.5, -0.2, 0.1, 0.3]}
        assert strategy.should_buy(data, 2) == True
        assert strategy.should_buy(data, 3) == False

        # MACD死叉（从正转负）
        data = {'macd_hist': [0.5, 0.2, -0.1, -0.3]}
        assert strategy.should_sell(data, 2) == True

    def test_backtester_run(self):
        """测试回测引擎运行"""
        from stock_researcher.quantitative.backtest import Backtester, RSIStrategy

        # 准备测试数据
        prices = [100, 102, 98, 95, 97, 103, 108, 105, 110, 115]
        rsi = [50, 55, 35, 25, 30, 55, 65, 60, 70, 75]

        data = {
            'close': prices,
            'rsi': rsi,
        }

        backtester = Backtester(initial_capital=100000)
        result = backtester.run(
            strategy=RSIStrategy(oversold=30, overbought=70),
            data=data
        )

        # 验证结果结构
        assert result.strategy_name == "RSI策略"
        assert result.initial_capital == 100000
        assert result.final_capital > 0
        assert len(result.equity_curve) == len(prices)

    def test_backtester_metrics(self):
        """测试回测指标计算"""
        from stock_researcher.quantitative.backtest import Backtester, RSIStrategy

        # 创建一个盈利的场景
        prices = [100, 95, 90, 85, 95, 105, 110, 115, 120, 125]
        rsi = [50, 40, 30, 20, 30, 50, 60, 65, 70, 75]

        data = {'close': prices, 'rsi': rsi}

        backtester = Backtester(initial_capital=100000)
        result = backtester.run(RSIStrategy(), data)

        # 应该有盈利
        assert result.total_return > 0
        assert result.win_rate > 0

    def test_quick_backtest(self):
        """测试快速回测函数"""
        from stock_researcher.quantitative.backtest import quick_backtest, RSIStrategy

        prices = [100, 102, 98, 95, 105, 110, 108, 115]
        rsi = [50, 55, 35, 25, 45, 60, 55, 70]

        result = quick_backtest(
            strategy=RSIStrategy(),
            prices=prices,
            indicators={'rsi': rsi}
        )

        assert "strategy" in result
        assert "total_return" in result
        assert "sharpe_ratio" in result

    def test_backtester_with_commission(self):
        """测试手续费对回测的影响"""
        from stock_researcher.quantitative.backtest import Backtester, RSIStrategy

        prices = [100, 90, 100, 110, 100]
        rsi = [50, 25, 50, 75, 50]
        data = {'close': prices, 'rsi': rsi}

        # 高手续费
        backtester_high = Backtester(initial_capital=100000, commission=0.01)
        result_high = backtester_high.run(RSIStrategy(), data)

        # 低手续费
        backtester_low = Backtester(initial_capital=100000, commission=0.001)
        result_low = backtester_low.run(RSIStrategy(), data)

        # 低手续费应该有更好的收益
        assert result_low.final_capital >= result_high.final_capital


# ============================================================
# 集成测试
# ============================================================

class TestQuantIntegration:
    """量化模块集成测试"""

    def test_factor_library_with_backtest(self):
        """测试因子库与回测引擎集成"""
        from stock_researcher.quantitative.factors import FactorLibrary
        from stock_researcher.quantitative.backtest import Backtester, Strategy

        # 使用因子评分来决定交易
        library = FactorLibrary()

        class FactorBasedStrategy(Strategy):
            def __init__(self):
                super().__init__("因子策略")
                self.library = FactorLibrary()

            def should_buy(self, data, index):
                pe = data.get('pe', [20])[min(index, len(data.get('pe', [])) - 1)]
                roe = data.get('roe', [0.1])[min(index, len(data.get('roe', [])) - 1)]
                result = self.library.calc_composite_score({'pe': pe, 'roe': roe})
                return result.total_score > 65

            def should_sell(self, data, index):
                pe = data.get('pe', [20])[min(index, len(data.get('pe', [])) - 1)]
                roe = data.get('roe', [0.1])[min(index, len(data.get('roe', [])) - 1)]
                result = self.library.calc_composite_score({'pe': pe, 'roe': roe})
                return result.total_score < 35

        # 准备数据
        data = {
            'close': [100, 105, 110, 108, 115, 120, 118, 125],
            'pe': [25, 23, 20, 22, 18, 16, 17, 15],
            'roe': [0.12, 0.13, 0.15, 0.14, 0.16, 0.18, 0.17, 0.19],
        }

        backtester = Backtester(initial_capital=100000)
        result = backtester.run(FactorBasedStrategy(), data)

        assert result.strategy_name == "因子策略"
        assert result.final_capital > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
