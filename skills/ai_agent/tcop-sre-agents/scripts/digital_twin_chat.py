from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from typing import Any, Callable, TextIO

import state_io
from state_io import DEFAULT_AGENT_ID, MAIN_HANDLE

from common import (
    build_chat_client,
    build_monitor_client,
    call_api,
)

try:
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
        TencentCloudSDKException,
    )
except ImportError:
    print(
        json.dumps(
            {"success": False, "error": "tencentcloud-sdk-python 未安装，请运行: pip3 install tencentcloud-sdk-python"},
            ensure_ascii=True,
        )
    )
    sys.exit(1)

def _resolve_agent_id_by_name(name: str) -> dict[str, Any] | None:
    if not name or not name.strip():
        return None
    try:
        resp = call_api("ListAIWorkbenchAgents", {})
    except Exception as exc:
        print(
            f"[ResolveByName] ListAIWorkbenchAgents 调用失败（已忽略，回退到默认分身）：{exc}",
            file=sys.stderr,
        )
        return None

    agents = []
    if isinstance(resp, dict):
        agents = resp.get("Agents") or []
    if not isinstance(agents, list) or not agents:
        print(
            f"[ResolveByName] ListAIWorkbenchAgents 返回为空，无法解析 name='{name}'",
            file=sys.stderr,
        )
        return None

    matches = [a for a in agents if isinstance(a, dict) and a.get("Name") == name]
    if not matches:
        print(
            f"[ResolveByName] 未找到名为 '{name}' 的分身（共 {len(agents)} 个候选）；"
            f"将回退到下一级路由（last_used 或默认分身）",
            file=sys.stderr,
        )
        return None
    if len(matches) > 1:
        ids = [m.get("AgentId") for m in matches]
        print(
            f"[ResolveByName] name='{name}' 命中多个分身 {ids}，脚本不自动选择，"
            f"请由 AI 端明确传入 --agent-id；本轮将回退到下一级路由",
            file=sys.stderr,
        )
        return None

    agent_id = matches[0].get("AgentId") or ""
    if not agent_id:
        return None
    print(
        f"[ResolveByName] 通过 ListAIWorkbenchAgents 解析 name='{name}' → "
        f"AgentID={agent_id}",
        file=sys.stderr,
    )
    return {"agent_id": agent_id, "name": name}

def _resolve_agent_id(
    arg_agent_id: str,
    arg_name: str,
    state_dir: str | None,
) -> tuple[str, str, bool]:

    if arg_agent_id:
        return arg_agent_id, arg_name or "", False

    if arg_name:
        resolved = _resolve_agent_id_by_name(arg_name)
        if resolved:
            return resolved["agent_id"], resolved["name"], False

        print(
            f"[Resolve] 指名分身 '{arg_name}' 未能解析，继续按 last_used/默认回退",
            file=sys.stderr,
        )

    last_used = state_io.load_last_used(state_dir)
    if last_used:
        print(
            f"[Resolve] 未指定分身，自动复用 last_used_agent.json → "
            f"{last_used.get('name') or '(unnamed)'} ({last_used['agent_id']})",
            file=sys.stderr,
        )
        return last_used["agent_id"], last_used.get("name") or "", False

    print(
        f"[Resolve] 未指定分身且无 last_used 记忆，回退默认分身 {DEFAULT_AGENT_ID}",
        file=sys.stderr,
    )
    return DEFAULT_AGENT_ID, "", True

_POLL_INTERVAL_SEC = 2
_POLL_TIMEOUT_SEC = 120

