#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""短视频内容审核 —— 联网主脚本（调后端异步任务）

本地视频（可选）：
  预签名 POST /content-ops/videos/public-upload-url
  → 直传 OSS
  → 确认 POST /content-ops/videos/public-upload-confirm → video_id

质检任务：
  POST /video-compliance/tasks → GET 轮询 → 交付 Markdown

任务状态：pending / running / completed / failed
- completed：报告就绪；首次 GET completed 时服务端结算扣点（只扣一次）
- failed：失败，见 errors

输入：--text / --video（本地文件）/ --video-id 至少其一；
  --video 会先上传换 video_id，再创建质检（有 video_id 时后端可多模态提取）。

退出码：0 成功 / 2 无Key / 3 参数 / 4 余额 / 8 鉴权
       / 9 上传失败 / 10 4xx / 11 5xx / 12 失败 / 13 进行中
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
import urllib.request
from pathlib import Path

BASE_URL = "https://claw.lingyishuke.com/services"
TASKS_PATH = "/api/v1/content-quality/video-compliance/tasks"
PATH_UPLOAD_URL = "/api/v1/content-ops/videos/public-upload-url"
PATH_UPLOAD_CONFIRM = "/api/v1/content-ops/videos/public-upload-confirm"
PLATFORMS = {"douyin", "channels", "xhs", "bilibili", "kuaishou"}

DEFAULT_TIMEOUT = 600
HTTP_TIMEOUT = 60
UPLOAD_HTTP_TIMEOUT = 600
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 60
FALLBACK_PLAN_POINTS = 20

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100MB
DEFAULT_UPLOAD_CONTENT_TYPE = "application/octet-stream"

F_UPLOAD_URL_ALIASES = (
    "upload_url", "uploadUrl", "url", "signed_url", "signedUrl",
    "presigned_url", "presignedUrl",
)
F_UPLOAD_ID_ALIASES = ("upload_id", "uploadId")
F_OBJECT_KEY_ALIASES = (
    "object_key", "objectKey", "key", "file_key", "fileKey", "path",
)
F_VIDEO_ID_ALIASES = ("video_id", "videoId", "id")
F_VIDEO_URL_ALIASES = ("video_url", "videoUrl", "file_url", "fileUrl", "url")

# 成功终态（含旧 succeeded 兼容）
STATUS_OK = frozenset({"completed", "succeeded"})
# 失败终态（含旧 billing_failed 兼容）
STATUS_FAILED = frozenset({"failed", "billing_failed"})

E_OK, E_NO_KEY, E_PARAM, E_BALANCE, E_AUTH = 0, 2, 3, 4, 8
E_UPLOAD, E_4XX, E_5XX, E_FAILED, E_PENDING = 9, 10, 11, 12, 13

POINTS_PREFIX = "VIDEO_QC_POINTS_USED="
PLAN_PREFIX = "VIDEO_QC_PLAN_POINTS="
REPORT_START = "=== VIDEO_QC_REPORT_START ==="
REPORT_END = "=== VIDEO_QC_REPORT_END ==="
FILE_PREFIX = "VIDEO_QC_REPORT_FILE="
TASK_PREFIX = "VIDEO_QC_TASK_ID="
VIDEO_ID_PREFIX = "VIDEO_QC_VIDEO_ID="

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


def log(msg):
    print("[video_compliance] %s" % msg, file=sys.stderr, flush=True)


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
    # idempotency_key 已废弃（服务端忽略），有值时仍可带上兼容旧网关
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


