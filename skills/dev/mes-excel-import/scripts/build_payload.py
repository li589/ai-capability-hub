# -*- coding: utf-8 -*-
"""
参数组装模块：按 api_spec 将 Excel 行 dict 转换为接口 JSON 参数。
支持：字段映射（精确/模糊/默认）、类型转换、枚举映射、必填校验、日期格式转换。
"""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "api_specs"


def load_spec(api_name):
    """加载接口字段定义。api_name 如 eq_data / workstation_data"""
    p = SPEC_DIR / f"{api_name}.json"
    if not p.exists():
        raise FileNotFoundError(f"接口定义不存在: {p}（请在 api_specs/ 下补充 {api_name}.json）")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ---------- 类型转换 ----------

def _apply_transform(v, transform):
    """转换函数，transform 为字符串表达式"""
    if v is None:
        return None
    t = (transform or "").strip()
    if not t:
        return v

    # 去空格
    if t == "strip":
        return str(v).strip() if not isinstance(v, (int, float)) else v
    # 转 int（兼容 '123.0'）
    if t == "int":
        s = str(v).strip()
        try:
            return int(float(s))
        except ValueError:
            return s
    # 转 float
    if t == "float":
        try:
            return float(str(v).strip())
        except ValueError:
            return str(v).strip()
    # 字符串
    if t == "string":
        if isinstance(v, (int, float)):
            if float(v) == int(v):
                return str(int(v))
            return str(v)
        return str(v).strip()
    # 日期: 任意输入 -> yyyy-MM-dd
    if t == "date":
        return _to_date(v, "%Y-%m-%d")
    if t == "date_compact":
        return _to_date(v, "%Y%m%d")
    if t == "datetime":
        return _to_date(v, "%Y-%m-%d %H:%M:%S")
    # 布尔
    if t == "bool":
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "y", "是", "true")
    # 空串转 None
    if t == "none_if_empty":
        if v is None:
            return None
        s = str(v).strip()
        return None if s in ("", "null", "None", "none", "-") else s
    return v


def _to_date(v, fmt):
    """把常见日期格式转成 fmt 输出"""
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        return None
    # 纯数字 yyyymmdd
    if re.fullmatch(r"\d{8}", s):
        return datetime.strptime(s, "%Y%m%d").strftime(fmt)
    # 带横线/斜杠/点
    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S",
                    "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m"):
        try:
            return datetime.strptime(s, pattern).strftime(fmt)
        except ValueError:
            continue
    # 可能是 Excel 序列号日期
    try:
        num = float(s)
        if 20000 < num < 60000:  # 日期序列号范围
            return (datetime(1899, 12, 30) + __import__("datetime").timedelta(days=num)).strftime(fmt)
    except ValueError:
        pass
    return s  # 无法解析则原样返回


# ---------- 主转换逻辑 ----------

