# -*- coding: utf-8 -*-
"""场景模拟器（scenario_simulator.py，v7.6 新增）

设计目标：
- 在不同市场状态（牛市/熊市/震荡市/高波动）下分别模拟未来收益分布
- 提供概率化的预测（而非点估计），输出期望收益 + VaR + CVaR + 胜率
- 多场景概率加权合成（Stacking 风格）
- 蒙特卡洛模拟（GBM + 跳跃扩散 + 异方差）

使用示例：
    from quantitative.scenario_simulator import quick_scenario_forecast

    # 基于历史价格 + 当前因子分做场景预测
    result = quick_scenario_forecast(
        prices=[...],  # 历史收盘价
        current_score=72,  # 当前综合分 0-100
        horizon_days=20,  # 预测 20 个交易日
        n_simulations=2000,  # 蒙特卡洛次数
    )
    print(result['expected_return'], result['var_95'], result['bull_probability'])
"""
from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    """场景模拟结果。"""
    expected_return: float          # 期望收益（区间中位数）
    probability_bullish: float      # 看涨概率（>0% 收益）
    probability_bearish: float      # 看跌概率（<0% 收益）
    var_95: float                   # 95% VaR（损失阈值）
    cvar_95: float                  # 95% CVaR（条件损失均值）
    max_gain: float                 # 模拟中最大收益
    max_loss: float                 # 模拟中最大损失
    scenarios: Dict[str, float] = field(default_factory=dict)  # 各场景期望收益
    confidence: float = 0.0          # 综合置信度
    horizon_days: int = 20           # 预测周期
    metadata: Dict = field(default_factory=dict)


# ============================================================================
# 1. 场景生成器
# ============================================================================


def detect_market_regime_from_history(prices: list, window: int = 60) -> str:
    """根据历史价格自动判定市场状态。

    判定规则：
    - 60 日涨幅 > 15% + 波动率 < 35% → 牛市
    - 60 日跌幅 > 15% + 波动率 > 30% → 熊市
    - 波动率 > 40% → 高波动震荡
    - 其他 → 震荡市
    """
    if not prices or len(prices) < window + 1:
        return "震荡市"

    ret_60d = (prices[-1] - prices[-window]) / prices[-window]
    # 计算波动率
    returns = [(prices[i] - prices[i - 1]) / prices[i - 1]
               for i in range(1, len(prices))]
    recent_returns = returns[-window:]
    if not recent_returns:
        return "震荡市"
    mean_ret = sum(recent_returns) / len(recent_returns)
    var_ret = sum((r - mean_ret) ** 2 for r in recent_returns) / len(recent_returns)
    vol_annual = math.sqrt(var_ret) * math.sqrt(252)

    if ret_60d > 0.15 and vol_annual < 0.35:
        return "牛市"
    elif ret_60d <= -0.15:
        return "熊市"  # 单边大跌（波动率可低）
    elif vol_annual > 0.40:
        return "高波动"
    else:
        return "震荡市"


def _gbm_params(prices: list, window: int = 60) -> Tuple[float, float]:
    """计算几何布朗运动参数（μ, σ）。"""
    if len(prices) < window + 1:
        return 0.0, 0.20
    recent = prices[-window:]
    returns = [(recent[i] - recent[i - 1]) / recent[i - 1] for i in range(1, len(recent))]
    if not returns:
        return 0.0, 0.20
    mu = sum(returns) / len(returns)
    var = sum((r - mu) ** 2 for r in returns) / len(returns)
    sigma = math.sqrt(var)
    return mu, sigma


def _std_normal(rng) -> float:
    """Box-Muller 标准正态。"""
    u1 = rng.random()
    u2 = rng.random()
    if u1 <= 0:
        u1 = 1e-12
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


def _simulate_std_t(rng, dof: int) -> float:
    """v8.0: 标准化 Student-t 分布（N(0,1)/sqrt(chi2/dof)），比正态更厚尾。"""
    z = _std_normal(rng)
    chi2 = sum(_std_normal(rng) ** 2 for _ in range(max(dof, 2)))
    return z / math.sqrt(chi2 / dof) if chi2 > 0 else z


