# -*- coding: utf-8 -*-
"""
金融机构名单扩充引擎 v7.0.0 (institution_expander.py)

把 skill 的机构名单从 1330 家/27 类扩充至行业全量（约 2600+ 家），并新增
民营银行/外资法人银行/金融资产管理公司/村镇银行/保险中介等此前缺失的类型。

数据来源（三优先级，自动降级）：
  1. 实时接口：天天基金 fundcode_search.js（全量基金公司名册，无反爬）
  2. 精选数据：data/curated/*.json（行业协会公开名录/公开资料整理的离线数据，
     由维护脚本生成，与 registry 同步演进）
  3. 既有名单：data/*_list.json 原地合并去重

能力：
  - 名称规范化去重（剥离"股份有限公司/有限责任公司"等后缀、全半角统一）
  - registry（列式紧凑格式）与 *_list.json（分类型文件）双写保持一致
  - sentiment_targets.json 的 count 字段按扩充后实际数字同步
  - 生成 data/expansion_report.json（每类新增/总数/来源）

用法：
  python scripts/institution_expander.py                 # 全量扩充
  python scripts/institution_expander.py --report        # 只看统计
  python scripts/institution_expander.py --dry-run       # 不写文件
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from .http_utils import http_get, http_post
except ImportError:  # 脚本直跑
    from http_utils import http_get, http_post  # type: ignore

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
REGISTRY_FILE = DATA_DIR / "institution_registry.json"
CURATED_DIR = DATA_DIR / "curated"
REPORT_FILE = DATA_DIR / "expansion_report.json"

TODAY = datetime.now().strftime("%Y-%m-%d")

# ── 类别映射：curated 文件名 → (registry 类型名, list 文件名, 数据来源) ──
CATEGORY_MAP: Dict[str, Tuple[str, str, str]] = {
    # 既有类型扩充
    "securities":          ("证券公司", "securities_list.json", "中国证券业协会公开名录"),
    "fund_company":        ("基金管理公司", "fund_company_list.json", "天天基金/公开资料"),
    "futures":             ("期货公司", "futures_list.json", "中国期货业协会公开名录"),
    "insurance":           ("保险公司", "insurance_list.json", "中国保险行业协会公开名录"),
    "finance_company":     ("企业集团财务公司", "finance_company_list.json", "公开资料整理"),
    "financial_lease":     ("金融租赁公司", "financial_lease_list.json", "公开资料整理"),
    "consumer_finance":    ("消费金融公司", "consumer_finance_list.json", "公开资料整理"),
    "auto_finance":        ("汽车金融公司", "auto_finance_list.json", "公开资料整理"),
    "trust":               ("信托公司", "trust_list.json", "公开资料整理"),
    "money_broker":        ("货币经纪公司", "money_broker_list.json", "公开资料整理"),
    "financial_holding":   ("金融控股公司", "financial_holding_list.json", "公开资料整理"),
    "wealth_management":   ("银行理财子公司", "wealth_management_list.json", "公开资料整理"),
    "city_commercial":     ("城市商业银行", "city_commercial_bank_list.json", "公开资料整理"),
    "rural_commercial":    ("农村商业银行", "rural_commercial_bank_list.json", "公开资料整理"),
    "fund_subsidiary":     ("基金子公司", "fund_subsidiary_list.json", "公开资料整理"),
    # v7.0.0 新增类型
    "private_bank":        ("民营银行", "private_bank_list.json", "公开资料整理"),
    "foreign_bank":        ("外资法人银行", "foreign_bank_list.json", "公开资料整理"),
    "amc":                 ("金融资产管理公司", "amc_list.json", "公开资料整理"),
    "village_bank":        ("村镇银行", "village_bank_list.json", "公开资料整理(代表性样本)"),
    "insurance_broker":    ("保险经纪公司", "insurance_broker_list.json", "公开资料整理"),
    "insurance_assessor":  ("保险公估公司", "insurance_assessor_list.json", "公开资料整理"),
    "securities_consulting": ("证券投资咨询机构", "securities_consulting_list.json", "公开资料整理"),
}

# sentiment_targets 类键 → registry 类型名（count 同步用）
TARGET_TYPE_MAP: Dict[str, str] = {
    "fund_company": "基金管理公司",
    "securities": "证券公司",
    "commercial_bank": "城市商业银行",   # 商业银行口径=城商+农商+股份+国有+民营等
    "insurance": "保险公司",
    "trust_company": "信托公司",
    "private_fund": "私募基金管理公司",
    "foreign_institution": "外资金融机构",
    "futures": "期货公司",
    "wealth_management": "银行理财子公司",
    "leasing_consumer_finance": "金融租赁公司",
}

# v7.0.0: list 文件历史遗留的类型别名 → 标准类型名（吸收时归一化）
TYPE_ALIASES: Dict[str, str] = {
    "third_party": "第三方销售机构",
    "wealth_management": "银行理财子公司",
    "fund_subsidiary": "基金子公司",
    "大型国有商业银行": "国有大型商业银行",
    "保险公司(集团)": "保险公司",
    "保险公司(财产)": "保险公司",
    "保险公司(人身)": "保险公司",
    "再保险公司(境内)": "再保险公司",
}

_SUFFIX_RE = re.compile(
    r"(股份有限公司|有限责任公司|有限公司|责任公司|股份公司|集团）|集团\))"
)


def normalize_name(name: str) -> str:
    """名称规范化：去后缀/空白，全角括号→半角，用于跨源去重。"""
    n = (name or "").strip()
    n = n.replace("（", "(").replace("）", ")").replace(" ", "")
    for _ in range(2):
        n = _SUFFIX_RE.sub("", n)
    return n


def load_registry() -> Dict[str, List]:
    """读列式紧凑 registry → {"cols": [...], "rows": [[...]], "raw": doc}"""
    doc = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {"cols": doc["c"], "rows": doc["d"], "raw": doc}


def save_registry(cols: List[str], rows: List[List]) -> None:
    REGISTRY_FILE.write_text(
        json.dumps({"_f": "c", "c": cols, "d": rows}, ensure_ascii=False,
                   separators=(",", ":")),
        encoding="utf-8")


# ── 实时数据源 ─────────────────────────────────────────────────

def fetch_fund_companies_live() -> List[Dict[str, str]]:
    """天天基金基金公司目录页（fund.eastmoney.com/company/）。

    v7.0.0 修正：fundcode_search.js 已改版（第 5 列变为拼音缩写，不再含管理人），
    改为解析目录页 jsconp 链接文本（153 家，含外资/个人系新公司）。
    返回 [{"name": "易方达基金管理", ...}]；失败返回 []。
    """
    try:
        resp = http_get("https://fund.eastmoney.com/company/", timeout=20)
        if resp is None:
            return []
        html = resp.text
        names = re.findall(
            r'<a[^>]+href="[^"]*jsconp[^"]*"[^>]*>([^<]{2,30})</a>', html)
        if not names:
            names = re.findall(
                r'<a[^>]+>([^<]{2,30}基金管理[^<]{0,20})</a>', html)
        seen, out = set(), []
        for n in names:
            name = n.strip()
            key = normalize_name(name)
            if name and key and key not in seen:
                seen.add(key)
                out.append({"name": name})
        return out
    except Exception as e:
        print(f"[expander] 基金公司实时拉取失败（将用精选数据兜底）: {e}",
              file=sys.stderr)
        return []


def fetch_futures_companies_live() -> List[Dict[str, str]]:
    """期货业协会会员名录 API（v7.0.0 API 挖掘所得，直连复用）：
    POST http://www.cfachina.org/orc-report/api/basic/companyBaseInfo
    body: pageNo=1&pageSize=500&agencyName=&keyword=&flag=1

    返回全部期货公司（150+）；失败返回 []。
    """
    try:
        url = ("http://www.cfachina.org/orc-report/api/basic/companyBaseInfo")
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/133.0.0.0 Safari/537.36"),
            "Referer": "http://www.cfachina.org/",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        resp = http_post(url, data="pageNo=1&pageSize=500&agencyName=&keyword=&flag=1",
                         headers=headers, timeout=20, rate_limit_delay=0.3)
        if resp is None:
            return []
        data = resp.json()
        if data.get("errcode") != 0:
            return []
        rows = (data.get("data") or {}).get("dataList") or []
        out = []
        for r in rows:
            name = (r.get("name") or "").strip()
            if name:
                out.append({"name": name})
        return out
    except Exception as e:
        print(f"[expander] 期货公司实时拉取失败（将用精选数据兜底）: {e}",
              file=sys.stderr)
        return []


LIVE_SOURCES = {"fund_company": fetch_fund_companies_live,
                "futures": fetch_futures_companies_live}


# ── 核心：合并逻辑 ─────────────────────────────────────────────

def load_curated(category: str) -> List[Dict[str, str]]:
    path = CURATED_DIR / f"{category}.json"
    if not path.exists():
        return []
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
        out = []
        for i in items:
            if isinstance(i, str):          # 紧凑格式：纯名称数组
                out.append({"name": i})
            elif isinstance(i, dict) and i.get("name"):
                out.append(i)
        return out
    except Exception as e:
        print(f"[expander] curated/{category}.json 解析失败: {e}", file=sys.stderr)
        return []


def merge_category(reg_rows: List[List], cols: List[str],
                   category: str, items: List[Dict[str, str]],
                   type_name: str, data_source: str,
                   next_id: int, report: Dict[str, Dict],
                   dry_run: bool = False) -> Tuple[int, int]:
    """把 items 合并进 registry（按规范化名称+类型去重）。

    Returns:
        (新增条数, 该类型最终总数)
    """
    i_name, i_code, i_type = cols.index("name"), cols.index("code"), cols.index("type")
    i_ds, i_ut, i_web, i_us = (cols.index("data_source"), cols.index("update_time"),
                               cols.index("website"), cols.index("url_source"))
    existing = {}
    for row in reg_rows:
        if row[i_type] == type_name:
            existing[normalize_name(row[i_name])] = row
    added = 0
    for it in items:
        key = normalize_name(it["name"])
        if not key or key in existing:
            continue
        website = (it.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = "https://" + website
        row = [next_id, it["name"], it.get("code") or "", type_name,
               data_source, TODAY, website,
               "search_verified" if website else "curated"]
        reg_rows.append(row)
        existing[key] = row
        next_id += 1
        added += 1
    total = sum(1 for r in reg_rows if r[i_type] == type_name)
    report[category] = {"type": type_name, "added": added, "total": total,
                        "source": data_source}
    return added, total


def sync_list_files(type_name: str, list_file: str, reg_rows: List[List],
                    cols: List[str], data_source: str,
                    dry_run: bool = False) -> int:
    """按 registry 现状重写分类型 *_list.json（保持旧格式）。"""
    i_name, i_code, i_type = cols.index("name"), cols.index("code"), cols.index("type")
    insts = [{"name": r[i_name], "code": r[i_code] or "", "type": r[i_type]}
             for r in reg_rows if r[i_type] == type_name]
    insts.sort(key=lambda x: x["name"])
    if not dry_run and insts:
        doc = {"type": type_name, "type_name": type_name,
               "count": len(insts), "data_source": data_source,
               "update_time": TODAY, "institutions": insts}
        # 大名单（如私募 2 万家）用紧凑格式避免文件膨胀
        sep = None if len(insts) > 5000 else 1
        (DATA_DIR / list_file).write_text(
            json.dumps(doc, ensure_ascii=False, indent=sep), encoding="utf-8")
    return len(insts)


def sync_sentiment_targets(counts_by_type: Dict[str, int],
                           dry_run: bool = False) -> int:
    """按扩充后数字更新 sentiment_targets.json 各类 count。"""
    path = DATA_DIR / "sentiment_targets.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    updated = 0
    for key, type_name in TARGET_TYPE_MAP.items():
        if key in doc and type_name in counts_by_type:
            if doc[key].get("count") != counts_by_type[type_name]:
                doc[key]["count"] = counts_by_type[type_name]
                updated += 1
    if doc.get("_meta"):
        doc["_meta"]["updated_at"] = TODAY
        doc["_meta"]["version"] = "7.0.0"
    if not dry_run:
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return updated


def ingest_list_files(reg_rows: List[List], cols: List[str],
                      next_id: int, report: Dict[str, Dict],
                      dry_run: bool = False) -> Tuple[int, int]:
    """反向吸收：把 data/*_list.json（历史积累的更全类型名单，如私募 2 万家）
    中 registry 缺失的机构补入 registry，使 registry = list ∪ curated ∪ live。

    Returns:
        (新增条数, 涉及的 list 文件数)
    """
    i_name, i_code, i_type = (cols.index("name"), cols.index("code"),
                              cols.index("type"))
    i_ds, i_ut, i_web, i_us = (cols.index("data_source"), cols.index("update_time"),
                               cols.index("website"), cols.index("url_source"))
    # 1) 历史遗留别名类型行 → 标准类型（原地归一化）
    for row in reg_rows:
        t = row[i_type]
        if t in TYPE_ALIASES:
            row[i_type] = TYPE_ALIASES[t]
    # 2) 同类型内同名去重（归一化可能产生重复行）
    seen_rows: Dict[Tuple[str, str], List] = {}
    for row in reg_rows:
        key = (row[i_type], normalize_name(row[i_name]))
        if key in seen_rows:
            prev = seen_rows[key]
            if not prev[i_web] and row[i_web]:      # 保留有官网的
                prev[i_web], prev[i_us] = row[i_web], row[i_us]
            reg_rows.remove(row)                     # 保留先出现的
        else:
            seen_rows[key] = row
    existing: Dict[Tuple[str, str], List] = seen_rows
    added = 0
    touched = 0
    for f in sorted(DATA_DIR.glob("*_list.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        type_name = doc.get("type") or doc.get("type_name")
        data_source = doc.get("data_source", "公开信息/行业公开资料")
        insts = doc.get("institutions") or []
        if not type_name or not insts:
            continue
        type_name = TYPE_ALIASES.get(type_name, type_name)   # 别名归一化
        touched += 1
        for inst in insts:
            name = (inst.get("name") or "").strip()
            key = normalize_name(name)
            if not key or (type_name, key) in existing:
                continue
            row = [next_id, name, inst.get("code") or "", type_name,
                   data_source, TODAY, "", "list_file"]
            reg_rows.append(row)
            existing[(type_name, key)] = row
            next_id += 1
            added += 1
        report[f"ingest:{f.stem}"] = {"type": type_name, "added": added,
                                      "total": sum(
                                          1 for r in reg_rows if r[i_type] == type_name),
                                      "source": f"{f.name} 反向吸收"}
    return added, touched


def run(dry_run: bool = False, only: str = "") -> Dict[str, Dict]:
    reg = load_registry()
    cols, rows = reg["cols"], reg["rows"]
    next_id = max(r[cols.index("id")] for r in rows) + 1
    report: Dict[str, Dict] = {}

    # v7.0.0: 先反向吸收历史 list 文件（更全的独立名录 → registry）
    if not only:
        ingest_added, ingest_files = ingest_list_files(rows, cols, next_id,
                                                       report, dry_run)
        if ingest_added:
            print(f"  [ingest] 从 {ingest_files} 个 list 文件吸收 {ingest_added} 家")
            next_id += ingest_added

    for category, (type_name, list_file, data_source) in CATEGORY_MAP.items():
        if only and category != only:
            continue
        # 1) 实时源（可降级） 2) 精选数据 3) 都没有则跳过
        items = []
        if category in LIVE_SOURCES:
            items = LIVE_SOURCES[category]()
            if items:
                print(f"  [{category}] 实时源获取 {len(items)} 家")
        if not items:
            items = load_curated(category)
            if items:
                print(f"  [{category}] 精选数据 {len(items)} 家")
        if not items:
            continue
        added, total = merge_category(rows, cols, category, items, type_name,
                                      data_source, next_id, report, dry_run)
        next_id += added
        n_list = sync_list_files(type_name, list_file, rows, cols, data_source,
                                 dry_run)
        print(f"  [{category}] 新增 {added}，类型总数 {total}（list 文件 {n_list} 条）")

    counts_by_type: Dict[str, int] = {}
    i_type = cols.index("type")
    for r in rows:
        counts_by_type[r[i_type]] = counts_by_type.get(r[i_type], 0) + 1

    if not dry_run:
        save_registry(cols, rows)
        n_upd = sync_sentiment_targets(counts_by_type)
        print(f"sentiment_targets count 同步更新 {n_upd} 项")
        REPORT_FILE.write_text(json.dumps(
            {"_meta": {"version": "7.0.0", "date": TODAY,
                       "total_institutions": len(rows),
                       "total_types": len(counts_by_type)},
             "categories": report, "type_counts": counts_by_type},
            ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"registry 总数 {len(rows)} 家 / {len(counts_by_type)} 类")
    return report


def report_only() -> Dict[str, int]:
    reg = load_registry()
    cols, rows = reg["cols"], reg["rows"]
    i_type = cols.index("type")
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r[i_type]] = counts.get(r[i_type], 0) + 1
    for t in sorted(counts, key=counts.get, reverse=True):
        print(f"  {counts[t]:>5}  {t}")
    print(f"合计 {len(rows)} 家 / {len(counts)} 类")
    return counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="v7.0.0 机构名单扩充引擎")
    ap.add_argument("--dry-run", action="store_true", help="只统计不写文件")
    ap.add_argument("--report", action="store_true", help="只打印当前统计")
    ap.add_argument("--only", default="", help="只处理某类别（curated 文件名）")
    args = ap.parse_args()
    if args.report:
        report_only()
    else:
        run(dry_run=args.dry_run, only=args.only)
