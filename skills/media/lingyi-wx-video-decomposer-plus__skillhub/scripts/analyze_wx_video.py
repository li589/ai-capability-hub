#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号视频拆解分析编排脚本。

接收一条视频号分享链接 **或** 一个本地视频文件路径，自动完成：
  本地视频 → 预签名上传 → 确认 → 拿 video_id
  → 发起拆解（share_url 或 video_id 二选一）
  → 轮询进度 → 输出报告

进度打到 stderr 供调用方（assistant）转述，最终报告用分隔符包裹打到 stdout。
纯标准库实现（urllib），无第三方依赖。

用法：
    python3 analyze_wx_video.py <share_url 或 本地视频路径> \
        [--out PATH] [--max-wait 600] [--interval 4]
    python3 analyze_wx_video.py --task-id <id> [--out PATH] [--max-wait 600]

API Key：
    自动从「技能目录」下的 config.json 的 LY_API_KEY 字段读取
    （技能目录 = scripts/ 的上一级，即 SKILL.md 所在目录）。
    兼容环境变量 LY_API_KEY 作为回退。
    请求头 Authorization: <api_key>（无 Bearer）。

base url 默认 https://claw.lingyishuke.com/services（写死在脚本里）。

退出码：
    0   成功，报告已输出
    2   输入错误（未给输入 / 本地文件不存在或非视频格式）
    3   未取到 API Key 或鉴权失效（401/403）
    4   发起拆解失败（含余额不足，附充值链接）
    5   任务失败（status=FAILED）
    6   轮询网络 / 429 终态错误，或 404 任务失效
    7   COMPLETED 但报告为空
    9   本地视频上传失败（取预签名 / 上传 / 确认任一步）
    124 等待超时

