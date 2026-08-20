#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书爆款短视频拆解【零一数科·出品】 —— 联网主脚本 (v0.1.0)

异步任务模型：
  读 Key → 校验参数（小红书分享链接 或 本地视频文件 或 video_id）→
  【本地上传时先走：取预签名 → PUT 直传 → 确认 拿 video_id】→
  POST 创建拆解任务（立即返回 analysis_task_id）→
  GET 轮询进度（stderr 输出）→ 终态后取 data.result.markdown →
  拼接 markdown → 写盘 → 分隔符协议输出 stdout。

失败可按 task_id 调用 POST <tasks/{id}/retry>（异步）后再轮询。
退出码见 SKILL.md「退出码处理」。纯标准库（urllib）。

⚠️ 本脚本由「生成Skill（API→付费版）」基于 main.py.tpl 生成，业务区按
   references/api.md 的实际契约调整：
   - 任务 id 字段是 data.analysis_task_id（非 task_id）→ 统一经 get_task_id(data) 读取
   - 输入为 share_url 或 video_id/video_ids（非 text）→ CLI 用 --share-url / --video-file / --video-id
   - status 大小写都可能出现，统一 .lower() 判断
   - 进度字段 current_stage / progress_message
   - 报告 markdown 取 data.result.markdown
   - 本 API 无 billing.total_points 字段，扣点按前置约定 128 点/任务（_POINTS_USED 常为空，回退「约 128 点」）
