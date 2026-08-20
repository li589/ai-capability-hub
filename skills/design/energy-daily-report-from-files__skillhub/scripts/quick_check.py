#!/usr/bin/env python3
"""Run one simple read-only check and present a concise Chinese result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from diagnose_and_resume import diagnose
from friendly_error import friendly_error


def quick_check(project: Path, *, deep: bool = False, check_dependencies: bool = True) -> dict:
    diagnosis = diagnose(project, check_dependencies=check_dependencies)
    delivery = None
    domestic = None
    if deep:
        try:
            from validate_delivery import validate
            delivery = validate(project.resolve())
        except Exception as exc:
            delivery = {"ok": False, "errors": [friendly_error(exc)], "warnings": []}
        try:
            from validate_domestic_readiness import check_domestic_readiness
            domestic = check_domestic_readiness(project.resolve())
        except Exception as exc:
            domestic = {"status": "failed", "checks": [], "summary": {}, "error": friendly_error(exc)}
    ok = diagnosis["ok"] and (delivery is None or delivery["ok"]) and (domestic is None or domestic["status"] != "failed")
    problems = []
    for item in diagnosis["state_errors"] + diagnosis["preflight"]["errors"]:
        problems.append({
            "code": item.get("code", "UNKNOWN"),
            "message": item.get("reason") or item.get("message", "未知问题"),
            "action": item.get("action") or item.get("suggestion", "查看日志并保留现场。"),
        })
    if delivery:
        problems.extend({"code": "DELIVERY_CHECK", "message": item, "action": "按交付校验提示补齐后重新运行。"} for item in delivery["errors"])
    if domestic and domestic.get("status") == "failed":
        for item in domestic.get("checks", []):
            if item.get("status") == "failed":
                problems.append({"code": "DOMESTIC_READINESS", "message": item.get("message", "国内部署准备度未通过"), "action": item.get("action") or "按国内适配指南修复。"})
    return {
        "ok": ok,
        "level": "deep" if deep else "quick",
        "headline": "检查通过，可以继续" if ok else "检查未通过，请按下列步骤处理",
        "progress_percent": diagnosis["progress"]["percent"],
        "resume_from": diagnosis["resume_from"],
        "next_action": diagnosis["next_action"],
        "selected_port": diagnosis["preflight"]["selected_port"],
        "problems": problems,
        "warnings": diagnosis["preflight"]["warnings"] + ((delivery or {}).get("warnings", [])),
        "domestic_readiness": domestic,
        "data_safety": diagnosis["data_safety"],
    }


def render_text(result: dict, *, technical: bool = False) -> str:
    lines = [f"[{'通过' if result['ok'] else '未通过'}] {result['headline']}"]
    lines.append(f"- 构建进度：{result['progress_percent']}%")
    lines.append(f"- 建议恢复点：{result['resume_from']}")
    lines.append(f"- 下一步：{result['next_action']}")
    if result["selected_port"]:
        lines.append(f"- 候选端口：{result['selected_port']}")
    lines.append(f"- 数据保护：{result['data_safety']}")
    if result["problems"]:
        lines.append("- 请按顺序处理：")
    for index, item in enumerate(result["problems"], 1):
        code = f" [{item['code']}]" if technical else ""
        lines.append(f"  {index}. {item['message']}{code}")
        lines.append(f"     操作：{item['action']}")
    if result["warnings"]:
        lines.append(f"- 另有 {len(result['warnings'])} 条非阻断提示；使用 --json 查看详情。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="一条命令检查无纸化系统是否可以继续")
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--deep", action="store_true", help="同时运行完整交付校验")
    parser.add_argument("--skip-dependencies", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--technical", action="store_true", help="在文本结果中显示技术错误码")
    args = parser.parse_args()
    result = quick_check(Path(args.project_dir), deep=args.deep, check_dependencies=not args.skip_dependencies)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result, technical=args.technical))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
