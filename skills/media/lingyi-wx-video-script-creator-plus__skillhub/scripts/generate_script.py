#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频号爆款文案生成（进阶版）【零一数科·出品】 —— 联网主脚本

远端付费 API 生成微信视频号脚本。流程：
  读 key → (无 --task-id) GET config 校验枚举/必填/范围 →
  组装 body → POST 创建 → 轮询 GET 看 data.status → 完整响应写盘 →
  调 render_report.py 输出后端 markdown 为 MD。

退出码见 SKILL.md「退出码处理」。纯标准库。
"""

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------- 常量
BASE_URL = "https://claw.lingyishuke.com/services"
API_PREFIX = "/api/v1/social-analytics/collector"
PATH_CONFIG = "/wx-video-script-creations/config"
PATH_CREATE = "/wx-video-script-creations"
PATH_STATUS = "/wx-video-script-creations/{task_id}"

# 需按 config options 校验的枚举字段
ENUM_FIELDS = ("mode", "direction", "platform", "industry", "purpose",
               "script_type", "depth")

# 实际扣点候选字段名（后端字段未固定，尽量兼容；命中即透出给 agent）。
POINTS_KEYS = (
    "points_used", "cost_points", "points_cost", "credits_used",
    "credit_cost", "deducted_points", "charge_points", "used_points",
    "consume_points", "points",
)

COMPLETED_STATUSES = {"COMPLETED", "COMPLETE", "SUCCESS", "SUCCEEDED", "DONE"}
FAILED_STATUSES = {"FAILED", "ERROR", "CANCELLED", "CANCELED"}
RUNNING_STATUSES = {"PENDING", "QUEUED", "RUNNING", "PROCESSING"}

DEFAULT_POLL_INTERVAL = 5
DEFAULT_POLL_TIMEOUT = 600
HTTP_RETRY_TIMES = 3
POLL_RETRY_TIMES = 3
MAX_BACKOFF = 16

# 退出码
E_OK = 0
E_NO_KEY = 2
E_PARAM = 3
E_BALANCE = 4
E_TIMEOUT = 5
E_TASK_FAIL = 6
E_RANGE = 7
E_AUTH = 8
E_FORBIDDEN = 9
E_4XX = 10
E_5XX = 11
E_CONFIG_FAIL = 21
E_RENDER = 22

RESULT_TOKENS = ("===TASK_ID===", "===RESPONSE_PATH===", "===MD_PATH===", "===OVERVIEW_MD===", "===POINTS_USED===")

# --------------------------------------------------------------------------- 工具
def log(msg):
    print("[generate_script] %s" % msg, file=sys.stderr, flush=True)


def fail(code, msg):
    log("❌ " + msg)
    sys.exit(code)


def get_api_key():
    """读技能目录 config.json 的 LY_API_KEY，回退环境变量。"""
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
    return env.strip() if env else None


def ssl_context(insecure):
    if not insecure and not os.environ.get("LY_SKIP_SSL_VERIFY"):
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def http_request(method, url, headers=None, body=None, timeout=30, insecure=False):
    """发起一次 HTTP 请求，返回 (status, text)。URLError 上抛由调用方决定重试。"""
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    ctx = ssl_context(insecure)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            return status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def auth_headers(api_key, ctype=False):
    h = {"Authorization": api_key, "X-Appbuilder-From": "openclaw"}
    if ctype:
        h["Content-Type"] = "application/json; charset=utf-8"
    h["Accept"] = "application/json"
    return h


def parse_json(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def first_present(d, keys):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return None


def _coerce_points(v):
    """把候选值规整成非负数，无效返回 None。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)) and v >= 0:
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def extract_points_used(data):
    """从响应 data 里尽力解析本次实际扣点，找不到返回 None。

    后端扣点字段名未固定，按 POINTS_KEYS 在顶层及常见子对象（usage/billing/
    cost/charge/result）里查找。agent 收到 None 时应回退为「以账户实际扣点为准」。
    """
    if not isinstance(data, dict):
        return None
    for k in POINTS_KEYS:
        v = _coerce_points(data.get(k))
        if v is not None:
            return v
    for sub in ("usage", "billing", "cost", "charge", "result"):
        sub_d = data.get(sub)
        if isinstance(sub_d, dict):
            for k in POINTS_KEYS:
                v = _coerce_points(sub_d.get(k))
                if v is not None:
                    return v
    return None


