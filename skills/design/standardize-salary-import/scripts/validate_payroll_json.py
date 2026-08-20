#!/usr/bin/env python3
"""Validate normalized salary-import rows and print a canonical JSON result.

The script reads one local JSON file, performs no network requests, writes no
files, and never modifies the source. Row-level validation problems are returned
in stdout while malformed input causes exit code 2.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised when the input document cannot be safely processed."""


COLUMNS = (
    "name",
    "expense_type",
    "id_type",
    "id_number",
    "mobile",
    "employment_date",
    "salary",
    "tax_exempt_income",
    "tax_exemption_item",
    "tibet_additional_deduction",
    "pension_insurance",
    "medical_insurance",
    "unemployment_insurance",
    "critical_illness_medical",
    "housing_fund",
    "other_after_tax_deduction",
    "official_transportation_expense",
    "communication_expense",
    "lawyer_case_expense",
    "enterprise_annuity",
    "remarks",
)

TEXT_FIELDS = {
    "name",
    "expense_type",
    "id_type",
    "id_number",
    "mobile",
    "tax_exemption_item",
    "remarks",
}
REQUIRED_FIELDS = ("name", "id_type", "id_number")
MONEY_FIELDS = {
    "salary",
    "tax_exempt_income",
    "tibet_additional_deduction",
    "pension_insurance",
    "medical_insurance",
    "unemployment_insurance",
    "critical_illness_medical",
    "housing_fund",
    "other_after_tax_deduction",
    "official_transportation_expense",
    "communication_expense",
    "lawyer_case_expense",
    "enterprise_annuity",
}
ID_TYPES = {
    "居民身份证",
    "中国护照",
    "港澳居民来往内地通行证",
    "中华人民共和国港澳居民居住证",
    "台湾居民来往大陆通行证",
    "中华人民共和国台湾居民居住证",
    "外国护照",
    "外国人永久居留身份证",
    "外国人工作许可证（A类）",
    "外国人工作许可证（B类）",
    "外国人工作许可证（C类）",
}
EXEMPTION_ITEMS = {
    "远洋船员工资薪金收入减按50%征收个人所得税",
    "离休费、离休生活补助费免征个人所得税",
    "退休费免征个人所得税",
    "退职费免征个人所得税",
    "安家费免征个人所得税",
    "院士津贴免征个人所得税",
    "政府特殊津贴免征个人所得税",
    "抚恤金免征个人所得税",
    "福利费免征个人所得税",
    "差旅费津贴、误餐补助不征个人所得税",
    "托儿补助费不征个人所得税",
    "独生子女补贴不征个人所得税",
    "亚洲开发银行支付给我国公民或国民的薪金和津贴免征个人所得税",
    "财税字〔1994〕020号第二条第(九)项、财税〔1980〕189号规定的符合条件的外籍专家、个人取得工资薪金所得免征个人所得税",
    "外籍个人生活费用免税",
    "外籍个人探亲费、语言训练费、子女教育费免税",
    "外籍个人出差补贴免税",
    "符合条件的外交人员免征个人所得税",
    "工伤保险免税",
    "生育津贴和生育医疗费免税",
    "企业职工从破产企业取得的一次性安置费收入免征个人所得税",
    "远洋运输船员取得的伙食费不征个人所得税",
    "高级专家延长离退休期间工薪免征个人所得税",
    "其他",
}

CENT = Decimal("0.01")
MAX_MONEY = Decimal("99999999.99")
FORMULA_PREFIXES = ("=", "+", "-", "@")
DATE_RE = re.compile(
    r"^\s*(\d{4})\s*(?:[-/.年])\s*(\d{1,2})\s*(?:[-/.月])\s*(\d{1,2})\s*日?\s*$"
)
SUMMARY_RE = re.compile(r"^(?:本页|本月|当月)?(?:小计|合计|总计)$|^累计$")
RESIDENT_ID_NUMBER_RE = re.compile(r"^\d{17}[\dX]$")
MOBILE_RE = re.compile(r"^\d{11}$")


