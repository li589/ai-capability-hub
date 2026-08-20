---
name: lark-unified
description: "Unified Lark/Feishu CLI suite covering messaging, documents,
  spreadsheets, base tables, calendar, mail, tasks, wiki, slides, meetings, OKR,
  approval, attendance and more. Wraps the official lark-cli (larksuite/cli)
  with 200+ commands across 18 business domains, a three-tier command model
  (shortcuts / API commands / raw API), and a non-TTY setup path for headless
  environments. Use when working with Lark/Feishu through the CLI: sending or
  searching messages, creating and editing docs and sheets, querying base
  records, managing calendar events and meetings, reading mail, managing tasks
  and wikis, handling approvals, or calling any Lark OpenAPI endpoint. Feishu
  Project (飞书项目 / Meegle) requests — 工作项, 需求, 缺陷, node/state transitions, MQL,
  WBS — route to a bundled on-demand sub-skill."
description_zh: 飞书/Lark 全能套件：消息、文档、表格、多维表格、日历、邮件、任务、Wiki、幻灯片、会议、OKR、审批等 18
  个业务域；飞书项目（Meegle）工作项按需转子技能
description_en: "Lark/Feishu unified CLI: messaging, docs, sheets, base,
  calendar, mail, tasks, wiki, slides & more; routes Feishu Project (Meegle) to
  an on-demand sub-skill"
version: 2.3.0
allowed-tools: Bash, Read
display_name: lark-unified
display_name_en: lark-unified
visibility: public
metadata:
  requires:
    bins:
      - lark-cli
  optionalBins:
    - meegle
  cliHelp: lark-cli --help
  alignedWith: larksuite/cli v1.0.82; larksuite/meegle-cli v1.0.19
disable-model-invocation: true
---

# Lark Unified

Wraps the official **`lark-cli`** (github.com/larksuite/cli, MIT) — 200+ commands over 18 Lark/Feishu business domains. This skill adds a non-TTY setup path and condenses the official 26-skill layout into one entry point.

It also routes to **飞书项目 / Meegle** (a separate product with a separate CLI) through an on-demand sub-skill. Read section 0 first to pick the right product.

## 0. Product routing — decide this before anything else

"Lark/Feishu" covers **two products that share nothing at runtime**: separate binaries, separate
authentication, separate credential stores. Picking the wrong one wastes an auth round-trip and, worse,
produces a confident answer about the wrong system.

| | Lark 协作 (this skill) | 飞书项目 / Meegle (sub-skill) |
|---|---|---|
| Binary | `lark-cli` | `meegle` |
| Install | required, always present | **on demand only** — see section 0.2 |
| Auth | `lark-cli auth login`, OAuth scopes | `meegle auth login`, device-code, no scope model |
| Credentials | `~/.lark-cli/`, OS keychain | `~/.meegle/`, OS keychain — **not shared** |
| Entry point | sections 1-8 below | [skills/meegle/SKILL.md](skills/meegle/SKILL.md) |

### 0.1 Routing signals

Route on **signal words first**, and only then on the command surface.

**→ Feishu Project / Meegle (load the sub-skill):** 飞书项目 · Meegle · Meego · 工作项· 需求单·
缺陷 · Bug 单 · 迭代 · 排期 · 工时 · 节点流转 · 状态流转 · MQL · 空间 (project space) ·
`project_key` · 计划表 / WBS · 度量图表 · 资源库 · 交付物 · a `project.feishu.cn` or `meegle.com` URL.

**→ Lark collaboration (stay here):** 消息 / 群 · 文档 / docx · 表格 / sheet · 多维表格 / Base ·
日历 · 邮件 · Wiki · 云盘 / Drive · 妙记 · 会议 · OKR · 审批 · 打卡 · 通讯录.

### 0.2 Word collisions — read this, do not guess

Several everyday words map to **both** products with completely different meanings. Getting these wrong
is the single most likely routing failure.

| Word | Lark collaboration |飞书项目 / Meegle | How to tell |
|---|---|---|---|
| **任务 / task** | Lark Task — a personal to-do item (`lark-cli task +create`) | a work-item **type** (`task`) inside a project space, alongside 需求 / 缺陷 | Mentions a 空间 / 项目 / 迭代 / work-item ID → Meegle. A standalone personal reminder → Lark Task. |
| **待办 / todo** | `lark-cli task +get-my-tasks` | `meegle mywork todo` | "我的飞书待办" → Lark Task. "飞书项目里我的待办" / mentions 空间 → Meegle. |
| **项目 / project** | usually loose wording for "a piece of work" | a **space** (`project_key`), a first-class entity | "项目空间" / "哪个项目下" → Meegle. |
| **评论 / comment** | doc, sheet and Drive comments | comments on a work item | Target is a doc/file → Lark. Target is a work item → Meegle. |
| **视图 / view** | Base view (`lark-cli base +view-list`) | Meegle view (`meegle view get`) | Mentions Base / 多维表格 / `app_token` → Lark. Mentions 空间 / 工作项 → Meegle. |
| **状态 / 流转** | n/a | node flow / state flow transitions | Any流转 wording → Meegle. |
| **排期 / 工时** | calendar events | `workhour list-schedule`, node schedules | 排期 of people or work items → Meegle. A meeting on a calendar → Lark. |

