#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""解析枚举定义(txt INSERT) + 本地化CSV(zh_CN) -> data/enum_dict.json
- txt: TB_META_INDEX 枚举元数据（Name + KeyValues，值的中文是 i18n key）
- csv: TB_LOCALIZATION 本地化表，PAYLOAD.Language.zh_CN 为中文文本，NAME 为语言键
"""
import re, json, os, csv

TXT = r"<本地化文案导出.txt>"
CSV = r"<本地化字典导出.csv>"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ---- 1. 解析 txt：提取枚举定义（记录可能跨行，按边界切分后合并） ----
enums = {}
text = open(TXT, "r", encoding="utf-8").read()
records, cur = [], []
for line in text.split("\n"):
    if line.strip().startswith("('") or line.strip().startswith("( '"):
        if cur:
            records.append("\n".join(cur))
        cur = [line]
    elif cur:
        cur.append(line)
if cur:
    records.append("\n".join(cur))
print("枚举记录(行):", len(records))

def extract_payload(rec):
    """从记录中提取 PAYLOAD JSON：花括号平衡扫描，跳过双引号字符串内部"""
    start = rec.index("'{")
    i = start + 1
    depth = 0
    in_str = False
    while i < len(rec):
        c = rec[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return rec[start + 1:i + 1]
        i += 1
    return None

for i, rec in enumerate(records):
    try:
        snippet = extract_payload(rec)
        if snippet is None:
            continue
        payload = json.loads(snippet)
    except Exception as e:
        if i < 3:
            print(f"记录{i} 解析失败: {type(e).__name__}: {e}")
        continue
    name = payload.get("Name", "")
    if not name:
        continue
    kvs = {}
    for kv in payload.get("KeyValues", []) or []:
        code = str(kv.get("Name"))
        kvs[code] = kv.get("DisplayText") or code  # i18n key（也可能是直值）
    enums[name] = {
        "display_key": payload.get("DisplayText"),  # 枚举名自身的语言键
        "values": kvs,                              # 值代码 -> 语言键
    }

print("枚举数:", len(enums))
# 收集所有需要翻译的 key
need_keys = set()
for name, e in enums.items():
    if e["display_key"]:
        need_keys.add(e["display_key"])
    for code, key in e["values"].items():
        if key and not key.isdigit():  # 纯数字 key 无需翻译（如直接是 "0"）
            need_keys.add(key)
print("需翻译的语言键:", len(need_keys))

# ---- 2. 解析 CSV：NAME -> zh_CN ----
loc = {}
with open(CSV, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        name = row.get("NAME", "")
        if not name:
            continue
        try:
            payload = json.loads(row.get("PAYLOAD", "{}"))
            zh = (payload.get("Language") or {}).get("zh_CN")
        except Exception:
            zh = None
        if zh:
            loc[name] = zh
print("本地化条目(zh_CN):", len(loc))

# ---- 3. 合并 ----
result = {}
untranslated = []
for name, e in enums.items():
    vals = {}
    for code, key in e["values"].items():
        if key in loc:
            vals[code] = loc[key]
        elif key in (None, "") or key.isdigit():
            vals[code] = key  # 无语言键的值，直接使用代码
        else:
            vals[code] = key  # 保留 key 原样
            untranslated.append((name, code, key))
    display = loc.get(e["display_key"], name) if e["display_key"] else name
    result[name] = {"display": display, "values": vals}

# 保留原始本地化映射（key->中文），供查询用
result_meta = {
    "generated": "2026-08-05",
    "source": "新建 文本文档.txt + _TB_LOCALIZATION__202608051806.csv(zh_CN)",
    "localization": loc,
    "enums": result,
}

json.dump(result_meta, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- 4. 输出摘要 ----
print("=" * 60)
print("未翻译的 key 数:", len(untranslated))
for name, e in sorted(result.items()):
    if name in ("EQ_STATUS", "LOT_STATUS", "MO_STATUS", "IS_PAUSE", "MATERIAL_TYPE", "EXECUTE_TYPE",
                "OP_TYPE", "DATA_TYPE", "COLLECTION_TYPE", "MO_TYPE", "IS_LIMIT", "BAD_TYPE", "SOURCE_TYPE"):
        print(f"\n[{name}] {e['display']}")
        for code, v in e["values"].items():
            print(f"   {code} = {v}")
print("\nsaved:", OUT)
