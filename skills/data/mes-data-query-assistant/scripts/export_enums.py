#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导出枚举字典：da_collection_data + da_collection_choice_detail 全量 -> data/enum_map.json"""
import sys, os, json
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from db_query import connect, validate_sql

OUT = os.path.join(BASE, "data", "enum_map.json")

def q(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

conn = connect()
try:
    groups = q(conn, "SELECT ID, COLLECTION_ID, COLLECTION_NAME, COLLECTION_TYPE, DATA_TYPE FROM da_collection_data ORDER BY ID")
    choices = q(conn, "SELECT ID, PARENT_ID, COLLECTION_CHOICE_NAME FROM da_collection_choice_detail ORDER BY ID")
finally:
    conn.close()

id_to_name = {}
for g in groups:
    id_to_name[str(g["ID"])] = g["COLLECTION_NAME"] or g["COLLECTION_ID"] or str(g["ID"])
for c in choices:
    id_to_name[str(c["ID"])] = c["COLLECTION_CHOICE_NAME"]

data = {
    "generated": "2026-08-05",
    "note": "枚举字典：da_collection_data(收集项/组) + da_collection_choice_detail(选项)。ID->名称映射用于翻译 BAD_REASON/原因ID 等。",
    "collection_data": groups,
    "choice_detail": choices,
    "id_to_name": id_to_name,
    "collection_type_usage": {
        "1": "返工原因", "2": "报废", "5": "验退原因", "7": "我要闲置",
        "8": "我是故障", "10": "我要关机", "11": "我要暂停", "12": "暂停",
        "13": "解除暂停", "15": "工价加工方式", "17": "下拉/通用"
    }
}
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"导出完成：组 {len(groups)} 条，选项 {len(choices)} 条，映射 {len(id_to_name)} 条")
print("样例映射：", json.dumps({k: v for k, v in list(id_to_name.items())[:8]}, ensure_ascii=False))
