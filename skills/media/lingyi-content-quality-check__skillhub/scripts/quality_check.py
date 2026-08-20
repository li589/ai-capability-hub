#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""爆款内容预检（付费版）【零一数科·出品】 —— 联网主脚本 (v0.3.0)

异步任务模型：
  读 Key → 校验参数 → POST /tasks（立即返回 task_id）→
  GET 轮询进度（stderr 输出）→ 终态后提取 billing.total_points →
  按 modules 顺序拼接 results[m].markdown → 写盘 → 分隔符协议输出 stdout。

失败可按 task_id 调用 POST /tasks/{id}/retry（异步，再轮询；已成功模块不重跑）。

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
TASKS_PATH = "/api/v1/content-quality/tasks"
PLATFORMS = {"channels", "mp"}

DEFAULT_TIMEOUT = 90  # 单次轮询等待上限（秒）；WorkBuddy/Web 单轮调用有上限，留安全余量；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60  # 单次 HTTP 超时（创建/retry/get 均应快速返回）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5  # 轮询间隔（秒）

MODULES = ("compliance", "persona", "burst")
MODULE_LABEL = {
    "compliance": "合规检测",
    "persona": "人群反馈与用户评论",
    "burst": "爆款概率预测",
}
MODULE_ALIASES = {
    "compliance": "compliance", "c": "compliance", "合规": "compliance",
    "persona": "persona", "p": "persona", "人群": "persona",
    "burst": "burst", "b": "burst", "爆款": "burst",
}

# 约定回退扣点（仅「约 N 点」提示，不当作实扣）
PLAN_POINTS = {
    "compliance": 8,
    "persona": 22,
    "burst": 8,
}
FALLBACK_PLAN_TOTAL = 38

# 任务成功态；其余需要按失败处理（可重试）
STATUS_OK = "succeeded"
STATUS_TERMINAL = frozenset({
    "succeeded", "failed", "partial_failed", "billing_failed",
})
STATUS_RETRYABLE = frozenset({
    "failed", "partial_failed", "billing_failed", "pending", "running",
})

# 退出码
E_OK = 0
E_NO_KEY = 2
E_PARAM = 3
E_BALANCE = 4
E_AUTH = 8
E_4XX = 10
E_5XX = 11
E_FAILED = 12  # 已发起但中途失败
E_PENDING = 13  # 已发起但未到终态（轮询单次超时）；非失败，可续 --poll-task

# stdout 交付协议
POINTS_PREFIX = "CONTENT_QUALITY_POINTS_USED="
PLAN_PREFIX = "CONTENT_QUALITY_PLAN_POINTS="
REPORT_START = "=== CONTENT_QUALITY_REPORT_START ==="
REPORT_END = "=== CONTENT_QUALITY_REPORT_END ==="
FILE_PREFIX = "CONTENT_QUALITY_REPORT_FILE="
TASK_PREFIX = "CONTENT_QUALITY_TASK_ID="

SECTION_SEPARATOR = "\n\n---\n\n"

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


# --------------------------------------------------------------------------- 工具
def log(msg):
    print("[quality_check] %s" % msg, file=sys.stderr, flush=True)


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
        # 服务端兼容 Bearer 与裸 key；与其它 SKILL 对齐优先 Bearer
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


def read_text(arg):
    """--text 可为：文件路径、'-' 读 stdin、或直接文本。"""
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg).expanduser()
    if p.is_file():
        return p.read_text("utf-8")
    return arg


