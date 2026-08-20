#!/usr/bin/env python3
"""Validate a generic paperless business-system blueprint deterministically."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
FIELD_TYPES = {"string", "text", "integer", "decimal", "boolean", "date", "datetime", "enum", "json", "file"}
ACTIONS = {"read", "create", "update", "delete", "submit", "approve", "reject", "transition", "export", "admin"}
CONFIDENCE = {"confirmed", "candidate", "derived", "unknown"}


def validate_business_blueprint(blueprint: dict) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []

    def error(code: str, message: str, suggestion: str) -> None:
        errors.append({"code": code, "message": message, "suggestion": suggestion})

    def warning(code: str, message: str, suggestion: str) -> None:
        warnings.append({"code": code, "message": message, "suggestion": suggestion})

    def valid_key(value: object, label: str) -> bool:
        if not isinstance(value, str) or not KEY_RE.fullmatch(value):
            error("BLUEPRINT_KEY_INVALID", f"{label} 不是有效稳定 key：{value!r}", "使用小写字母开头，仅包含小写字母、数字、下划线或连字符的 2-64 位 key。")
            return False
        return True

    if not isinstance(blueprint, dict):
        return {"ok": False, "errors": [{"code": "BLUEPRINT_TYPE_INVALID", "message": "业务蓝图必须是 JSON 对象", "suggestion": "使用业务蓝图模板重新创建。"}], "warnings": []}

    for field in ["schema_version", "project_id", "system_name", "scenario", "organization", "entities", "pages", "roles", "permissions", "workflows", "metrics", "imports", "exports", "audit", "data_retention", "integrations", "ui"]:
        if field not in blueprint:
            error("BLUEPRINT_REQUIRED", f"缺少必填字段：{field}", "按模板补齐后重新校验。")

    valid_key(blueprint.get("project_id"), "project_id")
    if not isinstance(blueprint.get("system_name"), str) or not blueprint.get("system_name", "").strip():
        error("BLUEPRINT_SYSTEM_NAME", "system_name 不能为空", "填写用户可识别的系统名称。")
    scenarios = blueprint.get("scenario")
    if not isinstance(scenarios, list) or not scenarios or not all(isinstance(item, str) and item.strip() for item in scenarios):
        error("BLUEPRINT_SCENARIO", "scenario 必须是非空字符串数组", "至少声明一个真实业务场景。")

    organization = blueprint.get("organization")
    if not isinstance(organization, dict):
        error("BLUEPRINT_ORGANIZATION", "organization 必须是对象", "定义组织范围、显示名和层级。")
    else:
        valid_key(organization.get("scope_key"), "organization.scope_key")
        levels = organization.get("levels")
        if not isinstance(levels, list) or not levels:
            error("BLUEPRINT_ORG_LEVELS", "organization.levels 必须是非空数组", "至少定义一个组织层级。")
        else:
            seen_levels: set[str] = set()
            for item in levels:
                if not isinstance(item, dict) or not valid_key(item.get("key") if isinstance(item, dict) else None, "organization.level.key"):
                    continue
                key = item["key"]
                if key in seen_levels:
                    error("BLUEPRINT_KEY_DUPLICATE", f"组织层级 key 重复：{key}", "为每个层级使用唯一稳定 key。")
                seen_levels.add(key)

    entities = blueprint.get("entities")
    entity_map: dict[str, dict] = {}
    entity_fields: dict[str, set[str]] = {}
    if not isinstance(entities, list) or not entities:
        error("BLUEPRINT_ENTITIES", "entities 必须是非空数组", "至少定义一个可持久化业务实体。")
    else:
        for entity in entities:
            if not isinstance(entity, dict):
                error("BLUEPRINT_ENTITY_TYPE", "实体必须是对象", "修正 entities 中的非对象成员。")
                continue
            key = entity.get("key")
            if not valid_key(key, "entity.key"):
                continue
            if key in entity_map:
                error("BLUEPRINT_KEY_DUPLICATE", f"实体 key 重复：{key}", "使用唯一实体 key。")
                continue
            entity_map[key] = entity
            fields = entity.get("fields")
            field_keys: set[str] = set()
            if not isinstance(fields, list) or not fields:
                error("BLUEPRINT_FIELDS", f"实体 {key} 没有字段", "至少定义业务字段、状态和 version。")
                fields = []
            for field in fields:
                if not isinstance(field, dict):
                    error("BLUEPRINT_FIELD_TYPE", f"实体 {key} 包含非对象字段", "把字段改为对象。")
                    continue
                field_key = field.get("key")
                if not valid_key(field_key, f"{key}.field.key"):
                    continue
                if field_key in field_keys:
                    error("BLUEPRINT_KEY_DUPLICATE", f"实体 {key} 字段 key 重复：{field_key}", "使用唯一字段 key。")
                field_keys.add(field_key)
                if field.get("type") not in FIELD_TYPES:
                    error("BLUEPRINT_FIELD_TYPE_INVALID", f"实体 {key} 字段 {field_key} 类型无效", "使用受支持的数据类型。")
                if field.get("source_confidence") not in CONFIDENCE:
                    warning("BLUEPRINT_CONFIDENCE_MISSING", f"实体 {key} 字段 {field_key} 未声明有效来源置信度", "标记 confirmed、candidate、derived 或 unknown。")
                if field.get("type") == "enum" and (not isinstance(field.get("enum"), list) or not field["enum"]):
                    error("BLUEPRINT_ENUM_EMPTY", f"实体 {key} 枚举字段 {field_key} 没有候选值", "补齐枚举值并保留显示名映射。")
            entity_fields[key] = field_keys
            business_key = entity.get("business_key")
            if not isinstance(business_key, list) or not business_key:
                error("BLUEPRINT_BUSINESS_KEY", f"实体 {key} 缺少业务主键", "定义用于幂等导入和去重的字段组合。")
            else:
                missing = [item for item in business_key if item not in field_keys]
                if missing:
                    error("BLUEPRINT_BUSINESS_KEY_REFERENCE", f"实体 {key} 业务主键引用不存在字段：{', '.join(missing)}", "修正 business_key 或补充字段。")
            if "version" not in field_keys:
                error("BLUEPRINT_OPTIMISTIC_LOCK", f"实体 {key} 缺少 version 字段", "增加整数 version 字段并对冲突返回 HTTP 409。")
            org_field = entity.get("organization_field")
            if org_field and org_field not in field_keys:
                error("BLUEPRINT_ORG_FIELD_REFERENCE", f"实体 {key} 组织范围字段不存在：{org_field}", "补充组织字段或修正引用。")

    def keyed_items(field: str) -> dict[str, dict]:
        value = blueprint.get(field)
        result: dict[str, dict] = {}
        if not isinstance(value, list):
            error("BLUEPRINT_COLLECTION_TYPE", f"{field} 必须是数组", "按模板修正。")
            return result
        for item in value:
            if not isinstance(item, dict) or not valid_key(item.get("key") if isinstance(item, dict) else None, f"{field}.key"):
                continue
            if item["key"] in result:
                error("BLUEPRINT_KEY_DUPLICATE", f"{field} key 重复：{item['key']}", "使用唯一稳定 key。")
            result[item["key"]] = item
        return result

    pages = keyed_items("pages")
    forms = keyed_items("forms") if "forms" in blueprint else {}
    queries = keyed_items("queries") if "queries" in blueprint else {}
    dashboards = keyed_items("dashboards") if "dashboards" in blueprint else {}
    roles = keyed_items("roles")
    permissions = keyed_items("permissions")
    workflows = keyed_items("workflows")
    metrics = keyed_items("metrics")
    imports = keyed_items("imports")
    exports = keyed_items("exports")

    for collection_name, collection in [("page", pages), ("form", forms), ("query", queries), ("permission", permissions), ("workflow", workflows), ("metric", metrics), ("import", imports), ("export", exports)]:
        for key, item in collection.items():
            entity = item.get("entity")
            if entity and entity not in entity_map:
                error("BLUEPRINT_ENTITY_REFERENCE", f"{collection_name} {key} 引用不存在实体：{entity}", "修正实体引用。")
            if collection_name == "page" and item.get("form") and item["form"] not in forms:
                error("BLUEPRINT_FORM_REFERENCE", f"页面 {key} 引用不存在表单：{item['form']}", "修正 form 引用。")
            if entity in entity_fields:
                for ref_field in item.get("fields", []) + item.get("filters", []):
                    if ref_field not in entity_fields[entity]:
                        error("BLUEPRINT_FIELD_REFERENCE", f"{collection_name} {key} 引用实体 {entity} 不存在字段：{ref_field}", "修正字段引用。")

    for key, item in dashboards.items():
        missing = [metric for metric in item.get("metrics", []) if metric not in metrics]
        if missing:
            error("BLUEPRINT_METRIC_REFERENCE", f"看板 {key} 引用不存在指标：{', '.join(missing)}", "修正指标引用。")

    permission_keys = set(permissions)
    for key, item in permissions.items():
        actions = item.get("actions")
        if not isinstance(actions, list) or not actions or any(action not in ACTIONS for action in actions):
            error("BLUEPRINT_PERMISSION_ACTION", f"权限 {key} 包含无效 actions", "使用受支持的权限动作。")

    role_permissions = blueprint.get("role_permissions")
    if not isinstance(role_permissions, dict):
        error("BLUEPRINT_ROLE_PERMISSIONS", "role_permissions 必须是对象", "为每个角色分配权限。")
    else:
        for role_key, assigned in role_permissions.items():
            if role_key not in roles:
                error("BLUEPRINT_ROLE_REFERENCE", f"role_permissions 引用不存在角色：{role_key}", "修正角色引用。")
            if not isinstance(assigned, list):
                error("BLUEPRINT_ROLE_PERMISSION_TYPE", f"角色 {role_key} 权限必须是数组", "使用权限 key 数组。")
                continue
            unknown = [item for item in assigned if item != "*" and item not in permission_keys]
            if unknown:
                error("BLUEPRINT_PERMISSION_REFERENCE", f"角色 {role_key} 引用不存在权限：{', '.join(unknown)}", "修正权限引用。")

    for key, workflow in workflows.items():
        entity = workflow.get("entity")
        states = workflow.get("states")
        transitions = workflow.get("transitions")
        state_field = workflow.get("state_field")
        if entity in entity_fields and state_field not in entity_fields[entity]:
            error("BLUEPRINT_STATE_FIELD", f"工作流 {key} 状态字段不存在：{state_field}", "在实体中增加状态字段或修正引用。")
        if not isinstance(states, list) or len(set(states)) < 2:
            error("BLUEPRINT_STATES", f"工作流 {key} 至少需要两个唯一状态", "补齐起始、处理中和结束状态。")
            states = []
        if not isinstance(transitions, list) or not transitions:
            error("BLUEPRINT_TRANSITIONS", f"工作流 {key} 缺少状态转换", "定义允许的 from、to 与权限。")
            continue
        for transition in transitions:
            if not isinstance(transition, dict):
                error("BLUEPRINT_TRANSITION_TYPE", f"工作流 {key} 包含非对象转换", "修正 transitions。")
                continue
            valid_key(transition.get("key"), f"workflow {key}.transition.key")
            if transition.get("from") not in states or transition.get("to") not in states:
                error("BLUEPRINT_TRANSITION_STATE", f"工作流 {key} 转换引用不存在状态", "修正 from/to。")
            if transition.get("permission") not in permission_keys:
                error("BLUEPRINT_TRANSITION_PERMISSION", f"工作流 {key} 转换引用不存在权限：{transition.get('permission')}", "创建权限或修正引用。")
        for step in workflow.get("approval_steps", []):
            if not isinstance(step, dict) or step.get("role") not in roles:
                error("BLUEPRINT_APPROVAL_ROLE", f"工作流 {key} 审批步骤引用不存在角色", "修正审批角色。")

    for key, item in metrics.items():
        if not isinstance(item.get("formula"), str) or not item["formula"].strip():
            error("BLUEPRINT_METRIC_FORMULA", f"指标 {key} 缺少公式", "定义可版本化且可测试的后端计算规则。")
        if "/" in str(item.get("formula", "")) and item.get("zero_denominator") not in {"show_dash", "show_null", "not_applicable"}:
            error("BLUEPRINT_ZERO_DENOMINATOR", f"指标 {key} 未定义零分母策略", "使用 show_dash、show_null 或 not_applicable。")
        if not item.get("version"):
            error("BLUEPRINT_METRIC_VERSION", f"指标 {key} 缺少规则版本", "为计算规则设置版本。")

    for key, item in imports.items():
        if item.get("entity") in entity_map:
            business_key = item.get("business_key")
            if not isinstance(business_key, list) or not business_key:
                error("BLUEPRINT_IMPORT_KEY", f"导入 {key} 缺少业务主键", "定义幂等键。")
            elif any(field not in entity_fields[item["entity"]] for field in business_key):
                error("BLUEPRINT_IMPORT_KEY_REFERENCE", f"导入 {key} 业务主键引用不存在字段", "修正导入映射。")
        if item.get("idempotency") not in {"file_sha256_and_business_key", "batch_and_business_key"}:
            error("BLUEPRINT_IMPORT_IDEMPOTENCY", f"导入 {key} 未定义受支持的幂等策略", "使用文件指纹或批次加业务主键。")

    audit = blueprint.get("audit")
    if not isinstance(audit, dict) or audit.get("enabled") is not True or audit.get("log_before_after") is not True:
        error("BLUEPRINT_AUDIT", "审计必须启用并记录关键修改前后值", "启用 audit.enabled 和 log_before_after。")
    retention = blueprint.get("data_retention")
    if not isinstance(retention, dict) or not isinstance(retention.get("business_records_days"), int) or retention.get("business_records_days", 0) <= 0:
        error("BLUEPRINT_RETENTION", "数据保留策略无效", "设置正整数保留天数和迁移前备份策略。")
    integrations = blueprint.get("integrations")
    if not isinstance(integrations, dict):
        error("BLUEPRINT_INTEGRATIONS", "integrations 必须是对象", "声明接口是否启用及未配置策略。")
    else:
        if integrations.get("not_configured_policy") != "show_not_configured":
            error("BLUEPRINT_INTEGRATION_TRUTH", "未配置接口必须显示“未配置”", "设置 not_configured_policy 为 show_not_configured。")
        if not integrations.get("enabled") and integrations.get("real_time_claims_allowed") is not False:
            error("BLUEPRINT_REALTIME_CLAIM", "接口未启用时不得声称实时在线", "设置 real_time_claims_allowed 为 false。")
    ui = blueprint.get("ui")
    if not isinstance(ui, dict) or ui.get("responsive") is not True:
        warning("BLUEPRINT_RESPONSIVE", "未明确启用响应式布局", "为桌面和移动端启用 responsive。")

    personal_info = blueprint.get("personal_info")
    if personal_info is not None:
        if not isinstance(personal_info, dict):
            error("BLUEPRINT_PERSONAL_INFO_TYPE", "personal_info 必须是对象", "按国内适配模板定义个人信息保护配置。")
        elif personal_info.get("enabled"):
            for field in ["data_classification", "id_card_masking", "phone_masking", "bank_card_masking", "export_requires_permission", "retention_review_required"]:
                if personal_info.get(field) is not True:
                    error("BLUEPRINT_PERSONAL_INFO_CONTROL", f"个人信息保护缺少或未启用控制：{field}", "补齐数据分类、脱敏、导出权限和保留复核控制。")

    tax_config = blueprint.get("tax_config")
    if tax_config is not None:
        if not isinstance(tax_config, dict):
            error("BLUEPRINT_TAX_CONFIG_TYPE", "tax_config 必须是对象", "按模板定义税务配置。")
        else:
            if tax_config.get("currency") != "CNY":
                warning("BLUEPRINT_CURRENCY", "国内业务默认币种不是 CNY", "确认币种；人民币业务使用 CNY。")
            if tax_config.get("rounding") not in {"ROUND_HALF_UP", "ROUND_HALF_EVEN", "ROUND_DOWN"}:
                error("BLUEPRINT_TAX_ROUNDING", "金额舍入策略无效", "使用已定义的 Decimal 舍入策略。")
            if tax_config.get("automatic_filing") is not False or tax_config.get("automatic_payment") is not False:
                error("BLUEPRINT_PROHIBITED_FINANCIAL_AUTOMATION", "不得默认启用自动报税或自动付款", "保持 automatic_filing 和 automatic_payment 为 false。")
            if tax_config.get("enabled") and tax_config.get("rate_source") in {None, "", "example", "hardcoded"}:
                error("BLUEPRINT_TAX_RATE_SOURCE", "启用税务计算时必须声明用户确认的税率来源", "记录税率来源、有效期和规则版本。")

    fiscal_config = blueprint.get("fiscal_config")
    if fiscal_config is not None:
        if not isinstance(fiscal_config, dict):
            error("BLUEPRINT_FISCAL_CONFIG_TYPE", "fiscal_config 必须是对象", "按模板定义业务月和会计期间。")
        else:
            if fiscal_config.get("period_type") not in {"calendar", "business_month", "fiscal_year"}:
                error("BLUEPRINT_FISCAL_PERIOD", "会计期间类型无效", "使用 calendar、business_month 或 fiscal_year。")
            start_day = fiscal_config.get("business_month_start_day", 1)
            if not isinstance(start_day, int) or not 1 <= start_day <= 28:
                error("BLUEPRINT_BUSINESS_MONTH_START", "业务月起始日必须为 1-28", "避免月底不存在日期造成跨月错误。")
            if fiscal_config.get("holiday_calendar_status") not in {"not_configured", "user_confirmed"}:
                error("BLUEPRINT_HOLIDAY_CALENDAR", "节假日配置状态无效", "未提供有效日历时使用 not_configured。")

    if len(entity_map) < 2:
        warning("BLUEPRINT_SCOPE_NARROW", "蓝图仅包含一个实体，可能仍是单表电子化而非完整业务系统", "根据真实场景补充关联实体、流程、权限或指标。")
    if blueprint.get("confirmation_status") != "confirmed":
        warning("BLUEPRINT_PENDING_CONFIRMATION", "蓝图仍包含待确认或推断内容", "在映射和假设报告中列出，不得伪装为用户已确认。")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="校验通用无纸化业务系统蓝图")
    parser.add_argument("blueprint_file")
    args = parser.parse_args()
    path = Path(args.blueprint_file)
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        result = validate_business_blueprint(payload)
    except FileNotFoundError:
        result = {"ok": False, "errors": [{"code": "BLUEPRINT_FILE_NOT_FOUND", "message": "业务蓝图文件不存在", "suggestion": "从模板创建 config/business-system-blueprint.json。"}], "warnings": []}
    except json.JSONDecodeError as exc:
        result = {"ok": False, "errors": [{"code": "BLUEPRINT_JSON_INVALID", "message": "业务蓝图不是有效 JSON", "suggestion": f"检查第 {exc.lineno} 行第 {exc.colno} 列附近。"}], "warnings": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
