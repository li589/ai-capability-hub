# -*- coding: utf-8 -*-
"""
配对交易策略
Pairs Trading Strategy

基于协整检验的统计套利策略。在 A 股市场中寻找
具有长期均衡关系的股票对，进行价差交易。

策略流程：
1. 候选配对筛选（同行业 + 高相关性）
2. 协整检验（Engle-Granger / Johansen）
3. 价差建模（均值 + 标准差）
4. 交易信号生成（偏离阈值触发）
5. 动态止损（价差突破历史极值）

使用示例：
```python
from quantitative.pairs_trading import PairsTrader

trader = PairsTrader()
pairs = trader.find_pairs(stock_data, sector="银行")
signals = trader.generate_signals(pairs)
```
"""

import math
import warnings
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np

# coint / adfuller 分开导入：statsmodels 部分可用时回退路径仍能工作
try:
    from statsmodels.tsa.stattools import coint
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from statsmodels.tsa.stattools import adfuller
    HAS_ADFULLER = True
except ImportError:
    HAS_ADFULLER = False


@dataclass
class PairResult:
    """配对关系"""
    stock_a: str          # 股票A代码
    stock_b: str          # 股票B代码
    name_a: str = ""      # 股票A名称
    name_b: str = ""      # 股票B名称
    correlation: float = 0       # Pearson 相关系数
    coint_pvalue: float = 1.0    # 协整检验 p-value
    hedge_ratio: float = 1.0     # 对冲比率 (B 对 A)
    half_life: float = 0         # 价差均值回归半衰期（天）
    spread_mean: float = 0       # 价差均值
    spread_std: float = 0        # 价差标准差
    current_spread: float = 0    # 当前价差
    z_score: float = 0           # 当前 Z-Score
    signal: str = "无信号"       # 交易信号


