#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信视频号账号拆解（付费版）【零一数科·出品】 —— 联网主脚本 (v0.1.0)

异步任务模型（账号快拆）：
  读 Key → 校验 account_name → POST 创建（立即返回 task_id）→
  GET 轮询进度（stderr 输出）→ 终态后从 data.markdown 取报告 →
  data.total_points 取实扣 → 写盘 → 分隔符协议输出 stdout。

本接口只提供「创建 + 查询」两个端点，无重试端点；任务失败后由调用方用原账号名重新
--only-create 发起（重新计费）。报告 markdown 由后端预渲染、自带一级标题，脚本原样使用，
不二次叠加标题。退出码见 SKILL.md「退出码处理」。纯标准库。
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
import uuid
from pathlib import Path

# --------------------------------------------------------------------------- 常量
BASE_URL = "https://claw.lingyishuke.com/services"
TASKS_PATH = "/api/v1/common-gateway/analysis-skill/wx-video-account-quick-analysis"

DEFAULT_TIMEOUT = 90   # 单次轮询等待上限（秒）；< WorkBuddy/Web 单轮上限；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60      # 单次 HTTP 超时（创建/get）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5

# 约定回退扣点（仅「约 N 点」提示，不当作实扣）
PLAN_POINTS = 120          # 快拆较全量拆解轻，约定估值；实际以服务端 data.total_points 为准

# 任务态
STATUS_OK = "completed"            # 成功终态（后端预渲染好 data.markdown）
STATUS_TERMINAL = frozenset({"completed", "failed"})
STATUS_RETRYABLE = frozenset({"failed"})

# 退出码
E_OK = 0
E_NO_KEY = 2
E_PARAM = 3
E_BALANCE = 4
E_AUTH = 8
E_4XX = 10
E_5XX = 11
E_FAILED = 12   # 已发起但任务失败（status=failed，或终态但无报告）
E_PENDING = 13  # 已发起但未到终态（非失败，可续 --poll-task）

# stdout 交付协议（前缀按本 skill 代号）
PREFIX = "WX_ACCOUNT_QUICK"
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
    print("[wx_account_quick] %s" % msg, file=sys.stderr, flush=True)


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
            if attempt >= retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s网络错误：%s，%ds 后重试（%d/%d）" % (label, e, wait, attempt, retries))
            time.sleep(wait)
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s请求异常：%s，%ds 后重试（%d/%d）" % (label, e, wait, attempt, retries))
            time.sleep(wait)
    raise last_err


# --------------------------------------------------------------------------- 扣点提取
def extract_total_points(payload):
    """提取正式扣点字段。本接口完成态放在 data.total_points（number，顶层）。
    优先 data.total_points，再回退 billing.total_points 等历史候选 key。命中返回数值，否则 None。"""
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

    # 历史兼容回退（其它后端可能用的命名）
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
        fail(E_4XX, "%s无权访问该任务（HTTP 403）：%s" % (label, msg))
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
    """从任务 data 汇总人类可读进度文案。本接口进度字段：current_stage / progress_message。"""
    current = data.get("current_stage") or ""
    pmsg = data.get("progress_message") or ""
    status = data.get("status") or ""
    parts = []
    if current:
        parts.append("当前阶段：%s" % current)
    if pmsg:
        parts.append(pmsg)
    if parts:
        return "，".join(parts)
    return "status=%s 等待调度" % status


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s%s task_id=%s | %s" % (prefix, status or "?", elapsed_s, task_id or "-", summary))
    if emit_task_id and task_id:
        print("[wx_account_quick] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


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
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


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
    """从终态 data 取报告 markdown 字符串。本接口完成态由后端预渲染好 data.markdown，
    自带一级标题，直接 strip 返回。若服务端未来换成 results.<m>.markdown 也兼容。"""
    if isinstance(data, dict):
        # 单一报告：data.markdown（本接口主路径）
        mk = data.get("markdown")
        if mk:
            return str(mk).strip()

        result = data.get("result") if isinstance(data.get("result"), dict) else None
        if not mk and isinstance(result, dict):
            mk = result.get("markdown")
            if mk:
                return str(mk).strip()

        # 多模块兼容分支（本接口暂未使用，保留无害）
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
    return title.replace("\n", " ").strip() or "账号快拆报告"


def assemble_report(text, markdown_sections):
    """拼最终报告 markdown。markdown_sections: [str, ...] 已剔空。

    本接口 markdown 由后端预渲染、自带一级标题（# 微信视频号账号拆解报告）。
    若传入段落已以「# 」开头，原样使用，避免双标题；否则补「# 账号快拆报告：<摘要>」。"""
    clean = [s.replace("\r\n", "\n").replace("\r", "\n").strip() for s in markdown_sections if s and s.strip()]
    if not clean:
        return "# 账号快拆报告：%s\n" % make_title(text)

    joined = SECTION_SEPARATOR.join(clean)
    if joined.lstrip().startswith("# "):
        # 后端已渲染好一级标题，原样使用
        return joined + "\n"
    return "# 账号快拆报告：%s\n\n%s\n" % (make_title(text), joined)


def plan_points_for():
    return PLAN_POINTS


def handle_task_outcome(data, payload, text):
    """根据任务 status 产出报告或 fail。返回 (final_md, points, task_id)。"""
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    failure_message = data.get("error_message") or data.get("failure_message") or data.get("failure_code") or ""

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status == STATUS_OK:
        md = extract_markdown(data)
        if md:
            return assemble_report(text, [md]), points, task_id
        fail(E_FAILED, "任务成功但无可用 markdown：task_id=%s（可用 --only-create 重新发起）" % task_id)

    # 终态失败（failed）：本接口无重试端点，告知点数已返还、可重新发起
    if status in STATUS_RETRYABLE or status == "failed":
        fail(E_FAILED, "任务失败：status=%s %s task_id=%s。点数已返还；本接口无重试端点，可用原账号名重新 --only-create 发起（重新计费）。"
             % (status, failure_message or "未知原因", task_id))
    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, failure_message, task_id))


