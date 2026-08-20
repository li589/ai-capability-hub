#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书爆款图文生成【零一数科·出品】 —— 联网主脚本 (v0.1.0)

异步任务模型：
  读 Key → 校验参数 → （可选：上传参考图换 image_id）→ POST 创建任务（立即返回 task_id）→
  GET 轮询进度（stderr 输出）→ 终态后提取 data.total_points →
  取 data.markdown → 拼接报告 → 写盘 → 分隔符协议输出 stdout。

⚠️ 本 API 与标准范式的偏差（见 references/api.md 顶部「偏差」段）：
  1. 无 POST /{id}/retry 重试接口；--retry-task 实为「重新创建新任务」
     （新 task_id、独立扣费），失败重提须重供 --text 与业务参数重建 body。
  2. 扣点字段是 data.total_points（顶层整数），extract_total_points 已兼容。
  3. 有 GET /config 拉取 target_platform / seeding_structure / brand_tone 三组枚举，
     三者均为创建必填 且值须来自 config 实时 options，禁止硬编码示例值；
     --fetch-config 拉取实时枚举展示给用户选。
  4. 后端 data.markdown 自带一级标题（# 标题）且要求原样展示；assemble_report
     检测到 H1 即不再前置脚本标题、不插分隔线，避免出现两个 H1；仅无 H1 时
     才前置「# 种草图文方案：<话题>」兜底。
  5. 本 API 无幂等机制（文档无 idempotency 字段，§4.3 禁未声明字段→否则 422）；
     标准 §9 的『X-Idempotency-Key + body idempotency_key』不适用，已移除：
     不发幂等头、不向 body 注入 idempotency_key，CLI 亦无 --idempotency-key。
  6. 有可选「参考图上传」分支：POST 取预签名 → PUT 文件二进制 → POST 确认换 image_id，
     最多 3 张，单张 ≤10MB（超限本地拒绝退码 3、不发起上传，API 文档未明示该上限），
     上传后写入创建请求 reference_images。上传发生在创建任务之前，
     任一步失败任务未发起、未扣点。
  7. 偏差（文件上传必要）：参考图 PUT 直传单次 HTTP 超时设为 300s（UPLOAD_HTTP_TIMEOUT），
     标准 §9 默认 60s；JSON 接口（取预签名 / 确认 / 创建 / 查询）仍用 60s。
     上传失败按性质归入退出码 3/8/10/11，不自创码 9。
  8. 竞态宽限：status=completed 但 data.markdown 尚未回填时，COMPLETED_REPORT_GRACE_SECONDS=60
     内继续轮询等补齐（三处终态出口均触发：wait_for_task 入口短路/循环内/--poll-task 已终态分支）；
     宽限超时仍空则兜底落盘含续查指引的 md + stdout 正文 + exit12（不伪造真实正文）。

退出码见 SKILL.md「退出码处理」。纯标准库。
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

# --------------------------------------------------------------------------- 常量
BASE_URL = "https://claw.lingyishuke.com/services"
TASKS_PATH = "/api/v1/content/seeding-article-generation"
CONFIG_PATH = "/api/v1/content/seeding-article-generation/config"
# 参考图上传（可选分支）
UPLOAD_URL_PATH = "/api/v1/content-ops/images/public-upload-url"
UPLOAD_CONFIRM_PATH = "/api/v1/content-ops/images/public-upload-confirm"

DEFAULT_TIMEOUT = 90   # 单次轮询等待上限（秒）；< WorkBuddy/Web 单轮上限；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60      # 单次 HTTP 超时（创建/retry/get/取预签名/确认）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5
OVERALL_POLL_CAP = 25 * 60  # 开启 generate_images 时更耗时，整体轮询封顶 ~25 分钟
COMPLETED_REPORT_GRACE_SECONDS = 60  # 竞态宽限：status=completed 但 data.markdown 尚未落库时，再轮询 ≤60s 等补齐
UPLOAD_HTTP_TIMEOUT = 300    # 偏差：参考图 PUT 直传单次超时（标准 §9 默认 60s，图片上传放宽）

MAX_REF_IMAGES = 3
ALLOWED_IMAGE_EXTS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}
MAX_REF_IMAGE_BYTES = 10 * 1024 * 1024  # 单张参考图大小上限 10MB；超过本地拒绝(退码3)，不上传、不扣点（脚本侧约定，API 文档未明示）

# 约定回退扣点（仅「约 N 点」提示，不当作实扣）
PLAN_POINTS = 100         # 约定估值（账户余额门槛 100 点，见 api.md §5），正式实扣以 data.total_points 为准

# 任务态
STATUS_OK = "completed"
STATUS_TERMINAL = frozenset({"completed", "failed", "timeout"})
STATUS_RETRYABLE = frozenset({"failed", "timeout"})

# 退出码
E_OK = 0
E_NO_KEY = 2
E_PARAM = 3
E_BALANCE = 4
E_AUTH = 8
E_4XX = 10
E_5XX = 11
E_FAILED = 12   # 已发起但中途失败
E_PENDING = 13  # 已发起但未到终态（非失败，可续 --poll-task）

# stdout 交付协议（前缀按本 skill 代号）
PREFIX = "SEEDING_ARTICLE"
POINTS_PREFIX = "%s_POINTS_USED=" % PREFIX
PLAN_PREFIX = "%s_PLAN_POINTS=" % PREFIX
REPORT_START = "=== %s_REPORT_START ===" % PREFIX
REPORT_END = "=== %s_REPORT_END ===" % PREFIX
FILE_PREFIX = "%s_REPORT_FILE=" % PREFIX
TASK_PREFIX = "%s_TASK_ID=" % PREFIX
STATUS_PREFIX = "%s_STATUS=" % PREFIX
PROGRESS_PREFIX = "%s_PROGRESS=" % PREFIX
EAPSED_PREFIX = "%s_EAPSED=" % PREFIX

