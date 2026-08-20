#!/usr/bin/env python3
"""Quote supported products and validate a single-main-policy combination from the normalized product library."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

# 外部产品库目录：默认 ~/.workbuddy/copilot/企鹅保险/product-library
# 可用环境变量 PRODUCT_LIBRARY_DIR 覆盖（指向包含 catalog.json / rate_tables.json 的目录）
DEFAULT_LIBRARY_DIR = Path(os.path.expanduser("~/.workbuddy/copilot/企鹅保险/product-library"))


def library_dir() -> Path:
    env = os.environ.get("PRODUCT_LIBRARY_DIR")
    base = Path(env).expanduser() if env else DEFAULT_LIBRARY_DIR
    return base


def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
    base = library_dir()
    catalog_path = base / "catalog.json"
    rates_path = base / "rate_tables.json"
    if not catalog_path.exists() or not rates_path.exists():
        raise FileNotFoundError(
            f"未找到外部产品库：请在 {base} 下放置 catalog.json 与 rate_tables.json，"
            f"或通过环境变量 PRODUCT_LIBRARY_DIR 指定产品库目录。"
        )
    return (
        json.loads(catalog_path.read_text(encoding="utf-8")),
        json.loads(rates_path.read_text(encoding="utf-8")),
    )


def normalized_gender(value: str) -> str:
    return "男" if value in {"男", "male", "M"} else "女"


def payment(value: str) -> str:
    value = str(value).replace("交费", "交")
    if value in {"趸", "趸交", "一次性交清"}:
        return "趸交"
    if re.fullmatch(r"\d+年", value):
        return f"{value}交"
    return value


def age_in_band(age: int, band: str) -> bool:
    match = re.match(r"(\d+)\s*-\s*(\d+)", band)
    return bool(match and int(match.group(1)) <= age <= int(match.group(2)))


def choose_sheet(sheets: dict[str, Any], requested: str | None) -> tuple[str, dict[str, Any]]:
    if requested:
        for key, value in sheets.items():
            if requested == key or requested in key:
                return key, value
    if len(sheets) == 1:
        key = next(iter(sheets))
        return key, sheets[key]
    raise ValueError("需指定保障期限/领取年龄等费率表选项")


def quote_item(item: dict[str, Any], catalog: dict[str, Any], rates: dict[str, Any]) -> dict[str, Any]:
    code = str(item["product_code"]).strip()
    product = catalog["products"].get(code)
    if not product:
        raise ValueError(f"未找到产品代码 {code}")
    rate_table = rates.get(code)
    if not rate_table:
        raise ValueError(f"产品 {code} 缺少费率表")
    age = int(item["age"])
    gender = normalized_gender(str(item.get("gender", "")))
    model = rate_table["rate_type"]
    result: dict[str, Any] = {
        "product_code": code,
        "product_name": product["name"],
        "is_main": product["is_main"],
        "validity": product["validity"],
        "library_reference_version": product["library_reference_version"],
        "citation": {
            "product_document": product["sources"].get("product_document"),
            "rate_table": product["sources"].get("rate_table"),
            "document_id": product["terms"].get("document_id"),
        },
    }

    if model == "annual_fixed_by_age_band":
        social = "有社保" if bool(item.get("social_insurance", True)) else "无社保"
        bands = rate_table["sheets"]["标准"]["bands"]
        matched = next((band for band in bands if age_in_band(age, band["age_band"])), None)
        if not matched:
            raise ValueError(f"{code} 未覆盖年龄 {age}")
        result.update({"annual_premium": matched[social], "rate_basis": f"年龄段 {matched['age_band']}，{social}"})
        return result

    if model == "per_thousand_annual_premium_to_sum_assured":
        annual_premium = float(item.get("annual_premium", 0))
        if annual_premium <= 0:
            raise ValueError(f"{code} 的费率表按年交保费推基本保险金额，需输入 annual_premium")
        _sheet_name, sheet = choose_sheet(rate_table["sheets"], item.get("coverage_term"))
        pay = payment(str(item["payment_term"]))
        factor = sheet["rates"].get(str(age), {}).get(gender, {}).get(pay)
        if factor is None:
            raise ValueError(f"{code} 不支持年龄 {age}、{gender}、{pay}")
        result.update({"annual_premium": annual_premium, "sum_assured": round(annual_premium / 1000 * factor, 2), "rate_basis": f"每1000元年交保费对应基本保险金额 {factor}"})
        return result

    if code == "TLITLA001":
        pay = payment(str(item["payment_term"]))
        coverage_term = str(item["coverage_term"])
        sheet = rate_table["sheets"].get(gender)
        factor = sheet["rates"].get(str(age), {}).get(coverage_term, {}).get(pay) if sheet else None
        if factor is None:
            raise ValueError(f"{code} 不支持年龄 {age}、{gender}、{coverage_term}、{pay}")
        sum_assured = float(item["sum_assured"])
        result.update({"sum_assured": sum_assured, "annual_premium": round(factor * sum_assured / 1000, 2), "rate_basis": f"每1000元基本保险金额费率 {factor}"})
        return result

    if model == "per_thousand_sum_assured":
        sum_assured = float(item["sum_assured"])
        sheet_name, sheet = choose_sheet(rate_table["sheets"], item.get("coverage_term"))
        pay = payment(str(item.get("payment_term", sheet.get("payment_term", "年交"))))
        if code == "TCIA001":
            row = sheet["rates"].get(str(age), {})
            factor = row.get(gender)
        elif code == "TANSPM001":
            row = sheet["rates"].get(str(age), {})
            factor = row.get(pay)
        else:
            row = sheet["rates"].get(str(age), {})
            factor = row.get(gender, {}).get(pay)
        if factor is None:
            raise ValueError(f"{code} 不支持年龄 {age}、{gender}、{pay} 或所选保障期限")
        result.update({"sum_assured": sum_assured, "annual_premium": round(factor * sum_assured / 1000, 2), "rate_basis": f"{sheet_name}｜每1000元基本保险金额费率 {factor}"})
        return result

    raise ValueError(f"{code} 的费率模型待补充")


def validate_combination(quoted: list[dict[str, Any]], raw_items: list[dict[str, Any]], catalog: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    mains = [item for item in quoted if item["is_main"]]
    if len(mains) > 1:
        messages.append("不通过：一个方案只能配置一个主险")
    if not mains and quoted:
        messages.append("待核验：方案未包含主险，需确认是否符合产品搭配规则")
    if not mains:
        return messages
    main = mains[0]
    allowed = {r["rider_code"]: r["sum_assured_rule"] for r in catalog["combination_rules"].get(main["product_code"], [])}
    main_amount = float(main.get("sum_assured", 0))
    for item in quoted:
        if item["is_main"]:
            continue
        rule = allowed.get(item["product_code"])
        if rule is None:
            messages.append(f"不通过：{item['product_name']}未列入主险 {main['product_name']} 的搭配规则")
            continue
        rider_amount = float(item.get("sum_assured", 0))
        if rule in {"等于1：1", "等于1:1"} and main_amount and rider_amount != main_amount:
            messages.append(f"不通过：{item['product_name']}保额需与主险保持 1:1")
        elif rule.startswith("小于等于1：1") and main_amount and rider_amount > main_amount:
            messages.append(f"不通过：{item['product_name']}保额不得高于主险")
        elif rule.startswith("小于1:5") and main_amount and rider_amount >= main_amount / 5:
            messages.append(f"不通过：{item['product_name']}保额需符合资料库标注的“小于1:5”规则")
    return messages or ["通过：已完成单主险与已维护搭配规则校验"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Quote and validate a product combination")
    parser.add_argument("--input", required=True, help="Plan input JSON path")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()
    catalog, rates = load_data()
    request = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw_items = request.get("items", [])
    quoted = [quote_item(item, catalog, rates) for item in raw_items]
    result = {
        "library_validity": catalog["validity"],
        "library_reference_version": catalog["library_reference_version"],
        "items": quoted,
        "annual_premium_total": round(sum(float(item.get("annual_premium", 0)) for item in quoted), 2),
        "validation": validate_combination(quoted, raw_items, catalog),
    }
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
