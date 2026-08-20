#!/usr/bin/env python3
"""文档内容解析模块 — 提取 FIELD_INPUT_SPEC 结构。

从远程文档原文中查找并解析 ``## FIELD_INPUT_SPEC`` 标记后的 JSON 块，
供 doc_read_tracker 写入缓存、后续 call-api 校验使用。

@author jzc
@date 2026-05-24 18:36
"""
from __future__ import annotations

import json
from typing import Any


def extract_field_input_spec(content: str) -> dict[str, Any]:
    """从文档原文中提取 FIELD_INPUT_SPEC JSON 块。

    解析算法：
    1. 按行分割 content
    2. 逐行查找以 ``## FIELD_INPUT_SPEC`` 开头的行
    3. 找不到 → field_input_spec=None, warnings 含 field_input_spec_missing
    4. 找到 → 取下一行，strip() 后 json.loads()
    5. JSON 解析失败 → field_input_spec=None, warnings 含 field_input_spec_parse_error
    6. JSON 解析成功 → 返回解析结果 + 空 warnings

    Args:
        content: 远程文档的原始文本内容。

    Returns:
        字典，包含 ``field_input_spec``（解析后的 dict 或 None）和 ``warnings``（告警列表）。
    """
    warnings: list[dict[str, str]] = []

    lines = content.splitlines()
    spec_line_index = None

    for i, line in enumerate(lines):
        if line.strip().startswith("## FIELD_INPUT_SPEC"):
            spec_line_index = i
            break

    # Step: 未找到 FIELD_INPUT_SPEC 标记
    if spec_line_index is None:
        warnings.append({"type": "field_input_spec_missing", "message": "当前接口文档未包含 FIELD_INPUT_SPEC 定义"})
        return {"field_input_spec": None, "warnings": warnings}

    # Step: 取标记下一行进行 JSON 解析
    json_line_index = spec_line_index + 1
    if json_line_index >= len(lines):
        warnings.append({"type": "field_input_spec_parse_error", "message": "FIELD_INPUT_SPEC 标记后无有效内容"})
        return {"field_input_spec": None, "warnings": warnings}

    json_text = lines[json_line_index].strip()
    if not json_text:
        warnings.append({"type": "field_input_spec_parse_error", "message": "FIELD_INPUT_SPEC 标记后内容为空"})
        return {"field_input_spec": None, "warnings": warnings}

    # Step: 尝试 JSON 解析
    try:
        spec = json.loads(json_text)
    except json.JSONDecodeError:
        warnings.append({"type": "field_input_spec_parse_error", "message": "FIELD_INPUT_SPEC JSON 解析失败"})
        return {"field_input_spec": None, "warnings": warnings}

    return {"field_input_spec": spec, "warnings": warnings}