class PairsTrader:
    """
    配对交易策略

    寻找协整股票对，生成统计套利信号。

    参数：
    - min_correlation: 最小相关系数阈值
    - coint_significance: 协整显著性水平
    - entry_z: 入场 Z-Score 阈值
    - exit_z: 出场 Z-Score 阈值
    - stop_z: 止损 Z-Score 阈值
    """

    def __init__(
        self,
        min_correlation: float = 0.7,
        coint_significance: float = 0.05,
        entry_z: float = 2.0,
        exit_z: float = 0.5,
        stop_z: float = 3.0,
    ):
        self.min_correlation = min_correlation
        self.coint_significance = coint_significance
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.stop_z = stop_z

    @staticmethod
    def _safe_float(v, default=0.0) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    def calc_correlation(
        self, prices_a: List[float], prices_b: List[float]
    ) -> float:
        """计算 Pearson 相关系数"""
        if len(prices_a) < 20 or len(prices_b) < 20:
            return 0.0
        # 对齐长度
        min_len = min(len(prices_a), len(prices_b))
        a = np.array(prices_a[-min_len:], dtype=float)
        b = np.array(prices_b[-min_len:], dtype=float)
        # 使用对数收益率计算相关性（更稳定）
        ret_a = np.diff(np.log(a))
        ret_b = np.diff(np.log(b))
        if len(ret_a) < 5:
            return 0.0
        corr = np.corrcoef(ret_a, ret_b)[0, 1]
        return corr if not np.isnan(corr) else 0.0

    def calc_half_life(self, spread: np.ndarray) -> float:
        """
        计算价差的均值回归半衰期

        使用 OLS 回归: Δspread_t = α + β * spread_{t-1} + ε_t
        半衰期 = -ln(2) / β
        """
        if len(spread) < 20:
            return float("inf")

        spread_lag = spread[:-1]
        spread_diff = np.diff(spread)

        # OLS 回归
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                X = np.column_stack([np.ones(len(spread_lag)), spread_lag])
                beta = np.linalg.lstsq(X, spread_diff, rcond=None)[0]
                slope = beta[1]

                if slope < 0:
                    half_life = -math.log(2) / slope
                    return min(half_life, 500)  # 上限 500 天
            except Exception:
                pass

        return float("inf")

    def test_cointegration(
        self, prices_a: List[float], prices_b: List[float]
    ) -> Tuple[float, float, bool]:
        """
        Engle-Granger 协整检验

        Returns:
            (p_value, hedge_ratio, is_cointegrated)
        """
        if not HAS_STATSMODELS:
            # 回退：使用简单 OLS + ADF 检验
            return self._simple_coint_test(prices_a, prices_b)

        min_len = min(len(prices_a), len(prices_b))
        a = np.array(prices_a[-min_len:], dtype=float)
        b = np.array(prices_b[-min_len:], dtype=float)

        try:
            # 使用 statsmodels 的 coint 函数
            coint_t, p_value, crit_values = coint(a, b)

            # 计算对冲比率（OLS: A = α + β * B）
            X = np.column_stack([np.ones(len(b)), b])
            beta = np.linalg.lstsq(X, a, rcond=None)[0]
            hedge_ratio = beta[1]

            is_coint = p_value < self.coint_significance

            return p_value, hedge_ratio, is_coint
        except Exception:
            return 1.0, 1.0, False

    def _simple_coint_test(
        self, prices_a: List[float], prices_b: List[float]
    ) -> Tuple[float, float, bool]:
        """简化协整检验（不依赖 statsmodels 的 coint，仍需 adfuller）"""
        min_len = min(len(prices_a), len(prices_b))
        a = np.array(prices_a[-min_len:], dtype=float)
        b = np.array(prices_b[-min_len:], dtype=float)

        # OLS: A = α + β * B
        X = np.column_stack([np.ones(len(b)), b])
        beta = np.linalg.lstsq(X, a, rcond=None)[0]
        hedge_ratio = beta[1]

        if not HAS_ADFULLER:
            # 无 statsmodels：无法做 ADF 检验，保守返回不协整
            return 1.0, hedge_ratio, False

        # 残差 = A - α - β * B
        spread = a - (beta[0] + beta[1] * b)

        # ADF 检验残差平稳性
        try:
            adf_result = adfuller(spread, maxlag=10, autolag="AIC")
            p_value = adf_result[1]
            is_coint = p_value < self.coint_significance
            return p_value, hedge_ratio, is_coint
        except Exception:
            return 1.0, hedge_ratio, False

    def analyze_pair(
        self,
        stock_a: Dict,
        stock_b: Dict,
    ) -> Optional[PairResult]:
        """
        分析单个股票对

        Args:
            stock_a: {"symbol": "600036", "name": "招商银行", "prices": [...]}
            stock_b: {"symbol": "601398", "name": "工商银行", "prices": [...]}

        Returns:
            PairResult: 配对分析结果，不满足条件返回 None
        """
        prices_a = stock_a.get("prices", [])
        prices_b = stock_b.get("prices", [])

        if len(prices_a) < 60 or len(prices_b) < 60:
            return None

        # 1. 相关性筛选
        corr = self.calc_correlation(prices_a, prices_b)
        if corr < self.min_correlation:
            return None

        # 2. 协整检验
        p_value, hedge_ratio, is_coint = self.test_cointegration(prices_a, prices_b)
        if not is_coint:
            return None

        # 3. 价差分析
        min_len = min(len(prices_a), len(prices_b))
        a = np.array(prices_a[-min_len:], dtype=float)
        b = np.array(prices_b[-min_len:], dtype=float)
        spread = a - hedge_ratio * b

        spread_mean = spread.mean()
        spread_std = spread.std()
        current_spread = spread[-1]
        z_score = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0

        # 4. 半衰期
        half_life = self.calc_half_life(spread)

        # 5. 交易信号
        signal = self._generate_signal(z_score)

        return PairResult(
            stock_a=stock_a.get("symbol", ""),
            stock_b=stock_b.get("symbol", ""),
            name_a=stock_a.get("name", ""),
            name_b=stock_b.get("name", ""),
            correlation=round(corr, 4),
            coint_pvalue=round(p_value, 4),
            hedge_ratio=round(hedge_ratio, 4),
            half_life=round(half_life, 1),
            spread_mean=round(spread_mean, 2),
            spread_std=round(spread_std, 2),
            current_spread=round(current_spread, 2),
            z_score=round(z_score, 2),
            signal=signal,
        )

    def _generate_signal(self, z_score: float) -> str:
        """根据 Z-Score 生成交易信号（止损判断必须最优先，
        否则 |Z|>stop_z 会先命中入场分支，把止损变成加仓）"""
        if z_score > self.stop_z or z_score < -self.stop_z:
            return f"止损 (Z={z_score:.2f} 超过 {self.stop_z})"
        elif z_score > self.entry_z:
            return f"做空价差 (Z={z_score:.2f} > {self.entry_z}) — 卖出A买入B"
        elif z_score < -self.entry_z:
            return f"做多价差 (Z={z_score:.2f} < -{self.entry_z}) — 买入A卖出B"
        elif abs(z_score) < self.exit_z:
            return "价差回归 — 平仓观望"
        else:
            return "持有/观望"

    def find_pairs(
        self,
        stock_pool: List[Dict],
        sector: str = None,
        max_pairs: int = 20,
    ) -> List[PairResult]:
        """
        在股票池中寻找配对

        Args:
            stock_pool: 股票池 [{"symbol": "600036", "name": "...", "prices": [...], "sector": "银行"}, ...]
            sector: 限定的行业（None 表示全市场）
            max_pairs: 最大配对数量

        Returns:
            List[PairResult]: 配对结果列表（按协整显著性排序）
        """
        # 按行业分组
        if sector:
            candidates = [s for s in stock_pool if s.get("sector") == sector]
        else:
            candidates = stock_pool

        if len(candidates) < 2:
            return []

        results = []

        # 遍历所有可能的配对
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                result = self.analyze_pair(candidates[i], candidates[j])
                if result:
                    results.append(result)

                # 提前终止
                if len(results) >= max_pairs:
                    break
            if len(results) >= max_pairs:
                break

        # 按协整显著性排序
        results.sort(key=lambda x: x.coint_pvalue)

        return results[:max_pairs]

    def generate_report(self, pair: PairResult) -> str:
        """生成配对分析报告（Markdown）"""
        lines = [
            f"## 配对交易分析: {pair.name_a}({pair.stock_a}) ↔ {pair.name_b}({pair.stock_b})",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 相关系数 | {pair.correlation:.4f} |",
            f"| 协整 p-value | {pair.coint_pvalue:.4f} {'✅ 显著' if pair.coint_pvalue < 0.05 else '⚠️ 不显著'} |",
            f"| 对冲比率 | 1 : {pair.hedge_ratio:.4f} (B对A) |",
            f"| 价差均值 | {pair.spread_mean:.2f} |",
            f"| 价差标准差 | {pair.spread_std:.2f} |",
            f"| 当前价差 | {pair.current_spread:.2f} |",
            f"| Z-Score | {pair.z_score:.2f} |",
            f"| 半衰期 | {pair.half_life:.1f} 天 |",
            f"| **交易信号** | **{pair.signal}** |",
            f"",
            f"### 操作指南",
            f"",
            f"- 入场阈值: ±{self.entry_z}σ",
            f"- 出场阈值: ±{self.exit_z}σ",
            f"- 止损阈值: ±{self.stop_z}σ",
            f"",
        ]

        # 交易规则说明
        z = pair.z_score
        if z > self.entry_z:
            lines.append(
                f"当前 Z={z:.2f} > {self.entry_z}，价差偏高。"
                f"**建议**: 做空价差（卖出 {pair.name_a}，买入 {pair.name_b}），"
                f"等待价差回归均值后平仓。"
            )
        elif z < -self.entry_z:
            lines.append(
                f"当前 Z={z:.2f} < -{self.entry_z}，价差偏低。"
                f"**建议**: 做多价差（买入 {pair.name_a}，卖出 {pair.name_b}），"
                f"等待价差回归均值后平仓。"
            )
        else:
            lines.append(
                f"当前 Z={z:.2f} 在 ±{self.entry_z} 之间，无交易信号。"
                f"等待价差突破阈值后入场。"
            )

        return "\n".join(lines)


