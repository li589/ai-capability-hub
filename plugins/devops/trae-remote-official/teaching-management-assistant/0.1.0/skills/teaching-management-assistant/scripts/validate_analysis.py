#!/usr/bin/env python3
"""分析结果校验脚本（确定性）。

对标准化数据和模型生成的分析结果做兜底复核，输出校验报告。
不重新做业务分析，只做一致性/合理性检查。

用法：
  python3 validate_analysis.py --data output/normalized_data.xlsx \
      --results output/analysis_results.json [--item-data items.xlsx]
"""

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("需要 pandas：pip3 install pandas openpyxl", file=sys.stderr)
    sys.exit(2)


def check_data(df):
    checks = []
    # 评分状态与分数一致性
    if "status" in df and "score" in df:
        normal = df[df["status"] == "normal"]
        bad = normal["score"].isna().sum()
        checks.append(_c("normal记录应有分数", bad == 0,
                         f"{bad} 条 normal 记录缺分数"))
        # 缺考不应有分数污染统计
        absent_scored = df[(df["status"] == "absent") & (df["score"].notna())]
        checks.append(_c("缺考记录不带有效分数", len(absent_scored) == 0,
                         f"{len(absent_scored)} 条缺考记录仍带分数"))
    # 超满分/负分
    if "full_score" in df and df["full_score"].notna().any():
        over = df[(df["status"] == "normal") & (df["score"] > df["full_score"])]
        checks.append(_c("无超满分", len(over) == 0, f"{len(over)} 条超满分"))
    if {"score", "status"} <= set(df.columns):
        neg = df[(df["status"] == "normal") & (df["score"] < 0)]
        checks.append(_c("无负分", len(neg) == 0, f"{len(neg)} 条负分"))
    duplicate_keys = _duplicate_keys(df)
    if duplicate_keys:
        normal = df[df["status"] == "normal"]
        duplicates = int(normal.duplicated(subset=duplicate_keys).sum())
        checks.append(_c("无未解决的语义重复记录", duplicates == 0,
                         f"{duplicates} 条记录在 {duplicate_keys} 上重复"))
    return checks


def check_results(results, df):
    checks = []
    if not isinstance(results, dict):
        return [_c("结果为 JSON 对象", False, "analysis_results.json 不是对象")]

    # 分层人数一致性
    for key, val in _walk(results):
        if isinstance(val, list) and val and isinstance(val[0], dict):
            keys = set(val[0].keys())
            if {"tier", "count"} <= keys:
                total = sum(x.get("count", 0) for x in val)
                normal_n = _effective_student_count(df)
                if normal_n:
                    checks.append(_c(f"分层[{key}]人数合理",
                                     total == normal_n,
                                     f"分层合计 {total}，有效人数 {normal_n}"))
            if {"seg", "count"} <= keys or {"segment", "count"} <= keys:
                total = sum(x.get("count", 0) for x in val)
                checks.append(_c(f"分布[{key}]非空", total > 0, f"分段合计 {total}"))
            # 比率范围
            for x in val:
                for rk in ("pct", "pass_rate", "excellent_rate", "low_rate",
                           "score_rate", "difficulty_P", "attainment"):
                    if rk in x and x[rk] is not None:
                        v = x[rk]
                        hi = 1.0 if rk in ("difficulty_P", "attainment") else 100.0
                        if not (-0.001 <= v <= hi + 0.001):
                            checks.append(_c(f"{key}.{rk} 越界", False,
                                             f"值 {v} 超出 [0,{hi}]"))

    # NaN / Infinity 扫描
    nan_hits = _scan_bad_numbers(results)
    checks.append(_c("无 NaN/Infinity", len(nan_hits) == 0,
                     f"发现 {len(nan_hits)} 处非法数值：{nan_hits[:5]}"))
    checks.extend(check_recomputed_metrics(results, df))
    return checks


def check_item_consistency(item_data_path, _results):
    """逐题得分之和应与整卷总分一致（如提供）。"""
    checks = []
    if not item_data_path:
        return checks
    try:
        df = _read_tabular(item_data_path)
    except Exception as e:
        return [_c("读取逐题数据", False, str(e))]
    total_cols = [c for c in df.columns if str(c) in ("总分", "total", "合计")]
    metadata_cols = {
        "学号", "姓名", "班级", "性别", "student_id", "student_name",
        "class", "gender", "assessment_id", "exam_type", "term",
    }
    item_cols = [
        c for c in df.columns
        if c not in total_cols
        and c not in metadata_cols
        and pd.api.types.is_numeric_dtype(df[c])
    ]
    if total_cols and item_cols:
        recomputed = df[item_cols].sum(axis=1)
        given = pd.to_numeric(df[total_cols[0]], errors="coerce")
        diff = (recomputed - given).abs()
        bad = int((diff > 0.51).sum())
        checks.append(_c("逐题得分和=总分", bad == 0,
                         f"{bad} 名学生逐题之和与总分不符"))
    return checks


