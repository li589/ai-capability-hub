# API Reference — Tier 2 / Tier 3 and shared mechanics (lark-cli 1.0.82)

Tier 1 (`+shortcuts`) is covered per-domain elsewhere. This file covers **Tier 2 (typed API
commands)**, **Tier 3 (`lark-cli api`)**, and the mechanics common to every call: flags,
JSON envelope, exit codes, dry-run, pagination, path safety. All verified against the
installed `lark-cli 1.0.82`.

## Tier 2 — typed API commands

```
lark-cli <domain> <resource> <method> [typed flags] [--params '<json>'] [--data '<json>']
```

One command per Lark Open API method. Unlike Tier 3 it validates parameters, exposes typed
flags with inline enum docs, prints a Risk level, and gates `high-risk-write` behind `--yes`.

Discovery:

```bash
lark-cli <domain> --help                # +shortcuts, then "resource  method1, method2, ..."
lark-cli <domain> <resource> --help
lark-cli <domain> <resource> <method> --help    # typed flags, Risk, schema pointer
```

`lark-cli approval --help` prints raw resources after the shortcuts:

```
  approvals   get, search
  instances   cancel, cc, create, get, initiated
  tasks       add_sign, approve, query, reject, remind, rollback, transfer
```

`<method> --help` groups flags into **API Parameters** (Required / Optional, with
`enum: k=desc|k=desc` inline), **Request Body** (`--data`), **Raw Parameter Input**
(`--params`), **Execution** (`--as`, `--dry-run`, `--yes`, pagination), **Output**. It also
prints the schema pointer, e.g. `lark-cli schema approval.tasks.query`.

### `--params` vs `--data` vs typed flags

- `--params` — query/URL parameters as JSON; `--data` — request body as JSON.
- Both accept `-` (stdin) and `@file`.
- **Typed flags override matching keys in `--params`** (stated verbatim in `--help`).
- Some methods require both: `lark-cli schema attendance.user_tasks.query` has
  `required: ["data", "params"]`.

```bash
lark-cli approval tasks query --topic 1 --as user
lark-cli attendance user_tasks query --employee-type employee_id \
  --data '{"user_ids":["abc"],"check_date_from":20260701,"check_date_to":20260731}' --as user
```

Prefer a `+shortcut` when one covers the task — shortcuts carry batching, file handling and
safety tips the typed command lacks.

## `lark-cli schema` — authoritative parameter source

```bash
lark-cli schema                                   # all methods, JSON array
lark-cli schema <service>.<resource>.<method>     # one method
lark-cli schema <service> <resource> <method>     # space-separated form also works
```

Measured on 1.0.82: bare `lark-cli schema` returns a **JSON array of 245 methods**
(~42k lines). Always narrow to one method unless you are indexing.

Top-level keys are exactly `name`, `description`, `inputSchema`, `outputSchema`, `_meta`:

- `name` — space-separated `"<domain> <resource> <method>"`, e.g. `"vc meeting get"`.
- `description` — the API's Chinese title, sometimes with an **identity note appended**,
  e.g. `"创建群。Identity: \`bot\` only (\`tenant_access_token\`)"`.
- `inputSchema` — `properties.params` and/or `properties.data`, each with its own `required`
  array; `data` carries `"carrier": "--data"`. Leaf fields expose `type`, `description`,
  **`flag`** (the exact CLI flag), **`example`**, plus `enum`, `enumDescriptions`, `default`,
  `minimum` where applicable.
- `outputSchema` — response shape, same annotation style.
- `_meta` — `envelope_version`, `scopes`, `required_scopes`, `access_tokens`, `danger`,
  `risk`, `doc_url`.

`_meta` answers identity and permission questions without trial and error: `access_tokens`
says whether `--as user`, `--as bot`, or both are accepted.

Real examples:

- `lark-cli schema vc.meeting.get` — required `meeting_id` (`flag: --meeting-id`,
  `example: "6911188411932033028"`), optional `query_mode` with `enum: [0,1]` and
  `enumDescriptions: ["只查询会议信息（默认）","只查询会议产物（纪要、逐字稿）"]`, and
  `_meta: {scopes:["vc:meeting:readonly","vc:meeting.meetingevent:read"],
  access_tokens:["bot","user"], danger:false, risk:"read", doc_url:"..."}`.