# ============================================================
# v3.1.0 增量 — Johansen 协整检验 / 半衰期筛选 / Z-Score 信号
# ============================================================

def johansen_test(prices_a, prices_b, det_order=0, maxlag=1):
    """Johansen 协整检验（基于 statsmodels）。

    Returns:
        dict: trace_stat, trace_cv_5pct, is_coint, hedge_ratio, eigenvalues
    """
    import numpy as _np
    a = _np.array(prices_a, dtype=float)
    b = _np.array(prices_b, dtype=float)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    if n < 60:
        return {'trace_stat': None, 'trace_cv_5pct': None,
                'is_coint': False, 'hedge_ratio': None, 'eigenvalues': [],
                'error': '样本不足'}
    try:
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
    except ImportError:
        return {'trace_stat': None, 'is_coint': False,
                'hedge_ratio': None, 'error': 'statsmodels 未安装'}
    data = _np.column_stack([_np.log(a), _np.log(b)])
    try:
        result = coint_johansen(data, det_order=det_order, k_ar_diff=maxlag)
    except Exception as e:
        return {'trace_stat': None, 'is_coint': False, 'hedge_ratio': None, 'error': str(e)}

    # 特征值 / 协整向量
    eig = [float(x) for x in result.eig]
    evec = result.evec
    # 第一协整向量 (v0, v1) 满足 v0·logA + v1·logB 平稳
    #   => logA = -(v1/v0)·logB，对冲比率 = -evec[1,0]/evec[0,0]
    if len(eig) > 0 and abs(evec[0, 0]) > 1e-9:
        beta_a = float(-evec[1, 0] / evec[0, 0])
    else:
        beta_a = 1.0
    # 使用 statsmodels 自带的临界值表（cvt[:, 1] 为 5% 水平），
    # 不再硬编码（硬编码值与 det_order 语义不匹配，判定偏松）
    cv = float(result.cvt[0, 1])
    trace_stat = float(result.lr1[0])  # 第 0 个特征值对应的 trace 统计量
    return {
        'trace_stat': round(float(result.lr1[0]), 4),
        'trace_cv_5pct': float(cv),
        'is_coint': bool(trace_stat > cv),
        'hedge_ratio': round(beta_a, 4),
        'eigenvalues': [round(x, 4) for x in eig],
    }