def emit(*pairs):
    """成对输出标记块：name / value。"""
    for name, value in pairs:
        print(name)
        print(value)
    sys.stdout.flush()


# --------------------------------------------------------------------------- config
def fetch_config(base_url, api_key, insecure):
    """GET config，返回 {field: {value: label}} 用于枚举校验与中英对照展示。失败 raise。

    保留每个 option 的中文 label（缺失时回退为 value 本身），供 agent 向用户
    展示中文选项；传后端仍用英文 value。
    """
    url = base_url.rstrip("/") + API_PREFIX + PATH_CONFIG
    for attempt in range(1, HTTP_RETRY_TIMES + 1):
        try:
            status, text = http_request("GET", url, headers=auth_headers(api_key),
                                        timeout=30, insecure=insecure)
        except urllib.error.URLError as e:
            if attempt >= HTTP_RETRY_TIMES:
                raise RuntimeError("config 网络错误：%s" % e)
            time.sleep(min(2 ** (attempt - 1), MAX_BACKOFF))
            continue
        if status == 401:
            fail(E_AUTH, "鉴权失败（HTTP 401）：API Key 无效或已过期，请更新 config.json 的 LY_API_KEY。")
        if status >= 500:
            if attempt >= HTTP_RETRY_TIMES:
                raise RuntimeError("config 服务端错误 HTTP %d" % status)
            time.sleep(min(2 ** (attempt - 1), MAX_BACKOFF))
            continue
        payload = parse_json(text) or {}
        if status != 200 or payload.get("result") != "success":
            raise RuntimeError("config 返回异常：HTTP %s message=%s" % (status, payload.get("message")))
        opts = {}
        for item in payload.get("data") or []:
            field = item.get("field")
            if field and item.get("options"):
                m = {}
                for o in item.get("options") or []:
                    v = o.get("value")
                    if not v:
                        continue
                    m[v] = o.get("label") or v
                if m:
                    opts[field] = m
        return opts
    raise RuntimeError("config 拉取重试用尽")


def _format_options(field, allowed):
    """把 {value: label} 渲染成「中文 label（英文 value）」可读串，用于错误提示。"""
    if not allowed:
        return ""
    parts = []
    for v, label in allowed.items():
        if label and label != v:
            parts.append("%s（%s）" % (label, v))
        else:
            parts.append(v)
    return " / ".join(parts)


def emit_config_options(config_opts):
    """把 config 中英对照输出到 stdout 标记块 + stderr 人类可读，供 agent 用中文问用户。"""
    if not config_opts:
        return
    compact = {}
    for field in ENUM_FIELDS:
        m = config_opts.get(field)
        if not m:
            continue
        compact[field] = [{"label": label, "value": v} for v, label in m.items()]
    print("===CONFIG_OPTIONS===")
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    sys.stdout.flush()
    log("config 可选项（向用户展示用中文 label，传后端用英文 value）：")
    for field in ENUM_FIELDS:
        m = config_opts.get(field)
        if m:
            log("  %s: %s" % (field, _format_options(field, m)))


# --------------------------------------------------------------------------- 校验 + body
def parse_json_arg(s, field):
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        fail(E_PARAM, "--%s 不是合法 JSON：%s（原文：%s）" % (field, e, s[:120]))


