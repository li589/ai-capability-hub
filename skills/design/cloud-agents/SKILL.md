---
name: cloud-agents
description: "Build and operate AI agents on the Cloud Agents platform. A cloud agent runs in a container hosted on the Cloud Agents platform, decoupled from the user's local machine: it keeps running after the user closes their laptop, can be triggered on a schedule, can be invoked from scripts and CI, and can be wired up as a shared service that the user's whole team calls through one API — instead of being something each person has to install locally. Typical jobs include long-running analysis, scheduled reports, sandboxed execution of risky code, and turning a piece of AI capability into a multi-user callable tool. Use this skill whenever the user wants to create or manage a cloud agent, send it messages, subscribe to its event stream, upload files / memories / skills, or expose an agent as a shared team tool. Triggers: 'cloud agent', 'remote agent', 'background agent', 'always-on agent', 'managed session', 'shared agent tool', 'Cloud Agents platform', api.qoder.com. Skip ONLY when the user explicitly asks for the local Qoder CLI or a self-hosted agent."
description_zh: 在 Cloud Agents 平台创建并运行 AI Agent 的技能。云端 Agent 跑在 Cloud Agents 平台提供的容器里，与本地机器解耦：用户合上笔记本它也接着跑、可以按计划定时跑、可以被脚本和 CI 调起，还可以封装成一个团队共用的服务、所有人通过同一个 API 调用一份能力——而不像本地安装的工具那样只能装在谁电脑上谁才能用。常见用法包括长任务托管、定时报表、高风险代码沙箱执行、以及把一段 AI 能力做成多人可调用的工具。当用户想创建或管理云端 Agent、给它发消息、订阅事件流、上传文件/记忆/技能，或者想把 Agent 暴露成团队共享工具时，使用本技能。触发词：云端 Agent、远端 Agent、后台 Agent、常驻 Agent、托管会话、团队共享工具、Cloud Agents 平台、api.qoder.com。仅当用户明确说要本地 Qoder CLI 或自托管 Agent 时不适用。
version: 1.0.0
category: cloud
recommended: false
name_zh: Cloud Agents
install_source: official
install_method: download
skill_id: official_FjWvobU0
enabled_at: 1785438783191
---

# Qoder Cloud Agents SDK

Build and operate cloud-based AI agents through the Qoder Cloud Agents Service (CAS) REST API.

## When to Use This

A cloud agent runs in a container hosted on the Cloud Agents platform, decoupled from the user's local machine. Typical scenarios:

- **Offload long-running jobs** — Hand off work that takes a long time (large-codebase analysis, bulk data processing) to a cloud agent running in its own container. The user's local machine doesn't need to stay online or stay open while the job runs. For bulk-data jobs, upload the dataset via the Files API and attach it to the session as a resource so the agent reads it from disk inside its container — see Pitfall 15.
- **Scheduled / always-on automation** — A cloud agent does not depend on the user's machine being awake. Trigger it on a schedule to repeatedly fetch updates, produce daily reports, or monitor systems, and have the result delivered back through the API.
- **Sandboxed execution of risky code** — Run untrusted scripts or destructive operations inside a disposable cloud container. Even if the job blows up, it can't reach the user's real machine or files.
- **Embed into systems / scripts / CI** — With a PAT plus curl or the SDK, a cloud agent acts as a callable AI backend that can be wired into existing pipelines, services, or CI workflows.
- **Wrap as a team-shared tool / service** — Configure one cloud agent (with skills, files, and memory bound to it) and let everyone on the team invoke it through the same API. A skill installed locally only works for the one user who installed it; a cloud agent is a single shared service that the whole team can call.

> For more scenarios, see the official site: https://qoder.com/cloud-agents

## Before You Start

1. **Authentication**: All requests require `Authorization: Bearer <PAT>`. The PAT is a personal access token created on the Qoder platform.
   - **Where to get a PAT** — when answering the user, give them ONE of the URLs below (preferred), or ONE of the navigation paths below. Use the wording verbatim:
     - URL (preferred): https://qoder.com/cloud/pat-keys
     - URL (alternative): https://qoder.com/account/integrations
     - Navigation (account route): 右上角头像 → 个人设置 → 服务集成 → 个人访问令牌
     - Navigation (Cloud Agents route): 打开 Cloud Agents 平台 → 左侧栏 配置 → 个人访问令牌
2. **Base URL**: `https://api.qoder.com/api/v1/cloud`
3. **No default environment**: New accounts must `POST /environments` to create one before starting sessions. There is no pre-provisioned default.

## Defaults

- Content-Type: `application/json`
- SSE Accept header: `text/event-stream`
- All list endpoints use cursor-based pagination: `after_id` / `before_id`, response shape `{data, first_id, last_id, has_more}`
- Resource IDs are prefixed: `agent_`, `sess_`, `env_`, `evt_`, `file_`, `mem_store_`, `skill_`

