#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compress_data.py - 把 data/ 下的大 JSON 文件压缩到列式压缩格式 {_f,c,m}
确保 fund-advisor 整体包 < 10MB

用法: python scripts/compress_data.py
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def _read_rows(data, keys):
    """v9.0: 兼容读取数据行 — 裸 list / {key:[...]} / 列式格式（新/旧变体）。"""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for k in keys:
        v = data.get(k)
        if isinstance(v, list):
            return v
    try:
        from scripts.fund_advisor_paths import is_columnar, _decode_columnar
        if is_columnar(data):
            return _decode_columnar(data).get("items", []) or []
    except Exception:
        pass
    return []


def compress_list(data: list, keep_keys: list = None) -> dict:
    """把 list[dict] 压缩为 {_f, c, m} 列式格式"""
    if not data:
        return {"_f": [], "c": [], "m": {"count": 0}}
    if keep_keys is None:
        all_keys = sorted(set(k for item in data for k in item.keys()))
    else:
        all_keys = keep_keys
    cols = {k: [] for k in all_keys}
    for item in data:
        for k in all_keys:
            cols[k].append(item.get(k))
    return {"_f": all_keys, "c": [cols[k] for k in all_keys], "m": {"count": len(data)}}


def compress_dict_with_lists(d: dict, list_keys: list) -> dict:
    """压缩 dict 中指定的 list 字段，保留 meta"""
    out = {"m": {}}
    for k, v in d.items():
        if k in list_keys and isinstance(v, list):
            out.update(compress_list(v))
            out["m"][f"{k}_count"] = len(v)
        else:
            out["m"][k] = v
    return out


def main():
    # 1. holdings_database.json: 14M → 压缩核心字段
    src = DATA / "holdings_database.json"
    if src.exists():
        data = json.loads(src.read_text(encoding="utf-8"))
        # 压缩 holdings（v9.0: 兼容 {"holdings":[...]} / v7.2 {"h":[...]} / 列式）
        holdings = _read_rows(data, ("holdings", "h", "items"))
        keep = ["fund_code", "fund_name", "manager_name", "company_name",
                "stock_code", "stock_name", "weight", "report_date"]
        out = compress_list(holdings, keep)
        out["m"]["updated"] = "2026-07-21"
        out["m"]["source"] = "天天基金 Q2持仓"
        src.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"holdings_database.json: {len(holdings)} 条 → {src.stat().st_size // 1024}KB")

    # 2. fund_managers_distilled.json: 8.8M → 核心字段压缩
    src = DATA / "fund_managers_distilled.json"
    if src.exists():
        data = json.loads(src.read_text(encoding="utf-8"))
        managers = _read_rows(data, ("managers", "items"))
        keep = ["manager_id", "name", "company_name", "tenure_days",
                "total_scale", "best_return", "current_fund_code", "current_fund_name"]
        out = compress_list(managers, keep)
        out["m"]["source"] = "天天基金 Q2"
        src.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"fund_managers_distilled.json: {len(managers)} 位 → {src.stat().st_size // 1024}KB")

    # 3. external_data.json: 6.2M → 精简字段
    src = DATA / "external_data.json"
    if src.exists():
        data = json.loads(src.read_text(encoding="utf-8"))
        # ratings
        ratings = data.get("ratings", [])
        rk = ["fund_code", "fund_name", "star_5_count", "shanghai_star", "cms_star", "morning_star", "fee"]
        # analysis
        analysis = data.get("analysis", [])
        ak = ["fund_code", "period", "risk_return_ratio", "anti_risk_ratio", "sharpe_ratio", "max_drawdown"]
        # profit_probability
        prob = data.get("profit_probability", [])
        pk = ["fund_code", "holding_period", "profit_probability", "avg_return"]
        out = {
            "ratings": compress_list(ratings, rk),
            "analysis": compress_list(analysis, ak),
            "profit_probability": compress_list(prob, pk),
            "m": {"source": "天天/晨星/好买", "updated": "2026-07-21"}
        }
        src.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"external_data.json: ratings={len(ratings)}, analysis={len(analysis)}, prob={len(prob)} → {src.stat().st_size // 1024}KB")

    # 4. 全市场基金经理名录: 2.2M → 1.5M
    src = DATA / "全市场基金经理名录_天天基金.json"
    if src.exists():
        data = json.loads(src.read_text(encoding="utf-8"))
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            keep = ["manager_id", "name", "company", "company_id", "fund_count",
                    "totalscale", "incepdate", "best_return"]
            data = compress_list(data, keep)
            src.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                           encoding="utf-8")
            print(f"全市场基金经理名录_天天基金.json: → {src.stat().st_size // 1024}KB")

    # 5. 删除原始 holdings.json 备份等冗余
    for fn in ["holdings_raw.json", "fund_managers.json", "fund_companies.json", "全市场基金名录_天天基金.json"]:
        p = DATA / fn
        if p.exists():
            p.unlink()
            print(f"已删除冗余: {fn}")

    # 总大小
    import os
    total = sum(p.stat().st_size for p in DATA.rglob("*") if p.is_file())
    print(f"\n📦 当前 data/ 总大小: {total // 1024 // 1024}MB ({total // 1024}KB)")


if __name__ == "__main__":
    main()