def http_request(url, method, headers, body, timeout):
    """发起 HTTP 请求，返回 (status, body_text)。URLError 上抛。"""
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
            # 5xx 也可重试
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
    """提取正式扣点字段 billing.total_points。

    优先：data.billing.total_points / billing.total_points
    回退：若干历史候选 key（兼容旧响应）。
    命中返回数值（int/float），否则 None。
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

    # 兼容旧字段
    legacy_keys = (
        "points_used", "credits_used", "used_points", "deducted_points",
        "charged_points", "points_cost", "point_used", "consumed_points",
        "billing_points", "spent_points", "cost_points",
    )
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


# --------------------------------------------------------------------------- --only 解析
def parse_only(raw):
    if raw is None or not str(raw).strip():
        return list(MODULES)
    tokens = [t.strip() for t in str(raw).split(",") if t.strip()]
    if not tokens:
        return list(MODULES)
    normalized = []
    invalid = []
    for tk in tokens:
        key = MODULE_ALIASES.get(tk.lower()) or MODULE_ALIASES.get(tk)
        if key is None:
            invalid.append(tk)
        elif key not in normalized:
            normalized.append(key)
    if invalid:
        fail(E_PARAM, "--only 含非法值：%s。可选：compliance/c/合规、persona/p/人群、burst/b/爆款。"
             % ", ".join(invalid))
    return [m for m in MODULES if m in normalized]


# --------------------------------------------------------------------------- HTTP 错误分流
def raise_for_http(status, payload, resp_text, label):
    """按 HTTP 状态码 fail()。payload 可为 None。"""
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


# --------------------------------------------------------------------------- 调统一任务 API
def _parse_task_response(status, resp_text, label):
    """解析任务类接口响应，返回 (data, payload)。"""
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


def _module_progress_summary(data):
    """从任务 data 汇总模块进度文案。"""
    modules = list(data.get("modules") or [])
    results = data.get("results") if isinstance(data.get("results"), dict) else {}
    current = data.get("current_module")
    done = []
    pending = []
    for m in modules:
        item = results.get(m)
        md = ""
        mod_status = ""
        if isinstance(item, dict):
            md = str(item.get("markdown") or "").strip()
            mod_data = item.get("data") if isinstance(item.get("data"), dict) else {}
            mod_status = str(mod_data.get("status") or "")
        label = MODULE_LABEL.get(m, m)
        if md or mod_status == "succeeded":
            done.append(label)
        elif m == current or mod_status == "running":
            pending.append("%s(进行中)" % label)
        else:
            pending.append(label)
    parts = []
    if done:
        parts.append("已完成：%s" % "、".join(done))
    if current:
        parts.append("当前：%s" % MODULE_LABEL.get(str(current), current))
    elif pending:
        parts.append("待完成：%s" % "、".join(pending))
    return "；".join(parts) if parts else "等待调度"


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    """向 stderr 输出人类可读进度（供 agent / 用户观测）。"""
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    summary = _module_progress_summary(data)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s%s task_id=%s | %s"
        % (prefix, status or "?", elapsed_s, task_id or "-", summary))
    if emit_task_id and task_id:
        # 尽早透出一次，方便用户中途询问进度 / 失败后重试
        print("[quality_check] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, text, platform, modules, options, idempotency_key, timeout):
    """POST /tasks（异步）：立即返回含 task_id 的快照。"""
    url = base_url.rstrip("/") + TASKS_PATH
    body_obj = {
        "text": text,
        "platform": platform,
        "modules": modules,
        "idempotency_key": idempotency_key,
    }
    if options:
        body_obj["options"] = options
    body = json.dumps(body_obj, ensure_ascii=False)
    label = "创建质检任务"
    log("%s：modules=%s text_len=%d platform=%s key=%s"
        % (label, ",".join(modules), len(text), platform, idempotency_key[:8] + "…"))

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
    """GET /tasks/{task_id}，返回 data dict。"""
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id
    label = "查询质检任务"
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
    """POST /tasks/{task_id}/retry（异步）：立即返回快照。"""
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id + "/retry"
    label = "重试质检任务"
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
    """轮询 GET 直到任务终态或单次超时。

    返回 (data, payload, exit_code)：终态返回 E_OK；单次轮询到上限返回 E_PENDING（非失败）。
    期间 stderr 输出进度（含早期 task_id）。
    """
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
            # 单次轮询到点：不当作失败，返回 E_PENDING，由调用方 emit 进行中状态、续轮询。
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


def _extract_one_markdown(item):
    """从 results.<module> 的单元素多种形态取 markdown 字符串。

    兼容形态：
      - {"markdown": "..."}
      - {"data": {"markdown": "..."}}（嵌套）
      - "..."（直接字符串）
      - {"data": {..., "results": {"markdown": "..."}}} 等更深处也试一次
    返回 stripped 字符串，无则空串。
    """
    if item is None:
        return ""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        md = item.get("markdown")
        if not md:
            inner = item.get("data")
            if isinstance(inner, dict):
                md = inner.get("markdown")
                if not md:
                    # 再深一层 results
                    inner2 = inner.get("results")
                    if isinstance(inner2, dict):
                        md = inner2.get("markdown")
        return str(md or "").strip()
    return ""


def extract_module_markdowns(data, modules):
    """从统一任务 results 中按 modules 顺序提取 markdown。

    兼容 results.<module> = { markdown } / { data: { markdown } } / "..." 等多种形态。
    某模块取不到不中断，记录到 missing；顺带用 results 实际 key 兜底
    （防止传入 modules 与服务端 key 对不上导致全部 missing）。
    返回 ([(module, markdown_str), ...], [missing_label, ...])。
    """
    results = data.get("results") or {}
    if not isinstance(results, dict):
        results = {}

    # 传入 modules 优先；若全部取不到，再用 results 实际 key 兜底
    order = list(modules) if modules else []
    used_fallback = False
    collected = {}
    for m in order:
        collected[m] = _extract_one_markdown(results.get(m))

    if order and not any(collected.values()) and results:
        # 全没取到但 results 非空：用 results 实际 key 兜底
        order = [k for k in results.keys()]
        used_fallback = True
        collected = {k: _extract_one_markdown(results.get(k)) for k in order}

    out = []
    missing = []
    for m in order:
        md = collected.get(m) or ""
        if md:
            out.append((m, md))
        else:
            item = results.get(m)
            err = ""
            if isinstance(item, dict):
                mod_data = item.get("data")
                if isinstance(mod_data, dict):
                    err = mod_data.get("error_message") or mod_data.get("status") or ""
            missing.append("%s%s" % (MODULE_LABEL.get(m, m), ("（%s）" % err) if err else ""))
    if used_fallback:
        log("提示：传入 modules 未命中 results，已用 results 实际 key 兜底：%s"
            % ",".join(order))
    return out, missing


def make_title(text):
    title = (text[:20] + "…") if len(text) > 20 else text
    return title.replace("\n", " ").strip() or "质检报告"


def assemble_report(text, module_markdowns, missing=None):
    """拼接最终报告 markdown。

    module_markdowns: [(module, md), ...] 已剔空。
    missing: [label, ...] 缺失模块标签列表；非空时在末尾追加「结果缺失」提示段，
    让用户清楚哪些模块没拿到结果（但仍生成 md，而非整体失败）。
    """
    parts = ["# 质检报告：%s" % make_title(text)]
    clean_sections = []
    for _, md in module_markdowns:
        s = str(md).replace("\r\n", "\n").replace("\r", "\n").strip()
        if s:
            clean_sections.append(s)
    if missing:
        miss_str = "、".join(missing)
        clean_sections.append("## 结果缺失\n\n以下模块未取到结果，可稍后用 `--retry-task` 重试：%s" % miss_str)
    if not clean_sections:
        return parts[0] + "\n"
    return parts[0] + "\n\n" + SECTION_SEPARATOR.join(clean_sections) + "\n"


def plan_points_for(modules):
    return sum(PLAN_POINTS.get(m, 0) for m in modules) or FALLBACK_PLAN_TOTAL


def handle_task_outcome(data, payload, modules, text, allow_partial=False):
    """根据任务 status 产出报告或 fail。

    返回 (final_md, points, task_id)
    """
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    failure_message = data.get("failure_message") or data.get("failure_code") or ""

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status == STATUS_OK:
        module_markdowns, missing = extract_module_markdowns(data, modules)
        if module_markdowns:
            # 有可用 markdown 就生成报告（哪怕部分模块缺失，也尽力落盘 + 标注）
            if missing:
                log("警告：部分模块无 markdown，仍生成报告并标注缺失：%s" % ", ".join(missing))
            return assemble_report(text, module_markdowns, missing=missing), points, task_id
        # 一个 markdown 都没取到：确实无法生成报告
        fail(E_FAILED, "任务成功但无可用 markdown：%s task_id=%s（可用 --retry-task 重试）"
             % (", ".join(missing) if missing else "results 为空", task_id))

    # 部分失败：若已有 markdown，无论是否 --allow-partial 都先尽力落盘（避免用户拿不到任何 md）
    module_markdowns, missing = extract_module_markdowns(data, modules)
    if module_markdowns and status == "partial_failed":
        log("任务部分失败 status=%s，仍交付已成功模块并标注缺失。failure=%s"
            % (status, failure_message))
        return assemble_report(text, module_markdowns, missing=missing), points, task_id

    detail = failure_message or status or "unknown"
    if status == "billing_failed":
        fail(E_FAILED, "质检模块已完成但扣点失败：%s task_id=%s（请稍后重试或联系支持）"
             % (detail, task_id))
    if status in STATUS_RETRYABLE:
        tip = "质检任务未成功：status=%s %s task_id=%s" % (status, detail, task_id)
        if missing:
            tip += "；无结果模块：%s" % ", ".join(missing)
        tip += "。可用 --retry-task %s 重试失败模块。" % task_id if task_id else ""
        fail(E_FAILED, tip)

    fail(E_FAILED, "未知任务状态 status=%s %s task_id=%s" % (status, detail, task_id))


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="内容质检（异步任务 API · v0.3.0）")
    ap.add_argument("--text", default=None, help="待检文本，或文件路径，或 '-' 读 stdin")
    ap.add_argument("--platform", default="channels", help="channels(视频号) / mp(公众号)，默认 channels")
    ap.add_argument("--only", default=None,
                    help="仅跑指定模块（CSV）：compliance,persona,burst；支持别名 c/p/b、合规/人群/爆款。"
                         "缺省 = 三块全跑。")
    ap.add_argument("--personas", default=None,
                    help="人群 CSV，如 '25-34-女-白领-高消费,35-44-女-宝妈-中消费'（仅 persona 模块生效）")
    ap.add_argument("--comment-count", type=int, default=None,
                    help="模拟评论条数（仅 persona 模块生效）")
    ap.add_argument("--out", default=None,
                    help="输出 MD 路径；缺省写入当前目录的 质检报告-<task_id>.md")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s，< WorkBuddy/Web 单轮上限）。到点不是错误——进行中任务 emit 状态后退出 13 可续轮询。" % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--idempotency-key", default=None,
                    help="幂等键；缺省自动生成 UUID。重复提交同一任务请保持不变。")
    ap.add_argument("--retry-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 调用 POST /tasks/{id}/retry，跳过 --text")
    ap.add_argument("--allow-partial", action="store_true",
                    help="partial_failed 时仍交付已成功模块的 markdown")
    ap.add_argument("--only-create", action="store_true",
                    help="仅 POST 创建任务拿 task_id 后即退出（退出码 0，不轮询）；stdout 输出 task_id+初始进度。配合 --poll-task 实现拆分轮询。")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；单次等待上限 --timeout。终态交付报告(exit0)；仍运行 emit 进行中(exit13，非失败，可续轮询)；终态失败 exit12。")
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

    # —— 轮询已有任务（仅轮询，超时 emit 进行中 + exit 13）——
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
            modules = list(data.get("modules") or MODULES)
            text_for_title = (args.text and read_text(args.text).strip()) or ("任务 %s" % task_id[:8])
            if not (args.text and read_text(args.text).strip()):
                log("提示：--poll-task 未带 --text，报告标题退化为「任务 %s」。建议 --poll-task 同时带 --text 以生成「质检报告：<内容>」标题。" % task_id[:8])
            final_md, used_points, task_id_out = handle_task_outcome(
                data, payload, modules, text_for_title, allow_partial=args.allow_partial,
            )
            _emit(final_md, used_points, plan_points_for(modules), args.out, task_id_out)
            return
        # 未到终态（code == E_PENDING）：emit 进行中
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
        modules = list(data.get("modules") or MODULES)
        # 重试模式无原文时用 task 侧结果拼；标题用 task_id 摘要
        text_for_title = (args.text and read_text(args.text).strip()) or ("任务 %s" % task_id[:8])
        final_md, used_points, task_id_out = handle_task_outcome(
            data, payload, modules, text_for_title, allow_partial=args.allow_partial,
        )
        _emit(final_md, used_points, plan_points_for(modules), args.out, task_id_out)
        return

    # —— 仅创建任务（创建后即退，不轮询）——
    if args.only_create:
        if not args.text:
            fail(E_PARAM, "--only-create 仍需 --text 提供待检文本。")
        if args.platform not in PLATFORMS:
            fail(E_PARAM, "platform 必须是 channels(视频号) 或 mp(公众号)，当前：%s" % args.platform)
        text = read_text(args.text)
        if not text.strip():
            fail(E_PARAM, "待检文本为空。")
        text = text.strip()
        if len(text) > 20000:
            fail(E_PARAM, "待检文本超过 20000 字符上限（当前 %d）。" % len(text))
        modules = parse_only(args.only)
        if not modules:
            fail(E_PARAM, "--only 解析后为空集合，请至少选一个模块。")
        options = {}
        if "persona" in modules:
            if args.personas:
                options["personas"] = [s.strip() for s in args.personas.split(",") if s.strip()]
            if args.comment_count is not None:
                if not (1 <= args.comment_count <= 20):
                    fail(E_PARAM, "--comment-count 须在 1–20 之间。")
                options["comment_count"] = args.comment_count
        idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
        data, payload = call_create_task(
            base_url, api_key, text, args.platform, modules,
            options or None, idem, HTTP_TIMEOUT,
        )
        task_id = str(data.get("task_id") or "")
        status = str(data.get("status") or "")
        summary = _module_progress_summary(data)
        print(TASK_PREFIX + task_id)
        print("CONTENT_QUALITY_STATUS=" + status)
        print("CONTENT_QUALITY_PROGRESS=" + summary)
        print(REPORT_START)
        print(REPORT_END)
        sys.stdout.flush()
        log("已创建任务（仅创建模式）：task_id=%s status=%s" % (task_id, status))
        sys.exit(E_OK)

    # —— 新建任务 ——
    if not args.text:
        fail(E_PARAM, "请提供 --text，或使用 --retry-task <task_id>。")

    if args.platform not in PLATFORMS:
        fail(E_PARAM, "platform 必须是 channels(视频号) 或 mp(公众号)，当前：%s" % args.platform)
    text = read_text(args.text)
    if not text.strip():
        fail(E_PARAM, "待检文本为空。")
    text = text.strip()
    if len(text) > 20000:
        fail(E_PARAM, "待检文本超过 20000 字符上限（当前 %d）。" % len(text))

    modules = parse_only(args.only)
    if not modules:
        fail(E_PARAM, "--only 解析后为空集合，请至少选一个模块。")
    log("将调用模块：%s" % ", ".join(MODULE_LABEL[m] for m in modules))

    options = {}
    if "persona" in modules:
        if args.personas:
            options["personas"] = [s.strip() for s in args.personas.split(",") if s.strip()]
        if args.comment_count is not None:
            if not (1 <= args.comment_count <= 20):
                fail(E_PARAM, "--comment-count 须在 1–20 之间。")
            options["comment_count"] = args.comment_count
    elif args.personas or args.comment_count is not None:
        log("提示：--personas / --comment-count 仅在 persona 模块启用时生效，本次已忽略。")

    idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())

    data, payload = call_create_task(
        base_url, api_key, text, args.platform, modules,
        options or None, idem, HTTP_TIMEOUT,
    )
    data, payload, code = wait_for_task(
        base_url, api_key, data, payload, args.timeout, poll_interval,
    )
    if code == E_PENDING:
        _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(
        data, payload, modules, text, allow_partial=args.allow_partial,
    )
    _emit(final_md, used_points, plan_points_for(modules), args.out, task_id_out)


def _emit_pending(data, task_id, elapsed):
    """单次轮询未到终态：透出进行中状态，退出码 E_PENDING（非失败，可续轮询）。

    stdout 协议（agent 据此续 --poll-task）：
      CONTENT_QUALITY_TASK_ID=<id>
      CONTENT_QUALITY_STATUS=<status>
      CONTENT_QUALITY_PROGRESS=<人类可读模块进度>
      CONTENT_QUALITY_EAPSED=<已用秒>
      === CONTENT_QUALITY_REPORT_START ===
      (空正文：进行中无报告)
      === CONTENT_QUALITY_REPORT_END ===
    """
    status = str(data.get("status") or "")
    summary = _module_progress_summary(data)
    print(TASK_PREFIX + (task_id or ""))
    print("CONTENT_QUALITY_STATUS=" + status)
    print("CONTENT_QUALITY_PROGRESS=" + summary)
    print("CONTENT_QUALITY_EAPSED=%d" % int(elapsed or 0))
    print(REPORT_START)
    print(REPORT_END)
    sys.stdout.flush()
    log("进行中：status=%s task_id=%s elapsed=%ds，可续 --poll-task。"
        % (status, task_id or "-", int(elapsed or 0)))
    sys.exit(E_PENDING)


def _safe_filename_stem(task_id):
    return "".join(c for c in str(task_id or "") if c.isalnum() or c in "-_") or uuid.uuid4().hex


def _write_report_to_disk(final_md, out_path, task_id):
    """把报告 md 落盘，三级兜底确保「必生成 md」。

    顺序：1) --out 指定路径 → 2) 当前工作目录 质检报告-<id>.md → 3) /tmp/质检报告-<id>.md。
    任一成功即返回绝对路径；全失败返回 ""（仅极端不可写环境才会）。
    每级独立 try，失败不中断、继续下一级。
    """
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "质检报告.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("质检报告-%s.md" % stem))
    candidates.append(Path("/tmp") / ("质检报告-%s.md" % stem))

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