============================================================================
接口契约 —— 与 references/api.md 一一对应
----------------------------------------------------------------------------
请求体、响应字段名集中在下方常量区维护，后端契约变动时改这一处即可。
============================================================================
"""

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

# 固定 base url。
BASE_URL = "https://claw.lingyishuke.com/services"

# --- 接口路径 --------------------------------------------------------------
PATH_UPLOAD_URL = "/api/v1/content-ops/videos/public-upload-url"
PATH_UPLOAD_CONFIRM = "/api/v1/content-ops/videos/public-upload-confirm"
PATH_TEARDOWN = "/api/v1/social-analytics/collector/wx-video-analyses"
PATH_STATUS = "/api/v1/social-analytics/collector/wx-video-analyses/{task_id}"

# --- 请求/响应字段名 -------------------------------------------------------
# 预签名上传响应里取上传地址等信息的 key
F_UPLOAD_URL = "upload_url"
F_UPLOAD_URL_ALIASES = ("upload_url", "uploadUrl", "url", "signed_url", "signedUrl", "presigned_url", "presignedUrl")
F_UPLOAD_METHOD = "method"        # 默认 PUT
F_UPLOAD_HEADERS = "headers"
F_UPLOAD_ID = "upload_id"
F_UPLOAD_ID_ALIASES = ("upload_id", "uploadId")
F_OBJECT_KEY = "object_key"
F_OBJECT_KEY_ALIASES = ("object_key", "objectKey", "key", "file_key", "fileKey", "path")
# 确认上传响应里取 video_id 的 key
F_VIDEO_ID = "video_id"
F_VIDEO_ID_ALIASES = ("video_id", "videoId", "id")
F_VIDEO_URL_ALIASES = ("video_url", "videoUrl", "file_url", "fileUrl", "url")
# 发起拆解响应里取任务 id 的 key
F_TASK_ID = "analysis_task_id"
F_TASK_ID_ALIASES = ("analysis_task_id", "analysisTaskId", "task_id", "taskId", "content_ops_task_id", "contentOpsTaskId")
# 余额不足判定 + 充值链接 key
F_RECHARGE_URL = "recharge_url"
# 本次实际扣点的高置信字段（命中才直接报数，否则交由调用方按 ≈128 估算）
F_POINTS_USED = ("points_used", "credits_used", "used_points", "deducted_points",
                 "charged_points", "points_cost", "point_used", "consumed_points",
                 "billing_points", "spent_points", "cost_points")

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 本地视频上传上限 100MB，超过直接拒绝
DEFAULT_UPLOAD_CONTENT_TYPE = "application/octet-stream"

DEFAULT_MAX_WAIT = 600
DEFAULT_INTERVAL = 4
MAX_BACKOFF = 30
POLL_RETRY_TIMES = 4
HTTP_RETRY_TIMES = 4
# 服务端有时先置 COMPLETED，过几秒才写入 result.markdown；命中此竞态时
# 在该宽限窗口内继续轮询，等报告落库，避免误报"完成但报告为空"。
COMPLETED_REPORT_GRACE_SECONDS = 60

# urllib 默认用系统/编译期证书链做校验。设环境变量 LY_SKIP_SSL_VERIFY=1 可跳过
# （仅用于 macOS 缺证书、企业代理中间人等无法正常校验的环境）。
if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()

REPORT_START = "=== WX_VIDEO_REPORT_START ==="
REPORT_END = "=== WX_VIDEO_REPORT_END ==="

STATUS_LABEL = {
    "QUEUED": "排队中",
    "PENDING": "等待中",
    "PROCESSING_MEDIA": "素材处理中",
    "ANALYZING": "LLM 拆解中",
    "UPLOADING": "上传中",
    "GENERATING_REPORT": "生成报告中",
    "COMPLETED": "完成",
    "FAILED": "失败",
    "SUCCESS": "完成",
    "DONE": "完成",
    "ERROR": "失败",
}

COMPLETED_STATUSES = {"COMPLETED", "SUCCESS", "DONE"}
FAILED_STATUSES = {"FAILED", "ERROR"}

WX_HOST = "weixin.qq.com"


def log(*args, **kwargs):
    """进度/错误信息打到 stderr，避免污染 stdout 报告区。"""
    print(*args, file=sys.stderr, flush=True, **kwargs)


def fail(code, message):
    log(message)
    sys.exit(code)


def get_api_key():
    """从技能目录下的 config.json 读取 LY_API_KEY 字段，回退到环境变量 LY_API_KEY。

    技能目录 = 本脚本所在 scripts/ 的上一级目录（SKILL.md 与 config.json 所在处）。
    """
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(skill_dir, "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            log("⚠️ config.json 顶层应为 JSON 对象（如 {\"LY_API_KEY\": \"...\"}），当前不是对象：%s" % config_path)
        else:
            key = str(data.get("LY_API_KEY") or "").strip()
            if key:
                return key
    except json.JSONDecodeError:
        log("⚠️ config.json JSON 格式错误，请检查语法（如引号、逗号）：%s" % config_path)
    except OSError:
        pass
    return (os.environ.get("LY_API_KEY") or "").strip()


def auth_headers(api_key, with_json=False):
    """Authorization: <api_key>（裸 key，不带 Bearer）+ X-Appbuilder-From: openclaw。"""
    headers = {"Authorization": api_key, "X-Appbuilder-From": "openclaw"}
    if with_json:
        headers["Content-Type"] = "application/json"
    return headers


def parse_json(text):
    try:
        return json.loads(text)
    except ValueError:
        return None


def first_present(data, keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def extract_points(payload):
    """从响应里提取本次实际扣点。

    只认 F_POINTS_USED 这类明确表示「已用点数」的字段，找不到返回 None（不猜数，
    由调用方按约 128 点回退，避免向付费用户报错误数字）。在 payload 自身及
    data / data.billing / data.result / data.payment / data.usage / billing 等层级查找。
    """
    if not isinstance(payload, dict):
        return None
    levels = [payload]
    inner = payload.get("data")
    if isinstance(inner, dict):
        levels.append(inner)
        for sub in ("billing", "result", "payment", "cost", "usage"):
            sub_obj = inner.get(sub)
            if isinstance(sub_obj, dict):
                levels.append(sub_obj)
    for sub in ("billing", "payment", "cost", "usage"):
        sub_obj = payload.get(sub)
        if isinstance(sub_obj, dict):
            levels.append(sub_obj)
    for level in levels:
        for key in F_POINTS_USED:
            if key in level:
                val = level[key]
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    return val
    return None


def http_request(method, url, headers=None, body=None, timeout=60):
    """发起一次 HTTP 请求，返回 (status, body_text)。URLError 上抛由调用方决定重试。"""
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def http_request_with_retries(method, url, headers=None, body=None, timeout=60,
                              retry_label="请求", retries=HTTP_RETRY_TIMES):
    """对瞬时网络错误做有限重试；HTTP 状态码由调用方判断。"""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return http_request(method, url, headers=headers, body=body, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            if attempt >= retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s网络错误：%s，%ds 后重试（%d/%d）" %
                (retry_label, e, wait, attempt, retries))
            time.sleep(wait)
    raise last_err


# ---------------------------------------------------------------------------
# 输入识别：视频号链接 vs 本地视频文件
# ---------------------------------------------------------------------------

def classify_input(raw):
    """返回 ('url', share_url) / ('file', abspath) / ('none', None) / ('bad_file', path)。

    判定优先级：先看是否为存在的本地文件 → 再从文本提取视频号链接。
    """
    raw = (raw or "").strip()
    if not raw:
        return ("none", None)

    # 本地文件：去掉可能的 file:// 前缀和首尾引号
    cand = raw
    if cand.startswith("file://"):
        cand = cand[len("file://"):]
    cand_path = os.path.expanduser(cand)
    if os.path.sep in cand or os.path.exists(cand_path):
        if os.path.isfile(cand_path):
            ext = os.path.splitext(cand_path)[1].lower()
            if ext in VIDEO_EXTS:
                return ("file", os.path.abspath(cand_path))
            return ("bad_file", cand_path)  # 存在但不是视频格式
        # 看起来像路径但文件不存在
        if not re.search(r"https?://", raw):
            # 排除裸域名/缺协议头的视频号链接（如 weixin.qq.com/sph/xxx）
            if not _looks_like_wx_host(raw):
                return ("bad_file", cand_path)

    # 从文本中提取 http(s) 链接，找视频号那条；裸域名也补 scheme 后尝试
    urls = re.findall(r"https?://[^\s\"'）)】>]+", raw)
    if not urls:
        m = re.search(r"(?:weixin\.qq\.com/[^\s\"'）)】>]+)", raw)
        if m:
            urls = ["https://" + m.group(0)]
    for u in urls:
        host = urllib.parse.urlparse(u).hostname
        if host and host.endswith(WX_HOST):
            return ("url", u)
    return ("none", None)


def _looks_like_wx_host(text):
    """文本中是否出现视频号 host（容忍无 scheme 的裸域名）。"""
    return bool(re.search(r"https?://[^\s/]*weixin\.qq\.com|(^|[^\w.])weixin\.qq\.com", text))


# ---------------------------------------------------------------------------
# 本地视频上传：预签名 → 直传 → 确认
# ---------------------------------------------------------------------------

def upload_local_video(base_url, api_key, path):
    """完成三步上传，返回 video_id。任一步失败以退出码 9 终止。"""
    size = os.path.getsize(path)
    filename = os.path.basename(path)
    if size > MAX_UPLOAD_BYTES:
        fail(2, "本地视频过大：%.1f MB，超过上传上限 %d MB。请压缩或裁剪后重试。"
             % (size / 1024 / 1024, MAX_UPLOAD_BYTES // (1024 * 1024)))

    # 1) 取预签名
    log("取预签名上传地址：%s（%.1f MB）" % (filename, size / 1024 / 1024))
    url = base_url.rstrip("/") + PATH_UPLOAD_URL
    content_type = mimetypes.guess_type(filename)[0] or DEFAULT_UPLOAD_CONTENT_TYPE
    body = json.dumps({"filename": filename, "content_type": content_type, "size": size},
                      ensure_ascii=False)
    try:
        status, text = http_request_with_retries("POST", url, headers=auth_headers(api_key, True),
                                                 body=body, retry_label="取预签名")
    except urllib.error.URLError as e:
        fail(9, "取预签名失败（网络错误）：%s" % e)
    if status in (401, 403):
        payload = parse_json(text) or {}
        fail(3, "鉴权失败（HTTP %d）：API Key 无效或已过期，请更新 config.json 中的 LY_API_KEY 后重试。"
            "服务端返回：%s" % (status, payload.get("message") or text[:200]))
    payload = parse_json(text) or {}
    data = payload.get("data") or {}
    upload_url = first_present(data, F_UPLOAD_URL_ALIASES)
    if status != 200 or not upload_url:
        fail(9, "取预签名失败：HTTP %s，message=%s，原文=%s" % (status, payload.get("message"), text[:200]))
    method = (data.get(F_UPLOAD_METHOD) or "PUT").upper()
    put_headers = data.get(F_UPLOAD_HEADERS) or {"Content-Type": DEFAULT_UPLOAD_CONTENT_TYPE}
    upload_id = first_present(data, F_UPLOAD_ID_ALIASES)
    object_key = first_present(data, F_OBJECT_KEY_ALIASES)
    presigned_file_url = first_present(data, F_VIDEO_URL_ALIASES)

    # 2) 直传文件字节到 OSS（不带平台 Authorization）
    log("上传文件中...")
    with open(path, "rb") as f:
        file_bytes = f.read()
    try:
        status, text = http_request_with_retries(method, upload_url, headers=put_headers, body=file_bytes,
                                                 timeout=600, retry_label="上传文件", retries=3)
    except urllib.error.URLError as e:
        fail(9, "上传文件失败（网络错误）：%s" % e)
    if status not in (200, 201, 204):
        fail(9, "上传文件失败：HTTP %s，原文=%s" % (status, text[:200]))

    # 3) 确认上传，换 video_id
    log("确认上传完成...")
    url = base_url.rstrip("/") + PATH_UPLOAD_CONFIRM
    confirm_obj = {}
    if upload_id:
        confirm_obj[F_UPLOAD_ID] = upload_id
    if object_key:
        confirm_obj[F_OBJECT_KEY] = object_key
    body = json.dumps(confirm_obj or {F_OBJECT_KEY: object_key}, ensure_ascii=False)
    try:
        status, text = http_request_with_retries("POST", url, headers=auth_headers(api_key, True),
                                                 body=body, retry_label="确认上传")
    except urllib.error.URLError as e:
        fail(9, "确认上传失败（网络错误）：%s" % e)
    payload = parse_json(text) or {}
    confirm_data = payload.get("data") or {}
    video_id = first_present(confirm_data, F_VIDEO_ID_ALIASES)
    video_url = first_present(confirm_data, F_VIDEO_URL_ALIASES) or presigned_file_url
    if status not in (200, 201) or not video_id:
        fail(9, "确认上传失败：HTTP %s，message=%s，原文=%s" % (status, payload.get("message"), text[:200]))

    log("上传完成：video_id=%s" % video_id)
    if video_url:
        log("上传后视频链接：%s" % video_url)
    return video_id


# ---------------------------------------------------------------------------
# 发起拆解
# ---------------------------------------------------------------------------

def create_task(base_url, api_key, share_url=None, video_id=None):
    """发起拆解任务，返回 task_id。失败按退出码终止。"""
    url = base_url.rstrip("/") + PATH_TEARDOWN
    body_obj = {"origin": "workbuddy", "origin_method": "skill"}
    if share_url:
        body_obj["share_url"] = share_url
    if video_id:
        body_obj["video_id"] = video_id
    body = json.dumps(body_obj, ensure_ascii=False)

    log("发起拆解任务：%s" % (share_url or ("video_id=" + video_id)))
    status = None
    text = ""
    for attempt in range(1, HTTP_RETRY_TIMES + 1):
        try:
            status, text = http_request("POST", url, headers=auth_headers(api_key, True),
                                        body=body, timeout=60)
        except urllib.error.URLError as e:
            if attempt >= HTTP_RETRY_TIMES:
                fail(6, "发起拆解网络错误：%s（请检查网络与服务可达性：%s）" % (e, base_url))
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("发起拆解网络错误：%s，%ds 后重试（%d/%d）" % (e, wait, attempt, HTTP_RETRY_TIMES))
            time.sleep(wait)
            continue
        if status >= 500:
            if attempt >= HTTP_RETRY_TIMES:
                fail(6, "发起拆解服务端暂时不可用（HTTP %d），已重试 %d 次仍失败，请稍后重试。"
                    % (status, HTTP_RETRY_TIMES))
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("发起拆解服务端错误 HTTP %d，%ds 后重试（%d/%d）" % (status, wait, attempt, HTTP_RETRY_TIMES))
            time.sleep(wait)
            continue
        break

    if status in (401, 403):
        payload = parse_json(text) or {}
        fail(3, "鉴权失败（HTTP %d）。API Key 无效或已过期，请更新 config.json 中的 LY_API_KEY 后重试。"
                "服务端返回：%s" % (status, payload.get("message") or text[:200]))

    payload = parse_json(text)
    if payload is None:
        fail(4, "发起拆解返回非 JSON（HTTP %d）：%s" % (status, text[:200]))

    # 余额不足：402 或 message 命中关键词
    data = payload.get("data") or {}
    msg = payload.get("message") or ""
    detail = payload.get("detail")
    trace_id = payload.get("trace_id")
    recharge = data.get(F_RECHARGE_URL)
    if status == 402 or "余额不足" in msg or recharge:
        tip = "余额不足，无法发起拆解。"
        if recharge:
            tip += " 请前往充值：%s" % recharge
        fail(4, tip)

    if status not in (200, 201) or payload.get("result") != "success":
        extra = ""
        if detail:
            extra += "，detail=%s" % detail
        if trace_id:
            extra += "，trace_id=%s" % trace_id
        fail(4, "发起拆解失败：HTTP %s，result=%s，message=%s%s"
             % (status, payload.get("result"), msg, extra))

    task_id = first_present(data, F_TASK_ID_ALIASES)
    if not task_id:
        fail(4, "发起拆解成功但缺少任务 id（key=%s）：%s" % (F_TASK_ID, text[:300]))
    points = extract_points(payload)
    log("任务已创建：task_id=%s" % task_id)
    return task_id, points


# ---------------------------------------------------------------------------
# 轮询
# ---------------------------------------------------------------------------

class RetryableError(Exception):
    pass


def poll_once(base_url, api_key, task_id):
    """轮询一次状态，返回 data dict；失败抛 RetryableError 由调用方重试/终止。"""
    encoded_task_id = urllib.parse.quote(str(task_id), safe="")
    url = base_url.rstrip("/") + PATH_STATUS.format(task_id=encoded_task_id)
    status, text = http_request("GET", url, headers=auth_headers(api_key), timeout=30)
    if status in (401, 403):
        payload = parse_json(text) or {}
        fail(3, "鉴权失败（HTTP %d）：API Key 无效或已过期，请更新 config.json 中的 LY_API_KEY 后重试。"
            "服务端返回：%s" % (status, payload.get("message") or text[:200]))
    if status == 429:
        raise RetryableError("429 限流")
    if status == 404:
        fail(6, "轮询失败：任务不存在或已失效（404）。task_id=%s" % task_id)
    if status >= 500:
        raise RetryableError("服务端错误 HTTP %d" % status)
    payload = parse_json(text)
    if payload is None:
        raise RetryableError("返回非 JSON")
    if status != 200 or payload.get("result") != "success":
        raise RetryableError("轮询返回异常：HTTP %s message=%s" % (status, payload.get("message")))
    return payload.get("data") or {}


def poll_loop(base_url, api_key, task_id, max_wait, interval):
    """轮询直到终态或超时。返回 (status, data, error_message_or_none)。"""
    deadline = time.monotonic() + max_wait
    last_signature = None
    backoff = interval

    while True:
        data = None
        err = None
        for _ in range(POLL_RETRY_TIMES):
            try:
                data = poll_once(base_url, api_key, task_id)
                err = None
                break
            except (RetryableError, urllib.error.URLError) as e:
                err = e
                wait = min(backoff, MAX_BACKOFF)
                log("轮询遇到可重试错误：%s，%ds 后重试" % (e, wait))
                time.sleep(wait)
                backoff = min(backoff * 2, MAX_BACKOFF)
        if err is not None:
            fail(6, "轮询连续 %d 次失败，终止：%s" % (POLL_RETRY_TIMES, err))
        backoff = interval

        status = data.get("status", "UNKNOWN")
        status_key = str(status or "UNKNOWN").upper()
        stage = data.get("current_stage", "")
        pmsg = data.get("progress_message", "")
        signature = (status, stage, pmsg)
        if signature != last_signature:
            label = STATUS_LABEL.get(status_key, status)
            log("[%s / stage=%s] %s" % (label, stage or "-", pmsg))
            last_signature = signature

        if status_key in COMPLETED_STATUSES:
            if _report_markdown(data):
                return ("COMPLETED", data, None)
            # 竞态：status 已 COMPLETED 但 result.markdown 尚未落库。
            # 在宽限窗口内继续轮询，等报告补齐；超时仍空则交回上层退出 7。
            grace_deadline = time.monotonic() + COMPLETED_REPORT_GRACE_SECONDS
            log("状态已完成但报告暂未返回，宽限窗口内继续轮询...")
            while time.monotonic() < grace_deadline:
                time.sleep(interval)
                try:
                    data = poll_once(base_url, api_key, task_id)
                except (RetryableError, urllib.error.URLError) as e:
                    log("宽限轮询出错（忽略，继续等）：%s" % e)
                    continue
                if _report_markdown(data):
                    return ("COMPLETED", data, None)
                if str(data.get("status", "")).upper() in FAILED_STATUSES:
                    return ("FAILED", data, data.get("error_message") or "视频拆解失败")
            return ("COMPLETED", data, None)
        if status_key in FAILED_STATUSES:
            return ("FAILED", data, data.get("error_message") or "视频拆解失败")
        if time.monotonic() > deadline:
            return ("TIMEOUT", data, None)
        time.sleep(interval)


# ---------------------------------------------------------------------------
# 交付报告
# ---------------------------------------------------------------------------

def _report_markdown(data):
    """从轮询返回的 data 中取 result.markdown；缺失返回 None。"""
    if not isinstance(data, dict):
        return None
    result = data.get("result") or {}
    if not isinstance(result, dict):
        return None
    return result.get("markdown")


def deliver_report(data, out_path, task_id, points=None):
    result = (data.get("result") or {}) if isinstance(data, dict) else {}
    markdown = result.get("markdown")
    if not markdown:
        stage = data.get("current_stage", "") if isinstance(data, dict) else ""
        pmsg = data.get("progress_message", "") if isinstance(data, dict) else ""
        errmsg = data.get("error_message", "") if isinstance(data, dict) else ""
        log("⚠️ 任务已标记完成，但接口未返回 result.markdown 报告内容。")
        log("   current_stage=%s | progress_message=%s | error_message=%s"
            % (stage or "-", pmsg or "-", errmsg or "-"))
        log("   多为报告尚未落库的短暂延迟，或服务端解析未能提取正文。")
        log("   可稍候用 --task-id %s 重新轮询一次；仍为空则改用本地文件方式重新发起。" % task_id)
        sys.exit(7)

    saved = None
    try:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(task_id or "unknown"))
        filename = "wx-video-%s.md" % safe
        path = out_path or filename
        if out_path and os.path.isdir(out_path):
            path = os.path.join(out_path, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown)
            if not markdown.endswith("\n"):
                f.write("\n")
        saved = os.path.abspath(path)
    except OSError as e:
        log("⚠️ 报告写入文件失败：%s（仍会在对话中渲染）" % e)

    # 本次实际扣点：优先取终态响应里的扣点字段，回退发起接口给出的扣点；都没有则为空，
    # 由调用方按约 128 点回退说明。
    final_points = extract_points(data)
    if final_points is None:
        final_points = points
    points_str = ""
    if final_points is not None and not isinstance(final_points, bool):
        try:
            f = float(final_points)
            points_str = str(int(f)) if f.is_integer() else str(f)
        except (TypeError, ValueError):
            points_str = str(final_points)
    print("WX_VIDEO_POINTS_USED=" + points_str)
    print("WX_VIDEO_REPORT_FILE=" + (saved or ""))
    print(REPORT_START)
    print(markdown)
    print(REPORT_END)
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="视频号视频拆解分析")
    parser.add_argument("input", nargs="?", default=None,
                        help="视频号分享链接，或本地视频文件路径")
    parser.add_argument("--task-id", default=None,
                        help="已有的任务 ID，跳过输入/上传/创建，直接轮询")
    parser.add_argument("--out", default=None, help="报告输出路径（目录或文件）")
    parser.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT, help="整体等待上限（秒）")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="轮询间隔（秒）")
    args = parser.parse_args()

    if not args.task_id and not args.input:
        parser.error("请提供视频号分享链接或本地视频路径，或使用 --task-id 恢复已有任务。")

    base_url = BASE_URL
    api_key = get_api_key()
    if not api_key:
        fail(3, "未取到 API Key：技能目录下的 config.json 不存在，或其中无有效的 LY_API_KEY 字段。\n"
                "请在技能目录（SKILL.md 所在处）创建 config.json，内容形如 "
                '{"LY_API_KEY": "你的密钥"}，或设置环境变量 LY_API_KEY 后重试。')

    if args.task_id:
        task_id = args.task_id
        points = None  # 恢复任务不重复扣点，无新增扣点信息
        log("恢复已有任务：task_id=%s" % task_id)
    else:
        kind, value = classify_input(args.input)
        if kind == "none":
            fail(2, "未识别到有效输入：请提供视频号分享链接，或本地视频文件路径。")
        if kind == "bad_file":
            ext = os.path.splitext(value)[1].lower()
            if not os.path.exists(value):
                fail(2, "本地文件不存在：%s" % value)
            fail(2, "不支持的视频格式：%s（支持 %s）" % (ext or "无扩展名", "/".join(sorted(VIDEO_EXTS))))

        share_url = None
        video_id = None
        if kind == "url":
            share_url = value
        elif kind == "file":
            video_id = upload_local_video(base_url, api_key, value)

        task_id, points = create_task(base_url, api_key, share_url=share_url, video_id=video_id)

    log("开始轮询拆解状态（最长 %ds，间隔 %ds）..." % (args.max_wait, args.interval))
    status, data, err = poll_loop(base_url, api_key, task_id, args.max_wait, args.interval)

    if status == "TIMEOUT":
        log("等待超时：已等待 %ds。当前状态：%s，进度：%s"
            % (args.max_wait, data.get("status"), data.get("progress_message")))
        log("任务仍在进行，task_id=%s。可稍后重新运行本脚本继续等待。" % task_id)
        sys.exit(124)
    if status == "FAILED":
        fail(5, "视频拆解失败：%s" % (err or "未知原因"))

    deliver_report(data, args.out, task_id, points)


if __name__ == "__main__":
    main()
