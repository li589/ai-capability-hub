# Other Domains Reference (lark-cli 1.0.82)

Low-frequency domains that still need to be on file. Per domain: one-line positioning,
shortcut table, examples, traps, scopes.

Verified against the installed `lark-cli 1.0.82` (`--help` / `schema`) and cross-checked
against `/tmp/lark_official/shortcuts/<domain>/*.go` (`Command:` / `Scopes:` / `Risk:`).

Conventions: `+name` = Tier 1 shortcut (preferred); `resource method` = Tier 2 typed API
command; Risk is verbatim from `--help`; `high-risk-write` exits **10** without `--yes` and
must never be auto-confirmed. Every domain except `mindnotes` has an embedded guide at
`lark-cli skills read lark-<domain>`.

---

## slides — presentation create/read/edit

Presentations are edited as **XML**, not blocks. Identified by `xml_presentation_id`; a
slides URL or a wiki URL resolving to slides is also accepted.

| Command | Risk | What it does |
|---|---|---|
| `+create` | write | Create from `--title` + `--slides` (JSON array of `<slide>` XML, **max 10**) |
| `+add-slide` | write | Append/insert one page (`--slide` = one complete `<slide>` XML doc) |
| `+delete-slide` | write | Delete one page by `--slide-id` |
| `+replace-slide` | write | Replace elements on a page via `block_replace` / `block_insert` parts |
| `+replace-pages` | write | Batch rebuild pages: create new before old, then delete old — **not atomic** |
| `+xml-get` | read | Fetch full presentation XML or one slide's XML |
| `+screenshot` | read | Save up to 10 page screenshots to files (no Base64 in stdout) |
| `+media-upload` | write | Upload a local image, return `file_token` for `<img src=...>` |
| `+history-list` | read | List history versions |
| `+history-revert` | write | Revert to a historical version |
| `+history-revert-status` | read | Poll the revert task |

Tier 2: `xml_presentations` (create, get), `xml_presentation.slide` (create, delete, get,
replace), `xml_presentation.slide_image` (list, render), `xml_presentation.history` (list,
revert, revert_status).

```bash
lark-cli slides +create --title "Q3 Review" --slides @slides.json
lark-cli slides +xml-get --presentation S7YwsFIGIlnS2qdscKDc1Yabcef --slide-number 3 --remove-attr-id
lark-cli slides +xml-get --presentation <url> --output ./deck.xml
lark-cli slides +screenshot --presentation <url> --slide-number 1 --slide-number 2 --output-dir ./shots
lark-cli slides +add-slide --presentation <id> --slide @page.xml --revision-id 42
```

**Traps.** Canvas is 960x540 — content outside clips silently. `+create --slides` caps at
10 pages; for more, create then loop `+add-slide` one page at a time.
`<img src="@./local.png">` inside slide XML is auto-uploaded and rewritten to `file_token`
by `+create`/`+add-slide`, so `+media-upload` is rarely needed explicitly. `--revision-id`
defaults to `-1` (latest); a real number gives optimistic locking (mismatch fails instead of
clobbering). `+replace-pages` is not atomic — a mid-flight failure leaves both pages.
`+delete-slide` is not undoable in place; recover via `+history-list` → `+history-revert` →
`+history-revert-status`. `+xml-get --raw` is incompatible with `--output` and `--jq`.
Wiki-hosted decks pull in conditional scope `wiki:node:read`.

**Scopes.** `slides:presentation:read|create|update|write_only|screenshot`,
`docs:document.media:upload`; conditional `wiki:node:read`.

---

## markdown — Drive-native Markdown files

Not doc blocks. Treats a Markdown file in Drive as a whole-file blob: fetch, edit, push
back. Keyed by `--file-token`.

| Command | Risk | What it does |
|---|---|---|
| `+create` | write | Create a Markdown file in Drive |
| `+fetch` | read | Download content |
| `+patch` | write | fetch → local pattern replace → overwrite, in one call |
| `+overwrite` | write | Replace entire content |
| `+diff` | read | Remote-vs-remote version diff, or remote-vs-local file diff |

```bash
lark-cli markdown +fetch --file-token <token>
lark-cli markdown +patch --file-token <token> --pattern "TODO: fill in" --content "Owner: Alice"
lark-cli markdown +patch --file-token <token> --regex --pattern '^## Status.*$' --content @newstatus.md
lark-cli markdown +diff --file-token <token> --file ./local.md --context-lines 5
lark-cli markdown +diff --file-token <token> --from-version 3 --to-version 7
```

