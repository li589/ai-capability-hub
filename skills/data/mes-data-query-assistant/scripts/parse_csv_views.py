#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""解析 data-1785904910103.csv -> 视图资产清单 JSON + 摘要"""
import csv, json, sys, collections

SRC = r"<客户视图导出.csv>"  # 客户从数据库导出后放入 data/
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

views = []
with open(SRC, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        payload = row.get("PAYLOAD", "")
        if not payload:
            continue
        try:
            obj = json.loads(payload)
        except Exception as e:
            print("PARSE_ERR:", e, payload[:100])
            continue
        views.append(obj)

print("total views:", len(views))

# 摘要：视图名 -> 列数
summary = []
for v in views:
    name = v.get("Name", "?")
    cols = v.get("Columns", []) or []
    summary.append((name, len(cols), [c.get("Name") for c in cols][:8]))

# 去重统计（同名视图可能有多次导出）
name_counts = collections.Counter(s[0] for s in summary)
print("unique names:", len(name_counts))
print("--- duplicated names ---")
for n, c in name_counts.items():
    if c > 1:
        print(f"  {n}: {c}")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(views, f, ensure_ascii=False, indent=1)

print("saved:", OUT)
print("--- first 12 view names ---")
for s in summary[:12]:
    print(" ", s[0], "| cols:", s[1], "|", ", ".join(s[2]))
