"""Cursor pagination for Jiandaoyun form data."""

from .errors import JiandaoyunError


def list_all_data(client, schema, params):
    all_records = []
    cursor = params.get("data_id", "")
    max_records = params.get("max_records", 0)
    pages = 0

    while True:
        pages += 1
        page_params = dict(params)
        page_params["limit"] = 100
        page_params["data_id"] = cursor
        result = client.call(schema, page_params)
        batch = _extract_data(result)
        all_records.extend(batch)

        if max_records and len(all_records) >= max_records:
            all_records = all_records[:max_records]
            break
        if len(batch) < 100:
            break
        next_cursor = batch[-1].get("_id") if isinstance(batch[-1], dict) else None
        if not next_cursor or next_cursor == cursor:
            raise JiandaoyunError(
                "pagination_error",
                "分页游标没有推进，已停止以避免无限循环。",
            )
        cursor = next_cursor

    return {
        "data": all_records,
        "total_returned": len(all_records),
        "pages_fetched": pages,
        "truncated": bool(max_records and len(all_records) >= max_records),
    }


def _extract_data(result):
    if not isinstance(result, dict):
        raise JiandaoyunError("invalid_response", "分页响应不是 JSON 对象。")
    value = result.get("data", [])
    if isinstance(value, dict) and isinstance(value.get("data"), list):
        value = value["data"]
    if not isinstance(value, list):
        raise JiandaoyunError("invalid_response", "分页响应中没有数据数组。")
    return value
