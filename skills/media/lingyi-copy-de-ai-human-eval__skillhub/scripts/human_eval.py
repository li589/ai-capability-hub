#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文案去AI味+真人点评【零一数科·出品】 —— 联网主脚本 (v0.2.0)

三种 mode 异步任务模型（对齐 /deai/tasks 接口）：
  读 Key → 校验参数 → POST /tasks → GET 轮询 → 提取结果 → 写盘 → 分隔符协议输出 stdout。

三种 mode：
  - full（默认）：改写 + 评估串联一次跑完，一份报告交付
  - rewrite：只改写
  - eval：只评估

full 模式内部：POST rewrite → 轮询 → 提取改写正文 → POST eval → 轮询 → 拼接两段 markdown → 一次交付。

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
import urllib.request
import uuid
from pathlib import Path

# --------------------------------------------------------------------------- 常量
BASE_URL = "https://claw.lingyishuke.com/services"
TASKS_PATH = "/api/v1/content-quality/deai/tasks"
PLATFORMS = {"xhs", "channels", "mp", "dy"}
MODES = {"rewrite", "eval"}

DEFAULT_TIMEOUT = 90
HTTP_TIMEOUT = 60
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5

MODE_LABEL = {
    "rewrite": "去 AI 味改写",
    "eval": "真人评估",
}

# 约定回退扣点（仅「约 N 点」提示，不当作实扣）
PLAN_POINTS = {"rewrite": 12, "eval": 15}
FALLBACK_PLAN_TOTAL_REWRITE = 12
FALLBACK_PLAN_TOTAL_EVAL = 15

STATUS_OK = "succeeded"
STATUS_TERMINAL = frozenset({
    "succeeded", "failed", "billing_failed",
})

# 退出码
E_OK = 0
E_NO_KEY = 2
E_PARAM = 3
E_BALANCE = 4
E_AUTH = 8
E_4XX = 10
E_5XX = 11
E_FAILED = 12
E_PENDING = 13

# stdout 交付协议
POINTS_PREFIX = "HUMAN_EVAL_POINTS_USED="
PLAN_PREFIX = "HUMAN_EVAL_PLAN_POINTS="
REPORT_START = "=== HUMAN_EVAL_REPORT_START ==="
REPORT_END = "=== HUMAN_EVAL_REPORT_END ==="
FILE_PREFIX = "HUMAN_EVAL_REPORT_FILE="
TASK_PREFIX = "HUMAN_EVAL_TASK_ID="
MODE_PREFIX = "HUMAN_EVAL_MODE="

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


# --------------------------------------------------------------------------- 工具
def log(msg):
    print("[human_eval] %s" % msg, file=sys.stderr, flush=True)


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
        msg = (
            payload.get("message")
            or (payload.get("detail") if isinstance(payload.get("detail"), str) else None)
            or ""
        )
        detail = payload.get("detail")
        if isinstance(detail, dict) and detail.get("message"):
            msg = detail.get("message") or msg
    if not msg:
        msg = (resp_text or "")[:200]

    if status == 401:
        fail(E_AUTH, "%s鉴权失败（HTTP 401）：API Key 无效或已过期，请更新 config.json 的 LY_API_KEY。服务端：%s"
             % (label, msg))
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
    if 400 <= status < 500:
        fail(E_4XX, "%s调用失败（HTTP %s）：%s" % (label, status, msg))
    if status >= 500:
        fail(E_5XX, "%s服务端错误（HTTP %s）：%s" % (label, status, msg or "Internal server error"))


