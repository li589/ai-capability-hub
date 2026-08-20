#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号达人匹配编排脚本。

接收候选达人账号列表 + 产品投放需求，自动完成：
  读配置（GET /creator-match/config，可选）
  → 发起达人匹配任务（POST /creator-match）→ 取 task_id
  → 轮询进度（GET /creator-match/{task_id}）→ 输出 Markdown 报告

进度打到 stderr 供调用方（assistant）转述，最终报告用分隔符包裹打到 stdout。
纯标准库实现（urllib），无第三方依赖。

用法：
    # 1) 读取可选枚举（行业/投放类型/价格档位/消费决策类型），让用户挑选项
    python3 creator_match.py --config

    # 2) 创建任务 + 拿到 task_id 与预计扣点（不轮询），供助手确认前报价
    python3 creator_match.py \
        --account "达人A" --account "达人B" \
        --product-name "多功能学习机" --product-price 39 \
        --price-band low --decision-type impulse \
        --selling-point "卖点1" --selling-point "卖点2" \
        --industry education --campaign-type seeding \
        --estimate-only

    # 3) 用户确认后，用 task_id 轮询出报告
    python3 creator_match.py --task-id <task_id> [--out PATH] [--max-wait 1200] [--interval 8]

配置参数 industries / campaign_types / price_band / decision_type 的合法可选值
请以 --config 实时返回为准（用 options[].value 入参，不要用 label）。

API Key：
    自动从「技能目录」下的 config.json 的 LY_API_KEY 字段读取
    （技能目录 = scripts/ 的上一级，即 SKILL.md 所在目录）。
    兼容环境变量 LY_API_KEY 作为回退。
    请求头 Authorization: Bearer <api_key>。

base url 默认 https://claw.lingyishuke.com/services（写死在脚本里）。

退出码：
    0   成功，报告已输出（--config 成功也走 0）
    2   输入错误（未给达人账号 / 产品名为空等）
    3   未取到 API Key 或鉴权失效（401/403）
    4   发起任务失败（含余额不足，附充值链接）
    5   任务失败（status=failed）
    6   创建/轮询阶段的网络 / 429 / 任务失效（404）
    7   completed 但报告为空
    124 等待超时（含 status=timeout 终态，可用 --task-id 恢复）

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
PATH_CONFIG = "/api/v1/common-gateway/analysis-skill/creator-match/config"
PATH_CREATE = "/api/v1/common-gateway/analysis-skill/creator-match"
PATH_STATUS = "/api/v1/common-gateway/analysis-skill/creator-match/{task_id}"

# --- 请求/响应字段名 -------------------------------------------------------
# 创建任务响应里取任务 id 的 key
F_TASK_ID_ALIASES = ("task_id", "taskId", "analysis_task_id", "analysisTaskId")
# 余额不足判定 + 充值链接 key
F_RECHARGE_URL = "recharge_url"
# 本次实际扣点的高置信字段（命中才直接报数，否则回退按 198×达人数 估算；
# 达人匹配任务逐个读取达人账号视频数据，点数消耗大且会浮动，
# 实际扣点按账号数量/达人视频数量而定，以服务端实际计费为准）
F_POINTS_USED = ("points_used", "credits_used", "used_points", "deducted_points",
                 "charged_points", "points_cost", "point_used", "consumed_points",
                 "billing_points", "spent_points", "cost_points",
                 "estimated_points", "estimated_cost", "points_estimate",
                 "points_required", "points_needed", "expected_points", "points",
                 "total_points")

# 达人匹配任务需要逐个读取达人账号视频数据，点数消耗大且随达人数量浮动。
# 平均每读取一个达人账号的视频数据约耗费 198 点，故预估扣点按 198 × 候选达人数 估算。
# 服务端当前版本「通常不会返回」点数字段，回退即用此估值；实际以任务复杂度/服务端计费为准。
POINTS_PER_ACCOUNT = 198

# 达人匹配任务比账号拆解更重（多账号 × 多达人视频研究），放宽等待上限，
# 并对齐 API 文档「建议设置 20 分钟左右的总等待上限」。
DEFAULT_MAX_WAIT = 1200
DEFAULT_INTERVAL = 8  # 文档建议轮询 5～10s
INITIAL_POLL_DELAY = 5  # 文档建议创建后约 5s 再首次轮询
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

