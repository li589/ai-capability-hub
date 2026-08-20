#!/usr/bin/env python3
"""发起一个新的 agent 任务并输出 thread_id 与 agent_run_id。"""

from __future__ import annotations

import argparse
import asyncio
import json

from common import create_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="发起 SciencePal agent 任务")
    parser.add_argument("--prompt", required=True, help="用户输入 prompt")
    parser.add_argument("--model-name", default=None, help="可选模型名")
    parser.add_argument("--agent-id", default=None, help="可选 agent_id")
    parser.add_argument(
        "--agent-select-type",
        default="manual",
        choices=["manual", "auto"],
        help="agent 选择方式",
    )
    parser.add_argument(
        "--web-search-on",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否开启网络搜索",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with create_client() as client:
        response = await client.runs.initiate(
            prompt=args.prompt,
            model_name=args.model_name,
            agent_id=args.agent_id,
            agent_select_type=args.agent_select_type,
            web_search_on=args.web_search_on,
        )
        if not response.agent_run_id:
            raise RuntimeError("接口未返回 agent_run_id")

        print(
            json.dumps(
                {
                    "thread_id": response.thread_id,
                    "agent_run_id": response.agent_run_id,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
