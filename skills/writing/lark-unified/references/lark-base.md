# Base — multi-dimensional tables (bitable): tables, fields, records, views, analytics

Owns everything inside a Lark Base: resolving Base URLs/titles to a `base_token`, the resource directory (`base-block`), tables, fields (including formula and lookup), records (read, search, write, attachments, history, share links), views and their filter/sort/group/card/timebar configuration, server-side aggregation via `+data-query`, forms, dashboards and their blocks, workflows, advanced permissions and roles. Does **not** own file import/export between local disk and Base (Drive domain), authentication and scope recovery (shared domain), or spreadsheet cells.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+url-resolve` | `--url` (alias `--query`) | Turn a Base / Wiki / record-share URL into `base_token` + `block_type` + real IDs |
| `+title-resolve` | `--title` (<= 30 chars) | Find a Base by a short title keyword via Drive search |
| `+base-create` | `--name`, `--folder-token`, `--time-zone`, `--table-name`, `--fields` | Create a Base, ideally with the first table's name and schema in one call |
| `+base-copy` | `--base-token`, `--name`, `--folder-token`, `--without-content`, `--time-zone` | Server-side copy; never emulate with export + import |
| `+base-get` | `--base-token` | Base name, owner, permission state |
| `+base-block-list` / `-create` / `-move` / `-rename` / `-delete` | `--base-token`, `--type`, `--parent-id`, `--yes` | Resource directory of folders / tables / docx / dashboards / workflows |
| `+table-list` / `+table-get` / `+table-create` / `+table-update` / `+table-delete` | `--base-token`, `--table-id`, `--name`, `--fields`, `--view`, `--offset`, `--limit`, `--yes` | Table lifecycle |
| `+field-list` / `+field-get` / `+field-create` / `+field-update` / `+field-delete` | `--table-id`, `--field-id`, `--json`, `--i-have-read-guide`, `--offset`, `--limit`, `--yes` | Field schema, including formula and lookup |
| `+field-search-options` | `--table-id`, `--field-id` | Enumerate existing options of a select field before writing |
| `+record-list` | `--table-id`, `--view-id`, `--field-id` (alias `--fields` / `--field-names`), `--filter-json`, `--sort-json`, `--offset`, `--limit`, `--format` | Read raw records with server-side filter / sort / projection |
| `+record-search` | `--keyword`, `--search-field`, plus the `+record-list` flags, or `--json` | Keyword search across chosen fields |
| `+record-get` | `--record-id` (repeatable), `--field-id`, `--json` | Fetch specific records by ID |
| `+record-upsert` | `--table-id`, `--record-id` (optional), `--json` | Create one record, or update it when `--record-id` is given |
| `+record-batch-create` | `--json` with `create_records` | Insert many records in one call |
| `+record-batch-update` | `--json` with `update_records` map | Patch many records by ID |
| `+record-delete` | `--record-id` (repeatable) or `--json`, `--yes` | Delete records (high-risk) |
| `+record-upload-attachment` / `-download-attachment` / `-remove-attachment` | `--record-id`, `--field-id`, file path, `--yes` | Attachment field I/O |
| `+record-history-list` | `--record-id` | Edit history of a single record |
| `+record-share-link-create` | `--record-ids` (max 100) | Share links for individual records |
| `+view-list` / `+view-get` / `+view-create` / `+view-rename` / `+view-delete` | `--table-id`, `--view-id`, `--offset`, `--limit`, `--yes` | View lifecycle |
| `+view-get-filter` / `-sort` / `-group` / `-card` / `-timebar` / `-visible-fields` | `--table-id`, `--view-id` | Read current view configuration |
| `+view-set-filter` / `-sort` / `-group` / `-card` / `-timebar` / `-visible-fields` | `--view-id`, `--json` | Write view configuration (read-modify-write) |
| `+data-query` | `--base-token`, `--dsl` | Server-side group-by, aggregation, filtered aggregation, Top/Bottom N |
| `+form-list` / `-get` / `-create` / `-update` / `-delete` | `--base-token`, `--table-id`, `--form-id`, `--yes` | Forms owned by a table |
| `+form-detail` | `--share-token` | Read a shared form's questions, filters, and required `base_token` |
| `+form-questions-list` / `-create` / `-update` / `-delete` | `--table-id`, `--form-id`, `--question-ids`, `--json`, `--yes` | Form questions (backed by table fields) |
| `+form-submit` | `--json`, `--base-token`, `--yes` | Submit a form response (high-risk) |
| `+dashboard-list` / `-get` / `-create` / `-update` / `-delete` | `--base-token`, `--dashboard-id`, `--page-size`, `--page-token`, `--yes` | Dashboards |
| `+dashboard-block-list` / `-get` / `-create` / `-update` / `-delete` / `-get-data` | `--dashboard-id`, `--block-id`, `data_config`, `--page-size`, `--yes` | Dashboard blocks and their computed results |
| `+dashboard-arrange` | `--dashboard-id` | Server-side smart re-layout (no x/y/w/h control) |
| `+workflow-list` / `-get` / `-create` / `-update` / `-enable` / `-disable` | `--base-token`, `--workflow-id`, steps JSON | Automations |
| `+role-list` / `-get` / `-create` / `-update` / `-delete` | `--base-token`, `--role-id`, permission JSON, `--yes` | Custom roles under advanced permissions |
| `+advperm-enable` / `+advperm-disable` | `--base-token`, `--yes` | Toggle advanced permissions |

## Key parameters

**`--base-token` and `--table-id`** — `--base-token` must be a real Base token, never a full URL, wiki token, or workspace token. `--table-id` accepts a table ID (starts with `tbl`) **or** a table name; the same applies to `--field-id`, `--view-id` which accept ID or name. Resolve unknown inputs with `+url-resolve` first; the `table=` query parameter in a Base URL is only the currently selected top-level block and may be a dashboard or workflow, so trust the returned `block_type` / `table_id` / `dashboard_id` / `workflow_id` rather than the parameter name.

**`+record-list`** — `--offset` defaults 0, `--limit` (alias `--page-size`) defaults 100 with range 1-200. `--filter-json` takes a filter object or `@file` and **overrides** any filters on `--view-id`. `--sort-json` is an array like `[{"field":"Updated","desc":true}]`, order is priority, max 10 keys. `--format` is `markdown` (default) or `json` — this is the record read-shape flag, distinct from the global `--format json|pretty|table|ndjson|csv`. Projection via `--field-id` (repeatable), with `--fields` and `--field-names` as aliases.

**`+record-search`** — `--keyword` plus `--search-field` (repeatable) are required unless you pass `--json` with the full request body. `--limit` defaults to **10** here, not 100, still capped at 200.

**`+record-upsert` vs batch writes** — `+record-upsert --json` is a bare `Map<FieldNameOrID, CellValue>`, **not** wrapped in `fields`. `+record-batch-create --json` is `{"create_records":[{...},{...}]}`. `+record-batch-update --json` is `{"update_records":{"recA":{...},"recB":{...}}}`. All three accept `@file`.

**`+data-query --dsl`** — Required. Shape is `{datasource:{type:"table",table:{tableId|tableName}}, dimensions:[], measures:[{field_name,aggregation,alias}], filters:{}, sort:[], pagination:{limit}, shaper:{format:"flat"}}`. Aggregations are `sum`, `avg`, `min`, `max`, `count`, `count_all`, `distinct_count`. `pagination.limit` maxes at **5000** and there is no offset — it caps returned aggregate rows, it is not a paging scan.

**Filter conditions** — `+view-set-filter`, `+record-list --filter-json`, `+record-search --filter-json` and form `visible_rule` all share one tuple protocol: `{"logic":"and","conditions":[["Status","intersects",["Doing"]],["Due","empty"]]}`. `empty` / `non_empty` may be written as 2-element tuples. `+data-query` does **not** use this — it uses an object DSL: `{"type":1,"conjunction":"and","conditions":[{"field_name":"Status","operator":"is","value":["Done"]}]}`.

**`+field-create` / `+field-update`** — `--json` is the field property object. Formula and lookup fields additionally require the hidden `--i-have-read-guide` flag, which you may only set after actually reading the corresponding guide.

## Gotchas

- **Use `--as user` by default.** Base documents are user resources; only switch to `--as bot` when the user explicitly asks for app identity, or when user identity reports resource-level inaccessibility *without* an authorization-recovery hint. Scope or `missing_scopes` errors mean go through user authorization, not identity downgrade. Never loop through identities on `91403`.
- **Batch writes cap at 200 records per call.** Exceeding it returns `1254104`; split into batches. Write serially to the same table — concurrency yields `1254291`, which needs a short wait and a retry, not parallel retries.
- **Only storage fields are writable.** System fields, `formula` and `lookup` are read-only, and attachment fields must go through the dedicated `+record-*-attachment` commands rather than being faked as ordinary CellValues. Writing them back produces `ignored_fields` / `READONLY`.
- **`select` fields accept only options that already exist.** Confirm with `+field-list` or `+field-search-options` before writing, or the value is rejected.
- **Cell value formats are strict.** Dates use `YYYY-MM-DD HH:mm:ss`, person fields use `[{"id":"ou_xxx"}]`, hyperlinks take a URL or Markdown link string. `1254045` means the field name does not exist (recheck spelling, case, and whether it lives on another table); `1254015` means the value type does not match the field.
- **`Invalid discriminator value` on field writes means an incomplete payload.** Re-read the current field, change only the target attribute, and resubmit the full structure — do not just bolt on a `type` key and retry.
- **`+form-questions-update` is a full overwrite, not a patch.** Unpassed fields fall back to defaults; empty strings, `null` or empty arrays are written as literal clears. Read `+form-questions-list` first and echo back every `title` / `description` / `required` / `option_display_mode` / `visible_rule` you want to keep. `+role-update`, by contrast, is a delta merge.
- **`+form-questions-delete` deletes the underlying table field.** The primary field's question cannot be deleted — never put its ID in `--question-ids`; use `+form-questions-update` instead.
- **`+form-detail` lives in a different identifier space.** It takes only `--share-token` from a shared form link, never `--base-token` / `--form-id`. Run it before `+form-submit` to read `questions[].type`, `required`, `filter` and the `base_token` attachments need, and never fill questions that the filter hides. Form attachments go in `--json.attachments`, not in `fields`.
- **A single page never proves a global conclusion.** Default `+record-list` pages, a fixed `--limit`, or local `jq` only establish facts inside what you read. `has_more=true` means the result is partial. Push filtering, sorting, projection, aggregation and limiting into Base itself — do not pull raw rows locally and post-process them by hand.
- **`+data-query` returns dimension rows without `record_id`.** Its dimension rows are deduplicated by field-value combination. For row-level output, record identity, or full raw fields, come back to `+record-list` / `+record-search` / `+record-get`.
- **`link` cell `record_id`s are join keys, not answers.** Cross-table work must read the target table's structure and resolve those IDs into human-readable fields before reporting.
- **Dashboards cannot be positioned precisely.** No shortcut accepts `x/y/w/h`; `+dashboard-arrange` is server-side smart layout only. State that limit before running it when the user asked for exact placement. Create blocks serially. `+dashboard-block-get-data` returns only computed results — no block name, type, layout or `data_config`, which come from `+dashboard-block-get`. Page fully with `--page-size 100` plus `--page-token` until `has_more=false`, then read blocks serially inside one shell call.
- **`+base-block-list` is the cheapest way to see what a Base contains** — folders, tables, docx, dashboards and workflows in one shot. `base-block` commands only manage the directory; content still goes through the table / dashboard / workflow commands.
- **System roles cannot be deleted, and disabling advanced permissions affects custom roles.** `+role-create` handles custom roles only. Confirm impact before `+role-delete` or `+advperm-disable`.
- **File paths must be cwd-relative.** Attachment uploads, `@file` JSON inputs and download destinations reject absolute paths with `unsafe file path`. Prefer stdin for large payloads.
- **Only `--format json|pretty|table|ndjson|csv` exists** as the global output flag — no standalone `--table`, `--csv`, `--yaml` or `--raw`. Pagination is `--page-all` / `--page-limit` / `--page-delay`, with `--page-size` / `--page-token` (dashboards) or `--offset` / `--limit` (records, fields, tables, views) per command.
- **Judge success by `ok == true` or the exit code, never `code == 0`.** Success envelopes carry no top-level `code`; misreading this on write commands can bypass idempotency and duplicate records.
- **High-risk writes gate on exit code 10.** `+record-delete`, `+record-remove-attachment`, `+table-delete`, `+field-delete`, `+field-update`, `+view-delete`, `+form-delete`, `+form-questions-delete`, `+form-submit`, `+dashboard-delete`, `+dashboard-block-delete`, `+base-block-delete`, `+role-delete`, `+role-update` and `+advperm-disable` exit `10` with `error.type == "confirmation"` when `--yes` is absent. Surface `error.action` and `error.risk`, get explicit user approval, then re-run the original argv with `--yes` appended. Never auto-append it; use `--dry-run` to preview without tripping the gate.

## Permissions

Request only the rows you actually hit. **Reading a table is three scopes** —
`base:record:read` + `base:table:read` + `base:field:read`:

```bash
lark-cli auth login --scope "base:record:read base:table:read base:field:read" --no-wait --json
```

Add `base:view:read` if you also read view configuration, and `base:app:read` for `+base-get`.

`--domain base` requests all 40 base scopes in this table, including `base:record:delete`, `base:role:*`
and `base:workflow:*`. In many tenants those extras land in an admin approval queue, so a read-only task
ends up blocked on permissions it never uses. If you need a domain-wide grant anyway, subtract the
destructive parts:
`--domain base --exclude "base:record:delete,base:table:delete,base:field:delete,base:role:delete"`.

Do **not** reach for `--recommend` here expecting a smaller request — it marks 310 scopes across all
domains as recommended, including all 43 base scopes and `base:record:delete`. It is broader than
`--domain base`, not narrower.

`lark-cli schema base.*` fails with `Unknown service: base` — the base shortcuts are not in the schema
registry, so this table is the source of truth for scopes here.

| Operation | Scope |
|---|---|
| `+base-get` | `base:app:read` |
| `+advperm-enable` / `+advperm-disable` | `base:app:update` |
| `+base-copy` | user identity `base:app:copy`; bot identity `base:app:copy` + `docs:permission.member:create` |
| `+title-resolve` | `search:docs:read` |
| `+table-list`, `+data-query` | `base:table:read` |
| `+table-get` | `base:table:read` + `base:field:read` + `base:view:read` |
| `+table-create` | `base:table:create` + `base:field:read` + `base:field:create` + `base:field:update` + `base:view:write_only` |
| `+table-update` / `+table-delete` | `base:table:update` / `base:table:delete` |
| `+field-list` / `+field-get` / `+field-search-options` | `base:field:read` |
| `+field-create` / `+field-update` / `+field-delete` | `base:field:create` / `base:field:update` / `base:field:delete` |
| `+record-list` / `+record-search` / `+record-get` / `+record-share-link-create` | `base:record:read` |
| `+record-download-attachment` | `base:record:read` + `docs:document.media:download` |
| `+record-batch-create` | `base:record:create` |
| `+record-upsert` | `base:record:create` + `base:record:update` |
| `+record-batch-update` | `base:record:update` |
| `+record-remove-attachment` | `base:record:update` + `base:field:read` |
| `+record-upload-attachment` | `base:record:update` + `base:field:read` + `docs:document.media:upload` |
| `+record-delete` | `base:record:delete` |
| `+record-history-list` | `base:history:read` |
| `+view-*` reads / writes | `base:view:read` / `base:view:write_only` |
| `+base-block-list` / `-create` / `-move` or `-rename` / `-delete` | `base:block:read` / `base:block:create` / `base:block:update` / `base:block:delete` |
| `+dashboard-*` reads / creates / updates / deletes | `base:dashboard:read` / `base:dashboard:create` / `base:dashboard:update` / `base:dashboard:delete` |
| `+form-list` / `-get` / `-detail` / `-questions-list` | `base:form:read` |
| `+form-create` / `+form-delete` | `base:form:create` / `base:form:delete` |
| `+form-update` / `+form-questions-create|update|delete` | `base:form:update` |
| `+form-submit` | `base:form:update` + `docs:document.media:upload` |
| `+workflow-list` / `-get` | `base:workflow:read` |
| `+workflow-create`; `+workflow-update` / `-enable` / `-disable` | `base:workflow:create`; `base:workflow:update` |
| `+role-list` / `-get`; `-create`; `-update`; `-delete` | `base:role:read`; `base:role:create`; `base:role:update`; `base:role:delete` |

## Examples

```bash
# Resolve a Base or Wiki URL into a real base_token and block identity
lark-cli base +url-resolve --as user --url "https://xxx.feishu.cn/base/<TOKEN>?table=tblXXX" --format json