REPORT_START = "=== CREATOR_MATCH_REPORT_START ==="
REPORT_END = "=== CREATOR_MATCH_REPORT_END ==="
CONFIG_START = "=== CREATOR_MATCH_CONFIG_START ==="
CONFIG_END = "=== CREATOR_MATCH_CONFIG_END ==="

STATUS_LABEL = {
    "pending": "排队中",
    "running": "执行中",
    "completed": "完成",
    "failed": "失败",
    "timeout": "超时",
    "QUEUED": "排队中",
    "PENDING": "等待中",
    "RUNNING": "执行中",
    "COMPLETED": "完成",
    "FAILED": "失败",
    "TIMEOUT": "超时",
    "SUCCESS": "完成",
    "DONE": "完成",
    "ERROR": "失败",
}

COMPLETED_STATUSES = {"completed", "success", "done"}
FAILED_STATUSES = {"failed", "error"}
TIMEOUT_STATUSES = {"timeout"}

# 字段中文标题映射，给 config 枚举与结构化兜底渲染用。
FIELD_LABELS = {
    "industries": "行业",
    "campaign_types": "投放类型",
    "price_band": "价格档位",
    "decision_type": "消费决策类型",
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
    """Authorization: Bearer <api_key>；创建/配置接口带 Content-Type: application/json。"""
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
    由调用方按约 500 点回退，避免向付费用户报错误数字）。在 payload 自身及
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

    真实接口在 pending/running 阶段通常不返回这些字段。本函数做兼容：有就用，
    没有返回 (None, None, None)，由调用方按 status + 已耗时回退反馈，绝不伪造。

    返回 (stage_zh, progress_message, percent)。
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
        stage_zh = stage_raw.strip()
    elif isinstance(pmsg, str) and pmsg.strip():
        # progress_message 文案里通常已含阶段信息，复用
        stage_zh = None

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
# 配置接口：GET /creator-match/config
# ---------------------------------------------------------------------------

def fetch_config(base_url, api_key):
    """拉取 industries / campaign_types / price_band / decision_type 枚举。

    成功打印 CREATOR_MATCH_CONFIG_START/END 分隔的 JSON（保留原文 data）后退出 0；
    失败按退出码终止（401/403→3，余额/其它非成功→4，网络→6）。
    """
    url = base_url.rstrip("/") + PATH_CONFIG
    log("拉取达人匹配参数配置：%s" % url)
    status = None
    text = ""
    for attempt in range(1, HTTP_RETRY_TIMES + 1):
        try:
            status, text = http_request("GET", url, headers=auth_headers(api_key), timeout=30)
        except urllib.error.URLError as e:
            if attempt >= HTTP_RETRY_TIMES:
                fail(6, "拉取配置网络错误：%s（请检查网络与服务可达性：%s）" % (e, base_url))
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("拉取配置网络错误：%s，%ds 后重试（%d/%d）" % (e, wait, attempt, HTTP_RETRY_TIMES))
            time.sleep(wait)
            continue
        if status >= 500:
            if attempt >= HTTP_RETRY_TIMES:
                fail(6, "拉取配置服务端暂时不可用（HTTP %d），已重试 %d 次仍失败，请稍后重试。"
                    % (status, HTTP_RETRY_TIMES))
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("拉取配置服务端错误 HTTP %d，%ds 后重试（%d/%d）" % (status, wait, attempt, HTTP_RETRY_TIMES))
            time.sleep(wait)
            continue
        break

    if status in (401, 403):
        payload = parse_json(text) or {}
        fail(3, "鉴权失败（HTTP %d）。API Key 无效或已过期，请更新 config.json 中的 LY_API_KEY 后重试。"
                "服务端返回：%s" % (status, payload.get("message") or text[:200]))

    payload = parse_json(text)
    if payload is None:
        fail(4, "拉取配置返回非 JSON（HTTP %d）：%s" % (status, text[:200]))
    if status != 200 or payload.get("result") != "success":
        msg = payload.get("message") or ""
        fail(4, "拉取配置失败：HTTP %s，result=%s，message=%s" % (status, payload.get("result"), msg))

    data = payload.get("data")
    if not isinstance(data, list):
        data = []
    print(CONFIG_START)
    print(json.dumps(data, ensure_ascii=False))
    print(CONFIG_END)
    sys.stdout.flush()
    # 同时打一份人类可读摘要到 stderr，供助手直接转述给用户挑选项（用 value 入参，不用 label）
    _emit_config_summary(data)
    return


def _emit_config_summary(data):
    """把配置数组渲染成易读的清单打到 stderr，供助手转述。"""
    if not data:
        log("（配置接口未返回任何字段）")
        return
    log("可用枚举（创建任务请用 value，不要用 label）：")
    for field in data:
        if not isinstance(field, dict):
            continue
        key = field.get("field", "")
        label = field.get("label") or FIELD_LABELS.get(key, key)
        options = field.get("options") or []
        opt_str = "、".join(
            "%s（value=%s）" % (o.get("label", ""), o.get("value", ""))
            for o in options if isinstance(o, dict)
        )
        log("• %s：%s" % (label, opt_str or "（无）"))


# ---------------------------------------------------------------------------
# 输入组装：候选达人账号 + 产品投放需求
# ---------------------------------------------------------------------------

def build_create_body(accounts, platform, industries, campaign_types, product, extra_data=None):
    """组装创建任务请求体。accounts 1～10 个，product.name / product.selling_points 必填。"""
    body_obj = {
        "platform": platform or "channels",
        "target_accounts": [{"account": a} for a in accounts if a],
    }
    if industries:
        body_obj["industries"] = industries
    if campaign_types:
        body_obj["campaign_types"] = campaign_types
    # product 是必填对象，至少含 name + selling_points
    if product:
        clean = {}
        for k in ("name", "price", "price_band", "decision_type", "selling_points"):
            if k in product and product[k] not in (None, "", []):
                clean[k] = product[k]
        body_obj["product"] = clean
    if extra_data is not None:
        body_obj["extra_data"] = extra_data
    body_obj["origin"] = "01workbuddy"
    body_obj["origin_method"] = "skill"
    return body_obj


# ---------------------------------------------------------------------------
# 发起达人匹配任务
# ---------------------------------------------------------------------------

def create_task(base_url, api_key, body_obj):
    """发起达人匹配任务，返回 (task_id, points)。失败按退出码终止。"""
    url = base_url.rstrip("/") + PATH_CREATE
    body = json.dumps(body_obj, ensure_ascii=False)

    label = "候选达人 %d 个" % len(body_obj.get("target_accounts", []))
    log("发起达人匹配任务：%s" % label)
    status = None
    text = ""
    for attempt in range(1, HTTP_RETRY_TIMES + 1):
        try:
            status, text = http_request("POST", url, headers=auth_headers(api_key, True),
                                        body=body, timeout=60)
        except urllib.error.URLError as e:
            if attempt >= HTTP_RETRY_TIMES:
                fail(6, "发起任务网络错误：%s（请检查网络与服务可达性：%s）" % (e, base_url))
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("发起任务网络错误：%s，%ds 后重试（%d/%d）" % (e, wait, attempt, HTTP_RETRY_TIMES))
            time.sleep(wait)
            continue
        if status >= 500:
            if attempt >= HTTP_RETRY_TIMES:
                fail(6, "发起任务服务端暂时不可用（HTTP %d），已重试 %d 次仍失败，请稍后重试。"
                    % (status, HTTP_RETRY_TIMES))
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("发起任务服务端错误 HTTP %d，%ds 后重试（%d/%d）" % (status, wait, attempt, HTTP_RETRY_TIMES))
            time.sleep(wait)
            continue
        break

    if status in (401, 403):
        payload = parse_json(text) or {}
        fail(3, "鉴权失败（HTTP %d）。API Key 无效或已过期，请更新 config.json 中的 LY_API_KEY 后重试。"
                "服务端返回：%s" % (status, payload.get("message") or text[:200]))

    payload = parse_json(text)
    if payload is None:
        fail(4, "发起任务返回非 JSON（HTTP %d）：%s" % (status, text[:200]))

    data = payload.get("data") or {}
    msg = payload.get("message") or ""
    detail = payload.get("detail")
    trace_id = payload.get("trace_id")
    recharge = data.get(F_RECHARGE_URL)
    # 余额不足：402 或 message 命中关键词
    if status == 402 or "余额不足" in msg or "点数不足" in msg or recharge:
        tip = "余额不足，无法发起点人匹配任务。"
        if recharge:
            tip += " 请前往充值：%s" % recharge
        else:
            tip += " 请前往 https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=01workbuddy 充值。"
        fail(4, tip)

    if status not in (200, 201) or payload.get("result") != "success":
        extra = ""
        if detail:
            extra += "，detail=%s" % detail
        if trace_id:
            extra += "，trace_id=%s" % trace_id
        fail(4, "发起任务失败：HTTP %s，result=%s，message=%s%s"
             % (status, payload.get("result"), msg, extra))

    task_id = first_present(data, F_TASK_ID_ALIASES)
    if not task_id:
        fail(4, "发起任务成功但缺少任务 id：%s" % text[:300])
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
    # 注意：HTTP 200 只表示「成功查询到状态」，任务本身可能失败，需看 data.status
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
    """
    deadline = time.monotonic() + max_wait
    start = time.monotonic()
    last_log = 0.0
    last_signature = None
    backoff = interval

    # 创建后先等约 5s 再首次轮询（API 文档建议）
    time.sleep(INITIAL_POLL_DELAY)

    def emit_progress(data):
        """返回 (status_key, signature, printed)。printed=True 表示实际打到了 stderr。"""
        raw_status = data.get("status", "unknown")
        status_key = _status_key(raw_status)
        elapsed = int(time.monotonic() - start)
        stage_zh, pmsg, percent = extract_progress(data)
        signature = (status_key, stage_zh, pmsg, percent)
        now = time.monotonic()
        if signature == last_signature and (now - last_log) < PROGRESS_KEEPALIVE_SECONDS:
            return status_key, signature, False
        label = STATUS_LABEL.get(status_key) or STATUS_LABEL.get(str(raw_status)) or raw_status
        parts = ["[%s]" % label, "已等待%ds" % elapsed]
        if pmsg:
            parts.append(pmsg)
        elif stage_zh:
            parts.append("当前阶段：%s" % stage_zh)
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
            # 竞态：status 已 completed 但 markdown 尚未落库。
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
                sk = _status_key(data.get("status", ""))
                if sk in FAILED_STATUSES:
                    return ("failed", data, _extract_error(data) or "达人匹配失败")
                if sk in TIMEOUT_STATUSES:
                    return ("TIMEOUT", data, None)
            return ("completed", data, None)
        if status_key in FAILED_STATUSES:
            return ("failed", data, _extract_error(data) or "达人匹配失败")
        if status_key in TIMEOUT_STATUSES:
            return ("TIMEOUT", data, None)
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


# 报告渲染：达人匹配 API 终态直接返回 data.markdown（文档约定）。
# 但为应对「有时没渲染为 md」的情况，这里对结构化结果做兜底渲染：
# 优先 data.markdown → data.result.sections[] → 其它结构化字段递归渲染。

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


def _has_content(v):
    if isinstance(v, list):
        return len(v) > 0
    if isinstance(v, dict):
        return any(not str(k).startswith("_") for k in v.keys())
    return False


def _inline_dict_title(d):
    for k in ("title", "name", "account", "rank", "tier", "topic"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def json_to_md(value, level=0):
    """把任意 JSON 值渲染成可读的 Markdown 片段（缩进 bullet 列表），不含标题。"""
    pad = "  " * level
    if isinstance(value, dict):
        if not value:
            return pad + "（空）"
        lines = []
        for k, v in value.items():
            if str(k).startswith("_"):
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
    return pad + _scalar_str(value)


def _render_sections(sections):
    """兜底渲染 data.result.sections[]。返回 Markdown 字符串。"""
    lines = ["# 达人匹配分析报告", ""]
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


def build_report(data):
    """从终态 data 构建可交付的 Markdown 报告字符串；无可渲染内容时返回 None。

    优先级：
      1) data.markdown（达人匹配 API 文档约定的报告字段，完成态返回）
      2) data.result.sections[]（兼容结构化形态）
      3) 其它结构化字段递归渲染
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
    # 最后一道兜底：把 data 里除标准字段外的内容递归渲染
    skip = {"task_id", "status", "current_stage", "progress_message",
            "error_message", "total_points", "scene", "started_at", "completed_at"}
    extras = {k: v for k, v in data.items() if k not in skip and not str(k).startswith("_")}
    if _has_content(extras):
        lines = ["# 达人匹配分析报告", "", json_to_md(extras), ""]
        return "\n".join(lines).strip()
    return None