SECTION_SEPARATOR = "\n\n---\n\n"

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


# --------------------------------------------------------------------------- 工具
def log(msg):
    print("[seeding_article] %s" % msg, file=sys.stderr, flush=True)


def fail(code, msg):
    log("❌ " + msg)
    sys.exit(code)


def to_text(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except Exception:
            return value.decode("utf-8", "ignore")
    return value


def get_api_key():
    """从技能目录 config.json 读 LY_API_KEY，回退环境变量。"""
    skill_dir = Path(__file__).resolve().parent.parent
    cfg = skill_dir / "config.json"
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text("utf-8"))
            if isinstance(data, dict) and data.get("LY_API_KEY"):
                return to_text(data["LY_API_KEY"]).strip()
        except (json.JSONDecodeError, OSError):
            pass
    env = os.environ.get("LY_API_KEY")
    return env.strip() if env else ""


def auth_headers(api_key):
    # 本 API 无幂等机制（文档无 idempotency 字段，§4.3 禁未声明字段），不发 X-Idempotency-Key 头；
    # X-Appbuilder-From: openclaw 为客户端约定头（API 文档 §1.3 未列，通常无害；用于平台侧来源标识）。
    # 上传两接口虽支持裸 key，脚本统一用 Bearer 即可。
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }
    return headers


def parse_json(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def read_text(arg):
    """--text 可为：文件路径、'-' 读 stdin、或直接文本。"""
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg).expanduser()
    if p.is_file():
        return p.read_text("utf-8")
    return arg


def http_request(url, method, headers, body, timeout):
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            return status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            raw = e.read()
        except Exception:
            raw = b""
        return status, raw.decode("utf-8", "ignore")


def http_request_with_retries(url, method, headers, body, timeout, label, retries=HTTP_RETRY_TIMES):
    """瞬时网络错误 / 5xx 有限重试；4xx 直接返回。"""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            status, text = http_request(url, method, headers, body, timeout)
            if status >= 500 and attempt < retries:
                wait = min(2 ** (attempt - 1), MAX_BACKOFF)
                log("%s服务端 %s，%ds 后重试（%d/%d）" % (label, status, wait, attempt, retries))
                time.sleep(wait)
                continue
            return status, text
        except urllib.error.URLError as e:
            last_err = e
            if attempt > retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s网络错误：%s，%ds 后重试（%d/%d）" % (label, e, wait, attempt, retries))
            time.sleep(wait)
        except Exception as e:
            last_err = e
            if attempt > retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s请求异常：%s，%ds 后重试（%d/%d）" % (label, e, wait, attempt, retries))
            time.sleep(wait)
    raise last_err


# --------------------------------------------------------------------------- 扣点提取
def extract_total_points(payload):
    """提取实际扣点。本 API 正式字段是 data.total_points（整数）；
    回退标准 data.billing.total_points 与历史候选 key。命中返回数值，否则 None。"""
    if not isinstance(payload, dict):
        return None

    def _as_number(val):
        if isinstance(val, bool):
            return None
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str) and val.strip():
            try:
                f = float(val.strip())
                return int(f) if f.is_integer() else f
            except ValueError:
                return None
        return None

    candidates = []
    data = payload.get("data")
    if isinstance(data, dict):
        candidates.append(data.get("total_points"))
        billing = data.get("billing")
        if isinstance(billing, dict):
            candidates.append(billing.get("total_points"))
    billing_top = payload.get("billing")
    if isinstance(billing_top, dict):
        candidates.append(billing_top.get("total_points"))
    candidates.append(payload.get("total_points"))

    for c in candidates:
        n = _as_number(c)
        if n is not None:
            return n

    legacy_keys = ("points_used", "credits_used", "used_points", "deducted_points",
                   "charged_points", "points_cost", "point_used", "consumed_points")
    levels = [payload]
    if isinstance(data, dict):
        levels.append(data)
        for sub in ("billing", "result", "payment", "cost", "usage"):
            sub_obj = data.get(sub)
            if isinstance(sub_obj, dict):
                levels.append(sub_obj)
    for sub in ("billing", "payment", "cost", "usage"):
        sub_obj = payload.get(sub)
        if isinstance(sub_obj, dict):
            levels.append(sub_obj)
    for level in levels:
        for key in legacy_keys:
            if key in level:
                n = _as_number(level[key])
                if n is not None:
                    return n
    return None


def extract_recharge(payload):
    if not isinstance(payload, dict):
        return None
    inner = payload.get("data")
    if isinstance(inner, dict) and inner.get("recharge_url"):
        return inner.get("recharge_url")
    return payload.get("recharge_url")


def fmt_points(value):
    if value is None or isinstance(value, bool):
        return ""
    try:
        f = float(value)
        return str(int(f)) if f.is_integer() else str(f)
    except (TypeError, ValueError):
        return str(value)