# Or find the Base by a short title keyword
lark-cli base +title-resolve --as user --title "客户台账" --format json

# Learn the structure before writing anything
lark-cli base +base-block-list --as user --base-token "<BASE_TOKEN>" --format json
lark-cli base +field-list --as user --base-token "<BASE_TOKEN>" --table-id "tblXXX" --limit 200 --format json

# Create a Base together with its first table schema in one call
lark-cli base +base-create --as user --name "项目跟踪" --table-name "任务" \
  --fields '[{"name":"标题","type":"text"},{"name":"状态","type":"select","options":[{"name":"Todo"},{"name":"Done"}]}]'

# Read records with a server-side filter, sort and projection
lark-cli base +record-list --as user --base-token "<BASE_TOKEN>" --table-id "任务" \
  --filter-json '{"logic":"and","conditions":[["状态","intersects",["Todo"]]]}' \
  --sort-json '[{"field":"更新时间","desc":true}]' \
  --field-id "标题" --field-id "状态" --limit 200 --format json

# Keyword search across chosen fields (note --limit defaults to 10 here)
lark-cli base +record-search --as user --base-token "<BASE_TOKEN>" --table-id "任务" \
  --keyword "Apollo" --search-field "标题" --limit 50 --format json

# Batch create (<= 200 per call), then patch specific records by ID
lark-cli base +record-batch-create --as user --base-token "<BASE_TOKEN>" --table-id "任务" \
  --json '{"create_records":[{"标题":"任务 A","状态":"Todo"},{"标题":"任务 B","状态":"Done"}]}'
