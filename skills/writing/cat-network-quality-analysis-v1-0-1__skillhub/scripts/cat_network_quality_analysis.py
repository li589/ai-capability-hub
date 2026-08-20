#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAT Network Quality Analysis — 调用 CAT AI Console 流式分析并将结果写入 Markdown 文件。

全程静默执行（不输出流式日志到 stdout/stderr），最终只输出一个 JSON 到 stdout，
供 agent 作为工具调用结果识别：

    {"code": 0, "report": "# 错误分析报告\\n...", "md_path": "...", "session_id": "...", "json_file": "...", "pcap_candidates": [...], "incomplete": false}
    {"code": 1, "error": "错误信息"}

用法:
    python3 cat_network_quality_analysis.py \\
        --query-text "进行错误分析" \\
        --task-id task-xxx \\
        --start-time 1773658839444 \\
        --end-time 1773745239444 \\
        [--analyze-action Console|PcapAnalysis|MultiTaskCompare] \\
        [--session-id xxx] \\
        [--output report.md] \\
        [--suppress-pcap-candidates]

AnalyzeAction 缺省按 query-text 自动推断：<structured_json> 带 compare_task_ids →
MultiTaskCompare；带 probe_time + code（抓包跟进）→ PcapAnalysis；其余 → Console。
多任务对比（MultiTaskCompare）场景 TaskID 由 query-text 内 structured_json 承载，
--task-id 可省略。

依赖:
    无第三方依赖，使用 Python 标准库实现 TC3-HMAC-SHA256 签名。

    若设置了环境变量 TCPROXYCLI_PROXY_ENDPOINT 和 TCPROXYCLI_SESSION_KEY，
    则自动切换为 tcproxycli 代理模式，无需本地云密钥。
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import shutil
import signal
import subprocess
from typing import Any, Iterator, TextIO
from urllib import error as urlerror
from urllib import request as urlrequest


class TencentCloudSDKException(Exception):
    """调用腾讯云 API 失败时的异常。"""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# 1. 工具函数 — 环境变量 / 密钥
# ═══════════════════════════════════════════════════════════════════════════


