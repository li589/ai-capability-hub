#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预测校准 (v9.0.0 新增)
======================
让预测的「置信度」名副其实。

问题：预测器输出的 confidence=0.7 并不代表真的 70% 命中。需要用历史
预测-实现对（PredictionTracker 已持久化 confidence + hit）做可靠性校准：
  - 把预测按 confidence 分桶，算各桶实际命中率 → 可靠性曲线
  - Brier 分数（综合校准+分辨）
  - calibrate(confidence) → 用可靠性曲线把原始置信度映射为「校准后置信度」

校准只在有足够历史样本时生效；样本不足时原样返回（诚实）。

纯函数（分桶/Brier/PAV 保序回归）离线可测；类封装接线 PredictionTracker。

用法:
    from stock_researcher.evolution.calibration import PredictionCalibrator
    cal = PredictionCalibrator().build(model=None, horizon="1M")
    print(cal.brier, cal.reliability)
    adj = PredictionCalibrator().calibrate(0.7, horizon="1M")
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple
from dataclasses import dataclass, field


@dataclass
class CalibrationResult:
    """校准结果"""
    n_samples: int = 0
    brier: float = 0.0              # 越低越好（0=完美）
    reliability: List[Dict] = field(default_factory=list)  # 分桶可靠性
    mean_confidence: float = 0.0
    mean_hit_rate: float = 0.0
    calibration_error: float = 0.0  # 期望校准误差 ECE
    sufficient: bool = False        # 样本是否充足
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层
# ════════════════════════════════════════════════════════════

DEFAULT_BINS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]


def bucket_reliability(
    pairs: Sequence[Tuple[float, int]],
    bins: Sequence[float] = None,
) -> List[Dict]:
    """分桶可靠性：pairs=[(confidence, hit(0/1))]。

    返回 [{bin_lo, bin_hi, mid, count, avg_conf, hit_rate}, ...]（仅保留 count>0 的桶）。
    """
    bins = list(bins or DEFAULT_BINS)
    out = []
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        bucket = [(c, h) for c, h in pairs if lo <= c < hi]
        if not bucket:
            continue
        confs = [c for c, _ in bucket]
        hits = [h for _, h in bucket]
        out.append({
            "bin_lo": round(lo, 2), "bin_hi": round(hi, 2),
            "mid": round((lo + hi) / 2, 2),
            "count": len(bucket),
            "avg_conf": round(sum(confs) / len(confs), 3),
            "hit_rate": round(sum(hits) / len(hits), 3),
        })
    return out


def brier_score(pairs: Sequence[Tuple[float, int]]) -> float:
    """Brier 分数 = mean((conf - hit)^2)。越低越好。"""
    lst = [(float(c), int(h)) for c, h in pairs
           if c is not None and h is not None and math.isfinite(float(c))]
    if not lst:
        return 0.0
    return sum((c - h) ** 2 for c, h in lst) / len(lst)


def expected_calibration_error(reliability: Sequence[Dict], total: int) -> float:
    """ECE = Σ (|桶占比| × |avg_conf - hit_rate|)。"""
    if total <= 0:
        return 0.0
    ece = 0.0
    for b in reliability:
        w = b["count"] / total
        ece += w * abs(b["avg_conf"] - b["hit_rate"])
    return ece


def isotonic_fit(pairs: Sequence[Tuple[float, int]]) -> List[Tuple[float, float]]:
    """保序回归（PAV）：拟合一组 (x=conf, y=hit) 单调非降映射。

    返回排序后的 [(x, fitted_y)]，用于 calibrate 插值。
    """
    pts = sorted((float(c), int(h)) for c, h in pairs
                 if c is not None and h is not None and math.isfinite(float(c)))
    if not pts:
        return []
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # PAV: 合并违规的相邻块（保证非降）
    blocks = [(xs[i], ys[i], 1, float(ys[i])) for i in range(len(xs))]  # (sum_x, sum_y, n, mean_y)
    # 用栈做 PAV
    stack = []
    for x, y in zip(xs, ys):
        stack.append([x, y, 1])
        while len(stack) >= 2:
            prev_mean = stack[-2][1] / stack[-2][2]
            cur_mean = stack[-1][1] / stack[-1][2]
            if cur_mean < prev_mean - 1e-12:
                # 合并
                sx = stack[-2][0] + stack[-1][0]
                sy = stack[-2][1] + stack[-1][1]
                nn = stack[-2][2] + stack[-1][2]
                stack.pop()
                stack[-1] = [sx, sy, nn]
            else:
                break
    # 展开为 (block_center_x, block_mean_y)
    fitted = []
    for sx, sy, nn in stack:
        fitted.append((sx / nn, sy / nn))
    return fitted


