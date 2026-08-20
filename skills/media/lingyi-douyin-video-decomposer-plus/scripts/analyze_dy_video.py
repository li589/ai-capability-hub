#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抖音爆款短视频拆解 —— 联网主脚本 (v0.1.0)

异步任务模型（视频输入）：
  读 Key → 识别输入（抖音分享链接 或 本地视频文件）→
  [本地视频] 预签名上传 → 直传 → 确认换 video_id →
  POST douyin-video-analyses（立即返回 analysis_task_id）→
  GET 轮询进度（stderr 输出）→ 终态后提取 result.markdown →
  写盘 → 分隔符协议输出 stdout。

无 /retry 接口：--retry-task <id> 不调任何 retry 路由，而是对同一 analysis_task_id
重新轮询（等价 --poll-task，不重新创建、不重复扣点）。

退出码见 SKILL.md「退出码处理」。纯标准库。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
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
TASKS_PATH = "/api/v1/social-analytics/collector/douyin-video-analyses"
UPLOAD_URL_PATH = "/api/v1/content-ops/videos/public-upload-url"
UPLOAD_CONFIRM_PATH = "/api/v1/content-ops/videos/public-upload-confirm"

DEFAULT_TIMEOUT = 90   # 单次轮询等待上限（秒）；< WorkBuddy/Web 单轮上限；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60      # 单次 HTTP 超时（创建/get/上传各步）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5
COMPLETED_REPORT_GRACE_SECONDS = 60  # 竞态宽限：终态 status 已成功但 markdown 尚未落库时，再轮询 ≤60s 等补齐

# 约定回退扣点（仅「约 N 点」提示，不当作实扣；本 API 轮询响应不含 billing 字段，运行时常空）
PLAN_POINTS = 128

# 任务态（小写判断，大小写都可能出现）
STATUS_OK = "completed"                       # 交付态
STATUS_OK_SET = frozenset({"completed", "success", "done"})  # 成功终态集合（status == STATUS_OK 的精确比较会漏 success/done）
STATUS_TERMINAL = frozenset({"completed", "success", "done", "failed", "error", "timeout"})
STATUS_RETRYABLE = frozenset({"failed", "error", "timeout"})

# 抖音输入识别
MAX_VIDEO_BYTES = 200 * 1024 * 1024  # 本地视频上传上限 200MB（服务端校验为准）
VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi")
DY_HOSTS = ("v.douyin.com", "www.douyin.com")
DEFAULT_UPLOAD_CONTENT_TYPE = "application/octet-stream"

# 调用来源埋点（脚本自动写入，对用户不可见）
ORIGIN = "01workbuddy"
ORIGIN_METHOD = "skill"

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
PREFIX = "DY_VIDEO"
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
    print("[dy_video] %s" % msg, file=sys.stderr, flush=True)


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


def first_present(data, keys):
    """从 dict 里取第一个非 None 的 key（兼容大小写/别名）。"""
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def http_request(url, method, headers, body, timeout):
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
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


# --------------------------------------------------------------------------- 输入识别（视频输入型）
def classify_input(raw):
    """识别输入：返回 ('url', share_url) / ('file', abspath) / ('none', None) /
    ('bad_file', path) / ('bad_url', url)。

    判定优先级：先看是否为存在的本地文件 → 再从文本里提取 http(s) 链接找抖音那条。
    """
    raw = (raw or "").strip()
    if not raw:
        return ("none", None)

    cand = raw
    if cand.startswith("file://"):
        cand = cand[len("file://"):]
    cand_path = os.path.expanduser(cand)
    if os.path.sep in cand or os.path.exists(cand_path):
        if os.path.isfile(cand_path):
            ext = os.path.splitext(cand_path)[1].lower()
            if ext not in VIDEO_EXTS:
                return ("bad_file", cand_path)  # 存在但不是支持的视频格式
            if os.path.getsize(cand_path) > MAX_VIDEO_BYTES:
                return ("bad_file", cand_path)  # 超过 200MB
            return ("file", os.path.abspath(cand_path))
        # 形似路径但文件不存在，且不像链接 → bad_file
        if not re.search(r"https?://", raw) and not _looks_like_douyin_host(raw):
            return ("bad_file", cand_path)

    # 从文本里提取 http(s) 链接；裸域名补 scheme
    urls = re.findall(r"https?://[^\s\"'）)>】]+", raw)
    if not urls:
        m = re.search(r"(?:v\.douyin\.com/[^\s\"'）)>】]+|www\.douyin\.com/video/[^\s\"'）)>】]+)", raw)
        if m:
            urls = ["https://" + m.group(0)]
    for u in urls:
        host = (urllib.parse.urlparse(u).hostname or "").lower()
        if host and host.endswith("douyin.com"):
            # 长链须带 /video/<id>；短链 v.douyin.com 直接放行
            if host == "www.douyin.com" and "/video/" not in u:
                return ("bad_url", u)
            return ("url", u)
        if host and host in ("v.douyin.com",):
            return ("url", u)
    # 给出了链接但非抖音
    if urls:
        return ("bad_url", urls[0])
    return ("none", None)