**Traps.** `+overwrite` replaces everything — prefer `+patch`, and run `+diff` first if
unsure what's remote. `--pattern` is **literal by default**; `--regex` switches to RE2 (no
backreferences, no lookaround). `--content`/`--pattern` support `@file` and `-`, but **only
one flag per call may read stdin** — use `@file` for the other. `--to-version` requires
`--from-version`; `--from-version` alone means "this version vs latest". No optimistic
locking anywhere here: concurrent editors → last writer wins.

**Scopes.** `drive:file:download`, `drive:file:upload`, `drive:drive.metadata:readonly`.

---

## vc — video conference

Two layers: meeting **records** (historical search/detail) and **live meeting control**
(the "agent in the meeting" flows, from `skills/lark-vc-agent/`).

| Command | Risk | What it does |
|---|---|---|
| `+search` | read | Search meeting records; **requires ≥1 filter** |
| `+detail` | read | Details incl. `note_id` and `minute_token`, by meeting IDs |
| `+recording` | read | Resolve `minute_token` from meeting-ids or calendar-event-ids |
| `+notes` | read | Query meeting notes via meeting-ids / minute-tokens / calendar-event-ids |
| `+meeting-events` | read | List meeting events by meeting ID |
| `+meeting-join` | write | Bot joins by meeting number |
| `+meeting-leave` | write | Bot leaves by meeting ID |
| `+meeting-list-active` | read | Active meetings for current identity or a target user |
| `+meeting-message-send` | write | In-meeting text message or reaction emoji |

Tier 2: `meeting get`.

```bash
lark-cli vc +search --query "roadmap" --start 2026-07-01 --end 2026-07-31
lark-cli vc +detail --meeting-ids 6911188411932033028   # → note_id, minute_token
lark-cli vc +meeting-join --meeting-number 123456789
lark-cli vc +meeting-message-send --meeting-id <id> --text "Recording started"
lark-cli vc +meeting-leave --meeting-id <id>
```

**Traps.** `+notes` **exists but is not listed** in `lark-cli vc --help` — it is real
(`Scopes: vc:note:read` in the Go source) and `--help` works on it; the visible list is not
exhaustive. `+search` with zero filters fails validation; `--start`/`--end` accept ISO 8601
or `YYYY-MM-DD`. `--page-size` on `+search` is a **string** flag, range 1-30, default 15,
and these search shortcuts expose `--page-token` but **not** `--page-all`. `meeting_id`
only exists **after the meeting starts** — before that use `--calendar-event-ids` on
`+recording`/`+notes`. Most reads here are `--as user` only (`+detail` takes bot or user).
`+meeting-events`/`+meeting-list-active` have a user scope plus a *conditional* bot scope,
so bot identity may or may not work. Meeting artifacts come back only with `query_mode=1`
on `vc meeting get`.

**Scopes.** `vc:meeting.search:read`, `vc:meeting:readonly`,
`vc:meeting.meetingevent:read`, `vc:record:readonly`, `vc:note:read`,
`vc:meeting.bot.join:write`, `vc:meeting.message:write`.

---

## minutes — Minutes (妙记) content and metadata

Container for a recording's AI artifacts (summary, todos, chapters, transcript, keywords)
plus raw media. Keyed by `minute_token`.

| Command | Risk | What it does |
|---|---|---|
| `+search` | read | By keyword / owners / participants / time range |
| `+detail` | read | Details with selective artifact flags |
| `+summary` | write | **Replace** the AI summary |
| `+todo` | write | Add / update / delete todo items |
| `+download` | read | Download the audio/video media |
| `+upload` | write | Upload a media file token to generate a minute |
| `+update` | write | Update the title |
| `+speaker-replace` | write | Rebind a transcript speaker from one user to another |
| `+word-replace` | write | Batch word replacement in the transcript |
| `+apply-permission` | write | Apply for view/edit permission |

Tier 2: `minutes get`.

```bash
lark-cli minutes +search --owner-ids me --start 2026-07-01 --end 2026-07-31
lark-cli minutes +detail --minute-tokens <tok> --summary --todo --transcript --output-dir ./minutes
lark-cli minutes +detail --minute-tokens tok1,tok2,tok3 --summary
lark-cli minutes +download --minute-tokens <tok> --url-only
lark-cli minutes +word-replace --minute-token <tok> \
  --replace-words '[{"source_word":"Lark CLI","target_word":"lark-cli"}]'
```

**Traps.** The flag is `--minute-tokens` (**plural**, comma-separated, max 50) on
`+detail` and `+download`, but `--minute-token` (**singular**) on `+word-replace`.
Mixing them yields `unknown flag` with a `did you mean` hint. `+detail` returns nothing
interesting without at least one artifact flag (`--summary --todo --chapter --transcript
--keyword`). `--transcript` is **written to a file**, not printed (default
`./minutes/{minute_token}/`; `--overwrite` to replace). `--output`/`--output-dir` reject
absolute paths. `+summary` replaces, never appends. Mostly `--as user`. `+apply-permission`
only *requests* access.