- `lark-cli schema im.chats.create` — `access_tokens: ["bot"]`, `danger: true`,
  `risk: "write"`, `scopes: ["im:chat","im:chat:create","im:chat:create_by_user"]`.
  `danger` is separate from `risk` and worth reading before writes.
- `lark-cli schema mindnotes.nodes.list` — `access_tokens: ["user"]`,
  `scopes: ["mindnote:node:read"]`. This is how you learn a command is user-only *before*
  hitting the identity error.

**Traps.** `schema` only knows **Tier 2 resources** — `lark-cli schema slides.+create`
fails with `Unknown resource: slides.+create` plus a `hint` listing valid resources; use
`lark-cli <domain> +<cmd> --help` for shortcuts. `schema` errors go to **stderr with exit
code 2** and stdout is empty, so capturing only stdout makes a failure look like an empty
success. There is no per-domain filter: all-or-one.

## Tier 3 — `lark-cli api` (raw escape hatch)

```
lark-cli api <METHOD> <PATH> [--params <json>] [--data <json>] [flags]
```

For endpoints with no typed command yet (new/preview APIs) when you already have the path
from the Lark docs. Extra flags: `--file` (multipart, `[field=]path`, `-` for stdin),
`-o/--output` (binary responses).

```bash
lark-cli api GET /open-apis/calendar/v4/calendars
lark-cli api GET /open-apis/im/v1/chats --params '{"page_size":50}' --page-all
lark-cli api POST /open-apis/im/v1/messages --params '{"receive_id_type":"open_id"}' --data @body.json
```

**Traps.** `lark-cli api --help` reports `Risk: write` for the whole command regardless of
endpoint — there is **no per-endpoint risk gating and no `--yes` gate** in Tier 3, so a
destructive DELETE goes straight through. That is the main reason to prefer Tier 2.
`--output` and `--page-all` are **mutually exclusive**:

```json
{"ok":false,"identity":"bot","error":{"type":"validation","subtype":"invalid_argument",
 "message":"--output and --page-all are mutually exclusive",
 "hint":"drop --page-all to save a binary response, or drop --output to paginate JSON"}}
```

`--page-size 0` means "use the API default" here, unlike shortcuts which have real ranges.

## Shared flags

From `lark-cli im +chat-list --help`; present on essentially every API-calling command
(pagination flags only where the endpoint paginates):

| Flag | Meaning |
|---|---|
| `--as <user\|bot>` | Identity to call with; must be allowed by `_meta.access_tokens`. |
| `--dry-run` | Print the request without executing. |
| `--format <fmt>` | `json` (default) \| `pretty` \| `table` \| `ndjson` \| `csv`. |
| `--json` | **Shorthand for `--format json`** — json is already the default. |
| `-q, --jq <expr>` | jq expression applied to the JSON output. |
| `--page-all` | Continue from `--page-token` until exhaustion or `--page-limit`. |
| `--page-delay <ms>` | Delay between pages; default **200**, range 0-60000 (0 disables). |
| `--page-limit <n>` | Max pages fetched by `--page-all`; default **10**. |
| `--page-size <n>` | Page size for one request (range per-endpoint). |
| `--page-token <cur>` | Starting pagination cursor. |

Plus `--yes` on `high-risk-write`, and `--output` / `--output-dir` / `--overwrite` on
file-writing commands. Note `--format pretty` appears in shortcut help but **not** in
`lark-cli api --help` (which lists `json|ndjson|table|csv`).

## JSON envelope contract

Success → **stdout**, `ok: true`:

```json
{ "ok": true, "identity": "bot", "data": { ... } }
```

Failure → **stderr**, `ok: false`:

```json
{
  "ok": false,
  "identity": "bot",
  "error": {
    "type": "validation", "subtype": "invalid_argument",
    "message": "...", "hint": "...", "param": "--page-limit",
    "params": [{"name":"--output","reason":"conflicts with --page-all"}],
    "missing_scopes": ["vc:note:read"]
  }
}
```

`type` / `subtype` / `message` are always present; `hint`, `param`, `params`,
`missing_scopes`, `risk`, `action` appear situationally.

**Success detection: check `ok == true`, or check the exit code. Never check `code == 0`.**
The success envelope has **no top-level `code` field** — `code` only exists nested inside
raw Lark payloads under `data`. A `code == 0` test on the envelope is always false and
reports every successful call as a failure.

```bash
out=$(lark-cli minutes +search --owner-ids me) || handle_failure   # correct
echo "$out" | jq -e '.ok == true' >/dev/null                       # correct
echo "$out" | jq -e '.code == 0'                                   # WRONG — never true
```

