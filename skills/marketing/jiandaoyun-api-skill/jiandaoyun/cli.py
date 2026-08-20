"""Machine-readable CLI for the Jiandaoyun Agent Skill."""

import argparse
import json
import os
import sys
from pathlib import Path

from .auth import configure_interactively, credential_status, load_api_key
from .client import APIClient
from .errors import JiandaoyunError
from .pagination import list_all_data
from .official_docs import docs_for_tool, fetch_doc, load_catalog, search_docs
from .safety import preview, require_confirmation
from .validation import apply_defaults_and_validate


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = SKILL_ROOT / "schemas"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        result = dispatch(args)
        _emit({"ok": True, **result} if isinstance(result, dict) else {"ok": True, "data": result})
        return 0
    except JiandaoyunError as exc:
        _emit({"ok": False, "error": exc.as_dict()})
        return 1
    except KeyboardInterrupt:
        _emit({"ok": False, "error": {"type": "cancelled", "message": "操作已取消。"}})
        return 130


def dispatch(argv):
    if not argv:
        return {"usage": "jdy <operation|tools|tool-help|configure|doctor> [options]"}
    command = argv.pop(0)
    if command == "configure":
        return _configure(argv)
    if command == "doctor":
        return _doctor(argv)
    if command == "docs":
        return _docs(argv)
    if command == "tools":
        return {"tools": [_summary(load_schema(path.stem)) for path in sorted(SCHEMA_DIR.glob("*.json"))]}
    if command == "tool-help":
        if not argv:
            raise JiandaoyunError("invalid_input", "请指定工具名。")
        return {"tool": load_schema(normalize_operation(argv[0]))}
    return _run_operation(normalize_operation(command), argv)


def normalize_operation(value):
    normalized = value.strip().replace("-", "_")
    if not normalized.startswith("jdy_"):
        normalized = "jdy_" + normalized
    return normalized


def load_schema(operation):
    path = SCHEMA_DIR / f"{operation}.json"
    if not path.exists():
        raise JiandaoyunError("unknown_operation", f"未知操作：{operation}")
    return json.loads(path.read_text(encoding="utf-8"))


def _run_operation(operation, argv):
    parser = argparse.ArgumentParser(prog=f"jdy {operation.removeprefix('jdy_').replace('_', '-')}")
    parser.add_argument("--input-file", help="JSON 输入文件；使用 - 从标准输入读取")
    parser.add_argument("--execute", action="store_true", help="执行写入；默认仅预览")
    parser.add_argument("--confirm-token", default="", help="预览返回的确认令牌")
    parser.add_argument(
        "--acknowledge-destructive",
        action="store_true",
        help="显式确认破坏性操作",
    )
    parser.add_argument(
        "--expected-update-time",
        default="",
        help="更新单条记录前要求匹配的 updateTime",
    )
    parsed = parser.parse_args(argv)
    schema = load_schema(operation)
    supplied = _read_input(parsed.input_file)
    params = apply_defaults_and_validate(schema, supplied)

    if schema["risk"] != "read" and not parsed.execute:
        return preview(schema, params)

    if schema["risk"] != "read":
        require_confirmation(
            schema,
            params,
            parsed.confirm_token,
            parsed.acknowledge_destructive,
        )
        if operation == "jdy_update_data" and not parsed.expected_update_time:
            raise JiandaoyunError(
                "expected_update_time_required",
                "修改单条记录必须提供刚刚读取到的 --expected-update-time。",
            )

    api_key, credential_source = load_api_key()
    client = APIClient(api_key)

    if operation == "jdy_update_data":
        _check_update_time(client, params, parsed.expected_update_time)
    if operation in {"jdy_create_data", "jdy_batch_create_data"}:
        _check_duplicates_before_create(client, operation, params)

    if operation in {"jdy_list_data", "jdy_list_data_2"} and params.get("limit") == 100 and not params.get("data_id"):
        result = list_all_data(client, schema, params)
    else:
        result = client.call(schema, params, allow_read_retries=schema["risk"] == "read")

    response = {
        "operation": operation,
        "risk": schema["risk"],
        "credential_source": _redact_source(credential_source),
        "data": result,
    }
    if schema.get("result_notice"):
        response["result_notice"] = schema["result_notice"]
    readback = _readback_after_write(client, operation, params, result)
    if readback is not None:
        response["readback"] = readback
    return response


def _configure(argv):
    parser = argparse.ArgumentParser(prog="jdy configure")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="从标准输入读取API Key，适合安装器；不要用命令行参数传Key",
    )
    parsed = parser.parse_args(argv)
    path = configure_interactively(sys.stdin if parsed.stdin else None)
    return {
        "configured": True,
        "credential_file": str(path),
        "mode": f"{path.stat().st_mode & 0o777:03o}",
        "warning": "凭据以本地明文保存但权限限制为当前用户可读；不要提交到版本库。",
    }