"""

from __future__ import annotations

import argparse
import json
import mimetypes
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
TASKS_PATH = "/api/v1/social-analytics/collector/xiaohongshu-video-analyses"
PATH_UPLOAD_URL = "/api/v1/content-ops/videos/public-upload-url"
PATH_UPLOAD_CONFIRM = "/api/v1/content-ops/videos/public-upload-confirm"

DEFAULT_TIMEOUT = 90   # 单次轮询等待上限（秒）；< WorkBuddy/Web 单轮上限；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60      # 单次 HTTP 超时（创建/retry/get）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5
COMPLETED_REPORT_GRACE_SECONDS = 60  # 竞态宽限：终态 status=completed 但 markdown 尚未落库时，再轮询 ≤60s 等补齐

# 本地视频上传（上限 200MB，以服务端实际校验为准）
MAX_UPLOAD_BYTES = 200 * 1024 * 1024
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
DEFAULT_UPLOAD_CONTENT_TYPE = "application/octet-stream"

# 约定回退扣点（仅「约 N 点」提示，不当作实扣）
PLAN_POINTS = 128  # 本 API 前置约定：每次新创建拆解任务成功完成扣 128 点

# 任务态（统一小写判断；后端大小写都可能出现）
STATUS_OK = "completed"
STATUS_TERMINAL = frozenset({"completed", "success", "done", "failed", "error", "timeout"})
STATUS_RETRYABLE = frozenset({"failed", "error", "timeout"})

# 上传响应字段别名（适配后端不同形态）
F_UPLOAD_URL_ALIASES = ("upload_url", "uploadUrl", "url", "signed_url", "signedUrl", "presigned_url", "presignedUrl")
F_UPLOAD_METHOD = "method"
F_UPLOAD_HEADERS = "headers"
F_UPLOAD_ID_ALIASES = ("upload_id", "uploadId")
F_OBJECT_KEY_ALIASES = ("object_key", "objectKey", "key", "file_key", "fileKey", "path")
F_VIDEO_ID_ALIASES = ("video_id", "videoId", "id")
F_VIDEO_URL_ALIASES = ("video_url", "videoUrl", "file_url", "fileUrl", "url")

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
PREFIX = "XHS_VIDEO"
POINTS_PREFIX = "%s_POINTS_USED=" % PREFIX
PLAN_PREFIX = "%s_PLAN_POINTS=" % PREFIX
REPORT_START = "=== %s_REPORT_START ===" % PREFIX
REPORT_END = "=== %s_REPORT_END ===" % PREFIX
FILE_PREFIX = "%s_REPORT_FILE=" % PREFIX
TASK_PREFIX = "%s_TASK_ID=" % PREFIX
STATUS_PREFIX = "%s_STATUS=" % PREFIX
PROGRESS_PREFIX = "%s_PROGRESS=" % PREFIX
EAPSED_PREFIX = "%s_EAPSED=" % PREFIX

REPORT_LABEL = "小红书拆解报告"
TITLE_LABEL = "小红书拆解报告"
SECTION_SEPARATOR = "\n\n---\n\n"

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


# --------------------------------------------------------------------------- 工具
def log(msg):
    print("[xhs_video] %s" % msg, file=sys.stderr, flush=True)


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


def first_present(data, keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def get_task_id(data):
    """本 API 任务 id 字段是 analysis_task_id；兼容 task_id / content_ops_task_id。"""
    if not isinstance(data, dict):
        return ""
    return str(first_present(data, ("analysis_task_id", "analysisTaskId", "task_id", "taskId",
                                    "content_ops_task_id", "contentOpsTaskId")) or "")


def norm_status(data):
    return str((data.get("status") if isinstance(data, dict) else "") or "").lower()


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


def auth_headers(api_key, idempotency_key=None):
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "X-Appbuilder-From": "openclaw",
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
    """提取正式扣点字段 billing.total_points。本 API 无该字段，通常返回 None。
    命中返回数值，否则 None（由调用方按「约 128 点」回退）。
    """
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
        billing = data.get("billing")
        if isinstance(billing, dict):
            candidates.append(billing.get("total_points"))
        candidates.append(data.get("total_points"))
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
        if msg:
            tip += " 服务端：%s" % msg
        if recharge:
            tip += " 请前往充值：%s" % recharge
        fail(E_BALANCE, tip)
    if status in (400, 422):
        fail(E_PARAM, "%s参数/校验失败（HTTP %s）：%s" % (label, status, msg))
    if status == 404:
        fail(E_4XX, "%s任务不存在（HTTP 404）：%s" % (label, msg))
    if 400 <= status < 500:
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
    """从任务 data 汇总人类可读进度文案。本 API 字段：progress_message / current_stage。"""
    if not isinstance(data, dict):
        return ""
    progress = data.get("progress_message") or data.get("current_stage") or ""
    status = data.get("status") or ""
    if progress:
        return "当前：%s" % progress
    return "status=%s 等待调度" % status


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    task_id = get_task_id(data)
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s%s task_id=%s | %s" % (prefix, status or "?", elapsed_s, task_id or "-", summary))
    if emit_task_id and task_id:
        print("[xhs_video] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, body_obj, idempotency_key, timeout, label="创建任务"):
    url = base_url.rstrip("/") + TASKS_PATH
    body_obj = dict(body_obj)
    body_obj.setdefault("idempotency_key", idempotency_key)
    body = json.dumps(body_obj, ensure_ascii=False)
    log("%s：key=%s" % (label, idempotency_key[:8] + "…"))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key, idempotency_key), body, timeout, label)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s（请检查网络与服务可达性：%s）" % (label, e, base_url))
    return _parse_task_response(status, resp_text, label)


def call_get_task(base_url, api_key, task_id, timeout, label="查询任务"):
    url = base_url.rstrip("/") + TASKS_PATH + "/" + urllib.parse.quote(str(task_id), safe="")
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def call_retry_task(base_url, api_key, task_id, timeout, label="重试任务"):
    # 注意：重试端点未在该 skill 的 API 文档中明示，按统一异步范式实现 POST <tasks/{id}/retry>。
    # 若服务端不支持，会以 4xx 透出；失败时优先 --poll-task 续查或重新创建。
    url = base_url.rstrip("/") + TASKS_PATH + "/" + urllib.parse.quote(str(task_id), safe="") + "/retry"
    log("%s：task_id=%s" % (label, task_id))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key), None, timeout, label)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def _grace_wait_for_markdown(base_url, api_key, data, payload, poll_interval):
    """竞态宽限：status 已到成功终态(completed)但 markdown 尚未回填时，在
    COMPLETED_REPORT_GRACE_SECONDS 内继续轮询。

    返回 (data, payload)——可能更新为带 markdown 的 data，也可能原样返回（宽限超时仍空）。
    中途 status 翻成可重试终态（failed/timeout 等）→ 返回新 data，交上层 handle_task_outcome 走失败分支。
    网络错误 continue 继续（宽限本为等短暂延迟，抖动不应中断）。判空统一用 `not extract_markdown(data)`。
    """
    task_id = get_task_id(data)
    if not task_id:
        return data, payload
    deadline = time.monotonic() + COMPLETED_REPORT_GRACE_SECONDS
    log("status 已到成功终态但 markdown 暂未回填，宽限 %ds 内继续轮询…" % COMPLETED_REPORT_GRACE_SECONDS)
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
        if norm_status(data) in STATUS_RETRYABLE:
            log("宽限窗口内 status 翻成 %s，交回上层走失败分支。" % norm_status(data))
            return data, payload
        # 仍成功终态且仍无 md → 继续等
    log("宽限窗口超时，markdown 仍未回填，走兜底交付（exit 12）。")
    return data, payload


def _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval):
    """终态出口通用钩子：若 status==成功终态且 markdown 空，触发宽限窗口。"""
    if norm_status(data) == STATUS_OK and not extract_markdown(data):
        return _grace_wait_for_markdown(base_url, api_key, data, payload, poll_interval)
    return data, payload


def wait_for_task(base_url, api_key, data, payload, timeout_total, poll_interval=PROGRESS_POLL_INTERVAL):
    """轮询 GET 直到终态或单次超时。返回 (data, payload, exit_code)：
    终态 E_OK；单次轮询到上限 E_PENDING（非失败）。"""
    if not isinstance(data, dict):
        fail(E_FAILED, "任务响应 data 无效，无法轮询。")
    status = norm_status(data)
    task_id = get_task_id(data)
    started = time.time()
    log_task_progress(data, elapsed=0, prefix="任务已提交", emit_task_id=True)

    if status in STATUS_TERMINAL:
        data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
        return data, payload, E_OK
    if not task_id:
        fail(E_FAILED, "创建任务未返回 analysis_task_id，无法轮询进度。")

    log("开始轮询任务进度（间隔 %ds，单次最长 %ds）…" % (poll_interval, int(timeout_total)))
    while True:
        elapsed = time.time() - started
        if elapsed >= timeout_total:
            log("单次轮询到上限（%ds）：仍非终态，可续轮询。" % int(timeout_total))
            return data, payload, E_PENDING
        time.sleep(poll_interval)
        try:
            data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        except SystemExit:
            raise
        except Exception as e:
            log("轮询暂失败：%s（将继续）" % e)
            continue
        status = norm_status(data)
        log_task_progress(data, elapsed=time.time() - started, prefix="进度")
        if status in STATUS_TERMINAL:
            log("任务到达终态：status=%s task_id=%s" % (status, task_id))
            data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
            return data, payload, E_OK


# --------------------------------------------------------------------------- 结果提取与报告拼装
def extract_markdown(data):
    """从终态 data 取报告 markdown 字符串。本 API 终态取 data.result.markdown。

    兼容多形态：data.markdown / data.result.markdown / data.results.<module>.markdown。取不到返回 ""。
    """
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
    return title.replace("\n", " ").strip() or TITLE_LABEL


def assemble_report(text, markdown_sections):
    """拼最终报告 markdown。markdown_sections: [str, ...] 已剔空。"""
    parts = ["# %s：%s" % (TITLE_LABEL, make_title(text))]
    clean = [s.replace("\r\n", "\n").replace("\r", "\n").strip() for s in markdown_sections if s and s.strip()]
    if not clean:
        return parts[0] + "\n"
    return parts[0] + "\n\n" + SECTION_SEPARATOR.join(clean) + "\n"


def plan_points_for():
    return PLAN_POINTS


def handle_task_outcome(data, payload, text, out_path):
    """根据任务 status 产出报告或兜底交付。返回 (final_md, points, task_id)。
    成功终态有 md → 返回正常三元组，由调用方 _emit。
    成功终态无 md（宽限超时仍空）→ 内部组装兜底 md、_emit 落盘+stdout、sys.exit(12)（不返回）。
    可重试终态/未知 → fail(12) 不变。
    """
    task_id = get_task_id(data)
    status = norm_status(data)
    failure_message = ""
    if isinstance(data, dict):
        failure_message = data.get("error_message") or data.get("failure_message") or data.get("failure_code") or ""

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status == STATUS_OK or status in {"success", "done"}:
        md = extract_markdown(data)
        if md:
            sections = [md]
            return assemble_report(text, sections), points, task_id
        # 兜底：组装「结果暂不可用」md，落盘 + stdout，exit 12（不本地伪造真实正文）
        log("⚠️ 任务已到成功终态但 markdown 宽限后仍为空，走兜底交付（exit 12）。task_id=%s" % task_id)
        fallback_note = (
            "> ⚠️ 任务已完成（task_id=%s），但报告正文暂未从服务端返回（多为报告落库延迟）。\n"
            "> 可稍后用 `--poll-task %s --share-url \"...\"` 续查，或重新创建。\n"
            "> 本次为兜底交付：文件已落盘，但正文待补；退出码 12 表示未真正成功产出报告，请勿将本段当真实报告发布。"
        ) % (task_id, task_id)
        fallback_md = assemble_report(text, [fallback_note])
        _emit(fallback_md, points, plan_points_for(), out_path, task_id, exit_code=E_FAILED)
        return  # _emit 内 sys.exit，此处不会到达

    # 可重试终态：尽力落盘（若有 md），否则失败
    md = extract_markdown(data)
    if status in STATUS_RETRYABLE:
        detail = failure_message or status or "unknown"
        tip = "任务未成功：status=%s %s task_id=%s" % (status, detail, task_id)
        if task_id:
            tip += "。可用 --retry-task %s 重试（若服务端支持），或重新创建。" % task_id
        fail(E_FAILED, tip)
    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, failure_message or status, task_id))


# --------------------------------------------------------------------------- 本地视频上传（预签名 → 直传 → 确认）
def upload_local_video(base_url, api_key, path):
    """三步上传：取预签名 → PUT 直传文件二进制 → 确认 换 video_id。任一步失败按退出码终止。

    服务端 public-upload-url/confirm 接口需带平台 Authorization；直传到预签名地址时
    **不要**带平台 Authorization（用返回的 method + headers 直传）。
    """
    if not os.path.isfile(path):
        fail(E_PARAM, "本地视频文件不存在：%s" % path)
    ext = os.path.splitext(path)[1].lower()
    if ext not in VIDEO_EXTS:
        fail(E_PARAM, "不支持的视频格式 %s（支持 %s）" % (ext or "无扩展名", "/".join(sorted(VIDEO_EXTS))))

    size = os.path.getsize(path)
    filename = os.path.basename(path)
    if size > MAX_UPLOAD_BYTES:
        fail(E_PARAM, "本地视频过大：%.1f MB，超过上传上限 %d MB，请压缩或裁剪后重试。"
             % (size / 1024 / 1024, MAX_UPLOAD_BYTES // (1024 * 1024)))

    # 1) 取预签名
    log("取预签名上传地址：%s（%.1f MB）" % (filename, size / 1024 / 1024))
    url = base_url.rstrip("/") + PATH_UPLOAD_URL
    content_type = mimetypes.guess_type(filename)[0] or DEFAULT_UPLOAD_CONTENT_TYPE
    req_body = json.dumps({"filename": filename, "content_type": content_type, "size": size}, ensure_ascii=False)
    try:
        status, text = http_request_with_retries(url, "POST", auth_headers(api_key), req_body, HTTP_TIMEOUT, "取预签名")
    except Exception as e:
        fail(E_5XX, "取预签名失败（网络错误）：%s（请检查网络与服务可达性：%s）" % (e, base_url))
    payload = parse_json(text)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        data = {}
    raise_for_http(status, payload, text, "取预签名")
    upload_url = first_present(data, F_UPLOAD_URL_ALIASES)
    if not upload_url:
        fail(E_4XX, "取预签名失败：响应缺少 upload_url。原文=%s" % text[:200])
    method = (data.get(F_UPLOAD_METHOD) or "PUT").upper()
    put_headers = data.get(F_UPLOAD_HEADERS) or {"Content-Type": DEFAULT_UPLOAD_CONTENT_TYPE}
    upload_id = first_present(data, F_UPLOAD_ID_ALIASES)
    object_key = first_present(data, F_OBJECT_KEY_ALIASES)

    # 2) 直传文件二进制到预签名地址（不带平台 Authorization）
    log("上传文件中...")
    with open(path, "rb") as f:
        file_bytes = f.read()
    try:
        status, text = http_request_with_retries(upload_url, method, put_headers, file_bytes, 600, "上传文件", retries=3)
    except Exception as e:
        fail(E_5XX, "上传文件失败（网络错误）：%s" % e)
    if status not in (200, 201, 204):
        fail(E_5XX, "上传文件失败：HTTP %s，原文=%s" % (status, text[:200]))

    # 3) 确认上传，换 video_id
    log("确认上传完成...")
    url = base_url.rstrip("/") + PATH_UPLOAD_CONFIRM
    confirm_obj = {}
    if upload_id:
        confirm_obj[F_UPLOAD_ID] = upload_id
    if object_key:
        confirm_obj[F_OBJECT_KEY] = object_key
    if not confirm_obj:
        fail(E_FAILED, "确认上传失败：预签名响应缺少 upload_id / object_key。")
    body = json.dumps(confirm_obj, ensure_ascii=False)
    try:
        status, text = http_request_with_retries(url, "POST", auth_headers(api_key), body, HTTP_TIMEOUT, "确认上传")
    except Exception as e:
        fail(E_5XX, "确认上传失败（网络错误）：%s" % e)
    payload = parse_json(text)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        data = {}
    raise_for_http(status, payload, text, "确认上传")
    video_id = first_present(data, F_VIDEO_ID_ALIASES)
    if not video_id:
        fail(E_FAILED, "确认上传失败：响应缺少 video_id。原文=%s" % text[:200])
    log("上传完成：video_id=%s" % video_id)
    return video_id


# --------------------------------------------------------------------------- 输入解析与构造 body
def resolve_input(args, base_url, api_key):
    """解析输入分支，返回直接用于创建 body 的字段 dict。互斥校验。
    本地文件触发上传分支拿 video_id。
    """
    share = (args.share_url or "").strip()
    file_ = (args.video_file or "").strip()
    vid = (args.video_id or "").strip()
    provided = sum([bool(share), bool(file_), bool(vid)])
    if provided != 1:
        fail(E_PARAM, "请且仅提供以下输入之一：--share-url（小红书视频笔记链接）/ "
              "--video-file（本地视频文件）/ --video-id（已上传视频 id）。")

    if share:
        return {"share_url": share}
    if file_:
        video_id = upload_local_video(base_url, api_key, os.path.expanduser(file_))
        return {"video_id": video_id}
    return {"video_id": vid}


def build_body(args, input_map):
    """按 references/api.md 构造 POST 创建任务 body。
    业务可选参数（industry/campaign_type/account_size）可引导但不强制、缺省不传。
    origin/origin_method 走埋点；platform 固定忽略。
    """
    body = dict(input_map)
    for key in ("industry", "campaign_type", "account_size"):
        v = getattr(args, key, None)
        if v and str(v).strip():
            body[key] = str(v).strip()
    body.setdefault("origin", "01workbuddy")
    body.setdefault("origin_method", "skill")
    return body


def derive_title(args, task_id):
    """报告一级标题摘要：优先 --title，回退 --share-url，再回退 video 文件名，再回退「任务 <id8>」。"""
    if getattr(args, "title", None) and args.title.strip():
        return args.title.strip()
    if getattr(args, "share_url", None) and args.share_url.strip():
        return args.share_url.strip()
    if getattr(args, "video_file", None) and args.video_file.strip():
        return os.path.basename(args.video_file.strip())
    if task_id:
        return "任务 %s" % str(task_id)[:8]
    return TITLE_LABEL


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="小红书爆款短视频拆解（异步拆解 API · v0.1.0）")
    ap.add_argument("--share-url", default=None, help="小红书视频笔记链接（与 --video-file / --video-id 三选一）")
    ap.add_argument("--video-file", default=None, help="本地视频文件路径（自动走预签名上传拿 video_id；与 --share-url / --video-id 三选一）")
    ap.add_argument("--video-id", default=None, help="已上传的视频 id（与 --share-url / --video-file 三选一）")
    ap.add_argument("--industry", default=None, help="行业（可选，如 beauty）。可引导不强制、缺省不传。")
    ap.add_argument("--campaign-type", default=None, help="活动类型（可选）。可引导不强制、缺省不传。")
    ap.add_argument("--account-size", default=None, help="账号体量（可选）。可引导不强制、缺省不传。")
    ap.add_argument("--title", default=None, help="报告标题摘要；--poll-task/--retry-task 时可显式提供，否则按 --share-url 等推断")
    ap.add_argument("--out", default=None, help="输出 MD 路径；缺省写当前目录的 %s-<task_id>.md" % REPORT_LABEL)
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s，< WorkBuddy/Web 单轮上限）。到点非错误，进行中退出 13 可续轮询。" % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--idempotency-key", default=None, help="幂等键；缺省自动生成 UUID。同任务重复提交保持不变。")
    ap.add_argument("--retry-task", default=None, metavar="TASK_ID", help="对已有 task_id 调用 POST /retry，跳过输入")
    ap.add_argument("--only-create", action="store_true", help="仅 POST 创建拿 task_id 后即退（退出码 0，不轮询）")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；建议带 --share-url（或 --title）用于报告标题。终态交付(exit0)；仍运行 exit13；终态失败 exit12。")
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

    # 创建类分支需要输入；poll/retry 不需要
    needs_input = not (args.poll_task or args.retry_task)
    if needs_input and not ((args.share_url and args.share_url.strip())
                            or (args.video_file and args.video_file.strip())
                            or (args.video_id and args.video_id.strip())):
        fail(E_PARAM, "请提供 --share-url / --video-file / --video-id 之一，或使用 --poll-task <id> / --retry-task <id>。")

    # —— 轮询已有任务 ——
    if args.poll_task:
        task_id = args.poll_task.strip()
        if not task_id:
            fail(E_PARAM, "--poll-task 不能为空。")
        data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        status = norm_status(data)
        if status not in STATUS_TERMINAL:
            data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        else:
            # 已终态：若成功终态但 markdown 空，进宽限窗口（修复竞态——--poll-task 是最常用路径）
            data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
            code = E_OK
        status = norm_status(data)
        if status in STATUS_TERMINAL:
            title = derive_title(args, task_id)
            if not ((getattr(args, "title", None) and args.title.strip()) or (args.share_url and args.share_url.strip())):
                log("提示：--poll-task 未带 --share-url/--title，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --share-url（与创建时相同）。" % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(data, payload, title, args.out)
            _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
            return
        _emit_pending(data, task_id, int(args.timeout))
        return

    # —— 重试模式 ——
    if args.retry_task:
        task_id = args.retry_task.strip()
        if not task_id:
            fail(E_PARAM, "--retry-task 不能为空。")
        data, payload = call_retry_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        if code == E_PENDING:
            _emit_pending(data, task_id, int(args.timeout))
            return
        title = derive_title(args, task_id)
        final_md, used_points, task_id_out = handle_task_outcome(data, payload, title, args.out)
        _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
        return

    # —— 仅创建任务（创建后即退，不轮询）——
    if args.only_create:
        input_map = resolve_input(args, base_url, api_key)
        body = build_body(args, input_map)
        idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
        data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
        task_id = get_task_id(data)
        status = norm_status(data)
        summary = _progress_summary(data)
        print(TASK_PREFIX + task_id)
        print(STATUS_PREFIX + status)
        print(PROGRESS_PREFIX + summary)
        print(REPORT_START)
        print(REPORT_END)
        sys.stdout.flush()
        log("已创建任务（仅创建模式）：task_id=%s status=%s" % (task_id, status))
        sys.exit(E_OK)

    # —— 新建任务（创建 + 内部轮询到终态或单次超时）——
    input_map = resolve_input(args, base_url, api_key)
    body = build_body(args, input_map)
    idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
    input_desc = ("share_url=" + input_map["share_url"]) if "share_url" in input_map else ("video_id=" + input_map["video_id"])
    log("将创建任务：%s" % input_desc)
    data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
    data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
    if code == E_PENDING:
        _emit_pending(data, get_task_id(data), int(args.timeout))
        return
    title = derive_title(args, get_task_id(data))
    final_md, used_points, task_id_out = handle_task_outcome(data, payload, title, args.out)
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
    """三级兜底确保必生成 md：--out → 当前目录 <报告>-<id>.md → /tmp/<报告>-<id>.md。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / (REPORT_LABEL + ".md")
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("%s-%s.md" % (REPORT_LABEL, stem)))
    candidates.append(Path("/tmp") / ("%s-%s.md" % (REPORT_LABEL, stem)))

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
