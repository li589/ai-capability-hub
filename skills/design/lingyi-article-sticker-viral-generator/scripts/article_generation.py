#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号贴图号爆款生成【零一数科·出品】 —— 联网主脚本 (v0.1.0)

异步任务模型：
  读 Key → 校验参数 → POST 创建任务（立即返回 task_id）→
  GET 轮询进度（stderr 输出）→ 终态后提取 data.total_points →
  取 data.markdown → 拼接报告 → 写盘 → 分隔符协议输出 stdout。

⚠️ 本 API 与标准范式的偏差（见 references/api.md 顶部「偏差」段）：
  1. 无 POST /{id}/retry 重试接口；--retry-task 实为「重新创建新任务」
     （新 task_id、独立扣费），失败重提须重供 --text 与业务参数重建 body。
  2. 扣点字段是 data.total_points（顶层整数），extract_total_points 已兼容。
  3. 有 GET /config 拉取 tone（内容调性）枚举，禁止硬编码示例值；
     --fetch-config 拉取实时枚举；tone 默认不传走后端默认。
  4. 后端 data.markdown 自带一级标题（# 标题）且要求原样展示；assemble_report
     检测到 H1 即不再前置脚本标题、不插分隔线，避免出现两个 H1；仅无 H1 时
     才前置「# 爆款图文：<话题>」兜底。
  5. 本 API 无幂等机制（文档无 idempotency 字段，§3.2 禁未声明字段→否则 422）；
     标准 §9 的『X-Idempotency-Key + body idempotency_key』不适用，已移除：
     不发幂等头、不向 body 注入 idempotency_key，CLI 亦无 --idempotency-key。

退出码见 SKILL.md「退出码处理」。纯标准库。

⚠️ 占位符说明：以下 {{占位符}} 已由生成器替换为本 skill 的实际值。
   PREFIX        ARTICLE_GEN  —— stdout 协议前缀
   TAG           article_gen  —— 日志标签
   TASKS_PATH    /api/v1/content/article-generation
   REPORT_LABEL  爆款图文 —— 报告默认文件名前缀
   TITLE_LABEL   爆款图文 —— 报告一级标题前缀
   业务提交字段（build_body）、markdown 取法（extract_markdown）、进度字段
   （_progress_summary）按 references/api.md 的实际契约编写。
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
TASKS_PATH = "/api/v1/content/article-generation"
CONFIG_PATH = "/api/v1/content/article-generation/config"

DEFAULT_TIMEOUT = 90   # 单次轮询等待上限（秒）；< WorkBuddy/Web 单轮上限；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60      # 单次 HTTP 超时（创建/retry/get）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5
OVERALL_POLL_CAP = 30 * 60  # 整体轮询封顶 ~30 分钟，避免无限轮询

# 约定回退扣点（仅「约 N 点」提示，不当作实扣）
PLAN_POINTS = 60          # 约定估值（「60 点起步」提示），正式实扣以 data.total_points 为准
# 若按模块计点，可定义 MODULE_POINTS = {...}，plan_points_for 据此求和

# 任务态
STATUS_OK = "completed"
STATUS_TERMINAL = frozenset({"completed", "failed", "timeout"})
STATUS_RETRYABLE = frozenset({"failed", "timeout"})

