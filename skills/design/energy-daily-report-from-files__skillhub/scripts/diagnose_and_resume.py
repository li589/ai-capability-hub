#!/usr/bin/env python3
"""Produce a read-only Chinese diagnosis and deterministic resume recommendation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from preflight_check import run_preflight
from validate_build_state import STAGES, validate_state

ERROR_CATALOG = {
    "FILE_LOCKED": ("文件被其他程序占用", "关闭占用文件的 Excel、WPS 或同步程序后重试。", True),
    "PORT_IN_USE": ("候选端口被占用", "关闭占用端口的程序，或设置 PAPERLESS_PORT 后重试。", True),
    "TEMPORARY_IO": ("发生短暂读写异常", "确认磁盘空间和目录权限正常后重试。", True),
    "OFFLINE_FILE_TEMPORARY": ("离线依赖文件暂时不可读", "关闭占用该文件的软件，确认磁盘可用后重试。", True),
    "CORRUPT_INPUT": ("输入文件损坏", "用原应用打开并另存为受支持格式，再从 ANALYZED 继续。", False),
    "ENCRYPTED_FILE": ("输入文件已加密", "提供未加密副本；不得尝试绕过密码保护。", False),
    "UNSUPPORTED_EXTENSION": ("文件格式不受支持", "另存为 xlsx、csv、docx、pdf、txt 或 md。", False),
    "ZIP_UNSAFE_PATH": ("ZIP 包含不安全路径", "重新打包为单一安全根目录，移除绝对路径、盘符和 ..。", False),
    "MAPPING_CONFLICT": ("关键字段映射冲突", "确认业务主键、组织范围、金额或审批映射后从 MAPPED 继续。", False),
    "DATABASE_INTEGRITY_FAILED": ("数据库完整性检查失败", "停止写入，从最近备份恢复并保留故障副本。", False),
    "TEST_FAILURE": ("必需验收用例失败", "修复失败断言并重测，不得把 pending 或 failed 改写为 passed。", False),
    "SECURITY_CHECK_REJECTED": ("安全检查拒绝继续", "按安全报告修复输入或配置，不得绕过安全门禁。", False),
}

STAGE_COMMANDS = {
    "ANALYZED": "重新运行输入安全检查和结构分析",
    "MAPPED": "重新生成并校验业务蓝图与字段映射",
    "SCAFFOLDED": "核验项目结构后继续生成基础工程",
    "IMPLEMENTED": "继续实现真实主流程、权限、审批和审计",
    "IMPORTED": "从未完成的导入批次继续，禁止重复提交已成功批次",
    "TESTED": "运行完整自动测试并生成真实验收证据",
    "PACKAGED": "运行交付校验，打包并在新目录独立解包复测",
}


def explain_error(error: object) -> dict:
    if not isinstance(error, dict):
        return {"code": "UNKNOWN_ERROR", "reason": "错误记录格式无效", "action": "保留现场并查看日志。", "automatic_retry": False}
    code = str(error.get("code", "UNKNOWN_ERROR")).upper()
    reason, action, retryable = ERROR_CATALOG.get(
        code,
        (str(error.get("message") or "未识别错误"), str(error.get("suggestion") or "保留现场并查看日志。"), False),
    )
    return {"code": code, "reason": reason, "action": action, "automatic_retry": retryable}


def diagnose(project: Path, *, check_dependencies: bool = True) -> dict:
    project = project.resolve()
    preflight = run_preflight(project, check_dependencies=check_dependencies)
    state_path = project / ".build-state.json"
    state_result = None
    state_data: dict = {}
    state_problem = None
    if not state_path.is_file():
        state_problem = {"code": "STATE_FILE_NOT_FOUND", "reason": "缺少 .build-state.json", "action": "从构建状态模板创建文件，并从 ANALYZED 开始。", "automatic_retry": False}
        resume_from = "ANALYZED"
    else:
        try:
            state_data = json.loads(state_path.read_text(encoding="utf-8-sig"))
            state_result = validate_state(state_data, project)
            resume_from = state_result["resume_from"]
        except json.JSONDecodeError as exc:
            state_problem = {"code": "STATE_JSON_INVALID", "reason": f"构建状态 JSON 在第 {exc.lineno} 行第 {exc.colno} 列无效", "action": "修复 JSON 后重新诊断；不要删除已有阶段产物。", "automatic_retry": False}
            resume_from = "ANALYZED"

    completed = [stage for stage in STAGES if isinstance(state_data.get("stages", {}).get(stage), dict) and state_data["stages"][stage].get("status") == "completed"]
    percent = round(len(completed) * 100 / len(STAGES))
    last_error = explain_error(state_data.get("last_error")) if state_data.get("last_error") else None
    state_errors = [explain_error(item) for item in (state_result or {}).get("errors", [])]
    if state_problem:
        state_errors.insert(0, state_problem)

    protected_artifacts = []
    for stage in completed:
        for artifact in state_data.get("stages", {}).get(stage, {}).get("artifacts", []):
            path = artifact.get("path") if isinstance(artifact, dict) else artifact
            if isinstance(path, str):
                protected_artifacts.append(path)

    blocking = bool(preflight["errors"] or state_errors)
    return {
        "ok": not blocking,
        "summary": "项目可继续运行" if not blocking else "项目需要按建议修复后继续",
        "progress": {"completed_stages": completed, "total_stages": len(STAGES), "percent": percent},
        "resume_from": resume_from,
        "next_action": STAGE_COMMANDS[resume_from],
        "data_safety": "诊断全程只读；保留已完成产物和导入批次，不删除数据库或构建状态。",
        "protected_artifacts": sorted(set(protected_artifacts)),
        "last_error": last_error,
        "preflight": {"ok": preflight["ok"], "errors": preflight["errors"], "warnings": preflight["warnings"], "selected_port": preflight["selected_port"]},
        "state_errors": state_errors,
    }


def render_text(result: dict) -> str:
    lines = [f"[{'可继续' if result['ok'] else '需处理'}] {result['summary']}"]
    progress = result["progress"]
    lines.append(f"- 构建进度：{progress['percent']}%（{len(progress['completed_stages'])}/{progress['total_stages']} 阶段）")
    lines.append(f"- 建议恢复点：{result['resume_from']}")
    lines.append(f"- 下一步：{result['next_action']}")
    lines.append(f"- 数据保护：{result['data_safety']}")
    for item in result["state_errors"] + result["preflight"]["errors"] + result["preflight"]["warnings"]:
        code = item.get("code", "UNKNOWN")
        reason = item.get("reason") or item.get("message", "未知问题")
        action = item.get("action") or item.get("suggestion", "查看日志并保留现场。")
        lines.append(f"- [{code}] {reason}；处理：{action}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="一键诊断无纸化系统并给出中文续跑建议")
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--skip-dependencies", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = diagnose(Path(args.project_dir), check_dependencies=not args.skip_dependencies)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
