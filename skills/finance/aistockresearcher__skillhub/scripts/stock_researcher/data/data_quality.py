# -*- coding: utf-8 -*-
"""数据质量标记模块 (v7.2 新增)
=============================
统一标记体系中所有数据字段的来源质量，让用户和下游模块能区分：
  - actual:      来自API/数据源的真实数据
  - derived:     从真实数据通过公式派生的（如 OPERATE_COST = revenue × (1 - margin)）
  - estimated:   估算值（如 PE分位经验映射、25%税率假设）
  - unavailable: 数据不可得（如东财API不返回的 FINANCE_EXPENSE）

用法:
    from data.data_quality import DataQuality, mark_field, QualityTag

    result = {
        "pe": mark_field(15.2, DataQuality.ACTUAL, "腾讯财经"),
        "pe_percentile": mark_field(35.0, DataQuality.ESTIMATED, "经验映射", "无历史PE序列"),
        "finance_expense": mark_field(0, DataQuality.UNAVAILABLE, "", "东财API不返回此字段"),
    }
    # 展现在报告中时:
    # PE: 15.2  | PE分位: 35.0(估算)  | 财务费用: 数据不可得
"""
from __future__ import annotations
from typing import Dict, Any, Optional


class DataQuality:
    """数据质量等级"""
    ACTUAL = "actual"            # 真实数据（来自API）
    DERIVED = "derived"          # 派生数据（公式计算）
    ESTIMATED = "estimated"      # 估算值（假设/映射）
    UNAVAILABLE = "unavailable"  # 数据不可得


def mark_field(value: Any, quality: str,
               source: str = "", note: str = "") -> Dict[str, Any]:
    """包装数据值，附加质量标记。

    Args:
        value: 数据值
        quality: DataQuality 等级
        source: 数据来源（如 "腾讯财经"/"东财API"）
        note: 备注（如 "假设25%税率"）

    Returns:
        {"value": ..., "quality": "actual", "source": "...", "note": "..."}
    """
    return {"value": value, "quality": quality, "source": source, "note": note}


def is_estimated(data: Any) -> bool:
    """检查数据是否为估算值。"""
    if isinstance(data, dict) and "quality" in data:
        return data["quality"] == DataQuality.ESTIMATED
    return False


def is_unavailable(data: Any) -> bool:
    """检查数据是否不可得。"""
    if isinstance(data, dict) and "quality" in data:
        return data["quality"] == DataQuality.UNAVAILABLE
    return False


def unwrap(data: Any, default: Any = None) -> Any:
    """从 QualityTag 中提取原始值。"""
    if isinstance(data, dict) and "value" in data:
        return data["value"]
    return data if data is not None else default


def build_quality_report(fields: Dict[str, Any]) -> Dict[str, Any]:
    """从一组标记字段生成数据质量报告。

    Returns:
        {"actual_count": 5, "derived_count": 2, "estimated_count": 1,
         "unavailable_count": 3, "estimated_fields": [...], "unavailable_fields": [...]}
    """
    counts = {"actual": 0, "derived": 0, "estimated": 0, "unavailable": 0}
    estimated_fields = []
    unavailable_fields = []

    for name, val in fields.items():
        if isinstance(val, dict) and "quality" in val:
            q = val["quality"]
            counts[q] = counts.get(q, 0) + 1
            if q == DataQuality.ESTIMATED:
                estimated_fields.append(name)
            elif q == DataQuality.UNAVAILABLE:
                unavailable_fields.append(name)

    return {
        "actual_count": counts["actual"],
        "derived_count": counts["derived"],
        "estimated_count": counts["estimated"],
        "unavailable_count": counts["unavailable"],
        "estimated_fields": estimated_fields,
        "unavailable_fields": unavailable_fields,
        "overall_quality": (
            "🟢 高" if counts["estimated"] + counts["unavailable"] == 0
            else "🟡 中" if counts["estimated"] + counts["unavailable"] <= 3
            else "🔴 低"
        ),
    }
