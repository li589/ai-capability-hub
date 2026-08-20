# -*- coding: utf-8 -*-
"""
历史形态匹配预测模块 v9.3
Historical Pattern Predictor

原理：在资产自身的历史中检索与"最近 N 日走势"最相似的形态窗口，
用这些窗口之后 horizon 日的真实涨跌做加权推断——相当于对单资产做
"近邻匹配 (k-NN on price shape)" 预测。

特点：
  - 纯标准库，零依赖，离线可用，确定性输出（无随机数）
  - 股票 / 基金净值 / 期货连续价格通用（输入收盘价序列即可）
  - 与 MultiHorizonForecaster 互补：后者基于规则信号，本模块基于历史重演
  - 诚实降级：历史不足 / 无相似形态时返回 data_mode="insufficient"，不编造

用法：
    from stock_researcher.quantitative.pattern_predictor import quick_pattern_forecast
    fc = quick_pattern_forecast(prices, horizon=5)
    print(fc["predicted_pct"], fc["prob_up"], fc["confidence"])
"""

import math
from typing import Dict, List, Optional


def _log_returns(prices: List[float]) -> List[float]:
    """对数收益率序列（过滤非正价格）。"""
    out = []
    prev = None
    for p in prices:
        try:
            p = float(p)
        except (TypeError, ValueError):
            continue
        if p <= 0:
            prev = None
            continue
        if prev is not None:
            out.append(math.log(p / prev))
        prev = p
    return out


def _pearson(x: List[float], y: List[float]) -> float:
    """皮尔逊相关系数（x/y 等长）。"""
    n = len(x)
    if n < 3:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx <= 0 or sy <= 0:
        return 0.0
    return cov / (sx * sy)


def _percentile(sorted_vals: List[float], q: float) -> float:
    """线性插值分位数（sorted_vals 已升序）。"""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = q * (len(sorted_vals) - 1)
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