Failures go to stderr; redirecting only stdout leaves an empty file and no error text.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (`ok: true`). Also the normal `--timeout` exit for `event consume`. |
| non-zero (commonly `2`) | Failure — validation, auth, scope, API error. `ok: false` on stderr. |
| `10` | **Confirmation required** for a `high-risk-write`. |

Verified:

```bash
$ lark-cli apps +openapi-key-delete --app-id dummy --key-id dummy --as user; echo $?
{"ok":false,"identity":"user","error":{"type":"confirmation","subtype":"confirmation_required",
 "message":"apps +openapi-key-delete requires confirmation","hint":"add --yes to confirm",
 "risk":"high-risk-write","action":"apps +openapi-key-delete"}}
10
```

Exit 10 is **not a failure** — nothing executed, nothing harmed. **Never auto-retry with
`--yes`**: surface `error.action` and `error.risk`, get an explicit human yes, then re-run.
Typed-command help states it directly: "the agent must NOT add `--yes` on its own". Detect
via `exit == 10` or `error.type == "confirmation"`.

Identity errors are plain exit 2, not 10:

```json
{"ok":false,"identity":"bot","error":{"type":"validation","subtype":"invalid_argument",
 "message":"resolved identity \"bot\" (via auto-detect or default-as) is not supported, this command only supports: user",
 "hint":"use --as user","param":"--as"}}
```

Unknown flags come back with suggestions:

```json
{"error":{"message":"unknown flag \"--minute-token\" for \"lark-cli minutes +download\"",
 "hint":"did you mean --minute-tokens? ...",
 "params":[{"name":"--minute-token","reason":"unknown flag","suggestions":["--minute-tokens"]}]}}
```

## `--dry-run`

```bash
$ lark-cli im +messages-send --chat-id oc_dummy --text hi --dry-run
{
  "ok": true, "identity": "bot", "dry_run": true,
  "data": {
    "api": [{
      "desc": "NOTE: dry-run validates request shape only. Bot/user membership in the target chat is not verified; the real send may fail with `Bot/User can NOT be out of the chat`.",
      "method": "POST", "url": "/open-apis/im/v1/messages",
      "params": {"receive_id_type": "chat_id"},
      "body": {"content": "{\"text\":\"hi\"}", "msg_type": "text", "receive_id": "oc_dummy"}
    }],
    "context": {"app_id": "cli_a1b2c3d4e5f6g7h8"}
  }
}
```

`data.api` is an **array** — one shortcut can expand into several HTTP calls. Each entry has
`method`, `url`, `params`, `body`; `desc` appears only when the command has a caveat.
`data.context.app_id` shows which app the request binds to. Exit code is `0` with
`dry_run: true` at top level. `lark-cli api... --dry-run` yields the same envelope, usually
without `desc`.

**Dry-run validates the request shape only.** It does not verify group membership, resource
existence, permissions, or scopes. A clean dry-run followed by a real call failing with
`Bot/User can NOT be out of the chat` is expected. Its real value is confirming *which*
presentation/chat/token a write would hit.

## `_notice` noise

The envelope can carry a top-level `_notice` object (`internal/output/errors.go`:
`Notice map[string]interface{} \`json:"_notice,omitempty"\``), populated by two independent
providers: `_notice.update` (newer CLI available) and `_notice.skills` (embedded skills out
of date). It rides along on normal output and can break strict JSON consumers.

```bash
export LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1
export LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1
```

These are **two separate opt-outs** — setting only `NO_UPDATE_NOTIFIER` does not suppress
the skills notice. Set both for scripted/agent use.

## Path safety

`--file`, `--output`, `--output-dir`, and `@file` accept **cwd-relative paths only**;
absolute paths and `~` are rejected:

```bash
$ lark-cli minutes +download --minute-tokens dummy --output-dir /tmp/xx; echo $?
{"ok":false,"identity":"bot","error":{"type":"validation","subtype":"invalid_argument",
 "message":"--output must be a relative path within the current directory, got \"/tmp/xx\" (hint: use a relative path like ./filename; flags that support stdin can read an out-of-tree file via '-' instead)"}}
2
```

It is a path-traversal defence, so `../` escapes are rejected too — `cd` into the target
directory instead. The documented workaround for an out-of-tree read is piping via `-`
(stdin), and **only one flag per call may read stdin** (use `@file` for others).
`event consume --output-dir` has the same restriction. Note the message says `--output`
even when the offending flag was `--output-dir`; read `message` for the actual value.