**When the signal is genuinely ambiguous, ask.** One clarifying question costs far less than authorizing
the wrong product. Do not "try both".

> This table and the domain table in section 5 are exhaustive for **Lark collaboration only**. If a
> request does not fit any Lark domain in section 5, do not force the closest-looking match — re-check
> section 0.1 and consider that it belongs to the Meegle sub-skill.

### 0.3 Loading the Meegle sub-skill

The `meegle` binary is **not** part of the default setup and must not be installed pre-emptively. Install
it only when the user has clearly asked for Feishu Project work.

```bash
# 1. Preflight -- installed? authenticated? one call, JSON + exit code
STATUS=$(find ~/.workbuddy/skills ./.workbuddy/skills -name meegle_status.py 2>/dev/null | head -1)
python3 "$STATUS"; echo "exit=$?"
```

| Exit | State | What to do |
|---|---|---|
| 0 | ready | Read the sub-skill and proceed |
| 3 | not installed | Install (step 2 below), then re-check |
| 4 | installed, not logged in | Run the device-code flow in the sub-skill's `auth-guard.md` |
| 5 | unparseable | Inspect `meegle auth status --format json` by hand |

Why a script rather than probing with a business command: Meegle registers its business commands **only
after login**, so an unauthenticated CLI answers `unknown command "workitem" for "meegle"` — byte-for-byte
identical to a genuinely nonexistent command. Only `auth status` distinguishes the two.

```bash
# 2. Install the binary ONLY -- both flags matter
npx -y @lark-project/meegle@latest install --no-skills --no-auth --host <host> --lang zh
```

- `--no-skills` — **required.** Without it the official wizard runs `skills add` and installs its own
  copy of the meegle skill into the agent's global skill directory, producing a duplicate that competes
  with the sub-skill bundled here.
- `--no-auth` — keeps installation and login separate, so the login step can follow the split
  device-code flow instead of blocking on a browser.
- **Requires Node.js 18+** (for `npx`). If `node --version` fails or reports < 18, stop and tell the
  user to install Node first — do not attempt a workaround.
- The wizard runs `npm install -g @lark-project/meegle`. **Tell the user before running it** and get
  their agreement: it writes to the global npm prefix, which is a change outside this workspace.
- `<host>` is `project.feishu.cn` (飞书项目) or `meegle.com` (Meegle international). If the user has not
  said which, ask — a wrong host means authorizing against the wrong tenant.

```bash
# 3. Hand off. Read the sub-skill before issuing any meegle business command.
```

Then read [skills/meegle/SKILL.md](skills/meegle/SKILL.md) and follow it. Login uses the CLI's **split
device-code flow**, wrapped by `scripts/meegle_setup.py`:

```bash
SETUP=$(find ~/.workbuddy/skills ./.workbuddy/skills -name meegle_setup.py 2>/dev/null | head -1)
python3 "$SETUP" --host <host> --print-url-only                  # turn 1: show URL, then END THE TURN
python3 "$SETUP" --resume --device-code <dc> --client-id <cid># turn 2: exchange for a token
```

Exit codes on `--resume`: **0** authenticated · **2** pending, poll again · **4** device code expired or
denied. Bare `meegle auth login` needs a TTY and fails here with `INTERACTIVE_BROWSER_REQUIRED`. The
sub-skill's auth section is adapted for this environment — see
[skills/meegle/NOTICE.md](skills/meegle/NOTICE.md) for exactly what was changed relative to upstream.

**Never mix the two CLIs in one pipeline.** IDs are not portable: a Meegle `work_item_id` means nothing
to `lark-cli`, and a Lark `open_id` is not a Meegle `user_key`. To cross products, resolve the identity
explicitly on each side (`lark-cli contact +search-user` ↔ `meegle user search`).

## 1. Preflight — run this first, every time

