# -*- coding: utf-8 -*-
"""供应商绩效查询(委外发货前必查):良品率 / 准交率 / 逾期 / 全景汇总。

⚠️ 绩效数据一律来自 OpenAPI 接口 getOutSourceDash(近一年,无需参数),不读数据库。
   (2026-08-17 用户确认:供应商绩效只能调接口获取)

用法(venv python):
  "$PY" supplier_perf.py --perf [--supplier X]        # 全景(在手单+良品率+准交率+逾期),近一年
  "$PY" supplier_perf.py --quality [--supplier X]     # 按良品率排序
  "$PY" supplier_perf.py --ontime [--supplier X]      # 按准交率排序
  "$PY" supplier_perf.py --overdue                    # 逾期说明(接口无明细,提示)
  "$PY" supplier_perf.py --perf --supplier CNC --out report.md

口径(2026-08-17 经接口与数据库双源对比验证):
  - 良品率 = 验收合格/(合格+验退),回货验收口径
  - 准交率 = 已完成委外单中最后一批回货日期<=要求回货日期的单占比(按单聚合,当天回货算准时)
  - 在手委外单数 = 委外中状态的单数(按单号去重)
  - 无回货记录的供应商接口返回 0.0(推荐排序自然靠后)
"""
import argparse
import sys

import api_common as ac

# 中文列名映射(展示层)
CN_COLS = {
    "SUPPLIER_ID": "供应商编号",
    "SUPPLIER_NAME": "供应商名称",
    "HANDS_ORDER_CNT": "在手委外单数",
    "HANDS_SEND_QTY": "在手发货数量",
    "GOOD_RATE": "良品率",
    "CHECK_TOTAL_QTY": "验收总数",
    "NG_QTY": "验退不良数",
    "ONTIME_RATE": "准交率",
    "FINISHED_CNT": "已完成单数",
    "OVERDUE_CNT": "逾期单数",
}


def render(title, cols, rows, out=sys.stdout):
    out.write("\n===== %s =====\n" % title)
    if not rows:
        out.write("(无数据)\n")
        return
    heads = [CN_COLS.get(c, c) for c in cols]
    out.write(" | ".join(heads) + "\n")
    out.write("-" * 60 + "\n")
    for r in rows:
        out.write(" | ".join(str(v) for v in r) + "\n")


def fetch():
    """调接口获取供应商绩效(近一年)。失败直接报错退出(绩效不落数据库)。"""
    cols, rows = ac.fetch_supplier_perf()
    if cols is None:
        sys.exit("❌ 绩效接口获取失败: %s(供应商绩效已停用数据库源)" % rows)
    return cols, rows


def filter_supplier(rows, supplier):
    if not supplier:
        return rows
    return [r for r in rows if supplier in str(r[0]) or supplier in str(r[1])]


def main():
    ap = argparse.ArgumentParser(description="供应商绩效查询(接口 getOutSourceDash,近一年)")
    ap.add_argument("--perf", action="store_true", help="全景汇总(在手单+良品率+准交率)")
    ap.add_argument("--quality", action="store_true", help="按良品率排序")
    ap.add_argument("--ontime", action="store_true", help="按准交率排序")
    ap.add_argument("--overdue", action="store_true", help="逾期说明(接口无明细)")
    ap.add_argument("--supplier", help="指定供应商(编号或名称片段)")
    ap.add_argument("--days", type=int, default=90, help="保留参数:接口固定近一年,此参数仅数据库模式有效(已停用)")
    ap.add_argument("--out", help="输出到文件")
    args = ap.parse_args()

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    try:
        cols, rows = fetch()
        rows = filter_supplier(rows, args.supplier)
        if not rows:
            render("供应商绩效(近一年,接口)", cols, [], out)
            return

        if args.quality:
            sel = [0, 1, 4, 5, 6, 7, 9]
            data = [tuple(r[i] for i in sel) for r in sorted(rows, key=lambda r: -(r[4] or 0))]
            render("供应商良品率排序(接口,近一年)", [cols[i] for i in sel], data, out)
        elif args.ontime:
            sel = [0, 1, 5, 4, 6, 7, 9]
            data = [tuple(r[i] for i in sel) for r in sorted(rows, key=lambda r: -(r[5] or 0))]
            render("供应商准交率排序(接口,近一年)", [cols[i] for i in sel], data, out)
        elif args.overdue:
            sel = [0, 1, 9, 8, 7, 6]
            data = [tuple(r[i] for i in sel) for r in sorted(rows, key=lambda r: -(r[9] or 0))]
            render("供应商逾期单数(接口,近一年;明细需另配接口)", [cols[i] for i in sel], data, out)
        else:  # 默认 perf 全景
            render("供应商委外全景汇总(接口 getOutSourceDash,近一年)", cols, rows, out)
    finally:
        if args.out:
            out.close()
            print("已输出:", args.out)


if __name__ == "__main__":
    main()