# content_format 与比例约束（静态，非 /config 返回；见 api.md §7）
CONTENT_FORMATS = ("xiaolvshu", "image_message")
RATIOS = {
    "xiaolvshu": {
        "cover": {"3:4", "1:1"},
        "body": {"3:4", "1:1"},
        "cover_default": "3:4",
        "body_default": "3:4",
    },
    "image_message": {
        "cover": {"2.35:1"},
        "body": {"16:9", "3:4", "1:1"},
        "cover_default": "2.35:1",
        "body_default": "16:9",
    },
}

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
PREFIX = "ARTICLE_GEN"
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
    print("[article_gen] %s" % msg, file=sys.stderr, flush=True)


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
    # 本 API 无幂等机制（文档无 idempotency 字段，§3.2 禁未声明字段），
    # 不发 X-Idempotency-Key 头（本 API 无幂等字段）。
    headers = {
        "Authorization": "Bearer %s" % api_key,
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


def normalize_ratio(value):
    """全角冒号归一为半角；去首尾空白；空串返回 ''。"""
    if value is None:
        return ""
    s = str(value).strip().replace("：", ":")
    return s


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
        print("[article_gen] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, body_obj, timeout, label="创建任务"):
    # 本 API 无幂等机制：不向 body 注入 idempotency_key（§3.2 禁未声明字段→否则 422），不发幂等头。
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
    # task_id 可能含 + / =，须 URL-path-encode
    encoded = urllib.parse.quote(str(task_id), safe="")
    url = base_url.rstrip("/") + TASKS_PATH + "/" + encoded
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def call_fetch_config(base_url, api_key, timeout, label="取配置"):
    """GET /config 拉取 tone 等枚举。不创建任务、不涉扣点。"""
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
    真正的「重建」在 main() 的 --retry-task 分支用 call_create_task 完成。
    保留原 <task_id> 仅作日志参考。"""
    log("%s：原 task_id=%s（本 API 无 /retry，将用相同参数重新创建新任务，独立扣费）" % (label, task_id))
    # 实际重建动作由调用方用 build_body + call_create_task 完成
    return None, None


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
            return data, payload, E_OK


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
    return title.replace("\n", " ").strip() or "爆款图文"


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
    没 H1 时，才前置 `# 爆款图文：<话题摘要>` 作为兜底标题。
    """
    clean = [s.replace("\r\n", "\n").replace("\r", "\n").strip() for s in markdown_sections if s and s.strip()]
    if not clean:
        return "# 爆款图文：%s\n" % make_title(text)

    # 后端 markdown 已自带 H1 → 原样输出（单段不加分隔线；多段保留各自的 H1）
    if any(_starts_with_h1(s) for s in clean):
        return SECTION_SEPARATOR.join(clean) + "\n"

    # 无 H1 → 前置脚本标题
    return "# 爆款图文：%s\n\n%s\n" % (make_title(text), SECTION_SEPARATOR.join(clean))


def plan_points_for():
    return PLAN_POINTS


def handle_task_outcome(data, payload, text):
    """根据任务 status 产出报告或 fail。返回 (final_md, points, task_id)。"""
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
        fail(E_FAILED, "任务已 completed 但无可用 markdown：task_id=%s。结果暂不可用；可用 --retry-task 重新创建。" % task_id)

    # 本 API status 枚举无 partial_failed（§4.6），失败一律重新创建
    detail = failure_message or status or "unknown"
    if status in STATUS_RETRYABLE:
        tip = "任务未成功：status=%s %s task_id=%s。本 API 无 /retry 接口，可重新创建（独立扣费）。" % (status, detail, task_id)
        fail(E_FAILED, tip)
    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, detail, task_id))


# --------------------------------------------------------------------------- 业务校验
def validate_business_args(args):
    """创建/重试前校验业务参数，客户端拦截非法值，避免靠服务端 422。"""
    if args.word_count is None:
        fail(E_PARAM, "缺少必填 --word-count（正文字数，100–50000）。")
    wc = args.word_count
    if wc < 100 or wc > 50000:
        fail(E_PARAM, "--word-count 必须在 100–50000 之间（当前 %s）。" % wc)

    if not args.product_name or not args.product_name.strip():
        fail(E_PARAM, "缺少必填 --product-name。")
    if not args.selling_points or not [s for s in args.selling_points if s and s.strip()]:
        fail(E_PARAM, "缺少必填 --selling-points（至少 1 条卖点）。")
    if not args.audience_desc or not args.audience_desc.strip():
        fail(E_PARAM, "缺少必填 --audience-desc。")
    if not args.pain_points or not [p for p in args.pain_points if p and p.strip()]:
        fail(E_PARAM, "缺少必填 --pain-points（至少 1 条痛点）。")

    fmt = (args.content_format or "").strip() or "xiaolvshu"
    if fmt not in CONTENT_FORMATS:
        fail(E_PARAM, "--content-format 必须是 %s 之一（当前 %r）。" % ("/".join(CONTENT_FORMATS), args.content_format))

    cover = normalize_ratio(args.cover_ratio)
    body = normalize_ratio(args.body_ratio)
    if cover and cover not in RATIOS[fmt]["cover"]:
        fail(E_PARAM, "封面比例 %r 不匹配 content_format=%s，允许：%s。" % (cover, fmt, sorted(RATIOS[fmt]["cover"])))
    if body and body not in RATIOS[fmt]["body"]:
        fail(E_PARAM, "配图比例 %r 不匹配 content_format=%s，允许：%s。" % (body, fmt, sorted(RATIOS[fmt]["body"])))

    for name, val, lo, hi in (
        ("main-image-count", args.main_image_count, 1, 5),
        ("inset-image-count", args.inset_image_count, 1, 5),
        ("title-count", args.title_count, 1, 5),
    ):
        if val is not None and (val < lo or val > hi):
            fail(E_PARAM, "--%s 必须在 %d–%d 之间（当前 %s）。" % (name, lo, hi, val))

    if args.product_price is not None and args.product_price < 0:
        fail(E_PARAM, "--product-price 必须 ≥0。")


