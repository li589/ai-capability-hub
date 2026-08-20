#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""委外业务清单查询(数据源 = 提供的 OPENAPI 查询接口,不读数据库)。

用法(venv python):
  "$PY" outsource_list.py --todo                        # 可委外清单(getCanOutsourceList)
  "$PY" outsource_list.py --intransit [--supplier X]    # 待回货清单(getOutSourceList)
  "$PY" outsource_list.py --hands [--supplier X]        # 供应商在手委外单汇总(getOutSourceDash)
  "$PY" outsource_list.py --detail OU-20260811001       # 指定委外单待回货信息(getOutSourceList)
"""
import argparse
import sys

import api_common as ac


def _query(entity_fn, body):
    """按数据实体查询(可委外清单 / 待回货清单各自独立,容器不混用)。"""
    rows, err = entity_fn(body)
    if err:
        sys.exit("❌ " + err)
    return rows


def _match_contains(field_val, kw):
    if field_val is None:
        return False
    fv = str(field_val)
    if not fv:  # 空值不匹配任何关键词(防止空供应商被误过滤放过)
        return False
    return str(kw) in fv or fv in str(kw)


def _filter(rows, supplier=None, outsource_id=None):
    if supplier:
        rows = [r for r in rows if _match_contains(r.get('SUPPLIER_ID'), supplier)
                or _match_contains(r.get('SUPPLIER_NAME'), supplier)]
    if outsource_id:
        rows = [r for r in rows if _match_contains(r.get('OUTSOURCE_ID'), outsource_id)]
    return rows


CN_SEND = {
    "MO_ID": "工单编号", "MA_ID": "产品编号", "MATERIAL_NAME": "产品名称",
    "OP_SEQ": "工序", "OP_ID": "工艺编号", "OP_NAME": "工艺名称",
    "SUPPLIER_ID": "预设供应商编号", "SUPPLIER_NAME": "预设供应商名称",
    "CANOUTQTY": "可委外数量", "OUTQTY": "委外数量", "BACKDATE": "默认回货日期",
}
CN_BACK = {
    "OUTSOURCE_ID": "委外单号", "SUPPLIER_ID": "供应商编号", "SUPPLIER_NAME": "供应商名称",
    "OUTSOURCE_STATUS": "状态", "MO_ID": "工单编号", "OP_SEQ": "工序",
    "OP_ID": "工艺编号", "OP_NAME": "工艺名称", "MA_ID": "产品编号",
    "MATERIAL_NAME": "产品名称", "SEND_QTY": "已发数量", "CAN_BACK_QTY": "待回货数量",
    "CREATE_TIME": "委外日期",
}
CN_HANDS = {
    "SUPPLIER_ID": "供应商编号", "SUPPLIER_NAME": "供应商名称",
    "HANDS_ORDER_CNT": "在手委外单数", "HANDS_SEND_QTY": "在手发货数量",
}


def render(title, cols, rows, out=sys.stdout):
    out.write("\n===== %s =====\n" % title)
    if not rows:
        out.write("(无数据)\n")
        return
    out.write(" | ".join(cols) + "\n")
    out.write("-" * 60 + "\n")
    for r in rows:
        out.write(" | ".join(str(v) for v in r) + "\n")


def main():
    ap = argparse.ArgumentParser(description="委外业务清单查询(接口数据源)")
    ap.add_argument("--todo", action="store_true", help="可委外清单(getCanOutsourceList)")
    ap.add_argument("--intransit", action="store_true", help="待回货清单(getOutSourceList)")
    ap.add_argument("--hands", action="store_true", help="供应商在手委外单汇总(getOutSourceDash)")
    ap.add_argument("--detail", help="指定委外单待回货信息(getOutSourceList)")
    ap.add_argument("--supplier", help="按供应商过滤(编号或名称)")
    ap.add_argument("--out", help="输出到文件")
    args = ap.parse_args()

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    try:
        if args.todo:
            rows = _query(ac.fetch_can_outsource, {"SUPPLIER_ID": "", "OP_ID": "", "MO_ID": "", "MA_ID": ""})
            rows = _filter(rows, supplier=args.supplier)
            sel = ["MO_ID", "MA_ID", "MATERIAL_NAME", "OP_SEQ", "OP_ID", "OP_NAME",
                   "SUPPLIER_ID", "SUPPLIER_NAME", "CANOUTQTY", "BACKDATE"]
            render("可委外清单(接口 getCanOutsourceList)", [CN_SEND.get(c, c) for c in sel],
                   [[r.get(c, "") for c in sel] for r in rows], out)

        if args.intransit:
            rows = _query(ac.fetch_back_list, {"SUPPLIER_ID": "", "OP_ID": "", "MO_ID": "", "MA_ID": "",
                                            "OUTSOURCE_ID": "", "OUTDATE_START": "", "OUTDATE_END": ""})
            rows = _filter(rows, supplier=args.supplier)
            sel = ["OUTSOURCE_ID", "SUPPLIER_ID", "SUPPLIER_NAME", "OUTSOURCE_STATUS", "MO_ID",
                   "OP_SEQ", "OP_ID", "OP_NAME", "MA_ID", "MATERIAL_NAME", "SEND_QTY", "CAN_BACK_QTY"]
            render("待回货清单(接口 getOutSourceList)", [CN_BACK.get(c, c) for c in sel],
                   [[r.get(c, "") for c in sel] for r in rows], out)

        if args.hands:
            cols, rows = ac.fetch_supplier_perf()
            if cols is None:
                sys.exit("❌ 绩效接口获取失败: %s" % rows)
            rows = [r for r in rows]
            if args.supplier:
                rows = [r for r in rows if args.supplier in str(r[0]) or args.supplier in str(r[1])]
            sel = [0, 1, 2, 3]
            render("供应商在手委外单汇总(接口 getOutSourceDash)",
                   [CN_HANDS.get(cols[i], cols[i]) for i in sel], [[r[i] for i in sel] for r in rows], out)

        if args.detail:
            rows = _query(ac.fetch_back_list, {"SUPPLIER_ID": "", "OP_ID": "", "MO_ID": "", "MA_ID": "",
                                            "OUTSOURCE_ID": args.detail, "OUTDATE_START": "", "OUTDATE_END": ""})
            sel = ["OUTSOURCE_ID", "SUPPLIER_ID", "SUPPLIER_NAME", "OUTSOURCE_STATUS", "MO_ID",
                   "OP_SEQ", "OP_ID", "OP_NAME", "MA_ID", "MATERIAL_NAME", "SEND_QTY", "CAN_BACK_QTY"]
            render("委外单 %s 待回货信息" % args.detail, [CN_BACK.get(c, c) for c in sel],
                   [[r.get(c, "") for c in sel] for r in rows], out)

        if not (args.todo or args.intransit or args.hands or args.detail):
            ap.print_help()
    finally:
        if args.out:
            out.close()
            print("已输出:", args.out)


if __name__ == "__main__":
    main()