def _looks_like_douyin_host(text):
    return bool(re.search(r"https?://[^\s/]*(?:v\.douyin\.com|www\.douyin\.com)|(^|[^\w.])(?:v\.douyin\.com|www\.douyin\.com)", text))


# --------------------------------------------------------------------------- 本地视频上传：预签名 → 直传 → 确认
def _raw_put(url, file_bytes, timeout):
    """裸 PUT 到预签名地址：不带平台 Authorization/X-Appbuilder-From，仅 octet-stream。"""
    req = urllib.request.Request(url, data=file_bytes, method="PUT")
    req.add_header("Content-Type", DEFAULT_UPLOAD_CONTENT_TYPE)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            return status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
        except Exception:
            raw = b""
        return e.code, raw.decode("utf-8", "ignore")


def upload_local_video(base_url, api_key, path):
    """完成三步上传，返回 video_id。任一步失败按新九码退出。"""
    size = os.path.getsize(path)
    filename = os.path.basename(path)
    if size > MAX_VIDEO_BYTES:
        fail(E_PARAM, "本地视频过大：%.1f MB，超过上传上限 %d MB。请压缩或裁剪后重试。"
             % (size / 1024 / 1024, MAX_VIDEO_BYTES // (1024 * 1024)))

    # 1) 取预签名
    log("取预签名上传地址：%s（%.1f MB）" % (filename, size / 1024 / 1024))
    url = base_url.rstrip("/") + UPLOAD_URL_PATH
    content_type = mimetypes.guess_type(filename)[0] or DEFAULT_UPLOAD_CONTENT_TYPE
    req_body = json.dumps({"filename": filename, "content_type": content_type, "size": size}, ensure_ascii=False)
    try:
        status, text = http_request_with_retries(url, "POST", auth_headers(api_key), req_body, HTTP_TIMEOUT, "取预签名")
    except Exception as e:
        fail(E_5XX, "取预签名失败（网络错误）：%s" % e)
    payload = parse_json(text) or {}
    data = payload.get("data") or {}
    upload_url = first_present(data, ("upload_url", "url", "signed_url", "presigned_url"))
    if status in (401, 403):
        fail(E_AUTH, "鉴权失败（HTTP %d）：API Key 无效或已过期，请更新 config.json 的 LY_API_KEY。服务端：%s"
             % (status, payload.get("message") or text[:200]))
    if status >= 500:
        fail(E_5XX, "取预签名服务端错误（HTTP %s）：%s" % (status, payload.get("message") or text[:200]))
    if status not in (200, 201) or not upload_url:
        fail(E_4XX, "取预签名失败：HTTP %s，message=%s，原文=%s" % (status, payload.get("message"), text[:200]))

    method = (data.get("method") or "PUT").upper()
    upload_id = first_present(data, ("upload_id", "uploadId"))
    object_key = first_present(data, ("object_key", "objectKey", "key"))
    if method != "PUT":
        fail(E_5XX, "取预签名返回不支持的 method=%s，当前仅支持 PUT 直传。" % method)

    # 2) 直传文件字节（不带平台鉴权）
    log("上传文件中（%.1f MB）..." % (size / 1024 / 1024))
    with open(path, "rb") as f:
        file_bytes = f.read()
    last_err = None
    for attempt in range(1, 4):
        try:
            up_status, up_text = _raw_put(upload_url, file_bytes, 600)
            if up_status in (200, 201, 204):
                break
            if up_status >= 500 and attempt < 3:
                wait = min(2 ** (attempt - 1), MAX_BACKOFF)
                log("上传服务端 %s，%ds 后重试（%d/3）" % (up_status, wait, attempt))
                time.sleep(wait)
                continue
            fail(E_4XX if up_status < 500 else E_5XX,
                 "上传文件失败：HTTP %s，原文=%s" % (up_status, up_text[:200]))
        except urllib.error.URLError as e:
            last_err = e
            if attempt >= 3:
                fail(E_5XX, "上传文件失败（网络错误）：%s" % e)
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("上传文件网络错误：%s，%ds 后重试（%d/3）" % (e, wait, attempt))
            time.sleep(wait)
    else:
        fail(E_5XX, "上传文件失败：%s" % last_err)

    # 3) 确认上传，换 video_id（成功 HTTP 201）
    log("确认上传完成...")
    url = base_url.rstrip("/") + UPLOAD_CONFIRM_PATH
    confirm_obj = {"upload_id": upload_id} if upload_id else {}
    if object_key:
        confirm_obj["object_key"] = object_key
    body = json.dumps(confirm_obj or {"object_key": object_key}, ensure_ascii=False)
    try:
        status, text = http_request_with_retries(url, "POST", auth_headers(api_key), body, HTTP_TIMEOUT, "确认上传")
    except Exception as e:
        fail(E_5XX, "确认上传失败（网络错误）：%s" % e)
    payload = parse_json(text) or {}
    confirm_data = payload.get("data") or {}
    video_id = first_present(confirm_data, ("video_id", "videoId", "id"))
    if status in (401, 403):
        fail(E_AUTH, "鉴权失败（HTTP %d）：API Key 无效或已过期。服务端：%s"
             % (status, payload.get("message") or text[:200]))
    if status >= 500:
        fail(E_5XX, "确认上传服务端错误（HTTP %s）：%s" % (status, payload.get("message") or text[:200]))
    if status not in (200, 201) or not video_id:
        fail(E_4XX if status < 500 else E_5XX,
             "确认上传失败：HTTP %s，message=%s，原文=%s" % (status, payload.get("message"), text[:200]))

    log("上传完成：video_id=%s" % video_id)
    return video_id


# --------------------------------------------------------------------------- 扣点提取
def extract_total_points(payload):
    """本 API 轮询响应不含 billing 字段，通常返回 None（由调用方按约 128 回退）。
    仍保留对 data.billing.total_points 及历史候选 key 的探测，命中即报数。"""
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
        if recharge:
            tip += " 请前往充值：%s" % recharge
        fail(E_BALANCE, tip)
    if status in (400, 422):
        fail(E_PARAM, "%s参数/校验失败（HTTP %s）：%s" % (label, status, msg))
    if status == 403:
        fail(E_4XX, "%s无权访问（HTTP 403）：可能用了不同平台的 Key 或查了跨平台任务。服务端：%s" % (label, msg))
    if status == 404:
        fail(E_4XX, "%s任务不存在（HTTP 404）：%s" % (label, msg))
    if 400 <= status < 500:
        fail(E_4XX, "%s调用失败（HTTP %s）：%s" % (label, status, msg))
    if status >= 500:
        fail(E_5XX, "%s服务端错误（HTTP %s）：%s" % (label, status, msg or "Internal server error"))


# --------------------------------------------------------------------------- 调任务 API
def _tid(data):
    """统一取任务 id：本 API 是 analysis_task_id（兼容通用 task_id）。"""
    if not isinstance(data, dict):
        return ""
    return str(data.get("analysis_task_id") or data.get("task_id") or "")


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
    """从任务 data 汇总人类可读进度文案。抖音字段：current_stage / progress_message（均 nullable）。"""
    if not isinstance(data, dict):
        return "等待调度"
    pmsg = data.get("progress_message")
    if pmsg:
        return str(pmsg)
    stage = data.get("current_stage")
    if stage:
        return "当前：%s" % stage
    status = str(data.get("status") or "")
    if status:
        return "status=%s 等待调度" % status
    return "等待调度"


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    task_id = _tid(data)
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s%s task_id=%s | %s" % (prefix, status or "?", elapsed_s, task_id or "-", summary))
    if emit_task_id and task_id:
        print("[dy_video] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, body_obj, idempotency_key, timeout, label="创建拆解任务"):
    url = base_url.rstrip("/") + TASKS_PATH
    body_obj = dict(body_obj)
    body_obj.setdefault("idempotency_key", idempotency_key)
    body = json.dumps(body_obj, ensure_ascii=False)
    log("%s：key=%s" % (label, (idempotency_key or "")[:8] + "…"))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key, idempotency_key), body, timeout, label)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s（请检查网络与服务可达性：%s）" % (label, e, base_url))
    return _parse_task_response(status, resp_text, label)


def call_get_task(base_url, api_key, task_id, timeout, label="查询拆解任务"):
    url = base_url.rstrip("/") + TASKS_PATH + "/" + urllib.parse.quote(str(task_id), safe="")
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def _grace_wait_for_markdown(base_url, api_key, data, payload, poll_interval):
    """竞态宽限：status 已到成功终态但 markdown 尚未回填时，在 COMPLETED_REPORT_GRACE_SECONDS 内继续轮询。

    返回 (data, payload)，可能更新为带 markdown 的，也可能原样返回（宽限超时仍空）。
    中途 status 翻成可重试终态 → 返回新 data，交上层走失败分支。网络错误 continue 继续。
    判空统一用 `not extract_markdown(data)`。
    """
    task_id = _tid(data)
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
        if str(data.get("status") or "") in STATUS_RETRYABLE:
            log("宽限窗口内 status 翻成 %s，交回上层走失败分支。" % data.get("status"))
            return data, payload
    log("宽限窗口超时，markdown 仍未回填，走兜底交付（exit 12）。")
    return data, payload


def _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval):
    """终态出口通用钩子：若 status 属成功终态集且 markdown 空，触发宽限窗口。"""
    status = str(data.get("status") or "")
    if status in STATUS_OK_SET and not extract_markdown(data):
        return _grace_wait_for_markdown(base_url, api_key, data, payload, poll_interval)
    return data, payload


