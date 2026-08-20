#!/usr/bin/env python3
"""Analyze VAT burden data from one local JSON file and print JSON to stdout.

The script is intentionally read-only: it performs no network requests and writes no files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any

getcontext().prec = 40

MONEY_FIELDS = (
    "sales_general",
    "output_tax",
    "input_tax_credit",
    "input_tax_transfer_out",
    "opening_credit_balance",
    "closing_credit_balance",
    "tax_general",
    "sales_simple",
    "tax_simple",
    "exempt_sales",
    "tax_reduction",
    "additional_credit",
    "prepaid_tax",
    "vat_payable",
    "vat_paid",
    "retained_tax_refund",
)
UNITS = {"yuan": Decimal("1"), "ten_thousand_yuan": Decimal("10000")}
TAXPAYER_TYPES = {"general", "small_scale"}
PERIOD_RE = re.compile(r"^(\d{4})(?:-(?:(\d{2})|Q([1-4])))?$")
CENT = Decimal("0.01")


class InputError(ValueError):
    """Raised when the input cannot be safely analyzed."""


def decimal_value(value: Any, field: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise InputError(f"{field} must be a decimal number, not boolean")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{field} is not a valid decimal number") from exc
    if not number.is_finite():
        raise InputError(f"{field} must be finite")
    return number


def money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def percent(numerator: Decimal | None, denominator: Decimal | None) -> str | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    result = numerator / denominator * Decimal("100")
    return format(result.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def period_key(period: str) -> tuple[int, int, int]:
    match = PERIOD_RE.fullmatch(period)
    if not match:
        raise InputError(f"period '{period}' must be YYYY, YYYY-MM, or YYYY-Qn")
    year, month, quarter = match.groups()
    if month:
        month_number = int(month)
        if not 1 <= month_number <= 12:
            raise InputError(f"period '{period}' contains an invalid month")
        return int(year), 1, month_number
    if quarter:
        return int(year), 2, int(quarter)
    return int(year), 3, 0


def tolerance(reference: Decimal | None, unit_factor: Decimal) -> Decimal:
    one_yuan_in_unit = Decimal("1") / unit_factor
    proportional = abs(reference or Decimal("0")) * Decimal("0.0001")
    return max(one_yuan_in_unit, proportional)


def issue(level: str, code: str, period: str | None, message: str, **details: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"level": level, "code": code, "message": message}
    if period is not None:
        item["period"] = period
    for key, value in details.items():
        item[key] = money(value) if isinstance(value, Decimal) else value
    return item


def parse_input(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal, parse_int=Decimal)
    except OSError as exc:
        raise InputError(f"cannot read input file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise InputError("top-level JSON value must be an object")
    return raw


def normalize(data: dict[str, Any]) -> tuple[str, str, Decimal, list[dict[str, Any]]]:
    entity = data.get("entity")
    if not isinstance(entity, str) or not entity.strip():
        raise InputError("entity must be a non-empty string")
    unit = data.get("unit")
    if unit not in UNITS:
        raise InputError("unit must be 'yuan' or 'ten_thousand_yuan'")
    periods = data.get("periods")
    if not isinstance(periods, list) or not periods:
        raise InputError("periods must be a non-empty array")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(periods):
        if not isinstance(row, dict):
            raise InputError(f"periods[{index}] must be an object")
        period = row.get("period")
        if not isinstance(period, str):
            raise InputError(f"periods[{index}].period must be a string")
        key = period_key(period)
        if period in seen:
            raise InputError(f"duplicate period '{period}'")
        seen.add(period)
        taxpayer_type = row.get("taxpayer_type")
        if taxpayer_type not in TAXPAYER_TYPES:
            raise InputError(f"{period}.taxpayer_type must be 'general' or 'small_scale'")
        item: dict[str, Any] = {
            "period": period,
            "_period_key": key,
            "taxpayer_type": taxpayer_type,
            "notes": row.get("notes", ""),
        }
        if not isinstance(item["notes"], str):
            raise InputError(f"{period}.notes must be a string")
        for field in MONEY_FIELDS:
            item[field] = decimal_value(row.get(field), f"{period}.{field}")
        normalized.append(item)

    normalized.sort(key=lambda item: item["_period_key"])
    return entity.strip(), unit, UNITS[unit], normalized


def add_reconciliation(
    issues: list[dict[str, Any]],
    period: str,
    code: str,
    label: str,
    actual: Decimal,
    expected: Decimal,
    unit_factor: Decimal,
) -> None:
    difference = actual - expected
    allowed = tolerance(expected, unit_factor)
    if abs(difference) > allowed:
        issues.append(
            issue(
                "warning",
                code,
                period,
                f"{label} differs from the simplified derived amount beyond tolerance",
                actual=actual,
                expected=expected,
                difference=difference,
                tolerance=allowed,
            )
        )


def analyze_period(row: dict[str, Any], unit_factor: Decimal) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    period = row["period"]
    issues: list[dict[str, Any]] = []
    for field in MONEY_FIELDS:
        value = row[field]
        if value is not None and value < 0:
            if row["notes"].strip():
                issues.append(issue("warning", "negative_value", period, f"{field} is negative; notes were provided", field=field, value=value))
            else:
                issues.append(issue("error", "unexplained_negative", period, f"{field} is negative without an explanation", field=field, value=value))

    sg, ss = row["sales_general"], row["sales_simple"]
    taxable_sales = None if sg is None and ss is None else (sg or Decimal("0")) + (ss or Decimal("0"))
    if taxable_sales is None:
        issues.append(issue("info", "missing_taxable_sales", period, "taxable sales are unknown; burden rates cannot be calculated"))
    elif taxable_sales == 0:
        issues.append(issue("info", "zero_taxable_sales", period, "taxable sales are zero; burden rates cannot be calculated"))
    elif taxable_sales < 0:
        issues.append(issue("error", "negative_taxable_sales", period, "total taxable sales are negative; burden rates are blocked", value=taxable_sales))

    general_expected = None
    closing_expected = None
    general_inputs = (
        row["output_tax"],
        row["input_tax_credit"],
        row["input_tax_transfer_out"],
        row["opening_credit_balance"],
    )
    if all(value is not None for value in general_inputs):
        net = row["output_tax"] + row["input_tax_transfer_out"] - row["input_tax_credit"] - row["opening_credit_balance"]
        general_expected = max(net, Decimal("0"))
        closing_expected = max(-net, Decimal("0"))
        if row["tax_general"] is not None:
            add_reconciliation(issues, period, "general_tax_mismatch", "general-method VAT payable", row["tax_general"], general_expected, unit_factor)
        if row["closing_credit_balance"] is not None:
            add_reconciliation(issues, period, "closing_credit_mismatch", "closing input tax credit balance", row["closing_credit_balance"], closing_expected, unit_factor)
    elif any(value is not None for value in general_inputs):
        issues.append(issue("info", "incomplete_general_reconciliation", period, "general-method reconciliation is incomplete because one or more component fields are unknown"))

    overall_expected = None
    components = (row["tax_general"], row["tax_simple"], row["tax_reduction"], row["additional_credit"])
    if all(value is not None for value in components):
        overall_expected = max(row["tax_general"] + row["tax_simple"] - row["tax_reduction"] - row["additional_credit"], Decimal("0"))
        if row["vat_payable"] is not None:
            add_reconciliation(issues, period, "vat_payable_mismatch", "reported VAT payable", row["vat_payable"], overall_expected, unit_factor)

    if row["exempt_sales"] not in (None, Decimal("0")):
        issues.append(issue("info", "exempt_sales_excluded", period, "exempt sales are excluded from the default taxable-sales denominator", value=row["exempt_sales"]))
    if row["retained_tax_refund"] not in (None, Decimal("0")):
        issues.append(issue("info", "retained_refund_disclosed", period, "retained tax refund is disclosed separately and is not treated as negative VAT burden", value=row["retained_tax_refund"]))

    metrics = {
        "period": period,
        "taxpayer_type": row["taxpayer_type"],
        "taxable_sales": money(taxable_sales),
        "vat_payable": money(row["vat_payable"]),
        "vat_paid": money(row["vat_paid"]),
        "comprehensive_burden_rate_pct": percent(row["vat_payable"], taxable_sales),
        "general_burden_rate_pct": percent(row["tax_general"], sg),
        "simple_burden_rate_pct": percent(row["tax_simple"], ss),
        "cash_burden_rate_pct": percent(row["vat_paid"], taxable_sales),
        "output_tax_rate_pct": percent(row["output_tax"], sg),
        "input_credit_contribution_pct": percent(row["input_tax_credit"], row["output_tax"]),
        "derived_general_tax": money(general_expected),
        "derived_closing_credit_balance": money(closing_expected),
        "derived_vat_payable": money(overall_expected),
    }
    return metrics, issues


def comparable_periods(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    return previous["_period_key"][1] == current["_period_key"][1]


def compare(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    prev_sales = None if previous["sales_general"] is None and previous["sales_simple"] is None else (previous["sales_general"] or Decimal("0")) + (previous["sales_simple"] or Decimal("0"))
    curr_sales = None if current["sales_general"] is None and current["sales_simple"] is None else (current["sales_general"] or Decimal("0")) + (current["sales_simple"] or Decimal("0"))
    prev_vat, curr_vat = previous["vat_payable"], current["vat_payable"]
    prev_rate = None if prev_vat is None or prev_sales is None or prev_sales <= 0 else prev_vat / prev_sales * Decimal("100")
    curr_rate = None if curr_vat is None or curr_sales is None or curr_sales <= 0 else curr_vat / curr_sales * Decimal("100")
    rate_change = None if prev_rate is None or curr_rate is None else curr_rate - prev_rate
    sales_change_pct = None
    tax_amount_effect = None
    denominator_effect = None
    if prev_sales is not None and curr_sales is not None and prev_sales > 0 and curr_sales > 0:
        sales_change_pct = (curr_sales / prev_sales - Decimal("1")) * Decimal("100")
        if prev_vat is not None and curr_vat is not None:
            tax_amount_effect = (curr_vat - prev_vat) / prev_sales * Decimal("100")
            denominator_effect = curr_vat * (Decimal("1") / curr_sales - Decimal("1") / prev_sales) * Decimal("100")

    component_changes = {}
    for field in ("output_tax", "input_tax_credit", "input_tax_transfer_out", "closing_credit_balance", "tax_general", "tax_simple", "tax_reduction", "additional_credit", "prepaid_tax", "vat_paid"):
        before, after = previous[field], current[field]
        component_changes[field] = money(after - before) if before is not None and after is not None else None

    return {
        "base_period": previous["period"],
        "current_period": current["period"],
        "comparable_frequency": comparable_periods(previous, current),
        "taxable_sales_change": money(curr_sales - prev_sales) if prev_sales is not None and curr_sales is not None else None,
        "taxable_sales_change_pct": money(sales_change_pct),
        "vat_payable_change": money(curr_vat - prev_vat) if prev_vat is not None and curr_vat is not None else None,
        "burden_rate_change_percentage_points": money(rate_change),
        "tax_amount_effect_percentage_points": money(tax_amount_effect),
        "denominator_effect_percentage_points": money(denominator_effect),
        "component_changes": component_changes,
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    entity, unit, unit_factor, periods = normalize(data)
    metrics: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for row in periods:
        period_metrics, period_issues = analyze_period(row, unit_factor)
        metrics.append(period_metrics)
        issues.extend(period_issues)

    for previous, current in zip(periods, periods[1:]):
        if comparable_periods(previous, current):
            before, after = previous["closing_credit_balance"], current["opening_credit_balance"]
            if before is not None and after is not None:
                allowed = tolerance(before, unit_factor)
                difference = after - before
                if abs(difference) > allowed:
                    issues.append(issue("warning", "credit_balance_discontinuity", current["period"], "opening credit balance does not agree with the preceding closing balance", preceding_period=previous["period"], opening=after, preceding_closing=before, difference=difference, tolerance=allowed))
        else:
            issues.append(issue("info", "mixed_period_frequency", current["period"], "period frequencies differ; continuity checks were skipped", preceding_period=previous["period"]))

    comparisons = [compare(previous, current) for previous, current in zip(periods, periods[1:])]
    counts = {level: sum(1 for item in issues if item["level"] == level) for level in ("error", "warning", "info")}
    if counts["error"]:
        status = "数据异常"
    elif counts["warning"] or any(item["burden_rate_change_percentage_points"] not in (None, "0.00", "-0.00") for item in comparisons):
        status = "波动需要解释"
    else:
        status = "暂未发现明显异常"

    return {
        "schema_version": "1.0",
        "entity": entity,
        "unit": unit,
        "status": status,
        "metrics": metrics,
        "comparisons": comparisons,
        "issues": issues,
        "issue_counts": counts,
        "limitations": [
            "Results are based only on user-provided data and do not replace VAT filings or tax authority determinations.",
            "Simplified reconciliations may not include every statutory VAT return line or special adjustment.",
            "Numerical associations are not, by themselves, evidence of business causation or non-compliance.",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Analyze VAT burden data from a UTF-8 JSON file. The script is read-only and prints JSON to stdout.")
    parser.add_argument("input", type=Path, help="path to the UTF-8 JSON input file")
    parser.add_argument("--pretty", action="store_true", help="pretty-print the JSON result")
    args = parser.parse_args()
    try:
        result = analyze(parse_input(args.input))
    except InputError as exc:
        json.dump({"error": str(exc)}, sys.stderr, ensure_ascii=False)
        sys.stderr.write("\n")
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
