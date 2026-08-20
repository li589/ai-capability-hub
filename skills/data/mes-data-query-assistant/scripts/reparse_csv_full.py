#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重新解析 CSV：提取 QueryScripts（MySql 优先）等全部元数据，生成 views_full.json + 统计"""
import csv, json, os, re

SRC = r"<客户视图导出.csv>"  # 客户从数据库导出的视图清单
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

views = []
with open(SRC, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        payload = json.loads(row["PAYLOAD"])
        qs = payload.get("QueryScripts") or {}
        mysql_sql = qs.get("MySql", "")
        # 判断是否为占位（'please input ... view sql'）
        placeholder = "please input" in mysql_sql.lower() or not mysql_sql.strip()
        views.append({
            "ID": payload.get("ID"),
            "Name": payload.get("Name"),
            "ViewName": payload.get("ViewName"),
            "DaoName": payload.get("DaoName"),
            "GroupId": payload.get("GroupId"),
            "MetaLevel": payload.get("MetaLevel"),
            "Description": payload.get("Description"),
            "DisplayText": payload.get("DisplayText"),
            "Columns": [{"Name": c.get("Name"), "DataType": c.get("DataType"),
                         "cn": c.get("DisplayText")} for c in (payload.get("Columns") or [])],
            "QueryScripts": qs,
            "MySqlSql": mysql_sql,
            "sql_placeholder": placeholder,
            "db_types_with_sql": [k for k, v in qs.items() if v and "please input" not in v.lower()],
        })

print("total:", len(views))
with_sql = [v for v in views if not v["sql_placeholder"]]
print("有 MySql SQL:", len(with_sql), "| 占位/空:", len(views) - len(with_sql))

# 统计哪些库类型有 SQL
from collections import Counter
dbcnt = Counter()
for v in views:
    for k, s in v["QueryScripts"].items():
        if s and "please input" not in s.lower():
            dbcnt[k] += 1
print("各库类型有SQL数:", dict(dbcnt))

with open(os.path.join(OUT_DIR, "views_full.json"), "w", encoding="utf-8") as f:
    json.dump(views, f, ensure_ascii=False, indent=1)
print("saved views_full.json")

# 抽查几条 SQL
for name in ["STATION_REPORT_SUM", "GET_EQ_STATUS", "HUM_TIME"]:
    for v in views:
        if v["Name"] == name:
            print(f"\n===== {name} =====")
            print(v["MySqlSql"][:600])
            break
