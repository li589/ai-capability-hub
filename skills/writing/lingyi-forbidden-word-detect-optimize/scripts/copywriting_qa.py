#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""违禁词检测+优化 —— 联网主脚本（调后端异步任务）

POST /copywriting-qa/tasks → GET 轮询 → 交付 Markdown。

任务状态：pending / running / completed / failed
- completed：报告就绪；首次 GET completed 时服务端结算扣点（只扣一次）
- failed：失败，见 errors

对外响应 data（精简）：task_id / status / markdown / errors / total_points
- 不再返回 skill_kind / usage_tokens / result_read_count / billing 对象
- total_points 为本次实扣点数字符串；兼容旧 billing.total_points

兼容：succeeded≈完成，billing_failed≈失败

退出码：0 成功 / 2 无Key / 3 参数 / 4 余额 / 8 鉴权 / 10 4xx / 11 5xx / 12 失败 / 13 进行中
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://claw.lingyishuke.com/services"
TASKS_PATH = "/api/v1/content-quality/copywriting-qa/tasks"
CHANNELS = {"xhs", "dy", "mp", "channels", "other"}

DEFAULT_TIMEOUT = 90
HTTP_TIMEOUT = 60
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 60
FALLBACK_PLAN_POINTS = 26

# 成功终态（含旧 succeeded 兼容）；失败终态（含旧 billing_failed 兼容）
STATUS_OK = frozenset({"completed", "succeeded"})
STATUS_FAILED = frozenset({"failed", "billing_failed"})

E_OK, E_NO_KEY, E_PARAM, E_BALANCE, E_AUTH = 0, 2, 3, 4, 8
E_4XX, E_5XX, E_FAILED, E_PENDING = 10, 11, 12, 13

POINTS_PREFIX = "COPY_QA_POINTS_USED="
PLAN_PREFIX = "COPY_QA_PLAN_POINTS="
REPORT_START = "=== COPY_QA_REPORT_START ==="
REPORT_END = "=== COPY_QA_REPORT_END ==="
FILE_PREFIX = "COPY_QA_REPORT_FILE="
TASK_PREFIX = "COPY_QA_TASK_ID="

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


def log(msg):
    print("[copywriting_qa] %s" % msg, file=sys.stderr, flush=True)


def fail(code, msg):
    log("❌ " + msg)
    sys.exit(code)


def get_api_key():
    skill_dir = Path(__file__).resolve().parent.parent
    cfg = skill_dir / "config.json"
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text("utf-8"))
            if isinstance(data, dict) and data.get("LY_API_KEY"):
                return str(data["LY_API_KEY"]).strip()
        except (json.JSONDecodeError, OSError):
            pass
    env = os.environ.get("LY_API_KEY")
    return env.strip() if env else ""


def auth_headers(api_key, idempotency_key=None):
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    return headers


def parse_json(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def read_text(arg):
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg).expanduser()
    if p.is_file():
        return p.read_text("utf-8")
    return arg


def http_request(url, method, headers, body, timeout):
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            return status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
        except Exception:
            raw = b""
        return e.code, raw.decode("utf-8", "ignore")


def http_request_with_retries(url, method, headers, body, timeout, label):
    last_err = None
    for attempt in range(1, HTTP_RETRY_TIMES + 1):
        try:
            status, text = http_request(url, method, headers, body, timeout)
            if status >= 500 and attempt < HTTP_RETRY_TIMES:
                wait = min(2 ** (attempt - 1), MAX_BACKOFF)
                log("%s %s，%ds 后重试" % (label, status, wait))
                time.sleep(wait)
                continue
            return status, text
        except Exception as e:
            last_err = e
            if attempt >= HTTP_RETRY_TIMES:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s 异常：%s，%ds 后重试" % (label, e, wait))
            time.sleep(wait)
    raise last_err