def validate_and_build(args, config_opts, base_url, api_key, insecure):
    """校验参数并组装创建任务 body。失败 fail(E_PARAM/E_RANGE)。"""
    # 枚举校验
    enum_map = {
        "mode": args.mode, "direction": args.direction, "platform": args.platform,
        "industry": args.industry, "purpose": args.purpose,
        "script_type": args.script_type, "depth": args.depth,
    }
    for field, val in enum_map.items():
        if val is None:
            continue
        if field in ("industry", "purpose"):
            continue  # 多值/兼容字段，单独校验
        allowed = config_opts.get(field) if config_opts else None
        if allowed and val not in allowed:
            fail(E_PARAM, "%s 值 `%s` 不在 config 可选值内，可选：%s"
                 % (field, val, _format_options(field, allowed)))
    # mode / direction / platform 必填
    if not args.mode:
        fail(E_PARAM, "mode 必填（creation / recreation）")
    if not args.direction:
        fail(E_PARAM, "direction 必填")
    if not args.platform:
        fail(E_PARAM, "platform 必填")
    # industry / purpose 至少一个
    if not args.industry and not args.industries:
        fail(E_PARAM, "industry / industries 至少提供一个")
    if not args.purpose and not args.purposes:
        fail(E_PARAM, "purpose / campaign_types 至少提供一个")

    body = {
        "mode": args.mode,
        "direction": args.direction,
        "platform": args.platform,
    }

    # 行业：单值→industry，多值→industries
    all_industries = []
    if args.industry:
        all_industries.append(args.industry)
    if args.industries:
        for part in args.industries:
            all_industries.extend([s.strip() for s in part.split(",") if s.strip()])
    if config_opts and config_opts.get("industry"):
        for ind in all_industries:
            if ind not in config_opts["industry"]:
                fail(E_PARAM, "industry 值 `%s` 不在 config 可选值内，可选：%s"
                     % (ind, _format_options("industry", config_opts["industry"])))
    if len(all_industries) == 1:
        body["industry"] = all_industries[0]
    elif len(all_industries) > 1:
        body["industries"] = all_industries

    # 目的：单值→purpose，多值→campaign_types
    all_purposes = []
    if args.purpose:
        all_purposes.append(args.purpose)
    if args.purposes:
        for part in args.purposes:
            all_purposes.extend([s.strip() for s in part.split(",") if s.strip()])
    if config_opts and config_opts.get("purpose"):
        for p in all_purposes:
            if p not in config_opts["purpose"]:
                fail(E_PARAM, "purpose 值 `%s` 不在 config 可选值内，可选：%s"
                     % (p, _format_options("purpose", config_opts["purpose"])))
    if len(all_purposes) == 1:
        body["purpose"] = all_purposes[0]
    elif len(all_purposes) > 1:
        body["campaign_types"] = all_purposes

    if args.script_type:
        body["script_type"] = args.script_type
    if args.depth:
        body["depth"] = args.depth

    # product
    product = parse_json_arg(args.product, "product")
    if args.mode == "creation" and args.direction == "influencer_commerce":
        if not isinstance(product, dict) or not any(
                (isinstance(v, str) and v.strip()) or v for v in product.values()):
            fail(E_PARAM, "mode=creation 且 direction=influencer_commerce 时，product 必填且非空对象"
                 "（name/price/selling_points/target_users 等）")
        body["product"] = product
    elif product is not None:
        body["product"] = product

    # account_brief
    ab = parse_json_arg(args.account_brief, "account-brief")
    if ab is not None:
        body["account_brief"] = ab

    # count / duration 范围先校验，避免参数明显非法时仍发起创建。
    if args.count is not None:
        if not (1 <= args.count <= 3):
            fail(E_RANGE, "count 必须在 1-3 之间，当前 %s" % args.count)
        body["count"] = args.count
    if args.target_duration_sec is not None:
        if not (1 <= args.target_duration_sec <= 1800):
            fail(E_RANGE, "target-duration-sec 必须在 1-1800 之间，当前 %s" % args.target_duration_sec)
        body["target_duration_sec"] = args.target_duration_sec

    # 源视频（二创必填）：只支持微信视频号分享链接。
    if args.mode == "recreation":
        sv = parse_json_arg(args.source_video, "source-video") or {}
        if not isinstance(sv, dict):
            fail(E_PARAM, "--source-video 须为 JSON 对象")
        share_url = args.share_url or sv.get("share_url") or sv.get("shared_url") or sv.get("url")
        if not share_url:
            fail(E_PARAM, "mode=recreation 时，源视频必填：微信视频号分享链接用 --share-url。")
        sv = {"shared_url": share_url}
        body["share_url"] = share_url
        body["source_video"] = sv

    if args.additional_requirements:
        body["additional_requirements"] = args.additional_requirements

    body["origin"] = "workbuddy"
    body["origin_method"] = "skill"
    return body


