#!/usr/bin/env python3
"""Validate resumable build state and make deterministic retry decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

STAGES = ["ANALYZED", "MAPPED", "SCAFFOLDED", "IMPLEMENTED", "IMPORTED", "TESTED", "PACKAGED"]
VALID_STATUS = {"pending", "in_progress", "completed", "failed"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TRANSIENT_ERRORS = {"FILE_LOCKED", "PORT_IN_USE", "TEMPORARY_IO", "OFFLINE_FILE_TEMPORARY"}
NON_RETRYABLE_ERRORS = {
    "CORRUPT_INPUT", "ENCRYPTED_FILE", "UNSUPPORTED_EXTENSION", "ZIP_UNSAFE_PATH",
    "BLUEPRINT_JSON_INVALID", "BLUEPRINT_KEY_DUPLICATE", "MAPPING_CONFLICT",
    "DATABASE_INTEGRITY_FAILED", "SECURITY_CHECK_REJECTED", "TEST_FAILURE",
}
MAX_AUTOMATIC_RETRIES = 2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decide_retry(error_code: str, attempt: int) -> dict:
    """Return a stable Chinese recovery decision for an error code and attempt number."""
    code = str(error_code or "").strip().upper()
    if code in TRANSIENT_ERRORS and 0 <= attempt < MAX_AUTOMATIC_RETRIES:
        return {
            "retry": True,
            "next_attempt": attempt + 1,
            "max_attempts": MAX_AUTOMATIC_RETRIES,
            "action": "重新检查前置条件后自动重试；不得重复提交已完成的导入批次。",
        }
    if code in TRANSIENT_ERRORS:
        return {
            "retry": False,
            "next_attempt": attempt,
            "max_attempts": MAX_AUTOMATIC_RETRIES,
            "action": "自动重试次数已用完，保留构建状态并输出中文解决步骤。",
        }
    if code in NON_RETRYABLE_ERRORS:
        return {
            "retry": False,
            "next_attempt": attempt,
            "max_attempts": MAX_AUTOMATIC_RETRIES,
            "action": "不要盲目重试；修复输入、配置、映射、数据库或测试问题后从失败阶段继续。",
        }
    return {
        "retry": False,
        "next_attempt": attempt,
        "max_attempts": MAX_AUTOMATIC_RETRIES,
        "action": "错误类型未列入自动重试白名单；保留现场并先完成诊断。",
    }


def validate_state(
    state: dict,
    project: Path,
    *,
    expected_input_fingerprint: str | None = None,
    expected_profile_sha256: str | None = None,
) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    checks: list[dict] = []

    def add_error(code: str, message: str, suggestion: str) -> None:
        errors.append({"code": code, "message": message, "suggestion": suggestion})

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    if not isinstance(state, dict):
        add_error("STATE_TYPE_INVALID", "构建状态必须是 JSON 对象", "使用构建状态模板重新创建文件。")
        return {"ok": False, "errors": errors, "warnings": warnings, "checks": checks, "resume_from": "ANALYZED"}

    blueprint_field = "business_blueprint_sha256"
    for field in ["schema_version", "skill_version", "project_id", "input_fingerprint", blueprint_field, "calculation_version", "current_stage"]:
        if not isinstance(state.get(field), str) or not state[field].strip():
            add_error("STATE_REQUIRED", f"缺少构建状态字段：{field}", "补齐字段后重新校验。")

    input_fingerprint = state.get("input_fingerprint", "")
    blueprint_sha = state.get(blueprint_field, "")
    if input_fingerprint and not SHA256_RE.fullmatch(input_fingerprint):
        add_error("STATE_INPUT_FINGERPRINT", "输入指纹不是 64 位小写 SHA-256", "重新按排序后的输入文件 SHA-256 计算整体指纹。")
    if blueprint_sha and not SHA256_RE.fullmatch(blueprint_sha):
        add_error("STATE_BLUEPRINT_HASH", "业务蓝图哈希不是 64 位小写 SHA-256", "重新计算 config/business-system-blueprint.json 的 SHA-256。")
    if expected_input_fingerprint and input_fingerprint != expected_input_fingerprint:
        add_error("STATE_INPUT_CHANGED", "输入文件与现有构建状态不一致", "保留旧项目并创建新输出目录，不要复用旧映射或导入状态。")
    if expected_profile_sha256 and blueprint_sha != expected_profile_sha256:
        add_error("STATE_BLUEPRINT_CHANGED", "业务蓝图与现有构建状态不一致", "创建新蓝图/规则版本并重新执行受影响阶段。")

    current = state.get("current_stage")
    if current not in STAGES:
        add_error("STATE_STAGE_INVALID", "current_stage 不是规定的七阶段之一", "使用 ANALYZED 到 PACKAGED 的标准阶段名。")

    stages = state.get("stages")
    if not isinstance(stages, dict):
        add_error("STATE_STAGES_INVALID", "stages 必须是对象", "按模板补齐七个阶段。")
        stages = {}

    first_incomplete = None
    incomplete_seen = False
    for stage in STAGES:
        entry = stages.get(stage)
        if not isinstance(entry, dict):
            add_error("STATE_STAGE_MISSING", f"缺少阶段：{stage}", "按模板补齐该阶段状态和产物列表。")
            if first_incomplete is None:
                first_incomplete = stage
            incomplete_seen = True
            continue
        status = entry.get("status")
        if status not in VALID_STATUS:
            add_error("STATE_STATUS_INVALID", f"阶段 {stage} 状态无效", "使用 pending、in_progress、completed 或 failed。")
            status = "failed"
        if status != "completed" and first_incomplete is None:
            first_incomplete = stage
        if status != "completed":
            incomplete_seen = True
        elif incomplete_seen:
            add_error("STATE_ORDER_INVALID", f"阶段 {stage} 已完成，但前序阶段未完成", "回退到最早未完成阶段，按顺序重新验证。")

        artifacts = entry.get("artifacts", [])
        if not isinstance(artifacts, list):
            add_error("STATE_ARTIFACTS_INVALID", f"阶段 {stage} 的 artifacts 不是列表", "使用相对项目路径数组。")
            artifacts = []
        if status == "completed" and not artifacts:
            add_error("STATE_ARTIFACTS_EMPTY", f"已完成阶段 {stage} 没有记录产物", "记录并校验该阶段关键产物。")
        for artifact in artifacts:
            relative = artifact.get("path") if isinstance(artifact, dict) else artifact
            expected_hash = artifact.get("sha256") if isinstance(artifact, dict) else None
            if not isinstance(relative, str) or not relative.strip():
                add_error("STATE_ARTIFACT_PATH", f"阶段 {stage} 包含无效产物路径", "使用非空相对路径。")
                continue
            normalized = relative.replace("\\", "/")
            pure = PurePosixPath(normalized)
            if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", normalized):
                add_error("STATE_ARTIFACT_UNSAFE_PATH", f"阶段 {stage} 包含不安全产物路径：{relative}", "只记录项目目录内的规范相对路径。")
                continue
            path = project.joinpath(*pure.parts)
            try:
                path.resolve().relative_to(project.resolve())
            except ValueError:
                add_error("STATE_ARTIFACT_UNSAFE_PATH", f"阶段 {stage} 的产物路径越界：{relative}", "删除越界路径并回退到该阶段重新生成。")
                continue
            exists = path.exists()
            add_check(f"artifact:{stage}:{normalized}", exists, "存在" if exists else "缺失")
            if status == "completed" and not exists:
                add_error("STATE_ARTIFACT_MISSING", f"已完成阶段 {stage} 缺少产物：{relative}", "回退到该阶段重新生成，不能继续使用完成标记。")
            if exists and expected_hash:
                if not path.is_file() or not SHA256_RE.fullmatch(str(expected_hash)):
                    add_error("STATE_ARTIFACT_HASH_INVALID", f"产物哈希记录无效：{relative}", "仅为文件记录有效 SHA-256。")
                elif sha256_file(path) != expected_hash:
                    add_error("STATE_ARTIFACT_CHANGED", f"产物内容已变化：{relative}", "回退到产生该文件的阶段并重新测试。")

    resume_from = first_incomplete or "PACKAGED"
    if errors and any(error["code"] in {"STATE_INPUT_CHANGED", "STATE_BLUEPRINT_CHANGED"} for error in errors):
        resume_from = "ANALYZED"
    elif errors:
        for stage in STAGES:
            if any(f"阶段 {stage}" in error["message"] for error in errors):
                resume_from = stage
                break

    last_error = state.get("last_error")
    recovery = None
    if isinstance(last_error, dict) and last_error.get("code"):
        recovery = decide_retry(last_error["code"], int(last_error.get("attempt", 0)))

    add_check("stage_order", not any(error["code"] == "STATE_ORDER_INVALID" for error in errors), f"建议从 {resume_from} 继续")
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "resume_from": resume_from,
        "recovery": recovery,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验无纸化业务系统构建状态并给出续跑阶段")
    parser.add_argument("state_file")
    parser.add_argument("--project-dir")
    parser.add_argument("--input-fingerprint")
    parser.add_argument("--business-blueprint-sha256")
    args = parser.parse_args()
    state_file = Path(args.state_file).resolve()
    project = Path(args.project_dir).resolve() if args.project_dir else state_file.parent
    if not state_file.is_file():
        result = {
            "ok": False,
            "errors": [{"code": "STATE_FILE_NOT_FOUND", "message": "构建状态文件不存在", "suggestion": "从模板创建 .build-state.json。"}],
            "warnings": [], "checks": [], "resume_from": "ANALYZED", "recovery": None,
        }
    else:
        try:
            state = json.loads(state_file.read_text(encoding="utf-8-sig"))
            result = validate_state(
                state,
                project,
                expected_input_fingerprint=args.input_fingerprint,
                expected_profile_sha256=args.business_blueprint_sha256,
            )
        except json.JSONDecodeError as exc:
            result = {
                "ok": False,
                "errors": [{"code": "STATE_JSON_INVALID", "message": "构建状态不是有效 JSON", "suggestion": f"检查第 {exc.lineno} 行第 {exc.colno} 列附近。"}],
                "warnings": [], "checks": [], "resume_from": "ANALYZED", "recovery": None,
            }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
