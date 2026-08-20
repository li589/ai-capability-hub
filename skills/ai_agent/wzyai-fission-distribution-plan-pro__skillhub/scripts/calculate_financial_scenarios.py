"""Calculate a closed single-order direct-commission scenario."""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys
from typing import Any


CENT = Decimal("0.01")


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> float:
    return float(value.quantize(CENT, rounding=ROUND_HALF_UP))


def calculate_scenario(
    price: float,
    cost: float,
    commission_rate: float,
    operating_rate: float,
    tax_rate: float,
) -> dict[str, float]:
    price_d = _decimal(price)
    cost_d = _decimal(cost)
    rates = [_decimal(commission_rate), _decimal(operating_rate), _decimal(tax_rate)]
    if price_d <= 0:
        raise ValueError("price must be positive")
    if cost_d < 0 or any(rate < 0 for rate in rates):
        raise ValueError("values must be non-negative")
    if sum(rates, Decimal("0")) > Decimal("1"):
        raise ValueError("combined rates cannot exceed one")

    direct_commission = (price_d * rates[0]).quantize(CENT, rounding=ROUND_HALF_UP)
    operating_reserve = (price_d * rates[1]).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_reserve = (price_d * rates[2]).quantize(CENT, rounding=ROUND_HALF_UP)
    company_contribution = (
        price_d - cost_d - direct_commission - operating_reserve - tax_reserve
    ).quantize(CENT, rounding=ROUND_HALF_UP)
    if company_contribution < 0:
        raise ValueError("negative company contribution; revise cost or rates")
    allocated = cost_d + direct_commission + operating_reserve + tax_reserve + company_contribution
    return {
        "price": _money(price_d),
        "hard_cost": _money(cost_d),
        "direct_commission": _money(direct_commission),
        "operating_reserve": _money(operating_reserve),
        "tax_reserve": _money(tax_reserve),
        "company_contribution": _money(company_contribution),
        "closure_delta": _money(price_d - allocated),
    }


def calculate_detailed_scenario(
    price: float,
    hard_cost: float,
    fulfillment_rate: float,
    refund_rate: float,
    platform_rate: float,
    commission_rate: float,
    tax_rate: float,
    operating_rate: float,
    incentive_budget_rate: float,
) -> dict[str, float]:
    price_d = _decimal(price)
    hard_cost_d = _decimal(hard_cost)
    rates = {
        "fulfillment_reserve": _decimal(fulfillment_rate),
        "refund_reserve": _decimal(refund_rate),
        "platform_fee": _decimal(platform_rate),
        "direct_commission": _decimal(commission_rate),
        "tax_reserve": _decimal(tax_rate),
        "operating_reserve": _decimal(operating_rate),
    }
    budget_d = _decimal(incentive_budget_rate)
    if price_d <= 0:
        raise ValueError("price must be positive")
    if hard_cost_d < 0 or budget_d < 0 or any(rate < 0 for rate in rates.values()):
        raise ValueError("values must be non-negative")
    if rates["direct_commission"] > budget_d:
        raise ValueError("commission exceeds incentive budget")
    amounts = {
        key: (price_d * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        for key, rate in rates.items()
    }
    company = (
        price_d - hard_cost_d - sum(amounts.values(), Decimal("0"))
    ).quantize(CENT, rounding=ROUND_HALF_UP)
    if company < 0:
        raise ValueError("negative company contribution; revise cost or rates")
    allocated = hard_cost_d + sum(amounts.values(), Decimal("0")) + company
    return {
        "price": _money(price_d),
        "hard_cost": _money(hard_cost_d),
        **{key: _money(value) for key, value in amounts.items()},
        "company_contribution": _money(company),
        "closure_delta": _money(price_d - allocated),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as stream:
        values = json.load(stream)
    print(json.dumps(calculate_scenario(**values), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