def extract_total_points(payload):
    """从 GET 响应取实扣：优先 data.total_points，兼容旧版 billing.total_points。"""
    if not isinstance(payload, dict):
        return None
    # 新契约：扁平 total_points
    for key in ("total_points", "points", "deducted_points"):
        val = payload.get(key)
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    # 兼容旧契约：billing.total_points
    billing = payload.get("billing")
    if isinstance(billing, dict):
        for key in ("total_points", "points", "deducted_points"):
            val = billing.get(key)
            if val is not None and str(val).strip() != "":
                return str(val).strip()
    return None


def format_task_error(data):
    """优先读 errors[{code,message}]，兼容旧 failure_code/failure_message。"""
    if not isinstance(data, dict):
        return ""
    errors = data.get("errors")
    if isinstance(errors, list) and errors:
        parts = []
        for item in errors[:5]:
            if isinstance(item, dict):
                code = str(item.get("code") or "").strip()
                msg = str(item.get("message") or "").strip()
                if code and msg:
                    parts.append("%s: %s" % (code, msg))
                elif msg:
                    parts.append(msg)
                elif code:
                    parts.append(code)
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "; ".join(parts)
    code = str(data.get("failure_code") or "").strip()
    msg = str(data.get("failure_message") or "").strip()
    if code or msg:
        return ("%s %s" % (code, msg)).strip()
    return str(data.get("status") or "failed")


def unwrap_data(body):
    if not isinstance(body, dict):
        return {}
    data = body.get("data")
    return data if isinstance(data, dict) else body


def handle_http_error(status, text):
    body = parse_json(text) or {}
    msg = str(body.get("message") or body.get("detail") or text or status)[:300]
    if status in (401, 403):
        fail(E_AUTH, "鉴权失败：%s" % msg)
    if status == 402:
        fail(E_BALANCE, "余额不足：%s" % msg)
    if 400 <= status < 500:
        fail(E_4XX, "请求错误 %s：%s" % (status, msg))
    fail(E_5XX, "服务错误 %s：%s" % (status, msg))


def create_task(api_key, payload, idempotency_key=None):
    url = BASE_URL.rstrip("/") + TASKS_PATH
    status, text = http_request_with_retries(
        url, "POST", auth_headers(api_key, idempotency_key),
        json.dumps(payload, ensure_ascii=False), HTTP_TIMEOUT, "创建任务",
    )
    if status >= 400:
        handle_http_error(status, text)
    data = unwrap_data(parse_json(text) or {})
    task_id = str(data.get("task_id") or "").strip()
    if not task_id:
        fail(E_5XX, "创建成功但无 task_id")
    return task_id, data


def get_task(api_key, task_id):
    """GET 任务。status=completed 时服务端会结算扣点（只扣一次）。"""
    url = BASE_URL.rstrip("/") + TASKS_PATH + "/" + task_id
    status, text = http_request_with_retries(
        url, "GET", auth_headers(api_key), None, HTTP_TIMEOUT, "查询任务",
    )
    if status >= 400:
        handle_http_error(status, text)
    return unwrap_data(parse_json(text) or {})


def retry_task(api_key, task_id):
    url = BASE_URL.rstrip("/") + TASKS_PATH + "/" + task_id + "/retry"
    status, text = http_request_with_retries(
        url, "POST", auth_headers(api_key), None, HTTP_TIMEOUT, "重试任务",
    )
    if status >= 400:
        handle_http_error(status, text)
    return unwrap_data(parse_json(text) or {})


def poll_until_done(api_key, task_id, timeout, poll_interval, only_once=False):
    deadline = time.time() + timeout
    while True:
        data = get_task(api_key, task_id)
        st = str(data.get("status") or "")
        if st in STATUS_OK:
            return data
        if st in STATUS_FAILED:
            fail(E_FAILED, "任务失败：%s" % format_task_error(data))
        if only_once or time.time() >= deadline:
            fail(E_PENDING, "任务进行中 status=%s" % (st or "unknown"))
        time.sleep(poll_interval)