def build_body(args, text):
    """按 references/api.md 构造 POST 创建任务 body。
    text 即 topic（选题/话题），兼作报告标题摘要。
    可选业务参数仅在设置时加入，缺省不传走后端默认。禁止发送 scene/account_id/*_image_quality/*_image_size。
    """
    fmt = (args.content_format or "").strip() or "xiaolvshu"

    body = {
        "topic": text,
        "word_count": args.word_count,
        "product": {
            "name": args.product_name.strip(),
            "selling_points": [s.strip() for s in args.selling_points if s and s.strip()],
        },
        "target_audience": {
            "description": args.audience_desc.strip(),
            "pain_points": [p.strip() for p in args.pain_points if p and p.strip()],
        },
    }

    # product 可选
    if args.product_price is not None:
        body["product"]["price"] = args.product_price
    if args.price_band and args.price_band.strip():
        body["product"]["price_band"] = args.price_band.strip()
    if args.decision_type and args.decision_type.strip():
        body["product"]["decision_type"] = args.decision_type.strip()

    # target_audience 可选
    if args.audience_age and args.audience_age.strip():
        body["target_audience"]["age_range"] = args.audience_age.strip()
    if args.audience_gender and args.audience_gender.strip():
        body["target_audience"]["gender"] = args.audience_gender.strip()

    # 顶层可选
    if args.content_format:
        body["content_format"] = fmt
    cover = normalize_ratio(args.cover_ratio)
    body_cover = cover or RATIOS[fmt]["cover_default"]
    if args.cover_ratio:  # 仅当用户显式传了才写入
        body["cover_image_ratio"] = body_cover
    body_ratio = normalize_ratio(args.body_ratio)
    if args.body_ratio:
        body["body_image_ratio"] = body_ratio or RATIOS[fmt]["body_default"]
    if args.tone and args.tone.strip():
        body["tone"] = args.tone.strip()
    if args.main_image_count is not None:
        body["main_image_count"] = args.main_image_count
    if args.inset_image_count is not None:
        body["inset_image_count"] = args.inset_image_count
    if args.title_count is not None:
        body["title_count"] = args.title_count

    body["origin"] = "01workbuddy"
    body["origin_method"] = "skill"

    return body


def add_business_args(ap):
    """追加本 skill 必填/可选业务参数。"""
    ap.add_argument("--word-count", type=int, default=None, help="正文字数，必填，100–50000。")
    ap.add_argument("--product-name", default=None, help="产品名称，必填。")
    ap.add_argument("--selling-points", action="append", default=None, metavar="POINT", help="产品卖点，必填≥1，可多次传入。")
    ap.add_argument("--product-price", type=float, default=None, help="产品价格，可选，≥0。")
    ap.add_argument("--price-band", default=None, help="价格带，如 low/mid/high，可选。")
    ap.add_argument("--decision-type", default=None, help="决策类型，如 considered，可选。")
    ap.add_argument("--audience-desc", default=None, help="目标受众描述，必填。")
    ap.add_argument("--pain-points", action="append", default=None, metavar="POINT", help="受众痛点，必填≥1，可多次传入。")
    ap.add_argument("--audience-age", default=None, help="受众年龄段，如 25-35，可选。")
    ap.add_argument("--audience-gender", default=None, help="受众性别，如 female/male，可选。")
    ap.add_argument("--content-format", default=None, help="内容形式：xiaolvshu(贴图号,默认) / image_message(公众号)。可选。")
    ap.add_argument("--cover-ratio", default=None, help="封面比例，需与 content_format 匹配，可选（不传走默认）。")
    ap.add_argument("--body-ratio", default=None, help="配图比例，需与 content_format 匹配，可选（不传走默认）。")
    ap.add_argument("--tone", default=None, help="内容调性，需取自 --fetch-config 的实时枚举，可选（不传走后端默认）。")
    ap.add_argument("--main-image-count", type=int, default=None, help="主图/封面数量，可选 1–5，默认 1。")
    ap.add_argument("--inset-image-count", type=int, default=None, help="正文配图数量，可选 1–5，默认 1。")
    ap.add_argument("--title-count", type=int, default=None, help="候选标题数量，可选 1–5，默认 3。")