# --------------------------------------------------------------------------- 调 deai 任务 API
def _parse_task_response(status, resp_text, label):
    payload = parse_json(resp_text)
    if status != 200:
        raise_for_http(status, payload, resp_text, label)
    if payload is None:
        fail(E_5XX, "%s返回非 JSON（HTTP %s）：%s" % (label, status, resp_text[:200]))
    if payload.get("result") != "success":
        fail(E_4XX, "%s失败：HTTP %s result=%s message=%s"
             % (label, status, payload.get("result"), payload.get("message")))
    data = payload.get("data")
    if not isinstance(data, dict):
        fail(E_FAILED, "%s返回 data 为空或非对象。" % label)
    return data, payload


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    mode = str(data.get("mode") or "")
    mode_label = MODE_LABEL.get(mode, mode)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s mode=%s%s task_id=%s"
        % (prefix, status or "?", mode_label, elapsed_s, task_id or "-"))
    if emit_task_id and task_id:
        print("[human_eval] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, text, mode, platform, options, idempotency_key, timeout):
    url = base_url.rstrip("/") + TASKS_PATH
    body_obj = {
        "text": text,
        "mode": mode,
        "platform": platform,
        "idempotency_key": idempotency_key,
        "origin": "workbuddy",
        "origin_method": "skill",
    }
    if options:
        body_obj["options"] = options
    body = json.dumps(body_obj, ensure_ascii=False)
    label = "创建%s任务" % MODE_LABEL.get(mode, mode)
    log("%s：mode=%s text_len=%d platform=%s key=%s"
        % (label, mode, len(text), platform, idempotency_key[:8] + "…"))

    try:
        status, resp_text = http_request_with_retries(
            url, "POST",
            auth_headers(api_key, idempotency_key),
            body, timeout, label,
        )
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s（请检查网络与服务可达性：%s）" % (label, e, base_url))

    return _parse_task_response(status, resp_text, label)


def call_get_task(base_url, api_key, task_id, timeout):
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id
    label = "查询任务"
    try:
        status, resp_text = http_request_with_retries(
            url, "GET",
            auth_headers(api_key),
            None, timeout, label, retries=2,
        )
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def call_retry_task(base_url, api_key, task_id, timeout):
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id + "/retry"
    label = "重试任务"
    log("%s：task_id=%s" % (label, task_id))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST",
            auth_headers(api_key),
            None, timeout, label,
        )
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def wait_for_task(base_url, api_key, data, payload, timeout_total, poll_interval=PROGRESS_POLL_INTERVAL):
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


def make_title(text):
    title = (text[:20] + "…") if len(text) > 20 else text
    return title.replace("\n", " ").strip() or "报告"