**Scopes.** `minutes:minutes.search:read`, `minutes:minutes.basic:read`,
`minutes:minutes.artifacts:read`, `minutes:minutes.media:export`,
`minutes:minutes:readonly|update`, `minutes:minutes.upload:write`,
`minutes:permission:apply`.

---

## okr — objectives and key results

Two-level tree (objective → key result) inside a **cycle**. Content is JSON, not plain
text: "simple" semi-plain `{"text":...,"mention":[...]}` or richtext ContentBlock, selected
by `--style`.

| Command | Risk | What it does |
|---|---|---|
| `+cycle-list` / `+cycle-detail` | read | List cycles / list objectives + KRs in a cycle |
| `+create` | write | Create one objective or KR (`--level objective\|key-result`) |
| `+batch-create` | write | Batch create objectives + KRs, **rolls back on failure** |
| `+patch` | write | Patch content / notes / score / deadline |
| `+weight` / `+reorder` | write | Adjust weight / position |
| `+indicator-update` | write | Update an indicator's current value |
| `+progress-create` / `+progress-update` | write | Create / update a progress record |
| `+progress-get` / `+progress-list` | read | Read progress |
| `+progress-delete` | **high-risk-write** | Delete a progress record — needs `--yes` |
| `+upload-image` | write | Upload an image for progress rich text |

Tier 2: `cycles`, `cycle.objectives`, `objectives`, `objective.key_results`,
`objective.alignments`, `objective.indicators`, `key_results`, `key_result.indicators`,
`alignments`, `categories`, `indicators`.

```bash
lark-cli okr +cycle-detail --cycle-id 6969382217837543437
lark-cli okr +create --level objective --cycle-id <cid> --content '{"text":"Ship v2 to all tenants"}'
lark-cli okr +create --level key-result --objective-id <oid> --content '{"text":"Migrate 100% of tenants"}'
lark-cli okr +progress-delete --progress-id <pid> --yes    # only after the human confirms
```

**Traps.** `--level objective` requires `--cycle-id`; `--level key-result` requires
`--objective-id`. `--content`/`--notes` are JSON, not raw strings (same one-stdin-flag rule).
`+progress-delete` is the only high-risk-write here → exit 10 without `--yes`.
`+batch-create` rolls back on failure; a loop of single `+create` calls does not.
`--cycle-id` is an int64 passed as a string. `--style richtext` returns much larger
payloads — trim with `--jq`.

**Scopes.** `okr:okr.period:readonly`, `okr:okr.content:readonly|writeonly`,
`okr:okr.progress:readonly|writeonly|delete`, `okr:okr.progress.file:upload`.

---

## approval — approval instances and tasks

**No shortcuts at all** — Tier 2 typed commands only. Use this for "my approval to-dos",
not `task`.

| Resource | Methods |
|---|---|
| `approvals` | `get`, `search` |
| `instances` | `cancel`, `cc`, `create`, `get`, `initiated` |
| `tasks` | `add_sign`, `approve`, `query`, `reject`, `remind`, `rollback`, `transfer` |

```bash
# topic: 1=待办 2=已办 3=已发起 17=未读知会 18=已读知会
lark-cli approval tasks query --topic 1 --as user
lark-cli approval approvals search --data '{"user_id":"ou_xxx"}' --as user
lark-cli approval approvals get --approval-code 7C468A54-8745-2245-9675-08B7C63E7A85
lark-cli approval instances create --data @instance.json --yes
lark-cli approval tasks approve --data @approve.json --yes
```

**Traps.** `tasks query --topic` is **required** and is a numeric enum passed as a string —
there is no "give me everything" mode. `instances create` and the task action verbs
(`approve`, `reject`, `transfer`, `rollback`, `add_sign`) are `high-risk-write` → exit 10
without `--yes`. Approval to-dos are **not** Lark tasks; non-approval to-dos belong to
`task`. This domain cannot create approval **definitions**, only instances against existing
ones, and third-party definitions reject native instance creation. Typed flags override
matching keys in `--params`. Most calls need `--as user`.

**Scopes.** Per method — take `_meta.scopes` from
`lark-cli schema approval.<resource>.<method>`.

---

## attendance — clock-in records

Minimal: one resource, one method, no shortcuts. Check your own attendance.

| Resource | Methods |
|---|---|
| `user_tasks` | `query` |