lark-cli base +record-batch-update --as user --base-token "<BASE_TOKEN>" --table-id "任务" \
  --json '{"update_records":{"recAAA":{"状态":"Done","完成时间":"2026-08-04 10:00:00"}}}'

# Single-record upsert: bare field map, never wrapped in "fields"
lark-cli base +record-upsert --as user --base-token "<BASE_TOKEN>" --table-id "任务" \
  --record-id "recAAA" --json '{"负责人":[{"id":"ou_xxx"}]}'

# Server-side aggregation instead of pulling rows locally
lark-cli base +data-query --as user --base-token "<BASE_TOKEN>" \
  --dsl '{"datasource":{"type":"table","table":{"tableName":"任务"}},"dimensions":[{"field_name":"状态","alias":"status"}],"measures":[{"field_name":"状态","aggregation":"count","alias":"cnt"}],"sort":[{"field_name":"cnt","order":"desc"}],"pagination":{"limit":10},"shaper":{"format":"flat"}}'

# View filters use the tuple protocol, not the data-query DSL
lark-cli base +view-get-filter --as user --base-token "<BASE_TOKEN>" --table-id "任务" --view-id "vewXXX" --format json
lark-cli base +view-set-filter --as user --base-token "<BASE_TOKEN>" --table-id "任务" --view-id "vewXXX" \
  --json '{"logic":"and","conditions":[["状态","intersects",["Todo"]]]}'

# Page dashboard blocks fully, then read one block's computed data
lark-cli base +dashboard-block-list --as user --base-token "<BASE_TOKEN>" \
  --dashboard-id "<DASHBOARD_ID>" --page-size 100 --format json
lark-cli base +dashboard-block-get-data --as user --base-token "<BASE_TOKEN>" --block-id "<BLOCK_ID>" --format json

# Destructive delete: preview, confirm with the user, then append --yes
lark-cli base +record-delete --as user --base-token "<BASE_TOKEN>" --table-id "任务" --record-id "recAAA" --dry-run
lark-cli base +record-delete --as user --base-token "<BASE_TOKEN>" --table-id "任务" --record-id "recAAA" --yes
```
