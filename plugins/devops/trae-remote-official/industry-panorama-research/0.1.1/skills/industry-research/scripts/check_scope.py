#!/usr/bin/env python3
"""Check generic structural facts before industry research starts."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Optional, Sequence


ORIGINAL_REQUEST_RE = re.compile(r"^-\s*用户原始请求[：:]\s*(.+)$", re.MULTILINE)
DISCOVERY_SECTION_RE = re.compile(
    r"^##\s+规划前行业发现线索（尚未核实）\s*$"
    r"(?P<body>.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
DISCOVERY_STATUS_RE = re.compile(r"^-\s*状态[：:]\s*(.+?)\s*$", re.MULTILINE)
DISCOVERY_STATUSES = {"已运行", "已跳过"}
PLAN_REQUIRED_FIELDS = (
    "行业定义",
    "包含",
    "不包含",
    "地域",
    "资料截止日",
    "历史观察期",
    "预测期",
    "指定企业或焦点",
)
CARD_REQUIRED_FIELDS = (
    "用户原始请求",
    "行业定义",
    "地域",
    "资料截止日",
    "时间范围",
    "指定企业或焦点",
)


class ScopeError(ValueError):
    """Raised when scope files fail a deterministic structural check."""


def missing_fields(text: str, fields: Sequence[str]) -> list[str]:
    return [
        field
        for field in fields
        if not re.search(rf"^-\s*{re.escape(field)}[：:]", text, re.MULTILINE)
    ]


def validate_scope(work_dir: Path, expected_date: str) -> None:
    plan_path = work_dir / "plan.md"
    card_path = work_dir / "research-card.md"
    missing = [path.name for path in (plan_path, card_path) if not path.is_file()]
    if missing:
        raise ScopeError("缺少规划文件：" + "、".join(missing))

    plan = plan_path.read_text(encoding="utf-8")
    card = card_path.read_text(encoding="utf-8")
    request_match = ORIGINAL_REQUEST_RE.search(card)
    if not request_match:
        raise ScopeError("research-card.md 缺少逐字用户原始请求。")

    structural_errors = []
    for name, text, fields in (
        (plan_path.name, plan, PLAN_REQUIRED_FIELDS),
        (card_path.name, card, CARD_REQUIRED_FIELDS),
    ):
        missing = missing_fields(text, fields)
        if missing:
            structural_errors.append(f"{name} 缺少字段：{'、'.join(missing)}")
    if structural_errors:
        raise ScopeError("；".join(structural_errors))

    discovery_section = DISCOVERY_SECTION_RE.search(card)
    if not discovery_section:
        raise ScopeError(
            "research-card.md 缺少“规划前行业发现线索（尚未核实）”章节。"
        )
    discovery_statuses = DISCOVERY_STATUS_RE.findall(
        discovery_section.group("body")
    )
    if len(discovery_statuses) != 1:
        raise ScopeError("规划前行业发现线索必须且只能填写一个状态。")
    discovery_status = discovery_statuses[0].strip()
    if discovery_status not in DISCOVERY_STATUSES:
        raise ScopeError("规划前行业发现线索状态只能是“已运行”或“已跳过”。")

    expected_line = f"- 资料截止日：{expected_date}"
    wrong_date_files = [
        name
        for name, text in ((plan_path.name, plan), (card_path.name, card))
        if expected_line not in text
    ]
    if wrong_date_files:
        raise ScopeError(
            "资料截止日不是系统研究日 "
            + expected_date
            + "："
            + "、".join(wrong_date_files)
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--expected-date", required=True)
    args = parser.parse_args(argv)
    try:
        validate_scope(args.work_dir, args.expected_date)
    except (OSError, ScopeError) as exc:
        print(f"SCOPE_FAIL: {exc}", file=sys.stderr)
        return 1
    print("SCOPE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
