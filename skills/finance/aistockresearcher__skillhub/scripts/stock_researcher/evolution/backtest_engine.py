#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
漫步前向回测引擎 (v6.0.0)
==========================
Walk-forward backtesting for prediction model validation.
纯 Python 标准库，零依赖。
"""

import sys
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from stock_researcher.data.market import MarketData
from stock_researcher.data.market_classifier import MarketClassifier
from stock_researcher.data.errors import safe_float


@dataclass
class BacktestResult:
    """回测结果"""
    code: str
    market: str
    total_signals: int = 0
    hit_count: int = 0
    hit_rate: float = 0.0
    avg_predicted_return: float = 0.0
    avg_actual_return: float = 0.0
    sharpe_if_followed: float = 0.0
    max_drawdown: float = 0.0
    by_horizon: Dict[str, dict] = field(default_factory=dict)
    signals_history: List[Dict] = field(default_factory=list)


class BacktestEngine:
    """漫步前向回测引擎

    用法:
        engine = BacktestEngine("600519", market="cn", train_window=120, test_window=20, step=5)
        result = engine.run()
        print(f"Hit rate: {result.hit_rate:.1%}")
    """

    def __init__(self, code: str, market: str = "cn",
                 train_window: int = 120, test_window: int = 20,
                 step: int = 5):
        self.code = code
        self.market = market
        self.train_window = train_window
        self.test_window = test_window
        self.step = step
        self._market_data = MarketData()

    def _fetch_history(self, days: int = 300) -> Dict:
        """获取历史K线"""
        try:
            return self._market_data.fetch_history(self.code, days=days)
        except Exception as e:
            print(f"[Backtest] 获取K线失败: {e}")
            return {}

    def _simple_predict(self, closes: List[float], horizon: int = 5) -> Tuple[str, float]:
        """简化版预测：基于近期趋势+波动率蒙特卡洛"""
        if len(closes) < 20:
            return ("neutral", 0.0)
        recent = closes[-10:]
        prev = closes[-20:-10]
        recent_ret = (recent[-1] / recent[0] - 1) if recent[0] != 0 else 0
        prev_ret = (prev[-1] / prev[0] - 1) if prev[0] != 0 else 0
        momentum = recent_ret * 0.6 + prev_ret * 0.4

        returns = [(recent[i] / recent[i-1] - 1) for i in range(1, len(recent)) if recent[i-1] != 0]
        mean_ret = sum(returns) / len(returns) if returns else 0
        std_ret = (sum((r - mean_ret)**2 for r in returns) / len(returns))**0.5 if returns else 0.01

        mc_return = momentum + random.gauss(0, std_ret * (horizon**0.5))
        direction = "up" if mc_return > 0 else "down"
        return (direction, mc_return)

    def run(self) -> BacktestResult:
        """执行漫步前向回测"""
        kline = self._fetch_history(days=max(self.train_window + self.test_window * 3, 300))
        closes = kline.get("closes", [])
        if len(closes) < self.train_window + 20:
            print(f"[Backtest] K线数据不足: {len(closes)} 条")
            return BacktestResult(code=self.code, market=self.market)

        result = BacktestResult(code=self.code, market=self.market)
        horizons = {"1d": 1, "3d": 3, "5d": 5, "10d": 10}
        horizon_stats = {h: {"hits": 0, "total": 0, "returns": []} for h in horizons}

        i = self.train_window
        while i + max(horizons.values()) < len(closes):
            train_data = closes[i - self.train_window:i]
            direction, predicted_ret = self._simple_predict(train_data, horizon=5)

            for h_name, h_days in horizons.items():
                if i + h_days < len(closes):
                    actual_ret = (closes[i + h_days] / closes[i] - 1) if closes[i] != 0 else 0
                    is_hit = (direction == "up" and actual_ret > 0) or \
                             (direction == "down" and actual_ret < 0)
                    horizon_stats[h_name]["total"] += 1
                    if is_hit:
                        horizon_stats[h_name]["hits"] += 1
                    horizon_stats[h_name]["returns"].append(actual_ret)

            result.total_signals += 1
            actual_5d = (closes[min(i+5, len(closes)-1)] / closes[i] - 1) if closes[i] != 0 else 0
            if (direction == "up" and actual_5d > 0) or (direction == "down" and actual_5d < 0):
                result.hit_count += 1

            result.signals_history.append({
                "date": str(i),
                "direction": direction,
                "predicted_ret": round(predicted_ret, 4),
                "actual_5d": round(actual_5d, 4),
            })

            i += self.step

        result.hit_rate = result.hit_count / result.total_signals if result.total_signals > 0 else 0

        for h_name, stats in horizon_stats.items():
            total = stats["total"]
            result.by_horizon[h_name] = {
                "hit_rate": round(stats["hits"] / total, 3) if total > 0 else 0,
                "total_signals": total,
            }

        all_returns = [r for h in horizon_stats.values() for r in h["returns"]]
        if all_returns:
            result.avg_actual_return = sum(all_returns) / len(all_returns)
            mean_r = result.avg_actual_return
            std_r = (sum((r - mean_r)**2 for r in all_returns) / len(all_returns))**0.5
            result.sharpe_if_followed = (mean_r / std_r * (252**0.5)) if std_r > 0 else 0

        return result

    def run_and_report(self) -> str:
        """运行回测并生成 Markdown 报告"""
        result = self.run()
        lines = [
            f"## 回测报告: {result.code} ({result.market})",
            f"",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总信号数 | {result.total_signals} |",
            f"| 命中率 (5日) | {result.hit_rate:.1%} |",
            f"| 夏普比率 (若跟随) | {result.sharpe_if_followed:.2f} |",
            f"| 平均每信号收益 | {result.avg_actual_return:.2%} |",
            f"",
            f"### 各周期命中率",
        ]
        for h, stats in result.by_horizon.items():
            lines.append(f"- **{h}**: {stats['hit_rate']:.1%} ({stats['total_signals']} 信号)")
        return "\n".join(lines)
