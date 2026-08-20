# -*- coding: utf-8 -*-
"""
标准模板快速导入：客户使用标准模板时，跳过字段匹配，直接按 template_maps.json 配置导入。
用法:
  python template_import.py <模板名>              # 按模板导入（默认逐条，防重复整批回滚）
  python template_import.py 检验方案
  python template_import.py 检验方案 --list       # 列出模板可用名
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requests
from parse_excel import read_excel

BASE = Path(__file__).resolve().parent.parent
TEMPLATES = BASE / "template_maps.json"


def value_convert(raw, value_map):
    """按模板 value_map 转换（如 无→0、是→true）"""
    if raw is None:
        return None
    s = str(raw).strip()
    if value_map and s in value_map:
        return value_map[s]
    return raw


def run(template_name, per_rule=True):
    tmpl = json.load(open(TEMPLATES, encoding="utf-8"))
    if template_name not in tmpl:
        print(f"模板不存在，可用: {list(tmpl.keys())}")
        return
    cfg = tmpl[template_name]
    spec = json.load(open(BASE / "api_specs" / f"{cfg['api']}.json", encoding="utf-8"))
    url = f"http://{json.load(open(BASE/'config.json',encoding='utf-8'))['server']['host']}:{json.load(open(BASE/'config.json',encoding='utf-8'))['server']['port']}{spec['endpoint']}"

    head_rows = read_excel(BASE / cfg["head_file"])["rows"]
    body_rows = read_excel(BASE / cfg["body_file"])["rows"]
    join = cfg["join_key"]
    body_by_key = {}
    for r in body_rows:
        body_by_key.setdefault(r.get(join), []).append(r)

    # 字段类型索引（用于转换）
    field_type = {}
    if "nested" in spec:
        for sec in ("head", "body"):
            for f in spec["nested"].get(sec, []):
                field_type[f["api_field"]] = f.get("type", "string")
    else:
        for f in spec.get("fields", []):
            field_type[f["api_field"]] = f.get("type", "string")

    def cast(field, v):
        t = field_type.get(field, "string")
        try:
            if t == "int":
                return int(float(str(v)))
            if t == "float":
                return float(str(v))
            if t == "bool":
                if isinstance(v, bool):
                    return v
                if isinstance(v, (int, float)):
                    return bool(v)
                return str(v).strip().lower() in ("1", "true", "yes", "y", "是", "是")
        except (ValueError, TypeError):
            pass
        return v

    def build(hr):
        head = {}
        for col, field in cfg["head_map"].items():
            v = value_convert(hr.get(col), cfg.get("value_map", {}).get(col))
            if v is not None:
                head[field] = cast(field, v)
        body = []
        for br in body_by_key.get(hr.get(join), []):
            item = {}
            for col, field in cfg["body_map"].items():
                v = value_convert(br.get(col), cfg.get("value_map", {}).get(col))
                if v is not None and str(v).strip() != "":
                    item[field] = cast(field, v)
            body.append(item)
        return {"head": head, "body": body}

    headers = {"Content-Type": "application/json"}
    inserted, existed, failed = [], [], []
    batch = [build(hr) for hr in head_rows]
    if per_rule:
        for hr, item in zip(head_rows, batch):
            r = requests.post(url, headers=headers, json={"OperationType": 0, "content": [item]}, timeout=30)
            txt = r.text
            rid = hr.get(join)
            if txt.startswith('{"res"'):
                inserted.append(rid)
            elif "addPrb" in txt or "已存在" in txt:
                existed.append(rid)
            else:
                failed.append((rid, txt[:150]))
            time.sleep(0.03)
    else:
        r = requests.post(url, headers=headers, json={"OperationType": 0, "content": batch}, timeout=60)
        print("批量响应:", r.text[:200])
        return

    total_detail = sum(len(b["body"]) for b in batch)
    print(f"模板[{template_name}] 导入完成")
    print(f"  ✅ 新插入: {len(inserted)} 条规则")
    print(f"  ⏭️  已存在跳过: {len(existed)} 条规则")
    print(f"  明细合计: {total_detail} 条")
    if failed:
        print(f"  ❌ 失败: {len(failed)} 条")
        for rid, msg in failed[:10]:
            print(f"     {rid}: {msg}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    name = sys.argv[1]
    if name == "--list" or len(sys.argv) > 2 and "--list" in sys.argv:
        tmpl = json.load(open(TEMPLATES, encoding="utf-8"))
        print("可用模板:", list(tmpl.keys()))
        for k, v in tmpl.items():
            print(f"  {k}: {v.get('desc','')}（{v['api']}）")
        sys.exit(0)
    run(name)