```bash
lark-cli attendance user_tasks query --employee-type employee_id \
  --data '{"user_ids":["abc123"],"check_date_from":20260701,"check_date_to":20260731}' --as user
```

**Traps.** Needs **both** `--params` and `--data` content (`schema` marks
`required: ["data","params"]`); `--employee-type` is the required param.
`check_date_from`/`check_date_to` are **integers** in `yyyyMMdd` form, not ISO date
strings. `--employee-type` (`employee_id | employee_no`) decides how `user_ids` is
interpreted — getting it wrong returns empty results, not an error. `user_ids` are
attendance employee IDs, **not** `open_id`; resolve via `contact` batch-get-id if you only
have emails/phones. Tenant-wide queries generally need admin backend permission.

**Scopes.** `lark-cli schema attendance.user_tasks.query` → `_meta.scopes`.

---

## apps — Miaoda (妙搭 / Spark) app development

Largest shortcut surface in the CLI: **82 shortcuts** in 1.0.82. App create/deploy/observe,
app-scoped database, file storage, roles, API keys, automation triggers, and an agent-driven
"chat to build" loop. Full list via `lark-cli apps --help`. Most useful ~15:

| Command | Risk | What it does |
|---|---|---|
| `+create` / `+list` / `+get` | write / read / read | Create app; list visible apps; one app's detail |
| `+init` | write | Initialize app code + local dev environment |
| `+session-create` / `+session-get` | write / read | Create a session; read status, queued turns, latest turn |
| `+chat` | write | Send a message to a session to build/iterate |
| `+html-publish` | write | Publish HTML → url or release_id |
| `+release-create` / `+release-get` | write / read | Ship; poll status |
| `+db-execute` / `+db-table-list` | write / read | SELECT/DML/DDL; list tables |
| `+log-list` | read | Search online app logs |
| `+env-set` / `+env-list` | write / read | App environment variables |
| `+file-upload` / `+file-download` | write / read | App file storage |
| `+access-scope-set` | write | Visibility: specific / public / tenant |

```bash
lark-cli apps +list --as user
lark-cli apps +session-create --app-id <app_id> --as user
lark-cli apps +chat --app-id <app_id> --session-id <sid> --message "做一个待办清单页面" --as user
lark-cli apps +release-create --app-id <app_id> --as user
lark-cli apps +release-get --app-id <app_id> --release-id <rid> --as user
lark-cli apps +db-execute --app-id <app_id> --sql "SELECT count(*) FROM todos" --as user
```

**Traps.** Nearly all of `apps` is **`--as user` only** — a bot-default profile gets
`resolved identity "bot" ... this command only supports: user` (exit 2). Several
irreversible operations: `+db-env-create` (splits a single-env DB into dev/online),
`+db-env-migrate` (publishes dev→online schema), `+db-recovery-apply` (overwrites data),
`+openapi-key-delete`; preview with `+db-env-diff` / `+db-recovery-diff` / `--dry-run`.
`+openapi-key-create`/`+openapi-key-reset` return the raw secret **once** (all other key
commands redact); prefer `+openapi-key-disable` over `-delete`. `+automation-create`
creates the trigger **disabled** — it won't fire until `+automation-enable`.
`+automation-get` redacts the webhook Bearer token. List commands use **cursor
pagination**, so `--page-all` boundaries differ from offset-style endpoints. Not the right
domain for ordinary Drive uploads (`drive`), doc editing (`doc`), or native Slides
(`slides`).

**Scopes.** Per command, and largely gated by the caller's Miaoda permissions rather than
classic OAuth scopes.

---

## event — real-time event consumption

Long-running event bus, not request/response. Subscribe by **EventKey**, receive NDJSON on
stdout — one JSON object per line.

| Command | Risk | What it does |
|---|---|---|
| `event list` | read | All EventKeys, grouped by domain, with AUTH + PARAMS columns |
| `event schema <EventKey>` | read | Required scopes, required console events, output schema |
| `event consume <EventKey>` | read | Start consuming; starts the daemon if needed |
| `event status` | read | Daemon status per discovered app |
| `event stop` | — | Stop the daemon |

```bash
lark-cli event list
lark-cli event schema im.message.receive_v1
lark-cli event consume im.message.receive_v1 --max-events 5 --timeout 2m
lark-cli event consume im.message.receive_v1 --jq '.chat_id' --quiet
lark-cli event consume card.action.trigger --output-dir ./events --timeout 30s
```

