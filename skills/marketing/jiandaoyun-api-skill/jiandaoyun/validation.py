"""Input and filter validation shared by all operations."""

from .errors import JiandaoyunError


FILTER_METHODS = {
    "company": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "account_pool": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "combo": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "combocheck": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "radiogroup": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "checkboxgroup": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "text": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "textarea": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "number": {"eq", "ne", "in", "nin", "gt", "lt", "range", "empty", "not_empty"},
    "date": {"eq", "range", "empty", "not_empty"},
    "datetime": {"eq", "range", "empty", "not_empty"},
    "phone": {"eq", "like", "empty", "not_empty"},
    "sn": {"like", "eq", "empty", "not_empty"},
    "serialno": {"like", "eq", "empty", "not_empty"},
    "user": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "usergroup": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "dept": {"eq", "ne", "in", "nin", "empty", "not_empty"},
    "deptgroup": {"eq", "ne", "in", "nin", "empty", "not_empty"},
}


def apply_defaults_and_validate(schema, supplied):
    if not isinstance(supplied, dict):
        raise JiandaoyunError("invalid_input", "输入必须是 JSON 对象。")

    known = set(schema["params"])
    unknown = sorted(set(supplied) - known)
    if unknown:
        raise JiandaoyunError("invalid_input", f"存在未知参数：{', '.join(unknown)}")

    result = dict(supplied)
    for name, definition in schema["params"].items():
        if name not in result and "default" in definition:
            result[name] = definition["default"]

    missing = [name for name in schema["required_params"] if name not in result]
    if missing:
        raise JiandaoyunError("invalid_input", f"缺少必填参数：{', '.join(missing)}")

    for name, value in result.items():
        expected = schema["params"][name].get("type")
        if not _matches_type(value, expected):
            raise JiandaoyunError(
                "invalid_input",
                f"参数 {name} 类型错误：要求 {expected}，实际为 {type(value).__name__}。",
            )

    _validate_common_limits(schema["name"], result)
    if schema["name"] == "jdy_list_data_2":
        validate_filter(result.get("filter"))
    if schema["name"] == "jdy_create_data":
        _validate_duplicate_guard(result.get("duplicate_check_filter"), result.get("allow_duplicate"))
    if schema["name"] == "jdy_batch_create_data":
        _validate_batch_duplicate_guard(
            result.get("duplicate_check_filters"),
            result.get("allow_duplicate"),
            len(result.get("data_list", [])),
        )
    return result


def _validate_common_limits(operation, params):
    if "limit" in params and not 1 <= params["limit"] <= 100:
        raise JiandaoyunError("invalid_input", "limit 必须在 1 到 100 之间。")
    if "skip" in params and params["skip"] < 0:
        raise JiandaoyunError("invalid_input", "skip 不能小于 0。")
    if params.get("max_records", 0) < 0:
        raise JiandaoyunError("invalid_input", "max_records 不能小于 0。")
    for key in ("data_ids", "data_list"):
        if key in params and len(params[key]) > 100:
            raise JiandaoyunError("invalid_input", f"{key} 每次最多 100 条。")


def _matches_type(value, expected):
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True


def validate_filter(filter_obj):
    if not filter_obj:
        return
    if not isinstance(filter_obj, dict):
        raise JiandaoyunError("invalid_filter", "filter 必须是对象。")
    conditions = filter_obj.get("cond", [])
    if not isinstance(conditions, list):
        raise JiandaoyunError("invalid_filter", "filter.cond 必须是数组。")
    for index, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            raise JiandaoyunError("invalid_filter", f"filter.cond[{index}] 必须是对象。")
        field_type = condition.get("type", "")
        method = condition.get("method", "")
        allowed = FILTER_METHODS.get(field_type)
        if allowed is not None and method not in allowed:
            hint = ""
            if method == "like" and field_type in {
                "text", "textarea", "company", "combo", "combocheck", "radiogroup"
            }:
                hint = " 文本类字段不支持 like；请使用 eq/in，或拉取后在客户端过滤。"
            raise JiandaoyunError(
                "invalid_filter",
                f"字段 {condition.get('field', '')} 的类型 {field_type} "
                f"不支持方法 {method}；允许值：{sorted(allowed)}。{hint}",
            )


def _validate_duplicate_guard(filter_obj, allow_duplicate):
    if allow_duplicate:
        return
    if not filter_obj:
        raise JiandaoyunError(
            "duplicate_check_required",
            "新建数据必须提供 duplicate_check_filter；"
            "只有用户明确接受重复数据时才可设置 allow_duplicate=true。",
        )
    validate_filter(filter_obj)


def _validate_batch_duplicate_guard(filters, allow_duplicate, record_count):
    if allow_duplicate:
        return
    if not filters:
        raise JiandaoyunError(
            "duplicate_check_required",
            "批量新建必须提供与 data_list 一一对应的 duplicate_check_filters；"
            "只有用户明确接受重复数据时才可设置 allow_duplicate=true。",
        )
    if len(filters) != record_count:
        raise JiandaoyunError(
            "invalid_input",
            "duplicate_check_filters 数量必须与 data_list 完全一致。",
        )
    for filter_obj in filters:
        validate_filter(filter_obj)