def _load_dotenv() -> None:
    """从 .env 文件中加载环境变量（不覆盖已有）。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    env_file = None
    for path in candidates:
        if os.path.isfile(path):
            env_file = path
            break
    if env_file is None:
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


def _get_credential() -> tuple[str, str, str]:
    """获取腾讯云密钥。优先使用 CAT_xxx 环境变量，未设置时降级使用 TENCENTCLOUD_xxx。

    返回 (secret_id, secret_key, token) 三元组，token 可能为空字符串。
    """
    _load_dotenv()
    secret_id = os.environ.get("CAT_SECRET_ID") or os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    secret_key = os.environ.get("CAT_SECRET_KEY") or os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    token = os.environ.get("CAT_TOKEN") or os.environ.get("TENCENTCLOUD_TOKEN", "")
    if not secret_id or not secret_key:
        raise RuntimeError(
            "未找到腾讯云密钥，请配置 CAT_SECRET_ID/CAT_SECRET_KEY "
            "或 TENCENTCLOUD_SECRET_ID/TENCENTCLOUD_SECRET_KEY 环境变量"
        )
    return secret_id, secret_key, token


# ═══════════════════════════════════════════════════════════════════════════
# 2. 统一 SSE 调用层 — 自动选择 tcproxycli / SDK
# ═══════════════════════════════════════════════════════════════════════════


def _is_tcproxy_mode() -> bool:
    """检测是否应使用 tcproxycli 代理模式。

    条件（全部满足）:
      1. 环境变量 TCPROXYCLI_PROXY_ENDPOINT 非空
      2. 环境变量 TCPROXYCLI_SESSION_KEY 非空
      3. PATH 中能找到 tcproxycli 二进制
    """
    if not os.environ.get("TCPROXYCLI_PROXY_ENDPOINT"):
        return False
    if not os.environ.get("TCPROXYCLI_SESSION_KEY"):
        return False
    return shutil.which("tcproxycli") is not None


def _tcproxy_sse_iter(
    params: dict[str, Any],
) -> Iterator[dict[str, str]]:
    """通过 tcproxycli 子进程调用 CAT ProcessAIEventsStream，产出 SSE 事件字典。"""
    cmd: list[str] = [
        "tcproxycli", "cat", "ProcessAIEventsStream",
        "--stream",
        "--stream-output", "ndjson",
        "--region", "ap-guangzhou",
        "--version", "2018-04-09",
        "--endpoint", (
            os.environ.get("CAT_ENDPOINT")
            or os.environ.get("TENCENTCLOUD_ENDPOINT")
            or "cat.ai.tencentcloudapi.com"
        ),
        "--timeout", "300",
        "--AnalyzeAction", params.get("analyze_action") or "Console",
        "--QueryText", params["query_text"],
        "--CallerScene", "skill_capi",
    ]
    # 多任务对比场景 TaskID 由 QueryText 内的 structured_json 承载，命令行不传
    if params.get("task_id") and params.get("analyze_action") != "MultiTaskCompare":
        cmd += ["--TaskID", params["task_id"]]
    if params.get("start_time") is not None:
        cmd += ["--StartTime", str(params["start_time"])]
    if params.get("end_time") is not None:
        cmd += ["--EndTime", str(params["end_time"])]
    if params.get("session_id"):
        cmd += ["--SessionID", params["session_id"]]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    stderr_lines: list[str] = []
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                ndjson_obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            data_str = ndjson_obj.get("data", "")
            if data_str:
                yield {"data": data_str}
    finally:
        proc.stdout.close()
        # 收集 stderr 末尾几行用于错误诊断
        try:
            stderr_data = proc.stderr.read() if proc.stderr else ""
        finally:
            if proc.stderr:
                proc.stderr.close()
        stderr_lines = [
            ln.strip() for ln in stderr_data.splitlines() if ln.strip()
        ]
        try:
            rc = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = proc.wait()
        if rc != 0:
            tail = "\n".join(stderr_lines[-3:]) if stderr_lines else ""
            detail = f"（exit={rc}, stderr={tail}）" if tail else f"（exit={rc}）"
            raise RuntimeError(f"tcproxycli 调用失败{detail}")


def _infer_report_type(query_text: str) -> str:
    """根据 query_text 推断 report_type，用于缺省输出路径命名。

    与 SKILL.md §2 意图路由一致：多任务对比 > 抓包 > 错误 > 整体 > 性能。
    """
    text = (query_text or "").strip()
    # 多任务对比：结构化 JSON 且含 compare_task_ids 字段
    if "<structured_json>" in text and "compare_task_ids" in text:
        return "multitask_compare_report"
    # 抓包跟进：结构化 JSON 且含 probe_time + code 字段
    if "<structured_json>" in text and "probe_time" in text and "code" in text:
        return "pcap_report"
    if "<structured_json>" in text or "抓包" in text or "抓个包" in text or "抓一下包" in text or "pcap" in text.lower():
        return "pcap_report"
    if "错误" in text or "报错" in text or "排查" in text or "诊断" in text:
        return "error_report"
    if "整体" in text or "全面" in text or "汇总" in text or "概况" in text:
        return "overall_report"
    if "慢" in text or "延迟" in text or "性能" in text:
        return "performance_report"
    return "error_report"


def _infer_analyze_action(query_text: str) -> str:
    """根据 query_text 推断 AnalyzeAction。

    - 含 `<structured_json>` 且带 `compare_task_ids` 字段 → ``MultiTaskCompare``
    - 含 `<structured_json>` 且带 `probe_time` + `code` 字段（抓包跟进型 payload）→ ``PcapAnalysis``
    - 其余场景（错误 / 整体 / 性能 / 抓包直达）→ ``Console``
    """
    text = (query_text or "").strip()
    if "<structured_json>" in text:
        if "compare_task_ids" in text:
            return "MultiTaskCompare"
        if "probe_time" in text and "code" in text:
            return "PcapAnalysis"
    return "Console"


def _extract_main_task_id(query_text: str) -> str:
    """从多任务对比的 <structured_json> payload 中提取 main_task_id。

    用于缺省输出路径命名（以主任务 ID 为前缀）。提取失败返回空串，
    由调用方回退到 --task-id。
    """
    text = (query_text or "").strip()
    if "<structured_json>" not in text or "compare_task_ids" not in text:
        return ""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    try:
        payload = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, TypeError):
        return ""
    main_task_id = payload.get("main_task_id", "")
    return main_task_id if isinstance(main_task_id, str) else ""


def _sha256_hex(data: bytes) -> str:
    """计算 SHA256 十六进制摘要。"""
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    """计算 HMAC-SHA256。"""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _build_tc3_authorization(
    secret_id: str,
    secret_key: str,
    service: str,
    host: str,
    payload: str,
    timestamp: int,
    token: str = "",
) -> str:
    """构造腾讯云 TC3-HMAC-SHA256 签名 Authorization 头。

    参考: https://cloud.tencent.com/document/api/213/30654
    """
    # 1. 拼接规范请求串
    algorithm = "TC3-HMAC-SHA256"
    ct = "application/json; charset=utf-8"
    canonical_uri = "/"
    canonical_querystring = ""
    canonical_headers = f"content-type:{ct}\nhost:{host}\n"
    signed_headers = "content-type;host"
    hashed_payload = _sha256_hex(payload.encode("utf-8"))

    canonical_request = (
        f"POST\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{hashed_payload}"
    )

    # 2. 拼接待签名字符串
    date = datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    service_line = service
    credential_scope = f"{date}/{service_line}/tc3_request"
    hashed_canonical_request = _sha256_hex(canonical_request.encode("utf-8"))
    string_to_sign = (
        f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
    )

    # 3. 计算签名
    secret_date = _hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, service_line)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = _hmac_sha256(secret_signing, string_to_sign).hex()

    # 4. 拼接 Authorization
    authorization = (
        f"{algorithm} Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return authorization


def _sdk_sse_iter(
    params: dict[str, Any],
) -> Iterator[dict[str, str]]:
    """通过 TC3-HMAC-SHA256 签名直接调用 CAT ProcessAIEventsStream，产出 SSE 事件字典。

    不依赖 tencentcloud-sdk-python，仅用标准库实现签名与 HTTP 请求。
    """
    secret_id, secret_key, token = _get_credential()

    host = (
        os.environ.get("CAT_ENDPOINT")
        or os.environ.get("TENCENTCLOUD_ENDPOINT")
        or "cat.ai.tencentcloudapi.com"
    )

    # 构造请求体
    api_params: dict[str, Any] = {
        "AnalyzeAction": params.get("analyze_action") or "Console",
        "QueryText": params["query_text"],
        "CallerScene": "skill_capi",
    }
    if params.get("session_id"):
        api_params["SessionID"] = params["session_id"]
    if params.get("start_time") is not None:
        api_params["StartTime"] = params["start_time"]
    if params.get("end_time") is not None:
        api_params["EndTime"] = params["end_time"]
    # 多任务对比场景 TaskID 由 QueryText 内的 structured_json 承载，请求体不传
    if params.get("task_id") and params.get("analyze_action") != "MultiTaskCompare":
        api_params["TaskID"] = params["task_id"]

    payload = json.dumps(api_params, ensure_ascii=False)
    timestamp = int(datetime.datetime.now().timestamp())

    authorization = _build_tc3_authorization(
        secret_id, secret_key, "cat", host, payload, timestamp, token,
    )

    ct = "application/json; charset=utf-8"
    headers: dict[str, str] = {
        "Authorization": authorization,
        "Content-Type": ct,
        "Host": host,
        "X-TC-Action": "ProcessAIEventsStream",
        "X-TC-Version": "2018-04-09",
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Region": "ap-guangzhou",
        "Accept": "text/event-stream",
    }
    if token:
        headers["X-TC-Token"] = token

    url = f"https://{host}"
    req = urlrequest.Request(url, data=payload.encode("utf-8"), headers=headers, method="POST")

    try:
        resp = urlrequest.urlopen(req, timeout=300)
    except urlerror.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise TencentCloudSDKException(
            f"HTTP {e.code} {e.reason}: {body[:500]}"
        ) from e
    except urlerror.URLError as e:
        raise RuntimeError(f"网络请求失败: {e.reason}") from e

    # 解析 SSE 流，产出与 SDK call_sse 兼容的 dict 事件
    event: dict[str, str] = {}
    try:
        for raw_line in resp:
            if not raw_line:
                continue
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                if event:
                    yield event
                    event = {}
                continue
            if line.startswith(":"):
                continue
            colon_idx = line.find(":")
            if colon_idx == -1:
                continue
            key = line[:colon_idx]
            val = line[colon_idx + 1:]
            if val and val[0] == " ":
                val = val[1:]
            if key == "data":
                if "data" not in event:
                    event["data"] = val
                else:
                    event["data"] += "\n" + val
            elif key in ("event", "id"):
                event[key] = val
    finally:
        resp.close()


# ---------------------------------------------------------------------------
# SSE 全局超时包装器 — 300 秒硬限制
# ---------------------------------------------------------------------------

_SSE_TIMEOUT_SECONDS = 300


class _SSETimeoutWrapper:
    """用 SIGALRM 给 SSE 迭代器套一层 300 秒硬超时。

    用法与原始迭代器完全一致：

        for event in _call_cat_sse(params):
            ...

    超时后抛出 ``TimeoutError``，由调用方捕获并做收尾。
    """

    def __init__(self, params: dict[str, Any], timeout: int = _SSE_TIMEOUT_SECONDS):
        self._params = params
        self._timeout = timeout
        self._iter: Iterator[dict[str, str]] | None = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._iter is None:
            self._iter = (
                _tcproxy_sse_iter(self._params)
                if _is_tcproxy_mode()
                else _sdk_sse_iter(self._params)
            )
        _set_sse_alarm(self._timeout)
        try:
            event = next(self._iter)
        except StopIteration:
            _cancel_sse_alarm()
            raise
        except BaseException:
            _cancel_sse_alarm()
            raise
        _cancel_sse_alarm()
        return event


def _set_sse_alarm(seconds: int) -> None:
    """设定 SIGALRM 定时器（仅 main thread）。"""
    signal.signal(signal.SIGALRM, _sse_alarm_handler)
    signal.alarm(seconds)


def _cancel_sse_alarm() -> None:
    """取消 SIGALRM 定时器。"""
    signal.alarm(0)


def _sse_alarm_handler(_signum: int, _frame: Any) -> None:
    """SIGALRM 触发回调：抛出 TimeoutError。"""
    raise TimeoutError(
        f"SSE 调用超过 {_SSE_TIMEOUT_SECONDS} 秒硬限制，已终止"
    )


def _call_cat_sse(
    params: dict[str, Any],
) -> Iterator[dict[str, str]]:
    """统一 SSE 调用入口：根据环境变量自动选择 tcproxycli 或 SDK。

    全局硬超时 300 秒：无论哪种后端，SSE 消费超过 300 秒即抛
    ``TimeoutError``，由调用方捕获并终止流程。
    """
    return _SSETimeoutWrapper(params, timeout=300)


# ═══════════════════════════════════════════════════════════════════════════
# 3. SSE 事件解析
# ═══════════════════════════════════════════════════════════════════════════


def _parse_sse_event(data: str) -> dict[str, Any]:
    """
    解析 SSE 事件的 data 字段（标准 JSON 字符串，包含 Type 字段）。

    返回:
        {
            "type": "agent_message_chunk"|"agent.done"|"pcap_check.done"|"",
            "content": "增量文本",
            "full_text": "完整文本",
            "session_id": "会话ID",
            "tool_name": "工具名称（如有）",
            "tool_data": { ... }  # 工具附带数据（如有）
        }
    """
    text = data.strip()
    if not text:
        return {"type": "", "content": "", "full_text": "", "session_id": "",
                "tool_name": "", "tool_data": None}

    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"type": "", "content": text, "full_text": "", "session_id": "",
                "tool_name": "", "tool_data": None}

    return {
        "type": obj.get("Type", ""),
        "content": obj.get("Content", ""),
        "full_text": obj.get("FullText", ""),
        "session_id": obj.get("SessionID", ""),
        "tool_name": obj.get("ToolName", ""),
        "tool_data": obj.get("Data"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. 流式 CAT AI Console 调用 — 全程静默，写入 md_file
# ═══════════════════════════════════════════════════════════════════════════


def _unescape_content(text: str) -> str:
    """将 SSE 返回中的字面转义 \\n / \\" 还原为真实字符。"""
    return text.replace("\\n", "\n").replace('\\"', '"')