> Section 0 comes first. This preflight covers **`lark-cli` only** — it says nothing about whether the
> `meegle` binary exists or is authorized. For a Feishu Project request, run the Meegle check in
> [section 0.3](#03-loading-the-meegle-sub-skill) instead.

Do **not** guess whether Lark is configured. Run the status script; it prints JSON and sets an exit code.

```bash
# Works whether the skill is installed user-level or project-level
STATUS=$(find ~/.workbuddy/skills ./.workbuddy/skills -name lark_status.py 2>/dev/null | head -1)
python3 "$STATUS" --json; echo "exit=$?"
```

| Exit | State | What to do |
|---|---|---|
| 0 | configured | Proceed. If `userLoggedIn:false`, only `--as bot` work is possible. |
| 3 | not installed | `npx -y @larksuite/cli@latest install` (takes several minutes) |
| 4 | not configured | Local workspace → run `lark_setup.py`. Agent workspace → `lark-cli config bind` |
| 5 | unparseable | Inspect `lark-cli config show` manually |

For a fuller picture — version, config file, bot/user identity, endpoint reachability — run the CLI's own
health check. It always exits 0, so read the `ok` field and per-check `status` (`pass` / `warn` / `fail`):

```bash
lark-cli doctor
```

> **Why a script and not a grep?** `lark-cli config show` emits **`appId`** (camelCase). Matching on `app_id` never succeeds, which silently reports "not configured" and re-triggers authorization on every run. The script parses JSON and accepts both spellings. Never reintroduce a `grep "app_id"` check.

**Before you trigger any authorization prompt**, work out which scopes the task actually needs and check
whether they are already granted. Asking for a whole domain because it is convenient pushes the user into
an admin approval queue for permissions the task never uses. See
[Request the fewest scopes that do the job](#request-the-fewest-scopes-that-do-the-job).

## 2. Setup rules

**Never run these — they need a TTY and render a broken QR code here:**

- `lark-cli config init` (bare/interactive)
- `lark-cli config init --new`
- any interactive `lark-cli config bind` with no flags

**Local workspace — use the setup script (device flow, no TTY):**

```bash
SETUP=$(find ~/.workbuddy/skills ./.workbuddy/skills -name lark_setup.py 2>/dev/null | head -1)

python3 "$SETUP"                  # feishu, opens browser
python3 "$SETUP" --brand lark     # Lark international
python3 "$SETUP" --no-browser  # print URL instead of opening
python3 "$SETUP" --force          # re-register even if already configured
```

The script is idempotent: if `appId` already exists it exits 0 immediately and does **not** re-authorize.

**Preferred agent pattern — split flow.** Never show a URL and then block polling in the same turn; in harnesses that hide intermediate output the user never sees the link.

```bash
# Turn 1 — get the URL, then END THE TURN and wait for the user
python3 "$SETUP" --print-url-only
# -> {"verification_url": "...", "device_code": "...", "resume_command": "..."}

# Turn 2 — after the user says they authorized, YOU run this (not the user)
python3 "$SETUP" --device-code <device_code>
```

Optionally render a QR code alongside the URL. `--output` only accepts a **relative** path:

```bash
lark-cli auth qrcode "<verification_url>" --output lark-qr.png   # PNG (preferred)
lark-cli auth qrcode "<verification_url>" --ascii                #ASCII, only if asked
```

Treat the URL as an opaque string — no re-encoding, no reassembling query params.

**Agent workspace (OpenClaw / Hermes / Lark Channel).** When `OPENCLAW_HOME`, `HERMES_HOME`, or `LARK_CHANNEL` is set, `config init` refuses by design — the host already provisioned an app. Bind instead, and **confirm the identity preset with the user first**:

```bash
lark-cli config bind --identity bot-only      # safer: no impersonation
lark-cli config bind --identity user-default  # needed for personal calendar/mail/drive
```

To change identity policy on the *same* app, use `lark-cli config strict-mode` — no re-bind needed.

**Manual path**, if you already hold credentials:

```bash
echo "<APP_SECRET>" | lark-cli config init --app-id <APP_ID> --app-secret-stdin --brand feishu
```

Multiple apps are supported as named profiles: `lark-cli profile list | add | use <name> | rename | remove`
(`use -` toggles back). Per-command override: `--profile <name>`.

Config lives at `~/.lark-cli/config.json` (override with `LARKSUITE_CLI_CONFIG_DIR`); agent workspaces nest under `~/.lark-cli/openclaw/` or `~/.lark-cli/hermes/`. Secrets go to the OS keychain, not the JSON.

## 3. Authentication

```bash
lark-cli auth status --json --verify        # who am I, is the token valid
lark-cli whoami                             # effective identity, short form
lark-cli auth check --scope "<scope>"       # exit 0 = present, 1 = missing
lark-cli auth scopes                        # scopes this app already holds
lark-cli auth list                          # all authenticated users
lark-cli auth login --device-code <code>    # finish a split-flow login
lark-cli auth logout --json                 # clears LOCAL session only
```

`auth login` **requires** a scope selector (`--domain`, `--scope`, or `--recommend`). Scopes accumulate across logins, so you can start with three and add more later — nothing already granted is lost.

Read `identity`, `verified`, `identities.user.status`, `identities.user.userName`, `identities.user.tokenStatus` from `auth status`.

### Request the fewest scopes that do the job

Every scope on the consent screen is one more thing the user has to approve, and in many tenants an
unapproved scope lands in an admin review queue (`待发布` in the console). `--domain base` asks for
**40** base scopes — create, update, delete, roles, workflows, advanced permissions — when reading one
table needs **three**. That turns a five-second read into an approval ticket.

So the default is `--scope`, naming exactly what the command needs:

```bash
# Read records from a Base -- this is the entire scope set
lark-cli auth login --scope "base:record:read base:table:read base:field:read" --no-wait --json
```

One `--scope` string, space- or comma-separated. A misspelled scope is rejected server-side with
`error.type: "authentication"`, so typos fail loudly instead of silently granting nothing.

**Find the scopes before asking for anything:**

1. Each domain reference has a `## Permissions` table mapping shortcut → exact scopes. For example
   [lark-base.md](references/lark-base.md) lists `+record-list` as `base:record:read`.
2. For native API commands, `lark-cli schema <service>.<resource>.<method>` returns `_meta.scopes`.
   This does **not** cover base — `schema base.*` fails with `Unknown service: base`, since the base
   shortcuts are not in the schema registry. Use the reference table there.
3. If a call still fails, the error carries `missing_scopes`. Request exactly those and nothing else.

**Widening, in increasing order of cost:**

```bash
# 1. Precise -- the default, and what the official lark-shared skill recommends
lark-cli auth login --scope "base:record:read base:table:read base:field:read" --no-wait --json

# 2. A whole domain minus the destructive parts
lark-cli auth login --domain base \
  --exclude "base:record:delete,base:table:delete,base:field:delete,base:role:delete" \
  --no-wait --json
```

`--exclude` subtracts from `--domain`; both combine additively with `--scope`.

**`--recommend` is not a minimal option — it is one of the broadest.** The official README describes it
as "recommended auto-approval scopes", which reads like a small safe subset. It is not. The CLI's embedded
scope catalogue marks **310** scopes as `recommend: true`, spanning `im` (51), `base` (43), `directory`
(33), `docs` (31), plus `approval`, `calendar`, `contact`, `minutes` and more — including **13 delete
scopes** (`base:record:delete`, `base:role:delete`, `base:workflow:delete`, `im:chat:delete`,
`space:document:delete`, …). It therefore requests *more* than `--domain base`, not less. Reasonable for a
long-lived personal setup where the user knowingly authorizes broadly; wrong for "read one table".

**`--domain all` is a last resort, never a starting point.** It requests scopes across all 23 domains —
mail, calendar, attendance, approval, contact — for a task that touches one. Use it only when the user
explicitly asks to authorize everything up front, and never as a reaction to a `missing_scope` error.

### Minimum scopes for common tasks

| Task | Scopes to request |
|---|---|
| Read Base records / tables | `base:record:read base:table:read base:field:read` |
| Read a Base including view config | add `base:view:read` |
| Write Base records | add `base:record:create base:record:update` |
| Read a docx | `docx:document:readonly` |
| Create a docx | `docx:document:create` |
| Read a spreadsheet range | `sheets:spreadsheet:read` |
| Write spreadsheet cells | `sheets:spreadsheet:write_only` |
| Today's calendar | `calendar:calendar.event:read` |
| Create a calendar event | `calendar:calendar.event:create calendar:calendar.event:update` |
| Read chat messages | `im:message:readonly im:chat:read` |
| Send a message as the user | `im:message.send_as_user im:message` |
| Read mail | `mail:user_mailbox.message:readonly` + address / subject / body read scopes |
| List or read wiki nodes | `wiki:node:retrieve` |
| Read my tasks | `task:task:read` |
| Look up a colleague | `contact:user:search` — **user identity only**, `--as bot` is rejected with exit 2 |
| Search docs by keyword | `search:docs:read` |
| Download a Drive file | `drive:file:download drive:drive.metadata:readonly` |

Resolving a Base or doc from a **wiki** URL additionally needs `wiki:node:read` / `wiki:node:retrieve`.
Downloading a Base attachment additionally needs `docs:document.media:download`.

### Check before re-authorizing

`auth check` says whether the token already covers a scope, so you avoid a redundant consent screen.
It exits **1** when something is missing and prints `{"ok":false,"missing":[...]}`; an
`{"error":"not_logged_in"}` body means there is no user session at all. **Capture the exit code on the
same line** — piping into `head` or `jq` overwrites `$?` with the pipeline's status:

```bash
OUT=$(lark-cli auth check --scope "base:record:read base:table:read base:field:read" --json); RC=$?
# RC=0 -> already granted, just run the command
# RC=1 -> read OUT.missing and request only those
```

`auth scopes` shows what the app currently holds under `userScopes`; a freshly registered app holds
only `offline_access`.

### Where this differs from the official README

The official README's Quick Start opens with `lark-cli auth login --recommend`, and the official
`lark-shared` skill puts "获取全部权限 → `--domain all`" at the top of its auth lookup table. Both are
optimized for one-time broad setup, not for a single task.

The least-privilege guidance above is **not** a departure from official intent — `lark-shared` states it
directly:

> `lark-cli auth login --scope "<missing_scope>"   # 按具体 scope 授权（推荐，符合最小权限原则）`

and the upstream design follows the same principle: each shortcut declares "the narrowest scope the
upstream API accepts", and `internal/auth/scope.go` `MissingScopes` does **exact-string** matching, so a
broader scope form does not satisfy a narrower requirement. Declaring or requesting wide does not help.

What this skill changes is only the **default ordering**: `--scope` first, `--domain` when a task genuinely
spans a domain, `--recommend` / `--domain all` only on explicit user request.

### Identity: bot vs user

| Identity | Flag | Token | Reach |
|---|---|---|---|
| Bot | `--as bot` | `tenant_access_token` | App-level. Only needs console scopes — **no `auth login`**. Cannot see the user's calendar, mail, or drive. |
| User | `--as user` | `user_access_token` | The user's own resources. Needs console scopes **and** `auth login`. |

`--as` accepts `user`, `bot`, `auto`. Resolution is `--as` flag → `config default-as` → `auto`. Because it is not hard-wired to bot, **pass `--as` explicitly** whenever identity matters.

The classic failure: `--as bot` returns an empty agenda because the bot is reading *its own* empty calendar. Personal resources need `--as user`.

### Missing permissions

Errors carry `missing_scopes`, `console_url`, and `hint`.

- **Bot** → pass `console_url` to the user verbatim so they enable the scope in the developer console. **Never** run `auth login` for a bot.
- **User** → request **exactly** the scopes in `missing_scopes`, nothing more:

  ```bash
  lark-cli auth login --scope "<scope_1> <scope_2>" --no-wait --json
  ```

  Do not respond to a missing scope by widening to `--domain <name>` or `--domain all`. Scopes accumulate,
  so a second precise login later costs the user one more consent tap — while an over-broad first request
  can cost them an admin approval cycle.

`auth logout` only clears the local session. Revoking server-side authorization, or a single granted scope, must be done by the user in Lark's authorization-management page.

## 4. Command model

Three tiers, in order of preference:

```bash
# Tier 1— shortcuts (prefer these): smart defaults, table output, --dry-run
lark-cli im +messages-send --chat-id oc_xxx --text "Hello"

# Tier 2 — generated API commands, 1:1 with OpenAPI endpoints
lark-cli calendar calendars list
lark-cli calendar events instance_view --params '{"calendar_id":"primary","start_time":"1700000000","end_time":"1700086400"}'

# Tier 3 — raw API, covers 2500+ endpoints
lark-cli api GET /open-apis/calendar/v4/calendars
lark-cli api POST /open-apis/im/v1/messages --params '{"receive_id_type":"chat_id"}' --data '{...}'
```

Inspect before calling a raw endpoint:

```bash
lark-cli schema                        # list everything
lark-cli schema im.chats.create        # one method (dotted form)
lark-cli schema im chats create        # same thing, space-separated
lark-cli <domain> --help               # per-domain command list
```

A `schema` result has five top-level keys: `name`, `description`, `inputSchema`, `outputSchema`, `_meta`.
Two things matter in practice:

- The **identity constraint is appended to `description`**, not a separate field — e.g.
  `创建群。Identity: bot only (tenant_access_token)`.
- **`_meta` holds what you need before calling**: `scopes`, `access_tokens`, `risk`
  (`read` / `write` / `high-risk-write`), a separate `danger` boolean, and `doc_url`.

`lark-cli <domain> --help` is the primary command list but **not guaranteed complete** — a few shortcuts are
registered hidden yet remain callable (e.g. `vc +notes`). If a name from these references is missing from
`--help`, try `lark-cli <domain> <shortcut> --help` before concluding it does not exist.

For the full mechanics of tiers 2 and 3 — typed-command discovery, `schema` output shape, `api` usage,
the complete flag table, and envelope/exit-code handling — see
[references/api_reference.md](references/api_reference.md).

### Flags that actually exist

Output format is a **single `--format` flag**. `--table`, `--csv`, `--yaml`, `--raw` do **not** exist — the old
skill listed all four and every one of them fails.

```bash
--format json     # default; --json is shorthand for this
--format table
--format ndjson   # for piping
--format csv
--format pretty   # shortcuts only -- NOT accepted by `lark-cli api`
```

Pagination: `--page-all`, `--page-limit N`, `--page-delay MS` (default 200ms). `--page-limit` defaults to 10,
but its valid range differs by tier — on shortcuts it must be **1-1000** (`--page-limit 0` is a validation
error), while on `lark-cli api` **0 means unlimited**. Individual commands also accept `--page-size` and
`--page-token`.

Other flags on a typical shortcut: `--as`, `--dry-run`, `--jq`, `--json`, `--yes` (confirm high-risk writes),
`--output`, `--params` / `--data` (JSON payloads), `--profile`.

Quiet JSON for scripts:

```bash
LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1 LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1 lark-cli auth status --json
```

### JSON contract — check `ok`, never `code`

Success → stdout, exit 0:

```json
{ "ok": true, "identity": "user", "data": { ... }, "meta": { "count": 1 } }
```

Error → stderr, non-zero exit:

```json
{ "ok": false, "identity": "user", "error": { "type": "authorization", "subtype": "missing_scope", "code": 99991679, "message": "...", "hint": "...", "missing_scopes": ["..."] } }
```

Test `ok == true` or the exit code. There is **no top-level `code` on success** — `code` only exists inside the error envelope and holds the upstream OpenAPI number. Judging by the legacy `{"code":0}` shape marks every success as a failure, which is dangerous around writes: a misread on `task +create` can bypass idempotency and duplicate records.

### Exit code 10 — approval gate

High-risk writes without `--yes` exit **10** with `error.type: "confirmation"`. This is not a failure. Show the
user the pending action, get explicit confirmation, then re-run with `--yes`. Never silently append `--yes`
and retry on your own.

**Identity is checked before the confirmation gate.** A high-risk command with the wrong identity exits **2**
(`resolved identity "bot" ... only supports: user`) and never reaches the gate — so exit 2 does *not* mean the
command is safe. Fix identity first, then expect 10:

```bash
lark-cli apps +openapi-key-delete --app-id <id> --key-id <k>             # exit 2  (identity)
lark-cli apps +openapi-key-delete --app-id <id> --key-id <k> --as user   # exit 10 (needs --yes)
```

### Hard rules

- **Relative paths only.** `--file`, `--output`, `--output-dir`, `@file` reject absolute paths, e.g.
  `unsafe output path: --output must be a relative path within the current directory`. Some of these flags
  accept `-` to read an out-of-tree file from stdin; pipe large payloads that way.
- Never print `appSecret` or access tokens.
- Confirm intent before writes and deletes; preview with `--dry-run`.
- Ignore `_notice.update` in output unless the user asked about versions. Update with `lark-cli update` (refreshes CLI *and* skills).

## 5. Domains

`lark-cli --help` lists 23 domains. The 18 you will actually reach for are below; shortcut names come from the CLI's own command registry — verify with
`lark-cli <domain> --help` before improvising.

> Domain name vs reference filename: the CLI invocation is **`lark-cli docs`** (plural), even though the
> reference file is named `lark-doc.md` after the official skill folder. Same for `vc`, `note`, `apps`.

| Domain | What it does | Representative shortcuts | Reference |
|---|---|---|---|
| **im** | Messages, group chats, search, files, reactions, cards, Feed pins | `+messages-send` `+messages-reply` `+messages-search` `+messages-mget` `+messages-resources-download` `+chat-list` `+chat-create` `+chat-search` `+chat-update` `+chat-members-list` `+chat-messages-list` `+threads-messages-list` `+flag-create` `+feed-shortcut-create` | [lark-im.md](references/lark-im.md) |
| **docs** | Docx create/read/update, media, history, search | `+create` `+fetch` `+update` `+search` `+media-insert` `+media-upload` `+media-download` `+media-preview` `+resource-download` `+resource-update` `+history-list` `+history-revert` | [lark-doc.md](references/lark-doc.md) |
| **drive** | Files, folders, permissions, comments, versions, sync | `+upload` `+download` `+inspect` `+search` `+create-folder` `+move` `+delete` `+import` `+export` `+export-download` `+preview` `+list-comments` `+add-comment` `+member-add` `+member-list` `+version-history` `+permission-get-setting` `+status` `+pull` `+push` `+sync` | [lark-drive.md](references/lark-drive.md) |
| **sheets** | Spreadsheet read/write, styles, charts, pivots, filters | `+workbook-create` `+workbook-info` `+workbook-export` `+sheet-create` `+sheet-copy` `+sheet-info` `+csv-get` `+cells-get` `+cells-set` `+cells-search` `+cells-replace` `+cells-clear` `+range-sort` `+chart-create` `+pivot-create` `+filter-create` `+csv-put` | [lark-sheets.md](references/lark-sheets.md) |
| **base** | Multi-dimensional tables: records, fields, views, dashboards, roles | `+url-resolve` `+base-create` `+base-get` `+table-list` `+record-list` `+record-search` `+record-get` `+record-batch-create` `+record-batch-update` `+record-delete` `+record-upsert` `+field-list` `+field-create` `+data-query` `+view-list` `+view-set-filter` `+dashboard-list` `+role-create` | [lark-base.md](references/lark-base.md) |
| **calendar** | Events, agenda, free/busy, meeting rooms, RSVP | `+agenda` `+create` `+update` `+get` `+search-event` `+freebusy` `+suggestion` `+room-find` `+rsvp` `+meeting` | [lark-calendar.md](references/lark-calendar.md) |
| **task** | Tasks, tasklists, subtasks, reminders, assignees | `+create` `+update` `+get-my-tasks` `+get-related-tasks` `+search` `+complete` `+reopen` `+assign` `+comment` `+reminder` `+followers` `+set-ancestor` `+tasklist-create` `+tasklist-search` `+tasklist-members` `+tasklist-task-add` `+upload-attachment` | [lark-task.md](references/lark-task.md) |
| **mail** | Read, search, send, reply, forward, drafts, templates, watch | `+messages` `+message` `+send` `+reply` `+reply-all` `+forward` `+draft-create` `+draft-edit` `+draft-send` `+message-trash` `+message-modify` `+thread` `+triage` `+watch` `+signature` `+share-to-chat` `+lint-html` | [lark-mail.md](references/lark-mail.md) |
| **wiki** | Knowledge spaces, node trees, members | `+space-list` `+space-create` `+delete-space` `+node-list` `+node-get` `+node-create` `+node-copy` `+node-delete` `+move` `+move-to-drive` `+member-add` `+member-list` `+member-remove` | [lark-wiki.md](references/lark-wiki.md) |
| **contact** | User and bot lookup | `+search-user` `+get-user` `+search-bot` | [lark-contact.md](references/lark-contact.md) |
| **slides** | Presentations, slide pages, screenshots | `+create` `+add-slide` `+delete-slide` `+replace-slide` `+replace-pages` `+xml-get` `+screenshot` `+media-upload` `+history-list` | [other-domains.md](references/other-domains.md) |
| **markdown** | Native Markdown files in Drive | `+create` `+fetch` `+patch` `+overwrite` `+diff` | [other-domains.md](references/other-domains.md) |
| **vc** | Meetings, recordings, notes, live meeting control | `+search` `+detail` `+recording` `+notes`† `+meeting-events` `+meeting-join` `+meeting-leave` `+meeting-list-active` `+meeting-message-send` | [other-domains.md](references/other-domains.md) |
| **minutes** | Minutes metadata, AI summaries, todos, media | `+search` `+detail` `+summary` `+todo` `+download` `+upload` `+update` `+speaker-replace` `+word-replace` `+apply-permission` | [other-domains.md](references/other-domains.md) |
| **okr** | Objectives, key results, cycles, progress | `+create` `+batch-create` `+patch` `+cycle-list` `+cycle-detail` `+progress-create` `+progress-list` `+progress-update` `+indicator-update` `+weight` `+reorder` `+upload-image` | [other-domains.md](references/other-domains.md) |
| **approval** | Approval tasks, instances, definitions | *No shortcuts.* `approval tasks query` `approval tasks approve` `approval instances create` `approval approvals search` `approval approvals get` | [other-domains.md](references/other-domains.md) |
| **attendance** | Personal punch records | *No shortcuts.* `lark-cli attendance --help`, `lark-cli schema attendance.<resource>.<method>` | [other-domains.md](references/other-domains.md) |
| **apps** | Miaoda/Spark app dev, hosting, DB, logs, releases | `+init` `+create` `+list` `+get` `+update` `+release-create` `+db-execute` `+db-table-list` `+env-set` `+env-list` `+file-upload` `+log-list` `+trace-list` `+html-publish` `+automation-list` `+role-list` | [other-domains.md](references/other-domains.md) |

Also available: **contact** (`+search-user` `+get-user` `+search-bot` — see [lark-contact.md](references/lark-contact.md)), **event** (WebSocket subscriptions: `event list`, `event consume <event_key>`, `event status`, `event stop`), **whiteboard** (`+update` `+export`, plus hidden `+query`†), **note** (`+detail` `+transcript`), **mindnotes** (mind-note nodes), **application** (self-management for the bound app), **approval**, **attendance**.

> † Registered as hidden: absent from `--help` but callable (`vc +notes`, `whiteboard +query`).
>
> Shortcut names are checked against the CLI's own registry — a wrong name is rejected outright. These do **not** exist despite looking plausible: `+cells-read`, `+cells-find`, `+sheet-list`, `+workbook-list`, `+workbook-get`, `+get-range`, `+range-get`. Use `+csv-get` / `+cells-get`, `+cells-search`, and `+workbook-info` (which also lists child sheets). When unsure, run `lark-cli <domain> --help`.

**This table does not contain 飞书项目 / Meegle.** Work items, node/state transitions, MQL, project
spaces, WBS plans and workhour scheduling are a different product with a different binary — go to
[section 0](#0-product-routing-decide-this-before-anything-else) and load the sub-skill. Do not
substitute `lark-cli task` or `lark-cli approval` for a Meegle request just because they are the nearest
row here.

## 6. Worked examples

```bash
# Send a message
lark-cli im +chat-search --keyword "engineering"
lark-cli im +messages-send --chat-id oc_xxx --text "Hello team" --as bot

# Preview a risky write first
lark-cli im +messages-send --chat-id oc_xxx --text "test" --dry-run

# Today's agenda (personal resource -> must be user identity)
lark-cli calendar +agenda --as user

# Create a doc from markdown
lark-cli docs +create --doc-format markdown \
  --content $'<title>Weekly Report</title>\n  # Progress\n- Shipped X'

# Inspect a workbook (this also lists child sheets), then read a range.
# Quote A1 references -- an unquoted '!' triggers bash history expansion.
lark-cli sheets +workbook-info --spreadsheet-token <token> --as user
lark-cli sheets +csv-get --spreadsheet-token <token> --range 'Sheet1!A1:D20' --as user

# Query base records with pagination
lark-cli base +record-list --app-token <app_token> --table-id tbl_xxx --page-all --page-limit 5

# All chats as a table
lark-cli im +chat-list --as user --format table
```

## 7. Entity IDs

`open_id` (ou_), `user_id`, `union_id`, `email` · chat `oc_` · message `om_` · `document_id` / `doc_token` · `file_token` / `file_key` · base `app_token` + `tbl_` · `spreadsheet_token` · wiki `space_id` + `node_token` · `calendar_id` (`primary` for self) + `event_id` · `task_guid` · `note_id`

Tokens are not interchangeable across domains. A wiki node wrapping a doc needs `wiki +node-get` to resolve the underlying `doc_token` first.

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Consent screen asks for dozens of scopes / admin approval needed for a simple read | `--domain <name>` or `--domain all` used instead of `--scope` | Request the exact scopes from the domain reference's Permissions table; `--domain base` is 40 scopes, reading a table is 3 |
| Setup re-runs authorization every time | `grep "app_id"` against camelCase `appId` output | Use `lark_status.py` / `lark_setup.py`; never grep `app_id` |
| `not configured` in an agent workspace | Host app not bound | `lark-cli config bind --identity bot-only` |
| `config init` refuses | Agent workspace guard | Use `config bind`, or `--force-init` only if the user truly wants a second app |
| Empty agenda / empty drive | Bot reading its own resources | Re-run with `--as user` |
| `missing_scope` on bot | Console scope not enabled | Send `console_url` to the user; do not `auth login` |
| `unsafe file path` | Absolute path passed | Use a relative path under cwd |
| Exit code 10 | High-risk write needs confirmation | Confirm with the user, re-run with `--yes` |
| Every call "fails" in a wrapper script | Checking `code == 0` | Check `ok == true` or exit code |
| Broken QR code / hang | Interactive `config init` | Use `lark_setup.py` |
| User never sees the auth URL | URL shown and polled in one turn | Split flow: `--print-url-only`, end turn, then `--device-code` |
| `unknown command "workitem"` from `meegle` | Meegle registers business commands **only after login** — an unauthenticated CLI looks identical to a nonexistent command | Run `meegle auth status --format json`; if `authenticated:false`, log in first (see the sub-skill) |
| Asked about 工作项 / 需求 / 迭代, but `lark-cli` has no such domain | Wrong product | [Section 0](#0-product-routing-decide-this-before-anything-else) — this is Meegle, not Lark collaboration |
| A duplicate meegle skill appears after install | Official wizard ran `skills add` | Reinstall with `--no-skills`; remove the globally added copy |

Update both CLI and skills together:

```bash
lark-cli update
```