# --------------------------------------------------------------------------- HTTP 错误分流
def raise_for_http(status, payload, resp_text, label):
    msg = ""
    if isinstance(payload, dict):
        msg = (payload.get("message")
               or (payload.get("detail") if isinstance(payload.get("detail"), str) else None)
               or "")
        detail = payload.get("detail")
        if isinstance(detail, dict) and detail.get("message"):
            msg = detail.get("message") or msg
    if not msg:
        msg = (resp_text or "")[:200]

    if status == 401:
        fail(E_AUTH, "%s鉴权失败（HTTP 401）：API Key 无效或已过期，请更新 config.json 的 LY_API_KEY。服务端：%s" % (label, msg))
    if status == 402:
        recharge = extract_recharge(payload or {})
        tip = "%s余额不足，无法调用。" % label
        if recharge:
            tip += " 请前往充值：%s" % recharge
        else:
            tip += " 请充值后再试（服务端：%s）。" % msg
        fail(E_BALANCE, tip)
    if status in (400, 422):
        fail(E_PARAM, "%s参数/校验失败（HTTP %s）：%s" % (label, status, msg))
    if status == 404:
        fail(E_4XX, "%s任务不存在（HTTP 404）：%s" % (label, msg))
    if 400 < status < 500:
        fail(E_4XX, "%s调用失败（HTTP %s）：%s" % (label, status, msg))
    if status >= 500:
        fail(E_5XX, "%s服务端错误（HTTP %s）：%s" % (label, status, msg or "Internal server error"))


# --------------------------------------------------------------------------- 调任务 API
def _parse_task_response(status, resp_text, label):
    payload = parse_json(resp_text)
    if status != 200:
        raise_for_http(status, payload, resp_text, label)
    if payload is None:
        fail(E_5XX, "%s返回非 JSON（HTTP %s）：%s" % (label, status, resp_text[:200]))
    if payload.get("result") != "success":
        fail(E_4XX, "%s失败：HTTP %s result=%s message=%s" % (label, status, payload.get("result"), payload.get("message")))
    data = payload.get("data")
    if not isinstance(data, dict):
        fail(E_FAILED, "%s返回 data 为空或非对象。" % label)
    return data, payload


def _progress_summary(data):
    """从任务 data 汇总人类可读进度文案。本 API 字段：progress_message / current_stage / status。"""
    progress = (data.get("progress_message") or "").strip()
    current = (data.get("current_stage") or "").strip()
    status = (data.get("status") or "").strip()
    if progress:
        return progress
    if current:
        return "当前阶段：%s" % current
    if status:
        return "status=%s，等待调度" % status
    return "等待调度"


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s%s task_id=%s | %s" % (prefix, status or "?", elapsed_s, task_id or "-", summary))
    if emit_task_id and task_id:
        print("[seeding_article] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, body_obj, timeout, label="创建任务"):
    # 本 API 无幂等机制：不向 body 注入 idempotency_key（§4.3 禁未声明字段→否则 422），不发幂等头。
    url = base_url.rstrip("/") + TASKS_PATH
    body_obj = dict(body_obj)
    body = json.dumps(body_obj, ensure_ascii=False)
    log("%s：提交 %d 个字段" % (label, len(body_obj)))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key), body, timeout, label)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s（请检查网络与服务可达性：%s）" % (label, e, base_url))
    return _parse_task_response(status, resp_text, label)


def call_get_task(base_url, api_key, task_id, timeout, label="查询任务"):
    # task_id 是 JWT，含 . 与 base64url 字符，须 URL-path-encode 并原样传递
    encoded = urllib.parse.quote(str(task_id), safe="")
    url = base_url.rstrip("/") + TASKS_PATH + "/" + encoded
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def call_fetch_config(base_url, api_key, timeout, label="取配置"):
    """GET /config 拉取 target_platform / seeding_structure / brand_tone 枚举。不创建任务、不涉扣点。"""
    url = base_url.rstrip("/") + CONFIG_PATH
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    payload = parse_json(resp_text)
    if status != 200:
        raise_for_http(status, payload, resp_text, label)
    if payload is None or payload.get("result") != "success":
        fail(E_4XX, "%s失败：HTTP %s result=%s message=%s" % (label, status,
              (payload or {}).get("result"), (payload or {}).get("message")))
    data = payload.get("data")
    return data if isinstance(data, list) else (data if isinstance(data, dict) else []), payload


def call_retry_task(base_url, api_key, task_id, timeout, label="重试（重新创建）"):
    """⚠️ 偏差：本 API 无 /retry 接口。此函数不直接发请求——
    真正的「重建」在 main() 的 --retry-task 分支用 build_body + call_create_task 完成。
    保留原 <task_id> 仅作日志参考。"""
    log("%s：原 task_id=%s（本 API 无 /retry，将用相同参数重新创建新任务，独立扣费）" % (label, task_id))
    return None, None


def _grace_wait_for_markdown(base_url, api_key, data, payload, poll_interval):
    """竞态宽限：status 已 completed 但 data.markdown 尚未回填时，在 COMPLETED_REPORT_GRACE_SECONDS 内继续轮询。

    返回 (data, payload)——可能更新为带 markdown 的 data，也可能原样返回（宽限超时仍空）。
    中途 status 翻成 failed/timeout → 返回新 data，交上层 handle_task_outcome 走失败分支。
    网络错误 continue 继续（宽限本为等短暂延迟，抖动不应中断）。判空统一用 `not extract_markdown(data)`。
    """
    task_id = str(data.get("task_id") or "")
    if not task_id:
        return data, payload
    deadline = time.monotonic() + COMPLETED_REPORT_GRACE_SECONDS
    log("status 已 completed 但 markdown 暂未回填，宽限 %ds 内继续轮询…" % COMPLETED_REPORT_GRACE_SECONDS)
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        try:
            data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        except SystemExit:
            raise
        except Exception as e:
            log("宽限轮询暂失败（忽略继续）：%s" % e)
            continue
        if extract_markdown(data):
            log("宽限窗口内 markdown 已回填，继续交付。")
            return data, payload
        new_status = str(data.get("status") or "")
        if new_status in STATUS_RETRYABLE:  # failed/timeout
            log("宽限窗口内 status 翻成 %s，交回上层走失败分支。" % new_status)
            return data, payload
        # status 仍 completed 且仍无 md → 继续等
    log("宽限窗口超时，markdown 仍未回填，走兜底交付（exit 12）。")
    return data, payload


