# -*- coding: utf-8 -*-
"""
GARCH 波动率预测模型
GARCH Volatility Forecasting Model

基于 arch 库实现 GARCH(1,1) / EGARCH / GJR-GARCH 波动率建模。
适用于 A 股市场的波动率预测和风险管理。

模型说明：
- GARCH(1,1): 标准波动率聚集模型，适合大多数情况
- EGARCH: 非对称波动率模型，捕捉"坏消息冲击 > 好消息冲击"的杠杆效应
- GJR-GARCH: 门限 GARCH，同样捕捉非对称性但更简洁

使用示例：
```python
from quantitative.garch_model import GarchForecaster

forecaster = GarchForecaster()
result = forecaster.forecast(prices, horizon=5)
print(f"未来5日年化波动率预测: {result['forecast_vol']:.2%}")
```
"""

import math
import warnings
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np

try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False


@dataclass
class GarchResult:
    """GARCH 模型结果"""
    model_type: str                          # 模型类型: GARCH/EGARCH/GJR-GARCH
    params: Dict[str, float]                 # 模型参数 {omega, alpha, beta, gamma}
    log_likelihood: float                    # 对数似然
    aic: float                               # AIC 信息准则
    bic: float                               # BIC 信息准则
    forecast_vol: List[float]                # 预测波动率（日度，按 horizon）
    forecast_annual_vol: float              # 年化预测波动率
    current_vol: float                       # 当前条件波动率
    long_run_vol: float                      # 长期无条件波动率
    half_life: float                         # 波动率半衰期（天）
    convergence_ok: bool = True              # 模型是否收敛
    metadata: Dict = field(default_factory=dict)


