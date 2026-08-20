#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""解析 schema 3.0.xlsx -> data/schema.json（表清单+字段）+ data/schema.md（数据字典）"""
import json, os, re
from python_calamine import CalamineWorkbook

SRC = r"<客户schema导出.xlsx>"  # 客户从数据库导出的表结构
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TEMPLATES = {"明细表结构模版", "基础数据表结构模版"}

wb = CalamineWorkbook.from_path(SRC)
sheet_names = wb.sheet_names

# ---- 1. 目录 ----
cat_rows = list(wb.get_sheet_by_name("目录").to_python(skip_empty_area=False))
tables_meta = []
for r in cat_rows[1:]:
    if not r or r[2] is None:
        continue
    tables_meta.append({
        "seq": r[0], "category": r[1], "table": str(r[2]).strip(),
        "cn_name": r[3], "origin": r[4], "origin_mean": r[5],
    })
print("目录表数:", len(tables_meta))

# ---- 2. 每个表 sheet 的字段 ----
def clean(v):
    if v is None:
        return ""
    s = str(v).strip()
    return s

schema = {}
for meta in tables_meta:
    tname = meta["table"]
    if tname in TEMPLATES or tname not in sheet_names:
        continue
    ws = wb.get_sheet_by_name(tname)
    rows = list(ws.to_python(skip_empty_area=False))
    if len(rows) < 4:
        continue
    # rows[0]: 表名行, rows[1]: 中文名, rows[2]: 列头, rows[3:]: 字段
    header = [clean(c) for c in (rows[2] if len(rows) > 2 else [])]
    fields = []
    for r in rows[3:]:
        fname = clean(r[0]) if len(r) > 0 else ""
        if not fname or fname == "字段名":
            continue
        fields.append({
            "name": fname,
            "cn": clean(r[1]) if len(r) > 1 else "",
            "type": clean(r[2]) if len(r) > 2 else "",
            "len": clean(r[3]) if len(r) > 3 else "",
            "nullable": clean(r[4]) if len(r) > 4 else "",
            "pk": clean(r[5]) if len(r) > 5 else "",
            "default": clean(r[6]) if len(r) > 6 else "",
            "lc_name": clean(r[7]) if len(r) > 7 else "",
            "note": clean(r[8]) if len(r) > 8 else "",
        })
    schema[tname] = {
        "cn_name": clean(rows[1][0]) if len(rows) > 1 and rows[1] else "",
        "upper": clean(rows[0][7]) if len(rows) > 0 and len(rows[0]) > 7 else "",
        "category": meta["category"],
        "origin": meta["origin"], "origin_mean": meta["origin_mean"],
        "fields": fields,
    }

print("解析表数:", len(schema))
total_fields = sum(len(v["fields"]) for v in schema.values())
print("总字段数:", total_fields)

# 分类统计
from collections import Counter
cat_cnt = Counter(v["category"] for v in schema.values())
print("分类:", dict(cat_cnt))

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "schema.json"), "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=1)
print("saved schema.json")

# ---- 3. 生成 schema.md ----
lines = ["# MES 数据字典（Schema 3.0）", ""]
lines.append(f"- 来源：`schema 3.0.xlsx`（目录 129 表，实际解析 {len(schema)} 张）")
lines.append(f"- 字段总数：{total_fields}")
lines.append("")
for cat in ["基础数据类", "业务信息类", "业务记录类"]:
    pass
cats = [c for c in cat_cnt]
lines.append("## 目录")
lines.append("")
lines.append("| 分类 | 表数 |")
lines.append("|------|------|")
for c, n in cat_cnt.items():
    lines.append(f"| {c} | {n} |")
lines.append("")

for tname, t in schema.items():
    lines.append(f"## {tname} — {t['cn_name']}（{t['category']}）")
    if t["origin"]:
        lines.append(f"原表：{t['origin']}（{t['origin_mean']}）")
    lines.append("")
    lines.append("| 字段名 | 字段含义 | 类型 | 长度 | 可空 | 主键 | 说明 |")
    lines.append("|--------|---------|------|------|------|------|------|")
    for f in t["fields"]:
        lines.append(f"| {f['name']} | {f['cn']} | {f['type']} | {f['len']} | {f['nullable']} | {f['pk']} | {f['note']} |")
    lines.append("")

with open(os.path.join(OUT_DIR, "schema.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("saved schema.md,", len(lines), "lines")
