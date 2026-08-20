#!/usr/bin/env python3
"""根据 thread_id 下载 sandbox 中的全部文件。"""

from __future__ import annotations

import argparse
import asyncio
import json

from common import create_client, download_all_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载 SciencePal sandbox 文件")
    parser.add_argument("--thread-id", required=True, help="thread_id")
    parser.add_argument("--output-dir", required=True, help="本地输出目录")
    parser.add_argument("--root", default="/", help="sandbox 起始目录")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with create_client() as client:
        sandbox_info = await client.sandbox.get_thread_sandbox(args.thread_id)
        downloaded = await download_all_files(
            client,
            sandbox_info.sandbox_id,
            args.output_dir,
            root=args.root,
        )
        print(
            json.dumps(
                {
                    "thread_id": sandbox_info.thread_id,
                    "project_id": sandbox_info.project_id,
                    "sandbox_id": sandbox_info.sandbox_id,
                    "downloaded_count": len(downloaded),
                    "output_dir": args.output_dir,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