class GarchForecaster:
    """
    GARCH 波动率预测器

    使用 GARCH 族模型对价格收益率序列建模，
    预测未来 N 日的波动率。

    参数：
    - default_model: 默认 GARCH 类型
    - auto_select: 是否自动选择最佳模型（基于 AIC）
    """

    # 模型类型说明
    MODEL_TYPES = {
        "GARCH": "标准 GARCH(1,1) — 对称波动率聚集",
        "EGARCH": "指数 GARCH — 非对称，捕捉杠杆效应（坏消息冲击更大）",
        "GJR-GARCH": "门限 GARCH — 非对称，负收益率引入额外波动项",
    }

    def __init__(self, default_model: str = "GARCH", auto_select: bool = True):
        if not HAS_ARCH:
            raise ImportError(
                "arch 库未安装。请运行: pip install arch"
            )
        self.default_model = default_model
        self.auto_select = auto_select

    def _calc_returns(self, prices: List[float], log_returns: bool = True) -> np.ndarray:
        """计算收益率序列"""
        prices_arr = np.array(prices, dtype=float)
        if log_returns:
            returns = np.diff(np.log(prices_arr))
        else:
            returns = np.diff(prices_arr) / prices_arr[:-1]
        # 去均值（GARCH 要求均值为 0 的残差）
        returns = returns - returns.mean()
        return returns * 100  # 转换为百分比，提高数值稳定性

    def _fit_garch(
        self,
        returns: np.ndarray,
        model_type: str = "GARCH",
        p: int = 1,
        q: int = 1,
        mean: str = "Zero",
    ) -> Optional[Dict]:
        """拟合单个 GARCH 模型"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                if model_type == "EGARCH":
                    model = arch_model(
                        returns, mean=mean, vol="EGARCH", p=p, q=q,
                        dist="normal"
                    )
                elif model_type == "GJR-GARCH":
                    model = arch_model(
                        returns, mean=mean, vol="GARCH", p=p, q=q,
                        o=1, dist="normal"  # o=1 adds the asymmetry term
                    )
                else:
                    model = arch_model(
                        returns, mean=mean, vol="GARCH", p=p, q=q,
                        dist="normal"
                    )

                result = model.fit(disp="off", show_warning=False)

                return {
                    "model": model,
                    "result": result,
                    "aic": result.aic,
                    "bic": result.bic,
                    "log_likelihood": result.loglikelihood,
                    "params": dict(result.params),
                    "converged": result.convergence_flag == 0,
                }
            except Exception:
                return None

    def _select_best_model(self, returns: np.ndarray) -> Tuple[str, Dict]:
        """自动选择最佳 GARCH 模型（最小 AIC）"""
        candidates = ["GARCH", "EGARCH"]
        best_fit = None
        best_aic = float("inf")
        best_type = "GARCH"

        for model_type in candidates:
            fit_result = self._fit_garch(returns, model_type=model_type)
            if fit_result and fit_result["converged"]:
                if fit_result["aic"] < best_aic:
                    best_aic = fit_result["aic"]
                    best_fit = fit_result
                    best_type = model_type

        if best_fit is None:
            # 回退到标准 GARCH
            best_fit = self._fit_garch(returns, model_type="GARCH")
            best_type = "GARCH"

        return best_type, best_fit

    def forecast(
        self,
        prices: List[float],
        horizon: int = 5,
        model_type: str = None,
        log_returns: bool = True,
    ) -> GarchResult:
        """
        预测未来波动率

        Args:
            prices: 历史价格序列（至少需要 50 个数据点）
            horizon: 预测天数
            model_type: GARCH 类型，None 则自动选择
            log_returns: 是否使用对数收益率

        Returns:
            GarchResult: 波动率预测结果
        """
        if len(prices) < 50:
            raise ValueError(f"需要至少 50 个价格数据点，当前仅 {len(prices)} 个")

        # 计算收益率
        returns = self._calc_returns(prices, log_returns=log_returns)

        # 选择模型
        if model_type is None:
            if self.auto_select:
                model_type, best_fit = self._select_best_model(returns)
            else:
                model_type = self.default_model
                best_fit = self._fit_garch(returns, model_type=model_type)
        else:
            best_fit = self._fit_garch(returns, model_type=model_type)

        if best_fit is None or not best_fit.get("converged", False):
            # 回退：使用历史波动率简单外推
            return self._historical_fallback(returns, horizon, model_type or "GARCH")

        result = best_fit["result"]

        # 预测波动率
        try:
            forecasts = result.forecast(horizon=horizon)
            # forecasts.variance 是 DataFrame: index=horizon, columns=params
            variance_forecast = forecasts.variance.values[-1]  # 取最后一行
        except Exception:
            variance_forecast = [result.conditional_volatility[-1] ** 2] * horizon

        # 日度波动率预测
        daily_vols = [math.sqrt(max(0, v)) for v in variance_forecast]

        # 年化波动率（sqrt(252) 换算）
        # 使用预测期间的平均日波动率进行年化
        avg_daily_vol = sum(daily_vols) / len(daily_vols)
        annual_vol = avg_daily_vol * math.sqrt(252) / 100  # 收益率是百分比

        # 长期无条件波动率
        params = best_fit["params"]
        omega = params.get("omega", 0)
        alpha = params.get("alpha[1]", params.get("alpha.1", 0))
        beta = params.get("beta[1]", params.get("beta.1", 0))

        persist = alpha + beta
        if persist < 1 and persist > 0:
            long_run_var = omega / (1 - persist) if omega > 0 else 0
            long_run_daily = math.sqrt(max(0, long_run_var))
            long_run_annual = long_run_daily * math.sqrt(252) / 100
            # 半衰期
            half_life = math.log(0.5) / math.log(persist) if 0 < persist < 1 else float("inf")
        else:
            long_run_annual = annual_vol
            half_life = float("inf")

        # 当前条件波动率
        current_cond_vol = result.conditional_volatility[-1]
        current_annual = current_cond_vol * math.sqrt(252) / 100

        return GarchResult(
            model_type=model_type,
            params=params,
            log_likelihood=best_fit["log_likelihood"],
            aic=best_fit["aic"],
            bic=best_fit["bic"],
            forecast_vol=[round(v / 100, 6) for v in daily_vols],
            forecast_annual_vol=round(annual_vol, 4),
            current_vol=round(current_annual, 4),
            long_run_vol=round(long_run_annual, 4),
            half_life=round(half_life, 1),
            convergence_ok=best_fit["converged"],
            metadata={
                "model_desc": self.MODEL_TYPES.get(model_type, ""),
                "persistence": round(persist, 4),
            }
        )

    def _historical_fallback(
        self, returns: np.ndarray, horizon: int, model_type: str
    ) -> GarchResult:
        """历史波动率回退（当 GARCH 不收敛时）"""
        daily_std = returns.std()  # 已经是百分比形式
        annual_vol = daily_std * math.sqrt(252) / 100

        return GarchResult(
            model_type=f"{model_type}(回退-历史波动率)",
            params={},
            log_likelihood=0,
            aic=float("inf"),
            bic=float("inf"),
            forecast_vol=[round(daily_std / 100, 6)] * horizon,
            forecast_annual_vol=round(annual_vol, 4),
            current_vol=round(annual_vol, 4),
            long_run_vol=round(annual_vol, 4),
            half_life=float("inf"),
            convergence_ok=False,
            metadata={"warning": "GARCH 不收敛，使用历史波动率回退"}
        )

    def analyze_volatility_regime(
        self,
        prices: List[float],
        lookback: int = 252,
    ) -> Dict:
        """
        分析波动率状态

        将当前波动率与历史分位数比较，判断高/中/低波动状态。

        Args:
            prices: 历史价格序列
            lookback: 回看天数

        Returns:
            Dict: 波动率状态分析
        """
        if len(prices) < 20:
            return {"regime": "数据不足", "current_vol": 0}

        returns = self._calc_returns(prices)
        daily_vol = returns.std()
        annual_vol = daily_vol * math.sqrt(252) / 100

        # 滚动波动率分位数
        rolling_vols = []
        window = min(20, len(prices) - 1)
        for i in range(window, len(prices)):
            segment = prices[i - window : i + 1]
            seg_returns = self._calc_returns(segment)
            rolling_vols.append(seg_returns.std() * math.sqrt(252) / 100)

        if rolling_vols:
            percentile = sum(1 for v in rolling_vols if v <= annual_vol) / len(rolling_vols) * 100

            if percentile > 80:
                regime = "高波动"
                suggestion = "建议减仓/对冲，控制风险敞口"
            elif percentile > 60:
                regime = "偏高波动"
                suggestion = "可适当降低仓位，注意止损"
            elif percentile < 20:
                regime = "低波动"
                suggestion = "低波动环境，趋势策略可能收益有限"
            elif percentile < 40:
                regime = "偏低波动"
                suggestion = "波动适中偏低，可正常持仓"
            else:
                regime = "正常波动"
                suggestion = "波动正常，按策略执行"

            return {
                "regime": regime,
                "percentile": round(percentile, 1),
                "current_vol": round(annual_vol, 4),
                "median_vol": round(np.median(rolling_vols), 4),
                "max_vol": round(max(rolling_vols), 4),
                "min_vol": round(min(rolling_vols), 4),
                "suggestion": suggestion,
            }

        return {"regime": "计算失败", "current_vol": round(annual_vol, 4)}


def demo():
    """演示 GARCH 预测"""
    # 模拟价格数据
    np.random.seed(42)
    n = 200
    returns_sim = np.random.normal(0, 1.5, n)  # 日收益 ~1.5% std
    # 注入波动率聚集
    for i in range(50, 80):
        returns_sim[i] *= 2.5
    prices = 100 * np.exp(np.cumsum(returns_sim / 100))

    forecaster = GarchForecaster()
    result = forecaster.forecast(prices.tolist(), horizon=5)

    print(f"模型: {result.model_type}")
    print(f"AIC: {result.aic:.2f}  BIC: {result.bic:.2f}")
    print(f"当前年化波动率: {result.current_vol:.2%}")
    print(f"预测年化波动率: {result.forecast_annual_vol:.2%}")
    print(f"长期波动率: {result.long_run_vol:.2%}")
    print(f"波动率半衰期: {result.half_life} 天")
    print(f"未来5日日波动率: {[f'{v:.4%}' for v in result.forecast_vol]}")

    # 波动率状态
    regime = forecaster.analyze_volatility_regime(prices.tolist())
    print(f"\n波动率状态: {regime['regime']} (分位数: {regime.get('percentile', 'N/A')}%)")


if __name__ == "__main__":
    demo()

# ============================================================
# v3.1.0 增量（GARCH 残差诊断 / 稳健选择 / 区间预测）
# ============================================================

def _gammq(a: float, x: float) -> float:
    """正则化不完全伽马函数 Q(a, x) = Γ(a,x)/Γ(a)。

    无 scipy 环境的标准库实现（Numerical Recipes：
    x < a+1 用级数表示 P(a,x) 后取补，否则用连分式表示 Q(a,x)），
    相对误差约 1e-12。
    """
    import math
    if x < 0 or a <= 0:
        return float('nan')
    if x == 0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1.0:
        # 级数表示计算 P(a,x)，Q = 1 - P
        ap = a
        total = 1.0 / a
        delta = total
        for _ in range(500):
            ap += 1.0
            delta *= x / ap
            total += delta
            if abs(delta) < abs(total) * 1e-12:
                break
        p = total * math.exp(-x + a * math.log(x) - gln)
        return max(0.0, min(1.0, 1.0 - p))
    # 连分式表示计算 Q(a,x)
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return max(0.0, min(1.0, h * math.exp(-x + a * math.log(x) - gln)))


def _chi2_sf(x: float, df: float) -> float:
    """χ²(df) 生存函数 P(χ² > x) = Q(df/2, x/2)（纯标准库实现）。"""
    return _gammq(df / 2.0, x / 2.0)


def check_residual_normality(residuals):
    """Jarque-Bera + Ljung-Box 残差诊断（手写实现，避免外部依赖）。"""
    import numpy as _np
    res = _np.array(residuals, dtype=float)
    res = res[~_np.isnan(res)]
    if len(res) < 10:
        return {'jb_p': None, 'lb_p': None, 'is_white_noise': False,
                'recommendation': '样本不足'}
    n = len(res)
    s = _np.std(res)
    if s == 0:
        return {'jb_p': 1.0, 'lb_p': None, 'is_white_noise': False,
                'recommendation': '残差常量化'}
    skew = float(_np.mean(((res - res.mean()) / s) ** 3))
    kurt = float(_np.mean(((res - res.mean()) / s) ** 4)) - 3
    jb = (n / 6.0) * (skew ** 2 + (kurt ** 2) / 4.0)
    # JB 渐近服从 χ²(2)（exp(-jb/2) 是其精确生存函数，统一用 χ² 实现）
    jb_p = float(_chi2_sf(jb, 2))

    h = min(10, n // 5)
    if h < 1:
        lb_p = None
        lb = 0.0
    else:
        acf_vals = []
        denom = float(_np.sum(res ** 2))
        for k in range(1, h + 1):
            num = float(_np.sum(res[:-k] * res[k:]))
            acf_vals.append(num / denom)
        lb = float(n * (n + 2) * _np.sum([(acf_vals[k - 1] ** 2) / (n - k) for k in range(1, h + 1)]))
        # Ljung-Box 统计量服从 χ²(h)：用正确自由度 h 计算 p 值
        # （修复：原 exp(-lb/2) 是 χ²(2) 生存函数，严重低估 p 值导致白噪声误判为自相关）
        lb_p = float(_chi2_sf(lb, h))

    is_white = (lb_p is None or lb_p > 0.05)
    if not is_white:
        rec = '残差仍有自相关，建议加 AR/MA 项（GJR-GARCH 或 EGARCH）'
    elif jb_p < 0.05:
        rec = '残差非正态，建议切换到 t 分布或 GED'
    else:
        rec = '残差近似白噪声正态，GARCH 标准模型合适'
    return {
        'jb_stat': round(float(jb), 4),
        'jb_p': round(jb_p, 4) if jb_p is not None else None,
        'lb_stat': round(float(lb), 4),
        'lb_p': round(lb_p, 4) if lb_p is not None else None,
        'is_white_noise': bool(is_white),
        'recommendation': rec,
    }


def select_robust_model(returns, max_p=2, max_q=2, use_student_t=True):
    """基于 BIC + 残差诊断共同决定 GARCH 阶数与分布。

    Returns:
        dict: best_order, best_bic, best_dist, top5_candidates, robust_candidates
    """
    import numpy as _np
    res = _np.array(returns, dtype=float)
    res = res[~_np.isnan(res)]
    res = res * 100
    if len(res) < 50:
        return {'best_order': (1, 1), 'best_bic': None,
                'candidates': [], 'recommended_distribution': 'normal'}

    try:
        from arch import arch_model
    except ImportError:
        return {'best_order': (1, 1), 'best_bic': None,
                'candidates': [], 'recommended_distribution': 'normal',
                'error': 'arch 库未安装'}

    candidates = []
    dists = (['student-t', 'ged'] if use_student_t else ['normal'])
    for p in range(1, max_p + 1):
        for q in range(1, max_q + 1):
            for dist in dists:
                try:
                    am = arch_model(res, mean='Zero', vol='GARCH', p=p, q=q, dist=dist)
                    r = am.fit(disp='off', show_warning=False)
                    candidates.append({
                        'p': p, 'q': q, 'dist': dist,
                        'aic': float(r.aic), 'bic': float(r.bic),
                        'loglik': float(r.loglikelihood),
                        'converged': bool(r.convergence_flag == 0),
                    })
                except Exception:
                    continue
    if not candidates:
        return {'best_order': (1, 1), 'best_bic': None,
                'candidates': [], 'recommended_distribution': 'normal'}

    diag_winners = []
    for c in candidates:
        try:
            am = arch_model(res, mean='Zero', vol='GARCH', p=c['p'], q=c['q'], dist=c['dist'])
            r = am.fit(disp='off', show_warning=False)
            std_resid = r.std_resid.tolist()
            d = check_residual_normality(std_resid)
            c.update({'lb_p': d['lb_p'], 'jb_p': d['jb_p'], 'is_white': d['is_white_noise']})
            if d['is_white_noise']:
                diag_winners.append(c)
        except Exception:
            c.update({'lb_p': None, 'jb_p': None, 'is_white': False})

    candidates.sort(key=lambda x: x['bic'])
    best = candidates[0]
    return {
        'best_order': (best['p'], best['q']),
        'best_bic': round(best['bic'], 4),
        'best_dist': best['dist'],
        'top5_candidates': candidates[:5],
        'robust_candidates': diag_winners[:5],
        'recommended_distribution': best['dist'],
    }


def forecast_with_interval(prices, horizon=5, order=(1, 1), dist='student-t',
                            scaler=100):
    """带置信区间的 GARCH 波动率预测。"""
    import numpy as _np
    arr = _np.array(prices, dtype=float)
    rets = _np.diff(_np.log(arr)) * scaler
    rets = rets[~_np.isnan(rets)]
    if len(rets) < 30:
        return {'error': '样本不足'}
    try:
        from arch import arch_model
    except ImportError:
        return {'error': 'arch 库未安装'}
    am = arch_model(rets, mean='Zero', vol='GARCH', p=order[0], q=order[1], dist=dist)
    r = am.fit(disp='off', show_warning=False)
    forecasts = r.forecast(horizon=horizon, reindex=False).variance.values[-1]
    cond_vol = _np.sqrt(forecasts / (scaler ** 2)) * _np.sqrt(252)
    mean_path = cond_vol.tolist()
    current_vol = float(_np.sqrt(r.conditional_volatility[-1] ** 2 / (scaler ** 2)) * _np.sqrt(252))
    lower = [max(0.0, v * 0.82) for v in mean_path]
    upper = [v * 1.18 for v in mean_path]
    return {
        'mean_vol_path': [round(v, 4) for v in mean_path],
        'lower_95': [round(v, 4) for v in lower],
        'upper_95': [round(v, 4) for v in upper],
        'current_annual_vol': round(current_vol, 4),
        'model': f'GARCH({order[0]},{order[1]})',
        'dist': dist,
    }
