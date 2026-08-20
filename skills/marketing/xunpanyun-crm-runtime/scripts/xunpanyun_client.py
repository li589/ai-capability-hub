#!/usr/bin/env python3
"""Safe CLI client for LeadsCloud / Xunpanyun OpenAPI."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any
from urllib import error, request


TOKEN_HOST = "https://crm-api.leadscloud.com"
OPENAPI_HOST = "https://open-api.leadscloud.com"
WRITE_OBJECTS = {"lead", "customer", "contact", "opportunity", "followUpRecord"}
POOL_OBJECTS = {"lead", "customer"}

MATCH_TYPES = {
    "exact": 1,
    "eq": 1,
    "contains": 2,
    "lt": 4,
    "lte": 5,
    "gt": 6,
    "gte": 7,
    "ne": 8,
    "any": 9,
    "not-any": 10,
    "range": 11,
    "empty": 12,
    "not-empty": 13,
    "not-contains": 14,
    "dynamic": 15,
    "calendar": 16,
    "contains-all": 17,
    "not-contains-all": 18,
}
SENSITIVE_KEY_PARTS = ("secret", "access_token", "authorization")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {
            key: "[REDACTED]" if any(part in key.lower() for part in SENSITIVE_KEY_PARTS) else redact(item)
            for key, item in value.items()
        }
        item_key = value.get("key")
        if isinstance(item_key, str) and any(part in item_key.lower() for part in SENSITIVE_KEY_PARTS):
            cleaned["value"] = "[REDACTED]"
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return re.sub(
            r"(?i)\b(client_secret|access_token|authorization|bearer)\b\s*[:= ]\s*[^\s,;]+",
            r"\1=[REDACTED]",
            value,
        )
    return value


def emit(payload: Any) -> None:
    print(json.dumps(redact(payload), ensure_ascii=False, indent=2))


def parse_credentials() -> tuple[str, str]:
    client_id = os.environ.get("XUNPANYUN_CLIENT_ID")
    client_secret = os.environ.get("XUNPANYUN_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "AUTH_REQUIRED: set XUNPANYUN_CLIENT_ID and XUNPANYUN_CLIENT_SECRET in the runtime environment."
        )
    return client_id.strip(), client_secret.strip()


def http_json(
    method: str, url: str, token: str | None = None, body: Any = None
) -> tuple[int | str, dict[str, Any]]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(text)
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(text)
        except json.JSONDecodeError:
            return exc.code, {"message": "Non-JSON HTTP error response"}
    except Exception as exc:  # pragma: no cover - defensive CLI surface
        return "ERR", {"error": type(exc).__name__, "message": str(exc)}


def api_error(prefix: str, status: int | str, resp: dict[str, Any]) -> SystemExit:
    safe = {
        "http_status": status,
        "code": resp.get("code"),
        "message": resp.get("messageShow") or resp.get("message") or resp.get("error"),
    }
    return SystemExit(f"{prefix}: {json.dumps(redact(safe), ensure_ascii=False)}")


def get_token(args: argparse.Namespace, scope: str | None = None) -> str:
    client_id, client_secret = parse_credentials()
    body: dict[str, Any] = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if scope:
        body["scope"] = scope
    status, resp = http_json("POST", f"{TOKEN_HOST}/v2-privilege/oidc/token", body=body)
    if resp.get("code") != 10000:
        raise api_error("Token request failed", status, resp)
    token = (resp.get("data") or {}).get("access_token")
    if not isinstance(token, str) or not token:
        raise SystemExit("Token request failed: response did not contain an access token.")
    return token


def rows_from(resp: dict[str, Any]) -> tuple[list[dict[str, Any]], int | None]:
    data = resp.get("data")
    if isinstance(data, dict):
        for key in ["fieldDataList", "records", "rows", "list", "data", "items", "result"]:
            value = data.get(key)
            if isinstance(value, list):
                return value, data.get("total")
        for value in data.values():
            if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                return value, data.get("total")
    if isinstance(data, list):
        return data, None
    return [], None


def fields_from(resp: dict[str, Any]) -> list[dict[str, Any]]:
    data = resp.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["fieldDefinitionList", "records", "rows", "list", "data", "items", "result"]:
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def get_user_id(args: argparse.Namespace, token: str) -> int:
    if getattr(args, "user_id", None):
        return int(args.user_id)
    status, resp = http_json(
        "GET", f"{args.openapi_host}/v2-openapi/organization/users?activate=3", token=token
    )
    if resp.get("code") != 10000:
        raise api_error("Could not query users", status, resp)
    staff = (resp.get("data") or {}).get("fieldDataList") or []
    if not staff:
        raise SystemExit("No staff rows found in organization/users response.")
    admin = next(
        (row for row in staff if row.get("isAdmin") in [1, True] or "系统管理员" in str(row.get("role_value"))),
        staff[0],
    )
    return int(admin["id"])


def get_fields(args: argparse.Namespace, token: str, obj: str) -> list[dict[str, Any]]:
    status, resp = http_json(
        "GET", f"{args.openapi_host}/v2-openapi/crm/objects/{obj}/fields", token=token
    )
    if resp.get("code") != 10000:
        raise api_error(f"Could not query fields for {obj}", status, resp)
    return fields_from(resp)


def field_by_api_key(fields: list[dict[str, Any]], api_key: str) -> dict[str, Any] | None:
    return next((field for field in fields if field.get("apiKey") == api_key), None)


def require_field(fields: list[dict[str, Any]], api_key: str) -> dict[str, Any]:
    field = field_by_api_key(fields, api_key)
    if field:
        return field
    raise SystemExit(f"Field {api_key!r} is not exposed by this tenant's field metadata.")


def default_object_type_id(fields: list[dict[str, Any]]) -> int:
    object_type = field_by_api_key(fields, "objectType")
    options = (object_type or {}).get("optionInfos") or []
    if not options:
        raise SystemExit("Could not discover objectType optionInfos.")
    option = next(
        (item for item in options if "默认" in str(item.get("displayName") or item.get("name") or item.get("optionValue"))),
        options[0],
    )
    return int(option["id"])


def object_id_from_fields(fields: list[dict[str, Any]]) -> int:
    object_id = next((field.get("objectId") for field in fields if field.get("objectId")), None)
    if not object_id:
        raise SystemExit("Could not discover objectId from fields response.")
    return int(object_id)


def parse_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_assignment(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise SystemExit(f"Invalid assignment {raw!r}; expected apiKey=value.")
    key, value = raw.split("=", 1)
    if not key:
        raise SystemExit(f"Invalid assignment {raw!r}; apiKey is empty.")
    return key, parse_value(value)


def build_items(args: argparse.Namespace) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ("name", "email", "phone"):
        value = getattr(args, key, None)
        if value is not None:
            items.append({"key": key, "value": value})
    for raw in getattr(args, "item", None) or []:
        key, value = parse_assignment(raw)
        items.append({"key": key, "value": value})
    if not items:
        raise SystemExit("No fields supplied. Pass --name, --email, --phone, or --item apiKey=value.")
    return items


def validate_items(
    items: list[dict[str, Any]], fields: list[dict[str, Any]], allowed_extra: set[str] | None = None
) -> None:
    exposed = {field.get("apiKey") for field in fields}
    exposed.update(allowed_extra or set())
    missing = sorted({item["key"] for item in items if item["key"] not in exposed})
    if missing:
        raise SystemExit(f"Fields not exposed by this tenant: {', '.join(missing)}")


def prepare_write_body(
    args: argparse.Namespace, token: str | None, obj: str, data_id: int | None = None
) -> dict[str, Any]:
    if obj not in WRITE_OBJECTS:
        raise SystemExit(f"Write support is limited to: {', '.join(sorted(WRITE_OBJECTS))}.")
    fields: list[dict[str, Any]] | None = None
    if token:
        fields = get_fields(args, token, obj)
    if not getattr(args, "object_id", None) or not getattr(args, "object_type_id", None):
        if not token:
            raise SystemExit(
                "Offline dry-run/preview requires --object-id and --object-type-id."
            )
        fields = fields or get_fields(args, token, obj)
    if not getattr(args, "user_id", None) and not token:
        raise SystemExit("Offline dry-run requires --user-id.")
    items = build_items(args)
    if fields:
        validate_items(items, fields)
    body = {
        "objectApiKey": obj,
        "objectId": int(args.object_id) if args.object_id else object_id_from_fields(fields or []),
        "objectTypeId": int(args.object_type_id) if args.object_type_id else default_object_type_id(fields or []),
        "userId": int(args.user_id) if args.user_id else get_user_id(args, token or ""),
        "isRepeatRuleTriggered": not bool(args.skip_repeat_rule),
        "isCheckRuleTriggered": not bool(args.skip_check_rule),
        "items": items,
    }
    if data_id is not None:
        body["dataId"] = int(data_id)
    return body


def write_gate(args: argparse.Namespace, action: str, endpoint: str, body: dict[str, Any]) -> bool:
    preview = {"action": action, "endpoint": endpoint, "request": body}
    if args.dry_run:
        emit({"dry_run": True, **preview})
        return False
    if not args.confirm:
        emit({"requires_confirmation": True, **preview})
        raise SystemExit("Write blocked. Review with --dry-run, then re-run with --confirm.")
    return True


def api_write(args: argparse.Namespace, token: str, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    status, resp = http_json("POST", f"{args.openapi_host}{endpoint}", token=token, body=body)
    return {
        "http_status": status,
        "code": resp.get("code"),
        "message": resp.get("messageShow") or resp.get("message"),
        "data": resp.get("data"),
    }


def write_accepted(write_result: dict[str, Any]) -> bool:
    return write_result.get("code") == 10000


def response_record_id(write_result: dict[str, Any]) -> int | None:
    """Return a unique record ID from documented/common response shapes only."""

    found: set[int] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"dataId", "auto_column_id", "id"}:
                    try:
                        found.add(int(item))
                    except (TypeError, ValueError):
                        pass
                elif isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    data = write_result.get("data")
    if isinstance(data, (int, str)) and not isinstance(data, bool):
        try:
            found.add(int(data))
        except ValueError:
            pass
    else:
        visit(data)
    return next(iter(found)) if len(found) == 1 else None


def item_values(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {str(item["key"]): item.get("value") for item in items}


def safe_verification(call: Any) -> dict[str, Any]:
    try:
        return call()
    except SystemExit as exc:
        return {
            "status": "inconclusive",
            "reason": "verification_query_failed",
            "errorType": type(exc).__name__,
        }
    except Exception as exc:  # pragma: no cover - defensive CLI surface
        return {
            "status": "inconclusive",
            "reason": "verification_query_failed",
            "message": type(exc).__name__,
        }


def public_write_result(write_result: dict[str, Any]) -> dict[str, Any]:
    record_id = response_record_id(write_result)
    return {
        "http_status": write_result.get("http_status"),
        "code": write_result.get("code"),
        "message": write_result.get("message"),
        "responseDataPresent": write_result.get("data") is not None,
        "recordId": record_id,
    }


def emit_write_result(write_result: dict[str, Any], verification: dict[str, Any]) -> None:
    emit({"write": public_write_result(write_result), "verification": verification})


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "auto_column_id", "name", "createdTime", "updatedTime", "createdUser_value",
        "updatedUser_value", "ownerId", "ownerId_value", "email", "phone", "whatsApp",
        "objectType", "objectType_value", "followStatus", "followStatus_value", "stageId",
        "stageId_value", "publicPool_value", "auto_column_public_flag", "auto_column_duplicate_flag",
        "customer", "customer_value", "opportunity", "opportunity_value", "contact", "contact_value",
        "leadTag", "leadTag_value", "sourceType", "sourceType_value", "recentFollowUpTime",
        "recentFollowUpContent",
    ]
    return {key: row[key] for key in keys if key in row}


def cmd_token(args: argparse.Namespace) -> None:
    token = get_token(args)
    emit({"code": 10000, "access_token_present": bool(token)})


def cmd_users(args: argparse.Namespace) -> None:
    token = get_token(args)
    status, resp = http_json(
        "GET", f"{args.openapi_host}/v2-openapi/organization/users?activate=3", token=token
    )
    rows, total = rows_from(resp)
    safe_rows = [
        {
            "id": row.get("id"), "cnName": row.get("cnName"), "enName": row.get("enName"),
            "loginName": row.get("loginName"), "isAdmin": row.get("isAdmin"),
            "role_value": row.get("role_value"), "deleteFlag_value": row.get("deleteFlag_value"),
        }
        for row in rows
    ]
    emit({"http_status": status, "code": resp.get("code"), "total": total, "rows": safe_rows})


def cmd_fields(args: argparse.Namespace) -> None:
    token = get_token(args)
    fields = get_fields(args, token, args.object)
    rows = []
    for field in fields:
        option_infos = field.get("optionInfos") or []
        rows.append({
            "id": field.get("id"), "apiKey": field.get("apiKey"),
            "displayName": field.get("displayName"), "objectId": field.get("objectId"),
            "dataType": field.get("dataType"),
            "options": [
                {"id": item.get("id"), "displayName": item.get("displayName") or item.get("name") or item.get("optionValue")}
                for item in option_infos
            ][:20],
            "optionCount": len(option_infos),
            "optionsTruncated": len(option_infos) > 20,
        })
    emit({"object": args.object, "count": len(rows), "fields": rows})


def parse_match(value: str) -> int:
    if value in MATCH_TYPES:
        return MATCH_TYPES[value]
    try:
        number = int(value)
    except ValueError as exc:
        raise SystemExit(f"Unknown match type {value!r}.") from exc
    if number not in MATCH_TYPES.values():
        raise SystemExit(f"Unsupported match type number {number}.")
    return number


def filter_condition(fields: list[dict[str, Any]], raw: str) -> dict[str, Any]:
    parts = raw.split(":", 2)
    if len(parts) != 3:
        raise SystemExit(f"Invalid filter {raw!r}; expected apiKey:match:value.")
    api_key, match_name, raw_value = parts
    field = require_field(fields, api_key)
    parsed = parse_value(raw_value)
    values = parsed if isinstance(parsed, list) else ([] if match_name in {"empty", "not-empty"} else [parsed])
    search_field = {"id": field["id"]} if field.get("id") is not None else {"apiKey": api_key}
    return {
        "matchType": parse_match(match_name),
        "searchField": search_field,
        "searchRange": [{"values": values, "condMode": 1}],
    }


def verification_field_checks(row: dict[str, Any], expected: dict[str, Any]) -> dict[str, str]:
    """Compare only user-confirmed fields without echoing their values or unrelated PII."""

    checks: dict[str, str] = {}
    for key, wanted in expected.items():
        if key not in row:
            checks[key] = "not_returned"
        elif row.get(key) == wanted or str(row.get(key)) == str(wanted):
            checks[key] = "match"
        else:
            checks[key] = "mismatch"
    return checks


def query_verification(
    args: argparse.Namespace,
    token: str,
    obj: str,
    *,
    data_id: int | None = None,
    exact_filters: dict[str, Any] | None = None,
    expected: dict[str, Any] | None = None,
    unique: bool = True,
    fields: list[dict[str, Any]] | None = None,
    max_pages: int = 100,
) -> dict[str, Any]:
    """Query BizDataList and return a PII-minimized structured verification result."""

    user_id = get_user_id(args, token)
    fields = fields if fields is not None else get_fields(args, token, obj)
    body: dict[str, Any] = {
        "objApiKey": obj,
        "userId": user_id,
        "pageNo": 1,
        "pageSize": 20,
        "includeDeleteData": 0,
        "publicFlag": 0,
    }
    filters = exact_filters or {}
    if filters:
        missing = sorted(key for key in filters if not field_by_api_key(fields, key))
        if missing:
            return {
                "status": "inconclusive",
                "object": obj,
                "reason": "verification_fields_not_exposed",
                "fields": missing,
            }
        body["filterParam"] = {
            "filterType": 1,
            "conditions": [
                filter_condition(fields, f"{key}:exact:{json.dumps(value, ensure_ascii=False)}")
                for key, value in filters.items()
            ],
        }
    endpoint = f"{args.openapi_host}/v2-openapi/crm/objects/BizDataList"
    scanned_pages = 0
    scan_complete = True
    matched: list[dict[str, Any]] = []
    last_status: int | str = "ERR"
    last_resp: dict[str, Any] = {}
    total: int | None = None
    while True:
        last_status, last_resp = http_json("POST", endpoint, token=token, body=body)
        if last_resp.get("code") != 10000:
            return {
                "status": "inconclusive",
                "object": obj,
                "reason": "verification_query_error",
                "http_status": last_status,
                "code": last_resp.get("code"),
                "message": last_resp.get("messageShow") or last_resp.get("message"),
            }
        page_rows, total = rows_from(last_resp)
        scanned_pages += 1
        if data_id is None:
            matched.extend(page_rows)
            break
        matched.extend(
            row for row in page_rows if str(row.get("auto_column_id")) == str(data_id)
        )
        if matched or not page_rows:
            break
        current_page = int(body["pageNo"])
        if total is not None and current_page * int(body["pageSize"]) >= int(total):
            break
        if scanned_pages >= max_pages:
            scan_complete = False
            break
        body["pageNo"] = current_page + 1

    expected = expected or {}
    checks = verification_field_checks(matched[0], expected) if len(matched) == 1 else {}
    count_ok = len(matched) == 1 if unique else len(matched) > 0
    fields_ok = not checks or all(value == "match" for value in checks.values())
    verified = count_ok and fields_ok and scan_complete
    reason = None
    if not scan_complete:
        reason = "scan_limit_reached"
    elif not matched:
        reason = "no_match"
    elif unique and len(matched) != 1:
        reason = "multiple_matches"
    elif not fields_ok:
        reason = "field_check_inconclusive"
    return {
        "status": "verified" if verified else "inconclusive",
        "object": obj,
        "method": "BizDataList",
        "criteria": {"dataId": data_id} if data_id is not None else {"exact": list(filters)},
        "matchCount": len(matched),
        "recordIds": [row.get("auto_column_id") for row in matched[:20]],
        "fieldChecks": checks,
        "scannedPages": scanned_pages,
        "scanComplete": scan_complete,
        "reason": reason,
    }


def order_product_verification(
    args: argparse.Namespace,
    token: str,
    order_id: int,
    details: list[list[dict[str, Any]]],
    delete_detail_ids: list[int],
) -> dict[str, Any]:
    """Verify every requested order-detail create/update/delete without returning PII."""

    fields = get_fields(args, token, "orderProduct")
    preferred = ["order", "orderId", "orderDataId", "parentOrder", "parentOrderId"]
    relation_key = next((key for key in preferred if field_by_api_key(fields, key)), None)
    if relation_key is None:
        return {
            "status": "inconclusive",
            "object": "orderProduct",
            "reason": "order_relation_field_not_exposed",
        }
    checks: list[dict[str, Any]] = []
    for index, items in enumerate(details):
        values = item_values(items)
        raw_data_id = values.pop("dataId", None)
        if raw_data_id is not None:
            try:
                detail_data_id = int(raw_data_id)
            except (TypeError, ValueError):
                checks.append(
                    {
                        "operation": "update",
                        "inputIndex": index,
                        "status": "inconclusive",
                        "reason": "invalid_detail_data_id",
                    }
                )
                continue
            check = query_verification(
                args,
                token,
                "orderProduct",
                data_id=detail_data_id,
                expected=values,
                fields=fields,
            )
            check.update({"operation": "update", "inputIndex": index})
        else:
            sku = values.get("stockKeepingUnit")
            if sku is None:
                check = {
                    "status": "inconclusive",
                    "object": "orderProduct",
                    "reason": "new_detail_missing_sku",
                }
            else:
                check = query_verification(
                    args,
                    token,
                    "orderProduct",
                    exact_filters={relation_key: order_id, "stockKeepingUnit": sku},
                    expected=values,
                    unique=True,
                    fields=fields,
                )
            check.update({"operation": "create", "inputIndex": index})
        checks.append(check)

    for detail_data_id in delete_detail_ids:
        raw_check = query_verification(
            args,
            token,
            "orderProduct",
            data_id=detail_data_id,
            fields=fields,
        )
        deleted = (
            raw_check.get("reason") == "no_match"
            and raw_check.get("scanComplete") is True
        )
        checks.append(
            {
                "operation": "delete",
                "recordId": detail_data_id,
                "status": "verified" if deleted else "inconclusive",
                "reason": None if deleted else "delete_target_still_present_or_query_incomplete",
                "method": raw_check.get("method"),
                "scannedPages": raw_check.get("scannedPages"),
                "scanComplete": raw_check.get("scanComplete"),
            }
        )

    verified = bool(checks) and all(check.get("status") == "verified" for check in checks)
    return {
        "status": "verified" if verified else "inconclusive",
        "object": "orderProduct",
        "relationField": relation_key,
        "requestedCount": len(checks),
        "checks": checks,
        "reason": None if verified else "one_or_more_detail_checks_inconclusive",
    }


def cmd_query(args: argparse.Namespace) -> None:
    token = get_token(args)
    user_id = get_user_id(args, token)
    fields = get_fields(args, token, args.object)
    body: dict[str, Any] = {
        "objApiKey": args.object,
        "userId": user_id,
        "pageNo": args.page_no,
        "pageSize": args.page_size,
        "includeDeleteData": args.include_delete_data,
        "publicFlag": args.public_flag,
    }
    if args.group_api_key:
        body["groupApiKey"] = args.group_api_key
    raw_filters = list(args.filter or [])
    if args.name is not None:
        raw_filters.append(f"name:{args.match}:{args.name}")
    if args.expression and not raw_filters:
        raise SystemExit("--expression requires at least one --filter or --name condition.")
    if raw_filters:
        conditions = [filter_condition(fields, raw) for raw in raw_filters]
        filter_type = 3 if args.expression else (1 if args.filter_mode == "and" else 2)
        body["filterParam"] = {"filterType": filter_type, "conditions": conditions}
        if args.expression:
            body["filterParam"]["expression"] = args.expression
    sort_api_key = args.sort_field or "createdTime"
    sort_field = field_by_api_key(fields, sort_api_key)
    if args.sort_field and not sort_field:
        raise SystemExit(f"Sort field {sort_api_key!r} is not exposed by this tenant.")
    if sort_field:
        sort_types = {"asc": 0, "desc": 1, "none": -1}
        body["BizDataConditionParam"] = {
            "fieldId": sort_field.get("id"),
            "apiKey": sort_api_key,
            "type": sort_types[args.sort_direction],
            "displayName": sort_field.get("displayName") or sort_api_key,
        }
    endpoint = f"{args.openapi_host}/v2-openapi/crm/objects/BizDataList"
    scanned_pages = 0
    scan_complete = True
    while True:
        status, resp = http_json("POST", endpoint, token=token, body=body)
        page_rows, total = rows_from(resp)
        scanned_pages += 1
        if args.data_id is None:
            rows = page_rows
            break
        rows = [row for row in page_rows if str(row.get("auto_column_id")) == str(args.data_id)]
        if rows or not page_rows:
            break
        current_page = int(body["pageNo"])
        if total is not None and current_page * args.page_size >= int(total):
            break
        if scanned_pages >= args.max_pages:
            scan_complete = False
            break
        body["pageNo"] = current_page + 1
    emit(
        {
            "http_status": status, "code": resp.get("code"),
            "message": resp.get("messageShow") or resp.get("message"), "userId": user_id,
            "total": total, "count": len(rows), "scannedPages": scanned_pages,
            "scanComplete": scan_complete,
            "warning": None if scan_complete else "data-id scan stopped at --max-pages before the result set ended",
            "rows": [compact_row(row) if args.compact else row for row in rows],
        }
    )


def cmd_create_object(args: argparse.Namespace) -> None:
    token = get_token(args) if args.confirm else None
    body = prepare_write_body(args, token, args.object)
    endpoint = "/v2-openapi/crm/objects/objFieldData"
    if not write_gate(args, "create", endpoint, body):
        return
    token = token or get_token(args)
    write_result = api_write(args, token, endpoint, body)
    if not write_accepted(write_result):
        emit_write_result(
            write_result,
            {"status": "not_run", "reason": "write_not_accepted"},
        )
        return
    new_id = response_record_id(write_result)
    expected = item_values(body["items"])
    if new_id is not None:
        verification = safe_verification(
            lambda: query_verification(
                args, token, args.object, data_id=new_id, expected=expected
            )
        )
    else:
        confirmed_name = expected.get("name")
        if not isinstance(confirmed_name, str) or not confirmed_name.strip():
            verification = {
                "status": "inconclusive",
                "object": args.object,
                "reason": "response_missing_record_id_and_no_confirmed_name",
            }
        else:
            verification = safe_verification(
                lambda: query_verification(
                    args,
                    token,
                    args.object,
                    exact_filters={"name": confirmed_name},
                    expected=expected,
                )
            )
            verification["fallback"] = "confirmed_name_exact"
    emit_write_result(write_result, verification)


def cmd_update_object(args: argparse.Namespace) -> None:
    token = get_token(args) if args.confirm else None
    body = prepare_write_body(args, token, args.object, int(args.data_id))
    endpoint = "/v2-openapi/crm/objects/objFieldData"
    if not write_gate(args, "update", endpoint, body):
        return
    token = token or get_token(args)
    write_result = api_write(args, token, endpoint, body)
    verification = (
        safe_verification(
            lambda: query_verification(
                args,
                token,
                args.object,
                data_id=int(args.data_id),
                expected=item_values(body["items"]),
            )
        )
        if write_accepted(write_result)
        else {"status": "not_run", "reason": "write_not_accepted"}
    )
    emit_write_result(write_result, verification)


def pool_context(args: argparse.Namespace) -> tuple[str | None, int, int, int]:
    explicit = args.org_id and args.user_id and args.object_id
    if not args.confirm and not explicit:
        raise SystemExit("Offline dry-run/preview requires --org-id, --user-id, and --object-id.")
    token = get_token(args) if args.confirm else None
    if args.org_id:
        org_id = int(args.org_id)
    else:
        client_id, _ = parse_credentials()
        try:
            org_id = int(client_id)
        except ValueError as exc:
            raise SystemExit("The configured client ID is not a numeric orgId; pass --org-id explicitly.") from exc
    user_id = int(args.user_id) if args.user_id else get_user_id(args, token or "")
    if args.object_id:
        object_id = int(args.object_id)
    else:
        object_id = object_id_from_fields(get_fields(args, token or "", args.object))
    return token, org_id, user_id, object_id


def cmd_pool(args: argparse.Namespace) -> None:
    token, org_id, user_id, object_id = pool_context(args)
    body: dict[str, Any] = {
        "orgId": org_id,
        "userId": user_id,
        "objectId": object_id,
        "selectedDataIds": [int(value) for value in args.selected_data_id],
    }
    if args.pool_action in {"assign", "transfer"}:
        body["selectedUserId"] = int(args.selected_user_id)
    if args.pool_action == "assign":
        endpoint = "/v2-openapi/crm/public-pool/objects/batch-assign"
    elif args.pool_action == "transfer":
        endpoint = "/v2-openapi/crm/private-pool/objects/batch-assign"
        body["isReserve"] = bool(args.is_reserve)
    else:
        endpoint = "/v2-openapi/crm/public-pool/objects/batch-return"
        body["returnReason"] = int(args.return_reason)
        if args.return_desc:
            body["returnDesc"] = args.return_desc
    if not write_gate(args, f"pool-{args.pool_action}", endpoint, body):
        return
    write_result = api_write(args, token or get_token(args), endpoint, body)
    accepted = write_accepted(write_result)
    emit(
        {
            "write": public_write_result(write_result),
            "accepted": accepted,
            "verification": {
                "status": "pending_system_notification" if accepted else "not_run",
                "reason": "pool_operations_are_asynchronous" if accepted else "write_not_accepted",
                "recordIds": body["selectedDataIds"],
            },
        }
    )


def cmd_opportunity_stage(args: argparse.Namespace) -> None:
    token = get_token(args) if args.confirm else None
    if not args.user_id and not token:
        raise SystemExit("Offline dry-run requires --user-id.")
    body: dict[str, Any] = {
        "updateUserId": int(args.user_id) if args.user_id else get_user_id(args, token or ""),
        "opportunityId": int(args.opportunity_id),
        "salesStageStatus": int(args.sales_stage_status),
        "salesStageId": int(args.sales_stage_id),
        "forward": False,
    }
    optional = {
        "lastStageId": args.last_stage_id,
        "transactionAmount": args.transaction_amount,
        "winReason": args.win_reason,
        "winDesc": args.win_desc,
    }
    body.update({key: value for key, value in optional.items() if value is not None})
    if args.update_transaction_time:
        body["updateTransactionTime"] = True
    endpoint = "/v2-openapi/crm/objects/salesStageStatus"
    if not write_gate(args, "opportunity-stage", endpoint, body):
        return
    token = token or get_token(args)
    write_result = api_write(args, token, endpoint, body)
    if write_accepted(write_result):
        opportunity_fields = get_fields(args, token, "opportunity")
        stage_key = next(
            (
                key
                for key in ("stageId", "salesStageId", "saleStageId")
                if field_by_api_key(opportunity_fields, key)
            ),
            None,
        )
        verification = (
            safe_verification(
                lambda: query_verification(
                    args,
                    token,
                    "opportunity",
                    data_id=int(args.opportunity_id),
                    expected={stage_key: body["salesStageId"]},
                    fields=opportunity_fields,
                )
            )
            if stage_key is not None
            else {
                "status": "inconclusive",
                "object": "opportunity",
                "reason": "stage_field_not_exposed",
            }
        )
    else:
        verification = {"status": "not_run", "reason": "write_not_accepted"}
    emit_write_result(write_result, verification)


def detail_items(raw: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid --detail-json value: {exc}") from exc
    if not isinstance(value, dict) or not value:
        raise SystemExit("--detail-json must be a non-empty JSON object.")
    return [{"key": key, "value": item} for key, item in value.items()]


def cmd_order_data(args: argparse.Namespace) -> None:
    explicit = args.user_id and args.main_object_id and args.main_object_type_id
    detail_requested = bool(args.detail_json or args.delete_detail_id)
    if detail_requested:
        explicit = explicit and args.detail_object_id and args.detail_object_type_id
    if not args.confirm and not explicit:
        required = "--user-id, --main-object-id, and --main-object-type-id"
        if detail_requested:
            required += ", plus --detail-object-id and --detail-object-type-id for detail changes"
        raise SystemExit(f"Offline dry-run/preview requires {required}.")
    token = get_token(args, scope="crm.write") if args.confirm else None
    if not args.user_id and not token:
        raise SystemExit("Offline dry-run requires --user-id.")
    order_fields = get_fields(args, token, "order") if token else []
    main_items = build_items(args)
    main_keys = {item["key"] for item in main_items}
    if not args.data_id:
        required_main = {"ownerId", "customer", "objectType", "orderTime"}
        missing_main = sorted(required_main - main_keys)
        if missing_main:
            raise SystemExit(f"New orders require main fields: {', '.join(missing_main)}")
        if not detail_requested and not {"orderAmount", "originalAmount"}.issubset(main_keys):
            raise SystemExit("A new order without details requires orderAmount and originalAmount.")
    if order_fields:
        validate_items(main_items, order_fields)
    main_object: dict[str, Any] = {
        "objectId": int(args.main_object_id) if args.main_object_id else object_id_from_fields(order_fields),
        "objectTypeId": int(args.main_object_type_id) if args.main_object_type_id else default_object_type_id(order_fields),
        "objectApiKey": "order",
        "objectTypeApiKey": args.main_object_type_api_key,
        "isCheckRuleTriggered": not bool(args.skip_check_rule),
        "isRepeatRuleTriggered": not bool(args.skip_repeat_rule),
        "items": main_items,
    }
    if args.data_id:
        main_object["dataId"] = int(args.data_id)
    body: dict[str, Any] = {
        "userId": int(args.user_id) if args.user_id else get_user_id(args, token or ""),
        "mainObject": main_object,
    }
    if detail_requested:
        detail_fields = get_fields(args, token, "orderProduct") if token else []
        details = [detail_items(raw) for raw in args.detail_json or []]
        for items in details:
            detail_map = {item["key"]: item["value"] for item in items}
            required_detail = {"stockKeepingUnit", "quantity", "unitPrice"}
            missing_detail = sorted(required_detail - detail_map.keys())
            if missing_detail:
                raise SystemExit(f"Each order detail requires: {', '.join(missing_detail)}")
            quantity = detail_map["quantity"]
            if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or quantity < 1:
                raise SystemExit("Each order-detail quantity must be a number greater than or equal to 1.")
        if detail_fields:
            for items in details:
                validate_items(items, detail_fields, allowed_extra={"dataId"})
        sub_object: dict[str, Any] = {
            "objectId": int(args.detail_object_id) if args.detail_object_id else object_id_from_fields(detail_fields),
            "objectTypeId": int(args.detail_object_type_id) if args.detail_object_type_id else default_object_type_id(detail_fields),
            "objectApiKey": "orderProduct",
            "objectTypeApiKey": args.detail_object_type_api_key,
            "isCheckRuleTriggered": not bool(args.skip_check_rule),
            "isRepeatRuleTriggered": not bool(args.skip_repeat_rule),
            "items": details,
        }
        if args.delete_detail_id:
            sub_object["deleteDataIds"] = [int(value) for value in args.delete_detail_id]
        body["subObject"] = sub_object
    endpoint = "/v2-openapi/crm/objects/orderData"
    if not write_gate(args, "order-data", endpoint, body):
        return
    token = token or get_token(args, scope="crm.write")
    write_result = api_write(args, token, endpoint, body)
    if not write_accepted(write_result):
        emit_write_result(
            write_result,
            {"status": "not_run", "reason": "write_not_accepted"},
        )
        return
    order_id = int(args.data_id) if args.data_id else response_record_id(write_result)
    expected = item_values(main_object["items"])
    if order_id is not None:
        order_check = safe_verification(
            lambda: query_verification(
                args, token, "order", data_id=order_id, expected=expected
            )
        )
    else:
        confirmed_name = expected.get("name")
        if isinstance(confirmed_name, str) and confirmed_name.strip():
            order_check = safe_verification(
                lambda: query_verification(
                    args,
                    token,
                    "order",
                    exact_filters={"name": confirmed_name},
                    expected=expected,
                )
            )
            order_check["fallback"] = "confirmed_name_exact"
            ids = order_check.get("recordIds") or []
            if order_check.get("status") == "verified" and len(ids) == 1:
                try:
                    order_id = int(ids[0])
                except (TypeError, ValueError):
                    order_id = None
        else:
            order_check = {
                "status": "inconclusive",
                "object": "order",
                "reason": "response_missing_record_id_and_no_confirmed_name",
            }
    detail_delete_ids = [int(value) for value in args.delete_detail_id or []]
    detail_check = (
        safe_verification(
            lambda: order_product_verification(
                args, token, order_id, details, detail_delete_ids
            )
        )
        if detail_requested and order_id is not None
        else {
            "status": "not_requested" if not detail_requested else "inconclusive",
            "object": "orderProduct",
            "reason": None if not detail_requested else "order_id_unavailable",
        }
    )
    overall_verified = order_check.get("status") == "verified" and detail_check.get(
        "status"
    ) in {"verified", "not_requested"}
    emit_write_result(
        write_result,
        {
            "status": "verified" if overall_verified else "inconclusive",
            "order": order_check,
            "orderProduct": detail_check,
        },
    )


def https_host(value: str) -> str:
    host = value.rstrip("/")
    if not host.lower().startswith("https://"):
        raise argparse.ArgumentTypeError("--openapi-host must use HTTPS")
    return host


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--openapi-host", default=OPENAPI_HOST, type=https_host)
    parser.add_argument("--user-id", help="CRM user ID for permission checks and writes")


def add_write_guard(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="Print the request body without writing")
    group.add_argument("--confirm", action="store_true", help="Required to execute the write")


def add_item_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name")
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--item", action="append", help="Field assignment apiKey=value; value may be JSON")


def add_write_common(parser: argparse.ArgumentParser) -> None:
    add_item_args(parser)
    parser.add_argument("--object-id")
    parser.add_argument("--object-type-id")
    parser.add_argument("--skip-repeat-rule", action="store_true", help="Disable duplicate checking; requires explicit business approval")
    parser.add_argument("--skip-check-rule", action="store_true", help="Disable business validation; requires explicit business approval")
    add_write_guard(parser)


def add_pool_common(parser: argparse.ArgumentParser) -> None:
    add_common(parser)
    parser.add_argument("object", choices=sorted(POOL_OBJECTS))
    parser.add_argument("--org-id")
    parser.add_argument("--object-id")
    parser.add_argument("--selected-data-id", action="append", required=True)
    add_write_guard(parser)
    parser.set_defaults(func=cmd_pool)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LeadsCloud / Xunpanyun OpenAPI helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("token")
    add_common(p)
    p.set_defaults(func=cmd_token)

    p = sub.add_parser("users")
    add_common(p)
    p.set_defaults(func=cmd_users)

    p = sub.add_parser("fields")
    add_common(p)
    p.add_argument("object")
    p.set_defaults(func=cmd_fields)

    p = sub.add_parser("query")
    add_common(p)
    p.add_argument("object")
    p.add_argument("--name")
    p.add_argument("--match", choices=["exact", "contains"], default="exact")
    p.add_argument("--data-id", type=int)
    p.add_argument("--max-pages", type=int, default=100, help="Maximum pages scanned for --data-id")
    p.add_argument("--filter", action="append", help="Repeatable apiKey:match:value filter")
    p.add_argument("--filter-mode", choices=["and", "or"], default="and")
    p.add_argument("--expression", help="Advanced formula such as '(1 or 2) and 3'")
    p.add_argument("--sort-field")
    p.add_argument("--sort-direction", choices=["asc", "desc", "none"], default="desc")
    p.add_argument("--group-api-key")
    p.add_argument("--public-flag", type=int, choices=[0, 1], default=0)
    p.add_argument("--include-delete-data", type=int, choices=[0, 1], default=0)
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--full", dest="compact", action="store_false")
    p.set_defaults(func=cmd_query, compact=True)

    p = sub.add_parser("create")
    add_common(p)
    p.add_argument("object", choices=sorted(WRITE_OBJECTS))
    add_write_common(p)
    p.set_defaults(func=cmd_create_object)

    p = sub.add_parser("update")
    add_common(p)
    p.add_argument("object", choices=sorted(WRITE_OBJECTS))
    p.add_argument("--data-id", required=True)
    add_write_common(p)
    p.set_defaults(func=cmd_update_object)

    pool = sub.add_parser("pool")
    pool_sub = pool.add_subparsers(dest="pool_action", required=True)
    p = pool_sub.add_parser("assign")
    add_pool_common(p)
    p.add_argument("--selected-user-id", required=True)
    p = pool_sub.add_parser("transfer")
    add_pool_common(p)
    p.add_argument("--selected-user-id", required=True)
    p.add_argument("--is-reserve", action="store_true")
    p = pool_sub.add_parser("return")
    add_pool_common(p)
    p.add_argument("--return-reason", required=True)
    p.add_argument("--return-desc")

    p = sub.add_parser("opportunity-stage")
    add_common(p)
    p.add_argument("--opportunity-id", required=True)
    p.add_argument("--sales-stage-status", required=True)
    p.add_argument("--sales-stage-id", required=True)
    p.add_argument("--last-stage-id", type=int)
    p.add_argument("--transaction-amount", type=float)
    p.add_argument("--win-reason", type=int)
    p.add_argument("--win-desc")
    p.add_argument("--update-transaction-time", action="store_true")
    add_write_guard(p)
    p.set_defaults(func=cmd_opportunity_stage)

    p = sub.add_parser("order-data")
    add_common(p)
    add_item_args(p)
    p.add_argument("--data-id")
    p.add_argument("--main-object-id")
    p.add_argument("--main-object-type-id")
    p.add_argument("--main-object-type-api-key", default="defaultObjectType")
    p.add_argument("--detail-object-id")
    p.add_argument("--detail-object-type-id")
    p.add_argument("--detail-object-type-api-key", default="defaultObjectType")
    p.add_argument("--detail-json", action="append", help="One order-detail JSON object; repeat for multiple rows")
    p.add_argument("--delete-detail-id", action="append")
    p.add_argument("--skip-repeat-rule", action="store_true", help="Disable duplicate checking; requires explicit business approval")
    p.add_argument("--skip-check-rule", action="store_true", help="Disable business validation; requires explicit business approval")
    add_write_guard(p)
    p.set_defaults(func=cmd_order_data)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
