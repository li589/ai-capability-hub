#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MES 智能问数 · 只读 SQL 执行器
用法：
  python db_query.py "SELECT 1"
  python db_query.py --file queries.sql        # 批量执行（每行/每段一条）
  python db_query.py --test                     # 连接测试
安全：应用层二次校验（只 SELECT + 表白名单 + 单语句 + 行数截断），
      与数据库层只读账号构成双重兜底。
"""
import sys, os, json, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
    CFG = json.load(f)

DATA_DIR = CFG.get("data_dir") or os.path.join(BASE, "data")

with open(os.path.join(DATA_DIR, "allowed_tables.json"), "r", encoding="utf-8") as f:
    ALLOWED = set(json.load(f))

DB = CFG["database"]
MAX_ROWS = CFG["limits"]["max_rows"]

# ---- 枚举翻译（来自 enum_dict.json，zh_CN 本地化）----
_ENUM_DATA = {}
_ED_PATH = os.path.join(DATA_DIR, "enum_dict.json")
if os.path.exists(_ED_PATH):
    with open(_ED_PATH, "r", encoding="utf-8") as f:
        _ED = json.load(f).get("enums", {})
    for _ename, _e in _ED.items():
        _ENUM_DATA[_ename] = _e.get("values", {})

# 列名(大小写不敏感) -> 枚举名；同时支持常用中文别名
COL_ENUM = {
    "EQ_N_STATUS": "EQ_STATUS", "设备状态": "EQ_STATUS", "EQ_STATUS": "EQ_STATUS",
    "EXECUTE_TYPE": "EXECUTE_TYPE", "操作类型": "EXECUTE_TYPE",
    "BAD_TYPE": "BAD_TYPE", "不良类型": "BAD_TYPE",
    "LOT_STATUS": "LOT_STATUS", "批量状态": "LOT_STATUS",
    "MO_STATUS": "MO_STATUS", "工单状态": "MO_STATUS",
    "IS_PAUSE": "IS_PAUSE", "暂停否": "IS_PAUSE",
    "MATERIAL_TYPE": "MATERIAL_TYPE", "物料类型": "MATERIAL_TYPE",
    "OP_TYPE": "OP_TYPE", "工艺特性": "OP_TYPE",
    "COLLECTION_TYPE": "COLLECTION_TYPE", "收集类型": "COLLECTION_TYPE",
    "IS_LIMIT": "IS_LIMIT",
    # MO_TYPE 是自由编码（工单单别，客户确认不需要枚举翻译），不映射
    "SOURCE_TYPE": "SOURCE_TYPE", "来源类型": "SOURCE_TYPE", "来源": "SOURCE_TYPE",
    "MOLD_STATUS": "MOLD_STATUS", "模具状态": "MOLD_STATUS",
}

# 业务枚举（非系统枚举字典，人工维护）：不良来源类型
_BIZ_ENUM = {
    "SOURCE_TYPE": {"1": "结束加工", "2": "二次判定"},
}


def translate(col, val):
    """按列名翻译枚举值为中文；无法翻译则原样返回"""
    if val is None:
        return val
    enum_name = COL_ENUM.get(str(col).upper()) or COL_ENUM.get(str(col))
    if not enum_name:
        return val
    mapping = _BIZ_ENUM.get(enum_name) or _ENUM_DATA.get(enum_name, {})
    return mapping.get(str(val), val)


def validate_sql(sql):
    """返回 (ok, msg)。只允许单条 SELECT、表在白名单。"""
    s = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    s = re.sub(r"--[^\n]*", "", s)
    s = s.strip().rstrip(";").strip()
    if not s:
        return False, "空语句"
    if ";" in s:
        return False, "禁止多语句（分号）"
    head = s.lstrip("(")[:20].upper()
    if not head.startswith("SELECT"):
        return False, f"只允许 SELECT，收到: {head}"
    upper = s.upper()
    for kw in ["UPDATE", "DELETE", "INSERT", "DROP", "ALTER", "TRUNCATE",
               "CREATE", "REPLACE", "INTO", "LOAD_FILE", "BENCHMARK", "SLEEP("]:
        # 前后词边界，避免误伤 CREATE_TIME / UPDATED_BY 等字段名
        pat = r"\b" + re.escape(kw) + (r"\b" if not kw.endswith("(") else "")
        if re.search(pat, upper):
            return False, f"检测到危险关键字: {kw}"
    for m in re.findall(r"\bfrom\s+([a-zA-Z_][\w]*)|\bjoin\s+([a-zA-Z_][\w]*)", s, re.IGNORECASE):
        t = (m[0] or m[1]).lower()
        if t not in ALLOWED:
            return False, f"表不在白名单: {t}"
    return True, "ok"


def connect():
    import pymysql
    return pymysql.connect(host=DB["host"], port=int(DB["port"]),
                           user=DB["user"], password=DB["password"],
                           database=DB["dbname"], charset="utf8mb4",
                           connect_timeout=5)


def run(sql):
    conn = connect()
    try:
        try:
            cur = conn.cursor()
            cur.execute("SET SESSION MAX_EXECUTION_TIME = %d" % (CFG["limits"]["max_query_seconds"] * 1000))
        except Exception:
            pass  # 旧版 MySQL 无此变量，忽略
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]
        return cols, rows, truncated
    finally:
        conn.close()


def fmt_table(cols, rows):
    if not cols:
        return "(无返回列)"
    w = [len(str(c)) for c in cols]
    # 按列名翻译枚举值（如 EQ_N_STATUS 1 -> 闲置）
    srows = [[str(translate(cols[i], c))[:60] for i, c in enumerate(r)] for r in rows]
    for r in srows:
        for i, c in enumerate(r):
            w[i] = max(w[i], len(c))
    line = "+-" + "-+-".join("-" * x for x in w) + "-+"
    out = [line]
    out.append("| " + " | ".join(str(c).ljust(w[i]) for i, c in enumerate(cols)) + " |")
    out.append(line)
    for r in srows:
        out.append("| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(r)) + " |")
    out.append(line)
    return "\n".join(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if "--test" in args:
        try:
            conn = connect()
            with conn.cursor() as c:
                c.execute("SELECT VERSION()")
                print("连接成功 | MySQL:", c.fetchone()[0], "| 库:", DB["dbname"], "| 用户:", DB["user"])
            conn.close()
            return
        except Exception as e:
            print("连接失败:", e)
            return
    sqls = []
    if "--file" in args:
        p = args[args.index("--file") + 1]
        text = open(p, encoding="utf-8").read()
        sqls = [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]
    else:
        sqls = args if args else ["SELECT 1"]
    for sql in sqls:
        print("=" * 66)
        ok, msg = validate_sql(sql)
        if not ok:
            print("❌ 校验拒绝：", msg)
            continue
        print("SQL:", sql[:200])
        try:
            cols, rows, trunc = run(sql)
            print(fmt_table(cols, rows))
            if trunc:
                print(f"⚠ 结果超过 {MAX_ROWS} 行，已截断显示（共返回前 {MAX_ROWS} 行）")
            print(f"✅ 共 {len(rows)} 行")
        except Exception as e:
            print("❌ 执行失败：", e)


if __name__ == "__main__":
    main()
