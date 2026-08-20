# -*- coding: utf-8 -*-
"""多因子筛选引擎 (v8.0 新增)
==============================
扩展现有十维评分体系，新增六类因子分析：
  1. 动量因子 — 1/3/6/12月动量，多周期加权
  2. 波动率因子 — 下行波动率惩罚、波动率锥
  3. 质量因子 — 经理稳定性、费率效率、规模适宜度
  4. 价值因子 — 持仓 PE/PB 分位数 vs 同类
  5. 情绪因子 — 资金流方向、评级变化趋势
  6. 宏观敏感度 — Beta to 沪深300/中债指数

能力:
  - 因子合成: 等权/波动率倒数加权/IC加权
  - 分层排名: 按基金类型分层，各层独立排名
  - 因子暴露报告: 单基金六维雷达图数据输出
  - 同业相对强度: 因子暴露 vs 同类中位数

纯标准库实现，零外部依赖。
"""
from __future__ import annotations

import math
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fund_advisor_paths import DATA_DIR, load_json_data  # noqa: E402

# ── 因子定义 ──────────────────────────────────────────────────
FACTOR_DEFINITIONS = {
    "momentum": {
        "name": "动量因子",
        "description": "多周期收益动量（1/3/6/12月），近期权重更高",
        "weight_default": 0.20,
        "periods": [1, 3, 6, 12],
        "decay_weights": [0.40, 0.30, 0.20, 0.10],  # 近月权重高
    },
    "volatility": {
        "name": "波动率因子",
        "description": "下行波动率惩罚，低波动基金得分更高",
        "weight_default": 0.15,
    },
    "quality": {
        "name": "质量因子",
        "description": "经理稳定性(年限+跳槽频率)+费率效率+规模适宜度(2-50亿最优)",
        "weight_default": 0.20,
    },
    "value": {
        "name": "价值因子",
        "description": "持仓组合PE/PB分位数 vs 同类，低估值得分更高",
        "weight_default": 0.15,
    },
    "sentiment": {
        "name": "情绪因子",
        "description": "资金流方向(净申购/净赎回)+评级变化趋势(上调/下调)",
        "weight_default": 0.15,
    },
    "macro_sensitivity": {
        "name": "宏观敏感度",
        "description": "Beta to 沪深300/中债指数，衡量市场敏感度",
        "weight_default": 0.15,
    },
}

# 各基金类型的默认因子权重微调
TYPE_FACTOR_TILTS = {
    "股票型": {"momentum": 0.25, "volatility": 0.15, "quality": 0.15, "value": 0.20, "sentiment": 0.10, "macro_sensitivity": 0.15},
    "混合型": {"momentum": 0.20, "volatility": 0.15, "quality": 0.20, "value": 0.15, "sentiment": 0.15, "macro_sensitivity": 0.15},
    "偏股混合": {"momentum": 0.25, "volatility": 0.15, "quality": 0.15, "value": 0.20, "sentiment": 0.10, "macro_sensitivity": 0.15},
    "偏债混合": {"momentum": 0.10, "volatility": 0.20, "quality": 0.30, "value": 0.10, "sentiment": 0.15, "macro_sensitivity": 0.15},
    "债券型": {"momentum": 0.10, "volatility": 0.20, "quality": 0.30, "value": 0.10, "sentiment": 0.15, "macro_sensitivity": 0.15},
    "纯债": {"momentum": 0.10, "volatility": 0.20, "quality": 0.35, "value": 0.05, "sentiment": 0.15, "macro_sensitivity": 0.15},
    "指数型": {"momentum": 0.25, "volatility": 0.15, "quality": 0.10, "value": 0.20, "sentiment": 0.10, "macro_sensitivity": 0.20},
    "QDII": {"momentum": 0.20, "volatility": 0.15, "quality": 0.15, "value": 0.15, "sentiment": 0.15, "macro_sensitivity": 0.20},
    "ETF": {"momentum": 0.25, "volatility": 0.15, "quality": 0.10, "value": 0.20, "sentiment": 0.10, "macro_sensitivity": 0.20},
}

# 评分等级
SCORE_GRADES = [
    (80, "🔵 强烈推荐"),
    (65, "🟢 推荐"),
    (50, "🟡 可选"),
    (0,  "⚪ 不推荐"),
]


