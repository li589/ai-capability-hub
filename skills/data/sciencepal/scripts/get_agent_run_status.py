#!/usr/bin/env python3
"""获取 agent run 当前状态。"""

from __future__ import annotations

import argparse
import asyncio
import json

from common import create_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="查询 SciencePal agent run 状态")
    parser.add_argument("--agent-run-id", required=True, help="agent_run_id")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with create_client() as client:
        run = await client.runs.get(args.agent_run_id)
        print(
            json.dumps(
                {
                    "id": run.id,
                    "thread_id": run.thread_id,
                    "status": run.status,
                    "started_at": run.started_at,
                    "completed_at": run.completed_at,
                    "error": run.error,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
