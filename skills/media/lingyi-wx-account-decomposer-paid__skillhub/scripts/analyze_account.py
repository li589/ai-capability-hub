#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号账号拆解分析编排脚本。

接收一个视频号【账号名称】（昵称），自动完成：
  发起拆解（POST account_name）→ 取 task_id
  → 轮询进度 → 输出 Markdown 报告

进度打到 stderr 供调用方（assistant）转述，最终报告用分隔符包裹打到 stdout。
纯标准库实现（urllib），无第三方依赖。

用法：
    python3 analyze_account.py "<账号名称>" \
        [--platform <平台>] [--out PATH] [--max-wait 600] [--interval 8]
    python3 analyze_account.py "<账号名称>" --estimate-only
        # 只创建任务、拿 task_id 与预计扣点后即退出（不轮询），
        # 让助手在确认前先把预计扣点告诉用户；确认后再用下行轮询。
    python3 analyze_account.py --task-id <id> [--out PATH] [--max-wait 600]

API Key：
    自动从「技能目录」下的 config.json 的 LY_API_KEY 字段读取
    （技能目录 = scripts/ 的上一级，即 SKILL.md 所在目录）。
    兼容环境变量 LY_API_KEY 作为回退。
    请求头 Authorization: Bearer <api_key>。

base url 默认 https://claw.lingyishuke.com/services（写死在脚本里）。

退出码：
    0   成功，报告已输出
    2   输入错误（未给账号名称 / 为空）
    3   未取到 API Key 或鉴权失效（401/403）
    4   发起拆解失败（含余额不足，附充值链接）
    5   任务失败（status=failed）
    6   创建/轮询阶段的网络 / 429 / 任务失效（404）
    7   completed 但报告为空
    124 等待超时

