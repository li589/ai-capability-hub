# Task — tasks, tasklists and task attachments

Owns Lark Task: creating and updating tasks, completing/reopening them, parent-child (ancestor) links, comments, assignees and followers, reminders, listing "my tasks" and "tasks related to me", keyword search over tasks and tasklists, tasklist creation and membership, and uploading a local file as a task attachment. Does **not** own Minutes to-dos (a "todo" inside a meeting recording or 妙记 URL belongs to the minutes domain), calendar events, or resolving a person's name to an `open_id` (contact domain).

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+create` | `--summary` (required), `--description`, `--assignee`, `--follower`, `--due`, `--tasklist-id`, `--idempotency-key`, `--data` | Create a task; returns `guid` + `url` |
| `+update` | `--task-id`, `--summary`, `--description`, `--due`, `--data` | Patch task fields; returns `updated_fields` and per-task `confirmed` |
| `+set-ancestor` | `--task-id`, `--ancestor-id` (omit to detach) | Attach a task under a parent task, or make it independent |
| `+complete` | `--task-id` | Mark complete; returns `status`, `completed_at`, `already_completed` |
| `+reopen` | `--task-id` | Reopen a completed task |
| `+assign` | `--task-id`, `--add`, `--remove`, `--idempotency-key` | Add/remove assignees (comma-separated IDs) |
| `+followers` | `--task-id`, `--add`, `--remove`, `--idempotency-key` | Add/remove followers |
| `+comment` | `--task-id`, `--content` | Append a comment |
| `+reminder` | `--task-id`, `--set` (e.g. `15m`/`1h`/`1d`), `--remove` | Set relative reminders, or clear all of them |
| `+get-my-tasks` | `--query`, `--complete`, `--due-start`, `--due-end`, `--page-all`, `--page-limit`, `--page-token` | Tasks assigned to me (user identity only) |
| `+get-related-tasks` | `--include-complete`, `--created-by-me`, `--followed-by-me`, `--page-all`, `--page-limit`, `--page-token` | Tasks related to me: created by me / followed by me |
| `+search` | `--query`, `--creator`, `--assignee`, `--follower`, `--completed`, `--due`, `--page-all`, `--page-limit`, `--page-token` | Keyword + filter search over tasks |
| `+upload-attachment` | `--resource-id` (required), `--file` (required), `--resource-type`, `--user-id-type` | Upload one local file (<= 50 MB) as a task attachment |
| `+tasklist-create` | `--name`, `--member`, `--data` | Create a tasklist, optionally with editors and initial tasks |
| `+tasklist-search` | `--query`, `--creator`, `--create-time`, `--page-all`, `--page-limit`, `--page-token` | Search tasklists by keyword/creator/created-at range |
| `+tasklist-task-add` | `--tasklist-id`, `--task-id`, `--section-guid` | Put an existing task into a tasklist (optionally a section) |
| `+tasklist-members` | `--tasklist-id`, `--set`, `--add`, `--remove` | Manage tasklist members |

## Key parameters

**`--task-id` (and `--resource-id`)** — must be the Task OpenAPI **GUID**, or a Feishu task applink containing `guid=` (e.g. `https://applink.feishu.cn/client/todo/task?guid=<guid>`); the CLI extracts the query parameter itself. The client-facing display number (`t104121`, i.e. `suite_entity_num`) is rejected with `task display number "t104121" is not a Task OpenAPI GUID`. `--tasklist-id` accepts a tasklist GUID or a tasklist applink the same way.

**Time values (`--due`, `--due-start`, `--due-end`)** — accept ISO 8601, `YYYY-MM-DD`, relative offsets (`+2d`, `-1d`, `+3w`, `2h`) or a millisecond timestamp. A bare `YYYY-MM-DD` or a `+Nd` / `+Nw` offset is treated as **all-day** and snapped to start-of-day; other forms keep the exact instant. Range flags (`+search --due`, `+tasklist-search --create-time`) take a single `start,end` string, e.g. `--due "-1d,+7d"`; start must be `<=` end.

**`--assignee` / `--follower` / `--add` / `--remove` / `--member` / `--set`** — comma-separated ID lists. Use `ou_xxx` (`open_id`) for people and `cli_xxx` (app id) for applications; the CLI infers `type: app` from the `cli_` prefix and `type: user` otherwise. There is no flag to pass emails or names — resolve them through the contact domain first.

**`+get-my-tasks --complete` vs `+search --completed` vs `+get-related-tasks --include-complete`** — three different names for three different commands. `--complete=true` returns only completed tasks, `false` only incomplete, and omitting it returns both. `--include-complete` defaults to **true**; pass `--include-complete=false` for open items only.

**`+upload-attachment --resource-type`** — defaults to `task`. Use `task_delivery` when uploading on behalf of a task agent. `--file` takes exactly one regular file; directories and multi-file lists are rejected.

**`--data`** — raw JSON body merged first, then overridden by the explicit flags (`+create`, `+update`, `+tasklist-create`). Invalid JSON fails with `--data must be a valid JSON object`.

## Gotchas