def wait_for_task(base_url, api_key, data, payload, timeout_total, poll_interval=PROGRESS_POLL_INTERVAL):
    """轮询 GET 直到终态或单次超时。返回 (data, payload, exit_code)：
    终态 E_OK；单次轮询到上限 E_PENDING（非失败）。"""
    if not isinstance(data, dict):
        fail(E_FAILED, "任务响应 data 无效，无法轮询。")
    status = str(data.get("status") or "")
    task_id = _tid(data)
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
        status = str(data.get("status") or "")
        log_task_progress(data, elapsed=time.time() - started, prefix="进度")
        if status in STATUS_TERMINAL:
            log("任务到达终态：status=%s task_id=%s" % (status, task_id))
            data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
            return data, payload, E_OK


# --------------------------------------------------------------------------- 结果提取与报告拼装
def extract_markdown(data):
    """从终态 data 取报告 markdown。抖音取 data.result.markdown（单一报告）。
    取不到返回 ""。"""
    if not isinstance(data, dict):
        return ""
    mk = data.get("markdown")
    result = data.get("result") if isinstance(data.get("result"), dict) else None
    if not mk and isinstance(result, dict):
        mk = result.get("markdown")
    if mk:
        return str(mk).strip()

    # 多模块分支（本 API 不出现，保留为兼容兜底）
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
    return title.replace("\n", " ").strip() or "抖音视频拆解报告"