def build_row_object(row, fields, col_map=None, errors=None, label_prefix=""):
    """
    按字段列表构建一个 JSON 对象（head/body/平铺行共用）。
    row: {excel列名: 值}
    fields: 字段定义列表（api_field/label/type/required/transform/mapping/source/default）
    col_map: 智能映射 {api_field: excel列名}，None 时按字段定义中的 source.col
    返回: obj dict（仅含成功转换的字段）
    """
    obj = {}
    for f in fields:
        # 系统自动生成的 ID 不传、不校验
        if f.get("auto_generate"):
            continue
        api_field = f["api_field"]
        label = label_prefix + f.get("label", api_field)
        ftype = f.get("type", "string")
        required = f.get("required", False)
        default = f.get("default")
        transform = f.get("transform")
        mapping = f.get("mapping") or {}
        source = f.get("source") or {}

        # 确定取值来源
        raw = None
        src_mode = source.get("mode", "exact")

        if src_mode == "default":
            raw = default
        elif src_mode == "mapping":
            # 列 + 枚举映射
            col = col_map.get(api_field) if col_map else source.get("col")
            raw = row.get(col) if col else None
        else:  # exact / fuzzy（fuzzy 时 col_map 由 AI 给出）
            col = None
            if col_map and api_field in col_map:
                col = col_map[api_field]
            elif source.get("col"):
                col = source["col"]
            if col:
                raw = row.get(col)
                # 兼容列名大小写/空格差异
                if raw is None:
                    for k in row:
                        if k and k.strip() == str(col).strip():
                            raw = row[k]
                            break

        # 类型转换
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            # 空值处理
            if required:
                if errors is not None:
                    errors.append(f"[{label}] 必填字段缺失")
                continue
            # 可选空字段：有默认值用默认值，否则跳过（不传）
            if default is not None:
                obj[api_field] = _apply_transform(default, transform)
            continue

        val = _apply_transform(raw, transform)

        # 枚举映射
        if mapping:
            key = str(val).strip()
            if key in mapping:
                val = mapping[key]
            elif str(val) in mapping:
                val = mapping[str(val)]

        # 按类型转换
        if ftype == "int":
            try:
                val = int(float(str(val)))
            except (ValueError, TypeError):
                if errors is not None:
                    errors.append(f"[{label}] 无法转整数: {raw}")
                continue
        elif ftype == "float":
            try:
                val = float(str(val))
            except (ValueError, TypeError):
                if errors is not None:
                    errors.append(f"[{label}] 无法转小数: {raw}")
                continue
        elif ftype == "string":
            if val is None:
                continue
            if isinstance(val, float) and val == int(val):
                val = str(int(val))
            else:
                val = str(val)
        elif ftype == "bool":
            if isinstance(val, bool):
                pass
            elif isinstance(val, (int, float)):
                val = bool(val)
            else:
                s = str(val).strip().lower()
                val = s in ("1", "true", "yes", "y", "是", "是")

        obj[api_field] = val

    return obj


def build_payload(row, spec, col_map=None):
    """
    将 Excel 行 dict 转为接口 content 元素（平铺对象或 {head, body} 嵌套对象）。
    row: {excel列名: 值}
    spec: api_specs 中的字段定义
    col_map: 智能映射 {api_field: excel列名}，None 时按字段定义中的 source.col
    返回: (payload, errors)  errors 为必填缺失/转换失败的错误列表
    """
    errors = []

    if "nested" in spec:
        # 嵌套结构：head + body
        head = build_row_object(row, spec["nested"].get("head", []), col_map, errors, label_prefix="主表.")
        body = build_row_object(row, spec["nested"].get("body", []), col_map, errors, label_prefix="明细.")
        payload = {}
        if head:
            payload["head"] = head
        if body:
            payload["body"] = [body]
        return payload, errors

    # 平铺结构
    payload = build_row_object(row, spec.get("fields", []), col_map, errors)
    return payload, errors


def validate_spec(spec):
    """检查 spec 合法性，返回错误列表（head/body 各自分组内查重，不跨组）"""
    errors = []
    if "nested" in spec:
        for sec in ("head", "body"):
            seen = set()
            for f in spec["nested"].get(sec, []):
                if "api_field" not in f:
                    errors.append(f"{sec} 字段缺少 api_field")
                    continue
                if f["api_field"] in seen:
                    errors.append(f"{sec} 重复字段: {f['api_field']}")
                seen.add(f["api_field"])
        return errors
    seen = set()
    for f in spec.get("fields", []):
        if "api_field" not in f:
            errors.append("字段缺少 api_field")
            continue
        if f["api_field"] in seen:
            errors.append(f"重复字段: {f['api_field']}")
        seen.add(f["api_field"])
    return errors


if __name__ == "__main__":
    import sys
    # 测试: python build_payload.py <spec名> '<json行>'
    spec_name = sys.argv[1]
    row = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    sp = load_spec(spec_name)
    errs = validate_spec(sp)
    if errs:
        print("SPEC 错误:", errs)
        sys.exit(1)
    payload, errors = build_payload(row, sp)
    print("payload:", json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    if errors:
        print("errors:", errors)