def _send_to_start_run(
    api_params: dict[str, Any],
) -> tuple[str, str]:
    client = build_chat_client()
    print(
        f"[Send] fibona.SendAIWorkbenchChat（SessionID={'(空) 首发' if not api_params.get('SessionID') else api_params['SessionID']}）"
        f"——仅消费 SESSION_INFO+RUN_STARTED 后断开",
        file=sys.stderr,
    )
    resp_iter = client.call_sse("SendAIWorkbenchChat", api_params)

    session_id = api_params.get("SessionID") or ""
    run_id = ""
    error_payload: dict[str, Any] | None = None
    ev_count = 0

    for event in resp_iter:
        ev_count += 1
        if not isinstance(event, dict):
            continue
        raw = event.get("data")
        if not isinstance(raw, str) or not raw:
            continue
        try:
            outer = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(outer, dict):
            continue

        if outer.get("code") not in (0, None):
            error_payload = {
                "code": outer.get("code"),
                "msg": outer.get("msg"),
                "request_id": outer.get("RequestId"),
            }
            break
        inner = outer.get("data")
        if not isinstance(inner, dict):
            continue

        ev_type = inner.get("type")

        if ev_type == "CUSTOM" and inner.get("name") == "SESSION_INFO":
            sid = inner.get("sessionId") or ""
            if sid:
                session_id = sid
                print(f"[Send] SESSION_INFO sessionId={sid}", file=sys.stderr)
            continue

        if ev_type == "RUN_STARTED":
            run_id = inner.get("runId") or ""
            print(f"[Send] RUN_STARTED runId={run_id}", file=sys.stderr)

            if session_id and run_id:
                print(
                    f"[Send] 已拿到 sessionId+runId，断开 SSE（events={ev_count}），转快照轮询",
                    file=sys.stderr,
                )
                break
            continue

        if ev_type == "DIRECT_ROUTING":
            print(
                f"[Send] DIRECT_ROUTING agent_id={inner.get('agent_id')}",
                file=sys.stderr,
            )
            continue

        if ev_type in ("ERROR", "RUN_ERROR"):
            error_payload = {
                "code": inner.get("code", ev_type),
                "msg": inner.get("message") or inner.get("error") or json.dumps(inner, ensure_ascii=False),
                "request_id": outer.get("RequestId"),
            }
            print(
                f"[Send] {ev_type}: code={error_payload['code']} msg={error_payload['msg'][:200]}",
                file=sys.stderr,
            )
            break

        if ev_type in ("RUN_FINISHED", "DONE"):
            error_payload = {
                "code": "EARLY_DONE",
                "msg": f"流在拿到 runId 前就结束（{ev_type}），可能为空回复",
                "request_id": outer.get("RequestId"),
            }
            break

    if error_payload:
        raise RuntimeError(
            f"SendAIWorkbenchChat 启动失败: code={error_payload.get('code')} "
            f"msg={error_payload.get('msg')} request_id={error_payload.get('request_id')}"
        )

    if not run_id:
        raise RuntimeError(
            f"SendAIWorkbenchChat 流结束仍未拿到 runId（events={ev_count}, session_id={session_id}），"
            "无法转快照轮询"
        )

    return session_id, run_id

def _extract_reply_text(message: dict[str, Any]) -> str:
    content = message.get("Content") or ""
    if content:

        stripped = content.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, dict) and isinstance(parsed.get("type"), str):
                    return parsed.get("delta") or ""
                if isinstance(parsed, list):
                    return "".join(
                        p.get("delta", "")
                        for p in parsed
                        if isinstance(p, dict) and isinstance(p.get("type"), str) and p.get("delta")
                    )
            except json.JSONDecodeError:
                pass
        return content

    blocks = message.get("ContentBlocks") or []
    parts: list[str] = []
    for blk in blocks:
        if not isinstance(blk, dict):
            continue
        if blk.get("Type") != "TEXT_MESSAGE_CONTENT":
            continue
        data = blk.get("Data") or ""
        if not isinstance(data, str):
            continue
        try:
            ev = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict) and isinstance(ev.get("delta"), str):
            parts.append(ev["delta"])
    return "".join(parts)

def _extract_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = message.get("ContentBlocks") or []
    tool_calls: list[dict[str, Any]] = []
    for blk in blocks:
        if not isinstance(blk, dict):
            continue
        ev_type = blk.get("Type") or ""
        if not ev_type.startswith("TOOL_CALL_"):
            continue
        data = blk.get("Data") or ""
        ev: dict[str, Any] = {}
        if isinstance(data, str):
            try:
                ev = json.loads(data) if data else {}
            except json.JSONDecodeError:
                ev = {}
        elif isinstance(data, dict):
            ev = data
        tool_calls.append(
            {
                "type": ev_type,
                "tool": ev.get("toolName"),
                "args": ev.get("args"),
                "output": ev.get("output"),
                "ts": ev.get("timestamp"),
            }
        )
    return tool_calls