def assemble_report(text, markdown, mode):
    """拼接最终报告 markdown。

    v0.2.0：data.markdown 是后端直出的单个段落（## 去 AI 味改写 或 ## 真人评估）。
    脚本只加顶级 # 标题。
    """
    if mode == "rewrite":
        top = "# 去 AI 味改写：%s" % make_title(text)
    else:
        top = "# 真人评估报告：%s" % make_title(text)
    md = str(markdown or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not md:
        return top + "\n"
    return top + "\n\n" + md + "\n"


def plan_points_for(mode):
    return PLAN_POINTS.get(mode, 0) or (FALLBACK_PLAN_TOTAL_REWRITE if mode == "rewrite" else FALLBACK_PLAN_TOTAL_EVAL)


def handle_task_outcome(data, payload, text, mode):
    """根据任务 status 产出报告或 fail。"""
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    failure_code = data.get("failure_code") or ""
    failure_message = data.get("failure_message") or ""

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status == STATUS_OK:
        markdown = str(data.get("markdown") or "").strip()
        if markdown:
            return assemble_report(text, markdown, mode), points, task_id
        fail(E_FAILED, "任务成功但 markdown 为空：task_id=%s（可用 --retry-task 重试）" % task_id)

    detail = failure_message or failure_code or status or "unknown"
    if status == "billing_failed":
        fail(E_FAILED, "%s已完成但扣点失败：%s task_id=%s（请稍后重试或联系支持）"
             % (MODE_LABEL.get(mode, mode), detail, task_id))
    if status == "failed":
        tip = "%s任务失败：%s task_id=%s" % (MODE_LABEL.get(mode, mode), detail, task_id)
        tip += "。可用 --retry-task %s 重试。" % task_id if task_id else ""
        fail(E_FAILED, tip)

    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, detail, task_id))


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="文案去AI味+真人点评（异步任务 API · v0.2.0）")
    ap.add_argument("--text", default=None, help="待处理文案，或文件路径，或 '-' 读 stdin")
    ap.add_argument("--mode", default=None, required=False,
                    help="rewrite(去AI味改写) / eval(真人评估)。必填。")
    ap.add_argument("--platform", default="xhs",
                    help="xhs(小红书) / channels(视频号) / mp(公众号) / dy(抖音)，默认 xhs")
    ap.add_argument("--personas", default=None,
                    help="读者 CSV，如 '25-34-女-白领-高消费,35-44-女-宝妈-中消费'（仅 eval 生效）")
    ap.add_argument("--comment-count", type=int, default=None,
                    help="模拟评论条数（仅 eval 生效，其他声音 = max(0, count - 读者数)）")
    ap.add_argument("--out", default=None,
                    help="输出 MD 路径；缺省写入当前目录的 报告-<task_id>.md")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s）。到点不是错误——进行中任务 emit 状态后退出 13 可续轮询。"
                    % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--idempotency-key", default=None,
                    help="幂等键；缺省自动生成 UUID。rewrite 与 eval 必须用不同 key。")
    ap.add_argument("--retry-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 调用 POST /tasks/{id}/retry，沿用原 mode")
    ap.add_argument("--only-create", action="store_true",
                    help="仅 POST 创建任务拿 task_id 后即退出（退出码 0，不轮询）；配合 --poll-task 实现拆分轮询。")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；终态交付报告(exit0)；仍运行 emit 进行中(exit13)；终态失败 exit12。")
    args = ap.parse_args()

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "未取到 API Key：技能目录下 config.json 不存在或无 LY_API_KEY 字段。\n"
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
        data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        status = str(data.get("status") or "")
        if status not in STATUS_TERMINAL:
            data, payload, code = wait_for_task(
                base_url, api_key, data, payload, args.timeout, poll_interval,
            )
        else:
            code = E_OK
        status = str(data.get("status") or "")
        if status in STATUS_TERMINAL:
            mode = str(data.get("mode") or "eval")
            text_for_title = (args.text and read_text(args.text).strip()) or ("任务 %s" % task_id[:8])
            if not (args.text and read_text(args.text).strip()):
                log("提示：--poll-task 未带 --text，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --text。"
                    % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(
                data, payload, text_for_title, mode,
            )
            _emit(final_md, used_points, plan_points_for(mode), args.out, task_id_out, mode)
            return
        _emit_pending(data, task_id, int(args.timeout))
        return

    # —— 重试模式 ——
    if args.retry_task:
        task_id = args.retry_task.strip()
        if not task_id:
            fail(E_PARAM, "--retry-task 不能为空。")
        data, payload = call_retry_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        data, payload, code = wait_for_task(
            base_url, api_key, data, payload, args.timeout, poll_interval,
        )
        if code == E_PENDING:
            _emit_pending(data, task_id, int(args.timeout))
            return
        mode = str(data.get("mode") or "eval")
        text_for_title = (args.text and read_text(args.text).strip()) or ("任务 %s" % task_id[:8])
        final_md, used_points, task_id_out = handle_task_outcome(
            data, payload, text_for_title, mode,
        )
        _emit(final_md, used_points, plan_points_for(mode), args.out, task_id_out, mode)
        return

    # —— 新建/仅创建任务 ——
    # mode 必填（创建新任务时）
    if not args.mode:
        fail(E_PARAM, "请提供 --mode rewrite 或 --mode eval。")
    mode = args.mode.strip().lower()
    if mode not in MODES:
        fail(E_PARAM, "--mode 必须是 rewrite 或 eval，当前：%s" % args.mode)

    if not args.text:
        fail(E_PARAM, "请提供 --text，或使用 --retry-task <task_id>。")

    if args.platform not in PLATFORMS:
        fail(E_PARAM, "platform 必须是 xhs/channels/mp/dy，当前：%s" % args.platform)
    text = read_text(args.text)
    if not text.strip():
        fail(E_PARAM, "待处理文案为空。")
    text = text.strip()
    if len(text) > 20000:
        fail(E_PARAM, "待处理文案超过 20000 字符上限（当前 %d）。" % len(text))

    log("将执行：%s" % MODE_LABEL.get(mode, mode))

    # options 仅 eval 生效
    options = {}
    if mode == "eval":
        if args.personas:
            options["personas"] = [s.strip() for s in args.personas.split(",") if s.strip()]
        if args.comment_count is not None:
            if not (1 <= args.comment_count <= 20):
                fail(E_PARAM, "--comment-count 须在 1–20 之间。")
            options["comment_count"] = args.comment_count
    elif args.personas or args.comment_count is not None:
        log("提示：--personas / --comment-count 仅在 eval 模式生效，rewrite 模式已忽略。")

    idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())

    data, payload = call_create_task(
        base_url, api_key, text, mode, args.platform,
        options or None, idem, HTTP_TIMEOUT,
    )

    # 仅创建模式
    if args.only_create:
        task_id = str(data.get("task_id") or "")
        status = str(data.get("status") or "")
        print(TASK_PREFIX + task_id)
        print(MODE_PREFIX + mode)
        print("HUMAN_EVAL_STATUS=" + status)
        print(REPORT_START)
        print(REPORT_END)
        sys.stdout.flush()
        log("已创建任务（仅创建模式）：task_id=%s mode=%s status=%s" % (task_id, mode, status))
        sys.exit(E_OK)

    # 同步等待
    data, payload, code = wait_for_task(
        base_url, api_key, data, payload, args.timeout, poll_interval,
    )
    if code == E_PENDING:
        _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(
        data, payload, text, mode,
    )
    _emit(final_md, used_points, plan_points_for(mode), args.out, task_id_out, mode)


