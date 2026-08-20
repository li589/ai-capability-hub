#!/usr/bin/env python3
"""带通知回调的轮询脚本：启动通知 + 定期状态更新 + 完成通知"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from common import create_client, download_all_files, is_terminal_status

DEFAULT_POLL_INTERVAL = 20  # 秒，每20秒检查一次
DEFAULT_TIMEOUT = 3600  # 1小时
NOTIFY_DIR = Path(__file__).parent.parent / "notifications"


def notify(session_key: str, message: str, notify_type: str = "status"):
    """写入通知文件，等待心跳或主动检查时推送"""
    NOTIFY_DIR.mkdir(parents=True, exist_ok=True)
    notify_file = NOTIFY_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{notify_type}.json"
    notify_data = {
        "timestamp": datetime.now().isoformat(),
        "session_key": session_key,
        "type": notify_type,
        "message": message
    }
    notify_file.write_text(json.dumps(notify_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[NOTIFY] {notify_type}: {message}")
    sys.stdout.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="带通知回调的 SciencePal 轮询脚本"
    )
    parser.add_argument("--agent-run-id", required=True, help="agent_run_id")
    parser.add_argument("--thread-id", required=True, help="thread_id")
    parser.add_argument("--session-key", required=True, help="回调的 session key")
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
        help="状态文件路径",
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
    session_key = args.session_key
    output_dir = args.output_dir or f"./downloads/{agent_run_id}"
    poll_interval = args.poll_interval
    timeout = args.timeout
    status_file = args.status_file

    # 启动通知
    notify(session_key, f"SciencePal 任务已启动\nagent_run_id: {agent_run_id}\nthread_id: {thread_id}", "started")

    print(f"[{datetime.now().isoformat()}] 开始轮询 agent_run_id={agent_run_id}")
    print(f"[{datetime.now().isoformat()}] thread_id={thread_id}")
    print(f"[{datetime.now().isoformat()}] 输出目录: {output_dir}")
    print(f"[{datetime.now().isoformat()}] 轮询间隔: {poll_interval}s")
    sys.stdout.flush()

    async with create_client() as client:
        start_time = asyncio.get_running_loop().time()
        last_status = None
        poll_count = 0

        while True:
            run = await client.runs.get(agent_run_id)
            status = run.status
            poll_count += 1

            # 状态变化时通知
            if status != last_status:
                notify(session_key, f"任务状态变更: {status}", "status_change")
                print(f"[{datetime.now().isoformat()}] 状态: {status}")
                sys.stdout.flush()
                last_status = status

            # 每20秒（每次轮询）通知一次当前状态
            if poll_count > 1:
                elapsed = int(asyncio.get_running_loop().time() - start_time)
                notify(session_key, f"任务运行中... 状态: {status}, 已运行: {elapsed}s", "progress")

            if is_terminal_status(status):
                print(f"[{datetime.now().isoformat()}] 任务结束，最终状态: {status}")
                sys.stdout.flush()
                break

            # 检查超时
            elapsed = asyncio.get_running_loop().time() - start_time
            if elapsed >= timeout:
                error_msg = f"轮询超时 ({timeout}秒)"
                notify(session_key, f"任务超时: {error_msg}", "error")
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
                    Path(status_file).parent.mkdir(parents=True, exist_ok=True)
                    Path(status_file).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
                sys.exit(1)

            await asyncio.sleep(poll_interval)

        # 检查最终状态
        if run.status != "completed":
            error_msg = run.error or f"任务未成功完成: {run.status}"
            notify(session_key, f"任务失败: {error_msg}", "error")
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
                Path(status_file).parent.mkdir(parents=True, exist_ok=True)
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

        # 完成通知
        notify(session_key, f"任务完成!\n共下载 {len(downloaded)} 个文件\n输出目录: {output_dir}", "completed")

        print(f"[{datetime.now().isoformat()}] 下载完成，共 {len(downloaded)} 个文件")
        sys.stdout.flush()

        result = {
            "success": True,
            "agent_run_id": agent_run_id,
            "thread_id": thread_id,
            "sandbox_id": sandbox_info.sandbox_id,
            "downloaded_count": len(downloaded),
            "output_dir": str(Path(output_dir).resolve()),
            "files": downloaded[:20],
        }

        if status_file:
            Path(status_file).parent.mkdir(parents=True, exist_ok=True)
            Path(status_file).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{datetime.now().isoformat()}] 状态文件已写入: {status_file}")

        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
