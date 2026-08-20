#!/usr/bin/env python3
"""Skill 本地联调脚本。

用法（项目根目录）:
  .venv/bin/python skills/<skill-name>/test.py
  .venv/bin/python skills/<skill-name>/test.py --base http://127.0.0.1:38080

复制 _template 后请修改 MODEL、CAPABILITY 与 payload。
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import requests

DEFAULT_BASE = "http://127.0.0.1:38080"
MODEL = "ixhlink-skills-lyric-gen"
CAPABILITY = "chat"


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill 本地联调")
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--skip-wait", action="store_true", help="402 时只打印支付信息，不等待")
    args = parser.parse_args()

    body = {
        "capability": CAPABILITY,
        "model": MODEL,
        "payload": {
            "messages": [{"role": "user", "content": "写一首盛夏告别的流行歌词"}],
            "options": {
                "genre": "pop",
                "theme": "盛夏告别",
                "mood": "失落虐",
                "pov": "我对他",
                "length": "standard",
                "language": "zh",
                "material": "暗恋未果，旧教室，橘色路灯",
            },
        },
    }
    base = args.base.rstrip("/")
    print(f"POST {base}/api/v1/llm/invoke")
    print(json.dumps(body, ensure_ascii=False, indent=2))

    resp = requests.post(f"{base}/api/v1/llm/invoke", json=body, timeout=120)
    print(f"\nHTTP {resp.status_code}")
    print(f"WeixinPay-Required: {resp.headers.get('WeixinPay-Required', '')}")
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

    if resp.status_code == 402:
        if args.skip_wait:
            return 0
        input("\n完成支付后按 Enter 重试…")
        headers = {"WeixinPay-Required": resp.headers.get("WeixinPay-Required", "")}
        pid = resp.headers.get("X-Payment-Id", "")
        if pid:
            headers["X-Payment-Id"] = pid
        resp = requests.post(f"{base}/api/v1/llm/invoke", json=body, headers=headers, timeout=120)
        print(f"\n重试 HTTP {resp.status_code}")
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

    if resp.status_code != 200 or not resp.json().get("success"):
        return 1

    task = (resp.json().get("data") or {}).get("task")
    if isinstance(task, dict) and task.get("id"):
        task_id = str(task["id"])
        print(f"\n轮询任务 {task_id} …")
        while True:
            tr = requests.get(f"{base}/api/v1/llm/tasks/{task_id}", timeout=30)
            data = tr.json().get("data") or {}
            status = data.get("status", "")
            print(f"  status={status}")
            if status in {"succeeded", "failed", "insufficient_points"}:
                print(json.dumps(data, ensure_ascii=False, indent=2))
                return 0 if status == "succeeded" else 2
            time.sleep(3)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