def _extract_error(data):
    """从终态 data 提取失败原因。返回字符串 or None。"""
    if not isinstance(data, dict):
        return None
    msg = data.get("error_message")
    if isinstance(msg, str) and msg.strip():
        return msg.strip()
    errs = data.get("errors")
    parts = _join_errors(errs)
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
    pre_rendered = bool(isinstance(data.get("markdown"), str) and data.get("markdown").strip())
    if not markdown:
        errmsg = _extract_error(data) or ""
        log("⚠️ 任务已标记完成，但未能构建可交付的报告内容。")
        log("   status=%s | error_message=%s" % (data.get("status", "-"), errmsg or "-"))
        log("   data 既无 markdown，也无可渲染的结构化结果。")
        log("   可稍候用 --task-id %s 重新轮询一次；仍为空则联系服务端排查。" % task_id)
        sys.exit(7)

    markdown, looks_valid = normalize_markdown(markdown)
    if not looks_valid:
        log("⚠️ 报告内容疑似非标准 markdown（未识别到标题/列表/表格标记），已按原样输出供核对。")
    if not markdown or not markdown.strip():
        log("⚠️ 报告内容规整后为空。可稍候用 --task-id %s 重新轮询一次。" % task_id)
        sys.exit(7)

    if pre_rendered:
        log("报告来源：服务端预渲染 markdown")
    else:
        log("报告来源：本地兜底渲染结构化结果")

    saved = _write_report(markdown, out_path, task_id)

    # 本次实际扣点：优先取终态响应里的扣点字段，回退创建接口给出；都没有则空
    final_points = extract_points(data)
    if final_points is None:
        final_points = points
    points_str = _fmt_points(final_points)
    print("CREATOR_MATCH_POINTS_USED=" + points_str)
    print("CREATOR_MATCH_REPORT_FILE=" + (saved or ""))
    print(REPORT_START)
    print(markdown)
    print(REPORT_END)
    sys.stdout.flush()