============================================================================
接口契约 —— 与 references/api.md 一一对应
----------------------------------------------------------------------------
请求体、响应字段名集中在下方常量区维护，后端契约变动时改这一处即可。
============================================================================
"""

import argparse
import json
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
PATH_CREATE = "/api/v1/common-gateway/analysis-skill/wx-video-account-analysis"
PATH_STATUS = "/api/v1/common-gateway/analysis-skill/wx-video-account-analysis/{task_id}"

# --- 请求/响应字段名 -------------------------------------------------------
# 创建任务响应里取任务 id 的 key
F_TASK_ID = "task_id"
F_TASK_ID_ALIASES = ("task_id", "taskId", "analysis_task_id", "analysisTaskId")
# 余额不足判定 + 充值链接 key
F_RECHARGE_URL = "recharge_url"
# 本次实际扣点的高置信字段（命中才直接报数，否则交由调用方按 ≈168 估算；
# 含 total_points：服务端完成态常以此字段给出本次真实扣点；预估约 168 点，
# 实际扣点按任务复杂度而定）
F_POINTS_USED = ("points_used", "credits_used", "used_points", "deducted_points",
                 "charged_points", "points_cost", "point_used", "consumed_points",
                 "billing_points", "spent_points", "cost_points",
                 "estimated_points", "estimated_cost", "points_estimate",
                 "points_required", "points_needed", "expected_points", "points",
                 "total_points")

DEFAULT_MAX_WAIT = 600
DEFAULT_INTERVAL = 8  # 文档建议轮询 5～15s，取中位附近
MAX_BACKOFF = 30
POLL_RETRY_TIMES = 4
HTTP_RETRY_TIMES = 4
# 服务端有时先置 completed，过几秒才写入 markdown；命中此竞态时
# 在该宽限窗口内继续轮询，等报告落库，避免误报"完成但报告为空"。
COMPLETED_REPORT_GRACE_SECONDS = 60
# 轮询进度保活间隔：即使状态/阶段没变，每过这么久也向 stderr 补一行（更新已等待时长），
# 让调用方有东西可转述，避免长时间沉默被用户误认为卡住。
PROGRESS_KEEPALIVE_SECONDS = 30

# urllib 默认用系统/编译期证书链做校验。设环境变量 LY_SKIP_SSL_VERIFY=1 可跳过
# （仅用于 macOS 缺证书、企业代理中间人等无法正常校验的环境）。
if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()

REPORT_START = "=== ACCOUNT_REPORT_START ==="
REPORT_END = "=== ACCOUNT_REPORT_END ==="

STATUS_LABEL = {
    "pending": "排队中",
    "running": "执行中",
    "completed": "完成",
    "failed": "失败",
    "QUEUED": "排队中",
    "PENDING": "等待中",
    "COMPLETED": "完成",
    "FAILED": "失败",
    "SUCCESS": "完成",
    "DONE": "完成",
    "ERROR": "失败",
}

COMPLETED_STATUSES = {"completed", "success", "done"}
FAILED_STATUSES = {"failed", "error"}

# 服务端 steps_timing 里的 stage 标识 → 中文，用于把进度阶段转述给用户。
# （样例完成态有 steps_timing；若 running 态也开始返回，按这里映射成中文。）
STAGE_LABEL = {
    "data_fetch": "数据采集",
    "video_deconstruct": "视频拆解",
    "context_derivation": "上下文推导",
    "knowledge_injection": "知识注入",
    "account_analysis_node": "账号分析",
    "scoring_call": "爆款评分",
    "result_assemble": "结果组装",
    "backflow_submit": "回流提交",
}


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
    """Authorization: Bearer <api_key>；创建接口带 Content-Type: application/json。"""
    headers = {"Authorization": "Bearer " + api_key}
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
    由调用方按约 168 点回退，避免向付费用户报错误数字）。在 payload 自身及
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


def _fmt_points(p):
    """把点数格式化成展示用字符串。"""
    if p is None or isinstance(p, bool):
        return ""
    try:
        f = float(p)
        return str(int(f)) if f.is_integer() else str(f)
    except (TypeError, ValueError):
        return str(p)


def extract_progress(data):
    """从轮询响应里尽量提取「当前阶段 / 进度文案 / 进度百分比」。

    真实接口在 pending/running 阶段通常不返回这些字段（样例只有完成态的
    steps_timing）。本函数做兼容：有就用，没有返回 (None, None, None)，
    由调用方按 status + 已耗时回退反馈，绝不伪造。

    返回 (stage_zh, progress_message, percent)：
      - stage_zh：当前阶段中文名（优先 current_stage，回退 steps_timing 里有
        duration_ms>0 的最后阶段，并映射 STAGE_LABEL）
      - progress_message：服务端进度文案
      - percent：0~100 的进度百分比（progress / progress_percent / percent）
    """
    if not isinstance(data, dict):
        return (None, None, None)
    stage_raw = data.get("current_stage") or data.get("stage")
    pmsg = data.get("progress_message") or data.get("progress_msg") or data.get("message")
    percent = None
    for k in ("progress_percent", "progressPercent", "percent", "progress"):
        v = data.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            percent = float(v)
            if 0 <= percent <= 1:  # 0~1 归一成 0~100
                percent = percent * 100
            break

    stage_zh = None
    if isinstance(stage_raw, str) and stage_raw.strip():
        stage_zh = STAGE_LABEL.get(stage_raw.strip(), stage_raw.strip())
    else:
        # 回退：从 steps_timing 取最后一个有耗时的阶段作为「已推进到」的提示。
        st = data.get("steps_timing")
        if isinstance(st, dict) and st:
            last = None
            for k, v in st.items():
                if isinstance(v, dict) and isinstance(v.get("duration_ms"), (int, float)) \
                        and v["duration_ms"] > 0:
                    last = (v.get("stage") or k.replace("_timing_", "")).strip()
            if last:
                stage_zh = STAGE_LABEL.get(last, last)

    return (stage_zh,
            (pmsg.strip() if isinstance(pmsg, str) else None),
            percent)


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
# 输入识别：账号名称
# ---------------------------------------------------------------------------

def classify_input(raw):
    """返回 ('account', name) 或 ('none', None)。

    账号名称为任意非空字符串（不做 host/格式判断，保持通用）。
    """
    raw = (raw or "").strip()
    if not raw:
        return ("none", None)
    return ("account", raw)


# ---------------------------------------------------------------------------
# 发起拆解
# ---------------------------------------------------------------------------

def create_task(base_url, api_key, account_name, platform=None):
    """发起账号拆解任务，返回 (task_id, points)。失败按退出码终止。"""
    url = base_url.rstrip("/") + PATH_CREATE
    body_obj = {"account_name": account_name}
    if platform:
        body_obj["platform"] = platform
    body = json.dumps(body_obj, ensure_ascii=False)

    label = account_name + ("（platform=%s）" % platform if platform else "")
    log("发起账号拆解任务：%s" % label)
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

    data = payload.get("data") or {}
    msg = payload.get("message") or ""
    detail = payload.get("detail")
    trace_id = payload.get("trace_id")
    recharge = data.get(F_RECHARGE_URL)
    # 余额不足：402 或 message 命中关键词
    if status == 402 or "余额不足" in msg or "点数不足" in msg or recharge:
        tip = "余额不足，无法发起账号拆解。"
        if recharge:
            tip += " 请前往充值：%s" % recharge
        else:
            tip += " 请前往 https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy 充值。"
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
    log("任务已创建：task_id=%s%s" % (task_id,
        ("（本次预计/已扣点数：%s）" % _fmt_points(points) if points is not None else "")))
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


def _status_key(status):
    """状态值归一为小写字符串，兼容大写枚举。"""
    return str(status or "unknown").strip().lower()


def poll_loop(base_url, api_key, task_id, max_wait, interval):
    """轮询直到终态或超时。返回 (status, data, error_message_or_none)。

    向 stderr 输出进度，供调用方（assistant）转述给用户，避免长时间沉默：
      - 状态/阶段/进度文案/百分比任一变化 → 立刻打一行；
      - 否则每 30s 打一行保活（更新已等待时长），让用户知道仍在推进。
    进度字段优先用服务端返回的 current_stage / progress_message / progress_percent；
    这些字段缺失时（真实接口在 pending/running 通常不返回），回退用「状态 + 已等待时长」。
    """
    deadline = time.monotonic() + max_wait
    start = time.monotonic()
    last_log = 0.0
    last_signature = None
    backoff = interval

    def emit_progress(data):
        """返回 (status_key, signature, printed)。printed=True 表示实际打到了 stderr。"""
        raw_status = data.get("status", "unknown")
        status_key = _status_key(raw_status)
        elapsed = int(time.monotonic() - start)
        stage_zh, pmsg, percent = extract_progress(data)
        signature = (status_key, stage_zh, pmsg, percent)
        now = time.monotonic()
        # 变化就打；没变化但距上次输出已过保活间隔也打（更新已等待时长）
        if signature == last_signature and (now - last_log) < PROGRESS_KEEPALIVE_SECONDS:
            return status_key, signature, False
        label = STATUS_LABEL.get(status_key) or STATUS_LABEL.get(str(raw_status)) or raw_status
        parts = ["[%s]" % label, "已等待%ds" % elapsed]
        if stage_zh:
            parts.append("当前阶段：%s" % stage_zh)
        if pmsg:
            parts.append(pmsg)
        if percent is not None:
            parts.append("进度：%d%%" % round(percent))
        elif status_key in ("pending", "running") and not stage_zh and not pmsg:
            # 服务端没给进度细节时，明确告诉用户任务仍在推进，别误以为卡住
            parts.append("服务端处理中，请稍候…")
        log(" · ".join(parts))
        return status_key, signature, True

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

        status_key, sig, printed = emit_progress(data)
        if printed:
            last_signature = sig
            last_log = time.monotonic()

        if status_key in COMPLETED_STATUSES:
            if build_report(data):
                return ("completed", data, None)
            # 竞态：status 已 completed 但报告结构尚未落库。
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
                if build_report(data):
                    return ("completed", data, None)
                if _status_key(data.get("status", "")) in FAILED_STATUSES:
                    return ("failed", data, _extract_error(data) or "账号拆解失败")
            return ("completed", data, None)
        if status_key in FAILED_STATUSES:
            return ("failed", data, _extract_error(data) or "账号拆解失败")
        if time.monotonic() > deadline:
            return ("TIMEOUT", data, None)
        time.sleep(interval)


# ---------------------------------------------------------------------------
# 报告规整与交付
# ---------------------------------------------------------------------------

def normalize_markdown(md):
    """规整服务端返回的 markdown，尽量保证是可渲染的合法 markdown。

    处理：二次转义（字面 \\n 还原为换行）、首尾引号/code fence/<markdown> 包裹去除。
    校验：规整后是否以 # 开头或含 ## / - / |（表格）等 markdown 标记。
    返回 (normalized_md, looks_valid)。
    """
    if not isinstance(md, str) or not md.strip():
        return md, False
    out = md

    # 字面转义还原：若没有真实换行却出现 \n 字面，多为被二次 JSON 转义
    if "\n" not in out and "\\n" in out:
        out = out.replace("\\n", "\n").replace('\\"', '"').replace("\\t", "\t")
    if "\\r" in out:
        out = out.replace("\\r\\n", "\n").replace("\\r", "\n")

    out = out.strip()
    # 去掉首尾成对引号包裹
    if len(out) >= 2 and out[0] == '"' and out[-1] == '"':
        out = out[1:-1].strip()
    # 去掉首尾成对 ``` 包裹
    m = re.match(r"^```[a-zA-Z]*\s*\n", out)
    if m and out.rstrip().endswith("```"):
        out = out[m.end():].rsplit("```", 1)[0].strip()
    # 去掉 <markdown>...</markdown> 包裹
    out = re.sub(r"(?is)^<markdown>\s*\n", "", out)
    out = re.sub(r"(?is)\n</markdown>\s*$", "", out).strip()

    looks_valid = bool(out.startswith("#") or re.search(r"(^|\n)##\s", out)
                       or re.search(r"(^|\n)-\s", out) or "|" in out)
    return out, looks_valid


# ---------------------------------------------------------------------------
# 报告渲染：真实接口返回结构化 JSON（data.result.sections 或 data.report_v2），
# 并不返回现成的 data.markdown。这里把结构化结果渲染成 Markdown 报告。
# 若服务端某天开始返回 data.markdown，优先用它。
# ---------------------------------------------------------------------------

# v2 schema (data.report_v2) 的 8 块顺序与标题
V2_BLOCK_TITLES = [
    ("account", "账号信息"),
    ("overview", "账号概览"),
    ("portrait", "受众画像"),
    ("content_structure", "内容结构分析"),
    ("videos", "视频逐条拆解"),
    ("explosive_formula", "爆款公式"),
    ("competitors", "竞品对标分析"),
    ("recommendations", "运营建议"),
]


def _scalar_str(v):
    """标量值渲染。None→—，bool→是/否，float 尽量去掉无意义尾零。"""
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return ("%.4f" % v).rstrip("0").rstrip(".")
    return str(v)


def json_to_md(value, level=0):
    """把任意 JSON 值渲染成可读的 Markdown 片段（缩进 bullet 列表），不含标题。

    level 控制缩进层级，用于嵌套。对任意结构都安全，空容器给占位文案。
    """
    pad = "  " * level
    if isinstance(value, dict):
        if not value:
            return pad + "（空）"
        lines = []
        for k, v in value.items():
            if str(k).startswith("_"):
                # 跳过 _meta / _score_breakdown 等内部元数据
                continue
            if isinstance(v, (dict, list)) and _has_content(v):
                lines.append("%s- **%s**：" % (pad, k))
                lines.append(json_to_md(v, level + 1))
            else:
                lines.append("%s- **%s**：%s" % (pad, k, _scalar_str(v)))
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return pad + "（无）"
        lines = []
        for idx, item in enumerate(value, 1):
            if isinstance(item, dict):
                # dict 列表：序号 + 其字段作为深层 bullet
                title = _inline_dict_title(item)
                head = "%s%d." % (pad, idx)
                lines.append(head + (" " + title if title else ""))
                inner = json_to_md(item, level + 1)
                if inner.strip():
                    lines.append(inner)
            elif isinstance(item, list):
                lines.append("%s%d." % (pad, idx))
                lines.append(json_to_md(item, level + 1))
            else:
                lines.append("%s- %s" % (pad, _scalar_str(item)))
        return "\n".join(lines)
    # 标量
    return pad + _scalar_str(value)


def _has_content(v):
    """dict/list 是否有可渲染内容（忽略 _ 前缀键后仍非空）。"""
    if isinstance(v, list):
        return len(v) > 0
    if isinstance(v, dict):
        return any(not str(k).startswith("_") for k in v.keys())
    return False


def _inline_dict_title(d):
    """给 dict 列表项取一个简短的内联标题（取 name/account/title 字段），便于速览。"""
    for k in ("title", "name", "account", "topic", "format", "hook_type", "script_type", "region"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _render_sections(sections):
    """渲染 v1/v1c schema：data.result.sections[]。返回 Markdown 字符串。"""
    lines = ["# 微信视频号账号拆解报告", ""]
    ordered = sorted(
        [s for s in sections if isinstance(s, dict)],
        key=lambda x: x.get("order") if isinstance(x.get("order"), (int, float)) else 999,
    )
    for s in ordered:
        title = s.get("title") or s.get("key") or "未命名"
        order = s.get("order")
        if isinstance(order, (int, float)):
            lines.append("## %s. %s" % (int(order), title))
        else:
            lines.append("## %s" % title)
        lines.append("")
        stype = (s.get("section_type") or "").strip()
        content = s.get("content")
        if stype == "markdown" and isinstance(content, str):
            lines.append(content.strip())
        elif isinstance(content, (dict, list)):
            rendered = json_to_md(content)
            if rendered.strip():
                lines.append(rendered)
            else:
                lines.append("（无内容）")
        else:
            lines.append(_scalar_str(content) if content is not None else "（无内容）")
        lines.append("")
    return "\n".join(lines).strip()


def _render_report_v2(report_v2):
    """渲染 v2 schema：data.report_v2。返回 Markdown 字符串。"""
    lines = ["# 微信视频号账号拆解报告", ""]
    for key, title in V2_BLOCK_TITLES:
        if key not in report_v2:
            continue
        lines.append("## %s" % title)
        lines.append("")
        rendered = json_to_md(report_v2[key])
        if rendered.strip():
            lines.append(rendered)
        else:
            lines.append("（无内容）")
        lines.append("")
    # 渲染 v2 中未列入清单的额外块
    for key in report_v2:
        if key in dict(V2_BLOCK_TITLES) or str(key).startswith("_"):
            continue
        lines.append("## %s" % key)
        lines.append("")
        lines.append(json_to_md(report_v2[key]))
        lines.append("")
    return "\n".join(lines).strip()


def build_report(data):
    """从终态 data 构建可交付的 Markdown 报告字符串；无可渲染内容时返回 None。

    优先级：
      1) data.markdown（若服务端真的返回了现成 markdown，直接用）
      2) v1/v1c：data.result.sections[]
      3) v2：data.report_v2
    """
    if not isinstance(data, dict):
        return None
    md = data.get("markdown")
    if isinstance(md, str) and md.strip():
        return md.strip()
    result = data.get("result")
    if isinstance(result, dict):
        sections = result.get("sections")
        if isinstance(sections, list) and sections:
            return _render_sections(sections)
    report_v2 = data.get("report_v2")
    if isinstance(report_v2, dict) and report_v2:
        return _render_report_v2(report_v2)
    return None


def _extract_error(data):
    """从终态 data 多处提取失败原因。返回字符串 or None。

    真实接口 failed 态可能把原因放在 data.error_message（文档）、
    data.errors（list）、或 data.result.errors。"""
    if not isinstance(data, dict):
        return None
    msg = data.get("error_message")
    if isinstance(msg, str) and msg.strip():
        return msg.strip()
    errs = data.get("errors")
    parts = _join_errors(errs)
    if parts:
        return parts
    result = data.get("result")
    if isinstance(result, dict):
        parts = _join_errors(result.get("errors"))
        if parts:
            return parts
    msg2 = data.get("message")
    if isinstance(msg2, str) and msg2.strip() and data.get("result") != "success":
        return msg2.strip()
    return None


def _join_errors(errs):
    if isinstance(errs, list) and errs:
        parts = [str(e).strip() for e in errs if e not in (None, "", [], {})]
        parts = [p for p in parts if p]
        if parts:
            return "；".join(parts)
    if isinstance(errs, str) and errs.strip():
        return errs.strip()
    return None


def deliver_report(data, out_path, task_id, points=None):
    if not isinstance(data, dict):
        data = {}
    markdown = build_report(data)
    # 标记报告来源：是直接取的 markdown，还是本地渲染的结构化结果
    pre_rendered = bool(isinstance(data.get("markdown"), str) and data.get("markdown").strip())
    if not markdown:
        scene = data.get("scene", "") or ""
        errmsg = _extract_error(data) or ""
        log("⚠️ 任务已标记完成，但未能构建可交付的报告内容。")
        log("   scene=%s | status=%s | error_message=%s"
            % (scene or "-", data.get("status", "-"), errmsg or "-"))
        log("   data 既无 markdown，也无 result.sections / report_v2 可渲染。")
        log("   可稍候用 --task-id %s 重新轮询一次；仍为空则联系服务端排查。" % task_id)
        sys.exit(7)

    markdown, looks_valid = normalize_markdown(markdown)
    if not looks_valid:
        log("⚠️ 报告内容疑似非标准 markdown（未识别到标题/列表/表格标记），已按原样输出供核对。")
    if not markdown or not markdown.strip():
        log("⚠️ 报告内容规整后为空。原始响应可解析字段缺失。")
        log("   可稍候用 --task-id %s 重新轮询一次。" % task_id)
        sys.exit(7)

    # 来自服务端现成 markdown 时透出该来源，方便排查；本地渲染的不额外提示
    if pre_rendered:
        log("报告来源：服务端预渲染 markdown")
    else:
        log("报告来源：本地渲染结构化结果（%s）"
            % ("data.result.sections" if isinstance(data.get("result"), dict) and data["result"].get("sections")
               else "data.report_v2"))

    saved = None
    try:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(task_id or "unknown"))
        filename = "wx-account-%s.md" % safe
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

    # 本次实际扣点：优先取终态响应里的扣点字段（含 total_points，完成态常给出本次真实扣点），
    # 回退发起接口给出的扣点；都没有则为空，由调用方按约 168 点回退说明、最终以服务端按任务复杂度计费为准。
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
    print("ACCOUNT_POINTS_USED=" + points_str)
    print("ACCOUNT_REPORT_FILE=" + (saved or ""))
    print(REPORT_START)
    print(markdown)
    print(REPORT_END)
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="微信视频号账号拆解分析")
    parser.add_argument("input", nargs="?", default=None,
                        help="视频号账号名称（昵称）")
    parser.add_argument("--platform", default=None, help="平台，可不传")
    parser.add_argument("--task-id", default=None,
                        help="已有的任务 ID，跳过输入/创建，直接轮询")
    parser.add_argument("--out", default=None, help="报告输出路径（目录或文件）")
    parser.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT, help="整体等待上限（秒）")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="轮询间隔（秒）")
    parser.add_argument("--estimate-only", dest="estimate_only", action="store_true",
                        help="只创建任务、拿到 task_id 与预计扣点后即退出（不轮询）。"
                             "用于让助手在确认前先把预计扣点/成本告诉用户，确认后再用 --task-id 轮询。")
    args = parser.parse_args()

    if not args.task_id and not args.input:
        parser.error("请提供视频号账号名称，或使用 --task-id 恢复已有任务。")
    if args.estimate_only and args.task_id:
        parser.error("--estimate-only 仅用于新建任务（需提供账号名称），恢复任务请直接用 --task-id。")

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
            fail(2, "未识别到有效输入：请提供视频号账号名称（昵称）。")
        task_id, points = create_task(base_url, api_key, value, platform=args.platform)

    # 只估算成本、拿 task_id，不轮询。让助手在确认前把预计扣点告诉用户。
    # 预计扣点：服务端若在创建响应里返回了点数字段就用真实值，否则回退约 168 点（经验估值，
    # 实际扣点按任务复杂度而定，以服务端实际计费为准，可高可低）。
    if args.estimate_only:
        pts = _fmt_points(points)
        estimate_str = pts if pts else "168"
        source = "服务端返回" if pts else "默认估算（服务端未在创建响应里返回点数字段）"
        log("已创建任务、仅估算成本（不轮询）：task_id=%s，预计扣点 %s 点（%s）"
            % (task_id, estimate_str, source))
        print("ACCOUNT_TASK_ID=" + task_id)
        print("ACCOUNT_ESTIMATE_POINTS=" + estimate_str)
        print("ACCOUNT_ESTIMATE_SOURCE=" + source)
        sys.stdout.flush()
        return  # 退出码 0，由助手转告用户、等确认后再用 --task-id 轮询

    log("开始轮询账号拆解状态（最长 %ds，间隔 %ds）...进度会持续打到 stderr" % (args.max_wait, args.interval))
    status, data, err = poll_loop(base_url, api_key, task_id, args.max_wait, args.interval)

    if status == "TIMEOUT":
        log("等待超时：已等待 %ds。当前任务仍在进行，task_id=%s。"
            "可稍后用 --task-id %s 重新轮询恢复。" % (args.max_wait, task_id, task_id))
        sys.exit(124)
    if status == "failed":
        fail(5, "账号拆解失败：%s" % (err or "未知原因"))

    deliver_report(data, args.out, task_id, points)


if __name__ == "__main__":
    main()