## Pagination semantics

**Manual** — pass `--page-size` and `--page-token`, follow the cursor yourself. Some
shortcuts only support this (e.g. `vc +search`, `minutes +search`, where `--page-size` is a
*string* flag, range 1-30, default 15, and `--page-all` is absent).

**Automatic** — `--page-all` walks pages until exhaustion or `--page-limit`, starting from
`--page-token` if set, sleeping `--page-delay` ms between pages.

| Flag | Default | Range |
|---|---|---|
| `--page-limit` | 10 | shortcuts **1-1000**; `lark-cli api` **0 = unlimited** |
| `--page-delay` | 200 ms | 0-60000 (0 disables throttling) |
| `--page-size` | per endpoint (20 for `im +chat-list`, range 1-100) | per endpoint |

**`--page-limit 0` is not universally "unlimited".** On shortcuts it is a validation error:

```json
{"error":{"message":"--page-limit must be an integer between 1 and 1000","param":"--page-limit"}}
```

Only `lark-cli api --help` documents `0 = unlimited`; treat unlimited as api-only.

Default `--page-limit 10` means `--page-all` **silently stops after 10 pages** — raise it
explicitly and check whether a cursor is still returned. `--page-all` conflicts with
`--output` on `lark-cli api`. Miaoda (`apps`) lists use cursor pagination, so page
boundaries differ from offset-style endpoints. Dropping `--page-delay` to 0 on large runs
invites rate limiting.

## Reading embedded skills

The CLI ships the official skill docs inside the binary, so they always match the CLI
version. `SKILL.md` and reference markdown are embedded; `assets/` and `scripts/` are not.

```bash
lark-cli skills list                                # JSON envelope
lark-cli skills list <skill>                        # one layer under a path, like ls
lark-cli skills read lark-slides                              # the skill's SKILL.md, raw markdown
lark-cli skills read lark-doc references/lark-doc-fetch.md
lark-cli skills read lark-doc/references/lark-doc-fetch.md    # slash form, equivalent
lark-cli skills read lark-doc --json                          # JSON envelope instead of raw markdown
```

`skills list` returns `{"ok":true,"skills":[{name,description,version,metadata}]}`, where
`metadata.cliHelp` points at the right `--help` entry point and `metadata.requires.bins`
lists required binaries. Each `description` also states what the skill does *not* cover,
which is the fastest way to resolve routing boundaries. There is no `lark-mindnotes` skill.

## CLI management commands

**`lark-cli doctor`** — health check over config, auth and connectivity. Returns a JSON
`checks` array of `{name, status, message}` (+ optional `hint`), `status` being
`pass|warn|fail`. Observed names: `cli_version`, `config_file`, `app_resolved`,
`bot_identity`, `user_identity`, `identity_ready`. Typical warn:
`"User identity: missing (no user logged in)"` with `hint: "run: lark-cli auth login --help"`.
`--offline` skips network checks. Run it first on any auth/identity failure — it separates
"not logged in" from "wrong scope" from "network".

**`lark-cli whoami`** — current effective identity as JSON; the quickest way to know what
`--as` will resolve to:

```json
{"profile":"cli_a1b2c3d4e5f6g7h8","appId":"cli_a1b2c3d4e5f6g7h8","brand":"feishu",
 "defaultAs":"auto","identity":"bot","identitySource":"auto_detect",
 "available":true,"tokenStatus":"ready"}
```

`defaultAs: "auto"` + `identitySource: "auto_detect"` explains "resolved identity bot ...
only supports: user" failures — pass `--as user`.

**`lark-cli profile`** — named configuration profiles (one per app): `add`, `list`,
`remove`, `rename`, `use` (`-` toggles back). `--profile <name>` is also a global flag. Its
help carries: **"AI agents: Do NOT switch or remove profiles unless the user explicitly
asks."** Switching silently retargets every later call at a different app; prefer the
per-invocation `--profile` flag over `profile use`.

**`lark-cli update`** — self-update, auto-detecting the install method
(`npm install -g @larksuite/cli@<version>`, `pnpm add -g`, or printing the GitHub Releases
URL for manual installs). `--check` checks without installing; `--json` for scripts. Do not
run unprompted: it changes the CLI version mid-session and command surfaces differ between
versions.
