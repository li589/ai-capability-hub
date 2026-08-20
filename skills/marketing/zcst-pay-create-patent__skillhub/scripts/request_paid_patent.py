#!/usr/bin/env python3
"""Request, pay for, and poll the paid patent merchant endpoint."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


MAX_RESPONSE_BYTES = 32 * 1024 * 1024
PATENT_TYPES = ("auto", "software", "mechanical", "process")


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="请求付费专利生成服务并轮询结果。")
    parser.add_argument("--service-url", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--patent-type", choices=PATENT_TYPES, default="auto")
    parser.add_argument("--email", default="")
    parser.add_argument("--out-trade-no")
    parser.add_argument("--payment-code")
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--request-timeout", type=int, default=90)
    parser.add_argument("--max-wait-seconds", type=int, default=1800)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    args.message = args.message.strip()
    args.email = args.email.strip()
    if not args.message:
        raise ValueError("message 不能为空")
    if len(args.message) > 500:
        raise ValueError(f"message 超过500字符，当前为{len(args.message)}字符")
    if args.email and (
        len(args.email) > 254
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", args.email)
    ):
        raise ValueError("email 格式不正确")
    if args.request_timeout < 1 or args.request_timeout > 300:
        raise ValueError("request-timeout 必须在1到300之间")
    if args.max_wait_seconds < 1 or args.max_wait_seconds > 1800:
        raise ValueError("max-wait-seconds 必须在1到1800之间")
    if args.out_trade_no and not args.out_trade_no.startswith("WX402_"):
        raise ValueError("out-trade-no 格式不正确")


def endpoint(service_url: str) -> str:
    value = service_url.rstrip("/") + "/api/skills/zcst-pay-create-patent/resource"
    parsed = urllib.parse.urlparse(value)
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and parsed.hostname not in local_hosts:
        raise ValueError("商户服务必须使用 HTTPS；仅本机联调允许 HTTP")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("service-url 格式不正确")
    return value


def request_once(args: argparse.Namespace) -> tuple[int, dict[str, str], dict[str, Any]]:
    payload = json.dumps({"input": {
        "message": args.message,
        "patent_type": args.patent_type,
        "email": args.email,
    }}, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if args.out_trade_no:
        headers["X-Out-Trade-No"] = args.out_trade_no
    if args.payment_code:
        headers["WeixinPay-Required"] = args.payment_code
    request = urllib.request.Request(
        endpoint(args.service_url), data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=args.request_timeout) as response:
            status = response.status
            response_headers = dict(response.headers.items())
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exception:
        status = exception.code
        response_headers = dict(exception.headers.items())
        raw = exception.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("商户服务响应超过大小限制")
    body = json.loads(raw.decode("utf-8"))
    if not isinstance(body, dict):
        raise ValueError("商户服务响应必须是 JSON 对象")
    return status, response_headers, body


def header(headers: dict[str, str], name: str) -> str | None:
    return next((value for key, value in headers.items() if key.lower() == name.lower()), None)


def save_success(args: argparse.Namespace, body: dict[str, Any]) -> int:
    if args.out_trade_no and body.get("out_trade_no") != args.out_trade_no:
        return output_failure("ORDER_NUMBER_MISMATCH", "成功响应的订单号与原订单不一致", args)
    if args.response_file is None:
        return output_failure("RESPONSE_FILE_REQUIRED", "成功响应必须保存到 response-file", args)
    args.response_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.response_file.with_suffix(args.response_file.suffix + ".tmp")
    temporary.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.response_file)
    print(json.dumps({
        "status": "succeeded",
        "code": "SUCCESS",
        "title": body.get("title"),
        "out_trade_no": body.get("out_trade_no"),
        "response_file": str(args.response_file.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0


def output_failure(code: str, message: str, args: argparse.Namespace, http_status: int | None = None) -> int:
    print(json.dumps({
        "status": "failed",
        "http_status": http_status,
        "code": code,
        "message": message,
        "out_trade_no": args.out_trade_no,
    }, ensure_ascii=False, indent=2))
    return 1


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        deadline = time.monotonic() + args.max_wait_seconds
        while True:
            status, headers, body = request_once(args)
            code = str(body.get("code") or "UNKNOWN")
            if status == 402 and code == "PAYMENT_REQUIRED":
                payment_code = header(headers, "WeixinPay-Required") or (
                    body.get("WeixinPay") or {}).get("WeixinPay-Required")
                out_trade_no = header(headers, "X-Out-Trade-No") or body.get("out_trade_no")
                if not payment_code or not out_trade_no:
                    return output_failure(
                        "INVALID_PAYMENT_REQUIRED_RESPONSE",
                        "402 响应缺少 payment_code 或 out_trade_no", args, status)
                print(json.dumps({
                    "status": "payment_required",
                    "http_status": status,
                    "payment_code": payment_code,
                    "out_trade_no": out_trade_no,
                    "amount": body.get("amount"),
                    "currency": body.get("currency"),
                    "description": body.get("description"),
                }, ensure_ascii=False, indent=2))
                return 0
            if status == 200 and code == "SUCCESS":
                return save_success(args, body)
            if status == 202 and code == "FULFILLMENT_IN_PROGRESS":
                retry_after_value = header(headers, "Retry-After") or body.get("retry_after")
                try:
                    retry_after = max(2, min(int(retry_after_value), 60))
                except (TypeError, ValueError):
                    retry_after = 10
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return output_failure(
                        "CLIENT_POLL_TIMEOUT",
                        "本次等待超过30分钟，请使用原订单继续查询", args, status)
                print(
                    f"专利任务处理中，{retry_after}秒后继续查询。",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(min(retry_after, remaining))
                continue
            pending_codes = {
                "NOT_PAID",
                "REFUNDING",
                "PAYMENT_STATUS_UNAVAILABLE",
                "DELIVERY_STATE_UNAVAILABLE",
                "FULFILLMENT_STATE_UNAVAILABLE",
            }
            print(json.dumps({
                "status": "pending" if code in pending_codes else "failed",
                "http_status": status,
                "code": code,
                "message": body.get("message", "服务返回未知状态"),
                "out_trade_no": body.get("out_trade_no") or args.out_trade_no,
            }, ensure_ascii=False, indent=2))
            return 0 if code in pending_codes else 1
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exception:
        return output_failure("NETWORK_OR_RESPONSE_ERROR", str(exception), args)


if __name__ == "__main__":
    raise SystemExit(main())