**Traps.** `event consume` runs **until stopped** — always pass `--max-events` and/or
`--timeout` from an agent, or the call never returns. `--timeout` firing is a **normal exit
(code 0)** with `reason: timeout` on stderr; not a failure. Output is **NDJSON**, not one
JSON document — parse line by line. `--jq` here has no `-q` shorthand and is a per-line
filter. `event schema` also lists **Required Console Events**, which must be enabled in the
developer console separately from OAuth scopes; missing them means silence, not an error.
`--as` must match the EventKey's declared AuthTypes (the AUTH column); default is `auto`.
`--output-dir` rejects absolute paths and `~`. `--max-events N` on multi-worker EventKeys
may emit up to `workers-1` past N. Card interactions arrive as `card.action.trigger`; its
token is valid 30 min and allows at most 2 card updates.

---

## whiteboard — boards inside docs

An object embedded in a Lark doc, addressed by `--whiteboard-token`. Input can be raw
whiteboard DSL, Mermaid, PlantUML, or SVG.

| Command | Risk | What it does |
|---|---|---|
| `+export` | read | Export as `preview` (image) / `svg` / `source` / `raw` nodes |
| `+update` | write | Update content from DSL / Mermaid / PlantUML / SVG |

```bash
lark-cli whiteboard +export --whiteboard-token <tok> --output-type source
lark-cli whiteboard +export --whiteboard-token <tok> --output-type preview --output ./board.png --overwrite
lark-cli whiteboard +update --whiteboard-token <tok> --input_format mermaid --source @flow.mmd --overwrite
```

**Traps.** Flag naming is **inconsistent with the rest of the CLI**: `+update` uses
underscore `--input_format`, hidden `+query` uses `--output_as`, while `+export` uses the
normal `--output-type`. Don't normalize by guess. Two hidden aliases still work: `+query`
(alias of `+export`, with `--output_as image|svg|code|raw`) and `+whiteboard-update` (alias
of `+update`); both are `Hidden: true` in the Go source and absent from `--help` — use the
canonical names. `--output` is **required** for `--output-type preview`; optional for
`svg`/`source`/`raw` (content goes to stdout). `+update` without `--overwrite` **adds to**
existing content instead of replacing. `--idempotent-token` must be ≥10 characters.
Editing needs edit permission on the host document, not just the board.

---

## note — meeting notes

Thin read-only domain over meeting notes. Reached from `vc +detail`, which returns `note_id`.

| Command | Risk | What it does |
|---|---|---|
| `+detail` | read | Display type, document tokens, by `--note-id` |
| `+transcript` | read | Fetch the unified transcript and save it to a file |

```bash
lark-cli vc +detail --meeting-ids <mid>          # → note_id
lark-cli note +detail --note-id <note_id>
lark-cli note +transcript --note-id <note_id> --locale zh_cn --output ./notes/t.md --overwrite
```

**Traps.** `+transcript` **writes a file**; the envelope only reports where (default
`./notes/{note_id}/unified_transcript.{md,txt}`). `--output` must be relative, and an
existing file blocks the call without `--overwrite`. `--locale` values are underscore-style
(`zh_cn`, `en_us`, `ja_jp`), **not** BCP-47 `zh-CN` — other domains use the dashed form, do
not copy across. A meeting note (`note_id`) is not a minute (`minute_token`): `note` = the
collaborative note, `minutes` = the recording's AI artifacts. Both commands need
`vc:note:read`; missing it surfaces as `error.missing_scopes: ["vc:note:read"]`.

---

## mindnotes — 思维笔记 (mind notes)

No shortcuts, and **no directory under `/tmp/lark_official/skills/`** — the only discovery
path is `lark-cli mindnotes --help` plus `schema`. There is no
`lark-cli skills read lark-mindnotes`.

| Resource | Methods |
|---|---|
| `nodes` | `list`, `create` |

```bash
lark-cli mindnotes nodes list --mindnote-id <id> --as user
lark-cli schema mindnotes.nodes.create              # node payload shape lives here only
lark-cli mindnotes nodes create --mindnote-id <id> --data @nodes.json --as user
```

**Traps.** `nodes create` is documented as "创建/更新" — the same method creates *and*
updates depending on the body; read the schema first, the payload shape is invisible in
`--help`. **`--as user` only** (`_meta.access_tokens: ["user"]`); a bot-default profile
gets exit 2 with `use --as user`. Scope is `mindnote:node:read` — **singular** `mindnote:`
while the CLI domain is plural `mindnotes`, easy to mistype in a scope request.
`--mindnote-id` is required on both methods. No pagination flags on `nodes list` — the node
tree returns in one shot. The domain description in `--help` is Chinese-only, unlike every
other domain; it simply hasn't been localized.

**Scopes.** `mindnote:node:read`; write scope via `lark-cli schema mindnotes.nodes.create`.