def issue(level: str, code: str, row: int, field: str | None, message: str) -> dict[str, Any]:
    result: dict[str, Any] = {"level": level, "code": code, "row": row, "message": message}
    if field is not None:
        result["field"] = field
    return result


def load_input(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError(f"cannot read input file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise InputError("top-level JSON value must be an object")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise InputError("rows must be an array")
    if len(rows) > 50000:
        raise InputError("rows must contain at most 50000 items")
    return value


def blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def is_summary_row(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return False
    name = str(raw.get("name") or "").strip()
    name = re.sub(r"[：:\s]+$", "", name)
    name = re.sub(r"[（(][^）)]*[）)]$", "", name).strip()
    identifiers_blank = blank(raw.get("id_type")) and blank(raw.get("id_number"))
    return identifiers_blank and bool(SUMMARY_RE.fullmatch(name))


def normalize_text(value: Any, row_number: int, field: str, issues: list[dict[str, Any]]) -> str:
    if blank(value):
        return ""
    if isinstance(value, (dict, list)):
        issues.append(issue("error", "invalid_text", row_number, field, "文本字段不能是对象或数组"))
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = str(value).strip()
    if text.startswith(FORMULA_PREFIXES):
        issues.append(
            issue("warning", "formula_like_text", row_number, field, "该文本以公式字符开头，写入 Excel 时必须强制为文本")
        )
    return text


def normalize_date(value: Any, row_number: int, issues: list[dict[str, Any]]) -> str:
    if blank(value):
        return ""
    text = str(value).strip()
    match = DATE_RE.fullmatch(text)
    if not match:
        issues.append(issue("error", "invalid_date", row_number, "employment_date", "日期必须包含明确的年、月、日"))
        return text
    year, month, day = (int(part) for part in match.groups())
    try:
        parsed = date(year, month, day)
    except ValueError:
        issues.append(issue("error", "invalid_date", row_number, "employment_date", "日期不是有效公历日期"))
        return text
    if not date(1900, 1, 1) <= parsed <= date(2099, 12, 31):
        issues.append(issue("error", "date_out_of_range", row_number, "employment_date", "日期必须在 1900/01/01 至 2099/12/31 之间"))
    return parsed.strftime("%Y/%m/%d")


def normalize_money(value: Any, row_number: int, field: str, issues: list[dict[str, Any]]) -> str:
    if blank(value):
        return ""
    if isinstance(value, bool):
        issues.append(issue("error", "invalid_money", row_number, field, "金额不能是布尔值"))
        return str(value)
    text = str(value).strip().replace(",", "").replace("，", "").replace("￥", "").replace("¥", "")
    negative_parentheses = text.startswith("(") and text.endswith(")")
    if negative_parentheses:
        text = "-" + text[1:-1].strip()
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        issues.append(issue("error", "invalid_money", row_number, field, "金额不是有效数字"))
        return str(value).strip()
    if not number.is_finite():
        issues.append(issue("error", "invalid_money", row_number, field, "金额必须是有限数字"))
        return str(value).strip()
    if number < 0:
        issues.append(issue("error", "negative_money", row_number, field, "模板金额字段不接受负数"))
    if number > MAX_MONEY:
        issues.append(issue("error", "money_out_of_range", row_number, field, "金额超过模板上限 99999999.99"))
        return str(value).strip()
    if number < -MAX_MONEY:
        issues.append(issue("error", "money_out_of_range", row_number, field, "金额绝对值超过模板上限 99999999.99"))
        return str(value).strip()
    try:
        return format(number.quantize(CENT, rounding=ROUND_HALF_UP), "f")
    except InvalidOperation:
        issues.append(issue("error", "invalid_money", row_number, field, "金额精度无法安全规范化"))
        return str(value).strip()


def normalize_row(raw: Any, row_number: int, issues: list[dict[str, Any]]) -> dict[str, str]:
    if not isinstance(raw, dict):
        issues.append(issue("error", "invalid_row", row_number, None, "人员行必须是 JSON 对象"))
        return {field: "" for field in COLUMNS}

    unknown = sorted(str(key) for key in raw.keys() if key not in COLUMNS)
    if unknown:
        issues.append(
            issue("warning", "unknown_fields", row_number, None, "模板没有以下字段：" + "、".join(unknown))
        )

    result: dict[str, str] = {}
    for field in COLUMNS:
        value = raw.get(field)
        if field in TEXT_FIELDS:
            result[field] = normalize_text(value, row_number, field, issues)
        elif field == "employment_date":
            result[field] = normalize_date(value, row_number, issues)
        elif field in MONEY_FIELDS:
            result[field] = normalize_money(value, row_number, field, issues)
        else:
            raise AssertionError(f"unhandled field: {field}")

    for field in REQUIRED_FIELDS:
        if not result[field]:
            issues.append(issue("error", "missing_required", row_number, field, "模板必填字段缺失，保持空白"))

    invalid_id_type = bool(result["id_type"] and result["id_type"] not in ID_TYPES)
    if invalid_id_type:
        issues.append(issue("error", "invalid_enum", row_number, "id_type", "证件类型不在模板枚举中"))
    if (
        result["id_type"] == "居民身份证"
        and result["id_number"]
        and not RESIDENT_ID_NUMBER_RE.fullmatch(result["id_number"])
    ):
        issues.append(
            issue(
                "error",
                "invalid_resident_id_number",
                row_number,
                "id_number",
                "居民身份证号码必须为 18 位：前 17 位为数字，末位为数字或大写 X",
            )
        )
    elif result["id_number"] and (not result["id_type"] or invalid_id_type):
        issues.append(
            issue(
                "error",
                "unverifiable_id_number",
                row_number,
                "id_number",
                "证件类型缺失或不在模板枚举中，无法确认该证件号码是否符合对应类型的格式要求",
            )
        )
    if result["mobile"] and not MOBILE_RE.fullmatch(result["mobile"]):
        issues.append(issue("error", "invalid_mobile", row_number, "mobile", "手机号码必须为 11 位数字"))
    if result["tax_exemption_item"] and result["tax_exemption_item"] not in EXEMPTION_ITEMS:
        issues.append(
            issue("error", "invalid_exemption_item", row_number, "tax_exemption_item", "减免事项不在 Sheet2 清单中")
        )
    if result["tax_exempt_income"] not in ("", "0.00") and not result["tax_exemption_item"]:
        issues.append(
            issue("warning", "missing_exemption_item", row_number, "tax_exemption_item", "免税收入非零但未提供减免事项")
        )
    return result


def validate(data: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    normalized_with_source: list[tuple[int, dict[str, str]]] = []
    for source_index, raw in enumerate(data["rows"], start=1):
        if is_summary_row(raw):
            issues.append(issue("info", "summary_row_excluded", source_index, "name", "识别为汇总行，未计入人员数"))
            continue
        normalized_with_source.append((source_index, normalize_row(raw, source_index, issues)))
    normalized = [row for _, row in normalized_with_source]

    seen: dict[tuple[str, str, str], int] = {}
    for source_index, row in normalized_with_source:
        key = (row["name"], row["id_type"], row["id_number"])
        if not all(key):
            continue
        if key in seen:
            issues.append(
                issue(
                    "warning",
                    "duplicate_person",
                    source_index,
                    None,
                    f"与第 {seen[key]} 行的姓名、证件类型和证件号码完全相同；保留两行",
                )
            )
        else:
            seen[key] = source_index

    error_count = sum(item["level"] == "error" for item in issues)
    warning_count = sum(item["level"] == "warning" for item in issues)
    excluded_summary_count = sum(item["code"] == "summary_row_excluded" for item in issues)
    return {
        "status": "ready" if error_count == 0 and warning_count == 0 else "needs_confirmation",
        "row_count": len(normalized),
        "error_count": error_count,
        "warning_count": warning_count,
        "excluded_summary_count": excluded_summary_count,
        "columns": list(COLUMNS),
        "normalized_rows": normalized,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical rows for the normal salary import template")
    parser.add_argument("input", type=Path, help="UTF-8 JSON file containing a top-level rows array")
    args = parser.parse_args()
    try:
        data = load_input(args.input)
        result = validate(data)
    except InputError as exc:
        print(json.dumps({"status": "fatal", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