def _doctor(argv):
    parser = argparse.ArgumentParser(prog="jdy doctor")
    parser.add_argument("--offline", action="store_true", help="只检查本地结构和凭据状态")
    parsed = parser.parse_args(argv)
    schemas = list(SCHEMA_DIR.glob("*.json"))
    status = {
        "schema_count": len(schemas),
        "credential": credential_status(),
        "online_check": "skipped",
    }
    if parsed.offline:
        return status
    api_key, source = load_api_key()
    schema = load_schema("jdy_list_apps")
    client = APIClient(api_key)
    result = client.call(schema, apply_defaults_and_validate(schema, {"limit": 1, "skip": 0}))
    status["online_check"] = "passed"
    status["credential_source"] = _redact_source(source)
    status["sample"] = result
    return status


def _docs(argv):
    parser = argparse.ArgumentParser(prog="jdy docs")
    subparsers = parser.add_subparsers(dest="docs_command", required=True)
    search_parser = subparsers.add_parser("search", help="离线搜索官方API文档目录")
    search_parser.add_argument("query")
    tool_parser = subparsers.add_parser("tool", help="查询工具对应的官方文档")
    tool_parser.add_argument("tool_name")
    fetch_parser = subparsers.add_parser("fetch", help="在线读取一篇官方文档正文")
    fetch_parser.add_argument("reference", help="文档ID、完整标题或官方URL")
    subparsers.add_parser("catalog", help="返回完整离线文档目录")
    parsed = parser.parse_args(argv)
    if parsed.docs_command == "search":
        return {"documents": search_docs(parsed.query)}
    if parsed.docs_command == "tool":
        return {"tool": parsed.tool_name, "documents": docs_for_tool(parsed.tool_name)}
    if parsed.docs_command == "fetch":
        return {"document": fetch_doc(parsed.reference)}
    return load_catalog()


def _check_update_time(client, params, expected):
    schema = load_schema("jdy_get_data")
    current = client.call(
        schema,
        {
            "app_id": params["app_id"],
            "entry_id": params["entry_id"],
            "data_id": params["data_id"],
        },
    )
    record = current.get("data", current) if isinstance(current, dict) else {}
    actual = record.get("updateTime") if isinstance(record, dict) else None
    if actual != expected:
        raise JiandaoyunError(
            "concurrent_modification",
            "记录 updateTime 已变化，已停止写入。",
            details={"expected": expected, "actual": actual},
        )


def _check_duplicates_before_create(client, operation, params):
    if params.get("allow_duplicate"):
        return
    filters = (
        [params["duplicate_check_filter"]]
        if operation == "jdy_create_data"
        else params["duplicate_check_filters"]
    )
    query_schema = load_schema("jdy_list_data_2")
    for index, filter_obj in enumerate(filters):
        result = client.call(
            query_schema,
            {
                "app_id": params["app_id"],
                "entry_id": params["entry_id"],
                "data_id": "",
                "fields": [],
                "filter": filter_obj,
                "limit": 1,
                "max_records": 0,
            },
            allow_read_retries=True,
        )
        records = _extract_records(result)
        if records:
            record = records[0] if isinstance(records[0], dict) else {}
            raise JiandaoyunError(
                "duplicate_detected",
                "查重发现已有记录，已停止新建。若业务上确实允许重复，"
                "请重新预览并由用户明确批准 allow_duplicate=true。",
                details={
                    "batch_index": index if operation == "jdy_batch_create_data" else None,
                    "existing_data_id": record.get("_id"),
                },
            )


def _extract_records(result):
    if not isinstance(result, dict):
        raise JiandaoyunError("invalid_response", "查重响应不是 JSON 对象。")
    records = result.get("data", [])
    if isinstance(records, dict):
        records = records.get("data", [])
    if not isinstance(records, list):
        raise JiandaoyunError("invalid_response", "查重响应中没有数据数组。")
    return records


def _readback_after_write(client, operation, params, result):
    if operation == "jdy_update_data":
        return client.call(
            load_schema("jdy_get_data"),
            {
                "app_id": params["app_id"],
                "entry_id": params["entry_id"],
                "data_id": params["data_id"],
            },
            allow_read_retries=False,
        )
    if operation == "jdy_create_data":
        record = result.get("data", result) if isinstance(result, dict) else {}
        data_id = record.get("_id") if isinstance(record, dict) else None
        if data_id:
            return client.call(
                load_schema("jdy_get_data"),
                {
                    "app_id": params["app_id"],
                    "entry_id": params["entry_id"],
                    "data_id": data_id,
                },
                allow_read_retries=False,
            )
    return None


def _read_input(path):
    if not path:
        return {}
    try:
        if path == "-":
            content = sys.stdin.read()
        else:
            content = Path(path).read_text(encoding="utf-8")
        return json.loads(content)
    except OSError as exc:
        raise JiandaoyunError("invalid_input", f"无法读取输入文件：{path}", details=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise JiandaoyunError("invalid_input", "输入文件不是有效JSON。", details=str(exc)) from exc


def _summary(schema):
    return {
        "name": schema["name"],
        "display_name": schema.get("display_name"),
        "domain": schema.get("domain"),
        "risk": schema["risk"],
    }


def _redact_source(source):
    if source == "environment":
        return source
    return os.path.basename(source)


def _emit(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
