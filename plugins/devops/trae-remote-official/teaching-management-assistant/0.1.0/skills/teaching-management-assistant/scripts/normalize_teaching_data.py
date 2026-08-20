#!/usr/bin/env python3
"""教学数据标准化脚本（确定性）。

读取已结构化的成绩/试卷文件，按模型提供的字段映射配置，输出：
  - 标准化数据（长表：一行一个 学生×科目/题目 记录）
  - 数据质量报告（JSON）
  - 处理记录（JSON）

不解析 Word/图片：这类材料由模型先提取为 CSV 结构化中间文件再传入。
不覆盖原始文件。

用法：
  python3 normalize_teaching_data.py --config config.json

config.json 结构见 build_arg_parser 文档与 README。
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("需要 pandas：pip3 install pandas openpyxl chardet", file=sys.stderr)
    sys.exit(2)

ABSENT_MARKERS = {"缺考", "缺", "缺席", "absent", "—", "-", "/", "\\", "未考", "弃考"}
EXEMPT_MARKERS = {"免考", "免修", "免", "exempt"}
CHEAT_MARKERS = {"作弊", "违纪", "cheating"}
MAKEUP_MARKERS = {"补考", "缓考", "make_up", "makeup"}
PRESERVED_FIELDS = (
    "student_id", "student_name", "class", "grade", "major", "gender",
    "assessment_id", "exam_type", "term", "item_type", "knowledge_point",
    "objective_id", "source",
)


def detect_encoding(path):
    try:
        import chardet
        with open(path, "rb") as f:
            raw = f.read(50000)
        enc = chardet.detect(raw)["encoding"] or "utf-8"
        return "utf-8" if enc.lower() in ("ascii", "iso-8859-1") else enc
    except Exception:
        return "utf-8"


def read_file(path, sheet=None):
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    if ext in (".csv", ".tsv", ".txt"):
        sep = "\t" if ext == ".tsv" else ","
        enc = detect_encoding(path)
        try:
            return pd.read_csv(path, encoding=enc, sep=sep)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="gbk", sep=sep)
    raise ValueError(f"不支持的文件类型：{ext}（Word/图片请先提取为 CSV）")


def classify_status(raw):
    """返回 (score 或 None, status)。"""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, "unknown"
    s = str(raw).strip()
    if s == "":
        return None, "unknown"
    low = s.lower()
    for markers, status in [
        (ABSENT_MARKERS, "absent"), (EXEMPT_MARKERS, "exempt"),
        (CHEAT_MARKERS, "cheating"), (MAKEUP_MARKERS, "make_up"),
    ]:
        if any(low == m.lower() or (len(m) > 1 and m.lower() in low)
               for m in markers):
            # 补考可能带分数，如 "补考58"
            num = _extract_number(s)
            return num, status
    num = _extract_number(s)
    if num is None:
        return None, "unknown"
    return num, "normal"


def _extract_number(s):
    import re
    m = re.search(r"-?\d+\.?\d*", str(s))
    return float(m.group()) if m else None


def normalize(config):
    quality = {"files": [], "issues": [], "summary": {}}
    log = {"steps": []}
    frames = []

    id_map = config["field_mappings"]           # {源列: 内部字段}
    value_cols = config.get("value_columns", config.get("subject_columns", []))
    long_mode = config.get("long_mode", False)  # 数据本身是长表
    record_type = config.get("record_type", "score")  # score / item_score
    default_full = config.get("full_scores", config.get("full_score"))

    for fspec in config["files"]:
        path = fspec["path"]
        df = read_file(path, fspec.get("sheet"))
        raw_rows = len(df)
        # 剔除疑似汇总行
        df, dropped = drop_summary_rows(df, id_map)
        df = df.rename(columns={k: v for k, v in id_map.items() if k in df.columns})
        if "source" not in df.columns:
            df["source"] = Path(path).stem
        before_dedup = len(df)
        if config.get("drop_exact_duplicates", True):
            df = df.drop_duplicates().copy()
        exact_duplicates = before_dedup - len(df)
        frames.append((df, fspec))
        quality["files"].append({
            "path": path, "raw_rows": raw_rows,
            "dropped_summary_rows": dropped,
            "dropped_exact_duplicates": exact_duplicates,
            "columns": list(df.columns),
        })
        log["steps"].append(
            f"读取 {path}：{raw_rows} 行，剔除疑似汇总行 {dropped}，"
            f"删除完全重复行 {exact_duplicates}")

    records = []
    for df, fspec in frames:
        ff = fspec.get("full_scores", fspec.get("full_score", default_full))
        if long_mode:
            for _, row in df.iterrows():
                score, status = classify_status(row.get("score"))
                dimension = row.get("item_id") if record_type == "item_score" else row.get("subject")
                records.append(_mk_record(
                    row, dimension, score, status,
                    _resolve_full_score(ff, dimension), record_type))
        else:
            cols = [c for c in value_cols if c in df.columns] or _guess_value_cols(df)
            for _, row in df.iterrows():
                for dimension in cols:
                    score, status = classify_status(row.get(dimension))
                    records.append(_mk_record(
                        row, dimension, score, status,
                        _resolve_full_score(ff, dimension), record_type))

    out = pd.DataFrame(records)
    # 质量统计
    quality["summary"] = build_quality_summary(out)
    quality["issues"] = build_issues(out)

    outdir = Path(config.get("output_dir", "output"))
    outdir.mkdir(parents=True, exist_ok=True)
    data_path = outdir / "normalized_data.xlsx"
    out.to_excel(data_path, index=False, engine="openpyxl")
    (outdir / "data_quality_report.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "processing_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"标准化完成：{len(out)} 条记录 -> {data_path}")
    print(f"有效(normal)：{quality['summary'].get('normal_records',0)} 条")
    print(f"质量报告：{outdir/'data_quality_report.json'}")
    return 0


def _mk_record(row, dimension, score, status, full_score, record_type):
    record = {field: _s(row.get(field)) for field in PRESERVED_FIELDS}
    record.update({
        "record_type": record_type,
        "subject": _s(dimension) if record_type == "score" else _s(row.get("subject")),
        "item_id": _s(dimension) if record_type == "item_score" else _s(row.get("item_id")),
        "score": score,
        "status": status,
        "full_score": full_score,
    })
    return record


def _resolve_full_score(spec, dimension):
    """支持统一满分或按科目/题号配置满分。"""
    if isinstance(spec, dict):
        value = spec.get(str(dimension), spec.get("default"))
    else:
        value = spec
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _s(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v).strip()


def drop_summary_rows(df, id_map):
    """剔除均分/汇总等噪声行。"""
    before = len(df)
    id_col = None
    for src, dst in id_map.items():
        if dst == "student_id" and src in df.columns:
            id_col = src
            break
    name_col = None
    for src, dst in id_map.items():
        if dst == "student_name" and src in df.columns:
            name_col = src
            break
    mask = pd.Series([True] * len(df))
    kw = ["平均", "均分", "合计", "总计", "小计", "最高", "最低", "汇总", "average", "mean", "total"]
    for col in [c for c in [id_col, name_col] if c]:
        col_str = df[col].astype(str)
        mask &= ~col_str.str.contains("|".join(kw), case=False, na=False)
    if id_col:  # 学号全空的行大概率是汇总
        mask &= df[id_col].notna()
    df2 = df[mask].copy()
    return df2, before - len(df2)


def _guess_value_cols(df):
    """宽表下猜测成绩/逐题列：数值型且非身份与上下文字段。"""
    id_fields = set(PRESERVED_FIELDS) | {"record_type", "full_score"}
    cols = []
    for c in df.columns:
        if c in id_fields:
            continue
        numeric_ratio = pd.to_numeric(df[c], errors="coerce").notna().mean()
        if numeric_ratio > 0.5:
            cols.append(c)
    return cols


def build_quality_summary(out):
    total = len(out)
    by_status = out["status"].value_counts().to_dict()
    return {
        "total_records": total,
        "normal_records": int(by_status.get("normal", 0)),
        "status_breakdown": {k: int(v) for k, v in by_status.items()},
        "students": int(out["student_id"].nunique()) if "student_id" in out else None,
        "subjects": sorted([s for s in out["subject"].dropna().unique()]) if "subject" in out else [],
        "classes": sorted([c for c in out["class"].dropna().unique()]) if "class" in out else [],
    }


def build_issues(out):
    issues = []
    # 缺失学号
    no_id = out["student_id"].isna().sum()
    if no_id:
        issues.append({"level": "warn", "type": "missing_id",
                       "detail": f"{no_id} 条记录缺学号，无法定位到个人"})
    # 语义重复只告警。完全相同的原始行已在标准化前删除；其余重复
    # 可能来自补考或多次考试，不能在缺少业务键时静默删除。
    dimension = "item_id" if out["item_id"].notna().any() else "subject"
    dup_keys = ["student_id", dimension, "assessment_id", "exam_type", "term"]
    dup = out[out["status"] == "normal"].duplicated(subset=dup_keys).sum()
    if dup:
        issues.append({"level": "warn", "type": "duplicate",
                       "detail": f"{dup} 条疑似重复记录"})
    # 超满分
    if out["full_score"].notna().any():
        over = out[(out["status"] == "normal") &
                   (out["score"] > out["full_score"])]
        if len(over):
            issues.append({"level": "warn", "type": "over_full_score",
                           "detail": f"{len(over)} 条得分超过满分"})
    # 负分
    neg = out[(out["status"] == "normal") & (out["score"] < 0)]
    if len(neg):
        issues.append({"level": "warn", "type": "negative",
                       "detail": f"{len(neg)} 条负分"})
    return issues


def build_arg_parser():
    p = argparse.ArgumentParser(description="教学数据标准化")
    p.add_argument("--config", required=True, help="配置 JSON 路径")
    return p


def main():
    args = build_arg_parser().parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    return normalize(config)


if __name__ == "__main__":
    sys.exit(main())
