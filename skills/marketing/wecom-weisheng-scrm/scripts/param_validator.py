#!/usr/bin/env python3
"""参数校验模块。

基于 FIELD_INPUT_SPEC 对 biz_params 执行强校验（不支持字段、必填缺失、
类型不匹配、const 不匹配）和弱校验（paired_fields 等规则），返回结构化
的校验结果和告警。

@author jzc
@date 2026-05-24 20:00
"""
from __future__ import annotations

from typing import Any


def _get_param_map(field_input_spec: dict, section_name: str, doc_url: str) -> tuple[dict[str, dict[str, Any]] | None, list[dict]]:
    """读取指定分区的参数定义集合。"""
    # Step: 分区缺失时按空对象处理，保持兼容旧文档
    section = field_input_spec.get(section_name, {})
    if not isinstance(section, dict):
        return None, [{
            "type": "field_input_spec_invalid",
            "message": "当前接口文档的 FIELD_INPUT_SPEC.{} 结构无效（期望 dict，实际为 {}），字段校验已跳过".format(
                section_name, type(section).__name__
            ),
            "doc_url": doc_url,
        }]

    invalid_names = [key for key, value in section.items() if not isinstance(value, dict)]
    if invalid_names:
        return None, [{
            "type": "field_input_spec_invalid",
            "message": "当前接口文档的 FIELD_INPUT_SPEC.{} 中以下字段定义无效（期望 dict）：{}，字段校验已跳过".format(
                section_name, ", ".join(invalid_names)
            ),
            "doc_url": doc_url,
        }]

    return section, []


def _validate_param_section(
    params: dict,
    field_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """对单个参数分区执行强校验。"""
    # Step: 强校验 — 不支持的字段
    unsupported_fields = [key for key in params if key not in field_map]

    # Step: 强校验 — 必填缺失
    missing_fields = [
        name for name, fdef in field_map.items()
        if fdef.get("required") and name not in params
    ]

    # Step: 强校验 — 类型不匹配
    invalid_type_fields: dict[str, dict[str, str]] = {}
    for key, value in params.items():
        fdef = field_map.get(key)
        if fdef is None:
            continue
        expected = fdef.get("kind", "scalar")
        actual = _value_kind(value)
        if expected != actual:
            invalid_type_fields[key] = {"expected": expected, "actual": actual}

    # Step: 强校验 — const 不匹配
    const_mismatch_fields: dict[str, dict[str, Any]] = {}
    for key, value in params.items():
        fdef = field_map.get(key)
        if fdef is None:
            continue
        const_val = fdef.get("const")
        if const_val is not None and value != const_val:
            const_mismatch_fields[key] = {"expected": const_val, "actual": value}

    return {
        "unsupported_fields": unsupported_fields,
        "missing_fields": missing_fields,
        "invalid_type_fields": invalid_type_fields,
        "const_mismatch_fields": const_mismatch_fields,
    }


def validate_call_params(
    call_params: dict,
    field_input_spec: dict | None,
    doc_url: str = "",
) -> tuple[dict | None, list[dict]]:
    """校验 path/query/body 三段参数是否符合 FIELD_INPUT_SPEC 定义。"""
    # Step: 复用旧逻辑处理 spec 缺失或整体无效场景
    if field_input_spec is None:
        return None, [{
            "type": "field_input_spec_missing",
            "message": "当前接口文档缺少可用的 FIELD_INPUT_SPEC，字段校验已跳过",
            "doc_url": doc_url,
        }]

    if not isinstance(field_input_spec, dict):
        return None, [{
            "type": "field_input_spec_invalid",
            "message": "当前接口文档的 FIELD_INPUT_SPEC 结构无效（期望 dict，实际为 {}），字段校验已跳过".format(
                type(field_input_spec).__name__
            ),
            "doc_url": doc_url,
        }]

    # Step: 读取三个参数分区的定义，保持对旧文档的兼容
    path_param_map, path_warnings = _get_param_map(field_input_spec, "path_params", doc_url)
    if path_warnings:
        return None, path_warnings

    query_param_map, query_warnings = _get_param_map(field_input_spec, "query_params", doc_url)
    if query_warnings:
        return None, query_warnings

    field_map, field_warnings = _get_param_map(field_input_spec, "fields", doc_url)
    if field_warnings:
        return None, field_warnings

    # Step: 分别校验 path/query/body 三段参数
    path_result = _validate_param_section(call_params.get("path_params", {}), path_param_map or {})
    query_result = _validate_param_section(call_params.get("query_params", {}), query_param_map or {})
    body_result = _validate_param_section(call_params.get("fields", {}), field_map or {})

    # Step: 汇总失败项，只输出非空分区
    result: dict[str, Any] = {}
    if any(path_result.values()):
        result["path_params"] = {key: value for key, value in path_result.items() if value}
    if any(query_result.values()):
        result["query_params"] = {key: value for key, value in query_result.items() if value}
    if any(body_result.values()):
        result["fields"] = {key: value for key, value in body_result.items() if value}
    if result:
        return result, []

    # Step: rules 继续只对 body 参数做弱提示，保持与旧逻辑一致
    warnings: list[dict] = []
    rules = field_input_spec.get("rules", [])
    if not isinstance(rules, list):
        rules = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("rule", "") == "paired_fields":
            _check_paired_fields(rule, call_params.get("fields", {}), warnings)

    return None, warnings


def validate_biz_params(
    biz_params: dict,
    field_input_spec: dict | None,
    doc_url: str = "",
) -> tuple[dict | None, list[dict]]:
    """校验 biz_params 是否符合 field_input_spec 定义。

    Args:
        biz_params: 业务参数字典。
        field_input_spec: 从文档中提取的字段输入规范，可能为 None。
        doc_url: 文档 URL，用于告警信息中标识来源。

    Returns:
        (validation_result, warnings) 二元组。
        validation_result 为 None 表示强校验通过，否则为包含失败详情的 dict。
        warnings 为弱校验告警列表。
    """
    # Step: biz_params 不是对象时直接返回结构化失败结果
    if not isinstance(biz_params, dict):
        return {
            "invalid_biz_params": {
                "expected": "object",
                "actual": type(biz_params).__name__,
            }
        }, []

    return validate_call_params({"path_params": {}, "query_params": {}, "fields": biz_params}, field_input_spec, doc_url)


def _value_kind(value: Any) -> str:
    """判断值的类型分类。

    Args:
        value: 待判断的值。

    Returns:
        "scalar"、"object" 或 "array"。
    """
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "scalar"


def _check_paired_fields(rule: dict, biz_params: dict, warnings: list[dict]) -> None:
    """检查 paired_fields 规则：如果只传了部分字段则生成告警。

    Args:
        rule: paired_fields 规则定义。
        biz_params: 业务参数字典。
        warnings: 告警收集列表。
    """
    paired = rule.get("fields", [])
    if not paired:
        return

    present = [f for f in paired if f in biz_params]
    absent = [f for f in paired if f not in biz_params]

    # 只传了部分字段时才告警
    if present and absent:
        warnings.append({
            "rule": "paired_fields",
            "fields": paired,
            "message": rule.get("message", f"以下字段建议同时传入: {', '.join(paired)}，当前缺少: {', '.join(absent)}"),
            "suggested_section": rule.get("suggested_section", ""),
        })
