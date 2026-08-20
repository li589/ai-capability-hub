#!/usr/bin/env python3
"""Calculate common e-commerce metrics from a JSON object.

The script never guesses missing inputs. It returns only metrics whose required
inputs are present and valid, plus warnings for invalid denominators.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def number(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    return float(value)


def safe_ratio(
    output: dict[str, float],
    warnings: list[str],
    name: str,
    numerator: float | None,
    denominator: float | None,
) -> None:
    if numerator is None or denominator is None:
        return
    if denominator == 0:
        warnings.append(f"Skipped {name}: denominator is zero")
        return
    output[name] = numerator / denominator


def calculate(data: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "visitors", "orders", "gmv", "discounts", "refunds", "ad_spend",
        "cogs", "platform_fees", "fulfillment_cost", "variable_return_cost",
        "opening_inventory_value", "closing_inventory_value", "period_days",
        "units_sold", "closing_inventory_units", "customers",
        "repeat_customers", "available_days", "in_stock_days",
        "eligible_selling_days", "hero_net_revenue", "total_net_revenue",
    ]
    values = {key: number(data, key) for key in keys}
    metrics: dict[str, float] = {}
    warnings: list[str] = []

    safe_ratio(metrics, warnings, "conversion_rate", values["orders"], values["visitors"])
    safe_ratio(metrics, warnings, "average_order_value", values["gmv"], values["orders"])
    safe_ratio(metrics, warnings, "roas", values["gmv"], values["ad_spend"])
    safe_ratio(metrics, warnings, "ad_cost_ratio", values["ad_spend"], values["gmv"])
    safe_ratio(metrics, warnings, "repeat_customer_rate", values["repeat_customers"], values["customers"])
    safe_ratio(metrics, warnings, "in_stock_rate", values["in_stock_days"], values["available_days"])
    safe_ratio(
        metrics,
        warnings,
        "sales_velocity",
        values["units_sold"],
        values["eligible_selling_days"],
    )
    safe_ratio(
        metrics,
        warnings,
        "bestseller_concentration",
        values["hero_net_revenue"],
        values["total_net_revenue"],
    )

    if values["units_sold"] is not None and values["closing_inventory_units"] is not None:
        safe_ratio(
            metrics,
            warnings,
            "sell_through_rate",
            values["units_sold"],
            values["units_sold"] + values["closing_inventory_units"],
        )

    if values["gmv"] is not None:
        net_revenue = values["gmv"] - (values["discounts"] or 0.0) - (values["refunds"] or 0.0)
        metrics["net_revenue"] = net_revenue
        if values["cogs"] is not None:
            gross_profit = net_revenue - values["cogs"]
            metrics["gross_profit"] = gross_profit
            safe_ratio(metrics, warnings, "gross_margin", gross_profit, net_revenue)

            variable_costs = sum(
                values[key] or 0.0
                for key in (
                    "platform_fees", "fulfillment_cost", "ad_spend", "variable_return_cost"
                )
            )
            contribution_profit = gross_profit - variable_costs
            metrics["contribution_profit"] = contribution_profit
            if values["visitors"] is not None:
                safe_ratio(
                    metrics,
                    warnings,
                    "net_contribution_per_1000_visits",
                    contribution_profit * 1000,
                    values["visitors"],
                )
            safe_ratio(
                metrics,
                warnings,
                "contribution_margin",
                contribution_profit,
                net_revenue,
            )

    opening = values["opening_inventory_value"]
    closing = values["closing_inventory_value"]
    if opening is not None and closing is not None and values["cogs"] is not None:
        average_inventory = (opening + closing) / 2
        safe_ratio(metrics, warnings, "inventory_turnover_period", values["cogs"], average_inventory)
        if values["period_days"] is not None:
            safe_ratio(
                metrics,
                warnings,
                "days_inventory",
                average_inventory * values["period_days"],
                values["cogs"],
            )

    return {
        "metrics": {key: round(value, 6) for key, value in sorted(metrics.items())},
        "warnings": warnings,
        "notes": [
            "Rates are decimals (0.12 means 12%).",
            "GMV, costs, and inventory values must use one currency and period.",
            "Net revenue subtracts discounts and refunds; omit them if GMV is already net.",
        ],
    }


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