def assemble_report(text, markdown_sections):
    """拼最终报告 markdown。markdown_sections: [str, ...] 已剔空。"""
    parts = ["# 抖音视频拆解报告：%s" % make_title(text)]
    clean = [s.replace("\r\n", "\n").replace("\r", "\n").strip() for s in markdown_sections if s and s.strip()]
    if not clean:
        return parts[0] + "\n"
    return parts[0] + "\n\n" + SECTION_SEPARATOR.join(clean) + "\n"


def plan_points_for():
    return PLAN_POINTS


def handle_task_outcome(data, payload, text, out_path):
    """根据任务 status 产出报告或兜底交付。返回 (final_md, points, task_id)。
    成功终态有 md → 返回正常三元组，由调用方 _emit。
    成功终态无 md（宽限超时仍空）→ 组装兜底 md、_emit 落盘+stdout、sys.exit(12)。
    可重试终态/未知 → fail(12) 不变。"""
    task_id = _tid(data)
    status = str(data.get("status") or "")
    failure_message = (data.get("error_message") or data.get("failure_message")
                       or data.get("failure_code") or "")

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status in STATUS_OK_SET:
        md = extract_markdown(data)
        if md:
            return assemble_report(text, [md]), points, task_id
        # 兜底：组装「结果暂不可用」md，落盘 + stdout，exit 12（不本地伪造真实正文）
        log("⚠️ 任务已到成功终态但 markdown 宽限后仍为空，走兜底交付（exit 12）。task_id=%s" % task_id)
        fallback_note = (
            "> ⚠️ 任务已完成（task_id=%s），但报告正文暂未从服务端返回（多为报告落库延迟）。\n"
            "> 可稍后用 `--poll-task %s --input \"...\"` 续查，或 `--retry-task %s` 重新轮询；\n"
            "> 仍未返回则重新发起一次拆解（新任务、重新扣点）。\n"
            "> 本次为兜底交付：文件已落盘，但正文待补；退出码 12 表示未真正成功产出报告，请勿将本段当真实报告发布。"
        ) % (task_id, task_id, task_id)
        fallback_md = assemble_report(text, [fallback_note])
        _emit(fallback_md, points, plan_points_for(), out_path, task_id, exit_code=E_FAILED)
        return  # _emit 内 sys.exit，此处不会到达

    md = extract_markdown(data)
    if md and status == "partial_failed":
        log("任务部分失败 status=%s，仍交付已有结果。failure=%s" % (status, failure_message))
        return assemble_report(text, [md]), points, task_id

    detail = failure_message or status or "unknown"
    if status == "billing_failed":
        fail(E_FAILED, "模块已完成但扣点失败：%s task_id=%s（请稍后重试或联系支持）" % (detail, task_id))
    if status in STATUS_RETRYABLE:
        tip = "任务未成功：status=%s %s task_id=%s" % (status, detail, task_id)
        if task_id:
            tip += "。可用 --retry-task %s 重新轮询续查；真重试请重新发起（新任务、重新扣点）。" % task_id
        fail(E_FAILED, tip)
    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, detail, task_id))


