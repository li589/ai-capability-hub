"""Validate a manual report-quality assessment against the approved rubric."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WEIGHTS = {
    "战略清晰度": 10,
    "产品与人群洞察": 15,
    "机制完整性": 10,
    "招募与运营可执行性": 15,
    "财务完整性": 15,
    "Mermaid图表表达": 10,
    "数据可信性": 10,
    "合规安全": 10,
    "语言与阅读体验": 5,
}


def evaluate(payload: dict) -> dict:
    scores = payload["scores"]
    if set(scores) != set(WEIGHTS):
        raise ValueError("scores must contain the exact approved rubric keys")
    for key, maximum in WEIGHTS.items():
        value = scores[key]
        if not isinstance(value, int) or value < 0 or value > maximum:
            raise ValueError(f"score out of range: {key}")
    total = sum(scores.values())
    hard_failures = list(payload.get("hard_failures", []))
    baseline_total = int(payload.get("baseline_total", 56))
    minimum_score = int(payload.get("minimum_score", 80))
    beats_baseline = total > baseline_total
    passed = total >= minimum_score and beats_baseline and not hard_failures
    return {
        "total": total,
        "maximum": sum(WEIGHTS.values()),
        "hard_failures": hard_failures,
        "beats_baseline": beats_baseline,
        "pass": passed,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