def check_recomputed_metrics(results, df):
    """复算结果 JSON 中可识别的均分和逐题难度指标。"""
    checks = []
    normal = df[df["status"] == "normal"].copy() if "status" in df else df.copy()
    normal["score"] = pd.to_numeric(normal.get("score"), errors="coerce")

    for path, value in _walk(results):
        if not isinstance(value, dict):
            continue

        dimension = _first(value, "subject", "科目")
        reported_mean = _number(_first(value, "mean", "avg", "average", "均分", "平均分"))
        if dimension is not None and reported_mean is not None and "subject" in normal:
            source = normal[normal["subject"].astype(str) == str(dimension)]["score"].dropna()
            if len(source):
                actual = float(source.mean())
                checks.append(_metric_check(
                    f"{path}.均分复算", reported_mean, actual, tolerance=0.11))

        item_id = _first(value, "item_id", "item", "题号")
        reported_p = _number(_first(value, "difficulty_P", "difficulty", "难度P"))
        if item_id is not None and reported_p is not None and "item_id" in normal:
            source = normal[normal["item_id"].astype(str) == str(item_id)]
            scores = source["score"].dropna()
            full_scores = pd.to_numeric(source.get("full_score"), errors="coerce").dropna()
            if len(scores) and len(full_scores) and float(full_scores.iloc[0]) > 0:
                actual = float(scores.mean() / full_scores.iloc[0])
                checks.append(_metric_check(
                    f"{path}.难度P复算", reported_p, actual, tolerance=0.002))
    return checks


def _effective_student_count(df):
    normal = df[df["status"] == "normal"] if "status" in df else df
    if "student_id" in normal and normal["student_id"].notna().any():
        return int(normal["student_id"].dropna().astype(str).nunique())
    return int(len(normal))


def _duplicate_keys(df):
    if not {"student_id", "status"} <= set(df.columns):
        return []
    dimension = None
    if "item_id" in df and df["item_id"].notna().any():
        dimension = "item_id"
    elif "subject" in df and df["subject"].notna().any():
        dimension = "subject"
    if not dimension:
        return []
    return [c for c in
            ("student_id", dimension, "assessment_id", "exam_type", "term")
            if c in df.columns]


def _read_tabular(path):
    p = Path(path)
    if p.suffix.lower() in (".csv", ".tsv"):
        return pd.read_csv(p, sep="\t" if p.suffix.lower() == ".tsv" else ",")
    return pd.read_excel(p)


def _first(obj, *keys):
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return None


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _metric_check(name, reported, actual, tolerance):
    diff = abs(reported - actual)
    return _c(name, diff <= tolerance,
              f"报告值 {reported:.4f}，源数据复算 {actual:.4f}，差值 {diff:.4f}")


def _walk(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{prefix}.{k}" if prefix else k)
        yield prefix, obj
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _walk(value, f"{prefix}[{i}]")
        yield prefix, obj


def _scan_bad_numbers(obj, path=""):
    hits = []
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            hits.append(path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            hits += _scan_bad_numbers(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _scan_bad_numbers(v, f"{path}[{i}]")
    return hits


def _c(name, passed, detail="", level="error"):
    return {"check": name, "passed": bool(passed),
            "level": "info" if passed else level, "detail": detail}


def main():
    ap = argparse.ArgumentParser(description="分析结果校验")
    ap.add_argument("--data", required=True, help="标准化数据 xlsx")
    ap.add_argument("--results", required=True, help="分析结果 json")
    ap.add_argument("--item-data", help="逐题得分 xlsx（可选）")
    ap.add_argument("--output", default="output/validation_report.json")
    args = ap.parse_args()

    df = pd.read_excel(args.data)
    results = json.loads(Path(args.results).read_text(encoding="utf-8"))

    all_checks = check_data(df) + check_results(results, df) + \
        check_item_consistency(args.item_data, results)

    failed = [c for c in all_checks if not c["passed"] and c["level"] == "error"]
    report = {"total": len(all_checks), "failed": len(failed),
              "passed": len(all_checks) - len(failed), "checks": all_checks}

    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"校验完成：{report['passed']}/{report['total']} 通过")
    for c in failed:
        print(f"  ✗ {c['check']}: {c['detail']}")
    print(f"报告：{outp}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