def deliver(data, out_path):
    markdown = str(data.get("markdown") or "").strip()
    if not markdown:
        fail(E_FAILED, "任务完成但 markdown 为空")
    out = Path(out_path).expanduser()
    out.write_text(markdown + "\n", encoding="utf-8")
    points = extract_total_points(data)
    log("deliver status=%s total_points=%s" % (data.get("status"), points))
    print(POINTS_PREFIX + (points if points else ""))
    print(PLAN_PREFIX + str(FALLBACK_PLAN_POINTS))
    print(FILE_PREFIX + str(out.resolve()))
    print(TASK_PREFIX + str(data.get("task_id") or ""))
    print(REPORT_START)
    print(markdown)
    print(REPORT_END)


def main():
    parser = argparse.ArgumentParser(description="违禁词检测+优化（后端异步任务）")
    parser.add_argument("--text", help="文案或文件路径或 -")
    parser.add_argument(
        "--channel",
        default=None,
        choices=sorted(CHANNELS),
        help="必填：xhs/dy/mp/channels/other（缺失须向用户确认后传入）",
    )
    parser.add_argument("--industry", default="")
    parser.add_argument("--is-commercial", action="store_true")
    parser.add_argument("--account-qualification", default="")
    parser.add_argument("--origin", default="01workbuddy")
    parser.add_argument("--origin-method", default="skill")
    parser.add_argument("--out", default="")
    parser.add_argument("--only-create", action="store_true")
    parser.add_argument("--poll-task", default="")
    parser.add_argument("--retry-task", default="")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=int, default=PROGRESS_POLL_INTERVAL)
    parser.add_argument(
        "--idempotency-key",
        default="",
        help="已废弃：服务端忽略；长任务以 task_id 为准",
    )
    parser.add_argument("--insecure", action="store_true")
    args = parser.parse_args()

    if args.insecure:
        global SSL_CONTEXT
        SSL_CONTEXT = ssl.create_default_context()
        SSL_CONTEXT.check_hostname = False
        SSL_CONTEXT.verify_mode = ssl.CERT_NONE

    # 创建任务：先校验业务参数，再查 Key（缺渠道时先让 agent 问用户）
    if not args.retry_task and not args.poll_task:
        if not args.text:
            fail(E_PARAM, "请提供 --text")
        text = read_text(args.text).strip()
        if not text:
            fail(E_PARAM, "文案为空")
        channel = (args.channel or "").strip()
        if not channel:
            fail(
                E_PARAM,
                "请提供 --channel（xhs/dy/mp/channels/other）",
            )
        if channel not in CHANNELS:
            fail(E_PARAM, "channel 无效，可选：xhs/dy/mp/channels/other")
    else:
        text = ""
        channel = ""

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "缺少 LY_API_KEY（config.json 或环境变量）")

    if args.retry_task:
        data = retry_task(api_key, args.retry_task.strip())
        task_id = str(data.get("task_id") or args.retry_task).strip()
        data = poll_until_done(api_key, task_id, args.timeout, args.poll_interval)
        out = args.out or ("违禁词检测+优化-%s.md" % task_id[:8])
        deliver(data, out)
        sys.exit(E_OK)

    if args.poll_task:
        task_id = args.poll_task.strip()
        data = poll_until_done(
            api_key, task_id, args.timeout, args.poll_interval, only_once=True
        )
        out = args.out or ("违禁词检测+优化-%s.md" % task_id[:8])
        deliver(data, out)
        sys.exit(E_OK)

    payload = {
        "text": text,
        "channel": channel,
        "industry": (args.industry or "").strip(),
        "is_commercial": bool(args.is_commercial),
        "account_qualification": (args.account_qualification or "").strip(),
        "origin": (args.origin or "").strip() or "01workbuddy",
        "origin_method": (args.origin_method or "").strip() or "skill",
    }
    idem = (args.idempotency_key or "").strip() or None
    task_id, data = create_task(api_key, payload, idem)
    log("task_id=%s status=%s" % (task_id, data.get("status")))

    if args.only_create:
        print(TASK_PREFIX + task_id)
        print(PLAN_PREFIX + str(FALLBACK_PLAN_POINTS))
        sys.exit(E_OK)

    data = poll_until_done(api_key, task_id, args.timeout, args.poll_interval)
    out = args.out or ("违禁词检测+优化-%s.md" % task_id[:8])
    deliver(data, out)
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