def calibrate_value(
    confidence: float, fitted: Sequence[Tuple[float, float]],
) -> float:
    """用保序拟合结果把原始置信度映射为校准后置信度（线性插值）。

    fitted 为空 → 原样返回。
    """
    if not fitted:
        return confidence
    f = sorted(fitted)
    if confidence <= f[0][0]:
        return f[0][1]
    if confidence >= f[-1][0]:
        return f[-1][1]
    for i in range(len(f) - 1):
        x0, y0 = f[i]
        x1, y1 = f[i + 1]
        if x0 <= confidence <= x1:
            if x1 == x0:
                return (y0 + y1) / 2
            return y0 + (y1 - y0) * (confidence - x0) / (x1 - x0)
    return confidence


# ════════════════════════════════════════════════════════════
# 校准器（接线 PredictionTracker）
# ════════════════════════════════════════════════════════════

class PredictionCalibrator:
    """预测置信度校准器。"""

    MIN_SAMPLES = 30   # 低于此数不校准（原样返回）

    def __init__(self):
        self._cache: Dict[str, CalibrationResult] = {}
        self._fitted: Dict[str, List] = {}

    def _load_pairs(
        self, model: Optional[str] = None, horizon: Optional[str] = None,
    ) -> List[Tuple[float, int]]:
        """从 PredictionTracker 读 (confidence, hit)。仅 resolved 记录。"""
        try:
            from stock_researcher.evolution.prediction_tracker import PredictionTracker
            tr = PredictionTracker()
            records = tr._read_all()
        except Exception:
            return []
        pairs = []
        for rec in records:
            if getattr(rec, "status", "") != "resolved":
                continue
            if model and getattr(rec, "source_model", "") != model:
                continue
            if horizon and getattr(rec, "horizon", "") != horizon:
                continue
            conf = getattr(rec, "confidence", None)
            hit = getattr(rec, "hit", None)
            if conf is not None and hit is not None:
                pairs.append((float(conf), int(hit)))
        return pairs

    def build(
        self, model: Optional[str] = None, horizon: Optional[str] = None,
    ) -> CalibrationResult:
        """构建校准结果（可靠性曲线 + Brier + 保序拟合）。"""
        key = f"{model}|{horizon}"
        if key in self._cache:
            return self._cache[key]
        pairs = self._load_pairs(model, horizon)
        if not pairs:
            res = CalibrationResult(note="无历史预测数据")
            self._cache[key] = res
            return res
        rel = bucket_reliability(pairs)
        brier = brier_score(pairs)
        ece = expected_calibration_error(rel, len(pairs))
        mean_conf = sum(c for c, _ in pairs) / len(pairs)
        mean_hit = sum(h for _, h in pairs) / len(pairs)
        fitted = isotonic_fit(pairs) if len(pairs) >= self.MIN_SAMPLES else []
        res = CalibrationResult(
            n_samples=len(pairs),
            brier=round(brier, 4),
            reliability=rel,
            mean_confidence=round(mean_conf, 3),
            mean_hit_rate=round(mean_hit, 3),
            calibration_error=round(ece, 4),
            sufficient=len(pairs) >= self.MIN_SAMPLES,
            note=("样本充足，已校准" if fitted else
                  f"样本不足(<{self.MIN_SAMPLES})，未校准"),
        )
        self._cache[key] = res
        self._fitted[key] = fitted
        return res

    def calibrate(
        self, confidence: float,
        model: Optional[str] = None, horizon: Optional[str] = None,
    ) -> float:
        """把原始置信度映射为校准后置信度。样本不足原样返回。"""
        key = f"{model}|{horizon}"
        if key not in self._fitted:
            self.build(model, horizon)
        fitted = self._fitted.get(key, [])
        return round(calibrate_value(confidence, fitted), 4)

    @staticmethod
    def format(res: CalibrationResult) -> str:
        lines = [
            f"预测校准 | 样本{res.n_samples} Brier{res.brier:.3f} "
            f"ECE{res.calibration_error:.3f} ({res.note})",
            f"  平均置信{res.mean_confidence:.0%} vs 实际命中{res.mean_hit_rate:.0%}",
        ]
        if res.sufficient:
            lines.append(f"  {'桶':<10}{'样本':>6}{'平均置信':>10}{'命中率':>8}")
            for b in res.reliability:
                if b["count"] > 0:
                    lines.append(
                        f"  [{b['bin_lo']:.1f}-{b['bin_hi']:.1f}]{b['count']:>6}"
                        f"{b['avg_conf']:>9.0%}{b['hit_rate']:>8.0%}"
                    )
        return "\n".join(lines)


def calibrate_confidence(
    confidence: float, horizon: Optional[str] = None,
) -> float:
    """便捷函数：校准单个置信度。"""
    return PredictionCalibrator().calibrate(confidence, horizon=horizon)