def _find_target_message(
    messages: list[dict[str, Any]], run_id: str
) -> dict[str, Any] | None:
    if not run_id or not messages:
        return None
    for m in messages:
        if (
            isinstance(m, dict)
            and m.get("Role") == "assistant"
            and m.get("RunId") == run_id
        ):
            return m
    return None

_TERMINAL_STATUS = {"completed", "failed", "interrupted", "timeout"}

def _poll_once(
    state_dir: str | None,
    handle: str,
    mon_client: Any,
    md_file: TextIO | None = None,
    write_stdout: bool = True,
) -> tuple[str, str, int, list[dict[str, Any]]]:
    rec = state_io.load_session(state_dir, handle)
    if not rec:
        print(f"[Poll] handle={handle} 不存在", file=sys.stderr)
        return "", "missing", 0, []

    session_id = rec.get("session_id") or ""
    run_id = rec.get("run_id") or ""
    emitted_len = int(rec.get("emitted_len") or 0)
    cur_status = rec.get("status") or ""

    if cur_status in _TERMINAL_STATUS and cur_status != "timeout":
        print(f"[Poll] handle={handle} 已终态 status={cur_status}，跳过 API", file=sys.stderr)
        return "", cur_status, emitted_len, []

    if not session_id or not run_id:
        print(
            f"[Poll] handle={handle} 缺 session_id/run_id（session={session_id!r} run={run_id!r}）",
            file=sys.stderr,
        )
        return "", "no-run", emitted_len, []

    try:
        resp = call_api(
            "ListAIWorkbenchMessages",
            {"SessionId": session_id, "Limit": 5, "Direction": "backward"},
            client=mon_client,
        )
    except Exception as exc:
        print(f"[Poll] handle={handle} 调用失败: {exc}", file=sys.stderr)
        return "", "error", emitted_len, []

    messages = resp.get("Messages") or []
    target = _find_target_message(messages, run_id)
    if target is None:
        print(
            f"[Poll] handle={handle} 尚无 assistant 消息（msgs={len(messages)}），等 run 启动",
            file=sys.stderr,
        )
        return "", "pending", emitted_len, []

    msg_status = target.get("Status") or "streaming"
    full_text = _extract_reply_text(target)
    tool_calls = _extract_tool_calls(target)
    full_len = len(full_text)

    finished_at = state_io._now_iso() if msg_status in _TERMINAL_STATUS else None

    actual_delta: list[str] = []

    def _upd(r: dict[str, Any]) -> dict[str, Any] | None:

        cur = int(r.get("emitted_len") or 0)
        d = full_text[cur:] if full_len > cur else ""
        if d and write_stdout:
            sys.stdout.write(d)
            sys.stdout.flush()
            if md_file is not None:
                md_file.write(d)
                md_file.flush()
            actual_delta.append(d)

        if r.get("emitted_len") == full_len and r.get("status") == msg_status and not finished_at:
            return None
        r["emitted_len"] = full_len
        r["status"] = msg_status
        if finished_at:
            r["finished_at"] = finished_at
        return r

    state_io.update_session(state_dir, handle, _upd)

    delta = "".join(actual_delta)
    print(
        f"[Poll] handle={handle} status={msg_status} chars={full_len} "
        f"delta={len(delta)} tool_calls={len(tool_calls)}",
        file=sys.stderr,
    )
    return delta, msg_status, full_len, tool_calls

