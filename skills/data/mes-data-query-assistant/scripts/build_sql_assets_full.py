#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 sql_assets_full.md：142 个含 SQL 的视图完整档案（分类 + 中文注释用途 + SQL 全文）"""
import json, os, re

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
views = json.load(open(os.path.join(OUT_DIR, "views_full.json"), encoding="utf-8"))
classified = json.load(open(os.path.join(OUT_DIR, "views_classified.json"), encoding="utf-8"))

# 视图名 -> SQL
sql_map = {v["Name"]: v["MySqlSql"] for v in views if not v["sql_placeholder"] and v["MySqlSql"]}

# 提取第一条中文注释作为用途说明
def first_cn_comment(sql):
    for m in re.findall(r"/\*([^*]+)\*/", sql):
        c = m.strip()
        if re.search(r"[\u4e00-\u9fff]", c):
            return c.strip()[:60]
    for m in re.findall(r"--\s*([^\n]+)", sql):
        c = m.strip()
        if re.search(r"[\u4e00-\u9fff]", c):
            return c.strip()[:60]
    return ""

lines = ["# SQL 视图资产库（含完整 SELECT 语句）", ""]
lines.append("- 来源：`data-1785904910103.csv`（QueryScripts.MySql），共 185 个视图定义，其中 **142 个含完整 SQL**，43 个为占位")
lines.append("- 每条含：视图名、用途（SQL 中文注释提取）、列结构、SQL 全文")
lines.append("- 用途：问数路由命中后直接复用（口径已验证）；表名与 `schema.md` 交叉验证一致（82/106）")
lines.append("")

total = 0
for cat in classified:
    items = classified[cat]
    has_sql = [it for it in items if it["name"] in sql_map]
    no_sql = [it for it in items if it["name"] not in sql_map]
    lines.append(f"## {cat}（含SQL {len(has_sql)} / 共 {len(items)}）")
    lines.append("")
    for it in has_sql:
        total += 1
        name = it["name"]
        sql = sql_map[name]
        usage = first_cn_comment(sql)
        lines.append(f"### {name}" + (f" — {usage}" if usage else ""))
        cols = ", ".join(c["name"] for c in it["columns"]) or "（无列定义）"
        lines.append(f"列：{cols}")
        lines.append("```sql")
        lines.append(sql.strip())
        lines.append("```")
        lines.append("")
    if no_sql:
        names = ", ".join(i["name"] for i in no_sql)
        lines.append(f"> 占位/无 SQL：{names}")
        lines.append("")
    lines.append("")

with open(os.path.join(OUT_DIR, "sql_assets_full.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("saved sql_assets_full.md,", len(lines), "lines,", total, "views with sql")
