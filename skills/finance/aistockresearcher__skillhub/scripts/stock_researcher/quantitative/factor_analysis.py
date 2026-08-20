# -*- coding: utf-8 -*-
"""
A股因子分析模型
Factor Analysis Model for A-shares

实现 A 股市场常用的多因子模型，包括：
- 规模因子 (Size): 小市值溢价
- 价值因子 (Value): 低估值溢价 (PE/PB)
- 动量因子 (Momentum): 趋势延续效应
- 质量因子 (Quality): ROE/毛利率/负债率
- 低波动因子 (Low Volatility): 低风险异象
- 成长因子 (Growth): 盈利/营收增长
- 换手率因子 (Turnover): 流动性溢价
- 分析师预期因子 (Analyst): 一致预期修正

使用示例：
```python
from quantitative.factor_analysis import FactorAnalyzer

analyzer = FactorAnalyzer()
scores = analyzer.score_stocks(stock_data_list)
top_stocks = analyzer.get_top_stocks(scores, n=20)
```
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np


@dataclass
class FactorScore:
    """单因子评分"""
    name: str                    # 因子名称
    raw_value: float             # 原始值
    z_score: float               # 标准化 Z-Score
    percentile: float            # 百分位排名 (0-100)
    score: float                 # 因子得分 (-100 ~ +100)
    direction: str               # 多空方向
    weight: float = 1.0          # 因子权重


@dataclass
class StockFactorReport:
    """个股因子分析报告"""
    symbol: str
    name: str = ""
    composite_score: float = 0         # 综合得分
    percentile_rank: float = 0         # 全市场排名百分位
    factors: Dict[str, FactorScore] = field(default_factory=dict)
    recommendation: str = "观望"


class FactorAnalyzer:
    """
    A股多因子分析器

    对股票池进行多维度因子评分，筛选优质标的。

    参数：
    - factor_weights: 各因子权重字典
    - enable_all: 是否启用所有因子
    """

    # 默认因子权重（v5.0 升级为 10 因子，新增 moat + financial_health）
    DEFAULT_WEIGHTS = {
        "value": 0.18,        # 价值因子（降权，部分被 moat 覆盖）
        "momentum": 0.12,     # 动量因子
        "quality": 0.13,      # 质量因子（降权，部分被 financial_health 覆盖）
        "size": 0.04,         # 规模因子
        "growth": 0.10,       # 成长因子
        "low_vol": 0.08,      # 低波动因子
        "turnover": 0.04,     # 换手率因子
        "analyst": 0.04,      # 分析师预期因子
        "moat": 0.15,         # 护城河因子（v5.0 新增）
        "financial_health": 0.12,  # 财务健康因子（v5.0 新增）
    }

    FACTOR_DESCRIPTIONS = {
        "value": "价值因子 - 低 PE/PB 股票超额收益",
        "momentum": "动量因子 - 近期强势股趋势延续",
        "quality": "质量因子 - 高 ROE/低负债 公司溢价",
        "size": "规模因子 - 小市值股票溢价效应",
        "growth": "成长因子 - 盈利/营收高增长溢价",
        "low_vol": "低波动因子 - 低风险股票长期超额收益",
        "turnover": "换手率因子 - 低换手率股票的流动性溢价",
        "analyst": "分析师预期因子 - 一致预期上调的超额收益",
        "moat": "护城河因子 - 高毛利率稳定性/ROIC 一致性溢价（v5.0 新增）",
        "financial_health": "财务健康因子 - Altman Z/Piotroski F/Beneish M 综合评估（v5.0 新增）",
    }

    def __init__(
        self,
        factor_weights: Dict[str, float] = None,
        enable_all: bool = True,
    ):
        self.factor_weights = factor_weights or self.DEFAULT_WEIGHTS.copy()

        # 归一化权重
        total = sum(self.factor_weights.values())
        if total > 0:
            self.factor_weights = {
                k: v / total for k, v in self.factor_weights.items()
            }

        self.enable_all = enable_all

    # ── 各因子计算方法 ──────────────────────────────

    @staticmethod
    def _safe_float(v, default=0.0) -> float:
        """安全转浮点数"""
        try:
            f = float(v)
            return f if abs(f) < 1e10 and not math.isnan(f) and not math.isinf(f) else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _cross_section_zscore(values: List[float]) -> List[float]:
        """横截面 Z-Score 标准化（去极值 + 标准化）"""
        arr = np.array(values, dtype=float)
        # 去极值：MAD 方法，5 倍中位数绝对偏差截尾
        median = np.median(arr)
        mad = np.median(np.abs(arr - median))
        if mad > 0:
            upper = median + 5 * mad
            lower = median - 5 * mad
            arr = np.clip(arr, lower, upper)
        # Z-Score
        std = arr.std()
        if std > 0:
            return list((arr - arr.mean()) / std)
        return [0.0] * len(values)

    @staticmethod
    def _percentile_rank(values: List[float]) -> List[float]:
        """计算百分位排名 (0-100)"""
        arr = np.array(values, dtype=float)
        n = len(arr)
        if n <= 1:
            return [50.0] * n
        ranks = np.argsort(np.argsort(arr))  # 双排序得到排名
        return list(ranks / (n - 1) * 100)

    def calc_value_factor(self, stock: Dict) -> FactorScore:
        """
        价值因子：低 PE/PB 股票得分高

        使用 PE_TTM 和 PB 的倒数加权
        """
        pe = self._safe_float(stock.get("pe", 0))
        pb = self._safe_float(stock.get("pb", 0))

        score = 0
        # PE 越低越好（正PE才有意义）
        if 0 < pe < 200:
            score += max(0, 100 - pe) * 0.6  # PE=0→60分, PE=100→0分
        # PB 越低越好
        if 0 < pb < 50:
            score += max(0, 100 - pb * 2) * 0.4  # PB=0→40分, PB=5→36分

        return FactorScore(
            name="value",
            raw_value=pe,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="低估值做多",
            weight=self.factor_weights.get("value", 0.25),
        )

    def calc_momentum_factor(self, stock: Dict) -> FactorScore:
        """
        动量因子：近期涨幅居前的股票得分高

        使用近 20/60 日涨跌幅
        """
        ret_20d = self._safe_float(stock.get("ret_20d", 0))  # 百分比
        ret_60d = self._safe_float(stock.get("ret_60d", 0))

        # 综合动量：20日占60%，60日占40%
        momentum = ret_20d * 0.6 + ret_60d * 0.4

        # 动量转换为得分（-50% ∼ +50% 映射到 0-100）
        score = max(0, min(100, 50 + momentum))

        return FactorScore(
            name="momentum",
            raw_value=momentum,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="动量做多",
            weight=self.factor_weights.get("momentum", 0.15),
        )

    def calc_quality_factor(self, stock: Dict) -> FactorScore:
        """
        质量因子：高 ROE、高毛利率、低负债率

        使用 ROE + 毛利率 + 资产负债率倒数
        """
        roe = self._safe_float(stock.get("roe", 0))  # 百分比
        gross_margin = self._safe_float(stock.get("gross_margin", 0))
        debt_ratio = self._safe_float(stock.get("debt_ratio", 50))

        score = 0
        # ROE 越高越好（0-40% 映射到 0-100）
        score += min(100, max(0, roe * 2.5)) * 0.5
        # 毛利率越高越好
        score += min(100, max(0, gross_margin * 1.5)) * 0.3
        # 负债率越低越好（反向：负债率 0%→100分, 80%→0分）
        debt_score = max(0, 100 - debt_ratio * 1.25)
        score += debt_score * 0.2

        return FactorScore(
            name="quality",
            raw_value=roe,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="高质量做多",
            weight=self.factor_weights.get("quality", 0.20),
        )

    def calc_size_factor(self, stock: Dict) -> FactorScore:
        """
        规模因子：小市值股票得分高（小市值溢价效应）

        使用总市值（亿元）
        """
        mcap = self._safe_float(stock.get("mcap", 0))  # 亿元

        # 市值越小得分越高
        # <50亿→100分, 50-200亿→80分, 200-1000亿→50分, >1000亿→20分
        if mcap <= 0:
            score = 50
        elif mcap < 50:
            score = 100
        elif mcap < 200:
            score = 80
        elif mcap < 500:
            score = 60
        elif mcap < 1000:
            score = 40
        else:
            score = max(10, 30 - mcap / 100)

        return FactorScore(
            name="size",
            raw_value=mcap,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="小市值做多",
            weight=self.factor_weights.get("size", 0.05),
        )

    def calc_growth_factor(self, stock: Dict) -> FactorScore:
        """
        成长因子：盈利和营收高增长

        使用 EPS 增长率和营收增长率
        """
        eps_growth = self._safe_float(stock.get("eps_growth", 0))  # 百分比
        revenue_growth = self._safe_float(stock.get("revenue_growth", 0))

        score = 0
        # EPS 增长
        score += min(100, max(0, 50 + eps_growth)) * 0.6
        # 营收增长
        score += min(100, max(0, 50 + revenue_growth)) * 0.4

        return FactorScore(
            name="growth",
            raw_value=eps_growth,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="高增长做多",
            weight=self.factor_weights.get("growth", 0.15),
        )

    def calc_low_vol_factor(self, stock: Dict) -> FactorScore:
        """
        低波动因子：低波动股票长期超额收益

        使用年化波动率（%）
        """
        volatility = self._safe_float(stock.get("volatility", 30))  # 年化波动率%

        # 波动率越低得分越高
        score = max(0, 100 - volatility * 1.5)

        return FactorScore(
            name="low_vol",
            raw_value=volatility,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="低波动做多",
            weight=self.factor_weights.get("low_vol", 0.10),
        )

    def calc_turnover_factor(self, stock: Dict) -> FactorScore:
        """
        换手率因子：低换手率股票的流动性溢价

        使用日均换手率（%）
        """
        turnover = self._safe_float(stock.get("turnover", 5))  # %

        # 换手率适中最好（过低缺乏流动性，过高炒作风险）
        if turnover <= 0:
            score = 50
        elif turnover < 1:
            score = 60  # 太低：流动性差
        elif turnover < 3:
            score = 90  # 适中偏低：最佳
        elif turnover < 5:
            score = 80  # 适中
        elif turnover < 10:
            score = 50  # 偏高
        else:
            score = 20  # 过高：炒作嫌疑

        return FactorScore(
            name="turnover",
            raw_value=turnover,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="适中换手做多",
            weight=self.factor_weights.get("turnover", 0.05),
        )

    def calc_analyst_factor(self, stock: Dict) -> FactorScore:
        """
        分析师预期因子：一致预期上调的股票得分高

        使用一致预期修正方向和覆盖机构数
        """
        eps_forecast_change = self._safe_float(stock.get("eps_forecast_change", 0))  # 百分比
        analyst_count = self._safe_float(stock.get("analyst_count", 0))

        score = 0
        # 预期上调
        score += min(100, max(0, 50 + eps_forecast_change * 5)) * 0.6
        # 覆盖机构越多越可靠
        score += min(100, analyst_count * 10) * 0.4

        return FactorScore(
            name="analyst",
            raw_value=eps_forecast_change,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="预期上修做多",
            weight=self.factor_weights.get("analyst", 0.04),
        )

    # ── v5.0 新增因子 ──────────────────────────────

    def calc_moat_factor(self, stock: Dict) -> FactorScore:
        """
        护城河因子（v5.0 新增）：
        - 优先使用预计算的 moat_score（来自 value_investing.moat.MoatAnalyzer）
        - 无预计算值时用毛利率 + ROE 稳定性代理
        """
        # 优先使用预计算的护城河评分
        moat_score = self._safe_float(stock.get("moat_score", 0))
        if moat_score > 0:
            return FactorScore(
                name="moat",
                raw_value=moat_score,
                z_score=0,
                percentile=0,
                score=round(moat_score, 1),
                direction="护城河做多",
                weight=self.factor_weights.get("moat", 0.15),
            )

        # 兜底：用毛利率 + ROE 代理
        gross_margin = self._safe_float(stock.get("gross_margin", 0))
        roe = self._safe_float(stock.get("roe", 0))
        # 毛利率 >40% 高分；ROE >15% 高分
        gm_score = max(0, min(100, (gross_margin - 10) / 30 * 100)) if gross_margin > 0 else 50
        roe_score = max(0, min(100, roe * 4)) if roe > 0 else 50
        score = gm_score * 0.6 + roe_score * 0.4

        return FactorScore(
            name="moat",
            raw_value=gross_margin,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="护城河代理",
            weight=self.factor_weights.get("moat", 0.15),
        )

    def calc_financial_health_factor(self, stock: Dict) -> FactorScore:
        """
        财务健康因子（v5.0 新增）：
        - 优先使用预计算的 health_score（来自 value_investing.financial_health）
        - 无预计算值时用资产负债率 + ROA 代理
        """
        health_score = self._safe_float(stock.get("health_score", 0))
        if health_score > 0:
            return FactorScore(
                name="financial_health",
                raw_value=health_score,
                z_score=0,
                percentile=0,
                score=round(health_score, 1),
                direction="财务健康做多",
                weight=self.factor_weights.get("financial_health", 0.12),
            )

        # 兜底：用资产负债率 + 流动比率代理
        debt_ratio = self._safe_float(stock.get("debt_ratio", 0))
        roe = self._safe_float(stock.get("roe", 0))
        # 资产负债率 <30% 高分；>70% 低分
        if debt_ratio < 30:
            solvency_score = 90
        elif debt_ratio < 50:
            solvency_score = 70
        elif debt_ratio < 70:
            solvency_score = 50
        else:
            solvency_score = 20
        # ROE >15% 加分
        quality_score = max(0, min(100, roe * 4)) if roe > 0 else 50
        score = solvency_score * 0.6 + quality_score * 0.4

        return FactorScore(
            name="financial_health",
            raw_value=debt_ratio,
            z_score=0,
            percentile=0,
            score=round(score, 1),
            direction="财务健康代理",
            weight=self.factor_weights.get("financial_health", 0.12),
        )

    # ── 综合评分 ──────────────────────────────────

    @staticmethod
    def _recommend_for_score(composite: float) -> str:
        """根据综合得分给出投资建议"""
        if composite >= 75:
            return "强烈推荐"
        elif composite >= 65:
            return "推荐关注"
        elif composite >= 50:
            return "中性"
        elif composite >= 35:
            return "谨慎"
        else:
            return "回避"

    def score_single_stock(self, stock: Dict) -> StockFactorReport:
        """
        对单只股票进行因子评分

        Args:
            stock: 股票数据字典
                {
                    "symbol": "600519",
                    "name": "贵州茅台",
                    "pe": 30.5, "pb": 12.3,
                    "roe": 25.6, "gross_margin": 92,
                    "debt_ratio": 21,
                    "mcap": 22000,  # 亿元
                    "ret_20d": 5.2, "ret_60d": -3.1,
                    "eps_growth": 15.0, "revenue_growth": 12.0,
                    "volatility": 28, "turnover": 0.5,
                    "eps_forecast_change": 2.0, "analyst_count": 30,
                }

        Returns:
            StockFactorReport: 因子分析报告
        """
        factors = {}

        # 计算各因子（v5.0: 新增 moat + financial_health）
        factors["value"] = self.calc_value_factor(stock)
        factors["momentum"] = self.calc_momentum_factor(stock)
        factors["quality"] = self.calc_quality_factor(stock)
        factors["size"] = self.calc_size_factor(stock)
        factors["growth"] = self.calc_growth_factor(stock)
        factors["low_vol"] = self.calc_low_vol_factor(stock)
        factors["turnover"] = self.calc_turnover_factor(stock)
        factors["analyst"] = self.calc_analyst_factor(stock)
        factors["moat"] = self.calc_moat_factor(stock)
        factors["financial_health"] = self.calc_financial_health_factor(stock)

        # 加权综合得分
        composite = sum(
            f.score * f.weight for f in factors.values()
        )

        # 确定推荐
        recommendation = self._recommend_for_score(composite)

        return StockFactorReport(
            symbol=stock.get("symbol", ""),
            name=stock.get("name", ""),
            composite_score=round(composite, 1),
            percentile_rank=0,  # 在批量评分时计算
            factors=factors,
            recommendation=recommendation,
        )

    def score_stocks(self, stock_list: List[Dict]) -> List[StockFactorReport]:
        """
        批量评分

        样本数 >= 3 时对各因子得分做横截面 Z-Score 标准化
        （MAD 去极值，见 _cross_section_zscore），综合得分改为
        加权 Z 值的映射 50 + 10·Σ(w·z)（截断到 0-100）；
        样本不足时保留单股启发式分数。

        Args:
            stock_list: 股票数据列表

        Returns:
            List[StockFactorReport]: 按综合得分降序排列的报告列表
        """
        reports = []
        for stock in stock_list:
            report = self.score_single_stock(stock)
            reports.append(report)

        # 横截面标准化：填充各因子的 z_score / percentile，
        # 并用标准化后的加权 Z 值重算综合得分
        if len(reports) >= 3:
            factor_names = list(self.factor_weights.keys())
            z_by_factor = {}
            for fn in factor_names:
                vals = [r.factors[fn].score for r in reports]
                zs = self._cross_section_zscore(vals)
                ps = self._percentile_rank(vals)
                for r, z, p in zip(reports, zs, ps):
                    r.factors[fn].z_score = round(z, 4)
                    r.factors[fn].percentile = round(p, 2)
                z_by_factor[fn] = zs
            for idx, r in enumerate(reports):
                z_comp = sum(
                    z_by_factor[fn][idx] * self.factor_weights.get(fn, 0)
                    for fn in factor_names
                )
                r.composite_score = round(max(0.0, min(100.0, 50 + 10 * z_comp)), 1)
                r.recommendation = self._recommend_for_score(r.composite_score)

        # 计算横截面排名百分位
        scores = [r.composite_score for r in reports]
        percentiles = self._percentile_rank(scores)
        for r, p in zip(reports, percentiles):
            r.percentile_rank = round(p, 1)

        # 按得分降序排列
        reports.sort(key=lambda x: x.composite_score, reverse=True)

        return reports

    def get_top_stocks(
        self, reports: List[StockFactorReport], n: int = 20
    ) -> List[StockFactorReport]:
        """获取得分最高的 N 只股票"""
        sorted_reports = sorted(
            reports, key=lambda x: x.composite_score, reverse=True
        )
        return sorted_reports[:n]

    def get_factor_exposure_report(
        self, reports: List[StockFactorReport]
    ) -> Dict:
        """
        生成因子暴露报告

        Returns:
            Dict: 各因子的得分统计（均值、中位数、标准差）
        """
        factor_names = list(self.factor_weights.keys())
        stats = {}

        for fn in factor_names:
            scores = []
            for r in reports:
                f = r.factors.get(fn)
                if f:
                    scores.append(f.score)

            if scores:
                arr = np.array(scores)
                stats[fn] = {
                    "mean": round(arr.mean(), 1),
                    "median": round(np.median(arr), 1),
                    "std": round(arr.std(), 1),
                    "min": round(arr.min(), 1),
                    "max": round(arr.max(), 1),
                    "weight": self.factor_weights.get(fn, 0),
                    "desc": self.FACTOR_DESCRIPTIONS.get(fn, ""),
                }

        return stats

    def to_markdown(self, report: StockFactorReport) -> str:
        """将单个报告转为 Markdown 格式"""
        lines = [
            f"## {report.symbol} {report.name} 因子分析",
            f"",
            f"| 项目 | 数值 |",
            f"|------|------|",
            f"| 综合得分 | {report.composite_score:.1f} / 100 |",
            f"| 市场排名 | 前 {100 - report.percentile_rank:.1f}% |",
            f"| 投资建议 | **{report.recommendation}** |",
            f"",
            f"### 因子明细",
            f"",
            f"| 因子 | 得分 | 权重 | 贡献 | 方向 |",
            f"|------|------|------|------|------|",
        ]

        for name, factor in report.factors.items():
            contribution = factor.score * factor.weight
            lines.append(
                f"| {factor.name} | {factor.score:.1f} | "
                f"{factor.weight:.0%} | {contribution:.1f} | "
                f"{factor.direction} |"
            )

        return "\n".join(lines)


def demo():
    """演示因子分析"""
    analyzer = FactorAnalyzer()

    # 模拟股票池
    stocks = [
        {
            "symbol": "600519", "name": "贵州茅台",
            "pe": 30, "pb": 12, "roe": 30, "gross_margin": 92,
            "debt_ratio": 21, "mcap": 22000,
            "ret_20d": 5, "ret_60d": -2,
            "eps_growth": 15, "revenue_growth": 18,
            "volatility": 28, "turnover": 0.5,
            "eps_forecast_change": 2, "analyst_count": 35,
        },
        {
            "symbol": "000858", "name": "五粮液",
            "pe": 25, "pb": 8, "roe": 25, "gross_margin": 75,
            "debt_ratio": 18, "mcap": 8000,
            "ret_20d": 8, "ret_60d": 15,
            "eps_growth": 12, "revenue_growth": 10,
            "volatility": 32, "turnover": 1.2,
            "eps_forecast_change": 5, "analyst_count": 28,
        },
    ]

    reports = analyzer.score_stocks(stocks)
    for r in reports:
        print(analyzer.to_markdown(r))
        print()

    # 因子暴露报告
    exposure = analyzer.get_factor_exposure_report(reports)
    print("## 因子暴露统计")
    for fn, stats in exposure.items():
        print(f"  {fn}: 均值={stats['mean']}, 中位数={stats['median']}")


if __name__ == "__main__":
    demo()


# ============================================================
# v3.1.0 增量 — 行业中性化 / IC 信息系数 / 因子相关矩阵
# ============================================================

def calc_industry_neutral_scores(stocks, factor_key, industry_key='industry'):
    """对单因子做行业内中性化（demean by industry），返回调整后的 z-score 列表。

    Args:
        stocks: 股票列表，每项含 factor_key 与 industry_key
        factor_key: 因子字段名
        industry_key: 行业字段名

    Returns:
        list[float]: 中性化后的 z-score
    """
    from collections import defaultdict
    buckets = defaultdict(list)
    for s in stocks:
        v = FactorAnalyzer._safe_float(s.get(factor_key, 0))
        ind = str(s.get(industry_key, 'unknown') or 'unknown')
        buckets[ind].append(v)

    # 每行业内 z-score
    neutral = []
    for s in stocks:
        ind = str(s.get(industry_key, 'unknown') or 'unknown')
        vals = buckets[ind]
        if len(vals) < 2:
            neutral.append(0.0)
            continue
        arr = np.array(vals, dtype=float)
        mu = float(arr.mean())
        sd = float(arr.std())
        v = FactorAnalyzer._safe_float(s.get(factor_key, 0))
        neutral.append((v - mu) / sd if sd > 0 else 0.0)
    return neutral


def calc_ic(stocks, factor_key, forward_returns, industry_key='industry'):
    """IC（Information Coefficient）— 因子值与下期收益的 Spearman 相关系数。

    支持全市场 IC 与 按行业计算的 IC-均值（IC Mean across industries）。

    Returns:
        dict: ic_all, ic_industry_mean, ic_ir, ic_std, n
    """
    n = min(len(stocks), len(forward_returns))
    if n < 5:
        return {'ic_all': 0.0, 'ic_industry_mean': 0.0, 'ic_ir': 0.0, 'ic_std': 0.0, 'n': n}

    fvals = np.array([FactorAnalyzer._safe_float(stocks[i].get(factor_key, 0))
                      for i in range(n)], dtype=float)
    rets = np.array([FactorAnalyzer._safe_float(forward_returns[i]) for i in range(n)],
                    dtype=float)

    # 全市场 IC: Spearman
    fr = np.argsort(np.argsort(fvals))
    rr = np.argsort(np.argsort(rets))
    if fr.std() > 0 and rr.std() > 0:
        ic_all = float(np.corrcoef(fr, rr)[0, 1])
    else:
        ic_all = 0.0

    # 行业内 IC
    industries = [str(stocks[i].get(industry_key, '') or '') for i in range(n)]
    by_ind = {}
    for i in range(n):
        by_ind.setdefault(industries[i], []).append(i)
    ic_by_ind = []
    ic_by_industry = {}
    for ind, idxs in by_ind.items():
        if len(idxs) < 5:
            continue
        f_sub = fvals[idxs]
        r_sub = rets[idxs]
        fr_s = np.argsort(np.argsort(f_sub))
        rr_s = np.argsort(np.argsort(r_sub))
        if fr_s.std() > 0 and rr_s.std() > 0:
            ic_v = float(np.corrcoef(fr_s, rr_s)[0, 1])
            ic_by_ind.append(ic_v)
            ic_by_industry[ind] = round(ic_v, 4)  # 循环内按键构建，避免错位
    ic_ind_mean = float(np.mean(ic_by_ind)) if ic_by_ind else ic_all
    ic_ind_std = float(np.std(ic_by_ind)) if ic_by_ind else 0.0
    ic_ir = ic_ind_mean / ic_ind_std if ic_ind_std > 1e-9 else 0.0

    return {
        'ic_all': round(ic_all, 4),
        'ic_industry_mean': round(ic_ind_mean, 4),
        'ic_ir': round(ic_ir, 4),
        'ic_std': round(ic_ind_std, 4),
        'ic_by_industry': ic_by_industry,
        'n': n,
    }


def factor_correlation_matrix(stocks, factor_keys, industry_key='industry',
                               neutralize=True):
    """返回因子间的相关系数矩阵（横截面 Spearman）。

    建议传入至少 10 只股票；可选 neutralize=True 先做行业内中性化。
    """
    if len(stocks) < 3:
        return {'keys': factor_keys, 'matrix': []}
    n = len(stocks)
    mat = []
    for k1 in factor_keys:
        v1 = []
        for k2 in factor_keys:
            a = np.array([FactorAnalyzer._safe_float(s.get(k1, 0)) for s in stocks])
            b = np.array([FactorAnalyzer._safe_float(s.get(k2, 0)) for s in stocks])
            if neutralize:
                a = np.array(calc_industry_neutral_scores(stocks, k1, industry_key))
                b = np.array(calc_industry_neutral_scores(stocks, k2, industry_key))
            ra = np.argsort(np.argsort(a))
            rb = np.argsort(np.argsort(b))
            if ra.std() > 0 and rb.std() > 0:
                v1.append(round(float(np.corrcoef(ra, rb)[0, 1]), 4))
            else:
                v1.append(0.0)
        mat.append(v1)
    return {'keys': list(factor_keys), 'matrix': mat, 'neutralized': neutralize, 'n': n}


def suggest_decile_weights(stocks, factor_key, forward_returns,
                            industry_key='industry', n_deciles=10):
    """基于十分位回测给出因子方向建议（做多高分位 / 做空低分位）。

    Returns:
        dict: long_decile, short_decile, long_short_return, mono_score
    """
    n = min(len(stocks), len(forward_returns))
    if n < n_deciles * 3:
        return {'error': '样本不足'}
    f = np.array([FactorAnalyzer._safe_float(stocks[i].get(factor_key, 0))
                  for i in range(n)])
    r = np.array([FactorAnalyzer._safe_float(forward_returns[i]) for i in range(n)])
    order = np.argsort(f)
    decile_size = n // n_deciles
    deciles = [order[i * decile_size:(i + 1) * decile_size]
               for i in range(n_deciles)]
    avg_ret = [float(np.mean(r[idx])) for idx in deciles if len(idx) > 0]
    long_dec = avg_ret[-1]
    short_dec = avg_ret[0]
    mono = sum((avg_ret[i + 1] - avg_ret[i]) for i in range(len(avg_ret) - 1))
    return {
        'long_decile': round(long_dec, 4),
        'short_decile': round(short_dec, 4),
        'long_short': round(long_dec - short_dec, 4),
        'mono_score': round(mono, 4),
        'avg_by_decile': [round(v, 4) for v in avg_ret],
    }