# --------------------------------------------------------------------------- main
def build_body(args, source_kind, source_value):
    """构造 POST 创建拆解任务 body。share_url 与 video_id 二选一必填。"""
    body = {}
    if source_kind == "url":
        body["share_url"] = source_value
    elif source_kind == "file":
        body["video_id"] = source_value  # 来自 upload_local_video
    else:
        fail(E_PARAM, "无效的输入来源：%s" % source_kind)
    body["origin"] = ORIGIN
    body["origin_method"] = ORIGIN_METHOD
    # 可选业务参数：可引导但不强制、缺省不传
    if getattr(args, "industry", None):
        body["industry"] = args.industry
    if getattr(args, "campaign_type", None):
        body["campaign_type"] = args.campaign_type
    if getattr(args, "account_size", None):
        body["account_size"] = args.account_size
    return body


def _resolve_input(args):
    """分类 --input，返回 (source_kind, source_value, title_seed)。
    本地文件已上传换 video_id（source_value=video_id, source_kind='file'）。"""
    raw = (args.input or "").strip()
    kind, value = classify_input(raw)
    if kind == "none":
        fail(E_PARAM, "未识别到有效输入：请提供抖音分享链接，或本地视频文件路径。")
    if kind == "bad_file":
        if not os.path.exists(value):
            fail(E_PARAM, "本地文件不存在：%s" % value)
        ext = os.path.splitext(value)[1].lower()
        if ext and ext not in VIDEO_EXTS:
            fail(E_PARAM, "不支持的视频格式：%s（支持 %s）" % (ext or "无扩展名", "/".join(VIDEO_EXTS)))
        fail(E_PARAM, "本地视频过大（超过 %dMB），请压缩或裁剪后重试：%s"
             % (MAX_VIDEO_BYTES // (1024 * 1024), value))
    if kind == "bad_url":
        fail(E_PARAM, "仅支持抖音视频链接（v.douyin.com 短链或 www.douyin.com/video/<id> 长链），收到的非抖音链接：%s" % value)

    if kind == "file":
        base_url = os.environ.get("LY_BASE_URL", BASE_URL)
        api_key = get_api_key()
        video_id = upload_local_video(base_url, api_key, value)
        return ("file", video_id, value)  # title seed 用原始路径

    return ("url", value, value)


def main():
    ap = argparse.ArgumentParser(description="抖音爆款短视频拆解（异步任务 API · v0.1.0）")
    ap.add_argument("--input", default=None,
                    help="抖音分享链接，或本地视频文件路径（创建/仅创建时必填；轮询时作报告标题种子）")
    ap.add_argument("--out", default=None, help="输出 MD 路径；缺省写当前目录的 抖音视频拆解报告-<task_id>.md")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s，< WorkBuddy/Web 单轮上限）。到点非错误，进行中退出 13 可续轮询。" % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--idempotency-key", default=None, help="幂等键；缺省自动生成 UUID。重复提交同一任务请保持不变。")
    ap.add_argument("--retry-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 重新轮询（本接口无 /retry，不重新创建、不重复扣点）。需带 --input 作标题种子。")
    ap.add_argument("--only-create", action="store_true", help="仅 POST 创建拿 analysis_task_id 后即退（退出码 0，不轮询）")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；务必带 --input（用于报告标题）。终态交付(exit0)；仍运行 exit13；终态失败 exit12。")
    # 可选业务参数
    ap.add_argument("--industry", default=None, help="行业（可选，如 beauty；缺省不传）")
    ap.add_argument("--campaign-type", default=None, help="活动类型（可选；缺省不传）")
    ap.add_argument("--account-size", default=None, help="账号体量（可选；缺省不传）")
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
            # 已终态：若成功终态但 markdown 空，进宽限窗口（修复竞态——--poll-task 是最常用路径）
            data, payload = _maybe_grace_for_completed(base_url, api_key, data, payload, poll_interval)
            code = E_OK
        status = str(data.get("status") or "")
        if status in STATUS_TERMINAL:
            title_seed = (args.input and args.input.strip()) or ("任务 %s" % task_id[:8])
            if not (args.input and args.input.strip()):
                log("提示：--poll-task 未带 --input，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --input。" % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(data, payload, title_seed, args.out)
            _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
            return
        _emit_pending(data, task_id, int(args.timeout))
        return

    # —— 重试模式（= 对同 task_id 重新轮询，不调 /retry、不重新创建、不重复扣点）——
    if args.retry_task:
        task_id = args.retry_task.strip()
        if not task_id:
            fail(E_PARAM, "--retry-task 不能为空。")
        log("重新轮询已有任务（本接口无 /retry，仅续轮询，不重新创建、不重复扣点）：task_id=%s" % task_id)
        data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        if code == E_PENDING:
            _emit_pending(data, task_id, int(args.timeout))
            return
        title_seed = (args.input and args.input.strip()) or ("任务 %s" % task_id[:8])
        if not (args.input and args.input.strip()):
            log("提示：--retry-task 未带 --input，报告标题退化为「任务 %s」。建议 --retry-task 同时带 --input。" % task_id[:8])
        final_md, used_points, task_id_out = handle_task_outcome(data, payload, title_seed, args.out)
        _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
        return

    # —— 仅创建任务（创建后即退，不轮询）——
    if args.only_create:
        if not args.input:
            fail(E_PARAM, "--only-create 仍需 --input 提供抖音分享链接或本地视频路径。")
        source_kind, source_value, title_seed = _resolve_input(args)
        body = build_body(args, source_kind, source_value)
        idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
        data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
        task_id = _tid(data)
        # 创建响应无 status 字段，合成 pending 透出
        status = "pending"
        summary = "已受理，等待调度"
        print(TASK_PREFIX + task_id)
        print(STATUS_PREFIX + status)
        print(PROGRESS_PREFIX + summary)
        print(REPORT_START)
        print(REPORT_END)
        sys.stdout.flush()
        log("已创建任务（仅创建模式）：task_id=%s status=%s" % (task_id, status))
        sys.exit(E_OK)

    # —— 新建任务（一把梭：创建后内部轮询到终态；Web 端易被打断，慎用）——
    if not args.input:
        fail(E_PARAM, "请提供 --input，或使用 --retry-task <task_id> 或 --poll-task <task_id>。")
    source_kind, source_value, title_seed = _resolve_input(args)
    body = build_body(args, source_kind, source_value)
    idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
    log("将创建拆解任务：source=%s" % (source_value if source_kind == "url" else "video_id=" + source_value))
    data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
    data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
    if code == E_PENDING:
        _emit_pending(data, _tid(data), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(data, payload, title_seed, args.out)
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
    """三级兜底确保必生成 md：--out → 当前目录 抖音视频拆解报告-<id>.md → /tmp/抖音视频拆解报告-<id>.md。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "抖音视频拆解报告.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("抖音视频拆解报告-%s.md" % stem))
    candidates.append(Path("/tmp") / ("抖音视频拆解报告-%s.md" % stem))

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
