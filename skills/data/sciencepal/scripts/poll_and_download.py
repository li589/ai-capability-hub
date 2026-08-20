#!/usr/bin/env python3
"""轮询 agent run 状态，完成后自动下载 sandbox 文件。"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from common import create_client, download_all_files, is_terminal_status

DEFAULT_POLL_INTERVAL = 10  # 秒
DEFAULT_TIMEOUT = 3600  # 1小时


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="轮询 SciencePal agent run 状态，完成后下载文件"
    )
    parser.add_argument("--agent-run-id", required=True, help="agent_run_id")
    parser.add_argument("--thread-id", required=True, help="thread_id")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="下载目录（默认: ./downloads/{agent_run_id}）",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help=f"轮询间隔秒数（默认: {DEFAULT_POLL_INTERVAL}）",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"超时秒数（默认: {DEFAULT_TIMEOUT}）",
    )
    parser.add_argument(
        "--status-file",
        default=None,
        help="状态文件路径，完成后写入结果（JSON格式）",
    )
    parser.add_argument(
        "--root",
        default="/workspace",
        help="sandbox 下载起始目录（默认: /workspace）",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    agent_run_id = args.agent_run_id
    thread_id = args.thread_id
    output_dir = args.output_dir or f"./downloads/{agent_run_id}"
    poll_interval = args.poll_interval
    timeout = args.timeout
    status_file = args.status_file

    print(f"[{datetime.now().isoformat()}] 开始轮询 agent_run_id={agent_run_id}")
    print(f"[{datetime.now().isoformat()}] thread_id={thread_id}")
    print(f"[{datetime.now().isoformat()}] 输出目录: {output_dir}")
    print(f"[{datetime.now().isoformat()}] 下载目录: {args.root}")
    sys.stdout.flush()

    async with create_client() as client:
        # 轮询状态
        start_time = asyncio.get_running_loop().time()
        last_status = None

        while True:
            run = await client.runs.get(agent_run_id)
            status = run.status

            # 状态变化时打印
            if status != last_status:
                print(f"[{datetime.now().isoformat()}] 状态: {status}")
                sys.stdout.flush()
                last_status = status

            if is_terminal_status(status):
                print(f"[{datetime.now().isoformat()}] 任务结束，最终状态: {status}")
                sys.stdout.flush()
                break

            # 检查超时
            elapsed = asyncio.get_running_loop().time() - start_time
            if elapsed >= timeout:
                error_msg = f"轮询超时 ({timeout}秒)"
                print(f"[{datetime.now().isoformat()}] 错误: {error_msg}")
                sys.stdout.flush()
                result = {
                    "success": False,
                    "error": error_msg,
                    "agent_run_id": agent_run_id,
                    "thread_id": thread_id,
                    "final_status": status,
                }
                if status_file:
                    Path(status_file).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
                sys.exit(1)

            await asyncio.sleep(poll_interval)

        # 检查最终状态
        if run.status != "completed":
            error_msg = run.error or f"任务未成功完成: {run.status}"
            print(f"[{datetime.now().isoformat()}] 错误: {error_msg}")
            sys.stdout.flush()
            result = {
                "success": False,
                "error": error_msg,
                "agent_run_id": agent_run_id,
                "thread_id": thread_id,
                "final_status": run.status,
            }
            if status_file:
                Path(status_file).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            sys.exit(1)

        # 下载文件
        print(f"[{datetime.now().isoformat()}] 开始下载 sandbox 文件...")
        sys.stdout.flush()

        sandbox_info = await client.sandbox.get_thread_sandbox(thread_id)
        downloaded = await download_all_files(
            client,
            sandbox_info.sandbox_id,
            output_dir,
            root=args.root,
        )

        print(f"[{datetime.now().isoformat()}] 下载完成，共 {len(downloaded)} 个文件")
        sys.stdout.flush()

        result = {
            "success": True,
            "agent_run_id": agent_run_id,
            "thread_id": thread_id,
            "sandbox_id": sandbox_info.sandbox_id,
            "downloaded_count": len(downloaded),
            "output_dir": str(Path(output_dir).resolve()),
            "files": downloaded[:20],  # 只列出前20个，避免太长
        }

        if status_file:
            Path(status_file).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{datetime.now().isoformat()}] 状态文件已写入: {status_file}")

        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
