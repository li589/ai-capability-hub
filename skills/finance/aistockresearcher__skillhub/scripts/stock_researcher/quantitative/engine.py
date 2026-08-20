# -*- coding: utf-8 -*-
"""
量化引擎
Quantitative Engine

整合 Alpha模型 + Risk模型 + Portfolio模型
提供完整的量化交易信号生成和风险管理

使用示例：
```python
from quantitative.engine import QuantitativeEngine

# 初始化引擎
engine = QuantitativeEngine()

# 添加Alpha模型
engine.add_alpha_model('dual_thrust', period=20)

# 添加风控模型
engine.add_risk_model('stop_loss', stop_loss_pct=0.05)

# 设置组合模型
engine.set_portfolio_model('equal_weight', max_positions=10)

# 生成信号
signals = engine.generate_signals(stock_data)

# 获取风控报告
risk_reports = engine.assess_risks(positions, market_data)
```
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import logging

import numpy as np

from .alpha_models import (
    AlphaModel, Insight, InsightDirection,
    DualThrustAlpha, RateOfChangeAlpha, MeanReversionAlpha,
    MomentumAlpha, ValueInvestingAlpha, create_alpha_model
)
from .risk_models import (
    RiskModel, RiskReport, RiskDecision,
    MaximumDrawdownRiskModel, StopLossRiskModel, TargetProfitRiskModel,
    CompositeRiskModel, create_risk_model
)
from .portfolio_models import (
    PortfolioConstructionModel, PortfolioTarget, PortfolioResult,
    EqualWeightPortfolio, RiskParityPortfolio, ValueWeightedPortfolio,
    MomentumPortfolio, create_portfolio_model
)
from .indicators import QuantIndicators

# v2.1.0 新增量化工具（可选依赖，按需导入）
logger = logging.getLogger(__name__)

try:
    from .garch_model import GarchForecaster
    HAS_GARCH = True
except ImportError:
    HAS_GARCH = False

try:
    from .factor_analysis import FactorAnalyzer
    HAS_FACTOR = True
except ImportError:
    HAS_FACTOR = False

try:
    from .pairs_trading import PairsTrader
    HAS_PAIRS = True
except ImportError:
    HAS_PAIRS = False

try:
    from .ml_predictor import MLPredictor, FeatureEngineer
    HAS_ML = True
except ImportError:
    HAS_ML = False


@dataclass
class QuantSignal:
    """量化信号"""
    symbol: str
    direction: InsightDirection
    confidence: float
    magnitude: float
    period: int
    model_name: str
    indicators: Dict = field(default_factory=dict)
    risk_report: RiskReport = None
    target_weight: float = 0


@dataclass
class QuantResult:
    """量化分析结果"""
    signals: List[QuantSignal]
    portfolio: PortfolioResult
    risk_reports: List[RiskReport]
    summary: Dict


class QuantitativeEngine:
    """
    量化引擎

    整合信号生成、风险评估、组合构建
    """

    def __init__(self, name: str = ""):
        self.name = name or "QuantitativeEngine"
        self._alpha_models: Dict[str, AlphaModel] = {}
        self._risk_models: Dict[str, RiskModel] = {}
        self._portfolio_model: PortfolioConstructionModel = None
        self._indicators: Dict[str, QuantIndicators] = {}
        self._price_history: Dict[str, List[Dict]] = {}

    def add_alpha_model(self, model_type: str, name: str = "", **kwargs) -> str:
        """
        添加Alpha模型

        Args:
            model_type: 模型类型
            name: 自定义名称
            **kwargs: 模型参数

        Returns:
            str: 模型标识
        """
        model = create_alpha_model(model_type, **kwargs)
        model.name = name or f"{model_type}_{len(self._alpha_models)}"
        self._alpha_models[model.name] = model
        return model.name

    def add_risk_model(self, model_type: str, name: str = "", **kwargs) -> str:
        """
        添加风控模型

        Args:
            model_type: 模型类型
            name: 自定义名称
            **kwargs: 模型参数

        Returns:
            str: 模型标识
        """
        model = create_risk_model(model_type, **kwargs)
        model.name = name or f"{model_type}_{len(self._risk_models)}"
        self._risk_models[model.name] = model
        return model.name

    def set_portfolio_model(self, model_type: str, **kwargs) -> None:
        """
        设置组合模型

        Args:
            model_type: 模型类型
            **kwargs: 模型参数
        """
        self._portfolio_model = create_portfolio_model(model_type, **kwargs)

    def add_price_data(self, symbol: str, ohlcv: Dict) -> None:
        """
        添加价格数据

        Args:
            symbol: 股票代码
            ohlcv: 包含 open, high, low, close, volume 的字典
        """
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        self._price_history[symbol].append(ohlcv)

        # 保持最近500条数据
        if len(self._price_history[symbol]) > 500:
            self._price_history[symbol] = self._price_history[symbol][-500:]

    def get_indicators(self, symbol: str) -> Optional[QuantIndicators]:
        """获取标的的技术指标计算器"""
        if symbol not in self._indicators:
            self._indicators[symbol] = QuantIndicators()
        return self._indicators.get(symbol)

    def generate_signals(
        self,
        symbols: List[str],
        price_data: Dict[str, Dict],
        fundamentals: Dict[str, Dict] = None
    ) -> List[QuantSignal]:
        """
        生成交易信号

        Args:
            symbols: 股票代码列表
            price_data: 价格数据 {symbol: {'open':, 'high':, 'low':, 'close':, 'volume':}}
            fundamentals: 财务数据 {symbol: {'pe':, 'pb':, 'roe':, 'earnings_growth':}}

        Returns:
            List[QuantSignal]: 信号列表
        """
        fundamentals = fundamentals or {}
        signals = []

        for symbol in symbols:
            data = price_data.get(symbol, {})
            if not data:
                continue

            # 添加价格数据到历史
            self.add_price_data(symbol, data)

            # 更新技术指标
            indicators = self.get_indicators(symbol)
            if indicators:
                indicator_results = indicators.update(data)

            # 获取当前标的历史数据
            history = self._price_history.get(symbol, [])
            if not history:
                continue

            # 用Alpha模型生成信号
            for model_name, model in self._alpha_models.items():
                try:
                    # 根据模型类型准备数据
                    if isinstance(model, ValueInvestingAlpha):
                        # 价值投资模型需要财务数据
                        fundamental = fundamentals.get(symbol, {})
                        if fundamental:
                            insight = model.update(symbol, {**data, **fundamental})
                        else:
                            insight = None
                    else:
                        # 其他模型使用价格数据
                        insight = model.update(symbol, data)

                    if insight and insight.direction != InsightDirection.FLAT:
                        # 获取指标结果（get_summary() 返回普通嵌套 dict）
                        ind_result = {}
                        if indicators:
                            ind_result = indicators.get_summary()

                        signals.append(QuantSignal(
                            symbol=symbol,
                            direction=insight.direction,
                            confidence=insight.confidence,
                            magnitude=insight.magnitude,
                            period=insight.period,
                            model_name=model_name,
                            indicators=ind_result
                        ))

                except Exception as e:
                    print(f"Error generating signal for {symbol} with model {model_name}: {e}")
                    continue

        return signals

    def assess_risks(
        self,
        positions: Dict[str, Dict],
        market_data: Dict[str, Dict]
    ) -> List[RiskReport]:
        """
        评估风险

        Args:
            positions: 持仓 {symbol: {'quantity': n, 'avg_price': p}}
            market_data: 市场数据 {symbol: {'price': current_price}}

        Returns:
            List[RiskReport]: 风控报告列表
        """
        reports = []

        for symbol, position in positions.items():
            mkt = market_data.get(symbol, {})
            if not mkt:
                continue

            for model_name, model in self._risk_models.items():
                try:
                    report = model.assess(symbol, position, mkt)
                    reports.append(report)
                except Exception as e:
                    print(f"Error assessing risk for {symbol}: {e}")

        return reports

    def construct_portfolio(
        self,
        signals: List[QuantSignal],
        current_positions: Dict[str, Dict],
        total_value: float,
        price_map: Dict[str, float]
    ) -> PortfolioResult:
        """
        构建组合

        Args:
            signals: 信号列表
            current_positions: 当前持仓
            total_value: 总价值
            price_map: 价格映射

        Returns:
            PortfolioResult: 组合结果
        """
        if self._portfolio_model is None:
            self._portfolio_model = EqualWeightPortfolio()

        # 将QuantSignal转换为Insight
        insights = [
            Insight(
                symbol=s.symbol,
                direction=s.direction,
                confidence=s.confidence,
                magnitude=s.magnitude,
                period=s.period,
                model_name=s.model_name
            )
            for s in signals
        ]

        return self._portfolio_model.construct(
            insights, current_positions, total_value, price_map
        )

    def run(
        self,
        symbols: List[str],
        price_data: Dict[str, Dict],
        positions: Dict[str, Dict],
        fundamentals: Dict[str, Dict] = None,
        total_value: float = 1000000
    ) -> QuantResult:
        """
        运行完整量化流程

        Args:
            symbols: 股票代码列表
            price_data: 价格数据
            positions: 当前持仓
            fundamentals: 财务数据
            total_value: 总资金

        Returns:
            QuantResult: 量化结果
        """
        fundamentals = fundamentals or {}

        # 1. 生成信号
        signals = self.generate_signals(symbols, price_data, fundamentals)

        # 2. 评估风险（RiskModel.assess 期望 {'price': ...} dict，不能传裸 float）
        price_map = {symbol: data.get('close', 0) for symbol, data in price_data.items()}
        market_data = {symbol: {'price': p} for symbol, p in price_map.items()}
        risk_reports = self.assess_risks(positions, market_data)

        # 3. 构建组合
        portfolio = self.construct_portfolio(signals, positions, total_value, price_map)

        # 4. 汇总结果
        summary = self._generate_summary(signals, portfolio, risk_reports)

        return QuantResult(
            signals=signals,
            portfolio=portfolio,
            risk_reports=risk_reports,
            summary=summary
        )

    def _generate_summary(
        self,
        signals: List[QuantSignal],
        portfolio: PortfolioResult,
        risk_reports: List[RiskReport]
    ) -> Dict:
        """生成分析摘要"""
        buy_signals = [s for s in signals if s.direction == InsightDirection.UP]
        sell_signals = [s for s in signals if s.direction == InsightDirection.DOWN]

        avg_confidence = sum(s.confidence for s in buy_signals) / len(buy_signals) if buy_signals else 0

        # 风控汇总
        risk_alerts = [r for r in risk_reports if r.decision != RiskDecision.NONE]
        exit_alerts = [r for r in risk_reports if r.decision == RiskDecision.EXIT]

        return {
            'total_signals': len(signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'avg_confidence': avg_confidence,
            'portfolio_targets': len(portfolio.targets),
            'risk_alerts': len(risk_alerts),
            'exit_alerts': len(exit_alerts),
            'top_signals': sorted(buy_signals, key=lambda x: x.confidence, reverse=True)[:5]
        }


class AShareQuantEngine:
    """
    A股专用量化引擎

    针对A股市场优化的量化策略
    """

    def __init__(self):
        self._engine = QuantitativeEngine()
        self._setup_defaults()

    def _setup_defaults(self):
        """设置默认配置"""
        # 添加多个Alpha模型
        self._engine.add_alpha_model('dual_thrust', k1=0.6, k2=0.6, period=20)
        self._engine.add_alpha_model('momentum', fast_period=5, slow_period=20)
        self._engine.add_alpha_model('mean_reversion', period=20, std_threshold=2.0)

        # 添加风控
        self._engine.add_risk_model('stop_loss', stop_loss_pct=0.07, trailing_pct=0.05)
        self._engine.add_risk_model('max_drawdown', max_drawdown=0.15)

        # 设置组合
        self._engine.set_portfolio_model('equal', max_positions=10)

    def analyze_stock(
        self,
        symbol: str,
        price_history: List[Dict],
        fundamentals: Dict = None
    ) -> Dict:
        """
        分析单只股票

        Args:
            symbol: 股票代码
            price_history: 历史价格数据列表
            fundamentals: 财务数据

        Returns:
            Dict: 分析结果
        """
        if not price_history:
            return {}

        # 逐根喂入历史K线，让Alpha模型积累足够窗口；
        # 保留最后一根K线产生的信号作为当前建议
        fundamentals = fundamentals or {}
        fund_map = {symbol: fundamentals} if fundamentals else None
        signals = []
        for bar in price_history[-30:]:
            signals = self._engine.generate_signals([symbol], {symbol: bar}, fund_map)

        # 获取最新指标
        indicators = self._engine.get_indicators(symbol)
        indicator_summary = indicators.get_summary() if indicators else {}

        # 获取最新价格
        latest = price_history[-1]
        current_price = latest.get('close', 0)

        return {
            'symbol': symbol,
            'current_price': current_price,
            'signals': [
                {
                    'direction': 'UP' if s.direction == InsightDirection.UP else 'DOWN',
                    'confidence': s.confidence,
                    'magnitude': s.magnitude,
                    'period': s.period,
                    'model': s.model_name
                }
                for s in signals
            ],
            'indicators': indicator_summary,
            'recommendation': self._get_recommendation(signals, indicator_summary)
        }

    def _get_recommendation(self, signals: List[QuantSignal], indicators: Dict) -> str:
        """生成投资建议（方向感知：看多/看空信号按置信度加权对决）"""
        if not signals:
            return "观望"

        up_conf = sum(s.confidence for s in signals if s.direction == InsightDirection.UP)
        down_conf = sum(s.confidence for s in signals if s.direction != InsightDirection.UP)
        net = up_conf - down_conf
        total = up_conf + down_conf

        if net > 0:
            if up_conf >= 1.4 and net / total > 0.5:
                return "强烈买入"
            return "适量买入" if net / total > 0.2 else "谨慎乐观"
        elif net < 0:
            if down_conf >= 1.4 and abs(net) / total > 0.5:
                return "强烈卖出"
            return "适量减仓" if abs(net) / total > 0.2 else "谨慎观望"
        return "观望"

    # ── v2.1.0 新增：波动率分析 ──────────────────────────

    def analyze_volatility(
        self,
        symbol: str,
        prices: List[float],
        horizon: int = 5,
    ) -> Optional[Dict]:
        """
        GARCH 波动率预测

        Args:
            symbol: 股票代码
            prices: 历史收盘价序列（至少50个）
            horizon: 预测天数

        Returns:
            Dict: 波动率分析结果，arch 库未安装时返回 None
        """
        if not HAS_GARCH or len(prices) < 50:
            return None

        try:
            forecaster = GarchForecaster(auto_select=True)
            result = forecaster.forecast(prices, horizon=horizon)

            # 波动率状态分析
            regime = forecaster.analyze_volatility_regime(prices)

            return {
                "symbol": symbol,
                "model": result.model_type,
                "aic": result.aic,
                "bic": result.bic,
                "current_annual_vol": result.current_vol,
                "forecast_annual_vol": result.forecast_annual_vol,
                "long_run_vol": result.long_run_vol,
                "half_life_days": result.half_life,
                "forecast_daily_vols": result.forecast_vol,
                "convergence": result.convergence_ok,
                "volatility_regime": regime.get("regime", "未知"),
                "regime_percentile": regime.get("percentile", 50),
                "regime_suggestion": regime.get("suggestion", ""),
            }
        except Exception as e:
            logger.warning(f"GARCH analysis failed for {symbol}: {e}")
            return None

    # ── v2.1.0 新增：因子分析 ────────────────────────────

    def analyze_factors(
        self,
        stocks: List[Dict],
        factor_weights: Dict[str, float] = None,
    ) -> Optional[Dict]:
        """
        多因子分析

        Args:
            stocks: 股票数据列表 [{"symbol": "600519", "pe": 30, ...}, ...]
            factor_weights: 因子权重（None 使用默认）

        Returns:
            Dict: 因子分析结果
        """
        if not HAS_FACTOR:
            return None

        try:
            analyzer = FactorAnalyzer(factor_weights=factor_weights)
            reports = analyzer.score_stocks(stocks)
            exposure = analyzer.get_factor_exposure_report(reports)

            top_stocks = analyzer.get_top_stocks(reports, n=10)

            return {
                "total_stocks": len(stocks),
                "top_10": [
                    {
                        "symbol": r.symbol,
                        "name": r.name,
                        "score": r.composite_score,
                        "percentile": r.percentile_rank,
                        "recommendation": r.recommendation,
                        "top_factors": sorted(
                            r.factors.items(),
                            key=lambda x: x[1].score * x[1].weight,
                            reverse=True,
                        )[:3],
                    }
                    for r in top_stocks
                ],
                "factor_exposure": exposure,
                "factor_weights": analyzer.factor_weights,
            }
        except Exception as e:
            logger.warning(f"Factor analysis failed: {e}")
            return None

    # ── v2.1.0 新增：配对交易分析 ────────────────────────

    def analyze_pairs(
        self,
        stock_pool: List[Dict],
        sector: str = None,
        max_pairs: int = 10,
    ) -> Optional[Dict]:
        """
        配对交易分析

        Args:
            stock_pool: 股票池 [{"symbol": "600036", "prices": [...], "name": "...", "sector": "银行"}, ...]
            sector: 行业限定
            max_pairs: 最大配对数量

        Returns:
            Dict: 配对分析结果
        """
        if not HAS_PAIRS:
            return None

        try:
            trader = PairsTrader()
            pairs = trader.find_pairs(stock_pool, sector=sector, max_pairs=max_pairs)

            if not pairs:
                return {"message": "未找到符合条件的协整配对", "pairs": []}

            return {
                "total_pairs": len(pairs),
                "pairs": [
                    {
                        "stock_a": p.stock_a,
                        "stock_b": p.stock_b,
                        "name_a": p.name_a,
                        "name_b": p.name_b,
                        "correlation": p.correlation,
                        "coint_pvalue": p.coint_pvalue,
                        "hedge_ratio": p.hedge_ratio,
                        "half_life_days": p.half_life,
                        "z_score": p.z_score,
                        "spread_mean": p.spread_mean,
                        "spread_std": p.spread_std,
                        "current_spread": p.current_spread,
                        "signal": p.signal,
                    }
                    for p in pairs
                ],
            }
        except Exception as e:
            logger.warning(f"Pairs analysis failed: {e}")
            return None

    # ── v2.1.0 新增：ML涨跌方向预测 ──────────────────────

    def predict_ml(
        self,
        symbol: str,
        ohlcv_history: List[Dict],
        money_flow: Dict = None,
    ) -> Optional[Dict]:
        """
        ML 涨跌方向预测

        注意：需要先训练模型或加载预训练模型。
        此方法仅做特征提取和方向预测，不包含训练逻辑。

        Args:
            symbol: 股票代码
            ohlcv_history: OHLCV 历史数据
            money_flow: 资金流向数据

        Returns:
            Dict: ML 预测结果，或 None（sklearn 未安装或模型未训练）
        """
        if not HAS_ML:
            return None

        try:
            # 提取特征
            features = FeatureEngineer.extract_features(ohlcv_history, money_flow)
            if not features:
                return {"symbol": symbol, "error": "特征提取失败，数据不足"}

            # 返回特征摘要（实际预测需要训练好的模型）
            return {
                "symbol": symbol,
                "features_count": len(features),
                "key_features": {
                    "rsi_14": features.get("rsi_14", 0),
                    "macd_hist": features.get("macd_hist", 0),
                    "ma20_dev": features.get("ma20_dev", 0),
                    "ret_5d": features.get("ret_5d", 0),
                    "ret_20d": features.get("ret_20d", 0),
                    "vol_20d": features.get("vol_20d", 0),
                    "bb_position": features.get("bb_position", 0.5),
                    "vol_ratio_5": features.get("vol_ratio_5", 1),
                },
                "note": "ML 模型需训练后使用。调用 run_ml_pipeline() 进行完整训练+预测。",
            }
        except Exception as e:
            logger.warning(f"ML prediction failed for {symbol}: {e}")
            return None

    def run_ml_pipeline(
        self,
        stock_pool: List[Dict],
        prediction_horizon: int = 5,
    ) -> Optional[Dict]:
        """
        完整 ML 流水线：特征提取 → 训练 → 预测

        Args:
            stock_pool: 股票池 [{"symbol": "...", "ohlcv": [...], "money_flow": {...}}, ...]
            prediction_horizon: 预测天数

        Returns:
            Dict: ML 训练和预测结果
        """
        if not HAS_ML:
            return None

        try:
            # 1. 特征提取（滑动窗口）+ 标签（每只股票用自身时序价格的未来收益，
            #    按日期对齐：第 i 天特征 ↔ 第 i 天的未来 N 日方向标签。
            #    修复：不再把多只股票的价格横截面列表当时序打标签）
            features_list = []
            labels_list = []
            latest_features = None
            predictor = MLPredictor(prediction_horizon=prediction_horizon)

            for stock in stock_pool:
                ohlcv = stock.get("ohlcv", [])
                if len(ohlcv) < 60:
                    continue

                mf = stock.get("money_flow", None)
                closes = [d.get("close", 0) for d in ohlcv]
                # 该股自身时序标签（尾部 horizon 天无未来数据，prepare_labels 已截断）
                stock_labels = predictor.prepare_labels(closes, prediction_horizon)

                # 滑动窗口特征：第 i 天用截至当日的 60 根窗口，标签同日复用
                for i in range(59, len(ohlcv) - prediction_horizon):
                    features = FeatureEngineer.extract_features(ohlcv[i - 59: i + 1], mf)
                    if features:
                        features_list.append(features)
                        labels_list.append(int(stock_labels[i]))

                # 最新一天的特征（仅用于预测，不参与训练）
                latest_features = FeatureEngineer.extract_features(ohlcv[-60:], mf) or latest_features

            if len(features_list) < 100:
                return {"error": f"样本不足（需要 ≥100，当前 {len(features_list)}）"}

            # 2. 标签数组
            labels = np.array(labels_list, dtype=int)

            # 3. 训练
            train_result = predictor.train(features_list, labels)
            if train_result.get("accuracy", 0) < 0.5:
                return {
                    "error": "模型准确率过低 (<50%)，数据可能不适合 ML 预测",
                    "accuracy": train_result["accuracy"],
                }

            # 4. 用最新一天的特征做预测
            if latest_features:
                latest_pred = predictor.predict(latest_features)

                return {
                    "accuracy": train_result["accuracy"],
                    "train_samples": train_result["train_samples"],
                    "top_features": train_result["top_features"],
                    "latest_prediction": {
                        "direction": latest_pred.direction,
                        "prob_up": latest_pred.prob_up,
                        "prob_down": latest_pred.prob_down,
                        "confidence": latest_pred.confidence,
                    },
                    "horizon_days": prediction_horizon,
                    "model_type": predictor.model_type,
                }

            return train_result

        except Exception as e:
            logger.warning(f"ML pipeline failed: {e}")
            return None


def create_quant_engine(engine_type: str = "default") -> QuantitativeEngine:
    """
    工厂函数：创建量化引擎

    Args:
        engine_type: 引擎类型
            - 'default': 默认引擎
            - 'ashare': A股专用引擎

    Returns:
        QuantitativeEngine: 量化引擎实例
    """
    if engine_type == "ashare":
        return AShareQuantEngine()
    return QuantitativeEngine()


# ============================================================
# v3.1.0 增量 — 信号融合 + 显著性检验
# ============================================================

def fuse_signals(signals, weights=None, min_agree=2):
    """多信号融合 — 加权投票 + 最少一致信号数门限。

    Args:
        signals: [{model, direction(UP/DOWN), confidence, magnitude}, ...]
        weights: 与 signals 等长的权重列表，None 等权
        min_agree: 至少多少个信号同向才发出建议

    Returns:
        dict: signal, agreement, confidence, weighted_score
    """
    if not signals:
        return {'signal': '无信号', 'agreement': 0, 'confidence': 0,
                'weighted_score': 0.0}
    if weights is None:
        weights = [1.0] * len(signals)
    up_score = sum(w * s.get('magnitude', 0) * s.get('confidence', 0.5)
                   for w, s in zip(weights, signals) if s.get('direction') == 'UP')
    down_score = sum(w * s.get('magnitude', 0) * s.get('confidence', 0.5)
                     for w, s in zip(weights, signals) if s.get('direction') == 'DOWN')
    n_up = sum(1 for s in signals if s.get('direction') == 'UP')
    n_down = sum(1 for s in signals if s.get('direction') == 'DOWN')
    if up_score > down_score and n_up >= min_agree:
        out_signal = 'BUY'
    elif down_score > up_score and n_down >= min_agree:
        out_signal = 'SELL'
    else:
        out_signal = 'HOLD'
    total_score = up_score + down_score
    return {
        'signal': out_signal,
        'agreement': max(n_up, n_down),
        'total_signals': len(signals),
        'confidence': round(float(max(up_score, down_score) / total_score), 4)
                      if total_score > 0 else 0,
        'weighted_score': round(float(up_score - down_score), 4),
        'up_score': round(float(up_score), 4),
        'down_score': round(float(down_score), 4),
    }


def permutation_significance(scores, labels, n_perm=500, seed=42):
    """置换检验 — 评估信号得分与未来收益是否有显著相关性。

    Returns:
        dict: observed, p_value, is_significant, threshold
    """
    import math
    import numpy as _np
    rng = _np.random.default_rng(seed)
    s = _np.array(scores, dtype=float)
    y = _np.array(labels, dtype=float)
    n = min(len(s), len(y))
    s, y = s[:n], y[:n]
    if n < 30:
        return {'observed': 0.0, 'p_value': None,
                'is_significant': False, 'error': '样本不足'}
    observed = float(_np.corrcoef(s, y)[0, 1])
    null_dist = []
    for _ in range(n_perm):
        ys = rng.permutation(y)
        null_dist.append(float(_np.corrcoef(s, ys)[0, 1]))
    null_dist = _np.array(null_dist)
    p_value = float((_np.sum(_np.abs(null_dist) >= _np.abs(observed)) + 1) /
                    (n_perm + 1))
    return {
        'observed': round(observed, 4),
        'p_value': round(p_value, 4),
        'is_significant': bool(p_value < 0.05),
        'threshold': round(float(_np.percentile(_np.abs(null_dist), 95)), 4),
    }


# ============================================================
# v5.0 增量 - 价值投资 + 技术信号融合
# ============================================================

def fuse_value_signals(value_signals, technical_signals,
                       value_weight=0.6, technical_weight=0.4,
                       period_days=20):
    """
    价值投资信号与技术信号加权融合（v5.0 新增）。

    长周期（>=20d）价值权重高（0.6）；短周期价值权重低（0.4）。

    Args:
        value_signals: [{direction(UP/DOWN/FLAT), score(0-100), module}, ...]
                       来自 value_investing 模块（moat/health/dcf/management/industry）
        technical_signals: [{direction(UP/DOWN/FLAT), confidence, magnitude, model}, ...]
                           来自 alpha_models
        value_weight / technical_weight: 权重（自动归一化）
        period_days: 投资周期（天），用于自动调整权重

    Returns:
        dict: {signal, value_score, technical_score, fused_score, agreement, details}
    """
    # 根据周期自动调整权重
    if period_days >= 20:
        # 长周期：价值占主导
        vw, tw = 0.6, 0.4
    else:
        # 短周期：技术占主导
        vw, tw = 0.4, 0.6
    # 用户显式传入的权重优先（非默认值时）
    if value_weight != 0.6 or technical_weight != 0.4:
        vw, tw = value_weight, technical_weight
    # 归一化
    total_w = vw + tw
    vw, tw = vw / total_w, tw / total_w

    # 价值信号评分（0-100 -> -100 ~ +100）
    value_score = 0
    value_count = 0
    value_directions = []
    for s in (value_signals or []):
        score = s.get('score', 50)
        if score > 0:
            # score > 65 看多, < 35 看空, 中间中性
            direction = 1 if score >= 65 else (-1 if score < 35 else 0)
            value_score += direction * abs(score - 50) * 2  # 转换到 -100 ~ +100
            value_directions.append(direction)
            value_count += 1
    value_score = value_score / max(value_count, 1) if value_count > 0 else 0
    value_agreement = 1 - abs(sum(value_directions)) / max(len(value_directions), 1) if value_directions else 0

    # 技术信号评分
    tech_score = 0
    tech_count = 0
    tech_directions = []
    for s in (technical_signals or []):
        direction = s.get('direction', 'FLAT')
        confidence = s.get('confidence', 0.5)
        magnitude = s.get('magnitude', 0)
        if direction == 'UP':
            d = 1
            tech_score += confidence * magnitude
        elif direction == 'DOWN':
            d = -1
            tech_score -= confidence * magnitude
        else:
            d = 0
        tech_directions.append(d)
        tech_count += 1
    # 技术分数缩放到 -100 ~ +100
    tech_score = max(-100, min(100, tech_score / max(tech_count, 1) * 5)) if tech_count > 0 else 0
    tech_agreement = 1 - abs(sum(tech_directions)) / max(len(tech_directions), 1) if tech_directions else 0

    # 融合
    fused_score = value_score * vw + tech_score * tw
    fused_score = max(-100, min(100, fused_score))

    # 方向判定
    if fused_score > 30:
        signal = 'BUY'
    elif fused_score < -30:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    # 整体一致性
    all_dirs = value_directions + tech_directions
    agreement = 1 - abs(sum(all_dirs)) / max(len(all_dirs), 1) if all_dirs else 0

    return {
        'signal': signal,
        'value_score': round(value_score, 1),
        'technical_score': round(tech_score, 1),
        'fused_score': round(fused_score, 1),
        'value_weight': round(vw, 2),
        'technical_weight': round(tw, 2),
        'agreement': round(agreement, 2),
        'value_signals_count': value_count,
        'technical_signals_count': tech_count,
        'period_days': period_days,
    }
