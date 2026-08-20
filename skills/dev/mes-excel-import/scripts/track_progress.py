# -*- coding: utf-8 -*-
"""
导入进度跟踪 / 检核报告生成器（P0-2，对应方法论 3.7 / 4.1）

功能：
1. 《基础资料整理跟进表》：按标准导入顺序（工厂→车间→工艺→设备→物料→工单→工艺路线→订单→领料→仓库）
   汇总各接口导入状态（计划/成功/失败/完成率），输出 xlsx
2. 《期初工单导入进度跟踪表》（4.1）：从 mo_data(erpInsertMoid) 报告明细提取工单导入结果

用法:
  # 自动扫描 reports/ 目录最新报告 + 指定计划条数
  python track_progress.py --client "客户A" --plan "eq_data:120,material_data:300,mo_data:80"

  # 指定报告目录（默认 skill 下 reports/）
  python track_progress.py --client "客户A" --report-dir "D:/xx/reports" --out "D:/xx/跟进表.xlsx"

输出: {out 或 reports}/{客户}_基础资料整理跟进表.xlsx
  Sheet1 基础资料整理跟进表 / Sheet2 期初工单导入进度跟踪（有工单数据时）/ Sheet3 失败明细
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 标准导入顺序（方法论 3.7 + 交付数据导入顺序）
IMPORT_ORDER = [
    ("工厂",       "factory_data",    "erp_fb"),
    ("车间",       "workstation_data","erp_ws"),
    ("工艺",       "me_op_data",      "erp_ob"),
    ("设备",       "eq_data",         "erp_eq"),
    ("物料",       "material_data",   "erp_mb"),
    ("工单",       "mo_data",         "erpInsertMoid"),
    ("工艺路线",   "process_route_data","erp_prb"),
    ("订单",       "order_data",      "erp_sod"),
    ("领料",       "process_route_detail_data", "erp_mrd"),
    ("仓库",       "warehouse_data",  "erp_wb"),
    ("检验",       "pqc_data",        "erp_ipd"),
    ("点检方案",   "emcheck_data",    "erp_emcheck"),
    ("模具",       "mold_data",       "erp_mold"),
]

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_DIR = ROOT / "reports"


def newest_report(report_dir, api_name, ep_name):
    """找 reports/ 下该接口最新的 xlsx 或 json 报告"""
    pats = [f"{api_name}_*.xlsx", f"{api_name}_*.json",
            f"{ep_name}_*.xlsx", f"{ep_name}_*.json"]
    cands = []
    for p in pats:
        cands += glob.glob(str(report_dir / p))
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def parse_report(path):
    """解析报告文件 → {success, failed, format_errors, rows:[{row,ok,error}...]}"""
    res = {"success": 0, "failed": 0, "format_errors": 0, "rows": []}
    try:
        if path.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            results = d.get("results", [])
            for r in results:
                ok = r.get("ok", False)
                res["rows"].append({"row": r.get("row"), "ok": ok, "error": r.get("error", "")})
                if ok:
                    res["success"] += 1
                else:
                    res["failed"] += 1
            res["format_errors"] = len(d.get("row_errors", []))
            return res
        # xlsx
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        if "汇总" in wb.sheetnames:
            for row in wb["汇总"].iter_rows(values_only=True):
                if not row or row[0] is None:
                    continue
                k, v = str(row[0]), row[1]
                if k == "成功":
                    res["success"] = int(v or 0)
                elif k == "失败":
                    res["failed"] = int(v or 0)
        if "明细" in wb.sheetnames:
            ws = wb["明细"]
            header = None
            for row in ws.iter_rows(values_only=True):
                if header is None:
                    header = list(row)
                    continue
                if not row or row[0] is None:
                    continue
                ok = str(row[1]) in ("成功", "True", "true")
                err = ""
                if "错误原因" in header:
                    err = str(row[header.index("错误原因")] or "")
                res["rows"].append({"row": row[0], "ok": ok, "error": err})
        wb.close()
        return res
    except Exception as e:
        res["error"] = str(e)
        return res


def build_tracking(rows, plan_map):
    """期初工单导入进度跟踪表（4.1）"""
    track = []
    for r in rows:
        if r.get("row") is None:
            continue
        track.append({
            "行号": r["row"],
            "工单号": str(r.get("wo_no") or r.get("MO_ID") or r.get("mo_no") or ""),
            "导入结果": "成功" if r["ok"] else "失败",
            "失败原因": r.get("error") or "",
        })
    return track


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, help="客户名（用于输出文件名）")
    ap.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="报告目录（默认 skill reports/）")
    ap.add_argument("--plan", default="", help="计划条数，格式 'api名:条数,...' 如 eq_data:120,material_data:300")
    ap.add_argument("--out", default="", help="输出 xlsx 路径（默认 report-dir/{客户}_基础资料整理跟进表.xlsx）")
    args = ap.parse_args()

    report_dir = Path(args.report_dir)
    plan_map = {}
    for item in args.plan.split(","):
        if ":" in item:
            k, v = item.split(":", 1)
            plan_map[k.strip()] = int(v.strip())

    # 1. 汇总各接口
    rows = []
    for name, api_name, ep_name in IMPORT_ORDER:
        rep = newest_report(report_dir, api_name, ep_name)
        if not rep:
            rows.append({
                "顺序": len(rows) + 1, "资料类别": name, "接口": api_name,
                "计划条数": plan_map.get(api_name, ""), "成功": "", "失败": "",
                "格式错误": "", "状态": "未导入", "完成率": "", "报告": ""
            })
            continue
        parsed = parse_report(rep)
        succ, fail = parsed["success"], parsed["failed"]
        fmt_err = parsed["format_errors"]
        plan = plan_map.get(api_name)
        rate = ""
        if plan:
            rate = f"{round(succ / plan * 100, 1)}%" if plan else ""
        status = "✅ 完成" if plan and succ >= plan else ("⚠️ 部分" if succ else "❌ 全部失败")
        if not plan:
            status = "✅ 已导入" if succ else "❌ 失败"
        rows.append({
            "顺序": len(rows) + 1, "资料类别": name, "接口": api_name,
            "计划条数": plan if plan else "", "成功": succ, "失败": fail,
            "格式错误": fmt_err, "状态": status, "完成率": rate,
            "报告": os.path.basename(rep)
        })

    # 2. 工单进度（4.1）：从 mo_data 报告明细提取
    wo_rows = []
    mo_rep = newest_report(report_dir, "mo_data", "erpInsertMoid")
    if mo_rep:
        parsed = parse_report(mo_rep)
        wo_rows = build_tracking(parsed["rows"], plan_map)

    # 3. 输出 xlsx
    out = args.out or str(report_dir / f"{args.client}_基础资料整理跟进表.xlsx")
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    # Sheet1 跟进表
    ws = wb.active
    ws.title = "基础资料整理跟进表"
    ws.append(["客户", args.client, "", "生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    ws.append([])
    headers = ["顺序", "资料类别", "接口", "计划条数", "成功", "失败", "格式错误", "状态", "完成率", "报告文件"]
    ws.append(headers)
    hfill = PatternFill("solid", fgColor="0B3D91")
    for c in ws[ws.max_row]:
        c.font = Font(color="FFFFFF", bold=True)
        c.fill = hfill
    ok_fill = PatternFill("solid", fgColor="C6EFCE")
    warn_fill = PatternFill("solid", fgColor="FFEB9C")
    err_fill = PatternFill("solid", fgColor="FFC7CE")
    for r in rows:
        ws.append([r["顺序"], r["资料类别"], r["接口"], r["计划条数"], r["成功"], r["失败"],
                   r["格式错误"], r["状态"], r["完成率"], r["报告"]])
        row = ws[ws.max_row]
        if r["状态"].startswith("✅"):
            for c in row:
                c.fill = ok_fill
        elif r["状态"].startswith("⚠️"):
            for c in row:
                c.fill = warn_fill
        elif r["状态"].startswith("❌") or r["状态"] == "未导入":
            for c in row:
                c.fill = err_fill
    for col, w in zip("ABCDEFGHIJ", [6, 14, 26, 10, 8, 8, 10, 12, 10, 30]):
        ws.column_dimensions[col].width = w

    # Sheet2 期初工单导入进度
    ws2 = wb.create_sheet("期初工单导入进度")
    ws2.append(["客户", args.client])
    ws2.append([])
    ws2.append(["行号", "工单号", "导入结果", "失败原因"])
    for c in ws2[ws2.max_row]:
        c.font = Font(color="FFFFFF", bold=True)
        c.fill = hfill
    for t in wo_rows:
        ws2.append([t["行号"], t["工单号"], t["导入结果"], t["失败原因"]])
    for col, w in zip("ABCD", [8, 30, 12, 60]):
        ws2.column_dimensions[col].width = w

    # Sheet3 失败明细（全接口）
    ws3 = wb.create_sheet("失败明细")
    ws3.append(["接口", "行号", "错误原因"])
    for c in ws3[ws3.max_row]:
        c.font = Font(color="FFFFFF", bold=True)
        c.fill = hfill
    for name, api_name, ep_name in IMPORT_ORDER:
        rep = newest_report(report_dir, api_name, ep_name)
        if not rep:
            continue
        parsed = parse_report(rep)
        for r in parsed["rows"]:
            if not r["ok"]:
                ws3.append([api_name, r["row"], r.get("error", "")])
    for col, w in zip("ABC", [26, 10, 80]):
        ws3.column_dimensions[col].width = w

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"已生成: {out}")
    print(f"  基础资料接口统计: {len(rows)} 项（成功导入 {sum(1 for r in rows if r['状态'].startswith('✅'))} 项）")
    if wo_rows:
        ok_n = sum(1 for t in wo_rows if t["导入结果"] == "成功")
        print(f"  期初工单导入: {len(wo_rows)} 条（成功 {ok_n} / 失败 {len(wo_rows)-ok_n}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
