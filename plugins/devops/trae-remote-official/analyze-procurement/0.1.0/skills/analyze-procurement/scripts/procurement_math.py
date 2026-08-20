#!/usr/bin/env python3
"""Run transparent procurement calculations from one JSON object.

Supported modes:
  quote_compare, price_trend, supplier_score, inventory, landed_cost

The script assumes that units, specifications, currencies, taxes, and commercial
bases have already been normalized. It warns about visible inconsistencies and
never invents missing decision inputs.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


def as_number(value: Any, field: str, *, required: bool = False) -> float | None:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field} must be finite")
    return float(value)


def as_text(value: Any, field: str, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def as_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def as_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def rounded(value: float) -> float:
    return round(value, 6)


def common_basis(
    rows: list[dict[str, Any]],
    warnings: list[str],
    fields: tuple[str, ...] = ("currency", "unit", "tax_basis", "incoterm"),
) -> dict[str, str]:
    basis: dict[str, str] = {}
    for field in fields:
        values = {
            str(row[field]).strip()
            for row in rows
            if row.get(field) is not None and str(row[field]).strip()
        }
        if len(values) == 1:
            basis[field] = next(iter(values))
        elif len(values) > 1:
            warnings.append(
                f"Mixed {field} values ({', '.join(sorted(values))}); comparison may not be normalized"
            )
    return basis


def sum_optional(row: dict[str, Any], fields: tuple[str, ...], prefix: str) -> float:
    total = 0.0
    for field in fields:
        value = as_number(row.get(field), f"{prefix}.{field}")
        total += value or 0.0
    return total


def quote_compare(payload: dict[str, Any]) -> dict[str, Any]:
    rows = [as_object(row, f"offers[{index}]") for index, row in enumerate(as_list(payload.get("offers"), "offers"))]
    if not rows:
        raise ValueError("offers must contain at least one row")
    warnings: list[str] = []
    basis = common_basis(rows, warnings)
    results: list[dict[str, Any]] = []

    additions = (
        "origin_charges",
        "freight",
        "insurance",
        "duty",
        "nonrecoverable_tax",
        "brokerage",
        "destination_charges",
        "expected_accessorials",
        "implementation",
        "support",
        "switching_cost",
        "expected_failure_cost",
    )
    deductions = ("credits", "rebates", "residual_value")

    for index, row in enumerate(rows):
        prefix = f"offers[{index}]"
        supplier = as_text(row.get("supplier"), f"{prefix}.supplier", required=True)
        quantity = as_number(row.get("quantity"), f"{prefix}.quantity", required=True)
        unit_price = as_number(row.get("unit_price"), f"{prefix}.unit_price", required=True)
        usable_quantity = as_number(row.get("usable_quantity"), f"{prefix}.usable_quantity")
        if quantity is None or quantity <= 0:
            raise ValueError(f"{prefix}.quantity must be greater than zero")
        if unit_price is None or unit_price < 0:
            raise ValueError(f"{prefix}.unit_price must be non-negative")
        if usable_quantity is None:
            usable_quantity = quantity
        if usable_quantity <= 0:
            raise ValueError(f"{prefix}.usable_quantity must be greater than zero")

        goods_cost = quantity * unit_price
        added_cost = sum_optional(row, additions, prefix)
        deducted_cost = sum_optional(row, deductions, prefix)
        economic_total = goods_cost + added_cost - deducted_cost
        recoverable_tax = as_number(row.get("recoverable_tax"), f"{prefix}.recoverable_tax") or 0.0
        cash_requirement = economic_total + recoverable_tax
        if economic_total < 0:
            warnings.append(f"{supplier}: economic total is negative; check credits and rebates")

        results.append(
            {
                "supplier": supplier,
                "goods_cost": rounded(goods_cost),
                "added_cost": rounded(added_cost),
                "deductions": rounded(deducted_cost),
                "economic_total": rounded(economic_total),
                "landed_or_tco_unit_cost": rounded(economic_total / usable_quantity),
                "cash_requirement": rounded(cash_requirement),
                "usable_quantity": rounded(usable_quantity),
            }
        )

    results.sort(key=lambda item: item["economic_total"])
    baseline = results[0]["economic_total"]
    for item in results:
        item["delta_to_lowest"] = rounded(item["economic_total"] - baseline)

    return {
        "mode": "quote_compare",
        "basis": basis,
        "offers": results,
        "warnings": warnings,
        "notes": [
            "Inputs must already share specification, unit, currency/FX date, tax basis, quantity tier, location, and Incoterm.",
            "Recoverable tax is excluded from economic total and included in cash requirement.",
            "Lowest total is not an award recommendation; apply mandatory gates and resilience separately.",
        ],
    }


def parse_month(raw: Any, field: str) -> str:
    text = as_text(raw, field, required=True)
    assert text is not None
    try:
        parsed = date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"{field} must start with an ISO date YYYY-MM-DD") from exc
    return f"{parsed.year:04d}-{parsed.month:02d}"


def price_trend(payload: dict[str, Any]) -> dict[str, Any]:
    rows = [as_object(row, f"rows[{index}]") for index, row in enumerate(as_list(payload.get("rows"), "rows"))]
    if not rows:
        raise ValueError("rows must contain at least one row")
    warnings: list[str] = []
    basis = common_basis(rows, warnings, fields=("currency", "unit", "tax_basis", "item"))
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"quantity": 0.0, "spend": 0.0, "prices": [], "rows": 0}
    )
    excluded = 0

    for index, row in enumerate(rows):
        prefix = f"rows[{index}]"
        quantity = as_number(row.get("quantity"), f"{prefix}.quantity", required=True)
        unit_price = as_number(row.get("unit_price"), f"{prefix}.unit_price", required=True)
        if quantity is None or quantity <= 0 or unit_price is None or unit_price < 0:
            excluded += 1
            warnings.append(f"{prefix} excluded: quantity must be > 0 and unit_price must be >= 0")
            continue
        month = parse_month(row.get("date"), f"{prefix}.date")
        bucket = grouped[month]
        bucket["quantity"] += quantity
        bucket["spend"] += quantity * unit_price
        bucket["prices"].append(unit_price)
        bucket["rows"] += 1

    if not grouped:
        raise ValueError("no valid rows remain after exclusions")

    series: list[dict[str, Any]] = []
    for month in sorted(grouped):
        bucket = grouped[month]
        wap = bucket["spend"] / bucket["quantity"]
        prices = bucket["prices"]
        series.append(
            {
                "month": month,
                "quantity": rounded(bucket["quantity"]),
                "spend": rounded(bucket["spend"]),
                "weighted_average_price": rounded(wap),
                "min_price": rounded(min(prices)),
                "max_price": rounded(max(prices)),
                "median_price": rounded(statistics.median(prices)),
                "included_rows": bucket["rows"],
            }
        )

    base = series[0]["weighted_average_price"]
    for item in series:
        item["price_index"] = rounded(item["weighted_average_price"] / base * 100) if base else None

    return {
        "mode": "price_trend",
        "basis": basis,
        "series": series,
        "included_rows": sum(item["included_rows"] for item in series),
        "excluded_rows": excluded,
        "warnings": warnings,
        "notes": [
            "Monthly average is quantity-weighted.",
            "Choose order, receipt, or invoice date intentionally before supplying rows.",
            "The index uses the first included month as 100.",
        ],
    }


def supplier_score(payload: dict[str, Any]) -> dict[str, Any]:
    criteria = [
        as_object(row, f"criteria[{index}]")
        for index, row in enumerate(as_list(payload.get("criteria"), "criteria"))
    ]
    suppliers = [
        as_object(row, f"suppliers[{index}]")
        for index, row in enumerate(as_list(payload.get("suppliers"), "suppliers"))
    ]
    if not criteria or not suppliers:
        raise ValueError("criteria and suppliers must each contain at least one row")

    parsed_criteria: list[dict[str, Any]] = []
    total_weight = 0.0
    for index, criterion in enumerate(criteria):
        prefix = f"criteria[{index}]"
        name = as_text(criterion.get("name"), f"{prefix}.name", required=True)
        weight = as_number(criterion.get("weight"), f"{prefix}.weight", required=True)
        lower = as_number(criterion.get("lower"), f"{prefix}.lower", required=True)
        upper = as_number(criterion.get("upper"), f"{prefix}.upper", required=True)
        direction = as_text(criterion.get("direction"), f"{prefix}.direction", required=True)
        if weight is None or weight < 0:
            raise ValueError(f"{prefix}.weight must be non-negative")
        if lower is None or upper is None or lower >= upper:
            raise ValueError(f"{prefix} requires lower < upper")
        if direction not in {"higher_better", "lower_better"}:
            raise ValueError(f"{prefix}.direction must be higher_better or lower_better")
        total_weight += weight
        parsed_criteria.append(
            {
                "name": name,
                "weight": weight,
                "lower": lower,
                "upper": upper,
                "direction": direction,
            }
        )
    if total_weight <= 0:
        raise ValueError("criteria weights must sum to more than zero")
    warnings: list[str] = []
    if not math.isclose(total_weight, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        warnings.append(f"Criteria weights sum to {rounded(total_weight)}; scores normalize by active weight")

    output: list[dict[str, Any]] = []
    for index, supplier in enumerate(suppliers):
        prefix = f"suppliers[{index}]"
        supplier_id = as_text(supplier.get("supplier"), f"{prefix}.supplier", required=True)
        metrics = as_object(supplier.get("metrics"), f"{prefix}.metrics")
        gates = supplier.get("gates", {})
        gates = as_object(gates, f"{prefix}.gates")

        failed_gates = sorted(name for name, value in gates.items() if value is False)
        unknown_gates = sorted(name for name, value in gates.items() if value is None)
        invalid_gates = sorted(
            name for name, value in gates.items() if not isinstance(value, (bool, type(None)))
        )
        if invalid_gates:
            raise ValueError(f"{prefix}.gates values must be true, false, or null")
        status = "ineligible" if failed_gates else ("conditional" if unknown_gates else "eligible")

        weighted = 0.0
        active_weight = 0.0
        normalized_metrics: dict[str, float] = {}
        missing_metrics: list[str] = []
        for criterion in parsed_criteria:
            name = criterion["name"]
            value = as_number(metrics.get(name), f"{prefix}.metrics.{name}")
            if value is None:
                missing_metrics.append(name)
                continue
            span = criterion["upper"] - criterion["lower"]
            if criterion["direction"] == "higher_better":
                normalized = (value - criterion["lower"]) / span
            else:
                normalized = (criterion["upper"] - value) / span
            normalized = max(0.0, min(1.0, normalized))
            normalized_metrics[name] = rounded(normalized)
            weighted += criterion["weight"] * normalized
            active_weight += criterion["weight"]

        score = weighted / active_weight * 100 if active_weight else None
        coverage = active_weight / total_weight
        output.append(
            {
                "supplier": supplier_id,
                "gate_status": status,
                "failed_gates": failed_gates,
                "unknown_gates": unknown_gates,
                "score": rounded(score) if score is not None else None,
                "weight_coverage": rounded(coverage),
                "missing_metrics": missing_metrics,
                "normalized_metrics": normalized_metrics,
            }
        )

    status_order = {"eligible": 0, "conditional": 1, "ineligible": 2}
    output.sort(
        key=lambda item: (
            status_order[item["gate_status"]],
            -(item["score"] if item["score"] is not None else -1),
        )
    )
    return {
        "mode": "supplier_score",
        "criteria_weight_sum": rounded(total_weight),
        "suppliers": output,
        "warnings": warnings,
        "notes": [
            "Gates are evaluated before score.",
            "Missing metrics are excluded from the supplier's active weight; compare weight coverage before ranking.",
            "Criterion lower/upper anchors are supplied by the analyst, not inferred from candidates.",
        ],
    }


def round_up_multiple(value: float, multiple: float) -> float:
    return math.ceil(value / multiple - 1e-12) * multiple


def inventory(payload: dict[str, Any]) -> dict[str, Any]:
    items = [as_object(row, f"items[{index}]") for index, row in enumerate(as_list(payload.get("items"), "items"))]
    if not items:
        raise ValueError("items must contain at least one row")
    warnings: list[str] = []
    output: list[dict[str, Any]] = []

    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        item_id = as_text(item.get("item"), f"{prefix}.item", required=True)
        usable = as_number(item.get("usable_on_hand"), f"{prefix}.usable_on_hand", required=True) or 0.0
        receipts = as_number(item.get("scheduled_receipts"), f"{prefix}.scheduled_receipts") or 0.0
        backorders = as_number(item.get("backorders"), f"{prefix}.backorders") or 0.0
        committed = as_number(item.get("committed_demand"), f"{prefix}.committed_demand") or 0.0
        demand = as_number(item.get("average_daily_demand"), f"{prefix}.average_daily_demand", required=True)
        lead_time = as_number(item.get("lead_time_days"), f"{prefix}.lead_time_days", required=True)
        review_period = as_number(item.get("review_period_days"), f"{prefix}.review_period_days") or 0.0
        safety_stock = as_number(item.get("safety_stock"), f"{prefix}.safety_stock")
        if demand is None or demand < 0 or lead_time is None or lead_time < 0:
            raise ValueError(f"{prefix} requires non-negative average_daily_demand and lead_time_days")
        if safety_stock is None:
            z = as_number(item.get("service_z"), f"{prefix}.service_z")
            demand_std = as_number(item.get("demand_std_daily"), f"{prefix}.demand_std_daily")
            if z is not None and demand_std is not None:
                safety_stock = z * demand_std * math.sqrt(lead_time)
            else:
                safety_stock = 0.0
                warnings.append(f"{item_id}: safety_stock missing; used 0")
        if safety_stock < 0:
            raise ValueError(f"{prefix}.safety_stock must be non-negative")

        position = usable + receipts - backorders - committed
        reorder_point = demand * lead_time + safety_stock
        target_position = demand * (lead_time + review_period) + safety_stock
        raw_order = max(0.0, target_position - position)
        moq = as_number(item.get("moq"), f"{prefix}.moq") or 0.0
        multiple = as_number(item.get("order_multiple"), f"{prefix}.order_multiple") or 1.0
        if moq < 0 or multiple <= 0:
            raise ValueError(f"{prefix} requires moq >= 0 and order_multiple > 0")
        constrained = 0.0
        if raw_order > 0:
            constrained = round_up_multiple(max(raw_order, moq), multiple)
        days_supply = position / demand if demand > 0 else None

        output.append(
            {
                "item": item_id,
                "inventory_position": rounded(position),
                "safety_stock": rounded(safety_stock),
                "reorder_point": rounded(reorder_point),
                "target_position": rounded(target_position),
                "raw_order_quantity": rounded(raw_order),
                "constrained_order_quantity": rounded(constrained),
                "days_of_supply": rounded(days_supply) if days_supply is not None else None,
                "below_reorder_point": position < reorder_point,
            }
        )

    output.sort(key=lambda item: (not item["below_reorder_point"], item["days_of_supply"] or math.inf))
    return {
        "mode": "inventory",
        "items": output,
        "warnings": warnings,
        "notes": [
            "Inventory position = usable on hand + scheduled receipts - backorders - committed demand.",
            "Order quantity is rounded up after MOQ and order multiple.",
            "The square-root safety-stock shortcut is unsuitable for intermittent, seasonal, censored, or promotion-driven demand.",
        ],
    }


def landed_cost(payload: dict[str, Any]) -> dict[str, Any]:
    lanes = [as_object(row, f"lanes[{index}]") for index, row in enumerate(as_list(payload.get("lanes"), "lanes"))]
    if not lanes:
        raise ValueError("lanes must contain at least one row")
    warnings: list[str] = []
    basis = common_basis(lanes, warnings, fields=("currency", "unit", "incoterm"))
    fields = (
        "goods_value",
        "origin_charges",
        "main_freight",
        "insurance",
        "duty",
        "nonrecoverable_tax",
        "brokerage",
        "destination_charges",
        "expected_accessorials",
    )
    output: list[dict[str, Any]] = []
    for index, lane in enumerate(lanes):
        prefix = f"lanes[{index}]"
        lane_id = as_text(lane.get("lane"), f"{prefix}.lane", required=True)
        usable_quantity = as_number(lane.get("usable_quantity"), f"{prefix}.usable_quantity", required=True)
        transit_days = as_number(lane.get("transit_days"), f"{prefix}.transit_days")
        if usable_quantity is None or usable_quantity <= 0:
            raise ValueError(f"{prefix}.usable_quantity must be greater than zero")
        total = sum_optional(lane, fields, prefix)
        recoverable_tax = as_number(lane.get("recoverable_tax"), f"{prefix}.recoverable_tax") or 0.0
        feasibility = as_text(lane.get("feasibility"), f"{prefix}.feasibility") or "unknown"
        if feasibility not in {"pass", "conditional", "fail", "unknown"}:
            raise ValueError(f"{prefix}.feasibility must be pass, conditional, fail, or unknown")
        output.append(
            {
                "lane": lane_id,
                "feasibility": feasibility,
                "landed_total": rounded(total),
                "landed_unit_cost": rounded(total / usable_quantity),
                "cash_requirement": rounded(total + recoverable_tax),
                "transit_days": rounded(transit_days) if transit_days is not None else None,
            }
        )
    feasibility_order = {"pass": 0, "conditional": 1, "unknown": 2, "fail": 3}
    output.sort(key=lambda item: (feasibility_order[item["feasibility"]], item["landed_total"]))
    return {
        "mode": "landed_cost",
        "basis": basis,
        "lanes": output,
        "warnings": warnings,
        "notes": [
            "Feasibility sorts before cost; a failed lane cannot win on price.",
            "Duty, tax, HS classification, origin, and valuation must be confirmed for the jurisdiction.",
            "Recoverable tax is excluded from landed total and included in cash requirement.",
        ],
    }


MODES = {
    "quote_compare": quote_compare,
    "price_trend": price_trend,
    "supplier_score": supplier_score,
    "inventory": inventory,
    "landed_cost": landed_cost,
}


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    mode = as_text(payload.get("mode"), "mode", required=True)
    assert mode is not None
    if mode not in MODES:
        raise ValueError(f"mode must be one of: {', '.join(MODES)}")
    return MODES[mode](payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON file; reads stdin when omitted")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        result = calculate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
