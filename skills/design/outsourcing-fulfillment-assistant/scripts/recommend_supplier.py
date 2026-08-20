#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""委外供应商推荐排序(选品选工艺 → 按绩效推荐)。

数据来源(2026-08-17 用户确认:本技能数据一律来自提供的 OPENAPI 接口,不读数据库):
  - 候选可委外工单: getCanOutsourceList(可委外清单)
  - 供应商绩效:      getOutSourceDash(近一年,无需参数)

流程:
  1. 调 getCanOutsourceList 取可委外工单(编号传接口过滤,中文名本地模糊匹配)
  2. 候选供应商 = 工单行预设供应商;预设为空扩到全部有绩效供应商
  3. 绩效排序(quality=良品率优先 / ontime=准交率优先 / 默认 quality),推荐第一名

用法(venv python):
  "$PY" recommend_supplier.py --product 石墨一号 [--process 涂抹石墨]
  "$PY" recommend_supplier.py --product SZJ001 [--op SZJ001] --priority ontime
  "$PY" recommend_supplier.py --mo SZJ-20260611017
"""
import argparse
import sys

import api_common as ac


def _is_code(s):
    """编号(字母/数字开头)才传给查询接口,中文名靠本地模糊匹配。"""
    return bool(s) and s[0].isascii() and s[0].isalnum()


def _match_contains(field_val, kw):
    if field_val is None:
        return False
    fv = str(field_val)
    if not fv:  # 空值不匹配任何关键词
        return False
    return str(kw) in fv or fv in str(kw)


def _match_rows(rows, field_groups, kws):
    """组内任一字段命中(OR),组间全部满足(AND)。"""
    hits = []
    for row in rows:
        ok = True
        for fields, kw in zip(field_groups, kws):
            if not kw:
                continue
            if not any(_match_contains(row.get(f), kw) for f in fields):
                ok = False
                break
        if ok:
            hits.append(row)
    return hits


def fetch_candidate(args):
    """实体A: 可委外清单(getCanOutsourceList)。编号参数传接口,中文名本地匹配。"""
    body = {"SUPPLIER_ID": "", "OP_ID": "", "MO_ID": "", "MA_ID": ""}
    if args.product and _is_code(args.product):
        body['MA_ID'] = args.product
    if args.process and _is_code(args.process):
        body['OP_ID'] = args.process
    if args.mo and _is_code(args.mo):
        body['MO_ID'] = args.mo
    lst, err = ac.fetch_can_outsource(body)
    if err:
        sys.exit("❌ " + err)
    # 本地模糊匹配(中文名)
    hits = _match_rows(lst, [['MA_ID', 'MATERIAL_NAME']], [args.product]) if args.product else lst
    if args.process:
        hits = _match_rows(hits, [['OP_ID', 'OP_NAME']], [args.process])
    if args.mo:
        hits = _match_rows(hits, [['MO_ID']], [args.mo])
    return hits


def render(title, cols, rows):
    print("\n===== %s =====" % title)
    if not rows:
        print("(无数据)")
        return
    print(" | ".join(cols))
    print("-" * 60)
    for r in rows:
        print(" | ".join(str(v) for v in r))


def main():
    ap = argparse.ArgumentParser(description="委外供应商推荐排序(接口数据源)")
    ap.add_argument("--product", help="产品(编号 MA_ID 或名称)")
    ap.add_argument("--process", help="工艺(编号 OP_ID 或名称)")
    ap.add_argument("--mo", help="工单编号 MO_ID")
    ap.add_argument("--priority", choices=["quality", "ontime", "auto"], default="auto",
                    help="排序策略: quality=良品率优先(默认), ontime=准交率优先(急单), auto=同quality")
    args = ap.parse_args()

    # 1. 候选可委外工单(接口)
    cand = fetch_candidate(args)
    if not cand:
        print("未找到可委外的工单(请核对产品/工艺/工单编号,或确认该工艺允许委外)")
        return
    cand_ops = set((r.get('OP_ID'), r.get('OP_NAME')) for r in cand)
    render("可委外工单(接口 getCanOutsourceList, 共%d行)" % len(cand),
           ["MO_ID", "产品编号", "产品名称", "工序", "工艺编号", "工艺名称", "预设供应商编号", "预设供应商名称", "可委外数量"],
           [[r.get('MO_ID'), r.get('MA_ID'), r.get('MATERIAL_NAME'), r.get('OP_SEQ'), r.get('OP_ID'),
             r.get('OP_NAME'), r.get('SUPPLIER_ID', ''), r.get('SUPPLIER_NAME', ''), r.get('CANOUTQTY')] for r in cand])

    # 2. 绩效(接口,近一年)
    cols_p, rows_p = ac.fetch_supplier_perf()
    if cols_p is None:
        sys.exit("❌ 供应商绩效接口获取失败: %s" % rows_p)
    perf = {r[0]: r for r in rows_p}
    perf_src = "接口 getOutSourceDash(近一年)"

    # 3. 候选供应商:预设供应商;预设为空扩到全部有绩效供应商
    preset = {r.get('SUPPLIER_ID') for r in cand if r.get('SUPPLIER_ID')}
    if preset:
        for sid in preset:
            if sid not in perf:
                perf[sid] = [sid, sid, 0, 0, None, None, 0, 0, 0, 0]
        ranked = [perf[sid] for sid in preset if sid in perf]
    else:
        ranked = list(rows_p)

    # 4. 排序(NULL 排最后)
    i_good, i_ontime, i_hands = cols_p.index('GOOD_RATE'), cols_p.index('ONTIME_RATE'), cols_p.index('HANDS_ORDER_CNT')
    if args.priority == "ontime":
        ranked.sort(key=lambda r: (r[i_ontime] is None, -(r[i_ontime] or 0), -(r[i_good] or 0), r[i_hands] or 0))
    else:
        ranked.sort(key=lambda r: (r[i_good] is None, -(r[i_good] or 0), -(r[i_ontime] or 0), r[i_hands] or 0))

    # 5. 输出
    sel = [0, 1, 2, 4, 5, 6]
    title = "供应商推荐(%s, 按%s排序)" % (
        perf_src, "准交率→良品率" if args.priority == "ontime" else "良品率→准交率")
    render(title, [cols_p[i] for i in sel], [tuple(r[i] for i in sel) for r in ranked])

    if ranked:
        top = ranked[0]
        print("\n★ 推荐供应商: %s(%s) 良品率=%s 准交率=%s 在手单数=%s" % (
            top[cols_p.index('SUPPLIER_NAME')], top[cols_p.index('SUPPLIER_ID')],
            top[i_good], top[i_ontime], top[i_hands]))
        print("  策略: %s | 候选工艺: %s" % (
            "急单优先(准交率最高)" if args.priority == "ontime" else "品质优先(良品率最高)",
            "、".join("%s(%s)" % (n, o) for o, n in cand_ops) or "全部"))


if __name__ == "__main__":
    main()
