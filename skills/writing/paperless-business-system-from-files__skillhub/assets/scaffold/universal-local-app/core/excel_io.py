from __future__ import annotations
from pathlib import Path

def require_openpyxl():
    try: import openpyxl
    except ImportError as e: raise RuntimeError('缺少 openpyxl，请先安装 requirements.txt') from e
    return openpyxl

def load_workbook_readonly(path:Path,data_only=False):
    op=require_openpyxl(); return op.load_workbook(path,read_only=True,data_only=data_only)

def new_workbook():
    return require_openpyxl().Workbook()