def _wait_blocking(
    state_dir: str | None,
    handle: str,
    md_file: TextIO | None,
    timeout: int = _POLL_TIMEOUT_SEC,
    poll_interval: int = _POLL_INTERVAL_SEC,
) -> tuple[str, int, list[dict[str, Any]]]:
    deadline = time.monotonic() + timeout
    mon_client = build_monitor_client()
    last_status = "pending"
    last_chars = 0
    tool_calls: list[dict[str, Any]] = []
    poll_idx = 0

    print(
        f"[Wait] 阻塞轮询 handle={handle} timeout={timeout}s interval={poll_interval}s",
        file=sys.stderr,
    )

    while time.monotonic() < deadline:
        poll_idx += 1
        _delta, status, full_len, tcs = _poll_once(
            state_dir, handle, mon_client, md_file=md_file, write_stdout=True
        )
        if tcs:
            tool_calls = tcs
        last_status = status
        last_chars = full_len

        if status in _TERMINAL_STATUS and status != "timeout":
            print(
                f"[Wait] ✅ 终态 status={status}（轮询 {poll_idx} 次, chars={last_chars}）",
                file=sys.stderr,
            )
            return status, last_chars, tool_calls

        time.sleep(poll_interval)

    state_io.update_session(
        state_dir, handle,
        lambda r: {**r, "status": "timeout"} if r.get("status") not in _TERMINAL_STATUS else r,
    )
    print(
        f"[Wait] ⚠️ 超时（{timeout}s）status={last_status} chars={last_chars}",
        file=sys.stderr,
    )
    return "timeout", last_chars, tool_calls

def _state_dir(args: argparse.Namespace) -> str | None:
    if getattr(args, "state_dir", None):
        return os.path.expanduser(args.state_dir)
    if getattr(args, "state_file", None):
        return os.path.dirname(os.path.abspath(os.path.expanduser(args.state_file))) or None
    return None

def _do_send(agent_id: str, content: str, session_id: str = "") -> tuple[str, str]:
    api_params: dict[str, Any] = {"SessionID": session_id or "", "Content": content}
    if agent_id:
        api_params["AgentID"] = agent_id
    return _send_to_start_run(api_params)

def _open_output(args: argparse.Namespace) -> tuple[TextIO | None, str]:
    output_path = ""
    if getattr(args, "output", ""):
        output_path = os.path.abspath(args.output)
        d = os.path.dirname(output_path)
        if d:
            os.makedirs(d, exist_ok=True)
        return open(output_path, "w", encoding="utf-8"), output_path
    return None, ""

def _decide_run_session(
    args: argparse.Namespace,
    existing: dict[str, Any] | None,
    state_dir: str | None = None,
    resolve_agent_id: Callable[[str, str], tuple[str, str, bool]] | None = None,
) -> tuple[str, str, str, str]:
    if resolve_agent_id is None:
        resolve_agent_id = lambda aid, nm: _resolve_agent_id(aid, nm, state_dir)

    if args.use_default_agent:
        reuse = ""
        if existing and existing.get("agent_id") == DEFAULT_AGENT_ID:
            reuse = existing.get("session_id") or ""

        if (
            args.session_id
            and existing
            and existing.get("agent_id")
            and existing.get("agent_id") != DEFAULT_AGENT_ID
            and args.session_id == (existing.get("session_id") or "")
        ):
            session_id = reuse
            print(
                f"[Run] 警告: --session-id {args.session_id} 属于分身 {existing.get('agent_id')}，"
                "已忽略，改用默认分身（首发）",
                file=sys.stderr,
            )
        else:
            session_id = args.session_id or reuse
        note = f"--use-default-agent: 强制默认分身 {DEFAULT_AGENT_ID}"
        return DEFAULT_AGENT_ID, "", session_id, note

    if args.session_id:
        session_belongs_main = (
            existing
            and existing.get("session_id")
            and args.session_id == existing.get("session_id")
        )

        if (
            not (args.agent_id or args.name)
            and existing
            and existing.get("agent_id")
            and session_belongs_main
        ):
            note = "续聊 main 会话"
            return existing.get("agent_id") or "", existing.get("name") or "", args.session_id, note

        agent_id, name, _ = resolve_agent_id(args.agent_id, args.name)

        if (
            (args.agent_id or args.name)
            and existing
            and existing.get("agent_id")
            and existing.get("agent_id") != agent_id
            and session_belongs_main
        ):
            note = (
                f"警告: --session-id {args.session_id} 属于分身 {existing.get('agent_id')}，"
                f"与目标分身 {agent_id} 不一致，已忽略该 session 改为首发"
            )
            return agent_id, name, "", note

        if not (args.agent_id or args.name):
            print(
                f"[Run] 无法确认该 session（{args.session_id}）归属分身，按 {agent_id} 续聊",
                file=sys.stderr,
            )
        return agent_id, name, args.session_id, ""

    if args.agent_id or args.name:
        agent_id, name, _ = resolve_agent_id(args.agent_id, args.name)
        if existing and existing.get("agent_id"):
            if existing.get("agent_id") == agent_id:
                return agent_id, name, existing.get("session_id") or "", "续聊"
            return agent_id, name, "", f"切分身 {existing.get('agent_id')}→{agent_id}"
        return agent_id, name, "", "首发"

    if existing and existing.get("agent_id"):
        return existing.get("agent_id") or "", existing.get("name") or "", existing.get("session_id") or "", "续聊"

    agent_id, name, _ = resolve_agent_id("", "")
    return agent_id, name, "", "首发"

