#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.4 高级基金筛选器 (AdvancedFundScreener)
============================================
多因子加权筛选:业绩 / 风险 / 经理 / 风格 / 费率 5 维评分,综合得分排序 Top N。

设计要点:
  - 不依赖外部数据,接收上游传入的 fund_metrics 字典列表(均已归一化为 0~100 分)
  - 支持自定义过滤条件(sharpe>=X、max_drawdown<=Y、manager_years>=Z 等)
  - 综合得分 = 业绩30% + 风险25% + 经理20% + 风格15% + 费率10%
  - 失败优雅降级:缺失字段用中位值(50)兜底,不抛错
  - 支持批量筛选(LRU 缓存 5 分钟)

输入 schema (fund_metrics):
    {
      "code": "110022",
      "name": "易方达蓝筹精选",
      "category": "偏股混合",
      "performance": {...},  # 业绩因子(子类字典或单项)
      "risk": {...},
      "manager": {...},
      "style": {...},
      "fee": {...},
      "performance_score": 80,  # 或者直接给 0~100 综合分
      ...
    }
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

SKILL_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_DIR / "scripts"))


# 5 维默认权重(总和 1.0)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "performance": 0.30,
    "risk": 0.25,
    "manager": 0.20,
    "style": 0.15,
    "fee": 0.10,
}

# 默认过滤条件(可被 None/空 dict 覆盖)
DEFAULT_FILTERS: Dict[str, Tuple[str, float]] = {
    # key: (operator, threshold)  operator: '>=' / '<=' / '>' / '<'
    "sharpe_3y": (">=", 0.5),
    "max_drawdown_3y": ("<=", 0.30),
    "manager_years": (">=", 3.0),
}


class AdvancedFundScreener:
    """v7.4 多因子基金筛选器"""

    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 filters: Optional[Dict[str, Tuple[str, float]]] = None,
                 top_n: int = 10,
                 cache_ttl_seconds: int = 300):
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}
        self.filters = filters or DEFAULT_FILTERS
        self.top_n = top_n
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_ttl = cache_ttl_seconds

    def screen(self,
               funds: List[Dict[str, Any]],
               filters: Optional[Dict[str, Tuple[str, float]]] = None,
               weights: Optional[Dict[str, float]] = None,
               top_n: Optional[int] = None,
               ascending: bool = False) -> List[Dict[str, Any]]:
        """筛选 + 综合评分 + 排序 Top N

        Args:
            funds: 基金指标字典列表
            filters: 自定义过滤条件(覆盖默认)
            weights: 自定义权重(覆盖默认)
            top_n: 返回 Top N(None 用 self.top_n)
            ascending: 是否升序(False=综合分高→低)

        Returns:
            Top N 基金列表,每条含原数据 + composite_score + ranking
        """
        cache_key = self._make_cache_key(funds, filters, weights, top_n, ascending)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        effective_filters = filters or self.filters
        effective_weights = weights or self.weights
        n = top_n if top_n is not None else self.top_n

        # 1) 过滤
        passed = [f for f in funds if self._passes_filter(f, effective_filters)]
        # 2) 综合评分
        for f in passed:
            f["composite_score"] = self._compute_composite(f, effective_weights)
        # 3) 排序 + Top N
        passed.sort(key=lambda x: x.get("composite_score", 0), reverse=not ascending)
        top = passed[:n]
        # 4) 加排名
        for rank, f in enumerate(top, 1):
            f["ranking"] = rank
        result = list(top)  # copy

        self._cache_set(cache_key, result)
        return result

    def screen_simple(self, funds: List[Dict[str, Any]],
                      category: Optional[str] = None,
                      top_n: int = 5) -> List[Dict[str, Any]]:
        """便捷接口:按类别筛选 + 综合评分 Top N

        Args:
            funds: 基金列表
            category: 基金类别(如 "偏股混合"),None=不过滤
            top_n: 前 N 名

        Returns:
            Top N 基金列表(含 composite_score)
        """
        pool = funds
        if category:
            pool = [f for f in funds if f.get("category") == category]
        return self.screen(pool, top_n=top_n)

    # ===== 评分 / 过滤 =====

    def _compute_composite(self, fund: Dict[str, Any],
                            weights: Dict[str, float]) -> float:
        """计算综合得分(0~100)。

        优先读 fund.performance_score / fund.risk_score 等综合分,
        否则从子类字典里聚合。
        """
        scores: Dict[str, float] = {}
        for dim in ("performance", "risk", "manager", "style", "fee"):
            # 1) 直接综合分
            direct_key = f"{dim}_score"
            if direct_key in fund:
                scores[dim] = self._clamp_score(fund[direct_key])
                continue
            # 2) 子类字典聚合
            sub = fund.get(dim, {})
            if isinstance(sub, dict):
                scores[dim] = self._aggregate_subscore(sub)
            else:
                scores[dim] = 50.0  # 兜底中位值
        # 加权求和
        total = sum(scores.get(d, 50) * weights.get(d, 0) for d in weights)
        return round(self._clamp_score(total), 2)

    def _aggregate_subscore(self, sub: Dict[str, Any]) -> float:
        """从子类字典中聚合分数。子字段值要么是 0~100 数字,要么是 (value, score) 元组。"""
        values: List[float] = []
        for k, v in sub.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if 0 <= v <= 100:
                    values.append(float(v))
                # 否则忽略(非分数字段)
            elif isinstance(v, tuple) and len(v) == 2:
                _, score = v
                if isinstance(score, (int, float)) and 0 <= score <= 100:
                    values.append(float(score))
        if not values:
            return 50.0
        return sum(values) / len(values)

    def _passes_filter(self, fund: Dict[str, Any],
                        filters: Dict[str, Tuple[str, float]]) -> bool:
        """判断单只基金是否满足过滤条件。

        字段查找路径:fund.metrics.<key> → fund.<key> → 0(不通过)。
        """
        if not filters:
            return True
        metrics = fund.get("metrics", {}) or {}
        for key, (op, threshold) in filters.items():
            # 字段查找:metrics 子字典 > fund 顶层
            value = metrics.get(key, fund.get(key))
            if value is None:
                return False  # 必填字段缺失 → 不通过
            try:
                value = float(value)
            except (TypeError, ValueError):
                return False
            if op == ">=" and not (value >= threshold):
                return False
            if op == "<=" and not (value <= threshold):
                return False
            if op == ">" and not (value > threshold):
                return False
            if op == "<" and not (value < threshold):
                return False
        return True

    @staticmethod
    def _clamp_score(v: Any) -> float:
        """截断到 [0, 100]。"""
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 50.0
        return max(0.0, min(100.0, v))

    # ===== 缓存 =====

    def _make_cache_key(self, funds: List[Dict], filters, weights, top_n,
                         ascending: bool) -> str:
        # 用前 3 只基金 + 列表长度作为数据指纹,避免完整序列化
        sample = tuple(sorted(f.get("code", "") for f in funds[:3]))
        return f"{len(funds)}:{sample}:{top_n}:{ascending}:{hash(str(filters))}:{hash(str(weights))}"

    def _cache_get(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
        return None

    def _cache_set(self, key: str, value):
        self._cache[key] = (time.time(), value)

    def clear_cache(self):
        self._cache.clear()


# ===== 便捷函数 =====

def quick_screen(funds: List[Dict[str, Any]],
                  category: Optional[str] = None,
                  top_n: int = 10) -> List[Dict[str, Any]]:
    """便捷函数:快速筛选 Top N。"""
    return AdvancedFundScreener(top_n=top_n).screen_simple(funds, category=category, top_n=top_n)