def half_life_filter(spread, max_halflife=120, min_halflife=3):
    """均值回归半衰期筛选 — 用 AR(1) 计算并约束。

    半衰期公式： lag = -ln(2) / ln(1 + phi)，phi 是 AR(1) 系数。

    Returns:
        dict: halflife, is_mean_reverting, recommendation
    """
    import numpy as _np
    s = _np.array(spread, dtype=float)
    s = s[~_np.isnan(s)]
    if len(s) < 30:
        return {'halflife': None, 'is_mean_reverting': False,
                'recommendation': '样本不足'}
    diff = _np.diff(s)
    lagged = s[:-1]
    # OLS: diff = a + phi * lagged + eps
    try:
        x_mean = _np.mean(lagged)
        y_mean = _np.mean(diff)
        num = _np.sum((lagged - x_mean) * (diff - y_mean))
        den = _np.sum((lagged - x_mean) ** 2)
        if abs(den) < 1e-12:
            return {'halflife': None, 'is_mean_reverting': False,
                    'recommendation': '方差为 0'}
        phi = float(num / den)
    except Exception:
        return {'halflife': None, 'is_mean_reverting': False,
                'recommendation': '估计失败'}

    if phi >= 0 or abs(1 + phi) < 1e-9:
        return {'halflife': float("inf"), 'phi': round(phi, 4),
                'is_mean_reverting': False,
                'recommendation': '非均值回归序列'}
    try:
        halflife = -math.log(2) / math.log(1 + phi)
    except Exception:
        halflife = float("inf")

    is_mr = (min_halflife <= halflife <= max_halflife)
    if not is_mr:
        if halflife < min_halflife:
            rec = f'半衰期过短 ({halflife:.1f} 天)，价差易被噪音触发；建议拉宽阈值'
        else:
            rec = f'半衰期过长 ({halflife:.1f} 天)，均值回归信号弱；建议弃用'
    else:
        rec = f'半衰期合适 ({halflife:.1f} 天)，可正常执行配对交易'
    return {
        'halflife': round(float(halflife), 2),
        'phi': round(phi, 4),
        'is_mean_reverting': bool(is_mr),
        'recommendation': rec,
    }


