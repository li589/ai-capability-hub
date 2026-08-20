# -*- coding: utf-8 -*-
"""
智能映射助手：根据客户 Excel 表头自动生成"表头 → 接口字段"候选映射。
- 优先用 term_dict.json 术语词典（客户常见叫法，如"品号"→MA_ID）
- 未命中时给出字段清单，由 AI 语义判断
用法:
  python auto_map.py <api_name> <excel_path> [--sheet SHEET]
输出:
  matched:  已自动匹配的表头映射（AI 确认后使用）
  unmatched: 未匹配的表头（AI 需语义判断）
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parse_excel import read_excel
from build_payload import load_spec

BASE = Path(__file__).resolve().parent.parent
TERM_DICT = BASE / "term_dict.json"


def normalize(s):
    return "".join(s.split()).lower().replace("-", "").replace("_", "")


def build_field_index(spec):
    """接口字段索引: 字段名/规范名/中文desc → api_field"""
    idx = {}
    field_lists = []
    if "nested" in spec:
        field_lists = list(spec["nested"].get("head", [])) + list(spec["nested"].get("body", []))
    else:
        field_lists = spec.get("fields", [])
    for f in field_lists:
        name = f["api_field"]
        idx.setdefault(normalize(name), []).append(name)
        desc = f.get("desc", "")
        if desc and "；" in desc:
            desc = desc.split("；")[0]
        if desc:
            idx.setdefault(normalize(desc), []).append(name)
    return idx


def main():
    if len(sys.argv) < 3:
        print("用法: python auto_map.py <api_name> <excel_path> [--sheet SHEET]")
        sys.exit(1)
    api, excel = sys.argv[1], sys.argv[2]
    sheet = sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else None

    spec = load_spec(api)
    data = read_excel(excel, sheet_name=sheet)
    headers = data["headers"]

    term_dict = json.load(open(TERM_DICT, encoding="utf-8"))
    field_idx = build_field_index(spec)
    api_field_set = set()
    for lst in ([spec.get("fields", [])] if "nested" not in spec else
                [spec["nested"].get("head", []), spec["nested"].get("body", [])]):
        for f in lst:
            api_field_set.add(f["api_field"])

    matched, unmatched = {}, []
    for h in headers:
        if not h:
            continue
        norm = normalize(h)
        # 1) 术语词典精确
        if h in term_dict and term_dict[h]["api_field"] in api_field_set:
            matched[h] = term_dict[h]["api_field"]
            continue
        # 2) 术语词典规范名
        hit = None
        for alias, info in term_dict.items():
            if normalize(alias) == norm and info["api_field"] in api_field_set:
                hit = info["api_field"]
                break
        if hit:
            matched[h] = hit
            continue
        # 3) 接口字段名直接匹配
        if norm in field_idx:
            cands = [c for c in field_idx[norm] if c in api_field_set]
            if cands:
                matched[h] = cands[0]
                continue
        # 4) 子串匹配（表头包含字段中文名，或字段名包含表头）
        sub_hit = None
        for alias, info in term_dict.items():
            if info["api_field"] not in api_field_set:
                continue
            if norm in normalize(alias) or normalize(alias) in norm:
                sub_hit = info["api_field"]
                break
        if sub_hit:
            matched[h] = sub_hit
            continue
        unmatched.append(h)

    print("=" * 60)
    print(f"接口 {api} ｜ Sheet: {data['sheet']} ｜ 表头 {len(headers)} 个")
    print("=" * 60)
    if matched:
        print("\n【已自动匹配】（AI 确认后可直接用）:")
        for h, f in matched.items():
            print(f"  {h:<16} -> {f}")
    if unmatched:
        print("\n【未匹配，需 AI 语义判断】:")
        for h in unmatched:
            print(f"  {h}")
    print("\n候选映射 JSON:")
    print(json.dumps(matched, ensure_ascii=False, indent=2))
    print("=" * 60)
    print("确认/修正后执行: python deliver.py run <api> <excel> --map '{...}'")


if __name__ == "__main__":
    main()