def print_config(data):
    """渲染 GET /config 的 tone 等枚举为易读文本。"""
    if isinstance(data, dict):
        items = [data]
    elif isinstance(data, list):
        items = [x for x in data if isinstance(x, dict)]
    else:
        items = []
    if not items:
        print("（config 未返回可识别字段）")
        return
    for item in items:
        field = item.get("field") or ""
        label = item.get("label") or field
        desc = item.get("desc") or ""
        print("字段：%s（%s）%s" % (field, label, ("—— " + desc) if desc else ""))
        options = item.get("options") or []
        for opt in options:
            if isinstance(opt, dict):
                ov = opt.get("value", "")
                ol = opt.get("label", "")
                od = opt.get("desc", "")
                print("  - %s\t%s%s" % (ov, ol, ("（" + od + "）") if od else ""))
        print("")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="公众号贴图号爆款生成【零一数科·出品】（异步任务 API · v0.1.0）")
    ap.add_argument("--text", default=None, help="选题/话题（即 topic），或文件路径，或 '-' 读 stdin；兼作报告标题摘要。")
    ap.add_argument("--out", default=None, help="输出 MD 路径；缺省写当前目录的 爆款图文-<task_id>.md")
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
    ap.add_argument("--fetch-config", action="store_true", help="GET /config 拉取 tone 等实时枚举并打印，不创建任务、不涉扣点。")
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

    # —— 取配置（拉取 tone 枚举，不创建任务、不扣点）——
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
            code = E_OK
        status = str(data.get("status") or "")
        if status in STATUS_TERMINAL:
            text_for_title = (args.text and read_text(args.text).strip()) or ("任务 %s" % task_id[:8])
            if not (args.text and read_text(args.text).strip()):
                log("提示：--poll-task 未带 --text，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --text。" % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(data, payload, text_for_title)
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
            fail(E_PARAM, "--retry-task 需重供 --text（topic）以重建请求体。")
        text = read_text(args.text).strip()
        if not text:
            fail(E_PARAM, "输入文本（topic）为空。")
        validate_business_args(args)
        body = build_body(args, text)
        log("--retry-task %s：本 API 无 /retry，将重新创建新任务（独立扣费）。" % old_id)
        data, payload = call_create_task(base_url, api_key, body, HTTP_TIMEOUT, label="重试（重新创建）")
        data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        if code == E_PENDING:
            _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
            return
        final_md, used_points, task_id_out = handle_task_outcome(data, payload, text)
        _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
        return

    # —— 仅创建任务（创建后即退，不轮询）——
    if args.only_create:
        if not args.text:
            fail(E_PARAM, "--only-create 仍需 --text 提供 topic。")
        text = read_text(args.text).strip()
        if not text:
            fail(E_PARAM, "输入文本（topic）为空。")
        validate_business_args(args)
        body = build_body(args, text)
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
        fail(E_PARAM, "请提供 --text（topic），或使用 --retry-task <task_id> / --poll-task <task_id>。")
    text = read_text(args.text).strip()
    if not text:
        fail(E_PARAM, "输入文本（topic）为空。")
    validate_business_args(args)
    body = build_body(args, text)
    log("将创建任务，topic_len=%d word_count=%s content_format=%s" % (
        len(text), args.word_count, (args.content_format or "xiaolvshu(默认)")))
    data, payload = call_create_task(base_url, api_key, body, HTTP_TIMEOUT)
    data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
    if code == E_PENDING:
        _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(data, payload, text)
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
    """三级兜底确保必生成 md：--out → 当前目录 爆款图文-<id>.md → /tmp/爆款图文-<id>.md。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "爆款图文.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("爆款图文-%s.md" % stem))
    candidates.append(Path("/tmp") / ("爆款图文-%s.md" % stem))

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


def _emit(final_md, used_points, plan_total, out_path, task_id):
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
    log("完成。task_id=%s points=%s" % (task_id or "-", points_str or "(empty)"))
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
