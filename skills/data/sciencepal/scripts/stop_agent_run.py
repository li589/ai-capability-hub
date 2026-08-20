#!/usr/bin/env python3
"""停止正在运行的 agent 任务。"""

from __future__ import annotations

import argparse
import asyncio
import json

from common import create_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="停止 SciencePal agent 运行")
    parser.add_argument("--agent-run-id", required=True, help="要停止的 agent_run_id")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with create_client() as client:
        success = await client.runs.stop(args.agent_run_id)
        # stop() 返回 bool，需要再查询状态获取详细信息
        run = await client.runs.get(args.agent_run_id)
        print(
            json.dumps(
                {
                    "agent_run_id": args.agent_run_id,
                    "stop_requested": success,
                    "status": run.status,
                    "error": run.error,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