def first_present(data, keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return None


def http_request(url, method, headers, body, timeout):
    if body is None:
        data = None
    elif isinstance(body, bytes):
        data = body
    else:
        data = body.encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
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


def http_request_with_retries(
    url, method, headers, body, timeout, label, retries=HTTP_RETRY_TIMES
):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            status, text = http_request(url, method, headers, body, timeout)
            if status >= 500 and attempt < retries:
                wait = min(2 ** (attempt - 1), MAX_BACKOFF)
                log("%s %s，%ds 后重试" % (label, status, wait))
                time.sleep(wait)
                continue
            return status, text
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s 异常：%s，%ds 后重试" % (label, e, wait))
            time.sleep(wait)
    raise last_err


def resolve_local_video(path_arg):
    """校验本地视频路径，返回绝对路径。"""
    raw = (path_arg or "").strip()
    if raw.startswith("file://"):
        raw = raw[len("file://"):]
    p = Path(raw).expanduser()
    if not p.is_file():
        fail(E_PARAM, "本地视频不存在：%s" % path_arg)
    ext = p.suffix.lower()
    if ext not in VIDEO_EXTS:
        fail(
            E_PARAM,
            "不支持的视频格式：%s（支持 %s）"
            % (ext or "无扩展名", "/".join(sorted(VIDEO_EXTS))),
        )
    size = p.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        fail(
            E_PARAM,
            "本地视频过大：%.1f MB，超过上传上限 %d MB。请压缩或裁剪后重试。"
            % (size / 1024 / 1024, MAX_UPLOAD_BYTES // (1024 * 1024)),
        )
    if size <= 0:
        fail(E_PARAM, "本地视频为空文件：%s" % p)
    return str(p.resolve())


def upload_local_video(api_key, path):
    """预签名 → 直传 → 确认，返回 video_id。失败退出码 9（过大/格式问题为 3）。"""
    path = resolve_local_video(path)
    size = os.path.getsize(path)
    filename = os.path.basename(path)

    # 1) 预签名
    log("取预签名上传地址：%s（%.1f MB）" % (filename, size / 1024 / 1024))
    content_type = mimetypes.guess_type(filename)[0] or DEFAULT_UPLOAD_CONTENT_TYPE
    body = json.dumps(
        {"filename": filename, "content_type": content_type, "size": size},
        ensure_ascii=False,
    )
    url = BASE_URL.rstrip("/") + PATH_UPLOAD_URL
    try:
        status, text = http_request_with_retries(
            url, "POST", auth_headers(api_key), body, HTTP_TIMEOUT, "取预签名",
        )
    except Exception as e:
        fail(E_UPLOAD, "取预签名失败（网络错误）：%s" % e)
    if status in (401, 403):
        handle_http_error(status, text)
    payload = parse_json(text) or {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    upload_url = first_present(data, F_UPLOAD_URL_ALIASES)
    if status != 200 or not upload_url:
        fail(
            E_UPLOAD,
            "取预签名失败：HTTP %s，message=%s，原文=%s"
            % (status, payload.get("message"), text[:200]),
        )
    method = str(data.get("method") or "PUT").upper()
    put_headers = data.get("headers") or {"Content-Type": DEFAULT_UPLOAD_CONTENT_TYPE}
    if not isinstance(put_headers, dict):
        put_headers = {"Content-Type": DEFAULT_UPLOAD_CONTENT_TYPE}
    upload_id = first_present(data, F_UPLOAD_ID_ALIASES)
    object_key = first_present(data, F_OBJECT_KEY_ALIASES)
    presigned_file_url = first_present(data, F_VIDEO_URL_ALIASES)

    # 2) 直传 OSS（不带平台 Authorization）
    log("上传文件中...")
    with open(path, "rb") as f:
        file_bytes = f.read()
    try:
        status, text = http_request_with_retries(
            upload_url,
            method,
            put_headers,
            file_bytes,
            UPLOAD_HTTP_TIMEOUT,
            "上传文件",
            retries=3,
        )
    except Exception as e:
        fail(E_UPLOAD, "上传文件失败（网络错误）：%s" % e)
    if status not in (200, 201, 204):
        fail(E_UPLOAD, "上传文件失败：HTTP %s，原文=%s" % (status, text[:200]))

    # 3) 确认 → video_id
    log("确认上传完成...")
    confirm_obj = {}
    if upload_id:
        confirm_obj["upload_id"] = upload_id
    if object_key:
        confirm_obj["object_key"] = object_key
    if not confirm_obj:
        fail(E_UPLOAD, "预签名响应缺少 upload_id/object_key，无法确认上传")
    confirm_url = BASE_URL.rstrip("/") + PATH_UPLOAD_CONFIRM
    try:
        status, text = http_request_with_retries(
            confirm_url,
            "POST",
            auth_headers(api_key),
            json.dumps(confirm_obj, ensure_ascii=False),
            HTTP_TIMEOUT,
            "确认上传",
        )
    except Exception as e:
        fail(E_UPLOAD, "确认上传失败（网络错误）：%s" % e)
    if status in (401, 403):
        handle_http_error(status, text)
    payload = parse_json(text) or {}
    confirm_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    video_id = first_present(confirm_data, F_VIDEO_ID_ALIASES)
    video_url = first_present(confirm_data, F_VIDEO_URL_ALIASES) or presigned_file_url
    if status not in (200, 201) or not video_id:
        fail(
            E_UPLOAD,
            "确认上传失败：HTTP %s，message=%s，原文=%s"
            % (status, payload.get("message"), text[:200]),
        )
    video_id = str(video_id).strip()
    log("上传完成：video_id=%s" % video_id)
    if video_url:
        log("上传后视频链接：%s" % video_url)
    return video_id


def extract_total_points(payload):
    """从 GET 响应取实扣：优先 data.total_points，兼容旧版 billing.total_points。"""
    if not isinstance(payload, dict):
        return None
    # 新契约：扁平 total_points（SkillReportTaskResponse）
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
    """GET 任务。status=completed 时服务端首次读取会结算扣点（只扣一次）。

    对外 data 仅含 task_id/status/markdown/errors/total_points。
    """
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


def parse_platforms(raw):
    if not raw:
        return []
    out = []
    for part in str(raw).replace("，", ",").split(","):
        p = part.strip()
        if p in PLATFORMS and p not in out:
            out.append(p)
    return out


def main():
    parser = argparse.ArgumentParser(description="短视频内容审核（后端异步任务）")
    parser.add_argument("--text", help="口播文案/字幕 或文件路径或 -")
    parser.add_argument(
        "--video",
        default="",
        help="本地视频路径：自动 content-ops 预签名上传 → 确认换 video_id（≤100MB）",
    )
    parser.add_argument(
        "--video-id",
        default="",
        help="已有 video_id（可与 text 同给；若同时给 --video 则以本参数为准、跳过上传）",
    )
    parser.add_argument(
        "--platforms",
        default="",
        help="逗号分隔：douyin,channels,xhs,bilibili,kuaishou；空=全5平台",
    )
    parser.add_argument("--industry", default="")
    parser.add_argument("--qualification-status", default="")
    parser.add_argument("--title-cover", default="")
    parser.add_argument("--is-commerce", action="store_true")
    parser.add_argument("--product-info", default="")
    parser.add_argument("--visual-audio-desc", default="")
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

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "缺少 LY_API_KEY（config.json 或环境变量）")

    if args.retry_task:
        data = retry_task(api_key, args.retry_task.strip())
        task_id = str(data.get("task_id") or args.retry_task).strip()
        data = poll_until_done(api_key, task_id, args.timeout, args.poll_interval)
        out = args.out or ("短视频内容审核-%s.md" % task_id[:8])
        deliver(data, out)
        sys.exit(E_OK)

    if args.poll_task:
        task_id = args.poll_task.strip()
        data = poll_until_done(
            api_key, task_id, args.timeout, args.poll_interval, only_once=True
        )
        out = args.out or ("短视频内容审核-%s.md" % task_id[:8])
        deliver(data, out)
        sys.exit(E_OK)

    video_id = (args.video_id or "").strip()
    local_video = (args.video or "").strip()
    if local_video and video_id:
        log("已提供 --video-id，跳过本地上传")
    elif local_video:
        video_id = upload_local_video(api_key, local_video)

    text = ""
    if args.text:
        text = read_text(args.text).strip()

    if not video_id and not text:
        fail(
            E_PARAM,
            "请提供 --text、--video 或 --video-id（至少其一）",
        )
    if not video_id and len(text) < 20:
        fail(
            E_PARAM,
            "口播/字幕过短，请至少提供约 20 字（或改用 --video / --video-id）",
        )

    payload = {
        "text": text,
        "video_id": video_id,
        "platforms": parse_platforms(args.platforms),
        "industry": (args.industry or "").strip(),
        "qualification_status": (args.qualification_status or "").strip(),
        "title_cover": (args.title_cover or "").strip(),
        "is_commerce": bool(args.is_commerce),
        "product_info": (args.product_info or "").strip(),
        "visual_audio_desc": (args.visual_audio_desc or "").strip(),
        "origin": (args.origin or "").strip() or "01workbuddy",
        "origin_method": (args.origin_method or "").strip() or "skill",
    }
    idem = (args.idempotency_key or "").strip() or None
    task_id, data = create_task(api_key, payload, idem)
    log("task_id=%s status=%s video_id=%s" % (task_id, data.get("status"), video_id or ""))

    if args.only_create:
        if video_id:
            print(VIDEO_ID_PREFIX + video_id)
        print(TASK_PREFIX + task_id)
        print(PLAN_PREFIX + str(FALLBACK_PLAN_POINTS))
        sys.exit(E_OK)

    data = poll_until_done(api_key, task_id, args.timeout, args.poll_interval)
    out = args.out or ("短视频内容审核-%s.md" % task_id[:8])
    if video_id:
        print(VIDEO_ID_PREFIX + video_id)
    deliver(data, out)
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
