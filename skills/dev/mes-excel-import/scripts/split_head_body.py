# -*- coding: utf-8 -*-
"""
合一表自动拆分模块（单头+单身合并一张表 → head 列表 + 按 head 分组的 body）

场景：客户/顾问为了维护方便，把单头字段和单身字段放在同一张表里。
典型形态（合一表）：
  - head 字段只在每组**首行**填写（后续行留空）——最常见
  - 或 head 字段**每行都复制**（标准模板导出）
  - body 字段（明细项）每行一条，跟在所属 head 后面

本模块自动完成：
  1. 列定位：根据 api_spec 的 nested.head/body 字段定义（或 col_map）确定
     Excel 中哪些列是 head 字段、哪些列是 body 字段
  2. 单头边界识别：head 字段"前向填充"后组合键变化 → 开启新单头
     （兼容"仅首行填"与"每行都填"两种模式，head 值相同自动合并）
  3. body 归属：head 为空的行自动归入最近单头

输出：[{"head": {...}, "body": [{...}, ...]}, ...]（与 nested 接口批量导入
       payload 结构一致，可直接用于 batch_runner）

用法：
  from split_head_body import split_head_body
  groups, info = split_head_body(rows, spec, col_map=None)

  rows: parse_excel.read_excel 的输出（[{excel列名: 值}, ...]）
  spec: build_payload.load_spec(接口名) 的输出（须含 nested.head/body）
  col_map: {api_field: excel列名}（可选；缺省按字段 label/source.col 匹配表头。
           客户表第 1 行为中文表头时建议由 AI 映射给出）
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_payload import build_row_object, load_spec  # noqa: E402


# ----------------------------------------------------------------------
# 列定位：Excel 表头 → spec 字段
# ----------------------------------------------------------------------

def _norm(s):
    """表头/字段名归一化（去空格、去*、小写）"""
    return str(s or "").strip().lstrip("*").strip().lower()


def resolve_columns(headers, spec, col_map=None):
    """
    确定 head 字段与 body 字段各自对应的 Excel 列名。
    headers: Excel 表头列表
    spec: api_spec（含 nested.head/body）
    col_map: {api_field: excel列名}（可选，优先）
    返回: (head_map, body_map)
      head_map: {api_field: excel列名}
      body_map: {api_field: excel列名}
    定位优先级：col_map[api_field] → 字段 source.col → 表头与 label/api_field 精确匹配
    """
    head_map, body_map = {}, {}
    if "nested" not in spec:
        return head_map, body_map
    header_norm = [_norm(h) for h in headers]

    def _locate(field):
        api_field = field["api_field"]
        # 1) col_map 显式指定
        if col_map and api_field in col_map:
            col = str(col_map[api_field]).strip()
            if col in headers:
                return col
            for h in headers:
                if _norm(h) == _norm(col):
                    return h
        # 2) spec 字段 source.col
        col = (field.get("source") or {}).get("col")
        if col and col in headers:
            return col
        if col:
            for h in headers:
                if _norm(h) == _norm(col):
                    return h
        # 3) 表头与 label / api_field 精确匹配
        label = _norm(field.get("label", ""))
        if label and label in header_norm:
            return headers[header_norm.index(label)]
        if _norm(api_field) in header_norm:
            return headers[header_norm.index(_norm(api_field))]
        return None

    for f in spec["nested"].get("head", []):
        col = _locate(f)
        if col:
            head_map[f["api_field"]] = col
    for f in spec["nested"].get("body", []):
        col = _locate(f)
        if col:
            body_map[f["api_field"]] = col
    return head_map, body_map


def _cell_empty(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


# ----------------------------------------------------------------------
# 核心：合一表拆分
# ----------------------------------------------------------------------

def split_head_body(rows, spec, col_map=None):
    """
    合一表自动拆分。
    rows: [{excel列名: 值}, ...]（parse_excel.read_excel 的 rows）
    spec: 含 nested.head/body 的接口定义
    col_map: {api_field: excel列名}（可选）
    返回: (groups, info)
      groups: [{"head": {...}, "body": [{...}, ...]}, ...]
      info: {"head_map": {...}, "body_map": {...}, "groups": N,
             "merged_rows": M, "warnings": [...]}
    """
    warnings = []

    if "nested" not in spec:
        warnings.append("接口为平铺结构（无 head/body），无需拆分")
        return [], {"head_map": {}, "body_map": {}, "groups": 0,
                    "merged_rows": 0, "warnings": warnings}

    head_defs = spec["nested"].get("head", [])
    body_defs = spec["nested"].get("body", [])

    if not rows:
        warnings.append("无数据行")
        return [], {"head_map": {}, "body_map": {}, "groups": 0,
                    "merged_rows": 0, "warnings": warnings}

    headers = list(rows[0].keys())
    head_map, body_map = resolve_columns(headers, spec, col_map)

    if not head_map:
        warnings.append("未能在表头中定位到任何单头(head)字段，无法识别单头边界（请提供 col_map 或检查表头）")
        return [], {"head_map": {}, "body_map": {}, "groups": 0,
                    "merged_rows": 0, "warnings": warnings}
    if not body_map:
        warnings.append("未能在表头中定位到任何单身(body)字段，请检查表头与接口定义")

    groups = []
    cur_key = None          # 当前组的 head 组合键
    cur_body_list = None    # 当前组的 body 列表
    prev_head_vals = {}     # head 字段"前向填充"值（{excel列名: 值}）

    for row in rows:
        # ---- head：前向填充 + 构建 ----
        filled = {}
        has_raw_head = False
        for api_field, col in head_map.items():
            v = row.get(col)
            if _cell_empty(v):
                if col in prev_head_vals:
                    filled[col] = prev_head_vals[col]
            else:
                filled[col] = v
                has_raw_head = True
        head_obj = build_row_object(filled, head_defs, col_map=head_map,
                                    label_prefix="主表.")
        # 更新前向填充缓存（用本行原始值，空则保留 prev）
        for api_field, col in head_map.items():
            v = row.get(col)
            if not _cell_empty(v):
                prev_head_vals[col] = v

        key = json.dumps(head_obj, ensure_ascii=False, sort_keys=True, default=str) if head_obj else ""

        # ---- 单头边界：head 组合键变化 → 新组 ----
        if key != cur_key:
            if not head_obj:
                # 表头开头的悬空行（无 head 值）或 head 构建失败
                if has_raw_head:
                    warnings.append("单头构建失败（必填字段缺失或类型转换错误），该行及后续 body 可能错位")
                else:
                    warnings.append("存在未归属的明细行（表格开头无单头字段值），已跳过")
                continue
            cur_key = key
            cur_body_list = []
            groups.append({"head": head_obj, "body": cur_body_list})

        # ---- body：归入当前组 ----
        body_obj = build_row_object(row, body_defs, col_map=body_map,
                                    label_prefix="明细.")
        if body_obj and cur_body_list is not None:
            cur_body_list.append(body_obj)

    # 清理无明细的组（head 有值但无任何 body 行）
    groups = [g for g in groups if g["body"]]
    merged_rows = sum(len(g["body"]) for g in groups)

    info = {
        "head_map": head_map,
        "body_map": body_map,
        "groups": len(groups),
        "merged_rows": merged_rows,
        "warnings": warnings,
    }
    return groups, info


# ----------------------------------------------------------------------
# CLI：python split_head_body.py <接口名> <rows.json> [col_map.json]
# ----------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python split_head_body.py <接口名> <rows.json> [col_map.json]")
        print("  rows.json: parse_excel.read_excel 输出的 rows 数组（[{excel列名: 值}, ...]）")
        print("  col_map.json(可选): {api_field: excel列名}")
        sys.exit(1)
    spec = load_spec(sys.argv[1])
    rows = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    cm = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) > 3 else None
    groups, info = split_head_body(rows, spec, cm)
    print("识别结果:", json.dumps(info, ensure_ascii=False, indent=2))
    print("--- 拆分预览 ---")
    for i, g in enumerate(groups, 1):
        print(f"组{i}: head={json.dumps(g['head'], ensure_ascii=False)} body={len(g['body'])}条")
        for b in g["body"][:2]:
            print(f"    {json.dumps(b, ensure_ascii=False)}")