- **Search vs list.** Only route to `+search` / `+tasklist-search` when the user actually supplies a keyword. Scope-only requests ("tasks I follow this year", "created by me") should use `+get-related-tasks`; "assigned to me" should use `+get-my-tasks`. Never pass a time phrase such as "since January" as `--query`.
- **`+search` has no implicit "me".** It does not rank results by relationship to the caller. To search tasks related to the current user you must resolve their `open_id` and pass `--assignee` / `--creator` / `--follower` explicitly.
- **`--query` or a filter is mandatory** for the search commands: with neither, the CLI errors with `query is empty and no filter is provided`.
- **`--created-by-me` / `--followed-by-me` filter client-side.** Pagination still walks upstream related-task pages, so a page can come back with fewer (or zero) rows while `has_more` is still true. Combine with `--page-all` when counting.
- **Reminders and repeat rules require `--due`.** A reminder or repeat rule cannot be set on a task with no due time. If both `start` and `due` exist, `start <= due`.
- **Mutually exclusive member flags.** `+tasklist-members` rejects `--set` combined with `--add`/`--remove`; `+reminder` rejects `--set` combined with `--remove`; `+assign` / `+followers` need at least one of `--add` / `--remove`. `+update` with no changed field fails with `no fields to update`.
- **Read commands are user-only.** `+search`, `+get-my-tasks`, `+get-related-tasks`, `+tasklist-search` declare `AuthTypes: user`. A bot token cannot see a user's task list — always pass `--as user`. Write shortcuts accept both identities, but a `tenant_access_token` (bot) cannot add cross-tenant task members.
- **Trust the write response.** `+update` returns `updated_fields` and `confirmed`; `+complete` returns `status` / `completed_at` / `already_completed`. Do not chain a `tasks get` just to re-verify what these fields already prove.
- **`--file` is cwd-relative only.** An absolute path fails with `unsafe file path`. Copy or write the file under the working directory first.
- **Rendering results.** Surface the returned `url` so the user can jump to the task; render member fields with real names (resolve via the contact domain) rather than raw `ou_` IDs, and format timestamps in local time.
- **There is no `+tasklist-list`, `+delete`, `+subtask-create` or `+section-*` shortcut.** Tasklist enumeration, deletion, subtasks, sections and custom fields go through the native API (`lark-cli schema task.tasklists.list`, then `lark-cli task tasklists list ...`).
- **No `+warm-token`.** It appears only in the CLI's test fixtures, not in the registered shortcut set.

## Permissions

| Command(s) | Scopes |
|---|---|
| `+create` `+update` `+set-ancestor` `+complete` `+reopen` `+assign` `+followers` `+tasklist-task-add` | `task:task:write` |
| `+comment` | `task:comment:write` |
| `+get-my-tasks` `+get-related-tasks` `+search` | `task:task:read` |
| `+tasklist-search` | `task:tasklist:read` |
| `+tasklist-members` | `task:tasklist:write` |
| `+tasklist-create` | `task:tasklist:write` + `task:task:write` |
| `+upload-attachment` | `task:attachment:write` |

Native-API extras: `task:section:read` / `task:section:write` for sections, `task:custom_field:read` / `task:custom_field:write` for custom fields and their options.

## Output, pagination and confirmation

Formats are selected with `--format json|pretty|table|ndjson|csv` only; there is no standalone `--table`, `--csv`, `--yaml` or `--raw` flag. Pagination is `--page-all` / `--page-limit` / `--page-delay`, with `--page-token` available per command (`--page-limit 0` means unbounded; `+search` caps auto-pagination at 40 pages). Success is `ok == true` (or exit code 0) — `code == 0` is not the contract. A high-risk write invoked without `--yes` exits with code **10** and `error.type == "confirmation"`; that is a prompt for the user, not a failure, and must never be auto-retried with `--yes` appended.

## Examples

```bash
# Create a task with an assignee and an all-day due date in 3 days
lark-cli task +create --as user --summary "Ship release notes" \
  --assignee ou_xxx --due "+3d" --idempotency-key rel-notes-2026-08 --format json

# Search open tasks assigned to two people, due within the next week
lark-cli task +search --as user --query "release" \
  --assignee "ou_xxx,ou_yyy" --completed=false --due "-1d,+7d" --format json

# My open tasks, all pages drained politely
lark-cli task +get-my-tasks --as user --complete=false \
  --page-all --page-limit 0 --page-delay 200 --format json

# Tasks I follow, including completed ones
lark-cli task +get-related-tasks --as user --followed-by-me --include-complete=true --page-all --format json

# Update a task from an applink, then comment on it
lark-cli task +update --as user \
  --task-id "https://applink.feishu.cn/client/todo/task?guid=<guid>" \
  --summary "Ship release notes (v2)" --due "2026-08-14" --format json
lark-cli task +comment --as user --task-id <guid> --content "Draft is in review"

# Reminder 1 hour before the due time, then clear all reminders
lark-cli task +reminder --as user --task-id <guid> --set 1h
lark-cli task +reminder --as user --task-id <guid> --remove

# Attach a local file (must be cwd-relative)
lark-cli task +upload-attachment --as user --resource-id <guid> --file ./report.pdf --format json

# Create a tasklist with editors, then move an existing task into it
lark-cli task +tasklist-create --as user --name "Q3 launch" --member "ou_xxx,ou_yyy" --format json
lark-cli task +tasklist-task-add --as user --tasklist-id <tasklist_guid> --task-id <guid>

# Complete a task (response already proves the new state)
lark-cli task +complete --as user --task-id <guid> --format json
```
