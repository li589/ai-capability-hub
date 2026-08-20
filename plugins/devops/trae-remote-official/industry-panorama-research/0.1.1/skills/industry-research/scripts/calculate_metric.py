#!/usr/bin/env python3
"""Perform a small set of transparent industry-research calculations."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sys
from typing import Sequence


class CalculationError(ValueError):
    """Raised for missing or invalid calculation inputs."""


def decimal_value(raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise CalculationError(f"不是有效数字：{raw}") from exc


def quantize(value: Decimal, precision: int) -> Decimal:
    step = Decimal(1).scaleb(-precision)
    return value.quantize(step, rounding=ROUND_HALF_UP)


def calculate(operation: str, values: Sequence[Decimal], periods: Decimal | None) -> Decimal:
    if operation in {"growth", "share", "multiple"}:
        if len(values) != 2:
            raise CalculationError(f"{operation} 需要两个数值。")
        first, second = values
        if operation == "growth":
            if first == 0:
                raise CalculationError("增长率的基期值不能为零。")
            return (second / first - 1) * 100
        if second == 0:
            raise CalculationError(f"{operation} 的分母不能为零。")
        result = first / second
        return result * 100 if operation == "share" else result

    if operation == "cagr":
        if len(values) != 2 or periods is None:
            raise CalculationError("cagr 需要起始值、结束值和 periods。")
        start, end = values
        if start <= 0 or end < 0 or periods <= 0:
            raise CalculationError("CAGR 的起始值和期数必须大于零，结束值不能为负。")
        return ((end / start) ** (Decimal(1) / periods) - 1) * 100

    if operation == "sum":
        if not values:
            raise CalculationError("sum 至少需要一个数值。")
        return sum(values, Decimal(0))

    if operation == "remainder":
        if len(values) < 2:
            raise CalculationError("remainder 需要总量和至少一个组成项。")
        return values[0] - sum(values[1:], Decimal(0))

    raise CalculationError(f"不支持的运算：{operation}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operation",
        required=True,
        choices=("growth", "cagr", "share", "multiple", "sum", "remainder"),
    )
    parser.add_argument("--values", nargs="+", required=True)
    parser.add_argument("--periods")
    parser.add_argument("--precision", type=int, default=2)
    args = parser.parse_args()
    try:
        if args.precision < 0 or args.precision > 8:
            raise CalculationError("precision 必须在 0 到 8 之间。")
        values = [decimal_value(value) for value in args.values]
        periods = decimal_value(args.periods) if args.periods is not None else None
        result = quantize(calculate(args.operation, values, periods), args.precision)
    except CalculationError as exc:
        print(f"计算失败：{exc}", file=sys.stderr)
        return 1
    print(f"operation={args.operation}")
    print(f"result={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