def _trim_to_first_h1(text: str) -> str:
    """从第一个 Markdown 一级标题（``# ``）开始截取文本。

    扫描每一行，找到第一个以 ``# `` 开头的行，返回从该行开始到末尾的全部内容。
    如果找不到任何一级标题，原样返回（不截取）。
    """
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("# "):
            return text[offset:]
        offset += len(line)
    return text


def _stream_cat_analysis(
    params: dict[str, Any],
    md_file: TextIO,
) -> tuple[str, Any, str, bool]:
    """
    调用 CAT ProcessAIEventsStream，消费全部 SSE 事件并写入 Markdown。

    全程静默：不输出任何内容到 stdout/stderr。
    流式期间增量写入 md_file，全部事件消费完毕后用 FullText 覆盖重写。

    **注意**：一级标题截取由调用方 ``run_pipeline`` 在追加 pcap 章节后统一执行。

    参数:
        params   — 请求参数
        md_file  — 已打开的 .md 文件句柄（以 w+ 模式打开）

    返回:
        (full_text, tool_data, session_id, incomplete)
    """
    if not params:
        return "", None, "", True

    resp_iter = _call_cat_sse(params)

    full_text = ""                   # done 事件中的完整文本（权威）
    session_id = ""                  # agent.start 中的会话 ID
    tool_data: Any = None            # done 事件附带的工具数据
    incremental_parts: list[str] = []  # 增量 Content 片段（降级使用）
    received_done = False            # 是否收到了 agent.done 事件

    for event in resp_iter:
        raw: str = event.get("data", "")
        if not raw:
            continue

        parsed = _parse_sse_event(raw)
        event_type = parsed.get("type", "")

        # agent.start — 提取 SessionID
        if event_type == "agent.start":
            sid = parsed.get("session_id", "")
            if sid:
                session_id = sid
            continue

        # done 类事件
        if event_type.endswith(".done"):
            if event_type == "agent.done":
                received_done = True
                full_text = parsed.get("full_text", "")
                sid = parsed.get("session_id", "")
                if sid and not session_id:
                    session_id = sid
                break
            elif event_type == "pcap_check.done":
                tool_data = parsed.get("tool_data")
                continue
            else:
                continue

        # 增量 chunk — 写入 md 文件
        content = parsed.get("content", "")
        if content and content != "{}":
            decoded = _unescape_content(content)
            incremental_parts.append(decoded)
            md_file.write(decoded)
            md_file.flush()

    # 确定最终文本：优先 FullText，否则用增量拼接
    if full_text:
        final_text = _unescape_content(full_text)
        incremental_text = "".join(incremental_parts)
        if len(final_text) < len(incremental_text):
            final_text = incremental_text
    elif incremental_parts:
        final_text = "".join(incremental_parts)
    else:
        return "", tool_data, session_id, not received_done

    # 覆盖重写 md 文件为最终文本
    md_file.seek(0)
    md_file.truncate()
    md_file.write(final_text)
    md_file.flush()

    return final_text, tool_data, session_id, not received_done


