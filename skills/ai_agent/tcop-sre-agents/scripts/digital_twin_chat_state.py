from __future__ import annotations

import argparse
import json
import sys

import state_io

def _state_dir(args: argparse.Namespace) -> str | None:
    if getattr(args, "state_dir", None):
        import os
        return os.path.expanduser(args.state_dir)
    if getattr(args, "state_file", None):
        import os
        return os.path.dirname(os.path.abspath(os.path.expanduser(args.state_file))) or None
    return None

def _print_show(state_dir: str | None) -> None:
    last_used = state_io.load_last_used(state_dir)
    sessions = state_io.list_sessions(state_dir)
    active = sum(1 for s in sessions if s.get("status") in ("running", "streaming", "pending"))

    if last_used:
        label = last_used.get("name") or "(unnamed)"
        print(f"last_used_agent: {label} / {last_used.get('agent_id')}", file=sys.stderr)
        print(f"  updated_at : {last_used.get('updated_at', '(unknown)')}", file=sys.stderr)
    else:
        print("last_used_agent: (none) — 跨会话无记忆", file=sys.stderr)

    print(f"sessions: {len(sessions)} 个（活跃 {active}/{state_io.max_concurrent()}）", file=sys.stderr)
    for s in sessions:
        print(
            f"  [{s.get('handle')}] {s.get('name') or '(unnamed)'} {s.get('agent_id') or ''} "
            f"status={s.get('status')} chars={s.get('emitted_len', 0)}",
            file=sys.stderr,
        )

    print(json.dumps({"last_used_agent": last_used, "sessions": sessions, "active": active}, ensure_ascii=True))

def cmd_show(args: argparse.Namespace) -> int:
    state_io.migrate_legacy_state(_state_dir(args))
    _print_show(_state_dir(args))
    return 0

def cmd_set(args: argparse.Namespace) -> int:
    if not args.agent_id:
        print("错误: 需要 --agent-id", file=sys.stderr)
        return 2
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    if args.agent_id == state_io.DEFAULT_AGENT_ID:
        print(
            f"[LastUsed] 默认分身 {state_io.DEFAULT_AGENT_ID} 不写入跨会话记忆（避免锁死）",
            file=sys.stderr,
        )
        return 0
    state_io.save_last_used(state_dir, args.agent_id, args.name or "")
    print(f"[LastUsed] 已写入跨会话记忆: {args.name or '(unnamed)'} ({args.agent_id})")
    return 0

def cmd_clear(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    removed = state_io.clear_last_used(state_dir)
    print(f"[LastUsed] {'已清空跨会话记忆' if removed else '无记忆可清空'}")
    return 0

def main() -> None:
    parser = argparse.ArgumentParser(
        description="tcop-sre-agents 分身记忆 + 会话状态查询（last_used_agent + sessions 概览）"
    )
    parser.add_argument("--state-dir", default=None, help="状态目录")
    parser.add_argument("--state-file", default=None, help="(兼容旧) state.json 路径，取 dirname")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show", help="打印 last_used_agent + 会话概览")
    p_show.set_defaults(func=cmd_show)

    p_set = sub.add_parser("set", help="设置 last_used_agent（跨会话记忆）")
    p_set.add_argument("--agent-id", required=True, help="agt-xxxxxxxx")
    p_set.add_argument("--name", default="", help="分身名（展示用）")
    p_set.set_defaults(func=cmd_set)

    p_clear = sub.add_parser("clear", help="清空 last_used_agent")
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