def _simulate_paths(current_price: float,
                    mu: float,
                    sigma: float,
                    horizon_days: int,
                    n_simulations: int,
                    seed: int = 42,
                    distribution: str = "normal",
                    use_jumps: bool = False,
                    lambda_jump: float = 0.05,
                    jump_mean: float = 0.0,
                    jump_vol: float = 0.02,
                    dof: int = 4) -> list:
    """v8.0: 统一蒙特卡洛路径生成（GBM / 肥尾 t / 泊松跳跃扩散）。

    Args:
        distribution: "normal"（标准正态 GBM）或 "t"（Student-t 肥尾）
        use_jumps: 是否启用泊松跳跃（每日 λ 概率叠加跳变）
        lambda_jump: 每日跳跃概率
        jump_mean/jump_vol: 跳跃的对数收益均值/波动
        dof: t 分布自由度（越小越肥尾）
    """
    rng = random.Random(seed)
    returns = []
    for _ in range(n_simulations):
        price = current_price
        for _ in range(horizon_days):
            z = _simulate_std_t(rng, dof) if distribution == "t" else _std_normal(rng)
            drift = mu - 0.5 * sigma ** 2
            log_return = drift + z * sigma
            if use_jumps and rng.random() < lambda_jump:
                log_return += rng.gauss(jump_mean, jump_vol)
            price *= math.exp(log_return)
        returns.append((price - current_price) / current_price)
    return returns


def _simulate_gbm_paths(current_price: float,
                       mu: float,
                       sigma: float,
                       horizon_days: int,
                       n_simulations: int,
                       seed: int = 42) -> list:
    """蒙特卡洛模拟 GBM 价格路径（返回每条路径的最终收益率）。
    v8.0: 复用 _simulate_paths（distribution=normal, use_jumps=False），保持旧行为。"""
    return _simulate_paths(
        current_price, mu, sigma, horizon_days, n_simulations,
        seed=seed, distribution="normal", use_jumps=False,
    )


# ============================================================================
# 2. 场景模拟器
# ============================================================================


