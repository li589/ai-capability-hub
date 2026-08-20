#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量用户运营体系搭建 —— 报告提交服务端（旁路）

纯标准库（urllib）。在 agent 写完三件套 Markdown 后调用，把报告正文
POST 到服务端做登记/校验。

设计原则——**绝不阻塞报告交付**：
  - 无论网络异常、超时、接口非 2xx、返回体无法解析，都只打日志并以退出码 0 结束；
  - 提交只是「锦上添花」，失败时报告本身已生成并展示给用户，提交结果可缺省。

提交端点为 free-report-content/integrity-check（多 skill 共用）：

    https://claw.lingyishuke.com/services/api/v1/content-ops/free-report-content/integrity-check

请求体必须携带 scene 以区分场景；本 skill 的 scene **固定为本 skill 的 metadata.slug**：

    POST Body: {"content": "<报告Markdown>", "scene": "lingyi-full-user-ops-system-build", "origin": "01workbuddy", "origin_method": "skill"}

> 现有约定示例：full_deconstruct=视频拆解、script_generation=脚本生成；
> 本 skill 固定传 lingyi-full-user-ops-system-build（= metadata.slug）。

用法:
    python3 submit_script.py <report_md_path> [--timeout 20]
    # 或从 stdin 读报告内容：
    cat report.md | python3 submit_script.py - [--timeout 20]

stdout 输出（始终输出，供 agent 解析）:
    === USER_LIFECYCLE_SUBMIT_START ===
    { "ok": true|false, "status": "checked|skipped", "http_status": 200,
      "result": <接口返回的 JSON 或原始文本>, "reason": "失败原因（仅 ok=false 时）" }
    === USER_LIFECYCLE_SUBMIT_END ===

退出码:
    0   总是 0（提交为旁路，不阻塞报告交付）
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://claw.lingyishuke.com/services/api/v1/content-ops/free-report-content/integrity-check"

# 场景标识：与本 skill metadata.slug 一致
SCENE = "lingyi-full-user-ops-system-build"

RESULT_START = "=== USER_LIFECYCLE_SUBMIT_START ==="
RESULT_END = "=== USER_LIFECYCLE_SUBMIT_END ==="


def log(msg: str) -> None:
    print(f"[submit_script] {msg}", file=sys.stderr, flush=True)


def emit(payload: dict) -> None:
    """把提交结果以标记块输出到 stdout，供 agent 解析。"""
    print(RESULT_START, flush=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
    print(RESULT_END, flush=True)


def read_content(src: str) -> "str | None":
    """从文件路径或 stdin（src == '-'）读取报告正文。失败返回 None。"""
    if src == "-":
        try:
            return sys.stdin.read()
        except Exception as e:  # noqa: BLE001
            log(f"读取 stdin 失败：{e}")
            return None
    p = Path(src).expanduser()
    if not p.exists() or not p.is_file():
        log(f"报告文件不存在：{p}")
        return None
    try:
        return p.read_text("utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"读取报告文件失败：{e}")
        return None


def call_submit_api(content: str, timeout: float) -> dict:
    """POST {"content": content, "scene": SCENE, "origin": "01workbuddy", "origin_method": "skill"} 到提交接口。

    scene 固定为 lingyi-full-user-ops-system-build（本 skill slug），与拆解/脚本生成等场景区分。
    任何异常（网络/超时/SSL/非 2xx）都被捕获并转为 {"ok": false, ...}，调用方据此
    降级，绝不抛出——提交是旁路，失败不影响报告交付。
    """
    payload = {"content": content, "scene": SCENE, "origin": "01workbuddy", "origin_method": "skill"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read().decode("utf-8", "ignore")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw
            return {"ok": True, "status": "checked", "http_status": status, "result": parsed}
    except urllib.error.HTTPError as e:
        # 接口返回了非 2xx：读出响应体便于排查，但仍视为旁路失败，不阻塞
        detail = ""
        try:
            detail = e.read().decode("utf-8", "ignore")[:1000]
        except Exception:  # noqa: BLE001
            pass
        log(f"提交接口返回 HTTP {e.code}，跳过提交：{detail}")
        return {"ok": False, "status": "skipped", "http_status": e.code,
                "reason": f"HTTP {e.code}: {detail}"}
    except urllib.error.URLError as e:
        log(f"提交接口请求失败（网络/超时），跳过提交：{e.reason}")
        return {"ok": False, "status": "skipped", "reason": f"URLError: {e.reason}"}
    except Exception as e:  # noqa: BLE001
        log(f"提交异常，跳过提交：{e}")
        return {"ok": False, "status": "skipped", "reason": f"{type(e).__name__}: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="报告提交服务端（旁路，失败不阻塞报告交付）")
    ap.add_argument("report", help="报告 Markdown 文件路径，或 '-' 从 stdin 读取")
    ap.add_argument("--timeout", type=float, default=20.0,
                    help="接口请求超时秒数（默认 20）")
    args = ap.parse_args()

    content = read_content(args.report)
    if content is None or not content.strip():
        log("报告内容为空或读取失败，跳过提交（不影响交付）。")
        emit({"ok": False, "status": "skipped", "reason": "empty_or_unreadable_report"})
        return 0

    log(f"正在提交报告到服务端（scene={SCENE}）…")
    result = call_submit_api(content, args.timeout)
    if result.get("ok"):
        log("报告提交完成。")
    else:
        log("报告提交未完成（已降级），报告本身不受影响。")
    emit(result)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        # 兜底：即便意外异常也不阻塞报告交付
        log(f"内部异常，跳过提交：{e}")
        emit({"ok": False, "status": "skipped", "reason": f"unexpected: {e}"})
        sys.exit(0)
