# -*- coding: utf-8 -*-
"""统一数据格式写入器（db_format.py，v9.0 新增）

单一格式事实源：monthly_updater / full_data_refresh / auto_updater 全量重建
统一产出新列式 {"_f":[列名],"c":[列数组],"m":meta}（is_columnar 双变体均可解码），
持仓用 {"holdings":[...],"m":{}}（normalize_holdings 兼容格式）。

零依赖（stdlib json）。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def to_columnar(rows: Sequence[Dict[str, Any]], columns: Sequence[str],
                meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """行列表 → 新列式格式 {"_f":[列名],"c":[列数组],"m":meta}。"""
    col_arrays: Dict[str, list] = {col: [] for col in columns}
    for r in rows or []:
        for col in columns:
            col_arrays[col].append(r.get(col))
    return {
        "_f": list(columns),
        "c": [col_arrays[col] for col in columns],
        "m": meta or {},
    }


def _write(path, data) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# 各文件默认列（与历史消费方字段对齐）
_MANAGER_COLS = ("code", "name", "company", "company_code", "investment_style",
                 "fund_type", "current_fund", "current_fund_code", "tenure_days",
                 "best_return", "manage_scale", "star_rating", "work_years",
                 "education", "bio")
_COMPANY_COLS = ("code", "name", "manager_count", "total_scale",
                 "products_count", "average_rating")
# v10.0: 产品目录列扩宽（fund_profile_collector 补充档案字段；旧消费方只读
# code/name/type/pinyin/update，_decode_columnar 对缺失列返回 None，向后兼容）
_PRODUCT_COLS = ("code", "name", "type", "pinyin", "update",
                 "risk_level", "scale", "inception_date",
                 "manager", "manager_code",
                 "management_fee", "custodian_fee", "subscription_fee",
                 "redemption_fee", "min_subscription",
                 "perf_1m", "perf_3m", "perf_6m", "perf_1y", "perf_3y", "perf_since",
                 "rating",
                 "investment_goal", "investment_scope",
                 "investment_strategy", "benchmark")


def write_managers_distilled(path, rows, meta=None, columns=None) -> None:
    """经理蒸馏库（新列式）。"""
    _write(path, to_columnar(rows, columns or _MANAGER_COLS,
                             meta or {"type": "managers", "updated": ""}))


def write_companies_distilled(path, rows, meta=None, columns=None) -> None:
    """公司蒸馏库（新列式）。"""
    _write(path, to_columnar(rows, columns or _COMPANY_COLS,
                             meta or {"type": "companies", "updated": ""}))


def write_products(path, rows, meta=None, columns=None) -> None:
    """产品目录（新列式）。"""
    _write(path, to_columnar(rows, columns or _PRODUCT_COLS,
                             meta or {"type": "products", "updated": ""}))


def write_holdings(path, rows, meta=None) -> None:
    """持仓库：股票级明细 + 紧凑外壳（normalize_holdings 兼容 {"holdings":[...]} 格式）。"""
    _write(path, {"holdings": list(rows or []), "m": meta or {"type": "holdings"}})


def write_plain(path, data, meta=None) -> None:
    """通用写入（原样数据 + meta）。"""
    _write(path, data)


def update_meta_append(meta_path, entry: Dict[str, Any], max_history: int = 100) -> Dict[str, Any]:
    """v9.0: 读旧 update_meta → append → 截断 → 保存（不覆写丢失 history）。"""
    p = Path(meta_path)
    old: Dict[str, Any] = {}
    if p.exists():
        try:
            old = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            old = {}
    history = old.get("history", []) or []
    history.append(entry)
    old["history"] = history[-max_history:]
    old["update_count"] = int(old.get("update_count", 0) or 0) + 1
    old["last_update"] = entry.get("time")
    _write(p, old)
    return old


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "m.json"
        write_managers_distilled(p, [{"code": "A001", "name": "张三", "company": "易方达"}],
                                 meta={"updated": "2026-08-10"})
        raw = json.loads(p.read_text(encoding="utf-8"))
        assert raw["_f"] == ["code", "name", "company", "company_code", "investment_style",
                             "fund_type", "current_fund", "current_fund_code", "tenure_days",
                             "best_return", "manage_scale", "star_rating", "work_years",
                             "education", "bio"]
        print("db_format OK:", raw["_f"][:3], "| 列数组长度:", [len(c) for c in raw["c"]][:3])