# --------------------------------------------------------------------------- main
def build_body(args, account_name):
    """按 references/api.md 构造 POST 创建任务 body。
    本接口 body：account_name（必填）+ 可选 platform + idempotency_key（调用处补）。"""
    body = {
        "account_name": account_name,
    }
    if getattr(args, "platform", None):
        body["platform"] = args.platform
    return body


def main():
    ap = argparse.ArgumentParser(description="微信视频号账号拆解（付费版）【零一数科·出品】（账号快拆 · 异步任务 API · v0.1.0）")
    ap.add_argument("--account-name", default=None,
                    help="视频号账号名称（昵称），新建任务必填；--poll-task 时用于生成报告标题")
    ap.add_argument("--platform", default=None, help="平台，可不传；本期固定按微信视频号处理")
    ap.add_argument("--out", default=None, help="输出 MD 路径；缺省写当前目录的 账号快拆报告-<task_id>.md")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s，< WorkBuddy/Web 单轮上限）。到点非错误，进行中退出 13 可续轮询。" % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--idempotency-key", default=None, help="幂等键；缺省自动生成 UUID。重复提交同一任务请保持不变。")
    ap.add_argument("--only-create", action="store_true",
                    help="仅 POST 创建拿 task_id 后即退（退出码 0，不轮询）。stdout 吐 task_id + 初始进度")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；建议带 --account-name（用于报告标题）。终态交付(exit0)；仍运行 exit13；终态失败 exit12。")
    args = ap.parse_args()

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "未取到 API Key：技能目录 config.json 不存在或无 LY_API_KEY 字段。\n"
              "请前往 https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy 获取，\n"
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
        account_name = (args.account_name or "").strip()
        if not account_name:
            log("提示：--poll-task 未带 --account-name，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --account-name。" % task_id[:8])
        data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        status = str(data.get("status") or "")
        if status not in STATUS_TERMINAL:
            data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        else:
            code = E_OK
        status = str(data.get("status") or "")
        if status in STATUS_TERMINAL:
            text_for_title = account_name or ("任务 %s" % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(data, payload, text_for_title)
            _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
            return
        _emit_pending(data, task_id, int(args.timeout))
        return

    # —— 仅创建任务（创建后即退，不轮询）——
    if args.only_create:
        if not args.account_name:
            fail(E_PARAM, "--only-create 需 --account-name 提供视频号账号名称。")
        account_name = args.account_name.strip()
        if not account_name:
            fail(E_PARAM, "账号名称为空。")
        body = build_body(args, account_name)
        idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
        data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
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

    # —— 新建任务（创建 + 内部轮询到终态；Web 端易打断，推荐改用 --only-create 拆分轮询）——
    if not args.account_name:
        fail(E_PARAM, "请提供 --account-name，或使用 --poll-task <task_id>。")
    account_name = args.account_name.strip()
    if not account_name:
        fail(E_PARAM, "账号名称为空。")
    body = build_body(args, account_name)
    idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
    log("将创建任务，account_name=%s" % account_name)
    data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
    data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
    if code == E_PENDING:
        _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(data, payload, account_name)
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
    """三级兜底确保必生成 md：--out → 当前目录 账号快拆报告-<id>.md → /tmp/账号快拆报告-<id>.md。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "账号快拆报告.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("账号快拆报告-%s.md" % stem))
    candidates.append(Path("/tmp") / ("账号快拆报告-%s.md" % stem))

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