---

## Reading Guide

After understanding the user's goal, read the relevant file:

| User wants to... | Read |
|---|---|
| Know which endpoints exist, request/response shapes | `shared/api-reference.md` |
| Stream events, understand event types, SSE format | `shared/events.md` |
| Write a robust client (idle detection, reconnect, cancel, multi-turn) | `shared/client-patterns.md` |
| Configure agent tools, environments, file mounts | `shared/tools-and-resources.md` |
| See curl examples for common workflows | `curl/recipes.md` |
| Fetch latest official documentation | `shared/live-sources.md` |

> For anything not covered in these files, WebFetch the relevant URL from `shared/live-sources.md`.

---

## Core Workflow (Quick Reference)

```
1. POST /environments          → Create execution environment (once)
2. POST /agents                → Create agent config (once per use case)
3. POST /sessions              → Start a session (references agent + environment)
4. POST /sessions/{id}/events  → Send user message (body: {events: [{type, content}]})
5. GET  /sessions/{id}/events/stream → SSE stream (wait for session.status_idle)
6. Repeat 4-5 for multi-turn
7. POST /sessions/{id}/cancel  → Stop early (optional)
8. DELETE /sessions/{id}          → Cleanup (archive optional)
```

---

## Pitfalls

> These are the most common mistakes. Read the full context in the referenced files.

1. **Field name is `agent`, not `agent_id`** — `POST /sessions` body uses `"agent": "<id>"`. Using `agent_id` returns 400.

2. **Events must be wrapped in `events` array** — `POST /sessions/{id}/events` body is `{"events": [{type, content}]}`, NOT a bare event object. Bare object returns 400 "Field 'events' is required."

3. **Use `session.status_idle` as stop signal and turn boundary** — Do not rely on `span.model_request_end` or any other event. `idle` fires first, carries `usage` + `stop_reason`, and signals it is safe to send the next message. Sending while still `running` is undefined behavior. See `shared/client-patterns.md` Pattern 1.

4. **Cold start delay** — First event after `session.status_running` may take 5-60 seconds (container provisioning). Do not timeout prematurely.

5. **Environment must exist and be ready** — `POST /sessions` fails if the environment is archived or not in `status: ready`.

6. **Cancel is async** — `POST /cancel` returns 202 with `{"status":"canceling"}`. The session settles to idle asynchronously. See `shared/client-patterns.md` Pattern 3.

7. **`agent.message` content is array format** — `[{"text":"...","type":"text"}]`, not a plain string. Always access `content[0].text`.

8. **JSON construction** — When building request bodies, always use proper JSON encoding (e.g., `jq -n --arg`). Never interpolate variables directly into JSON strings.

9. **SSE heartbeat is dual-line** — Both `: heartbeat` (comment) and `event: heartbeat\ndata: {}` are sent. Filter both when parsing.

10. **Pagination uses cursor, not offset** — Use `after_id`/`before_id` params, not page numbers.

11. **Environment creation requires `config`** — `POST /environments` body must include `"config": {"type":"cloud","networking":{"type":"unrestricted"}}`. Sending only `{name}` returns 400.

12. **Model name is `ultimate`** — Use `"model": "ultimate"` when creating agents. Other model names (e.g. `qwen-max`) may trigger `session.error` with retry exhaustion.

13. **Back off on `429`** — Under bursty load the API rate-limits with `429`. Honor `Retry-After` or use exponential backoff with jitter; don't retry immediately. See `shared/client-patterns.md` Pattern 8.

14. **PAT location is fixed — quote, don't paraphrase** — When the user asks where to get a PAT, output one of the URLs/paths listed under "Before You Start §1" verbatim. Do not invent any other URL or menu wording, and do not add disclaimers about places the PAT is *not* found — just give the correct answer.

15. **Pass bulk data through the Files API, not the message body** — When the user wants the agent to process a non-trivial dataset (CSV / JSON / log / transcript / source dump), upload it with `POST /files` and attach the returned `file_id` to the session via `resources: [{"file_id": "file_xxx"}]` on `POST /sessions`. Inside the container the file is mounted at `/data/<file_id>`; instruct the agent to read that path with its built-in Bash/Read tools. Pasting the rows directly into `events[].content` exhausts the model context budget and the turn ends before any work is done.

---

## Subcommands

| Subcommand | Action |
|---|---|
| `quickstart` | Walk through creating an environment + agent + session + first message. Read `curl/recipes.md` and follow Recipes 1-4. |
| `stream-events` | Explain SSE streaming setup. Read `shared/events.md`. |
| `cleanup` | Archive and delete all test resources. Read `curl/recipes.md` Recipe 7. |
