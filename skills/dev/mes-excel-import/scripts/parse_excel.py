# -*- coding: utf-8 -*-
"""
Excel 解析模块：读取客户 Excel（支持大数据量，read_only 模式）
返回: {"sheet": sheet名, "headers": [列名...], "rows": [ {列名: 值}, ... ], "total": N}
"""
import os
import sys
import json
from openpyxl import load_workbook

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False


def _cell_to_str(v):
    """单元格值统一转字符串（去掉 .0 尾巴）"""
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()


def read_excel(path, sheet_name=None, header_row=0, max_rows=None):
    """
    读取 Excel。
    path: 文件路径（.xlsx 用 openpyxl，.xls 需 pandas+xlrd）
    sheet_name: 指定 sheet，None 取第一个非空 sheet
    header_row: 表头所在行（0 起）
    max_rows: 最多读取的数据行数（None 全部，大数据量分页读时用）
    返回: dict {sheet, headers, rows, total, truncated}
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext == ".xlsx":
        wb = load_workbook(path, read_only=True, data_only=True)
        if sheet_name:
            if sheet_name not in wb.sheetnames:
                wb.close()
                raise ValueError(f"Sheet '{sheet_name}' 不存在，可选: {wb.sheetnames}")
            ws = wb[sheet_name]
        else:
            # 取第一个有数据的 sheet
            ws = None
            for name in wb.sheetnames:
                cand = wb[name]
                if cand.max_row > 0:
                    ws = cand
                    break
            if ws is None:
                wb.close()
                raise ValueError("Excel 中没有可用的 sheet")
            sheet_name = ws.title

        rows_iter = ws.iter_rows(values_only=True)
        headers = None
        rows = []
        idx = 0
        for row in rows_iter:
            if idx < header_row:
                idx += 1
                continue
            if headers is None:
                headers = [_cell_to_str(v) for v in row]
                idx += 1
                continue
            # 数据行
            d = {}
            for h, v in zip(headers, row):
                d[h] = v
            # 跳过全空行
            if all((v is None or str(v).strip() == "") for v in d.values()):
                idx += 1
                continue
            rows.append(d)
            idx += 1
            if max_rows and len(rows) >= max_rows:
                break
        wb.close()

        total = len(rows)
        return {
            "sheet": sheet_name,
            "headers": headers or [],
            "rows": rows,
            "total": total,
            "truncated": bool(max_rows and total >= max_rows),
        }

    elif ext == ".xls":
        if not _HAS_PANDAS:
            raise RuntimeError("读取 .xls 需要 pandas+xlrd，请安装: pip install pandas xlrd")
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row, dtype=object)
        headers = [str(c).strip() if c is not None else "" for c in df.columns]
        rows = []
        for _, r in df.iterrows():
            d = {h: ("" if pd.isna(v) else v) for h, v in zip(headers, r.values)}
            if all(str(v).strip() == "" for v in d.values()):
                continue
            rows.append(d)
            if max_rows and len(rows) >= max_rows:
                break
        return {
            "sheet": sheet_name or "Sheet1",
            "headers": headers,
            "rows": rows,
            "total": len(rows),
            "truncated": bool(max_rows and len(rows) >= max_rows),
        }

    else:
        raise ValueError(f"不支持的文件格式: {ext}（支持 .xlsx / .xls）")


def preview(path, sheet_name=None, n=5):
    """预览前 n 行，用于 AI 智能映射时理解表头结构"""
    data = read_excel(path, sheet_name=sheet_name, max_rows=n)
    return data


if __name__ == "__main__":
    # 命令行预览: python parse_excel.py <file> [sheet] [行数]
    if len(sys.argv) < 2:
        print("用法: python parse_excel.py <excel路径> [sheet名] [预览行数]")
        sys.exit(1)
    p = sys.argv[1]
    s = sys.argv[2] if len(sys.argv) > 2 else None
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    data = preview(p, s, n)
    print(f"Sheet: {data['sheet']}  共 {data['total']} 行")
    print("表头:", json.dumps(data["headers"], ensure_ascii=False, indent=2))
    print("--- 预览数据 ---")
    for i, r in enumerate(data["rows"][:n]):
        print(f"行{i+1}:", json.dumps(r, ensure_ascii=False, default=str))
