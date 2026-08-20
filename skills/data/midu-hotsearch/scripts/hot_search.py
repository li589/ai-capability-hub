#!/usr/bin/env python3
"""CLI helper for the Midu Hot Search API skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests


API_URL = "https://api.midu.com/ability/skill/znjs/hot/search"
SKILL_CODE = "HOTSEARCH"
DEFAULT_TIMEOUT = 60
DEFAULT_USER_ID = "skill-hotsearch-agent"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query hot search data across 30+ platforms via Midu API."
    )
    parser.add_argument(
        "--keyword",
        required=True,
        help="Search keyword, max 30 characters.",
    )
    parser.add_argument(
        "--user_id",
        default="",
        help=(
            "User identifier (official website ID) sent as X-User-Id header "
            "and gwUserId body field. "
            "If omitted, reads from MIDU_USER_ID env var; "
            "if still unset, uses default value 'skill-hotsearch-agent'."
        ),
    )
    parser.add_argument(
        "--start_time",
        default="",
        help=(
            "Start time in yyyy-MM-dd or yyyy-MM-dd HH:mm:ss format. "
            "Defaults to today 00:00:00 if omitted."
        ),
    )
    parser.add_argument(
        "--end_time",
        default="",
        help=(
            "End time in yyyy-MM-dd or yyyy-MM-dd HH:mm:ss format. "
            "Defaults to today 23:59:59 if omitted."
        ),
    )
    parser.add_argument(
        "--rank_types",
        default="",
        help=(
            "Comma-separated rank type codes (e.g. '1,3,8'). "
            "Omit to query all platforms."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds. Default: {DEFAULT_TIMEOUT}.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON response.",
    )
    return parser.parse_args()


def get_api_key() -> str:
    """Read MIDU_APP_SECRET from environment. Raise if missing."""
    api_key = os.getenv("MIDU_APP_SECRET", "").strip()
    if not api_key:
        raise RuntimeError(
            "Error: MIDU_APP_SECRET must be set in environment. "
            "Please go to https://ai.mdata.net/ to get your MIDU_APP_SECRET."
        )
    return api_key


def get_user_id(user_id_arg: str) -> str:
    """Resolve user identifier: CLI arg > MIDU_USER_ID env > default."""
    user_id = user_id_arg.strip() if user_id_arg.strip() else os.getenv("MIDU_USER_ID", "").strip()
    return user_id if user_id else DEFAULT_USER_ID


def build_headers(api_key: str, user_id: str) -> dict[str, str]:
    """Build HTTP headers per Midu Skill specification.

    - Authorization: Bearer {apiKey}  — gateway authentication
    - X-Skill-Code: skill code in uppercase — for statistics
    - X-User-Id: user identifier — business-level user identity (primary)
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Skill-Code": SKILL_CODE,
        "X-User-Id": user_id,
    }


def build_payload(
    keyword: str,
    user_id: str,
    start_time: str,
    end_time: str,
    rank_types: str,
) -> dict[str, Any]:
    """Build the JSON request body.

    User identifier is sent via X-User-Id header (primary).
    gwUserId in body serves as fallback per API spec.
    """
    if not keyword.strip():
        raise ValueError("keyword must not be empty")

    payload: dict[str, Any] = {
        "gwUserId": user_id,
        "keyword": keyword.strip(),
    }

    if start_time:
        payload["startTime"] = start_time
    if end_time:
        payload["endTime"] = end_time
    if rank_types:
        try:
            payload["rankTypes"] = [int(t.strip()) for t in rank_types.split(",")]
        except ValueError:
            raise ValueError(
                f"Invalid rank_types format: '{rank_types}'. "
                "Expected comma-separated integers (e.g. '1,3,8')."
            )

    return payload


def post_json(
    url: str,
    payload: dict[str, Any],
    timeout: int,
    api_key: str,
    user_id: str,
) -> dict[str, Any]:
    """Send POST request and parse JSON response."""
    try:
        response = requests.post(
            url,
            json=payload,
            headers=build_headers(api_key, user_id),
            timeout=timeout,
        )
    except requests.Timeout:
        raise RuntimeError(
            f"Request timed out after {timeout}s. "
            "Try increasing --timeout or narrowing the query range."
        )
    except requests.ConnectionError:
        raise RuntimeError(
            "Network connection failed. Please check your network and try again."
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if response.status_code in (401, 403):
        raise RuntimeError(
            "Invalid MIDU_APP_SECRET, please visit "
            "https://ai.mdata.net/ to obtain a valid key."
        )
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

    try:
        parsed = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Response is not valid JSON: {response.text}"
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(f"Response JSON is not an object: {parsed!r}")

    return parsed


def format_stat_time(stat_time) -> str | int:
    """Convert millisecond timestamp to readable string if possible."""
    if stat_time is None:
        return ""
    try:
        ts = int(stat_time)
        if ts > 1e12:  # milliseconds
            ts = ts // 1000
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return stat_time


def enrich_output(
    response: dict[str, Any],
    keyword: str,
    start_time: str,
    end_time: str,
    rank_types: str,
) -> dict[str, Any]:
    """Add query metadata and format timestamps in the response.

    Output conforms to Midu Skill billing spec:
    - code: business status code ("0000" = success)
    - itemCount: list count, used as per-item billing field
    """
    # v2 API: data is a flat array, itemCount is at the response root
    raw_data = response.get("data")
    if isinstance(raw_data, list):
        data_list = raw_data
    else:
        data_list = []

    item_count = response.get("itemCount", len(data_list))

    # Determine code: API returns status (1=success, 0=failure), map to code spec
    api_status = response.get("status", 0)
    if api_status == 1:
        code = "0000"
    else:
        code = "1001"

    # Enrich each item with formatted timestamps
    for item in data_list:
        if "statTime" in item and item["statTime"] is not None:
            item["statTimeFormatted"] = format_stat_time(item["statTime"])
        if "inTime" in item and item["inTime"] is not None:
            item["inTimeFormatted"] = format_stat_time(item["inTime"])

    output: dict[str, Any] = {
        "code": code,
        "itemCount": item_count,
        "data": data_list,
        "query_info": {
            "keyword": keyword,
            "startTime": start_time or "today",
            "endTime": end_time or "today",
            "rankTypes": rank_types or "all",
        },
    }

    # Include message for error responses
    if code != "0000":
        output["message"] = response.get("message", "Unknown error")

    return output


def print_output(output: dict[str, Any], pretty: bool) -> int:
    """Print JSON output and return exit code."""
    if pretty:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(output, ensure_ascii=False))
    return 0


def print_error(message: str, pretty: bool) -> int:
    """Print error JSON and return exit code 1."""
    payload = {"code": "9999", "message": message, "itemCount": 0}
    if pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 1


def main() -> int:
    args = parse_args()

    try:
        api_key = get_api_key()
        user_id = get_user_id(args.user_id)
        payload = build_payload(
            args.keyword,
            user_id,
            args.start_time,
            args.end_time,
            args.rank_types,
        )
        response = post_json(API_URL, payload, args.timeout, api_key, user_id)
        output = enrich_output(
            response,
            args.keyword,
            args.start_time,
            args.end_time,
            args.rank_types,
        )
        return print_output(output, args.pretty)
    except Exception as exc:
        return print_error(str(exc), args.pretty)


if __name__ == "__main__":
    raise SystemExit(main())