# --------------------------------------------------------------------------- 创建
def create_task(base_url, api_key, body, insecure):
    url = base_url.rstrip("/") + API_PREFIX + PATH_CREATE
    body_text = json.dumps(body, ensure_ascii=False)
    log("创建脚本生成任务：mode=%s direction=%s count=%s"
        % (body.get("mode"), body.get("direction"), body.get("count", 1)))
    status, text = None, ""
    for attempt in range(1, HTTP_RETRY_TIMES + 1):
        try:
            status, text = http_request("POST", url, headers=auth_headers(api_key, True),
                                        body=body_text, timeout=60, insecure=insecure)
        except urllib.error.URLError as e:
            if attempt >= HTTP_RETRY_TIMES:
                fail(E_5XX, "创建任务网络错误：%s（请检查网络与服务可达性：%s）" % (e, base_url))
            time.sleep(min(2 ** (attempt - 1), MAX_BACKOFF))
            continue
        if status >= 500:
            if attempt >= HTTP_RETRY_TIMES:
                fail(E_5XX, "创建任务服务端错误 HTTP %d，请稍后重试。" % status)
            time.sleep(min(2 ** (attempt - 1), MAX_BACKOFF))
            continue
        break

    if status == 401:
        fail(E_AUTH, "鉴权失败（HTTP 401）：API Key 无效或已过期，请更新 config.json 的 LY_API_KEY。")
    payload = parse_json(text) or {}
    msg = payload.get("message") or ""
    data = payload.get("data") or {}
    if status == 402 or "余额" in msg or data.get("recharge_url"):
        tip = "余额不足，无法创建任务。"
        if data.get("recharge_url"):
            tip += " 请前往充值：%s" % data["recharge_url"]
        fail(E_BALANCE, tip)
    if status == 400:
        fail(E_PARAM, "参数不合法（HTTP 400）：%s" % msg)
    if status == 422:
        fail(E_RANGE, "请求体验证失败（HTTP 422）：%s" % msg)
    if 400 <= status < 500 and status not in (400, 422):
        fail(E_4XX, "创建失败（HTTP %s）：%s" % (status, msg))
    if status not in (200, 201) or payload.get("result") != "success":
        fail(E_4XX, "创建失败：HTTP %s result=%s message=%s" % (status, payload.get("result"), msg))
    task_id = data.get("script_task_id") or data.get("content_ops_task_id")
    if not task_id:
        fail(E_4XX, "创建成功但缺少 script_task_id：%s" % text[:300])
    log("任务已创建：script_task_id=%s" % task_id)
    return task_id


# --------------------------------------------------------------------------- 轮询
class RetryableError(Exception):
    pass


def poll_once(base_url, api_key, task_id, insecure):
    url = base_url.rstrip("/") + API_PREFIX + PATH_STATUS.format(
        task_id=urllib.parse.quote(str(task_id), safe=""))
    status, text = http_request("GET", url, headers=auth_headers(api_key), timeout=30, insecure=insecure)
    if status == 401:
        fail(E_AUTH, "鉴权失败（HTTP 401）：API Key 无效或已过期。")
    if status == 403:
        fail(E_FORBIDDEN, "无权访问该任务（403）：可能 key 与 task 不匹配，请重新创建任务。")
    if status == 404:
        fail(E_FORBIDDEN, "任务不存在（404）：task_id=%s，请重新创建。" % task_id)
    if status == 429 or status >= 500:
        raise RetryableError("HTTP %d" % status)
    payload = parse_json(text)
    if payload is None:
        raise RetryableError("返回非 JSON")
    if status != 200 or payload.get("result") != "success":
        raise RetryableError("HTTP %s message=%s" % (status, payload.get("message")))
    return payload


