# -*- coding: utf-8 -*-
"""
腾讯在线表格（问卷模板）批量读取（依赖 tencent-docs skill 的 tencentdocs.py）
- 用法: python fetch_survey_sheets.py <file_url> [输出.json]
- 需先执行 tencentdocs.py tdoc_init 确认鉴权 READY
"""
import subprocess
import json
import sys
import os

PY = sys.executable
TEN_DOCS_SKILL = r"{{HOME}}/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin/1.0.0/skills/tencent-docs"
TEN_DOCS_PY = os.path.join(TEN_DOCS_SKILL, "tencentdocs.py")


def tdoc_call(service, tool, args):
    cmd = [PY, TEN_DOCS_PY, "tdoc_call", service, tool, json.dumps(args)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"raw": r.stdout[:500]}


def fetch_all_sheets(url, max_rows=99):
    """读取全部子表，返回 {sheet_name: csv_data}"""
    info = tdoc_call("sheet-mcp", "get_sheet_info", {"file_url": url})
    sheets = info.get("result", {}).get("content", [{}])[0].get("text", "")
    sheets = json.loads(sheets)["sheets"]
    out = {}
    for s in sheets:
        sid, name = s["sheet_id"], s["sheet_name"]
        r = tdoc_call("sheet-mcp", "get_cell_data", {
            "file_url": url, "sheet_id": sid,
            "start_row": 0, "start_col": 0,
            "end_row": max_rows, "end_col": 12, "return_csv": True,
        })
        try:
            text = r.get("result", {}).get("content", [{}])[0].get("text", "")
            out[name] = json.loads(text).get("csv_data", "")
        except Exception as e:
            out[name] = f"ERROR: {e}"
    return out


def main():
    if len(sys.argv) < 2:
        print("用法: python fetch_survey_sheets.py <file_url> [输出.json]")
        return 1
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "问卷模板_raw.json"
    data = fetch_all_sheets(url)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    for name, csv in data.items():
        lines = [l for l in csv.split("\n") if l.strip() and l.strip(",").strip()]
        print(f"=== {name} ({len(csv)} chars) ===")
        for l in lines[:4]:
            print("  ", l[:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
