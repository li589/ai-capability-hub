#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
customization-data-export 本地处理脚本。
读 raw.csv + 声明式 recipe → pandas 聚合 → 写本地 时间-描述.xlsx|csv → stdout 只回小摘要 JSON。

调用：
  python3 data_export.py --input raw.csv --recipe recipe.json \
      --out ./data-export-output --format xlsx --desc "学习统计Top10"

recipe.json 形如：
  {
    "group_by": ["resource_id", "resource_name"],
    "rename": {"resource_id": "资源ID", "resource_name": "资源名称"},
    "agg": [
      {"out_field": "学习次数", "func": "sum", "field": "view_count"},
      {"out_field": "学习人数", "func": "nunique", "field": "user_id"}
    ],
    "sort": {"by": "学习次数", "asc": false},
    "rank": true,
    "rank_field": "排名"
  }

stdout 成功：{"total": N, "top10": [...], "file": "<绝对路径>"}
stdout 失败：{"error": "..."}，退出码 1。
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print(json.dumps(
        {"error": "pandas 未安装，请先运行: pip install --user pandas openpyxl"},
        ensure_ascii=False))
    sys.exit(1)

# 强制 stdout 为 UTF-8：Windows 默认控制台编码可能是 cp936，
# 直接 print 含中文的 JSON 会让上层（workbuddy Bash 捕获）解析乱码。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SUPPORTED_FUNCS = {"sum", "count", "mean", "nunique", "max", "min"}


def emit(obj):
    """统一 JSON 输出（中文不转义）。"""
    print(json.dumps(obj, ensure_ascii=False, default=_json_default))


def _json_default(o):
    # 兜底：numpy 标量 → Python 原生
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


def _clean(value):
    """把值转成 JSON 可序列化的原生类型，NaN → None。"""
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        f = float(value)
        return None if np.isnan(f) else f
    if isinstance(value, float):
        return None if value != value else value  # NaN check
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def load_recipe(path):
    with open(path, "r", encoding="utf-8") as f:
        recipe = json.load(f)
    if not recipe.get("group_by"):
        raise ValueError("recipe.group_by 不能为空（无聚合的排名请用自写 Python）")
    if not recipe.get("agg"):
        raise ValueError("recipe.agg 不能为空")
    for item in recipe["agg"]:
        if item.get("func") not in SUPPORTED_FUNCS:
            raise ValueError(
                "不支持的 func: %s（支持 %s）" % (item.get("func"), sorted(SUPPORTED_FUNCS)))
        if "field" not in item or "out_field" not in item:
            raise ValueError("recipe.agg 每项需含 field 和 out_field")
    return recipe


def aggregate(df, recipe):
    group_by = recipe["group_by"]
    agg = recipe["agg"]
    rename = recipe.get("rename", {})

    for col in group_by:
        if col not in df.columns:
            raise ValueError("group_by 字段不存在于输入 CSV: %s（实际列: %s）"
                             % (col, list(df.columns)))

    grp = df.groupby(group_by)
    series_list = []
    for item in agg:
        field = item["field"]
        if field not in df.columns:
            raise ValueError("agg 字段不存在于输入 CSV: %s（实际列: %s）"
                             % (field, list(df.columns)))
        func = item["func"]
        if func == "nunique":
            s = grp[field].nunique()
        else:
            s = grp[field].agg(func)
        s.name = item["out_field"]
        series_list.append(s)

    result = pd.concat(series_list, axis=1).reset_index()
    result = result.rename(columns=rename)

    # 排序
    sort = recipe.get("sort")
    if sort and sort.get("by") in result.columns:
        result = result.sort_values(
            by=sort["by"], ascending=sort.get("asc", False)
        ).reset_index(drop=True)

    # 排名列
    if recipe.get("rank"):
        rank_field = recipe.get("rank_field", "排名")
        result.insert(0, rank_field, range(1, len(result) + 1))

    # 列顺序：排名列 → group_by(重命名后) → agg out_field
    group_by_renamed = [rename.get(g, g) for g in group_by]
    out_fields = [item["out_field"] for item in agg]
    col_order = []
    if recipe.get("rank"):
        col_order.append(recipe.get("rank_field", "排名"))
    col_order += group_by_renamed + out_fields
    result = result[[c for c in col_order if c in result.columns]]

    return result


def write_file(result, out_dir, fmt, desc):
    if fmt not in ("xlsx", "csv"):
        raise ValueError("format 必须是 xlsx 或 csv，收到: %s" % fmt)
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = "%s-%s.%s" % (timestamp, desc or "导出", fmt)
    filepath = os.path.join(out_dir, filename)
    if fmt == "csv":
        result.to_csv(filepath, index=False, encoding="utf-8-sig")
    else:
        try:
            import openpyxl  # noqa: F401  仅确认可用
        except ImportError:
            raise RuntimeError("openpyxl 未安装，请运行: pip install --user openpyxl")
        result.to_excel(filepath, index=False)
    return os.path.abspath(filepath)


def main():
    parser = argparse.ArgumentParser(description="customization-data-export 本地处理脚本")
    parser.add_argument("--input", required=True, help="输入 CSV 路径（raw.csv）")
    parser.add_argument("--recipe", required=True, help="聚合配方 JSON 路径")
    parser.add_argument("--out", required=True, help="输出目录")
    parser.add_argument("--format", default="xlsx", choices=("xlsx", "csv"),
                        help="输出格式，默认 xlsx")
    parser.add_argument("--desc", default="", help="中文描述，用于文件名")
    args = parser.parse_args()

    try:
        recipe = load_recipe(args.recipe)
        df = pd.read_csv(args.input, encoding="utf-8-sig")
        result = aggregate(df, recipe)
        filepath = write_file(result, args.out, args.format, args.desc)
        top10 = [{k: _clean(v) for k, v in row.items()}
                 for row in result.head(10).to_dict(orient="records")]
        emit({"total": int(len(result)), "top10": top10, "file": filepath})
        sys.exit(0)
    except Exception as e:
        emit({"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
