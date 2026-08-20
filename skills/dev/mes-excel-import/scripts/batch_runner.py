# -*- coding: utf-8 -*-
"""
批量调度模块：客户一份 Excel → 内部自动分批调用 → 进度显示 → 失败容错 → 生成报告。
- 客户无需拆分文档，本模块按 spec.batch_size 自动分批
- batch_mode: "array"   -> 每批传整个对象数组（接口支持批量时）
             "single"  -> 逐条调用（接口仅支持单条时）
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_payload import load_spec, build_payload, validate_spec
from call_api import call_api
from parse_excel import read_excel

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def run_delivery(api_name, excel_path, sheet_name=None, col_map=None,
                 batch_size=None, dry_run=False, progress=True):
    """
    执行一次数据交付。
    api_name: 接口名（eq_data 等）
    excel_path: 客户 Excel 路径
    sheet_name: 指定 sheet（None 自动取第一个）
    col_map: 智能映射 {api_field: excel列名}，None 用 spec 默认映射
    batch_size: 覆盖 spec 中的批大小
    dry_run: 只校验不调用（检查必填/格式）
    progress: 打印进度
    返回: 汇总 dict
    """
    spec = load_spec(api_name)
    spec_errs = validate_spec(spec)
    if spec_errs:
        return {"ok": False, "error": "接口定义错误: " + "; ".join(spec_errs)}

    # 1. 读 Excel（大数据量支持）
    data = read_excel(excel_path, sheet_name=sheet_name)
    rows = data["rows"]
    total = data["total"]
    if total == 0:
        return {"ok": False, "error": "Excel 中没有数据行"}
    if progress:
        print(f"[1/4] 读取 Excel: sheet={data['sheet']} 共 {total} 行")

    # 2. 逐行构建参数 + 必填校验（嵌套接口 head 字段前向填充）
    payloads = []
    row_errors = []
    last_head = {}
    nested = "nested" in spec
    for i, row in enumerate(rows, start=1):
        if nested:
            # head 字段若为空则复用上一行（客户 Excel 常只写首行）
            for hf in spec["nested"].get("head", []):
                col = None
                if col_map and hf["api_field"] in col_map:
                    col = col_map[hf["api_field"]]
                elif hf.get("source", {}).get("col"):
                    col = hf["source"]["col"]
                if col:
                    v = row.get(col)
                    if v is None or (isinstance(v, str) and v.strip() == ""):
                        if hf["api_field"] in last_head:
                            row[col] = last_head[hf["api_field"]]
        payload, errs = build_payload(row, spec, col_map)
        if nested and isinstance(payload, dict) and "head" in payload:
            last_head.update(payload["head"])
        if errs:
            row_errors.append({"row": i, "data": row, "errors": errs})
        else:
            payloads.append(payload)
    if progress:
        print(f"[2/4] 参数组装完成: 有效 {len(payloads)} 行, 格式错误 {len(row_errors)} 行")

    if dry_run:
        return {"ok": True, "dry_run": True, "total": total, "valid": len(payloads),
                "row_errors": row_errors, "payloads": payloads}

    if not payloads:
        return {"ok": False, "error": "没有可提交的有效行", "row_errors": row_errors}

    # 嵌套接口：按 head 主键合并 body（一条主记录 = head + 多条明细）
    if nested:
        merged = {}
        order = []
        merged_row = {}  # key -> 首行号
        for i, p in enumerate(payloads, start=1):
            head = p.get("head", {})
            key = json.dumps(head, sort_keys=True, ensure_ascii=False)
            if key not in merged:
                merged[key] = {"head": head, "body": []}
                order.append(key)
                merged_row[key] = i
            merged[key]["body"].extend(p.get("body", []))
        payloads = [merged[k] for k in order]
        if progress and len(payloads) != total:
            print(f"  嵌套合并: {total} 行明细 → {len(payloads)} 条主记录（head 相同自动合并）")
        row_of = {i: merged_row[k] for i, k in enumerate(order)}

    # 3. 分批调用
    bs = batch_size or spec.get("batch_size") or 500
    batch_mode = spec.get("batch_mode", "array")
    payload_cfg = spec.get("payload", {})
    op_type = payload_cfg.get("OperationType", 0) if isinstance(payload_cfg, dict) else 0
    # 支持 col_map 覆盖 OperationType（Excel 含"操作类型"列时）
    if col_map and "OperationType" in col_map:
        op_col = col_map["OperationType"]
        op_type = None  # 每批从行数据取

    ok_rule = spec.get("success_rule", {})
    ok_key = ok_rule.get("ok_key", "res")
    ok_value = ok_rule.get("ok_value", True)
    fail_key = ok_rule.get("fail_key", "code")
    fail_value = ok_rule.get("fail_value", 1)

    results = []  # 每行: {"row": 行号, "ok": bool, "resp": 返回, "error": 错误}
    success = 0
    failed = 0

    def check_resp(data):
        """解析响应：res=true 或 code=0 成功；code=1 失败取 message"""
        if not isinstance(data, dict):
            return False, str(data)[:200]
        # 优先看 ok_key（如 res: true）
        if ok_key in data:
            return data[ok_key] == ok_value, str(data.get("message") or "")
        # 再看 fail_key（如 code: 0 成功 / 1 失败）
        if fail_key in data:
            code = data[fail_key]
            if code == 0:
                return True, str(data.get("message") or "")
            return False, str(data.get("message") or data)
        return True, str(data.get("message") or "")

    batches = list(chunk_list(payloads, bs))
    if progress:
        print(f"[3/4] 开始调用（{batch_mode} 模式, 每批 {bs} 条, 共 {len(batches)} 批）")

    for bi, batch in enumerate(batches, start=1):
        if progress:
            print(f"  批 {bi}/{len(batches)} 处理中...", end="", flush=True)
        t0 = time.time()

        if batch_mode == "array":
            # 组装整批请求: {OperationType, content: [...]}
            body = {"content": batch}
            if op_type is not None:
                body["OperationType"] = op_type
            elif col_map and "OperationType" in col_map:
                op_col = col_map["OperationType"]
                v = rows[bi * bs - bs].get(op_col)  # 用批首行的操作类型
                body["OperationType"] = int(float(str(v))) if str(v).strip().isdigit() else 0
            resp = call_api(spec["endpoint"], body)
            # 整批成功/失败，逐元素展开
            biz_ok, biz_msg = check_resp(resp.get("data"))
            ok = resp["ok"] and biz_ok
            err_msg = resp.get("error") or (biz_msg if not biz_ok else None)
            for pi, p in enumerate(batch):
                results.append({
                    "row": row_of[pi + (bi - 1) * bs] if nested else pi + 1 + (bi - 1) * bs,
                    "ok": ok,
                    "resp": resp.get("data") if ok else None,
                    "error": err_msg,
                })
            if ok:
                success += len(batch)
            else:
                failed += len(batch)
        else:  # single 逐条
            for pi, p in enumerate(batch):
                body = {"content": [p]}
                if op_type is not None:
                    body["OperationType"] = op_type
                resp = call_api(spec["endpoint"], body)
                biz_ok, biz_msg = check_resp(resp.get("data"))
                ok = resp["ok"] and biz_ok
                results.append({
                    "row": row_of[pi + (bi - 1) * bs] if nested else pi + 1 + (bi - 1) * bs,
                    "ok": ok,
                    "resp": resp.get("data") if ok else None,
                    "error": resp.get("error") or (biz_msg if not biz_ok else None),
                })
                if ok:
                    success += 1
                else:
                    failed += 1
        if progress:
            print(f"  {time.time()-t0:.1f}s 累计成功 {success} / 失败 {failed}")

    # 4. 生成报告
    report_path = write_report(api_name, rows, results, row_errors, spec)
    if progress:
        print(f"[4/4] 完成。成功 {success} 条, 失败 {failed} 条, 报告: {report_path}")

    return {
        "ok": True,
        "api_name": api_name,
        "total": total,
        "valid": len(payloads),
        "success": success,
        "failed": failed,
        "row_errors": row_errors,   # 参数组装阶段错误（格式问题）
        "api_failures": [r for r in results if not r["ok"]],
        "report_path": str(report_path),
    }


def write_report(api_name, rows, results, row_errors, spec):
    """生成结果报告 xlsx：成功行 / 失败行+原因"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{api_name}_{ts}.xlsx"

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        wb = Workbook()
        # Sheet1: 汇总
        ws_sum = wb.active
        ws_sum.title = "汇总"
        ws_sum.append(["接口", api_name])
        ws_sum.append(["总行数", len(rows)])
        ws_sum.append(["成功", sum(1 for r in results if r["ok"])])
        ws_sum.append(["失败", sum(1 for r in results if not r["ok"]) + len(row_errors)])
        ws_sum.append(["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

        # Sheet2: 明细（原始数据 + 结果）
        ws_det = wb.create_sheet("明细")
        headers = ["行号", "结果"] + list(data_headers(rows)) + ["接口返回", "错误原因"]
        ws_det.append(headers)
        red_fill = PatternFill("solid", fgColor="FFC7CE")
        green_fill = PatternFill("solid", fgColor="C6EFCE")

        # 组装阶段错误（未提交）
        err_map = {e["row"]: e for e in row_errors}
        # 调用阶段结果
        res_map = {r["row"]: r for r in results}
        all_rows = set(err_map) | set(res_map)
        for rn in sorted(all_rows):
            orig = rows[rn - 1]
            if rn in err_map:
                line = [rn, "格式错误"] + list(orig.values()) + ["", "；".join(err_map[rn]["errors"])]
                ws_det.append(line)
                for c in ws_det[ws_det.max_row]:
                    c.fill = red_fill
            else:
                r = res_map[rn]
                resp_str = ""
                if r.get("resp") is not None:
                    resp_str = json.dumps(r["resp"], ensure_ascii=False, default=str)[:2000]
                line = [rn, "成功" if r["ok"] else "失败"] + list(orig.values()) + [resp_str, r.get("error") or ""]
                ws_det.append(line)
                if not r["ok"]:
                    for c in ws_det[ws_det.max_row]:
                        c.fill = red_fill
                else:
                    for c in ws_det[ws_det.max_row]:
                        c.fill = green_fill

        wb.save(path)
    except Exception as e:
        # 报告失败不阻断主流程，写 JSON 兜底
        path = path.with_suffix(".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"api": api_name, "results": results, "row_errors": row_errors},
                      f, ensure_ascii=False, default=str)
        print(f"  报告 xlsx 生成失败({e})，已用 JSON 兜底")
    return path


def data_headers(rows):
    if not rows:
        return []
    return list(rows[0].keys())


if __name__ == "__main__":
    # 用法: python batch_runner.py <api_name> <excel_path> [--dry-run] [--sheet SHEET] [--batch N] [--map '{json}']
    args = sys.argv[1:]
    if len(args) < 2:
        print("用法: python batch_runner.py <api_name> <excel_path> [--dry-run] [--sheet SHEET] [--batch N] [--map '{json}']")
        sys.exit(1)
    api, xlsx = args[0], args[1]
    kwargs = {}
    if "--dry-run" in args:
        kwargs["dry_run"] = True
    if "--sheet" in args:
        kwargs["sheet_name"] = args[args.index("--sheet") + 1]
    if "--batch" in args:
        kwargs["batch_size"] = int(args[args.index("--batch") + 1])
    if "--map" in args:
        kwargs["col_map"] = json.loads(args[args.index("--map") + 1])
    result = run_delivery(api, xlsx, **kwargs)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