def poll_loop(base_url, api_key, task_id, max_wait, interval, insecure, resp_out):
    deadline = time.monotonic() + max_wait
    backoff = interval
    last_sig = None
    while True:
        response, data, err = None, None, None
        for _ in range(POLL_RETRY_TIMES):
            try:
                response = poll_once(base_url, api_key, task_id, insecure)
                data = response.get("data") or {}
                err = None
                break
            except (RetryableError, urllib.error.URLError) as e:
                err = e
                wait = min(backoff, MAX_BACKOFF)
                log("轮询可重试错误：%s，%ds 后重试" % (e, wait))
                time.sleep(wait)
                backoff = min(backoff * 2, MAX_BACKOFF)
        if err is not None:
            fail(E_5XX, "轮询连续 %d 次失败：%s" % (POLL_RETRY_TIMES, err))
        backoff = interval

        status = str(data.get("status") or "UNKNOWN").upper()
        stage = data.get("current_stage", "")
        pmsg = data.get("progress_message", "")
        sig = (status, stage, pmsg)
        if sig != last_sig:
            log("[%s / stage=%s] %s" % (status, stage or "-", pmsg))
            last_sig = sig

        # 每轮落最新响应，防超时丢失
        if resp_out:
            try:
                _write_response(resp_out, response)
            except OSError:
                pass
            print("===TASK_ID===\n%s" % task_id, file=sys.stderr, flush=True)

        if status in COMPLETED_STATUSES:
            return response
        if status in FAILED_STATUSES:
            err_msg = data.get("error_message") or "脚本生成失败"
            log("任务失败：%s" % err_msg)
            raw = (data.get("result") or {}).get("raw") or {}
            for e in raw.get("errors") or []:
                log("  error: %s" % e)
            fail(E_TASK_FAIL, "任务失败：%s" % err_msg)
        if time.monotonic() > deadline:
            fail(E_TIMEOUT, "轮询超时（已等 %ds）。任务仍在进行，task_id=%s。"
                 "请稍后用 --task-id %s 续传，不要重新创建。" % (max_wait, task_id, task_id))
        time.sleep(interval)


def _write_response(path, response):
    """把轮询接口的完整 JSON 响应写盘（存档 / 续传 / 排查用）。"""
    Path(path).write_text(json.dumps(response, ensure_ascii=False, indent=2), "utf-8")