# ═══════════════════════════════════════════════════════════════════════════
# 5. pcap 候选列表
# ═══════════════════════════════════════════════════════════════════════════


def _format_pcap_rows(tool_data: dict[str, Any]) -> tuple[list[str], list[list[str]]] | None:
    """将 pcap_check.done 事件的 Data 字段转为表头 + 行数据。"""
    if not tool_data or not isinstance(tool_data, dict):
        return None
    items = tool_data.get("items", [])
    if not items:
        return None

    headers = ["城市", "运营商", "错误码", "任务ID", "拨测时间", "拨测点编码"]
    rows: list[list[str]] = []
    for item in items:
        probe_ts = item.get("probe_time")
        if probe_ts:
            probe_str = datetime.datetime.fromtimestamp(
                probe_ts / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            probe_str = ""
        rows.append([
            str(item.get("city", "")),
            str(item.get("operator", "")),
            str(item.get("error_id", "")),
            str(item.get("task_id", "")),
            probe_str,
            str(item.get("code", "")),
        ])
    return headers, rows


def _pcap_section_to_markdown(headers: list[str], rows: list[list[str]]) -> str:
    """将 pcap 表格渲染为 Markdown 表格字符串。"""
    lines: list[str] = []
    lines.append("")
    lines.append("## 🔍 抓包分析候选列表")
    lines.append("")
    lines.append(
        f"检测到 {len(rows)} 个错误记录配置了\"错误时抓包\"模式，"
        "以下为抓包分析候选项。"
    )
    lines.append("")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        safe_row = [cell.replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(safe_row) + " |")
    lines.append("")
    return "\n".join(lines)


def _build_pcap_payload(item: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """从单个 pcap 候选项构建 structured_json payload。

    返回:
        (payload_dict, payload_json) — payload_json 为紧凑 JSON 字符串，
        可直接包裹在 <structured_json>...</structured_json> 中。
    """
    payload = {
        "task_id": str(item.get("task_id", "")),
        "probe_time": item.get("probe_time"),
        "code": str(item.get("code", "")),
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return payload, payload_json


def _write_structured_json_file(
    items: list[dict[str, Any]],
    output_path: str,
    report_md_path: str,
) -> str:
    """把每个抓包候选项按序号写成一份 Markdown 文件。"""
    if not items:
        return ""

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    lines: list[str] = []
    lines.append("# 抓包分析 structured_json payload 列表")
    lines.append("")
    lines.append(
        f"本文件对应主报告 `{os.path.basename(report_md_path)}` 中的抓包候选表格。"
    )
    lines.append(
        f"共 {len(items)} 条候选。按序号取对应 `<structured_json>...</structured_json>` 整段，"
        "直接作为 `--query-text` 的值传入即可（注意保留标签，不要改动字段值）。"
    )
    lines.append("")

    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        _, payload_json = _build_pcap_payload(item)

        probe_ts = item.get("probe_time")
        if probe_ts:
            try:
                probe_str = datetime.datetime.fromtimestamp(probe_ts / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except (TypeError, ValueError, OSError):
                probe_str = str(probe_ts)
        else:
            probe_str = ""

        lines.append(f"## {idx}. 城市: {item.get('city', '')} | 运营商: {item.get('operator', '')} | 错误码: {item.get('error_id', '')} | 拨测时间: {probe_str}")
        lines.append("")
        lines.append("```text")
        lines.append(f"<structured_json>{payload_json}</structured_json>")
        lines.append("```")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


# ═══════════════════════════════════════════════════════════════════════════
# 6. 管道编排
# ═══════════════════════════════════════════════════════════════════════════


def run_pipeline(
    params: dict[str, Any],
    output_path: str,
    suppress_pcap_candidates: bool = False,
) -> dict[str, Any]:
    """
    全程静默执行分析，写入 Markdown 文件，返回结果字典。

        Input(dict) ──▶ SSE分析（静默写入 md）──▶ 追加 pcap 章节
                                           └──▶ 截取一级标题
                                           └──▶ 返回 {code, report, md_path, ...}

    参数:
        params                      — 调用 CAT AI Console 所需的参数字典
        output_path                 — 主报告 .md 路径
        suppress_pcap_candidates    — 若为 True，不把候选列表写入 .md / 导出 _json.md

    返回:
        {"code": 0, "report": str, "md_path": str, "session_id": str, "json_file": str, "pcap_candidates": list, "incomplete": bool}
        失败时 {"code": 1, "error": str}
    """
    # 确保输出目录存在
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    json_md_path = ""
    pcap_candidates: list[dict[str, Any]] = []

    with open(output_path, "w+", encoding="utf-8") as md_file:
        full_text, tool_data, session_id, incomplete = _stream_cat_analysis(params, md_file)

        if not full_text:
            return {"code": 1, "error": "未获取到分析内容"}

        # 追加 pcap 候选列表（如果有且未抑制）
        if tool_data and not suppress_pcap_candidates:
            pcap = _format_pcap_rows(tool_data)
            if pcap:
                headers, rows = pcap
                md_file.write(_pcap_section_to_markdown(headers, rows))
                md_file.flush()

                items = tool_data.get("items") or []
                if items:
                    # 构建 pcap_candidates 列表（直接返回给 agent）
                    for idx, item in enumerate(items, start=1):
                        if not isinstance(item, dict):
                            continue
                        _, payload_json = _build_pcap_payload(item)
                        pcap_candidates.append({
                            "index": idx,
                            "city": str(item.get("city", "")),
                            "operator": str(item.get("operator", "")),
                            "error_id": str(item.get("error_id", "")),
                            "task_id": str(item.get("task_id", "")),
                            "probe_time": item.get("probe_time"),
                            "code": str(item.get("code", "")),
                            "structured_json": f"<structured_json>{payload_json}</structured_json>",
                        })

                    # 仍然写入独立文件（人工追溯用）
                    first_task_id = ""
                    if isinstance(items[0], dict):
                        first_task_id = str(items[0].get("task_id") or "")
                    tid = first_task_id or (params.get("task_id") or "pcap")
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_md_path = os.path.join(
                        out_dir or ".",
                        f"{tid}_json_{ts}.md",
                    )
                    try:
                        written = _write_structured_json_file(
                            items=items,
                            output_path=json_md_path,
                            report_md_path=output_path,
                        )
                        if not written:
                            json_md_path = ""
                    except OSError:
                        json_md_path = ""

        # ── 截取：从第一个 Markdown 一级标题开始 ──
        md_file.seek(0)
        raw_content = md_file.read()
        trimmed_content = _trim_to_first_h1(raw_content)
        if trimmed_content != raw_content:
            md_file.seek(0)
            md_file.truncate()
            md_file.write(trimmed_content)
            md_file.flush()
            final_text = trimmed_content
        else:
            final_text = raw_content

    return {
        "code": 0,
        "report": final_text,
        "md_path": output_path,
        "session_id": session_id,
        "json_file": json_md_path,
        "pcap_candidates": pcap_candidates,
        "incomplete": incomplete,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 7. CLI 入口
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CAT Network Quality Analysis — 流式分析并输出 JSON 结果"
    )
    parser.add_argument(
        "--query-text",
        required=True,
        help="(必选) 发送给 CAT AI Console 的分析查询",
    )
    parser.add_argument(
        "--analyze-action",
        default=None,
        help=(
            "(可选) 分析类型：Console / PcapAnalysis / MultiTaskCompare。"
            "缺省时按 query-text 自动推断（<structured_json> 带 compare_task_ids → MultiTaskCompare，"
            "带 probe_time+code → PcapAnalysis，其余 → Console）"
        ),
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="(多任务对比场景可省略) 拨测任务 ID，格式如 task-xxxxxxxx",
    )
    parser.add_argument(
        "--start-time",
        type=int,
        required=True,
        help="(必选) 分析起始时间 (毫秒级时间戳)",
    )
    parser.add_argument(
        "--end-time",
        type=int,
        required=True,
        help="(必选) 分析截止时间 (毫秒级时间戳)",
    )
    parser.add_argument("--session-id", default=None, help="(可选) 会话 ID")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="(可选) 输出 Markdown 路径，默认: {task_id}_{report_type}_{timestamp}.md",
    )
    parser.add_argument(
        "--suppress-pcap-candidates",
        action="store_true",
        default=False,
        help="(可选) 抑制 pcap_check.done 事件的副作用",
    )

    args = parser.parse_args()

    # 计算输出路径 — 缺省时按 query_text 推断 report_type
    if args.output:
        output_path = args.output
    else:
        # 多任务对比优先取 payload 内 main_task_id 作为路径前缀
        tid = args.task_id or _extract_main_task_id(args.query_text) or "report"
        report_type = _infer_report_type(args.query_text)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{tid}_{report_type}_{ts}.md"

    # 解析 AnalyzeAction — 显式 --analyze-action 优先，否则按 query-text 自动推断
    # （抓包跟进型 <structured_json> → PcapAnalysis；多任务对比 → MultiTaskCompare；其余 → Console）
    analyze_action = args.analyze_action or _infer_analyze_action(args.query_text)

    # 构建输入参数
    params = {
        "query_text": args.query_text,
        "analyze_action": analyze_action,
        "task_id": args.task_id,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "session_id": args.session_id,
    }

    # 自动判定抓包场景
    auto_suppress = bool(args.session_id) or (
        "<structured_json>" in (args.query_text or "")
    )
    suppress_pcap_candidates = args.suppress_pcap_candidates or auto_suppress

    # 执行管道 — 全程静默，最终只输出一个 JSON 到 stdout
    try:
        result = run_pipeline(
            params,
            output_path=output_path,
            suppress_pcap_candidates=suppress_pcap_candidates,
        )
    except (TencentCloudSDKException, RuntimeError, TimeoutError, OSError) as err:
        result = {"code": 1, "error": str(err)}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
