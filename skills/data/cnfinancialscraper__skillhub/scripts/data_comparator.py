# -*- coding: utf-8 -*-
"""
data_comparator.py v1.0 — 同类数据横向对比与回测（v4.7 新增）
============================================================
对同类型的金融数据做：
  1. 横向对比 — 多组同类序列（如多只股票的两融、多只 ETF 的资金流）逐字段对比，
     输出最新值 / 均值 / 变化 / 排名。
  2. 数据回测 — 对每组序列校验数据质量：完整性、时间连续性、数值异常跳变、
     边界合理性，返回 0-100 质量评分与问题清单。

设计要点:
    - 纯标准库，零外部依赖
    - 泛化设计：接受任意 List[Dict] 序列，按数值字段自动识别
    - 严格时间过滤由上游数据函数保证，本模块聚焦对比与质量校验
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

log = logging.getLogger(__name__)

# 默认数值字段识别：排除常见非数值/标识字段
_NON_NUMERIC_KEYS = {
    "code", "name", "date", "market", "type", "title", "url", "person",
    "position", "reason", "buyer_branch", "seller_branch", "warning",
    "error", "update_time", "source", "curve_type", "id",
}


def _safe_float(val, default=0.0):
    if val is None:
        return default
    if isinstance(val, str) and val.strip() in ("-", "--", "", "—"):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _numeric_fields(records: List[Dict]) -> List[str]:
    """识别记录中的数值字段（排除标识类字段）。"""
    if not records:
        return []
    fields = []
    for key in records[0].keys():
        if key.lower() in _NON_NUMERIC_KEYS:
            continue
        if any(key.lower().startswith(p) for p in ("_", "spread_")):
            continue
        # 取最多 30 条样本判断是否数值型
        sample = [r.get(key) for r in records[:30]]
        numeric = 0
        for v in sample:
            if v is None or (isinstance(v, str) and v.strip() in ("-", "", "--")):
                continue
            try:
                float(v)
                numeric += 1
            except (ValueError, TypeError):
                break
        if numeric >= max(1, len(sample) // 2):
            fields.append(key)
    return fields


def _parse_date(d: str) -> Optional[str]:
    """规范化日期为 yyyy-MM-dd，失败返回 None。"""
    if not d:
        return None
    s = str(d)[:10].strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# ==================== 数据回测 ====================


def backtest_series(label: str, records: List[Dict],
                    date_key: str = "date",
                    value_fields: Optional[List[str]] = None,
                    jump_threshold: float = 5.0) -> Dict[str, Any]:
    """对单个数据序列做质量回测。

    校验维度:
        1. 完整性   — 记录数量、日期覆盖率
        2. 时间连续性 — 日期去重数、最大间隔（交易日/自然日）
        3. 数值异常  — 环比跳变超过阈值的记录
        4. 边界合理性 — 非正/缺失值占比

    Args:
        label: 序列名称（如 "600519 贵州茅台"）
        records: 记录列表，每项含 date 与数值字段
        date_key: 日期字段名
        value_fields: 指定数值字段；为空则自动识别
        jump_threshold: 环比跳变阈值（百分比），默认 500%（5.0 倍）

    Returns:
        {
            "label": str, "record_count": int,
            "score": int (0-100), "passed": bool,
            "issues": [ {level, field, message}, ... ],
            "by_dimension": {"completeness": {}, "continuity": {}, "numeric": {}, "boundary": {}},
            "fields_checked": [...],
        }
    """
    issues: List[Dict[str, str]] = []
    by_dim = {}

    n = len(records)
    if n == 0:
        return {
            "label": label, "record_count": 0, "score": 0, "passed": False,
            "issues": [{"level": "error", "field": date_key, "message": "无任何记录"}],
            "by_dimension": {}, "fields_checked": [],
        }

    fields = value_fields or _numeric_fields(records)
    score = 100
    dim = {}

    # 1) 完整性
    dates = [_parse_date(r.get(date_key, "")) for r in records]
    dates = [d for d in dates if d]
    unique_dates = len(set(dates))
    completeness_issues = []
    if unique_dates == 0:
        completeness_issues.append({"level": "error", "field": date_key, "message": "缺少有效日期字段"})
        score -= 30
    elif unique_dates < max(2, n):
        dup = n - unique_dates
        if dup > 0:
            completeness_issues.append({"level": "warn", "field": date_key, "message": f"存在 {dup} 条重复日期记录"})
            score -= max(0, min(dup * 2, 15))
    dim["completeness"] = {
        "record_count": n, "unique_dates": unique_dates, "issue_count": len(completeness_issues),
    }
    issues.extend(completeness_issues)

    # 2) 时间连续性（自然日间隔，跳过周末）
    continuity_issues = []
    if unique_dates >= 2:
        sorted_dates = sorted(set(dates))
        try:
            gaps = []
            for i in range(1, len(sorted_dates)):
                d1 = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
                d2 = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
                gaps.append((d2 - d1).days)
            # 排除周末/节假日（1天正常；>4天视为可能缺失）
            big_gaps = [g for g in gaps if g > 4]
            max_gap = max(gaps)
            if big_gaps:
                continuity_issues.append({
                    "level": "warn", "field": date_key,
                    "message": f"存在 {len(big_gaps)} 处超长间隔（最大 {max_gap} 天，可能缺数据）",
                })
                score -= min(len(big_gaps) * 5, 20)
            dim["continuity"] = {"span_days": (datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
                                               - datetime.strptime(sorted_dates[0], "%Y-%m-%d")).days,
                                 "max_gap_days": max_gap, "big_gaps": len(big_gaps)}
        except ValueError:
            pass
    issues.extend(continuity_issues)

    # 3) 数值异常跳变
    numeric_issues = []
    for f in fields:
        vals = [_safe_float(r.get(f)) for r in records]
        # 只对正数值做环比跳变检测
        for i in range(1, len(vals)):
            prev, cur = vals[i - 1], vals[i]
            if prev <= 0 or cur <= 0:
                continue
            ratio = abs(cur - prev) / abs(prev) * 100
            if ratio > jump_threshold * 100:
                numeric_issues.append({
                    "level": "warn", "field": f,
                    "message": f"第 {i + 1} 条相对上条跳变 {ratio:.1f}%（超 {jump_threshold * 100:.0f}%）",
                })
                score -= min(int(ratio // 100) * 3, 15)
                break  # 每字段最多报 1 条
    dim["numeric"] = {"fields": fields, "issue_count": len(numeric_issues)}
    issues.extend(numeric_issues)

    # 4) 边界合理性
    boundary_issues = []
    for f in fields:
        vals = [_safe_float(r.get(f)) for r in records]
        non_positive = sum(1 for v in vals if v <= 0)
        if non_positive > n * 0.5:
            boundary_issues.append({
                "level": "warn", "field": f,
                "message": f"超过 50% 的记录该字段为 0 或负值（{non_positive}/{n}），疑似异常",
            })
            score -= 10
    dim["boundary"] = {"issue_count": len(boundary_issues)}
    issues.extend(boundary_issues)

    # 汇总
    by_dim = dim
    score = max(0, min(100, score))
    return {
        "label": label,
        "record_count": n,
        "score": score,
        "passed": score >= 60,
        "issues": issues,
        "by_dimension": by_dim,
        "fields_checked": fields,
    }


# ==================== 横向对比 ====================


def compare_series(series_dict: Dict[str, List[Dict]],
                   date_key: str = "date",
                   value_fields: Optional[List[str]] = None,
                   limit: int = 50) -> Dict[str, Any]:
    """横向对比多组同类数据序列。

    Args:
        series_dict: {"标签": [记录列表], ...}，如 {"贵州茅台": [...两融...], "五粮液": [...]}
        date_key: 日期字段名
        value_fields: 指定数值字段；为空则取各组共同数值字段的并集
        limit: 每组取最近 N 条用于统计

    Returns:
        {
            "series_count": int, "common_fields": [...],
            "latest": {label: {field: 最新值}},        # 各序列最新值
            "change":  {label: {field: 环比变化}},      # 最新 vs 上一条
            "ranking": {field: [ {label, value, rank}, ... ]},  # 按最新值排名
            "per_series_stats": {label: {field: {latest, mean, min, max, change}}},
        }
    """
    if not series_dict:
        return {"series_count": 0, "common_fields": [], "latest": {}, "change": {}, "ranking": {}, "per_series_stats": {}}

    # 收集各组数值字段（并集）
    all_fields: List[str] = []
    for recs in series_dict.values():
        for f in (_numeric_fields(recs) if value_fields is None else value_fields):
            if f not in all_fields:
                all_fields.append(f)
    if value_fields:
        all_fields = [f for f in all_fields if f in value_fields] or all_fields

    latest: Dict[str, Dict[str, float]] = {}
    change: Dict[str, Dict[str, float]] = {}
    stats: Dict[str, Dict[str, Dict[str, float]]] = {}

    for label, recs in series_dict.items():
        recs = recs[-limit:] if limit else recs
        latest[label] = {}
        change[label] = {}
        stats[label] = {}
        for f in all_fields:
            vals = [_safe_float(r.get(f)) for r in recs]
            if not vals:
                continue
            latest_val = vals[-1]
            prev_val = vals[-2] if len(vals) > 1 else 0.0
            latest[label][f] = round(latest_val, 4)
            change[label][f] = round(latest_val - prev_val, 4) if len(vals) > 1 else None
            stats[label][f] = {
                "latest": round(latest_val, 4),
                "mean": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "change": change[label][f],
            }

    # 排名（按最新值降序）
    ranking: Dict[str, List[Dict[str, Any]]] = {}
    for f in all_fields:
        rows = []
        for label, recs in series_dict.items():
            vals = [_safe_float(r.get(f)) for r in (recs[-limit:] if limit else recs)]
            if not vals:
                continue
            rows.append({"label": label, "value": round(vals[-1], 4)})
        rows.sort(key=lambda x: x["value"], reverse=True)
        for i, row in enumerate(rows, 1):
            row["rank"] = i
        ranking[f] = rows

    return {
        "series_count": len(series_dict),
        "common_fields": all_fields,
        "latest": latest,
        "change": change,
        "ranking": ranking,
        "per_series_stats": stats,
    }


def compare_and_backtest(series_dict: Dict[str, List[Dict]],
                         date_key: str = "date",
                         value_fields: Optional[List[str]] = None,
                         jump_threshold: float = 5.0,
                         limit: int = 50) -> Dict[str, Any]:
    """一键：横向对比 + 数据回测。

    Args:
        series_dict: {"标签": [记录列表], ...}
        date_key: 日期字段名
        value_fields: 指定数值字段
        jump_threshold: 回测跳变阈值
        limit: 每组参与统计的最近条数

    Returns:
        {
            "comparison": {对比结果},
            "backtests": [ {回测结果}, ... ],
            "summary": {group_count, avg_score, best, worst},
        }
    """
    comparison = compare_series(series_dict, date_key, value_fields, limit)
    backtests = [
        backtest_series(label, recs, date_key, value_fields, jump_threshold)
        for label, recs in series_dict.items()
    ]

    scores = [b["score"] for b in backtests]
    summary = {
        "group_count": len(backtests),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "best": max(backtests, key=lambda b: b["score"]) if backtests else None,
        "worst": min(backtests, key=lambda b: b["score"]) if backtests else None,
    }
    # 精简 best/worst，避免嵌套过大
    if summary.get("best"):
        summary["best"] = {"label": summary["best"]["label"], "score": summary["best"]["score"]}
    if summary.get("worst"):
        summary["worst"] = {"label": summary["worst"]["label"], "score": summary["worst"]["score"]}

    return {"comparison": comparison, "backtests": backtests, "summary": summary}


# ==================== 便捷函数 ====================


def format_comparison_report(result: Dict[str, Any]) -> str:
    """将对比回测结果格式化为可读文本。"""
    comp = result.get("comparison", {})
    lines = [f"📊 同类数据横向对比与回测（{comp.get('series_count', 0)} 组）", "=" * 50]

    # 排名
    for field, rows in comp.get("ranking", {}).items():
        lines.append(f"\n【{field}】最新值排名:")
        for row in rows[:5]:
            lines.append(f"  {row['rank']}. {row['label']}: {row['value']}")

    # 回测评分
    lines.append("\n【数据质量回测】")
    for b in result.get("backtests", []):
        status = "✅" if b["passed"] else "⚠️"
        lines.append(f"  {status} {b['label']}: {b['score']} 分（{b['record_count']} 条记录）")
        for issue in b["issues"][:3]:
            lines.append(f"      - [{issue['level']}] {issue['message']}")

    summary = result.get("summary", {})
    lines.append(f"\n📈 汇总: 平均 {summary.get('avg_score', 0)} 分 | "
                 f"最佳 {summary.get('best', {}).get('label', '-')} | "
                 f"待关注 {summary.get('worst', {}).get('label', '-')}")
    return "\n".join(lines)


# ==================== CLI 测试入口 ====================

if __name__ == "__main__":
    # 示例：两只股票的两融模拟数据
    demo_a = [
        {"date": "2026-07-28", "margin_balance": 100.0, "margin_buy": 5.0},
        {"date": "2026-07-29", "margin_balance": 102.0, "margin_buy": 6.0},
        {"date": "2026-07-30", "margin_balance": 105.0, "margin_buy": 4.0},
        {"date": "2026-07-31", "margin_balance": 103.0, "margin_buy": 7.0},
    ]
    demo_b = [
        {"date": "2026-07-28", "margin_balance": 50.0, "margin_buy": 2.0},
        {"date": "2026-07-29", "margin_balance": 53.0, "margin_buy": 3.0},
        {"date": "2026-07-30", "margin_balance": 49.0, "margin_buy": 2.5},
        {"date": "2026-07-31", "margin_balance": 52.0, "margin_buy": 4.0},
    ]
    result = compare_and_backtest({"股票A": demo_a, "股票B": demo_b})
    print(format_comparison_report(result))
