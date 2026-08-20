# -*- coding: utf-8 -*-
"""
《模拟剧本》生成器（蓝图助手，方法论 3.5/3.6 模拟验证与客户应用培训用）

依据最佳实践流程（客户实际工艺路线/工序/设备/检验规则）生成客户版模拟剧本 xlsx，
结构完全沿用模板（4 个 Sheet）：
  1. 基础数据搭建      —— 系统搭建标准动作（保留模板，按客户模块微调）
  2. 生产报工模拟流程   —— 按客户工序动态生成（每工序 8 步标准操作）
  3. 质检流程          —— 首检/自巡检/末检/不良审核（保留模板）
  4. 设备流程          —— 设备维修/保养（保留模板）

用法:
  python gen_simulation_script.py --client "客户名" \
    --processes "PVC工序:高速混料造粒一体机,拉丝工序:拉丝机,制链工序:制链机" \
    --out "<项目>/3.5-1 模拟剧本V1.xlsx"

  --processes 格式："工序名:设备名,工序名:设备名"（设备名可省略，如 "配件组装"）
  若从调研报告/流程规划已有工序清单，可直接转换传入。

每工序 8 步标准操作（设备报工台选择→选择设备→点检→上下料→开始加工→过程检验→送检→结束加工）。
"""
import argparse
import os
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "模拟剧本模板V1.xlsx"

STD_STEPS = [
    ("设备报工台选择", "PAD端选择设备报工台", "PAD端", "操作工"),
    ("选择设备", "选择{dev}设备", "PAD端", "操作工"),
    ("设备点检", "选中设备，点击点检，维护点检内容", "PAD端", "操作工"),
    ("工单上下料", "扫码录入原材料信息", "PAD端", "操作工"),
    ("开始加工", "选择工单开始加工", "PAD端", "操作工"),
    ("过程检验", "点过程检验，选择首/巡/自检", "PAD端", "操作工"),
    ("送检", "点击送检，选择末检后提交", "PAD端", "操作工"),
    ("结束加工", "维护结束加工数量，记录耗料信息，结束加工打印标签", "PAD端", "操作工"),
]

# 组装类工序（PDA 手机端）模板：配件组装示例
STD_STEPS_ASSEMBLY = [
    ("生产报工台选择", "手机端选择生产报工", "PDA端", "领班"),
    ("开始加工", "选择工单开始加工", "PDA端", "领班"),
    ("过程检验", "点过程检验，选择首/巡/自/末检", "PDA端", "领班"),
    ("结束加工", "维护结束加工数量，结束加工打印标签", "PDA端", "领班"),
]


def parse_processes(s):
    """'工序名:设备名,工序名' → [(工序, 设备或'')]"""
    out = []
    for item in s.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            name, dev = item.split(":", 1)
            out.append((name.strip(), dev.strip()))
        else:
            out.append((item, ""))
    return out


def load_template(path):
    from openpyxl import load_workbook
    return load_workbook(path)


def read_sheet_rows(ws):
    """读取 sheet 所有行，返回 (headers, rows)"""
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(["" if v is None else str(v) for v in row])
    if not rows:
        return [], []
    return rows[0], rows[1:]


def build_report_flow(processes):
    """按客户工序生成『生产报工模拟流程』内容行"""
    out = []
    # 1 开批派工
    out.append(("", "", "1 开批派工", "", "", ""))
    out.append(("1.1", "工单数据维护", "维护生产工单一条，数量20000", "PC端", "", ""))
    out.append(("1.2", "工单下发", "下发工单一条", "PC端", "", ""))
    # 2 生产派工
    out.append(("", "", "2 生产派工", "", "", ""))
    out.append(("2.1", "生产派工", "选择派工的工艺，派工到相应的设备或人员", "PAD端", "", ""))
    # 3~N 各工序
    for i, (name, dev) in enumerate(processes, start=3):
        out.append(("", "", f"{i} {name}工序", "", "", ""))
        steps = STD_STEPS_ASSEMBLY if "组装" in name or "装配" in name or "包装" in name else STD_STEPS
        for j, (op, desc, term, who) in enumerate(steps, start=1):
            desc2 = desc.format(dev=dev) if dev else desc.replace("选择{dev}设备", "选择设备")
            out.append((f"{i}.{j}", op, desc2, term, who, ""))
    # 表单查询
    out.append(("", "", f"{len(processes)+3} 表单查询", "", "", ""))
    out.append(("", "生产相关数据查询", "", "PC端", "", ""))
    out.append(("", "质量相关数据查询", "", "PC端", "", ""))
    return out


def gen(client, processes, template_path, out_path):
    wb = load_template(template_path)
    # 重命名首个 sheet 为 基础数据搭建（模板已有，直接改表头信息即可）
    # Sheet1: 基础数据搭建 —— 原样保留（系统搭建标准动作）
    # Sheet2: 生产报工模拟流程 —— 按客户工序重建
    ws = wb["生产报工模拟流程"]
    new_rows = build_report_flow(processes)
    # 清空原内容（保留表头）
    ws.delete_rows(2, ws.max_row)
    for row in new_rows:
        ws.append(row)
    # 输出
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wb.save(out_path)
    print(f"已生成: {out_path}")
    print(f"  工序数: {len(processes)} · 生产报工步骤: {len(new_rows)-2} 行")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--processes", required=True, help='工序清单："工序名:设备名,工序名"')
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--out", required=True, help="输出 xlsx 路径")
    args = ap.parse_args()
    procs = parse_processes(args.processes)
    gen(args.client, procs, args.template, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
