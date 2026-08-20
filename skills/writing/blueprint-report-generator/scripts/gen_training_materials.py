# -*- coding: utf-8 -*-
"""
最佳实践流程培训材料生成器（P0-3，方法论 2.2 ☆）

- 从标准工具目录（E:\\eMES 3.0\\标准工具）扫描六列操作流程图
- 从操作手册素材库索引（<项目>/蓝图分析/操作手册素材库/索引.json）关联关键界面截图
- 生成 <客户>_最佳实践流程图.html（按模块分组，六列表格 + 截图引用）

用法:
  python gen_training_materials.py --client "客户名" \
    --tool-dir "E:/eMES 3.0/标准工具" \
    --library-index "<项目>/蓝图分析/操作手册素材库/索引.json" \
    --out "<项目>/最佳实践流程培训/"
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

# 标准六列流程库（与 references/best_practice_training.md 一致）
PROCESS_LIB = [
    {"name": "生产派工", "how": "任务聪明派-前端：工单下发后按设备/人员派工",
     "when": "工单下达后、开工前", "who": "班长/车间主任", "where": "平板/PC 派工台", "gain": "任务到人、进度可视",
     "module": "聪明任务派-前端", "img_hint": "派工"},
    {"name": "生产报工", "how": "设备报工台/手机端：完工扫码报数",
     "when": "每工序完工时", "who": "操作工", "where": "工位平板/手机", "gain": "产量实时、工时准确",
     "module": "工厂数字化-前端", "img_hint": "报工"},
    {"name": "首自巡检", "how": "质检一手抓-前端：首件检验 + 过程巡检",
     "when": "开工首件/每班", "who": "质检员", "where": "检验工位", "gain": "质量闭环、不良前移",
     "module": "质检一手抓-前端", "img_hint": "检验"},
    {"name": "设备点检保养", "how": "设备健康管：班前点检、周期保养",
     "when": "班前/按周期", "who": "操作工/保养员", "where": "设备旁/点检台", "gain": "设备透明、异常早发现",
     "module": "设备健康管-前端", "img_hint": "设备"},
    {"name": "模具领用退回", "how": "模具寿命知-前端：扫码领用/退回",
     "when": "装模/卸模时", "who": "操作工/模具管理员", "where": "模具库", "gain": "寿命可查、防超寿命",
     "module": "模具寿命知-前端", "img_hint": "模具"},
    {"name": "工单上料", "how": "用料轻松管-前端：按 BOM 扫码上料",
     "when": "开工前", "who": "物料员", "where": "工位", "gain": "用料准确、防错料",
     "module": "用料轻松管-前端", "img_hint": "上料"},
    {"name": "委外发货回货", "how": "委外轻松管/手机端：发货/回货扫码",
     "when": "委外节点", "who": "委外管理员", "where": "仓库/手机", "gain": "委外透明、账实一致",
     "module": "委外轻松管-后端", "img_hint": "委外"},
]


def load_library_index(index_path):
    """读取操作手册素材库索引.json → {模块名: [截图路径...]}"""
    if not index_path or not os.path.exists(index_path):
        return {}
    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)
    # 兼容两种结构：{模块: [路径]} 或 {模块: [{path: ...}]}
    out = {}
    for k, v in (data.items() if isinstance(data, dict) else []):
        paths = []
        for item in v if isinstance(v, list) else [v]:
            if isinstance(item, str):
                paths.append(item)
            elif isinstance(item, dict):
                paths.append(item.get("path") or item.get("file") or "")
        out[k] = [p for p in paths if p]
    return out


def scan_tool_dir(tool_dir):
    """扫描标准工具目录：找六列流程图文件（xlsx/docx/html），返回文件名列表"""
    if not tool_dir or not os.path.exists(tool_dir):
        return []
    pats = ["*.xlsx", "*.docx", "*.html", "*.md"]
    found = []
    for p in pats:
        found += glob.glob(str(Path(tool_dir) / "**" / p), recursive=True)
    return sorted(found)


def pick_image(lib_index, module, hint):
    """在模块下选 1 张关键界面图（优先含 hint 文件名，否则取第一张）"""
    paths = lib_index.get(module, [])
    if not paths:
        return ""
    for p in paths:
        if hint and hint in Path(p).name:
            return p
    return paths[0]


def to_html(client, lib_index, tool_files):
    rows_html = ""
    for p in PROCESS_LIB:
        img = pick_image(lib_index, p["module"], p["img_hint"])
        img_html = f"<img src='{img}' style='max-width:220px;border:1px solid #ddd;border-radius:6px'>" if img else "<span style='color:#999'>（无截图）</span>"
        rows_html += (
            "<tr>"
            f"<td><b>{p['name']}</b></td><td>{p['how']}</td><td>{p['when']}</td>"
            f"<td>{p['who']}</td><td>{p['where']}</td><td>{p['gain']}</td><td>{img_html}</td>"
            "</tr>"
        )
    tool_html = "".join(
        f"<li>{os.path.relpath(f, tool_dir) if tool_dir else f}</li>" for f in tool_files[:30]
    ) or "<li>未找到（确认 --tool-dir 指向 E:/eMES 3.0/标准工具）</li>"
    return (
        f"<html><head><meta charset='utf-8'><title>{client} 最佳实践流程培训</title></head><body>"
        f"<h1>{client} · 最佳实践流程培训材料</h1>"
        f"<p>方法论 2.2 ☆最佳实践流程培训 配套：六列流程 + 关键界面截图 + 标准工具目录清单</p>"
        f"<h2>一、最佳实践流程（WHAT/HOW/WHEN/WHO/WHERE/Gain）</h2>"
        f"<table border='1' cellspacing='0' cellpadding='6' style='border-collapse:collapse;width:100%;font-size:13px'>"
        f"<tr style='background:#0B3D91;color:#fff'><th>WHAT</th><th>HOW</th><th>WHEN</th><th>WHO</th><th>WHERE</th><th>Gain</th><th>界面参考</th></tr>"
        f"{rows_html}</table>"
        f"<h2>二、标准工具目录（六列流程图源文件）</h2><ul>{tool_html}</ul>"
        f"<p style='color:#888;font-size:12px'>生成：智能交付助手-蓝图助手 · gen_training_materials.py</p>"
        f"</body></html>"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--tool-dir", default="E:/eMES 3.0/标准工具")
    ap.add_argument("--library-index", default="")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    lib_index = load_library_index(args.library_index)
    tool_files = scan_tool_dir(args.tool_dir)
    html = to_html(args.client, lib_index, tool_files)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.client}_最佳实践流程图.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成: {out_path}")
    print(f"  流程条目: {len(PROCESS_LIB)} · 截图匹配: {sum(1 for p in PROCESS_LIB if pick_image(lib_index, p['module'], p['img_hint']))} · 工具文件: {len(tool_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