def _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval):
    """终态出口通用钩子：若 status==completed 且 markdown 空，触发宽限窗口。"""
    if str(data.get("status") or "") == STATUS_OK and not extract_markdown(data):
        return _grace_wait_for_markdown(base_url, api_key, data, payload, poll_interval)
    return data, payload


def wait_for_task(base_url, api_key, data, payload, timeout_total, poll_interval=PROGRESS_POLL_INTERVAL):
    """轮询 GET 直到终态或单次超时。返回 (data, payload, exit_code)：
    终态 E_OK；单次轮询到上限 E_PENDING（非失败）。"""
    if not isinstance(data, dict):
        fail(E_FAILED, "任务响应 data 无效，无法轮询。")
    status = str(data.get("status") or "")
    task_id = str(data.get("task_id") or "")
    started = time.time()
    log_task_progress(data, elapsed=0, prefix="任务已提交", emit_task_id=True)

    if status in STATUS_TERMINAL:
        data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
        return data, payload, E_OK
    if not task_id:
        fail(E_FAILED, "创建任务未返回 task_id，无法轮询进度。")

    log("开始轮询任务进度（间隔 %ds，单次最长 %ds）…" % (poll_interval, int(timeout_total)))
    while True:
        elapsed = time.time() - started
        if elapsed >= timeout_total:
            log("单次轮询到上限（%ds）：仍非终态，可续轮询。" % int(timeout_total))
            return data, payload, E_PENDING
        if elapsed >= OVERALL_POLL_CAP:
            log("整体轮询已达封顶（%ds），停止；可用 --poll-task 续轮询或重提。" % OVERALL_POLL_CAP)
            return data, payload, E_PENDING
        time.sleep(poll_interval)
        try:
            data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        except SystemExit:
            raise
        except Exception as e:
            log("轮询暂失败：%s（将继续）" % e)
            continue
        status = str(data.get("status") or "")
        log_task_progress(data, elapsed=time.time() - started, prefix="进度")
        if status in STATUS_TERMINAL:
            log("任务到达终态：status=%s task_id=%s" % (status, task_id))
            data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
            return data, payload, E_OK


# --------------------------------------------------------------------------- 参考图上传（可选分支）
def guess_image_content_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ALLOWED_IMAGE_EXTS.get(ext, "application/octet-stream")


def upload_one_image(base_url, api_key, path):
    """三步上传单张参考图，返回 image_id。任一步失败按性质归入 3/8/10/11 终止（任务未发起、未扣点）。"""
    p = Path(path).expanduser()
    if not p.is_file():
        fail(E_PARAM, "参考图不存在或不可读：%s（任务未发起、未扣点）" % path)
    filename = p.name
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        fail(E_PARAM, "参考图扩展名不支持：%s（允许 png/jpg/jpeg/webp/gif/bmp，任务未发起、未扣点）" % filename)
    size = p.stat().st_size
    if size > MAX_REF_IMAGE_BYTES:
        fail(E_PARAM, "参考图 %s 太大（%.1fMB），单张上限 %dMB，请压缩后重试（任务未发起、未扣点）。" % (
            path, size / 1024 / 1024, MAX_REF_IMAGE_BYTES // (1024 * 1024)))

    # 1) 取预签名（入参只需 filename）
    url = base_url.rstrip("/") + UPLOAD_URL_PATH
    body = json.dumps({"filename": filename}, ensure_ascii=False)
    log("取预签名上传地址：%s" % filename)
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key), body, HTTP_TIMEOUT, "取预签名")
    except Exception as e:
        fail(E_5XX, "取预签名网络错误（任务未发起、未扣点）：%s" % e)
    payload = parse_json(resp_text) or {}
    if status != 200 or payload.get("result") != "success":
        raise_for_http(status, payload, resp_text, "取预签名")  # 400/422→3, 401→8, 402→4, 5xx→11
    data = payload.get("data") or {}
    upload_url = data.get("upload_url") or data.get("url")
    upload_id = data.get("upload_id")
    method = (data.get("method") or "PUT").upper()
    if not upload_url or not upload_id:
        fail(E_5XX, "取预签名返回缺 upload_url/upload_id（任务未发起、未扣点）：%s" % resp_text[:200])

    # 2) 直传文件字节到 OSS（不带平台 Authorization），Content-Type 按扩展名
    content_type = guess_image_content_type(filename)
    file_bytes = p.read_bytes()
    put_headers = {"Content-Type": content_type}
    log("上传参考图文件中（%s，%d 字节）…" % (filename, len(file_bytes)))
    try:
        status, resp_text = http_request(upload_url, method, put_headers, file_bytes, UPLOAD_HTTP_TIMEOUT)
    except urllib.error.URLError as e:
        fail(E_5XX, "上传参考图网络错误（任务未发起、未扣点）：%s" % e)
    except Exception as e:
        fail(E_5XX, "上传参考图异常（任务未发起、未扣点）：%s" % e)
    if status not in (200, 201, 204):
        # OSS 4xx 通常为预签名失效/签名不匹配，视为可重试的设施错误
        fail(E_5XX, "上传参考图失败：HTTP %s（预签名 URL 可能已失效，请重试；任务未发起、未扣点）" % status)

    # 3) 确认上传（入参 upload_id + extra_data:{}；成功 HTTP 201，故不能复用 _parse_task_response）
    url = base_url.rstrip("/") + UPLOAD_CONFIRM_PATH
    body = json.dumps({"upload_id": upload_id, "extra_data": {}}, ensure_ascii=False)
    log("确认上传…")
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key), body, HTTP_TIMEOUT, "确认上传")
    except Exception as e:
        fail(E_5XX, "确认上传网络错误（任务未发起、未扣点）：%s" % e)
    payload = parse_json(resp_text) or {}
    if status not in (200, 201) or payload.get("result") != "success":
        raise_for_http(status, payload, resp_text, "确认上传")  # 4xx(非401)→10, 5xx→11
    data = payload.get("data") or {}
    image_id = data.get("image_id")
    if not image_id:
        fail(E_5XX, "确认上传返回缺 image_id（任务未发起、未扣点）：%s" % resp_text[:200])
    image_url = data.get("image_url")
    log("参考图上传完成：%s → image_id=%s%s" % (filename, image_id, (" url=%s" % image_url) if image_url else ""))
    return image_id