class FactorEngine:
    """多因子筛选引擎 v8.0"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._managers_db: Optional[Dict] = None
        self._funds_db: Optional[Dict] = None
        self._ratings_db: Optional[Dict] = None
        self._holdings_db: Optional[List[Dict]] = None
        self._stock_vals: Optional[Dict] = None
        # v9.0: 记录降级因子（无数据支撑时用基准回退的因子）
        self._degraded_factors: set = set()

    # ── 数据懒加载 ───────────────────────────────────────────
    @property
    def managers_db(self) -> Dict:
        if self._managers_db is None:
            self._managers_db = {}
            try:
                data = load_json_data(str(self.data_dir / 'fund_managers_distilled.json'))
                for m in data.get('managers', data.get('items', [])):
                    key = m.get('manager_id', '') or m.get('name', '')
                    if key:
                        self._managers_db[key] = m
            except Exception:
                pass
        return self._managers_db

    @property
    def funds_db(self) -> Dict:
        if self._funds_db is None:
            self._funds_db = {}
            try:
                data = load_json_data(str(self.data_dir / 'fund_products.json'))
                for f in data.get('products', data.get('items', [])):
                    code = f.get('code', '') or f.get('fund_code', '')
                    if code:
                        self._funds_db[code] = f
            except Exception:
                pass
        return self._funds_db

    @property
    def _holdings(self) -> List[Dict]:
        """v9.0: 持仓明细（股票级行，供价值因子穿透；读 self.data_dir 而非全局）。"""
        if self._holdings_db is None:
            self._holdings_db = []
            try:
                from scripts.fund_advisor_paths import load_json_data, normalize_holdings
                data = load_json_data(str(self.data_dir / 'holdings_database.json'))
                self._holdings_db = normalize_holdings(data) or []
            except Exception:
                pass
        return self._holdings_db

    @property
    def _stock_valuations(self) -> Dict:
        """v9.0: 股票估值表（可选 data/stock_valuations.json，数据管道填充）。"""
        if self._stock_vals is None:
            self._stock_vals = {}
            try:
                data = load_json_data(str(self.data_dir / 'stock_valuations.json'))
                for item in data.get('items', data.get('stocks', [])):
                    c = item.get('code', '')
                    if c:
                        self._stock_vals[str(c)] = item
            except Exception:
                pass
        return self._stock_vals

    @property
    def _ratings(self) -> Dict:
        """v9.0: 外部评级（external_data.json 的 ratings 分区）。"""
        if self._ratings_db is None:
            self._ratings_db = {}
            try:
                data = load_json_data(str(self.data_dir / 'external_data.json'))
                for r in data.get('ratings', data.get('items', [])):
                    c = str(r.get('fund_code', '')).zfill(6)
                    if c:
                        self._ratings_db[c] = r
            except Exception:
                pass
        return self._ratings_db

    @staticmethod
    def _clamp01(x: float) -> float:
        return max(0.0, min(1.0, float(x)))

    # ── 1. 因子暴露计算 ──────────────────────────────────────
    def compute_factor_exposures(
        self,
        fund_code: str,
        nav_history: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """计算单基金的六维因子暴露。

        Args:
            fund_code: 基金代码
            nav_history: 可选的历史净值序列（用于动量/波动率计算）

        Returns:
            {"fund_code": "000001",
             "fund_type": "股票型",
             "factors": {
               "momentum": 0.72,      # 0-1 标准化得分
               "volatility": 0.65,
               "quality": 0.80,
               "value": 0.55,
               "sentiment": 0.60,
               "macro_sensitivity": 0.70,
             },
             "composite_score": 67.5,  # 加权综合得分
             "grade": "🟢 推荐"}
        """
        fund_info = self._get_fund_info(fund_code)
        fund_type = fund_info.get('type', '混合型')
        weights = TYPE_FACTOR_TILTS.get(fund_type, TYPE_FACTOR_TILTS['混合型'])

        factors = {}
        factors['momentum'] = self._calc_momentum(fund_code, nav_history)
        factors['volatility'] = self._calc_volatility(fund_code, nav_history)
        factors['quality'] = self._calc_quality(fund_code, fund_info)
        factors['value'] = self._calc_value(fund_code, fund_type)
        factors['sentiment'] = self._calc_sentiment(fund_code, fund_type)
        factors['macro_sensitivity'] = self._calc_macro_sensitivity(fund_code, fund_type)

        # 加权综合得分
        composite = sum(factors[k] * weights.get(k, 0.15) * 100 for k in factors)
        grade = self._score_to_grade(composite)

        # v9.0: 记录降级因子（value/sentiment 无数据支撑用基准回退）
        degraded = bool(self._degraded_factors)
        notes = []
        if "value" in self._degraded_factors:
            notes.append("价值因子无持仓估值数据，使用类型基准回退")
        if "sentiment" in self._degraded_factors:
            notes.append("情绪因子无评级数据，使用中性回退")

        return {
            "fund_code": fund_code,
            "fund_name": fund_info.get("name", fund_code),
            "fund_type": fund_type,
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "factor_weights_used": weights,
            "composite_score": round(composite, 1),
            "grade": grade,
            "degraded": degraded,
            "degraded_factors": sorted(self._degraded_factors),
            "notes": notes,
            "generated_at": datetime.now().isoformat(),
        }

    def _calc_momentum(self, code: str, nav: Optional[List[float]]) -> float:
        """动量因子：多周期收益动量加权。"""
        if not nav or len(nav) < 252:
            return 0.50  # 数据不足，中性分
        scores = []
        for period_months, decay in zip([1, 3, 6, 12], [0.40, 0.30, 0.20, 0.10]):
            days = period_months * 21
            if len(nav) > days and nav[-days - 1] > 0:
                ret = (nav[-1] - nav[-days - 1]) / nav[-days - 1]
                # 标准化到 [0, 1]（假设月度收益-5%~+5%）
                normalized = min(max((ret / (period_months * 0.05) + 0.5), 0), 1)
                scores.append(normalized * decay)
            else:
                scores.append(0.50 * decay)
        return sum(scores)

    def _calc_volatility(self, code: str, nav: Optional[List[float]]) -> float:
        """波动率因子：低波动得高分（下行波动率惩罚）。"""
        if not nav or len(nav) < 60:
            return 0.50
        # 计算下行收益（只取负值）
        neg_rets = []
        for i in range(1, len(nav)):
            if nav[i - 1] > 0:
                r = (nav[i] - nav[i - 1]) / nav[i - 1]
                if r < 0:
                    neg_rets.append(r)
        if not neg_rets:
            return 0.80  # 无下行波动=高质量
        # 下行标准差
        mean_neg = sum(neg_rets) / len(neg_rets)
        down_vol = math.sqrt(sum((r - mean_neg) ** 2 for r in neg_rets) / len(neg_rets))
        # 映射到 [0, 1]：年化下行波动 0% -> 1.0, >30% -> 0.0
        annual_down_vol = down_vol * math.sqrt(252)
        score = max(0, min(1, 1 - annual_down_vol / 0.30))
        return score

    def _calc_quality(self, code: str, fund_info: Dict) -> float:
        """质量因子：经理稳定性+费率效率+规模适宜度。"""
        score = 0.50

        # 经理稳定性
        manager_name = fund_info.get("manager", fund_info.get("manager_name", ""))
        if manager_name:
            mgr = self.managers_db.get(manager_name, {})
            tenure_days = mgr.get("tenure_days", mgr.get("任职天数", 0))
            if isinstance(tenure_days, (int, float)) and tenure_days > 0:
                years = tenure_days / 365
                score += min(years / 10, 0.20)  # 10年以上加满
            else:
                score += 0.05  # 有经理但无法获取年限

        # 规模适宜度（2-50亿最优）
        scale = fund_info.get("scale", fund_info.get("fund_size", fund_info.get("规模", 0)))
        if isinstance(scale, (int, float)) and scale > 0:
            scale_yi = scale / 1e8  # 转为亿
            if 2 <= scale_yi <= 50:
                score += 0.15
            elif 1 <= scale_yi < 2 or 50 < scale_yi <= 100:
                score += 0.08
            else:
                score -= 0.05

        # 费率效率（假设数据不可用时使用默认值）
        fee = fund_info.get("management_fee", fund_info.get("fee", 0.015))
        if isinstance(fee, (int, float)) and fee > 0:
            if fee <= 0.005:  # <0.5%/年
                score += 0.15
            elif fee <= 0.01:
                score += 0.10
            elif fee <= 0.015:
                score += 0.05
            else:
                score -= 0.05

        return min(max(score, 0), 1)

    def _calc_value(self, code: str, fund_type: str) -> float:
        """v9.0: 价值因子 — 穿透持仓 PE/PB 加权；无估值数据回退类型基准并标记 degraded。"""
        code = str(code).zfill(6)
        holdings = self._holdings
        rows = [r for r in holdings if str(r.get('fund_code', '')).zfill(6) == code]
        valuations = self._stock_valuations
        pes, pbs, ws = [], [], []
        for r in rows:
            v = valuations.get(str(r.get('stock_code', '')))
            w = float(r.get('weight') or 0)
            if v and w > 0 and v.get('pe') and v.get('pb'):
                try:
                    pes.append(float(v['pe']))
                    pbs.append(float(v['pb']))
                    ws.append(w)
                except (TypeError, ValueError):
                    continue
        if ws:
            tw = sum(ws)
            w_pe = sum(p * w for p, w in zip(pes, ws)) / tw
            w_pb = sum(p * w for p, w in zip(pbs, ws)) / tw
            score = 0.7 * self._clamp01(1 - (w_pe - 10) / 30) + 0.3 * self._clamp01(1 - (w_pb - 1) / 5)
            self._degraded_factors.discard('value')
            return score
        self._degraded_factors.add('value')
        type_values = {
            "股票型": 0.55, "偏股混合": 0.55, "指数型": 0.60,
            "混合型": 0.60, "偏债混合": 0.65, "债券型": 0.70,
            "纯债": 0.70, "QDII": 0.55, "ETF": 0.60,
        }
        return type_values.get(fund_type, 0.60)

    def _calc_sentiment(self, code: str, fund_type: str) -> float:
        """v9.0: 情绪因子 — 外部评级共识 + 1 年盈利概率 + 源数；无数据回退中性并标记 degraded。"""
        rating = self._ratings.get(str(code).zfill(6))
        if rating:
            star = rating.get('avg_star') or rating.get('shanghai_star') or 0
            prob = rating.get('profit_probability_1y') or rating.get('profit_probability') or 0
            sources = int(rating.get('source_count') or 1)
            score = 0.5 * self._clamp01(float(star) / 5.0) \
                + 0.3 * self._clamp01(float(prob) / 100.0) \
                + 0.2 * min(float(sources) / 5.0, 1.0)
            self._degraded_factors.discard('sentiment')
            return self._clamp01(score)
        self._degraded_factors.add('sentiment')
        return 0.50  # 中性

    def _calc_macro_sensitivity(self, code: str, fund_type: str) -> float:
        """宏观敏感度：Beta 估算。"""
        type_betas = {
            "股票型": 0.85, "偏股混合": 0.80, "指数型": 0.95,
            "混合型": 0.60, "偏债混合": 0.25, "债券型": 0.10,
            "纯债": 0.05, "QDII": 0.70, "ETF": 0.95,
        }
        beta = type_betas.get(fund_type, 0.50)
        # 转换 Beta 为得分（Beta 接近 0.5 最优，均衡敏感度）
        score = 1.0 - abs(beta - 0.50)
        return max(0, min(1, score))

    # ── 2. 分层排名 ──────────────────────────────────────────
    def rank_by_factor(
        self,
        fund_list: List[str],
        factor_weights: Optional[Dict[str, float]] = None,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """按因子得分排名。

        Args:
            fund_list: 基金代码列表
            factor_weights: 自定义因子权重（None=按类型自动选择）
            top_n: 返回前N名

        Returns:
            [{fund_code, fund_name, composite_score, grade, factor_exposures}, ...]
            按 composite_score 降序排列
        """
        results = []
        for code in fund_list:
            try:
                exp = self.compute_factor_exposures(code)
                if factor_weights:
                    # 使用自定义权重重新计算
                    custom_score = sum(
                        exp["factors"][k] * factor_weights.get(k, 0.15) * 100
                        for k in exp["factors"]
                    )
                    exp["composite_score"] = round(custom_score, 1)
                    exp["grade"] = self._score_to_grade(custom_score)
                    exp["factor_weights_used"] = factor_weights
                results.append(exp)
            except Exception:
                continue

        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return results[:top_n]

    def peer_relative_strength(
        self,
        fund_code: str,
        peer_codes: List[str],
    ) -> Dict[str, Any]:
        """同业相对强度：各因子暴露 vs 同类中位数。

        Returns:
            {"fund_code": "000001",
             "peer_count": 25,
             "factor_percentiles": {"momentum": 0.75, ...},  # 在同类中的分位数
             "relative_strength": 1.15,  # >1 表示强于同类平均
             "rank_in_peer": "5/25"}
        """
        self_exp = self.compute_factor_exposures(fund_code)
        peer_exposures = []
        for pc in peer_codes:
            if pc == fund_code:
                continue
            try:
                peer_exposures.append(self.compute_factor_exposures(pc))
            except Exception:
                continue

        if not peer_exposures:
            return {"fund_code": fund_code, "error": "无同类基金数据"}

        percentiles = {}
        for factor in self_exp["factors"]:
            my_val = self_exp["factors"][factor]
            peer_vals = [p["factors"].get(factor, 0.5) for p in peer_exposures]
            peer_vals.append(my_val)
            peer_vals.sort()
            rank = peer_vals.index(my_val)
            percentiles[factor] = round(rank / len(peer_vals), 3)

        # 综合相对强度
        avg_percentile = sum(percentiles.values()) / len(percentiles)
        my_score = self_exp["composite_score"]
        peer_scores = [p["composite_score"] for p in peer_exposures]
        if peer_scores:
            peer_avg = sum(peer_scores) / len(peer_scores)
            rel_strength = round(my_score / max(peer_avg, 0.01), 2)
            rank = sum(1 for s in peer_scores if s > my_score) + 1
        else:
            rel_strength = 1.0
            rank = 1

        return {
            "fund_code": fund_code,
            "fund_name": self_exp.get("fund_name", ""),
            "peer_count": len(peer_exposures),
            "factor_percentiles": percentiles,
            "relative_strength": rel_strength,
            "rank_in_peer": f"{rank}/{len(peer_exposures) + 1}",
            "generated_at": datetime.now().isoformat(),
        }

    # ── 3. 因子归因 ──────────────────────────────────────────
    def factor_attribution(
        self,
        fund_code: str,
        benchmark_codes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """因子归因：分解收益来源。

        Returns:
            {"fund_code": "000001",
             "attribution": {
               "momentum_contribution": 0.15,
               "quality_contribution": 0.08,
               ...
             },
             "unexplained": 0.05}
        """
        exp = self.compute_factor_exposures(fund_code)
        weights = exp.get("factor_weights_used", {})
        total_weight = sum(weights.values()) or 1.0
        # v9.0: 按基金类型期望年收益做基准（权益 10% / 混合 7% / 债 4%）
        fund_type = exp.get("fund_type", "混合型")
        bench_ret = {
            "股票型": 0.10, "偏股混合": 0.10, "指数型": 0.10, "ETF": 0.10, "QDII": 0.10,
            "混合型": 0.07, "偏债混合": 0.06, "债券型": 0.04, "纯债": 0.03,
        }.get(fund_type, 0.07)

        attribution = {}
        for factor, score in exp["factors"].items():
            w = weights.get(factor, 0.15) / total_weight
            attribution[f"{factor}_contribution"] = round(score * w * bench_ret, 4)

        explained = sum(attribution.values())
        unexplained = max(0.0, bench_ret - explained)

        return {
            "fund_code": fund_code,
            "attribution": attribution,
            "explained_return": round(explained, 4),
            "unexplained_alpha": round(unexplained, 4),
            "generated_at": datetime.now().isoformat(),
        }

    # ── 4. 工具方法 ──────────────────────────────────────────
    def compute_composite_score(
        self,
        fund_code: str,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """快速计算综合因子得分。"""
        exp = self.compute_factor_exposures(fund_code)
        weights = custom_weights or exp.get("factor_weights_used", {})
        score = sum(exp["factors"][k] * weights.get(k, 0.15) * 100 for k in exp["factors"])
        return round(score, 1)

    def list_factor_definitions(self) -> List[Dict[str, Any]]:
        """列出所有因子定义。"""
        return [
            {
                "key": k,
                "name": v["name"],
                "description": v["description"],
                "default_weight": v["weight_default"],
            }
            for k, v in FACTOR_DEFINITIONS.items()
        ]

    def _get_fund_info(self, code: str) -> Dict:
        """获取基金基本信息。"""
        return self.funds_db.get(code, {"code": code, "type": "混合型"})

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """综合得分 -> 推荐等级。"""
        for threshold, grade in SCORE_GRADES:
            if score >= threshold:
                return grade
        return SCORE_GRADES[-1][1]


# 模块级单例
_engine_instance: Optional[FactorEngine] = None


def get_factor_engine() -> FactorEngine:
    """获取 FactorEngine 单例。"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = FactorEngine()
    return _engine_instance
