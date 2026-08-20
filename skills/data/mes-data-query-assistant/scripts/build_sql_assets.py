#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""基于 views_raw.json 生成：data/sql_assets.md（分类清单）+ data/views_classified.json"""
import json, os

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
views = json.load(open(os.path.join(OUT_DIR, "views_raw.json"), encoding="utf-8"))

# 主题分类规则（按名字关键词，顺序即优先级）
CATEGORIES = [
    ("质量/不良", ["PQC", "SPC", "ERROR_REASON", "NG_REASON", "EXCEPT_REASON", "DISQUALIFY", "SCRAP", "INSPECT"]),
    ("工单MO", ["GET_MO", "MO_", "PCP_MO", "PL_MO", "PACK_MO", "PCQ_MO", "MO_RELEASE", "MY_TASK"]),
    ("派工/报工", ["DISPATCH", "PCQ_", "REPORT", "CHECK_IN", "STATION_REPORT", "MO_STATION"]),
    ("设备", ["GET_EQ", "EQ_", "WO_WORK_EQ", "END_WORK_EQ", "GETEQLIST"]),
    ("模具", ["MOLD"]),
    ("SN序列号", ["SN_", "SNLIST", "MO_SN", "PQC_SN", "OP_SN", "PQC_SN"]),
    ("物料/领料", ["MA_", "MATERIAL", "REQUISTION", "STOCK_IN", "MAT_USE", "PRODUCT_"]),
    ("包装", ["PACK"]),
    ("外协", ["OUTSOURCE", "OUTBACK"]),
    ("工时/人员", ["WO_", "WAGE", "HUM_TIME", "WORKER", "GETOPUSER", "USER", "STATION_WORKER"]),
    ("质检任务", ["IN_", "GET_MA_PQC", "PQC_RANGE"]),
    ("基础/主数据", ["STATION", "OP_", "WS_", "CHOICE", "CHOSE", "CODERULE", "SOP", "GETBOXMSG", "PRODUCTION", "COREBASIC", "TASK_ALLOCATION"]),
    ("主页图表", ["HOME"]),
    ("其他", []),
]

def classify(name):
    for cat, kws in CATEGORIES:
        if any(kw in name for kw in kws):
            return cat
    return "其他"

classified = {}
for v in views:
    name = v.get("Name", "?")
    cat = classify(name)
    cols = [{"name": c.get("Name",""), "type": c.get("DataType",""),
             "cn": (c.get("DisplayText") or "")} for c in (v.get("Columns") or [])]
    classified.setdefault(cat, []).append({"name": name, "id": v.get("ID"), "columns": cols})

# 排序：每类内按名字
for cat in classified:
    classified[cat].sort(key=lambda x: x["name"])

with open(os.path.join(OUT_DIR, "views_classified.json"), "w", encoding="utf-8") as f:
    json.dump(classified, f, ensure_ascii=False, indent=1)

# 生成 sql_assets.md
lines = ["# SQL 视图资产库（MES 系统既有查询视图）", ""]
lines.append(f"- 来源：`data-1785904910103.csv`，共 {len(views)} 个视图/查询定义（含列结构与 i18n 标签）")
lines.append("- 用途：问数路由优先复用；每类视图附列清单")
lines.append("")
for cat in classified:
    items = classified[cat]
    lines.append(f"## {cat}（{len(items)}）")
    lines.append("")
    for it in items:
        lines.append(f"### {it['name']}")
        cn_cols = [f"{c['name']}({c['cn'][:20]})" for c in it["columns"] if c["cn"] and c["cn"] != "null"]
        if cn_cols:
            lines.append("> " + "、".join(cn_cols))
        col_str = ", ".join(c["name"] for c in it["columns"]) or "（无列定义）"
        lines.append(f"- 列：{col_str}")
        lines.append("")
    lines.append("")

with open(os.path.join(OUT_DIR, "sql_assets.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("saved sql_assets.md,", len(lines), "lines")
for cat in classified:
    print(f"  {cat}: {len(classified[cat])}")