def upload_reference_images(base_url, api_key, paths):
    """上传多张参考图，返回 image_id 列表。任一张失败即终止。"""
    if not paths:
        return []
    paths = [p for p in paths if p and p.strip()]
    if len(paths) > MAX_REF_IMAGES:
        fail(E_PARAM, "参考图最多 %d 张，传入 %d 张（任务未发起、未扣点）。" % (MAX_REF_IMAGES, len(paths)))
    image_ids = []
    for p in paths:
        image_ids.append(upload_one_image(base_url, api_key, p.strip()))
    return image_ids


# --------------------------------------------------------------------------- 结果提取与报告拼装
def extract_markdown(data):
    """从终态 data 取报告 markdown。本 API 取 data.markdown（单串）。
    兼容 data.result.markdown / data.results.<m>.markdown 多形态。取不到返回 ""。"""
    if isinstance(data, dict):
        mk = data.get("markdown")
        result = data.get("result") if isinstance(data.get("result"), dict) else None
        if not mk and isinstance(result, dict):
            mk = result.get("markdown")
        if mk:
            return str(mk).strip()

        results = data.get("results")
        if isinstance(results, dict):
            parts = []
            for _k, item in results.items():
                md = ""
                if isinstance(item, str):
                    md = item.strip()
                elif isinstance(item, dict):
                    md = item.get("markdown")
                    if not md and isinstance(item.get("data"), dict):
                        md = item["data"].get("markdown")
                if md:
                    parts.append(str(md).strip())
            if parts:
                return SECTION_SEPARATOR.join(parts)
    return ""


def make_title(text):
    title = (text[:20] + "…") if len(text) > 20 else text
    return title.replace("\n", " ").strip() or "种草图文方案"


def _starts_with_h1(md):
    """判断 markdown 是否以一级标题开头（首行 `# `）。"""
    for line in str(md).splitlines():
        s = line.strip()
        if not s:
            continue
        return s.startswith("# ") and not s.startswith("## ")
    return False


def assemble_report(text, markdown_sections):
    """拼最终报告 markdown。markdown_sections: [str, ...] 已剔空。

    ⚠️ 偏差：本 API 后端 data.markdown 已自带一级标题（# 标题），且文档要求
    「原样使用、不重新组织」。故若后端 markdown 已以 H1 开头，**不再前置脚本
    标题、不插分隔线**，直接原样拼接输出，避免出现两个 H1。仅当后端 markdown
    没 H1 时，才前置 `# 种草图文方案：<话题摘要>` 作为兜底标题。
    """
    clean = [s.replace("\r\n", "\n").replace("\r", "\n").strip() for s in markdown_sections if s and s.strip()]
    if not clean:
        return "# 种草图文方案：%s\n" % make_title(text)

    if any(_starts_with_h1(s) for s in clean):
        return SECTION_SEPARATOR.join(clean) + "\n"

    return "# 种草图文方案：%s\n\n%s\n" % (make_title(text), SECTION_SEPARATOR.join(clean))


def plan_points_for():
    return PLAN_POINTS


def handle_task_outcome(data, payload, text, out_path):
    """根据任务 status 产出报告或兜底交付。返回 (final_md, points, task_id)。
    completed 有 md → 返回正常三元组，由调用方 _emit。
    completed 无 md → 内部组装兜底 md、_emit 落盘+stdout、sys.exit(12)（不返回）。
    failed/timeout/未知 → fail(12) 不变。"""
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    failure_message = data.get("error_message") or data.get("failure_message") or ""

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status == STATUS_OK:
        md = extract_markdown(data)
        if md:
            return assemble_report(text, [md]), points, task_id
        # 兜底：组装「结果暂不可用」md，落盘 + stdout，exit 12
        log("⚠️ 任务已 completed 但 markdown 宽限后仍为空，走兜底交付（exit 12）。task_id=%s" % task_id)
        safe_text = text.replace('"', "'")[:30]
        fallback_note = (
            "> ⚠️ 任务已完成（task_id=%s），但报告正文暂未从服务端返回（多为报告落库延迟）。\n"
            "> 可稍后用 `--poll-task %s --text \"...\"` 续查，或 `--retry-task` 重新创建（独立扣费）。\n"
            "> 本次为兜底交付：文件已落盘，但正文待补；退出码 12 表示未真正成功产出报告，请勿将本段当真实种草图文发布。"
        ) % (task_id, task_id)
        fallback_md = assemble_report(text, [fallback_note])
        _emit(fallback_md, points, plan_points_for(), out_path, task_id, exit_code=E_FAILED)
        return  # _emit 内 sys.exit，此处不会到达

    detail = failure_message or status or "unknown"
    if status in STATUS_RETRYABLE:
        tip = "任务未成功：status=%s %s task_id=%s。本 API 无 /retry 接口，可重新创建（独立扣费）。" % (status, detail, task_id)
        fail(E_FAILED, tip)
    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, detail, task_id))


