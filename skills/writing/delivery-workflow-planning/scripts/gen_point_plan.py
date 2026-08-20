# -*- coding: utf-8 -*-
"""
报工点位与硬件规划生成器（方法论 3.4，随实施流程规划输出）

依据调研的车间/产线/人员/设备布局，按选型原则生成：
- Sheet1 报工点位规划：车间/产线 | 生产方式 | 点位类型 | 点位数量 | 覆盖设备/人员 | 备注
- Sheet2 硬件采购清单：硬件 | 数量 | 用途 | 客户利旧项

选型原则（与 references/报工点位规划.md 一致）：
- fixed  固定设备为主        → 工位机+扫码枪，max(1, ceil(设备数/5)) 台（4-6台/台）
- zone   车间界限明确        → 工位机+扫码枪，每车间1台起步，设备密集按 ceil(设备数/5) 叠加
- line   流水线/组装         → 工位机，每产线 1-2 台（默认1）
- mobile 人员多且独立报工     → 移动端（手机/PDA），按操作工 1:1
- qc     质检人员            → 移动端（手机/PDA），按质检人数 1:1

用法:
  python gen_point_plan.py --client "客户名" \
    --plan "PVC车间:fixed:8:6:1,拉丝车间:fixed:12:4:1,组装线1:line:0:10:0,质检科:qc:0:0:3" \
    --out "输出目录/{客户名}_报工点位规划.xlsx"
"""
import argparse
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# 模式 → (点位类型, 数量函数)
def qty_fixed(dev, ppl, qc):     return max(1, math.ceil(dev / 5))
def qty_zone(dev, ppl, qc):      return max(1, math.ceil(dev / 5)) if dev else 1
def qty_line(dev, ppl, qc):      return 1  # 每产线 1 台（产线数即 --plan 条目数）
def qty_mobile(dev, ppl, qc):    return max(1, ppl)
def qty_qc(dev, ppl, qc):        return max(1, qc)

MODE_DEF = {
    "fixed":  {"type": "工位机 + 扫码枪", "qty": qty_fixed, "note": "固定设备为主，1台覆盖4-6台设备"},
    "zone":   {"type": "工位机 + 扫码枪", "qty": qty_zone, "note": "车间界限明确，按车间布点，设备密集叠加"},
    "line":   {"type": "工位机", "qty": qty_line, "note": "流水线/组装车间，按产线布点"},
    "mobile": {"type": "移动端（手机/PDA）", "qty": qty_mobile, "note": "人员多且独立报工，按人1:1"},
    "qc":     {"type": "移动端（手机/PDA）", "qty": qty_qc, "note": "质检人员流动性强，标配移动端"},
}

MODE_NAME = {"fixed": "固定设备", "zone": "车间界限", "line": "流水线/组装",
             "mobile": "人员独立报工", "qc": "质检"}


def parse_plan(s):
    """'PVC车间:fixed:8:6:1,...' → [(name, mode, dev, ppl, qc)]"""
    out = []
    for item in s.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        name = parts[0].strip()
        mode = parts[1].strip().lower() if len(parts) > 1 else "fixed"
        dev = int(float(parts[2])) if len(parts) > 2 and parts[2] else 0
        ppl = int(float(parts[3])) if len(parts) > 3 and parts[3] else 0
        qc = int(float(parts[4])) if len(parts) > 4 and parts[4] else 0
        out.append((name, mode, dev, ppl, qc))
    return out


def build_rows(plan):
    rows = []
    for name, mode, dev, ppl, qc in plan:
        d = MODE_DEF.get(mode)
        if not d:
            d = MODE_DEF["fixed"]
            mode = "fixed"
        qty = d["qty"](dev, ppl, qc)
        cover = []
        if dev:
            cover.append(f"{dev}台设备")
        if ppl:
            cover.append(f"{ppl}人")
        if qc:
            cover.append(f"{qc}名质检")
        rows.append({
            "name": name, "mode": MODE_NAME[mode], "type": d["type"], "qty": qty,
            "cover": "、".join(cover) if cover else "-", "note": d["note"],
        })
    return rows


def build_hardware(rows):
    """汇总硬件采购清单：工位机 / 扫码枪 / 移动端"""
    wc = sum(r["qty"] for r in rows if "工位机" in r["type"])
    gun = wc  # 每工位机配1扫码枪（可调）
    mob = sum(r["qty"] for r in rows if "移动端" in r["type"])
    hw = []
    if wc:
        hw.append({"hw": "工位机（含支架）", "qty": wc, "use": "固定设备/流水线报工", "reuse": "可利旧客户电脑+外接屏"})
    if gun:
        hw.append({"hw": "扫码枪（USB/无线）", "qty": gun, "use": "工位机扫码报工", "reuse": "可利旧客户现有扫码枪"})
    if mob:
        hw.append({"hw": "移动终端（手机/PDA）", "qty": mob, "use": "人员独立报工/质检移动登记", "reuse": "可利旧客户手机（装APPA）"})
    return hw


def gen(client, plan, out_path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    rows = build_rows(plan)
    hw = build_hardware(rows)

    wb = Workbook()
    # Sheet1 点位规划
    ws = wb.active
    ws.title = "报工点位规划"
    ws.append(["客户", client, "", "生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    ws.append([])
    headers = ["车间/产线", "生产方式", "点位类型", "点位数量", "覆盖设备/人员", "选型说明"]
    ws.append(headers)
    hfill = PatternFill("solid", fgColor="0B3D91")
    for c in ws[ws.max_row]:
        c.font = Font(color="FFFFFF", bold=True)
        c.fill = hfill
    for r in rows:
        ws.append([r["name"], r["mode"], r["type"], r["qty"], r["cover"], r["note"]])
    ws.append([])
    ws.append(["合计工位机", sum(1 for r in rows if "工位机" in r["type"] and r["qty"])])
    ws.append(["合计移动端", sum(r["qty"] for r in rows if "移动端" in r["type"])])
    for col, w in zip("ABCDEF", [16, 14, 22, 10, 22, 40]):
        ws.column_dimensions[col].width = w

    # Sheet2 硬件采购清单
    ws2 = wb.create_sheet("硬件采购清单")
    ws2.append(["硬件", "数量", "用途", "客户利旧项"])
    for c in ws2[ws2.max_row]:
        c.font = Font(color="FFFFFF", bold=True)
        c.fill = hfill
    for h in hw:
        ws2.append([h["hw"], h["qty"], h["use"], h["reuse"]])
    for col, w in zip("ABCD", [24, 8, 34, 34]):
        ws2.column_dimensions[col].width = w

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wb.save(out_path)
    print(f"已生成: {out_path}")
    print(f"  点位: {len(rows)} 个车间/产线 · 工位机 {sum(r['qty'] for r in rows if '工位机' in r['type'])} 台 · 移动端 {sum(r['qty'] for r in rows if '移动端' in r['type'])} 台")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--plan", required=True, help='车间:模式:设备数:人数:质检数，逗号分隔；模式=fixed/zone/line/mobile/qc')
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    plan = parse_plan(args.plan)
    gen(args.client, plan, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
