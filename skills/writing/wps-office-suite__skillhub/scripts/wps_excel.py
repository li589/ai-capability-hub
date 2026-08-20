"""
WPS Excel CLI v4.7 - 完整命令集（含 Excel 智能分析 + 数据图表生成器 + 公式解释器）
"""
import subprocess
import json
import sys
from pathlib import Path

WORKER = Path(__file__).parent / "wps_worker.py"


def call_worker(cmd: str, args: dict) -> dict:
    """调用 Worker（带超时和错误处理）"""
    import time
    req = json.dumps({"cmd": cmd, "args": args}, ensure_ascii=False)
    proc = subprocess.Popen(
        [sys.executable, str(WORKER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent.parent),
    )
    cfg = {"timeout": 120}
    try:
        from wps_performance import get_worker_config
        cfg = get_worker_config()
    except Exception:
        pass
    
    timeout = cfg.get("timeout", 120)
    
    try:
        stdout, stderr = proc.communicate(input=req.encode("utf-8"), timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return {"ok": False, "error": f"操作超时（{timeout}秒），请检查文件是否过大或WPS是否卡住"}
    
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8") if stderr else "未知错误"
        return {"ok": False, "error": f"WPS Worker 异常: {err_msg[:200]}"}
    try:
        return json.loads(stdout.decode("utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "error": "Worker 输出解析失败"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="WPS Excel v4.7")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create")
    p.add_argument("--name", required=True)
    p.add_argument("--sheets", default="")
    p.add_argument("--filepath", default="")
    p.add_argument("--data", default="", help='JSON: {"Sheet1":[["A",1]]}')

    p = sub.add_parser("input")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--data", required=True, help='JSON array [["col1","col2"]]')

    p = sub.add_parser("formula")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--cell", required=True)
    p.add_argument("--formula", required=True)

    p = sub.add_parser("sort")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--sorts", required=True, help='JSON: [{"column":"金额","ascending":false}]')

    p = sub.add_parser("filter")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--conditions", required=True, help='JSON: [{"column":"金额","op":">","value":"1000"}]')
    p.add_argument("--logic", choices=["AND", "OR"], default="AND")

    p = sub.add_parser("chart")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--type", choices=["bar", "line", "pie", "column"], default="bar")
    p.add_argument("--data", default="A1:B10", help="数据范围")
    p.add_argument("--title", default="")

    p = sub.add_parser("add-sheet")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", required=True)
    p.add_argument("--headers", default="")
    p.add_argument("--data", default="")

    p = sub.add_parser("stats")
    p.add_argument("--file", required=True)
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--column", required=True)
    p.add_argument("--type", choices=["SUM", "AVG", "COUNT", "MAX", "MIN", "COUNTA"], default="SUM")

    p = sub.add_parser("info")
    p.add_argument("--file", required=True)

    p = sub.add_parser("engine-info", help="引擎+硬件信息")

    p = sub.add_parser("check-update", help="检查更新")

    p = sub.add_parser("nl-analyze", help="自然语言数据分析（如：按月份统计销售额并画趋势图）")
    p.add_argument("--file", required=True, help="Excel 文件路径")
    p.add_argument("--query", required=True, help="自然语言查询")
    p.add_argument("--sheet", default="Sheet1")

    p = sub.add_parser("invoice", help="发票 OCR 入账（PDF/图片 → Excel）")
    p.add_argument("--input", required=True, help="发票文件路径（PDF/图片）")
    p.add_argument("--output", default="", help="输出 Excel 路径")

    p = sub.add_parser("excel-analyze", help="Excel 深度分析（公式纠错/数据清洗/透视表/预测/NL2Formula）")
    p.add_argument("--file", required=True, help="Excel 文件路径")
    p.add_argument("--task", default="profile",
                   choices=["profile", "fix_formulas", "pivot", "predict", "nl2formula", "clean"],
                   help="分析任务类型")
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--column", help="预测列名（predict 任务）")
    p.add_argument("--method", default="auto", help="预测方法: auto/moving_avg/exponential/linear")
    p.add_argument("--steps", type=int, default=3, help="预测步数")
    p.add_argument("--query", help="自然语言查询（nl2formula 任务）")
    p.add_argument("--use-llm", action="store_true", help="使用 LLM 辅助（可选）")
    p.add_argument("--row-field", help="透视表行字段")
    p.add_argument("--value-field", help="透视表值字段")
    p.add_argument("--col-field", help="透视表列字段")
    p.add_argument("--agg-func", default="sum", help="透视表聚合方式")

    # v4.6: Excel 智能分析统一入口（合并 6 命令为 1 个）
    p = sub.add_parser("excel-smart", help="Excel 智能分析（统一入口，--action 路由到对应功能）")
    p.add_argument("--file", required=True, help="Excel 文件路径")
    p.add_argument("--action", default="profile",
                   choices=["profile", "fix_formulas", "pivot", "predict", "nl2formula", "clean", "hardware"],
                   help="分析动作")
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--column", help="预测/分析列名")
    p.add_argument("--method", default="auto", help="预测方法: auto/moving_avg/exponential/linear")
    p.add_argument("--steps", type=int, default=3, help="预测步数")
    p.add_argument("--query", help="自然语言查询（nl2formula 动作）")
    p.add_argument("--use-llm", action="store_true", help="使用 LLM 辅助（可选）")
    p.add_argument("--row-field", help="透视表行字段")
    p.add_argument("--value-field", help="透视表值字段")
    p.add_argument("--col-field", help="透视表列字段")
    p.add_argument("--agg-func", default="sum", help="透视表聚合方式")

    # v4.6: 数据图表生成器
    p = sub.add_parser("chart-gen", help="数据图表生成器（分析数据特征→推荐图表类型→生成图表）")
    p.add_argument("--file", required=True, help="Excel 文件路径")
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--action", default="auto", choices=["analyze", "recommend", "generate", "auto"],
                   help="图表生成动作")
    p.add_argument("--type", default="", help="图表类型（不指定则自动推荐）")
    p.add_argument("--output", default="", help="输出路径")

    # v4.7: 公式解释器（反向 NL2Formula）
    p = sub.add_parser("formula-explain", help="公式解释器（Excel公式→自然语言解释）")
    p.add_argument("--formula", help="要解释的公式（如 =SUM(A1:A10)）")
    p.add_argument("--file", help="Excel 文件路径（批量解释 Sheet 中所有公式）")
    p.add_argument("--sheet", default="Sheet1")
    p.add_argument("--cell", help="单元格地址（如 B2，需配合 --file）")

    args = parser.parse_args()

    if args.command == "create":
        sheets = [s.strip() for s in args.sheets.split(",") if s.strip()] if args.sheets else None
        data = json.loads(args.data) if args.data else None
        r = call_worker("create_excel", {
            "name": args.name, "sheets": sheets or ["Sheet1"],
            "filepath": args.filepath, "data": data or {}
        })
    elif args.command == "input":
        data = json.loads(args.data)
        r = call_worker("input_excel", {"filepath": args.file, "sheet": args.sheet, "data": data})
    elif args.command == "formula":
        r = call_worker("formula_excel", {
            "filepath": args.file, "sheet": args.sheet, "cell": args.cell, "formula": args.formula
        })
    elif args.command == "sort":
        sorts = json.loads(args.sorts)
        r = call_worker("sort_excel", {"filepath": args.file, "sheet": args.sheet, "sorts": sorts})
    elif args.command == "filter":
        conds = json.loads(args.conditions)
        r = call_worker("filter_excel", {
            "filepath": args.file, "sheet": args.sheet, "conditions": conds, "logic": args.logic
        })
    elif args.command == "chart":
        r = call_worker("chart_excel", {
            "filepath": args.file, "sheet": args.sheet,
            "type": args.type, "data": args.data, "title": args.title
        })
    elif args.command == "add-sheet":
        headers = json.loads(args.headers) if args.headers else None
        data = json.loads(args.data) if args.data else None
        r = call_worker("add_sheet_excel", {
            "filepath": args.file, "sheet": args.sheet, "headers": headers, "data": data
        })
    elif args.command == "stats":
        r = call_worker("stats_excel", {
            "filepath": args.file, "sheet": args.sheet,
            "column": args.column, "type": args.type
        })
    elif args.command == "info":
        r = call_worker("info_excel", {"filepath": args.file})
    elif args.command == "engine-info":
        r = call_worker("engine_info", {})
    elif args.command == "check-update":
        r = call_worker("check_update", {})
    elif args.command == "nl-analyze":
        query_str = args.query
        if args.file:
            query_str = args.query.replace("{file}", args.file)
        r = call_worker("nl_analyze", {
            "file": args.file, "query": args.query, "sheet": args.sheet
        })
    elif args.command == "invoice":
        r = call_worker("invoice_ocr", {"input": args.input, "output": args.output})
    elif args.command == "excel-analyze":
        r = call_worker("excel_analyze", {
            "file": args.file,
            "task": args.task,
            "sheet": args.sheet,
            "column": args.column or "",
            "method": args.method,
            "steps": args.steps,
            "query": args.query or "",
            "use_llm": args.use_llm,
            "row_field": args.row_field or "",
            "value_field": args.value_field or "",
            "col_field": args.col_field or "",
            "agg_func": args.agg_func,
        })
    elif args.command == "excel-smart":
        # v4.6: 统一入口，--action 路由到对应功能
        r = call_worker("excel_analyze", {
            "file": args.file,
            "task": args.action,
            "sheet": args.sheet,
            "column": args.column or "",
            "method": args.method,
            "steps": args.steps,
            "query": args.query or "",
            "use_llm": args.use_llm,
            "row_field": args.row_field or "",
            "value_field": args.value_field or "",
            "col_field": args.col_field or "",
            "agg_func": args.agg_func,
        })
    elif args.command == "chart-gen":
        # v4.6: 数据图表生成器
        from chart_recommender import ChartRecommender, DataAnalyzer
        if args.action == "analyze":
            a = DataAnalyzer(args.file, args.sheet)
            if a.load():
                r = {"ok": True, **a.get_profile()}
                a.close()
            else:
                r = {"ok": False, "error": "加载失败"}
        elif args.action == "recommend":
            a = DataAnalyzer(args.file, args.sheet)
            if a.load():
                profile = a.get_profile()
                cr = ChartRecommender()
                recs = cr.recommend(profile)
                r = {"ok": True, "recommendations": recs}
                a.close()
            else:
                r = {"ok": False, "error": "加载失败"}
        else:
            # generate / auto
            cr = ChartRecommender()
            r = cr.auto_generate(args.file, args.sheet, args.output, args.type)
            r = {"ok": r.get("success", False), **r}
    elif args.command == "formula-explain":
        # v4.7: 公式解释器（反向 NL2Formula，纯本地实现）
        from formula_explainer import FormulaExplainer
        explainer = FormulaExplainer()
        if args.formula:
            # 解释单个公式
            r = {"ok": True, "formula": args.formula, "explanation": explainer.explain(args.formula)}
        elif args.file and args.cell:
            # 解释指定单元格
            result = explainer.explain_cell(args.file, args.sheet, args.cell)
            r = {"ok": "error" not in result, **result}
        elif args.file:
            # 批量解释 Sheet 中所有公式
            results = explainer.explain_file(args.file, args.sheet)
            r = {"ok": True, "count": len(results), "formulas": results}
        else:
            r = {"ok": False, "error": "请指定 --formula 或 --file（可配合 --cell）"}
    else:
        r = {"ok": False, "error": "未知命令"}

    print(json.dumps(r, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