def _emit_pending(data, task_id, elapsed):
    status = str(data.get("status") or "")
    mode = str(data.get("mode") or "")
    mode_label = MODE_LABEL.get(mode, mode)
    print(TASK_PREFIX + (task_id or ""))
    print(MODE_PREFIX + mode)
    print("HUMAN_EVAL_STATUS=" + status)
    print("HUMAN_EVAL_PROGRESS=%s进行中" % mode_label)
    print("HUMAN_EVAL_EAPSED=%d" % int(elapsed or 0))
    print(REPORT_START)
    print(REPORT_END)
    sys.stdout.flush()
    log("进行中：status=%s mode=%s task_id=%s elapsed=%ds，可续 --poll-task。"
        % (status, mode_label, task_id or "-", int(elapsed or 0)))
    sys.exit(E_PENDING)


def _safe_filename_stem(task_id):
    return "".join(c for c in str(task_id or "") if c.isalnum() or c in "-_") or uuid.uuid4().hex


def _write_report_to_disk(final_md, out_path, task_id):
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "报告.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("报告-%s.md" % stem))
    candidates.append(Path("/tmp") / ("报告-%s.md" % stem))

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


def _emit(final_md, used_points, plan_total, out_path, task_id, mode):
    md_path = _write_report_to_disk(final_md, out_path, task_id)

    points_str = fmt_points(used_points)
    print(POINTS_PREFIX + points_str)
    print(PLAN_PREFIX + str(plan_total))
    print(FILE_PREFIX + md_path)
    print(TASK_PREFIX + (task_id or ""))
    print(MODE_PREFIX + mode)
    print(REPORT_START)
    sys.stdout.write(final_md)
    if not final_md.endswith("\n"):
        sys.stdout.write("\n")
    print(REPORT_END)
    sys.stdout.flush()
    log("完成。task_id=%s mode=%s points=%s" % (task_id or "-", mode, points_str or "(empty)"))
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