def cmd_run(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    handle = MAIN_HANDLE
    existing = state_io.load_session(state_dir, handle)

    agent_id, name, session_id, note = _decide_run_session(args, existing, state_dir)
    if note:
        print(f"[Run] {note} agent={agent_id} session={session_id or '(空)'}", file=sys.stderr)

    md_file, output_path = _open_output(args)
    try:
        new_session_id, run_id = _do_send(agent_id, args.content, session_id)
    except TencentCloudSDKException as exc:
        print(f"[Run] SDK 异常: code={exc.code} msg={exc.message} request_id={exc.requestId}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if md_file:
            md_file.close()
        return 1
    except RuntimeError as exc:
        print(f"[Run] send 失败: {exc}", file=sys.stderr)
        if md_file:
            md_file.close()
        return 1

    rec = state_io._new_session_record(handle, agent_id, name, new_session_id, run_id)
    state_io.save_session(state_dir, handle, rec)

    try:
        status, chars, tool_calls = _wait_blocking(
            state_dir, handle, md_file, timeout=args.poll_timeout, poll_interval=_POLL_INTERVAL_SEC
        )
    finally:
        if md_file is not None:
            md_file.close()

    sys.stdout.write("\n")
    sys.stdout.flush()

    if not args.no_state_write:
        if agent_id and agent_id != DEFAULT_AGENT_ID:
            state_io.save_last_used(state_dir, agent_id, name)
    else:

        state_io.delete_session(state_dir, handle)

    print(f"[Run] 完成 status={status} chars={chars} tool_calls={len(tool_calls)}", file=sys.stderr)

    return 0 if status == "completed" else 1

def cmd_start(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    handle = args.handle or ""
    if handle:

        try:
            state_io._handle_path(state_dir, handle)
        except ValueError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1
    existing = state_io.load_session(state_dir, handle) if handle else None

    if existing:

        agent_id = existing.get("agent_id") or ""
        name = existing.get("name") or ""
        session_id = existing.get("session_id") or ""
        if args.agent_id and args.agent_id != agent_id:
            print(
                f"[Start] 警告: handle={handle} 已绑定 agent={agent_id}，忽略 CLI --agent-id={args.agent_id}（续聊须同分身）",
                file=sys.stderr,
            )
        print(f"[Start] 续聊 handle={handle} agent={agent_id}", file=sys.stderr)
    else:

        if not args.force:
            active = state_io.count_active(state_dir)
            cap = state_io.max_concurrent()
            if active >= cap:
                print(
                    f"错误: 活跃会话 {active} 已达上限 {cap}。用 --force 覆盖，或先 prune 清理已完成会话。",
                    file=sys.stderr,
                )
                return 1
        agent_id, name, _using_default = _resolve_agent_id(args.agent_id, args.name, state_dir)
        session_id = ""
        try:
            handle = state_io.claim_handle(state_dir, args.handle or None)
        except FileExistsError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1
        print(f"[Start] 首发 handle={handle} agent={agent_id}", file=sys.stderr)

    try:
        new_session_id, run_id = _do_send(agent_id, args.content, session_id)
    except (TencentCloudSDKException, RuntimeError) as exc:
        print(f"[Start] send 失败: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if not existing and handle:
            state_io.delete_session(state_dir, handle)
        return 1
    except Exception as exc:
        print(f"[Start] 未预期异常: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if not existing and handle:
            state_io.delete_session(state_dir, handle)
        return 1

    rec = state_io._new_session_record(handle, agent_id, name, new_session_id, run_id, args.title or "")
    state_io.save_session(state_dir, handle, rec)
    if agent_id and agent_id != DEFAULT_AGENT_ID:
        state_io.save_last_used(state_dir, agent_id, name)

    print(f"handle={handle} session_id={new_session_id} run_id={run_id}")
    print(
        f"[Start] 已启动 handle={handle} session={new_session_id} run={run_id}（用 poll/wait 收回复）",
        file=sys.stderr,
    )
    return 0

def cmd_poll(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    if not args.handle:
        print("错误: poll 需要 --handle", file=sys.stderr)
        return 2
    mon_client = build_monitor_client()
    delta, status, full_len, tool_calls = _poll_once(
        state_dir, args.handle, mon_client, md_file=None, write_stdout=True
    )

    print(f"STATUS handle={args.handle} status={status} chars={full_len} delta={len(delta)}", file=sys.stderr)
    if status in ("failed", "interrupted"):
        return 1
    return 0

def cmd_wait(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    if not args.handle:
        print("错误: wait 需要 --handle", file=sys.stderr)
        return 2
    md_file, _ = _open_output(args)
    try:
        status, chars, tool_calls = _wait_blocking(
            state_dir, args.handle, md_file, timeout=args.timeout, poll_interval=_POLL_INTERVAL_SEC
        )
    finally:
        if md_file is not None:
            md_file.close()
    sys.stdout.write("\n")
    sys.stdout.flush()
    print(f"[Wait] 完成 status={status} chars={chars} tool_calls={len(tool_calls)}", file=sys.stderr)
    return 0 if status == "completed" else 1

def cmd_status(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    sessions = state_io.list_sessions(state_dir)
    if not sessions:
        print("(无会话)", file=sys.stderr)
        print(json.dumps({"sessions": [], "active": 0, "cap": state_io.max_concurrent()}, ensure_ascii=True))
        return 0
    active = sum(1 for s in sessions if s.get("status") in ("running", "streaming", "pending"))
    print(f"会话 {len(sessions)} 个（活跃 {active}/{state_io.max_concurrent()}）：", file=sys.stderr)
    for s in sessions:
        print(
            f"  [{s.get('handle')}] {s.get('name') or '(unnamed)'} {s.get('agent_id') or ''} "
            f"status={s.get('status')} chars={s.get('emitted_len', 0)} "
            f"session={s.get('session_id') or '(空)'} run={s.get('run_id') or '(空)'}",
            file=sys.stderr,
        )
    print(json.dumps({"sessions": sessions, "active": active, "cap": state_io.max_concurrent()}, ensure_ascii=True))
    return 0

def cmd_prune(args: argparse.Namespace) -> int:
    state_dir = _state_dir(args)
    state_io.migrate_legacy_state(state_dir)
    if args.handle:
        removed = state_io.delete_session(state_dir, args.handle)
        print(f"prune handle={args.handle}: {'已删除' if removed else '不存在'}", file=sys.stderr)
        return 0
    sessions = state_io.list_sessions(state_dir)
    terminal = {"completed", "failed", "interrupted", "timeout"}
    targets = [s for s in sessions if (args.all or s.get("status") in terminal)]
    removed_handles = []
    for s in targets:
        h = s.get("handle")
        if h and state_io.delete_session(state_dir, h):
            removed_handles.append(h)
    print(f"prune: 清理 {len(removed_handles)} 个会话 {removed_handles}", file=sys.stderr)
    print(json.dumps({"pruned": removed_handles}, ensure_ascii=True))
    return 0

_SUBCMDS = ("run", "start", "poll", "wait", "status", "prune")

def _add_state_dir_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--state-dir",
        default=None,
        help="状态目录（默认 $TCOP_SRE_STATE_DIR 或 ~/.local/state/tcop-sre-agents/）",
    )
    p.add_argument(
        "--state-file",
        default=None,
        help="(兼容旧) state.json 路径，取其 dirname 作为 state 目录",
    )

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Digital Twin Skill — 快照读对话（send 启动 run + 轮询 ListAIWorkbenchMessages 取回复）。"
        "无子命令时默认 run（单会话阻塞）。"
    )
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="单会话阻塞对话（= start --handle main + wait）")
    p_run.add_argument("--content", required=True, help="用户提问正文")
    p_run.add_argument("--agent-id", default="", help="agt-xxxxxxxx（不给则按 name/last_used/默认 解析）")
    p_run.add_argument("--name", default="", help="分身名（无 --agent-id 时按名解析）")
    p_run.add_argument("--session-id", default="", help="续聊 SessionID（不给则沿用 main handle）")
    p_run.add_argument("--output", "-o", default="", help="可选 md 归档路径")
    p_run.add_argument("--no-state-write", action="store_true", default=False, help="不写 last_used，结束后清理 main handle")
    p_run.add_argument("--use-default-agent", action="store_true", default=False, help="强制默认分身 agt-tmpl-default")
    p_run.add_argument("--poll-timeout", type=int, default=_POLL_TIMEOUT_SEC, help=f"轮询超时秒（默认 {_POLL_TIMEOUT_SEC}）")
    _add_state_dir_arg(p_run)
    p_run.set_defaults(func=cmd_run)

    p_start = sub.add_parser("start", help="非阻塞启动 run，立即返回 handle/session/run")
    p_start.add_argument("--content", required=True, help="用户提问正文")
    p_start.add_argument("--agent-id", default="", help="agt-xxxxxxxx")
    p_start.add_argument("--name", default="", help="分身名")
    p_start.add_argument("--handle", default="", help="指定 handle（已存在则续聊该会话；不给则自动 s1/s2...）")
    p_start.add_argument("--title", default="", help="会话标题（展示用）")
    p_start.add_argument("--force", action="store_true", default=False, help="超过并发上限时强制启动")
    _add_state_dir_arg(p_start)
    p_start.set_defaults(func=cmd_start)

    p_poll = sub.add_parser("poll", help="单次非阻塞轮询：输出新增 delta + STATUS 行")
    p_poll.add_argument("--handle", required=True, help="会话 handle")
    _add_state_dir_arg(p_poll)
    p_poll.set_defaults(func=cmd_poll)

    p_wait = sub.add_parser("wait", help="阻塞轮询 handle 到终态")
    p_wait.add_argument("--handle", required=True, help="会话 handle")
    p_wait.add_argument("--timeout", type=int, default=_POLL_TIMEOUT_SEC, help=f"超时秒（默认 {_POLL_TIMEOUT_SEC}）")
    p_wait.add_argument("--output", "-o", default="", help="可选 md 归档路径")
    _add_state_dir_arg(p_wait)
    p_wait.set_defaults(func=cmd_wait)

    p_status = sub.add_parser("status", help="列出所有会话状态")
    _add_state_dir_arg(p_status)
    p_status.set_defaults(func=cmd_status)

    p_prune = sub.add_parser("prune", help="清理已终态会话（--handle 指定 / --all 全清）")
    p_prune.add_argument("--handle", default="", help="只清理该 handle")
    p_prune.add_argument("--all", action="store_true", default=False, help="清理全部（含活跃）")
    _add_state_dir_arg(p_prune)
    p_prune.set_defaults(func=cmd_prune)

    argv = sys.argv[1:]
    if not argv or argv[0] not in _SUBCMDS:
        argv = ["run"] + argv
    return parser.parse_args(argv)

def main() -> None:
    args = _parse_args()
    if not getattr(args, "func", None):
        print("错误: 缺少子命令（run/start/poll/wait/status/prune）", file=sys.stderr)
        sys.exit(2)
    code = args.func(args)
    sys.exit(code)

if __name__ == "__main__":
    main()