# --------------------------------------------------------------------------- 业务校验
def validate_business_args(args):
    """创建/重试前校验业务参数，客户端拦截非法值，避免靠服务端 422。"""
    if not args.target_platform or not args.target_platform.strip():
        fail(E_PARAM, "缺少必填 --target-platform（请先 --fetch-config 拉取实时枚举后传入 value）。")
    if not args.seeding_structure or not args.seeding_structure.strip():
        fail(E_PARAM, "缺少必填 --seeding-structure（请先 --fetch-config 拉取实时枚举后传入 value）。")
    if not args.brand_tone or not args.brand_tone.strip():
        fail(E_PARAM, "缺少必填 --brand-tone（请先 --fetch-config 拉取实时枚举后传入 value）。")

    if not args.selling_points or not [s for s in args.selling_points if s and s.strip()]:
        fail(E_PARAM, "缺少必填 --selling-points（1-3 条非空卖点）。")
    sp = [s.strip() for s in args.selling_points if s and s.strip()]
    if len(sp) < 1 or len(sp) > 3:
        fail(E_PARAM, "--selling-points 需 1-3 条（当前 %d 条）。" % len(sp))
    for s in sp:
        if len(s) > 20:
            log("⚠️ 卖点「%s…」超过 20 字，后端将截断。" % s[:20])

    for name, val, lo, hi in (
        ("cover-count", args.cover_count, 0, 3),
        ("image-count", args.image_count, 0, 8),
    ):
        if val is not None and (val < lo or val > hi):
            fail(E_PARAM, "--%s 需 %d-%d（当前 %s）。" % (name, lo, hi, val))

    if args.reference_text and len(args.reference_text) > 500:
        fail(E_PARAM, "--reference-text 超过 500 字上限（当前 %d）。" % len(args.reference_text))
    if args.ref_image_desc and len(args.ref_image_desc) > 100:
        log("⚠️ --ref-image-desc 超过 100 字，后端将截断。")

    if args.ref_image:
        paths = [p for p in args.ref_image if p and p.strip()]
        if len(paths) > MAX_REF_IMAGES:
            fail(E_PARAM, "参考图最多 %d 张，传入 %d 张。" % (MAX_REF_IMAGES, len(paths)))
        for p in paths:
            rp = Path(p.strip()).expanduser()
            ext = os.path.splitext(p.strip())[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                fail(E_PARAM, "参考图 %s 扩展名不支持（允许 png/jpg/jpeg/webp/gif/bmp）。" % p)
            if not rp.is_file():
                fail(E_PARAM, "参考图不存在或不可读：%s" % p)
            size = rp.stat().st_size
            if size > MAX_REF_IMAGE_BYTES:
                fail(E_PARAM, "参考图 %s 太大（%.1fMB），单张上限 %dMB，请压缩后重试。" % (
                    p, size / 1024 / 1024, MAX_REF_IMAGE_BYTES // (1024 * 1024)))


def build_body(args, text, image_ids=None):
    """按 references/api.md 构造 POST 创建任务 body。
    text 即 product_or_topic（产品或话题），兼作报告标题摘要。
    可选业务参数仅在设置时加入，缺省不传走后端默认（禁未声明字段，否则 422）。
    image_ids 为已上传参考图换得，非空时写入 reference_images。
    """
    body = {
        "product_or_topic": text.strip()[:30],
        "selling_points": [s.strip() for s in args.selling_points if s and s.strip()][:3],
        "target_platform": args.target_platform.strip(),
        "seeding_structure": args.seeding_structure.strip(),
        "brand_tone": args.brand_tone.strip(),
        "origin": (args.origin or "01workbuddy").strip(),
        "origin_method": (args.origin_method or "skill").strip(),
    }

    # 可选字段：仅在设置时加入
    if args.reference_text and args.reference_text.strip():
        body["reference_text"] = args.reference_text.strip()[:500]
    if args.generate_images:
        body["generate_images"] = True
        # render_text_on_image 仅在 generate_images=true 时才有意义才写入
        if args.render_text_on_image:
            body["render_text_on_image"] = True

    # image_count_config：仅当 cover-count 或 image-count 显式传时构造，只含显式传入的子键
    icc = {}
    if args.cover_count is not None:
        icc["cover"] = args.cover_count
    if args.image_count is not None:
        icc["image"] = args.image_count
    if icc:
        body["image_count_config"] = icc

    # 参考图：仅当有 image_id 时写入 reference_images；reference_image_desc 随之
    if image_ids:
        body["reference_images"] = list(image_ids)[:MAX_REF_IMAGES]
        if args.ref_image_desc and args.ref_image_desc.strip():
            body["reference_image_desc"] = args.ref_image_desc.strip()[:100]

    return body


def add_business_args(ap):
    """追加本 skill 必填/可选业务参数。"""
    ap.add_argument("--target-platform", default=None,
                    help="目标平台，必填；值须取自 --fetch-config 的 target_platform.options[].value（勿硬编码示例值）。")
    ap.add_argument("--seeding-structure", default=None,
                    help="种草正文结构型，必填；值须取自 --fetch-config 的 seeding_structure.options[].value。")
    ap.add_argument("--brand-tone", default=None,
                    help="品牌/内容调性，必填；值须取自 --fetch-config 的 brand_tone.options[].value。")
    ap.add_argument("--selling-points", action="append", default=None, metavar="POINT",
                    help="核心卖点，必填 1-3 条，可多次传入；单条 >20 字后端截断。")
    ap.add_argument("--reference-text", default=None, help="用户补充/参考文案，可选，≤500 字。")
    ap.add_argument("--generate-images", action="store_true",
                    help="是否实际调用生图；不传=false 时通常只产方案与 AI 生图 Prompt。")
    ap.add_argument("--render-text-on-image", action="store_true",
                    help="是否允许把文字画进图；仅 --generate-images 时有意义。")
    ap.add_argument("--cover-count", type=int, default=None, help="封面张数，可选 0-3，默认 1。")
    ap.add_argument("--image-count", type=int, default=None, help="配图张数，可选 0-8，默认 1。")
    ap.add_argument("--ref-image", action="append", default=None, metavar="PATH",
                    help="参考图本地路径（png/jpg/jpeg/webp/gif/bmp），可多次传入最多 3 张；"
                         "脚本将三步上传换取 image_id 后写入 reference_images。")
    ap.add_argument("--ref-image-desc", default=None,
                    help="参考图附加提示词，≤100 字超出后端截断；仅在 --ref-image 存在时写入 body。")
    ap.add_argument("--origin", default="01workbuddy", help="调用来源/宿主（埋点），默认 01workbuddy。")
    ap.add_argument("--origin-method", default="skill", help="调用方式（审计/溯源），默认 skill。")


def print_config(data):
    """渲染 GET /config 的三组枚举为易读文本。三组均为创建必填。"""
    if isinstance(data, dict):
        items = [data]
    elif isinstance(data, list):
        items = [x for x in data if isinstance(x, dict)]
    else:
        items = []
    if not items:
        print("（config 未返回可识别字段）")
        return
    print("以下枚举均为创建任务必填项，请用对应 options 的 value 传入 CLI：")
    print("  --target-platform / --seeding-structure / --brand-tone")
    print("")
    for item in items:
        field = item.get("field") or ""
        label = item.get("label") or field
        desc = item.get("desc") or ""
        print("字段：%s（%s）%s" % (field, label, ("—— " + desc) if desc else ""))
        options = item.get("options") or []
        if not options:
            print("  ⚠️ options 为空，创建任务将因配置缺失失败，请联系管理员。")
        for opt in options:
            if isinstance(opt, dict):
                ov = opt.get("value", "")
                ol = opt.get("label", "")
                od = opt.get("desc", "")
                print("  - %s\t%s%s" % (ov, ol, ("（" + od + "）") if od else ""))
        print("")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="小红书爆款图文生成【零一数科·出品】（异步任务 API · v0.1.0）")
    ap.add_argument("--text", default=None,
                    help="产品或话题名称（即 product_or_topic），或文件路径，或 '-' 读 stdin；兼作报告标题摘要。≤30 字。")
    ap.add_argument("--out", default=None, help="输出 MD 路径；缺省写当前目录的 种草图文方案-<task_id>.md")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s，< WorkBuddy/Web 单轮上限）。到点非错误，进行中退出 13 可续轮询。" % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--retry-task", default=None, metavar="TASK_ID",
                    help="【偏差】本 API 无 /retry，--retry-task 实为用相同参数重新创建新任务（新 task_id、独立扣费）。须重供 --text 与业务参数重建 body。")
    ap.add_argument("--only-create", action="store_true", help="仅 POST 创建拿 task_id 后即退（退出码 0，不轮询）")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；务必带 --text（用于报告标题）。终态交付(exit0)；仍运行 exit13；终态失败 exit12。")
    ap.add_argument("--fetch-config", action="store_true",
                    help="GET /config 拉取 target_platform/seeding_structure/brand_tone 实时枚举并打印，不创建任务、不涉扣点。")
    add_business_args(ap)
    args = ap.parse_args()

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "未取到 API Key：技能目录 config.json 不存在或无 LY_API_KEY 字段。\n"
              "请前往 https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy 获取，\n"
              "写入 config.json（如 {\"LY_API_KEY\": \"你的密钥\"}）或设环境变量 LY_API_KEY 后重试。")

    if args.insecure or os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
        global SSL_CONTEXT
        SSL_CONTEXT = ssl.create_default_context()
        SSL_CONTEXT.check_hostname = False
        SSL_CONTEXT.verify_mode = ssl.CERT_NONE

    base_url = os.environ.get("LY_BASE_URL", BASE_URL)
    poll_interval = max(1.0, float(args.poll_interval or PROGRESS_POLL_INTERVAL))

    # —— 取配置（拉取三组枚举，不创建任务、不扣点）——
    if args.fetch_config:
        data, _ = call_fetch_config(base_url, api_key, HTTP_TIMEOUT)
        print_config(data)
        sys.exit(E_OK)

    # —— 轮询已有任务 ——
    if args.poll_task:
        task_id = args.poll_task.strip()
        if not task_id:
            fail(E_PARAM, "--poll-task 不能为空。")
        data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        status = str(data.get("status") or "")
        if status not in STATUS_TERMINAL:
            data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        else:
            # 已终态：若 completed 但 markdown 空，进宽限窗口（修复竞态——--poll-task 是最常用路径）
            data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
            code = E_OK
        status = str(data.get("status") or "")
        if status in STATUS_TERMINAL:
            text_for_title = (args.text and read_text(args.text).strip()) or ("任务 %s" % task_id[:8])
            if not (args.text and read_text(args.text).strip()):
                log("提示：--poll-task 未带 --text，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --text。" % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(data, payload, text_for_title, args.out)
            _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
            return
        _emit_pending(data, task_id, int(args.timeout))
        return

    # —— 重试模式（偏差：实际为重新创建新任务，独立扣费）——
    if args.retry_task:
        old_id = args.retry_task.strip()
        if not old_id:
            fail(E_PARAM, "--retry-task 不能为空。")
        if not args.text:
            fail(E_PARAM, "--retry-task 需重供 --text（product_or_topic）以重建请求体。")
        text = read_text(args.text).strip()
        if not text:
            fail(E_PARAM, "输入文本（product_or_topic）为空。")
        if len(text) > 30:
            fail(E_PARAM, "product_or_topic 超过 30 字上限（当前 %d）。" % len(text))
        validate_business_args(args)
        # 注意：--ref-image-desc 单独传但无 --ref-image 时忽略（不 fail）
        if args.ref_image_desc and args.ref_image_desc.strip() and not args.ref_image:
            log("⚠️ 传了 --ref-image-desc 但未传 --ref-image，将忽略 desc。")
        image_ids = upload_reference_images(base_url, api_key, args.ref_image) if args.ref_image else []
        body = build_body(args, text, image_ids)
        log("--retry-task %s：本 API 无 /retry，将重新创建新任务（独立扣费）。" % old_id)
        data, payload = call_create_task(base_url, api_key, body, HTTP_TIMEOUT, label="重试（重新创建）")
        data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        if code == E_PENDING:
            _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
            return
        final_md, used_points, task_id_out = handle_task_outcome(data, payload, text, args.out)
        _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
        return

    # —— 仅创建任务（创建后即退，不轮询；先上传参考图，再 build_body）——
    if args.only_create:
        if not args.text:
            fail(E_PARAM, "--only-create 仍需 --text 提供 product_or_topic。")
        text = read_text(args.text).strip()
        if not text:
            fail(E_PARAM, "输入文本（product_or_topic）为空。")
        if len(text) > 30:
            fail(E_PARAM, "product_or_topic 超过 30 字上限（当前 %d）。" % len(text))
        validate_business_args(args)
        if args.ref_image_desc and args.ref_image_desc.strip() and not args.ref_image:
            log("⚠️ 传了 --ref-image-desc 但未传 --ref-image，将忽略 desc。")
        image_ids = upload_reference_images(base_url, api_key, args.ref_image) if args.ref_image else []
        body = build_body(args, text, image_ids)
        data, payload = call_create_task(base_url, api_key, body, HTTP_TIMEOUT)
        task_id = str(data.get("task_id") or "")
        status = str(data.get("status") or "")
        summary = _progress_summary(data)
        print(TASK_PREFIX + task_id)
        print(STATUS_PREFIX + status)
        print(PROGRESS_PREFIX + summary)
        print(REPORT_START)
        print(REPORT_END)
        sys.stdout.flush()
        log("已创建任务（仅创建模式）：task_id=%s status=%s" % (task_id, status))
        sys.exit(E_OK)

    # —— 新建任务 ——
    if not args.text:
        fail(E_PARAM, "请提供 --text（product_or_topic），或使用 --retry-task <task_id> / --poll-task <task_id>。")
    text = read_text(args.text).strip()
    if not text:
        fail(E_PARAM, "输入文本（product_or_topic）为空。")
    if len(text) > 30:
        fail(E_PARAM, "product_or_topic 超过 30 字上限（当前 %d）。" % len(text))
    validate_business_args(args)
    if args.ref_image_desc and args.ref_image_desc.strip() and not args.ref_image:
        log("⚠️ 传了 --ref-image-desc 但未传 --ref-image，将忽略 desc。")
    image_ids = upload_reference_images(base_url, api_key, args.ref_image) if args.ref_image else []
    body = build_body(args, text, image_ids)
    log("将创建任务，product_or_topic_len=%d generate_images=%s ref_images=%d" % (
        len(text), args.generate_images, len(image_ids)))
    data, payload = call_create_task(base_url, api_key, body, HTTP_TIMEOUT)
    data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
    if code == E_PENDING:
        _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(data, payload, text, args.out)
    _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)