class HistoricalPatternPredictor:
    """历史形态匹配预测器。

    Args:
        window: 形态窗口长度（交易日，默认 20）
        top_k: 取相似度前 K 个形态参与推断（默认 5）
        min_corr: 相似度门槛（低于此相关系数视为不相似，默认 0.5）
    """

    def __init__(self, window: int = 20, top_k: int = 5, min_corr: float = 0.5):
        self.window = max(5, int(window))
        self.top_k = max(1, int(top_k))
        self.min_corr = float(min_corr)

    # ── 核心 API ──────────────────────────────────────────────
    def predict(self, prices: List[float], horizon: int = 5) -> Dict:
        """形态匹配预测。

        Returns:
            {
              data_mode: ok / insufficient / no_match
              current_price, horizon,
              predicted_pct: 加权平均预期涨跌幅（%）
              p_low / p_high: 匹配样本 forward 收益的 25/75 分位（%）
              prob_up: 匹配样本中上涨占比（%）
              confidence: 0~100 置信度
              n_matches / avg_similarity,
              matches: [{start, similarity, forward_pct}]（按相似度降序）
            }
        """
        horizon = max(1, int(horizon))
        base = {
            "data_mode": "insufficient", "current_price": None,
            "horizon": horizon, "predicted_pct": 0.0,
            "p_low": 0.0, "p_high": 0.0, "prob_up": 50.0,
            "confidence": 0.0, "n_matches": 0, "avg_similarity": 0.0,
            "matches": [],
        }
        valid_prices = [float(p) for p in prices
                        if p is not None and float(p) > 0]
        if len(valid_prices) < 2:
            return base
        base["current_price"] = round(valid_prices[-1], 4)

        rets = _log_returns(valid_prices)
        # 至少需要 window 的 query + window 的历史样本 + horizon 的 forward
        if len(rets) < self.window * 2 + horizon:
            return base

        query = rets[-self.window:]
        # 候选窗口终点上限：为 forward horizon 留出空间，且不含 query 自身
        end_limit = len(rets) - horizon
        scored = []
        for start in range(0, end_limit - self.window + 1):
            cand = rets[start:start + self.window]
            corr = _pearson(query, cand)
            if corr < self.min_corr:
                continue
            fwd_log = sum(rets[start + self.window:start + self.window + horizon])
            fwd_pct = (math.exp(fwd_log) - 1) * 100
            scored.append((corr, start, fwd_pct))

        if not scored:
            base["data_mode"] = "no_match"
            return base

        # 相似度降序；同分按 start 升序保证确定性
        scored.sort(key=lambda t: (-t[0], t[1]))
        top = scored[:self.top_k]

        # 相似度加权平均 forward 收益
        weights = [max(c, 0.01) for c, _, _ in top]
        wsum = sum(weights)
        predicted = sum(w * fp for w, (_, _, fp) in zip(weights, top)) / wsum

        fwds = sorted(fp for _, _, fp in top)
        p_low = _percentile(fwds, 0.25)
        p_high = _percentile(fwds, 0.75)
        prob_up = sum(1 for _, _, fp in top if fp > 0) / len(top) * 100

        confidence = self._confidence(len(scored), top[0][0], prob_up, fwds)

        base.update({
            "data_mode": "ok",
            "predicted_pct": round(predicted, 2),
            "p_low": round(p_low, 2),
            "p_high": round(p_high, 2),
            "prob_up": round(prob_up, 1),
            "confidence": confidence,
            "n_matches": len(scored),
            "avg_similarity": round(sum(c for c, _, _ in top) / len(top), 3),
            "matches": [
                {"start": s, "similarity": round(c, 3),
                 "forward_pct": round(fp, 2)}
                for c, s, fp in top
            ],
        })
        return base

    # ── 置信度 ────────────────────────────────────────────────
    def _confidence(self, n_total: int, best_corr: float,
                    prob_up: float, fwds: List[float]) -> float:
        """置信度 = 样本量分 40% + 相似度分 40% + 一致性分 20%。"""
        count_score = min(1.0, n_total / 10.0)
        corr_score = max(0.0, min(1.0, (best_corr - self.min_corr)
                                  / (1.0 - self.min_corr + 1e-9)))
        agree = max(prob_up, 100 - prob_up) / 100  # 方向一致性
        # forward 收益离散度越大，一致性越低
        if len(fwds) >= 2:
            mean = sum(fwds) / len(fwds)
            std = math.sqrt(sum((f - mean) ** 2 for f in fwds) / (len(fwds) - 1))
            disp_penalty = max(0.0, min(0.5, std / 20.0))
            agree = max(0.0, agree - disp_penalty)
        return round(100 * (0.4 * count_score + 0.4 * corr_score
                            + 0.2 * agree), 1)


# ── 便捷函数 ──────────────────────────────────────────────────

def quick_pattern_forecast(prices: List[float], horizon: int = 5,
                           window: int = 20, top_k: int = 5) -> Dict:
    """一步式历史形态匹配预测（股票/基金净值/期货价格通用）。"""
    return HistoricalPatternPredictor(window=window, top_k=top_k).predict(
        prices, horizon=horizon)


def pattern_direction_label(forecast: Dict, threshold: float = 1.0) -> str:
    """把预测结果转成中文方向标签：看涨 / 看跌 / 震荡。"""
    if not forecast or forecast.get("data_mode") != "ok":
        return "数据不足"
    pct = forecast.get("predicted_pct", 0.0)
    conf = forecast.get("confidence", 0.0)
    if pct >= threshold and conf >= 40:
        return "看涨"
    if pct <= -threshold and conf >= 40:
        return "看跌"
    return "震荡"


if __name__ == "__main__":
    import json
    # 确定性 demo：正弦叠加趋势，历史会重复出现相似形态
    demo = [100 * (1 + 0.001 * i) * (1 + 0.03 * math.sin(i / 5.0))
            for i in range(120)]
    r = quick_pattern_forecast(demo, horizon=5)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("方向：", pattern_direction_label(r))
