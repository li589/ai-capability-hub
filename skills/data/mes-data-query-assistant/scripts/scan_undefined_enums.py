# -*- coding: utf-8 -*-
"""
枚举未定义值扫描：把关键枚举字段在库中的实际取值 vs enum_dict.json 字典覆盖，
找出所有【未定义取值】列出来供客户确认（而非静默当脏数据）。

用法（venv python）：python scan_undefined_enums.py
"""
import sys, os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
ENUM_PATH = os.path.join(DATA, "enum_dict.json")

# 关键枚举字段扫描清单：{表名: [(列名, 枚举名, 中文说明)]}
SCAN_LIST = {
    "eq_status": [("EQ_N_STATUS", "EQ_STATUS", "设备状态")],
    "eq_mold_status": [("MOLD_STATUS", "MOLD_STATUS", "模具状态")],
    "ac_mo_report_process": [("EXECUTE_TYPE", "EXECUTE_TYPE", "操作类型")],
    "ac_lot_status": [("LOT_STATUS", "LOT_STATUS", "批量状态"), ("IS_PAUSE", "IS_PAUSE", "暂停否")],
    "in_except_reason_record": [("BAD_TYPE", "BAD_TYPE", "不良类型"), ("SOURCE_TYPE", "SOURCE_TYPE", "不良来源")],
    "pl_mo_data": [("MO_TYPE", "MO_TYPE", "工单单别")],
    "pl_mo_status": [("MO_STATUS", "MO_STATUS", "工单状态")],
    "me_pack_box_data": [("BOX_STATUS", "BOX_STATUS", "封箱否"), ("PACK_HIERARCHY", "PACK_HIERARCHY", "包装层级")],
    "me_pack_box_detail": [("PACK_TYPE", "PACK_TYPE", "包装类型")],
    "pl_mo_sn_detail": [("SN_STATUS", "SN_STATUS", "SN状态"), ("SN_SOURCE", "SN_DATA_SOURCE", "SN来源")],
    "eq_maintenance_plan_data": [("EQ_MAINTENANCE_STATUS", "EQ_MAINTENANCE_STATUS", "维修单状态"), ("EQ_MAINTENANCE_TYPE", "EQ_MAINTENANCE_TYPE", "维修单类型")],
    "dispatch_record": [("EXECUTE_TYPE", "EXECUTE_TYPE", "派工执行类型")],
    "eq_check_record": [("CHECK_FREQUENCY", "CHECK_FREQUENCY", "点检频率")],
    "ma_consume_detail": [("USAGE_TYPE", "MA_USE_TYPE", "耗料类型")],
    "ac_stock_in_data": [("STOCK_IN_TYPE", "IS_STOCK_IN", "入库类型")],
}

# 已确认的未定义值（客户确认过结论，不再提示）：
# {表名: {列名: {值: 结论说明}}}
KNOWN_UNDEFINED = {
    "eq_status": {"EQ_N_STATUS": {"0": "脏数据（初始/未上报态），统计过滤"}},
    "me_pack_box_detail": {"PACK_TYPE": {"2": "客户确认暂无此值，为残留/测试数据，视为异常值"}},
    "pl_mo_data": {"MO_TYPE": {"*": "自由编码主数据（工单单别），不需枚举翻译"}},
}


def load_enum():
    with open(ENUM_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d.get("enums", {})


def connect():
    import pymysql
    with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
        db = json.load(f)["database"]
    return pymysql.connect(host=db["host"], port=db["port"], user=db["user"],
                           password=db["password"], database=db["dbname"],
                           charset="utf8mb4", connect_timeout=10, read_timeout=30)


def main():
    enums = load_enum()
    conn = connect()
    cur = conn.cursor()
    with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
        dbname = json.load(f)["database"]["dbname"]
    cur.execute("SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s", (dbname,))
    cols_by_tbl = {}
    for t, c in cur.fetchall():
        cols_by_tbl.setdefault(t.lower(), set()).add(c.lower())

    undefined = []
    defined_count = 0
    for tbl, items in SCAN_LIST.items():
        for col, enum_name, desc in items:
            if tbl not in cols_by_tbl or col.lower() not in cols_by_tbl[tbl]:
                continue
            try:
                cur.execute(f"SELECT DISTINCT `{col}` FROM `{tbl}` WHERE `{col}` IS NOT NULL LIMIT 50")
                vals = [r[0] for r in cur.fetchall()]
            except Exception as e:
                print(f"⚠️ 查询 {tbl}.{col} 失败: {e}")
                continue
            mapping = enums.get(enum_name or "", {}).get("values", {})
            known = KNOWN_UNDEFINED.get(tbl, {}).get(col, {})
            undef, known_hits = [], []
            for v in vals:
                sv = str(v)
                if sv in mapping:
                    continue
                if sv in known or "*" in known:
                    known_hits.append(sv)
                    continue
                undef.append(sv)
            if undef:
                undefined.append((tbl, col, enum_name, desc, undef))
            elif not known_hits and mapping:
                defined_count += 1
            elif known_hits and not undef:
                defined_count += 1

    conn.close()
    print(f"📊 枚举扫描完成：{defined_count} 个字段取值全部有定义")
    if not undefined:
        print("✅ 没有未定义取值")
        return
    print(f"\n⚠️ 发现 {len(undefined)} 个字段存在未定义取值，需要确认：\n")
    for tbl, col, enum_name, desc, undef in undefined:
        ename = f"[{enum_name}]" if enum_name else "[无枚举映射]"
        print(f"  📍 {tbl}.{col}（{desc}）{ename}")
        print(f"     未定义值: {undef}")
        print()
    print("确认方式：客户给出含义后 → 1) 更新 data/enum_dict.json 对应枚举 values；2) 记录到 learned_knowledge.md")


if __name__ == "__main__":
    main()