# --------------------------------------------------------------------------- 输出 MD
def render_report(resp_path, md_out):
    """调 render_report.py 从响应 JSON 解析出 markdown 字段写成 MD。失败返回 False，不致命。"""
    here = Path(__file__).resolve().parent
    renderer = here / "render_report.py"
    if not renderer.is_file():
        log("⚠️ render_report.py 不存在，跳过输出 MD：%s" % renderer)
        return False
    cmd = [sys.executable, str(renderer), "--in", resp_path, "--out", md_out]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        log("⚠️ 输出 MD 异常：%s" % e)
        return False
    if r.returncode != 0:
        log("⚠️ 输出 MD 失败（exit %s）：%s" % (r.returncode, (r.stderr or "").strip()[-500:]))
        return False
    return True


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="视频号爆款文案生成（进阶版）—— 远端 API 生成脚本")
    ap.add_argument("--mode", choices=["creation", "recreation"], help="创作模式")
    ap.add_argument("--direction", help="创作方向 value")
    ap.add_argument("--platform", help="发布平台 value")
    ap.add_argument("--industry", help="行业 value（单值）")
    ap.add_argument("--industries", action="append", help="行业 value（可多次或逗号分隔）")
    ap.add_argument("--purpose", help="营销目的 value（单值）")
    ap.add_argument("--purposes", action="append", help="营销目的 value（可多次或逗号分隔）")
    ap.add_argument("--script-type", help="脚本类型 value（可选）")
    ap.add_argument("--product", help="商品信息 JSON 字符串")
    ap.add_argument("--account-brief", help="账号/人设信息 JSON 字符串")
    ap.add_argument("--source-video", help="源视频 JSON 字符串（二创）")
    ap.add_argument("--share-url", help="二创源视频分享链接（微信视频号）")
    ap.add_argument("--count", type=int, help="生成条数 1-3")
    ap.add_argument("--target-duration-sec", type=int, help="目标时长 1-1800 秒")
    ap.add_argument("--depth", choices=["fast", "deep"], help="创作深度")
    ap.add_argument("--additional-requirements", help="额外要求文本")
    ap.add_argument("--task-id", help="已有 script_task_id，跳过创建直接轮询（续传）")
    ap.add_argument("--skip-config", action="store_true", help="跳过 config 枚举预校验")
    ap.add_argument("--show-options", action="store_true",
                    help="只拉 config 并输出中英对照可选项（===CONFIG_OPTIONS=== 标记块）后退出，不创建任务。供 agent 先用中文向用户收集选择。")
    ap.add_argument("--response-out", default=None, help="接口响应 JSON 输出路径（存档/续传用）")
    ap.add_argument("--md-out", default=None, help="MD 报告输出路径")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    ap.add_argument("--poll-timeout", type=int, default=DEFAULT_POLL_TIMEOUT)
    args = ap.parse_args()

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "未取到 API Key：技能目录下 config.json 不存在或无 LY_API_KEY 字段。\n"
              "请前往 https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy 获取，\n"
              "写入 config.json（如 {\"LY_API_KEY\": \"你的密钥\"}）或设环境变量 LY_API_KEY 后重试。")

    base_url = os.environ.get("LY_BASE_URL", BASE_URL)
    insecure = args.insecure or bool(os.environ.get("LY_SKIP_SSL_VERIFY"))

    resp_out = args.response_out or "/tmp/wxscript_response.json"
    md_out = args.md_out

    # --show-options：只拉 config、输出中英对照、退出。供 agent 先用中文问用户。
    if args.show_options:
        try:
            config_opts = fetch_config(base_url, api_key, insecure)
        except RuntimeError as e:
            fail(E_CONFIG_FAIL, "拉取 config 失败：%s" % e)
        emit_config_options(config_opts)
        sys.exit(E_OK)

    if args.task_id:
        task_id = args.task_id
        log("恢复已有任务：task_id=%s" % task_id)
    else:
        config_opts = None
        if not args.skip_config:
            try:
                config_opts = fetch_config(base_url, api_key, insecure)
                emit_config_options(config_opts)
            except RuntimeError as e:
                fail(E_CONFIG_FAIL, "拉取 config 失败：%s。可加 --skip-config 继续（跳过枚举预校验，风险自负）。" % e)
        body = validate_and_build(args, config_opts, base_url, api_key, insecure)
        task_id = create_task(base_url, api_key, body, insecure)

    log("开始轮询（最长 %ds，间隔 %ds）..." % (args.poll_timeout, args.poll_interval))
    response = poll_loop(base_url, api_key, task_id, args.poll_timeout,
                         args.poll_interval, insecure, resp_out)
    data = response.get("data") or {}

    # 落最终接口响应
    _write_response(resp_out, response)
    log("响应已保存：%s" % resp_out)

    # 输出 MD（解析接口返回的 markdown 字段）
    overview_md = (data.get("result") or {}).get("markdown") or ""
    md_path = ""
    if md_out:
        if render_report(resp_out, md_out):
            md_path = str(Path(md_out).resolve())
            log("报告已输出：%s" % md_path)
        else:
            log("⚠️ 输出 MD 失败，仍交付响应 JSON 供排查。")
    elif not md_out:
        log("未指定 --md-out，跳过输出 MD（仅交付响应 JSON）。")

    # 解析本次实际扣点（尽力，后端字段未固定）。空则 agent 走兜底措辞。
    points_used = extract_points_used(data)
    points_str = "" if points_used is None else str(points_used)
    if points_used is not None:
        log("本次实际扣点：%s 点" % points_used)
    else:
        log("响应未携带扣点字段，实际扣点以账户侧为准。")

    emit(("===TASK_ID===", task_id),
         ("===RESPONSE_PATH===", str(Path(resp_out).resolve())),
         ("===MD_PATH===", md_path),
         ("===OVERVIEW_MD===", overview_md),
         ("===POINTS_USED===", points_str))
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