class ScenarioSimulator:
    """场景模拟器：在多种市场状态下分别模拟价格路径。

    设计要点：
    - 4 大市场状态：牛市/熊市/震荡市/高波动
    - 每个场景独立蒙特卡洛（GBM）
    - 用当前因子分动态调整各场景概率
    - 概率加权合成最终预测
    """

    # 场景参数（基于历史统计）
    SCENARIO_PARAMS = {
        "牛市":    {"mu": 0.002,  "sigma": 0.015, "prior": 0.30},
        "震荡市":  {"mu": 0.0005, "sigma": 0.012, "prior": 0.45},
        "高波动":  {"mu": 0.000,  "sigma": 0.030, "prior": 0.15},
        "熊市":    {"mu": -0.002, "sigma": 0.018, "prior": 0.10},
    }

    def __init__(self, n_simulations: int = 2000, seed: int = 42,
                 distribution: str = "normal", use_jumps: bool = False,
                 lambda_jump: float = 0.05, jump_mean: float = 0.0,
                 jump_vol: float = 0.02, dof: int = 4):
        # v8.0: 新增分布/跳跃参数（默认 normal/无跳跃 → 与 v7.6 行为一致）
        self.n_simulations = n_simulations
        self.seed = seed
        self.distribution = distribution
        self.use_jumps = use_jumps
        self.lambda_jump = lambda_jump
        self.jump_mean = jump_mean
        self.jump_vol = jump_vol
        self.dof = dof

    def simulate_scenario(self,
                          current_price: float,
                          scenario: str,
                          horizon_days: int = 20) -> list:
        """模拟单个场景的蒙特卡洛路径（v8.0 支持 t 分布 + 跳跃扩散）。"""
        params = self.SCENARIO_PARAMS.get(scenario, self.SCENARIO_PARAMS["震荡市"])
        return _simulate_paths(
            current_price=current_price,
            mu=params["mu"],
            sigma=params["sigma"],
            horizon_days=horizon_days,
            n_simulations=self.n_simulations,
            seed=self.seed + hash(scenario) % 10000,
            distribution=self.distribution,
            use_jumps=self.use_jumps,
            lambda_jump=self.lambda_jump,
            jump_mean=self.jump_mean,
            jump_vol=self.jump_vol,
            dof=self.dof,
        )

    def forecast(self,
                 prices: list,
                 current_score: float = 50.0,
                 horizon_days: int = 20,
                 detected_regime: Optional[str] = None) -> ScenarioResult:
        """综合场景预测。

        Args:
            prices: 历史价格序列（最近 ~120 日）
            current_score: 当前综合评分 0-100（v7.6 EnhancedFactor 综合）
            horizon_days: 预测周期（默认 20 个交易日 ≈ 1 月）
            detected_regime: 已检测的市场状态（None = 自动检测）

        Returns:
            ScenarioResult 场景预测结果
        """
        if not prices:
            return ScenarioResult(
                expected_return=0.0,
                probability_bullish=0.5,
                probability_bearish=0.5,
                var_95=0.0,
                cvar_95=0.0,
                max_gain=0.0,
                max_loss=0.0,
                scenarios={},
                confidence=0.0,
                horizon_days=horizon_days,
            )

        current_price = prices[-1]
        # 自动检测市场状态
        if detected_regime is None:
            detected_regime = detect_market_regime_from_history(prices)

        # 调整先验概率（基于当前评分）
        adjusted_priors = self._adjust_priors(current_score, detected_regime)

        # 各场景独立蒙特卡洛
        scenario_returns: Dict[str, list] = {}
        for scenario in self.SCENARIO_PARAMS.keys():
            scenario_returns[scenario] = self.simulate_scenario(
                current_price, scenario, horizon_days
            )

        # 概率加权期望
        expected_returns_by_scenario = {
            s: sum(returns) / len(returns)
            for s, returns in scenario_returns.items()
        }

        # 合并所有路径，按权重采样
        all_paths = []
        weights_for_paths = []
        for scenario, paths in scenario_returns.items():
            w = adjusted_priors[scenario]
            for p in paths:
                all_paths.append(p)
                weights_for_paths.append(w)

        # 归一化权重
        total_w = sum(weights_for_paths)
        if total_w > 0:
            weights_for_paths = [w / total_w for w in weights_for_paths]

        # 加权统计
        sorted_paths = sorted(all_paths)
        n = len(sorted_paths)
        expected = sum(p * w for p, w in zip(all_paths, weights_for_paths))

        # VaR 95%（5% 分位）
        var_95_idx = max(0, int(n * 0.05) - 1)
        var_95 = sorted_paths[var_95_idx]

        # CVaR 95%（最差 5% 的均值）
        tail = sorted_paths[:max(1, int(n * 0.05))]
        cvar_95 = sum(tail) / len(tail) if tail else 0.0

        # 看涨/看跌概率（加权）
        prob_bull = sum(w for p, w in zip(all_paths, weights_for_paths) if p > 0)
        prob_bear = sum(w for p, w in zip(all_paths, weights_for_paths) if p < 0)

        max_gain = max(all_paths)
        max_loss = min(all_paths)

        # 置信度：基于场景一致性和数据长度
        # 如果牛市/熊市概率都很低（震荡），则置信度较低
        max_scenario_prob = max(adjusted_priors.values())
        data_conf = min(1.0, len(prices) / 120)  # 数据长度因子
        confidence = (0.5 + 0.5 * max_scenario_prob) * data_conf

        return ScenarioResult(
            expected_return=expected,
            probability_bullish=prob_bull,
            probability_bearish=prob_bear,
            var_95=var_95,
            cvar_95=cvar_95,
            max_gain=max_gain,
            max_loss=max_loss,
            scenarios=expected_returns_by_scenario,
            confidence=confidence,
            horizon_days=horizon_days,
            metadata={
                "detected_regime": detected_regime,
                "adjusted_priors": adjusted_priors,
                "n_simulations": self.n_simulations,
                "distribution": self.distribution,
                "use_jumps": self.use_jumps,
            },
        )

    def _adjust_priors(self, current_score: float, detected_regime: str) -> Dict[str, float]:
        """根据当前评分 + 市场状态调整各场景先验概率。"""
        # 基础先验
        priors = {s: p["prior"] for s, p in self.SCENARIO_PARAMS.items()}

        # 用评分调整：score > 60 偏向牛市，< 40 偏向熊市
        score_bias = (current_score - 50) / 50  # [-1, +1]

        # 牛市/熊市调整
        priors["牛市"] = max(0.05, min(0.70, priors["牛市"] + score_bias * 0.30))
        priors["熊市"] = max(0.05, min(0.70, priors["熊市"] - score_bias * 0.25))

        # 检测到的市场状态微调
        if detected_regime == "牛市":
            priors["牛市"] += 0.10
        elif detected_regime == "熊市":
            priors["熊市"] += 0.10
        elif detected_regime == "高波动":
            priors["高波动"] += 0.10
        elif detected_regime == "震荡市":
            priors["震荡市"] += 0.10

        # 归一化
        total = sum(priors.values())
        if total > 0:
            priors = {k: v / total for k, v in priors.items()}
        return priors