def zscore_signal(prices_a, prices_b, hedge_ratio=1.0, lookback=60,
                   entry_z=2.0, exit_z=0.5):
    """基于滚动 z-score 的开平仓信号。

    Returns:
        dict: z_current, signal, spread_mean, spread_std, positions
    """
    import numpy as _np
    a = _np.array(prices_a, dtype=float)
    b = _np.array(prices_b, dtype=float)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    if n < lookback:
        return {'z_current': 0.0, 'signal': '数据不足'}

    spread = a - hedge_ratio * b
    rolling_mu = _np.array([_np.mean(spread[max(0, i - lookback):i + 1])
                            for i in range(n)])
    rolling_sd = _np.array([_np.std(spread[max(0, i - lookback):i + 1])
                            for i in range(n)])
    z = (spread - rolling_mu) / (rolling_sd + 1e-9)

    z_curr = float(z[-1])
    if z_curr > entry_z:
        signal = '做空价差 (short_spread)'  # 价差偏高, 期望回归
    elif z_curr < -entry_z:
        signal = '做多价差 (long_spread)'
    elif abs(z_curr) < exit_z:
        signal = '平仓 / 中性'
    else:
        signal = '持仓观望'

    positions = []
    state = 0  # 0=空仓, 1=多价差, -1=空价差
    for zi in z:
        if state == 0:
            if zi < -entry_z:
                state = 1
            elif zi > entry_z:
                state = -1
        elif state == 1 and zi >= -exit_z:
            state = 0
        elif state == -1 and zi <= exit_z:
            state = 0
        positions.append(state)

    return {
        'z_current': round(z_curr, 4),
        'signal': signal,
        'spread_mean': round(float(rolling_mu[-1]), 4),
        'spread_std': round(float(rolling_sd[-1]), 4),
        'entry_z': entry_z,
        'exit_z': exit_z,
        'positions': positions,
        'spread_last': [round(float(v), 4) for v in spread[-10:].tolist()],
    }


def demo():
    """演示配对交易"""
    np.random.seed(42)

    # 模拟两只协整股票的价格
    n = 200
    # 股票 B 是随机游走
    b_returns = np.random.normal(0.0005, 0.015, n)
    prices_b = 100 * np.exp(np.cumsum(b_returns))

    # 股票 A 与 B 协整
    noise = np.random.normal(0, 0.5, n)
    spread = np.zeros(n)
    for i in range(1, n):
        spread[i] = spread[i - 1] * 0.95 + noise[i]  # AR(1) 均值回归
    prices_a = 0.8 * prices_b + spread + 20

    stock_a = {"symbol": "600036", "name": "招商银行", "prices": prices_a.tolist()}
    stock_b = {"symbol": "601398", "name": "工商银行", "prices": prices_b.tolist()}

    trader = PairsTrader(min_correlation=0.5)
    result = trader.analyze_pair(stock_a, stock_b)

    if result:
        print(trader.generate_report(result))
    else:
        print("未找到有效配对")


if __name__ == "__main__":
    demo()