def _emit_pending(data, task_id, elapsed):
    """单次轮询未到终态：透出进行中状态，退出码 E_PENDING（非失败，可续轮询）。"""
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    print(TASK_PREFIX + (task_id or ""))
    print(STATUS_PREFIX + status)
    print(PROGRESS_PREFIX + summary)
    print(EAPSED_PREFIX + "%d" % int(elapsed or 0))
    print(REPORT_START)
    print(REPORT_END)
    sys.stdout.flush()
    log("进行中：status=%s task_id=%s elapsed=%ds，可续 --poll-task。" % (status, task_id or "-", int(elapsed or 0)))
    sys.exit(E_PENDING)


def _safe_filename_stem(task_id):
    return "".join(c for c in str(task_id or "") if c.isalnum() or c in "-_") or uuid.uuid4().hex


def _write_report_to_disk(final_md, out_path, task_id):
    """三级兜底确保必生成 md：--out → 当前目录 种草图文方案-<id>.md → /tmp/种草图文方案-<id>.md。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "种草图文方案.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("种草图文方案-%s.md" % stem))
    candidates.append(Path("/tmp") / ("种草图文方案-%s.md" % stem))

    last_err = None
    for p in candidates:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(final_md, "utf-8")
            md_path = str(p.resolve())
            log("报告已写入：%s" % md_path)
            return md_path
        except OSError as e:
            last_err = e
            log("写盘失败（%s），尝试下一兜底路径…" % p)
            continue
        except Exception as e:
            last_err = e
            log("写盘异常（%s）：%s，尝试下一兜底路径…" % (p, e))
            continue
    log("⚠️ 所有写盘路径均失败：%s（报告正文已通过 stdout 交付，可手动保存）" % last_err)
    return ""


def _emit(final_md, used_points, plan_total, out_path, task_id, exit_code=E_OK):
    md_path = _write_report_to_disk(final_md, out_path, task_id)
    points_str = fmt_points(used_points)
    print(POINTS_PREFIX + points_str)
    print(PLAN_PREFIX + str(plan_total))
    print(FILE_PREFIX + md_path)
    print(TASK_PREFIX + (task_id or ""))
    print(REPORT_START)
    sys.stdout.write(final_md)
    if not final_md.endswith("\n"):
        sys.stdout.write("\n")
    print(REPORT_END)
    sys.stdout.flush()
    log("完成。task_id=%s points=%s exit=%s" % (task_id or "-", points_str or "(empty)", exit_code))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
