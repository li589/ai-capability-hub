#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频号爆款文案生成（体验版）【零一数科·出品】 —— 脚本提交服务端（旁路）

纯标准库（urllib）。在 agent 渲染出最终脚本 Markdown 后调用，把脚本正文
POST 到服务端做登记/校验。

设计原则——**绝不阻塞脚本交付**：
  - 无论网络异常、超时、接口非 2xx、返回体无法解析，都只打日志并以退出码 0 结束；
  - 提交只是「锦上添花」，失败时脚本本身已生成并展示给用户，提交结果可缺省。

提交端点为 free-report-content/integrity-check（与拆解（体验版）v0.3.0 共用）：

    https://claw.lingyishuke.com/services/api/v1/content-ops/free-report-content/integrity-check

请求体必须携带 scene=script_generation 以区分场景：

    POST Body: {"content": "<脚本Markdown>", "scene": "script_generation"}

> 拆解场景不带 scene 或带 full_deconstruct，DB 记 full_deconstruct；
> 本生成场景固定传 script_generation，DB 据此归到脚本生成。

用法:
    python3 submit_script.py <script_md_path> [--timeout 20]
    # 或从 stdin 读脚本内容：
    cat script.md | python3 submit_script.py - [--timeout 20]

stdout 输出（始终输出，供 agent 解析）:
    === WX_SCRIPT_SUBMIT_START ===
    { "ok": true|false, "status": "checked|skipped", "http_status": 200,
      "result": <接口返回的 JSON 或原始文本>, "reason": "失败原因（仅 ok=false 时）" }
    === WX_SCRIPT_SUBMIT_END ===

退出码:
    0   总是 0（提交为旁路，不阻塞脚本交付）
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://claw.lingyishuke.com/services/api/v1/content-ops/free-report-content/integrity-check"

RESULT_START = "=== WX_SCRIPT_SUBMIT_START ==="
RESULT_END = "=== WX_SCRIPT_SUBMIT_END ==="


def log(msg: str) -> None:
    print(f"[submit_script] {msg}", file=sys.stderr, flush=True)


def emit(payload: dict) -> None:
    """把提交结果以标记块输出到 stdout，供 agent 解析。"""
    print(RESULT_START, flush=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
    print(RESULT_END, flush=True)


def read_content(src: str) -> "str | None":
    """从文件路径或 stdin（src == '-'）读取脚本文本。失败返回 None。"""
    if src == "-":
        try:
            return sys.stdin.read()
        except Exception as e:  # noqa: BLE001
            log(f"读取 stdin 失败：{e}")
            return None
    p = Path(src).expanduser()
    if not p.exists() or not p.is_file():
        log(f"脚本文件不存在：{p}")
        return None
    try:
        return p.read_text("utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"读取脚本文件失败：{e}")
        return None


def call_submit_api(content: str, timeout: float) -> dict:
    """POST {"content": content, "scene": "script_generation"} 到提交接口。

    scene 固定为 script_generation，标识这是脚本生成场景的提交，与拆解场景区分。
    任何异常（网络/超时/SSL/非 2xx）都被捕获并转为 {"ok": false, ...}，调用方据此
    降级，绝不抛出——提交是旁路，失败不影响脚本交付。
    """
    payload = {"content": content, "scene": "script_generation"}
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
        description="脚本提交服务端（旁路，失败不阻塞脚本交付）")
    ap.add_argument("script", help="脚本 Markdown 文件路径，或 '-' 从 stdin 读取")
    ap.add_argument("--timeout", type=float, default=20.0,
                    help="接口请求超时秒数（默认 20）")
    args = ap.parse_args()

    content = read_content(args.script)
    if content is None or not content.strip():
        log("脚本内容为空或读取失败，跳过提交（不影响交付）。")
        emit({"ok": False, "status": "skipped", "reason": "empty_or_unreadable_script"})
        return 0

    log("正在提交脚本到服务端…")
    result = call_submit_api(content, args.timeout)
    if result.get("ok"):
        log("脚本提交完成。")
    else:
        log("脚本提交未完成（已降级），脚本本身不受影响。")
    emit(result)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        # 兜底：即便意外异常也不阻塞脚本交付
        log(f"内部异常，跳过提交：{e}")
        emit({"ok": False, "status": "skipped", "reason": f"unexpected: {e}"})
        sys.exit(0)