def _write_report(markdown, out_path, task_id):
    """三级兜底落盘：--out 指定 → 工作目录 → /tmp。返回绝对路径 or None。"""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(task_id or "unknown"))
    filename = "creator-match-%s.md" % safe
    fallback_dirs = [
        os.getcwd(),
        "/tmp",
    ]
    # 1) --out 指定路径
    candidates = []
    if out_path:
        if os.path.isdir(out_path):
            candidates.append(os.path.join(out_path, filename))
        else:
            candidates.append(out_path)
    # 2) 工作目录 / 3) /tmp
    for d in fallback_dirs:
        candidates.append(os.path.join(d, filename))

    for path in candidates:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(markdown)
                if not markdown.endswith("\n"):
                    f.write("\n")
            return os.path.abspath(path)
        except OSError as e:
            log("⚠️ 报告写入失败 [%s]：%s" % (path, e))
            continue
    return None


def main():
    parser = argparse.ArgumentParser(
        description="微信视频号达人匹配：读配置→发起任务→轮询→交付报告")
    parser.add_argument("--account", action="append", default=None,
                        help="候选达人账号名称（昵称），可多次传入；1～10 个")
    parser.add_argument("--platform", default="channels",
                        help="目标内容平台，默认 channels（微信视频号）")
    parser.add_argument("--industry", action="append", default=None,
                        help="产品行业代码（可多次），可选值见 --config；用 value 不用 label")
    parser.add_argument("--campaign-type", action="append", default=None,
                        help="投放类型代码（可多次），可选值见 --config")
    parser.add_argument("--product-name", default=None, help="产品名称（必填）")
    parser.add_argument("--product-price", type=float, default=None, help="产品价格")
    parser.add_argument("--price-band", default=None,
                        help="价格档位，可选值见 --config")
    parser.add_argument("--decision-type", default=None,
                        help="消费决策类型，可选值见 --config")
    parser.add_argument("--selling-point", action="append", default=None,
                        help="产品核心卖点（必填，至少一个，可多次）")
    parser.add_argument("--task-id", default=None,
                        help="已有的任务 ID，跳过创建直接轮询")
    parser.add_argument("--out", default=None, help="报告输出路径（目录或文件）")
    parser.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT, help="整体等待上限（秒），默认 1200")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="轮询间隔（秒），默认 8")
    parser.add_argument("--extra-data", default=None,
                        help="扩展信息：文档抽取内容或其它补充文本（选填）")
    parser.add_argument("--estimate-only", dest="estimate_only", action="store_true",
                        help="只创建任务、拿到 task_id 与预计扣点后即退出（不轮询）。"
                             "用于让助手在确认前先把预计扣点告诉用户，确认后再用 --task-id 轮询。")
    parser.add_argument("--config", dest="config_only", action="store_true",
                        help="只拉取可选枚举配置（industries/campaign_types/price_band/decision_type）后退出。")
    args = parser.parse_args()

    base_url = BASE_URL
    api_key = get_api_key()
    if not api_key:
        fail(3, "未取到 API Key：技能目录下的 config.json 不存在，或其中无有效的 LY_API_KEY 字段。\n"
                "请在技能目录（SKILL.md 所在处）创建 config.json，内容形如 "
                '{"LY_API_KEY": "你的密钥"}，或设置环境变量 LY_API_KEY 后重试。')

    # 仅读配置
    if args.config_only:
        if args.estimate_only or args.task_id:
            parser.error("--config 与 --estimate-only / --task-id 互斥，请单独使用。")
        fetch_config(base_url, api_key)
        return  # 退出码 0

    if args.estimate_only and args.task_id:
        parser.error("--estimate-only 仅用于新建任务（需提供账号与产品信息），恢复任务请直接用 --task-id。")

    if args.task_id:
        task_id = args.task_id
        points = None  # 恢复任务不重复扣点
        log("恢复已有任务：task_id=%s" % task_id)
    else:
        # 校验新建任务必填项：1～10 个候选达人账号 + 产品名称 + 至少一个卖点
        accounts = [a.strip() for a in (args.account or []) if a and a.strip()]
        if not accounts:
            fail(2, "未提供候选达人账号：请通过 --account 传入至少一个视频号达人账号名称（昵称）。")
        if len(accounts) > 10:
            fail(2, "候选达人账号数量超过上限：最多 10 个，当前 %d 个。请缩减后重试。" % len(accounts))
        if not (args.product_name and args.product_name.strip()):
            fail(2, "未提供产品名称（必填）：请通过 --product-name 传入产品名称。")
        selling_points = [s for s in (args.selling_point or []) if s and s.strip()]
        if not selling_points:
            fail(2, "未提供产品核心卖点（必填）：请通过 --selling-point 传入至少一个卖点。")
        product = {
            "name": args.product_name.strip(),
            "selling_points": selling_points,
        }
        if args.product_price is not None:
            product["price"] = args.product_price
        if args.price_band:
            product["price_band"] = args.price_band
        if args.decision_type:
            product["decision_type"] = args.decision_type
        body_obj = build_create_body(
            accounts, args.platform, args.industry, args.campaign_type,
            product, extra_data=args.extra_data)
        task_id, points = create_task(base_url, api_key, body_obj)

    # 只估算成本、拿 task_id，不轮询。
    # 预计扣点：服务端若在创建响应里返回点数字段就用真实值，否则按 198 × 候选达人数 估算
    # （达人匹配需逐个读取达人账号视频数据，平均每读一个达人约耗 198 点；达人越多点数越巨大，
    # 实际按任务复杂度/达人视频数量而定，以服务端实际计费为准，可高可低）。
    if args.estimate_only:
        account_count = len(body_obj.get("target_accounts", [])) if not args.task_id else 0
        pts = _fmt_points(points)
        estimate_str = pts if pts else str(POINTS_PER_ACCOUNT * max(account_count, 1))
        source = ("服务端返回" if pts
                  else "按 198 点/达人 × %d 个达人估算（服务端未在创建响应里返回点数字段）" % account_count)
        log("已创建任务、仅估算成本（不轮询）：task_id=%s，预计扣点 %s 点（%s）"
            % (task_id, estimate_str, source))
        print("CREATOR_MATCH_TASK_ID=" + task_id)
        print("CREATOR_MATCH_ESTIMATE_POINTS=" + estimate_str)
        print("CREATOR_MATCH_ESTIMATE_SOURCE=" + source)
        sys.stdout.flush()
        return  # 退出码 0

    log("开始轮询达人匹配状态（最长 %ds，间隔 %ds）...进度会持续打到 stderr"
        % (args.max_wait, args.interval))
    status, data, err = poll_loop(base_url, api_key, task_id, args.max_wait, args.interval)

    if status == "TIMEOUT":
        log("等待超时：已等待 %ds。当前任务仍在进行（或服务端返回 timeout），task_id=%s。"
            "可稍后用 --task-id %s 重新轮询恢复。" % (args.max_wait, task_id, task_id))
        sys.exit(124)
    if status == "failed":
        fail(5, "达人匹配任务失败：%s" % (err or "未知原因"))

    deliver_report(data, args.out, task_id, points)


if __name__ == "__main__":
    main()