# ============================================================================
# 3. 便捷函数
# ============================================================================


def quick_scenario_forecast(prices: list,
                            current_score: float = 50.0,
                            horizon_days: int = 20,
                            n_simulations: int = 2000,
                            detected_regime: Optional[str] = None,
                            distribution: str = "normal",
                            use_jumps: bool = False,
                            lambda_jump: float = 0.05,
                            jump_mean: float = 0.0,
                            jump_vol: float = 0.02,
                            dof: int = 4) -> Dict:
    """快速场景预测（返回 dict 而非 ScenarioResult）。

    Args:
        prices: 历史价格序列
        current_score: 当前综合评分 0-100
        horizon_days: 预测周期（默认 20 = 1 月）
        n_simulations: 蒙特卡洛次数
        detected_regime: 已检测的市场状态
        distribution: v8.0 "normal"（GBM）或 "t"（Student-t 肥尾）
        use_jumps: v8.0 是否启用泊松跳跃扩散
        lambda_jump/jump_mean/jump_vol/dof: 跳跃与 t 分布参数（默认与旧行为一致）

    Returns:
        {
            'expected_return': 期望收益,
            'probability_bullish': 看涨概率,
            'probability_bearish': 看跌概率,
            'var_95': 95% VaR,
            'cvar_95': 95% CVaR,
            'max_gain': 最大收益,
            'max_loss': 最大损失,
            'scenarios': {scenario: 期望收益},
            'confidence': 置信度,
            'horizon_days': 预测周期,
            'detected_regime': 检测到的市场状态,
        }
    """
    simulator = ScenarioSimulator(n_simulations=n_simulations,
                                  distribution=distribution,
                                  use_jumps=use_jumps,
                                  lambda_jump=lambda_jump,
                                  jump_mean=jump_mean,
                                  jump_vol=jump_vol,
                                  dof=dof)
    result = simulator.forecast(
        prices=prices,
        current_score=current_score,
        horizon_days=horizon_days,
        detected_regime=detected_regime,
    )
    return {
        "expected_return": round(result.expected_return, 4),
        "probability_bullish": round(result.probability_bullish, 3),
        "probability_bearish": round(result.probability_bearish, 3),
        "var_95": round(result.var_95, 4),
        "cvar_95": round(result.cvar_95, 4),
        "max_gain": round(result.max_gain, 4),
        "max_loss": round(result.max_loss, 4),
        "scenarios": {k: round(v, 4) for k, v in result.scenarios.items()},
        "confidence": round(result.confidence, 3),
        "horizon_days": result.horizon_days,
        "detected_regime": result.metadata.get("detected_regime", "unknown"),
    }


# ============================================================================
# CLI 演示
# ============================================================================


if __name__ == "__main__":
    import json
    # 生成模拟数据：60 日上涨趋势
    demo_prices = [100 + i * 0.3 + (i % 5) * 0.5 for i in range(80)]
    result = quick_scenario_forecast(
        prices=demo_prices,
        current_score=72,  # 较强评分
        horizon_days=20,
        n_simulations=2000,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))