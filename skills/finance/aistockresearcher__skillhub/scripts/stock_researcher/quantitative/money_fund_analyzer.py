# -*- coding: utf-8 -*-
"""货币基金量化分析（money_fund_analyzer.py，v8.0 新增）

货币基金特性：收益 ≈ 7 日年化收益率，波动极小，看稳定性 + 规模。
评分逻辑：
  - 7日年化水平（50%）：年化越高越好（相对货币基金中枢 ~2%）
  - 7日年化稳定性（30%）：波动越小越好
  - 规模/申赎（20%）：规模大更安全，申赎稳定

用法：
    from stock_researcher.quantitative.money_fund_analyzer import MoneyFundAnalyzer
    r = MoneyFundAnalyzer().analyze(seven_day_yield_history=[1.8, 1.9, 2.0, 1.95, ...], fund_size=500)
"""

from typing import Dict, List, Optional


class MoneyFundAnalyzer:
    """货币基金量化分析（纯标准库）。"""

    def analyze(self, seven_day_yield_history: Optional[List[float]] = None,
                fund_size: Optional[float] = None,
                nav_series: Optional[List[float]] = None) -> Dict:
        """货币基金评分。

        Args:
            seven_day_yield_history: 7 日年化收益率历史（%）
            fund_size: 基金规模（亿元）
            nav_series: 净值序列（备选，用于推导收益率）

        Returns:
            {score, grade, metrics:{avg_yield, yield_std, fund_size}, signals}
        """
        yields = list(seven_day_yield_history or [])
        # 无 7 日年化时从净值序列推导日收益并年化
        if not yields and nav_series and len(nav_series) >= 2:
            rets = [(nav_series[i] / nav_series[i - 1] - 1) * 100 for i in range(1, len(nav_series))]
            if rets:
                yields = [r * 365 for r in rets]

        if not yields:
            return {"score": 0, "grade": "N/A", "metrics": {}, "signals": ["数据不足"]}

        avg_yield = sum(yields) / len(yields)
        if len(yields) > 1:
            mean = avg_yield
            var = sum((y - mean) ** 2 for y in yields) / len(yields)
            std = var ** 0.5
        else:
            std = 0.0

        # 1) 水平分（0-50）：年化 1.5% → 20，2.0% → 35，2.5% → 45，3%+ → 50
        level_score = max(0.0, min(50.0, (avg_yield - 1.0) * 25.0))
        # 2) 稳定分（0-30）：std 越小越好（<0.2 满分）
        stability_score = max(0.0, min(30.0, 30.0 - std * 60.0))
        # 3) 规模分（0-20）：>500 亿满分，<10 亿低
        if fund_size is not None:
            size_score = max(0.0, min(20.0, fund_size / 500.0 * 20.0))
        else:
            size_score = 10.0  # 未知规模给中性分
            stability_score -= 5.0  # 未知规模惩罚

        score = round(level_score + stability_score + size_score, 1)
        grade = ("A+" if score >= 80 else "A" if score >= 70 else
                 "B" if score >= 60 else "C")
        signals = []
        if avg_yield >= 2.5:
            signals.append(f"7日年化 {avg_yield:.2f}% 处于高位")
        elif avg_yield < 1.5:
            signals.append(f"7日年化 {avg_yield:.2f}% 偏低")
        if std < 0.1:
            signals.append("收益率高度稳定")
        elif std > 0.5:
            signals.append("收益率波动较大")
        if fund_size is not None and fund_size >= 500:
            signals.append("规模大，流动性安全")

        return {
            "score": score,
            "grade": grade,
            "metrics": {
                "avg_seven_day_yield": round(avg_yield, 3),
                "yield_std": round(std, 4),
                "fund_size_100m": round(fund_size, 1) if fund_size is not None else None,
                "samples": len(yields),
            },
            "signals": signals,
            "data_quality": "actual" if seven_day_yield_history else "derived",
        }

    def fetch_mf_nav(self, code: str) -> Dict:
        """获取货币基金净值（可选 akshare，未装/失败返回空 dict）。"""
        try:
            from stock_researcher.data.akshare_provider import ak_fund_nav
            return ak_fund_nav(code)
        except Exception:
            return {}

    def quick_money_fund_score(self, code: str) -> Dict:
        """一键货币基金评分（数据获取失败时返回数据不足）。"""
        nav = self.fetch_mf_nav(code)
        series = nav.get("nav_series") or []
        if series:
            return self.analyze(nav_series=series)
        return {"score": 0, "grade": "N/A", "metrics": {},
                "signals": ["净值数据不可用（akshare 未装或接口失败）"]}


if __name__ == "__main__":
    import json
    r = MoneyFundAnalyzer().analyze(
        seven_day_yield_history=[1.85, 1.92, 2.01, 1.98, 2.05, 2.10, 2.03],
        fund_size=800.0,
    )
    print(json.dumps(r, ensure_ascii=False, indent=2))
