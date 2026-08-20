# Sheets — spreadsheet workbooks, cells, and in-sheet objects

Owns everything inside a Lark spreadsheet: creating and importing workbooks, sheet structure (insert/delete/merge/resize/hide/freeze/group), reading and writing cell values, formulas, styles, notes and in-cell images, find/replace, atomic multi-operation batches, and the object layer (charts, pivot tables, conditional formats, filters, filter views, sparklines, floating images, dropdowns). Does **not** own finding spreadsheet files by name in cloud space (Drive `+search`), Base/bitable records, or document body edits.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+workbook-create` | `--title`, `--folder-token`, `--values`, `--sheets`, `--styles` | Create a new spreadsheet, optionally with typed data and styles in one step |
| `+workbook-import` | `--file` (required), `--folder-token`, `--name` | Turn a local `.xlsx` / `.xls` / `.csv` into a new spreadsheet |
| `+workbook-info` | `--url` / `--spreadsheet-token` | List sub-sheets with `sheet_id` / `title` / `row_count` / `column_count` |
| `+workbook-export` | `--file-extension`, `--sheet-id`, `--output-path` | Export the workbook as xlsx, or one sheet as csv |
| `+sheet-create` / `+sheet-copy` / `+sheet-rename` / `+sheet-move` / `+sheet-delete` / `+sheet-set-tab-color` | `--title`, `--index`, `--row-count`, `--col-count` | Sub-sheet lifecycle |
| `+sheet-info` | `--include`, `--range` | Layout: merges, row heights, col widths, hidden rows/cols, groups, frozen panes |
| `+csv-get` | `--range`, `--max-chars`, `--include-row-prefix`, `--skip-hidden` | Read a range as plain CSV text |
| `+csv-put` | `--start-cell`, `--csv`, `--allow-overwrite` | Flatten a CSV block onto the sheet (values or formulas) |
| `+cells-get` | `--range`, `--include`, `--max-chars` | Read values plus formulas / styles / comments / data validation |
| `+cells-set` | `--range`, `--cells`, `--copy-to-range`, `--max-cells` | Rich write: values, formulas, styles, notes, rich text |
| `+cells-set-image` | `--range` (single cell), `--image`, `--name` | Embed an image inside one cell |
| `+cells-clear` / `+cells-batch-clear` | `--range` / `--ranges`, `--scope`, `--yes` | Clear content, formats, or both (high-risk) |
| `+cells-set-style` / `+cells-batch-set-style` | `--range` / `--ranges`, style flags, `--border-styles` | Apply styles to one or many ranges |
| `+cells-search` | `--find`, `--range`, `--regex`, `--match-case`, `--match-entire-cell`, `--include-formulas`, `--max-matches`, `--offset` | Locate matching cells |
| `+cells-replace` | `--find`, `--replacement`, plus the same matching flags | Replace matched text |
| `+table-put` / `+table-get` | `--sheets`, `--styles` / `--range`, `--no-header` | Typed tabular I/O with dtypes and display formats |
| `+range-sort` / `+range-copy` / `+range-move` / `+range-fill` | `--range`, `--sort-keys`, `--has-header`, `--source-range`, `--target-range`, `--paste-type` | Structural range operations |
| `+dim-insert` / `+dim-delete` / `+dim-move` / `+dim-freeze` | `--position`, `--count`, `--inherit-style`, `--dimension` | Row/column insert, delete, move, freeze |
| `+rows-resize` / `+cols-resize` | `--range` + `--height` / `--width`, or `--heights` / `--widths` map, `--type` | Row heights and column widths |
| `+chart-create` / `+chart-update` / `+chart-delete` / `+chart-list` | `--properties`, `--chart-id` | Native charts |
| `+pivot-create` / `+pivot-update` / `+pivot-delete` / `+pivot-list` | `--source`, `--properties`, `--target-sheet-id` / `--target-sheet-name`, `--target-position`, `--pivot-table-id` | Pivot tables |
| `+cond-format-create` / `-update` / `-delete` / `-list` | `--properties`, `--rule-id` | Conditional formatting rules |
| `+filter-create` / `+filter-update` / `+filter-delete` / `+filter-list` | `--range`, `--properties`, `--sheet-id` | Sheet filter |
| `+filter-view-create` / `-update` / `-delete` / `-list` | `--view-id`, `--properties` | Saved filter views |
| `+sparkline-create` / `-update` / `-delete` / `-list` | `--group-id`, `--properties` | In-cell mini charts |
| `+float-image-create` / `-update` / `-delete` / `-list` | `--float-image-id`, `--image-uri` | Free-floating images |
| `+dropdown-set` / `+dropdown-get` / `+dropdown-update` / `+dropdown-delete` | `--range`, `--options` / `--source-range`, `--colors`, `--multiple`, `--highlight` | Data validation dropdowns |
| `+batch-update` | `--operations`, `--continue-on-error`, `--yes` | Run several write shortcuts atomically and serially |
| `+formula-verify` | `--sheet-id`, `--sheet-name`, `--range`, `--max-locations`, `--exit-on-error` | Scan for `#REF!` / `#VALUE!` / compile failures after writing formulas |
| `+history-list` / `+history-revert` / `+history-revert-status` | `--yes` | Version history and rollback |
| `+revision-get` / `+changeset-get` | `--start-revision`, `--end-revision` | Current revision, and the raw change list between two revisions |

## Key parameters

**Locating a workbook and a sheet** — Two independent XOR groups, each mandatory on most shortcuts. Workbook: `--url` or `--spreadsheet-token` (`--url` parses `/sheets/`, `/spreadsheets/` and `/wiki/` links). Sheet: `--sheet-id` or `--sheet-name`. Omitting either group fails validation with `specify at least one of ...`. `+workbook-create` and `+workbook-import` accept neither group because the target does not exist yet; `+workbook-info`, `+workbook-export`, `+batch-update`, `+cells-batch-clear`, `+cells-batch-set-style`, `+sheet-create`, `+pivot-*` and `+dropdown-update|delete` take only the workbook group.

**`+cells-set`** — `--range` and `--cells` required. `--cells` is a JSON 2D array whose dimensions must match `--range`; each cell may carry `value`, `formula`, `cell_styles`, `note` or `rich_text`. `--max-cells` defaults to 50000. `--copy-to-range` replicates whatever was written (values/formulas/styles, per fields actually passed) into a second range with relative formula shifting. `--allow-overwrite` defaults true.

**`+csv-put`** — `--start-cell` and `--csv` required. `--start-cell` must be a single anchor cell; `--range` is an accepted alias that collapses to the top-left cell. CSV is RFC 4180; a leading `=` is evaluated as a formula. No styles, notes or images — use `+cells-set` for those.

**`+cells-search` / `+cells-replace`** — Search text is `--find`, never `--query`. `--range` is optional (whole sheet when omitted). `--regex`, `--match-case`, `--match-entire-cell`, `--include-formulas` are booleans. Search paginates via `--max-matches` (default 5000) plus `--offset`. `+cells-replace` also requires `--replacement`; passing `""` deletes the matched content, and its `--dry-run` reports `would_replace_count` as a preflight.

**`+range-sort`** — `--range` and `--sort-keys` required. `--sort-keys` is `[{"column":"<col letter>","ascending":<bool>}, ...]`. `--has-header` defaults `false`, so a header row is sorted into the data unless you set it.

**`+pivot-create`** — `--source` (A1 with sheet prefix, e.g. `'Sheet1'!A1:D100`) and `--properties` required. Placement uses `--target-sheet-id` XOR `--target-sheet-name` plus `--target-position`; passing neither auto-creates a fresh sheet, which is the safe default. Pointing `--target-sheet-name` at the source sheet without `--target-position` lands the pivot at A1 and overwrites the source, so the anchor shows `#REF!`.

**`+rows-resize` / `+cols-resize`** — Two shapes. Uniform: `--range` (`2:10` for rows, `A:E` for cols) plus `--height` / `--width` in **pixels**, not points or Excel character units. Per-item: `--heights` / `--widths` as a map (`{"A":100,"C:E":120}`) applied atomically. `--type` is `pixel` / `standard` / `auto` (rows) and `pixel` / `standard` (cols); the map form cannot be nested inside `--operations`.

**`+sheet-info`** — `--include` accepts a comma-separated subset of `merges`, `row_heights`, `col_widths`, `hidden_rows`, `hidden_cols`, `groups`, `frozen`. Row/column *totals* come from `+workbook-info`, not here.

## Gotchas

- **Several intuitive command names do not exist.** `+cells-read`, `+cells-find`, `+sheet-list`, `+workbook-list`, `+workbook-get`, `+get-range`, `+range-get`, `+cell-get`, `+highlight`, `+conditional-format` are all rejected by the CLI. The real names are `+cells-get` / `+csv-get`, `+cells-search`, `+workbook-info` (which lists sheets), and `+cond-format-create`. Likewise there is no `--with-styles`, `--with-merges`, `--include-merged-cells`, `--query`, or `--dimension` on the resize commands.
- **Never guess `Sheet1`.** Unless the user or an earlier tool result stated a sheet name/id, call `+workbook-info` first. Real workbooks — especially Chinese ones — use names like `数据`, `Sheet`, `工作表 1`, or a business label, and guessing costs a `sheet not found` round trip.
- **A `Sheet1!` prefix inside `--range` does not satisfy sheet location.** `--range 'Sheet1!A1:B2'` still needs `--sheet-id` or `--sheet-name` alongside it.
- **Quote any A1 reference containing `!` with single quotes.** In bash, `!` triggers history expansion and fails with `event not found`; double quotes do not protect it. Do not reach for `set +H` — it is an illegal option under `sh` / `dash` and kills the whole command. If the sheet name itself needs inner single quotes, escape as `''\''Sales-2025'\''!A1:D100'`.
- **`--ranges` prefixes must be the sheet display name, case-sensitive** — never the `sheet_id`. `+cells-batch-clear` and `+cells-batch-set-style` cap out at 100 ranges each.
- **Writes that return `ok` are not verified results.** The envelope only says the request was accepted. Read back with `+csv-get` / `+cells-get` / `+<object>-list` when correctness matters, and always run `+formula-verify` to `status='success'` after any formula lands.
- **`+csv-put` numericizes literal-looking strings.** Dotted dates (`12.10` → `12.1`) and zero-padded IDs (`001` → `1`) lose their form. Columns that must stay literal go through `+table-put` with `dtypes: object`; columns that are genuinely quantities (amounts, percentages, counts, dates) should be written as numbers via `+table-put` `dtypes` + `formats`, or `+cells-set` with `number_format` — never as pre-formatted `"$1,234"` / `"30.5%"` strings.
- **`+dim-insert` does not inherit row height.** It carries values, formulas and borders, but new rows fall back to the default height and clip long text. Read the neighbouring `row_height` from `+sheet-info` and pair the insert with `+rows-resize` inside one `+batch-update`.
- **Charts have two header modes.** When `refs` covers only a data subset while the real header sits outside it, `snapshot.data.headerMode` must be `detached` with a `nameRef`; padding `refs` by one row is deprecated and produces "系列1/系列2" legends. `refs[i].value` must be a cell or plain rectangular range, never a whole row/column or open interval. Validate placement against `+workbook-info`'s `row_count` / `column_count`, remembering `position.row` is 0-based while A1 and `--dim-insert --position` are 1-based.
- **Composite JSON with `'Sheet'!` prefixes must go through stdin or `@file`.** Inline `--properties '{...}'` lets bash eat the inner single quotes and corrupts the JSON. Use `--properties - <<'JSON'` or `--properties @file.json`.
- **`@file` only accepts cwd-relative paths.** Absolute paths are rejected as `unsafe file path`, and the error text suggesting "cd there or use a relative path" should be ignored — both pollute the user's working directory. Use stdin instead: `--<flag> - < "$TMPFILE"`. The same rule covers `--file`, `--output-path` and `--image`.
- **`--print-schema` only works on composite JSON flags** (`--cells`, `--properties`, `--operations`, `--border-styles`, `--sort-keys`, `--options`). Pair with `--flag-name <name>` (no `--` prefix) to dump the full schema locally without any network call — more reliable than inferring nested structure from prose.
- **`+csv-get` includes hidden rows and columns by default.** Setting `--skip-hidden=true` filters them but the returned row numbers no longer line up with real sheet rows.
- **`+changeset-get` spans at most 20 revisions.** `end - start + 1 <= 20`, `--start-revision >= 1`, and omitting `--end-revision` resolves to the latest. `latest_revision` in the response is the workbook's current revision, independent of the queried window.
- **Only `--format json|pretty|table|ndjson|csv` exists.** There is no standalone `--table`, `--csv`, `--yaml` or `--raw` flag. Pagination is `--page-all` / `--page-limit` / `--page-delay`, with `--page-size` / `--page-token` on individual commands. Identity is `--as user|bot|auto`.
- **Read stdout only when scripting.** Data goes to stdout, diagnostics to stderr; `2>&1` mixes warnings into the JSON and breaks parsing. Feed the CLI UTF-8 without BOM.
- **Judge success by `ok == true` or the exit code, never `code == 0`.** Success envelopes have no top-level `code`; that field only appears inside error envelopes as the upstream OpenAPI numeric code.
- **High-risk writes gate on exit code 10.** `+cells-clear`, `+cells-batch-clear`, `+dim-delete`, `+sheet-delete`, `+dropdown-delete`, `+filter-delete`, `+history-revert`, `+history-revert-status` and `+batch-update` exit `10` with `error.type == "confirmation"` when `--yes` is missing. That is a gate, not a failure: show `error.action` and `error.risk`, get explicit approval, then re-run the original argv with `--yes` appended. Never auto-append it. `--dry-run` previews without tripping the gate.

## Permissions

| Operation | Scope |
|---|---|
| `+workbook-info`, `+sheet-info`, `+csv-get`, `+cells-get`, `+cells-search`, `+table-get`, `+formula-verify`, `+revision-get`, `+changeset-get`, `+history-list`, `+history-revert-status`, `+dropdown-get`, all `+*-list` | `sheets:spreadsheet:read` |
| `+csv-put`, `+cells-set`, `+cells-set-style`, `+cells-batch-set-style`, `+cells-clear`, `+cells-batch-clear`, `+cells-replace`, `+sheet-create`, `+sheet-rename`, `+sheet-copy`, `+sheet-delete`, `+sheet-set-tab-color`, `+dim-insert`, `+dim-delete`, `+dim-freeze`, `+range-copy`, `+range-move`, `+range-fill`, `+range-sort`, `+rows-resize`, `+cols-resize`, `+batch-update`, `+history-revert`, `+dropdown-set`, `+dropdown-update`, `+dropdown-delete`, `+filter-*` writes | `sheets:spreadsheet:write_only` |
| `+table-put`, `+dim-move`, `+sheet-move` | `sheets:spreadsheet:read` + `sheets:spreadsheet:write_only` |
| `+workbook-create` | `sheets:spreadsheet:create` + `sheets:spreadsheet:write_only` |
| `+cells-set-image` | `sheets:spreadsheet:write_only` + `drive:file:upload` |
| `+workbook-export` | `sheets:spreadsheet:read` + `docs:document:export` + `drive:drive.metadata:readonly` |
| `+workbook-import` | `docs:document.media:upload` + `docs:document:import` |

## Examples

```bash
# Always learn the real sheet names before touching cells
lark-cli sheets +workbook-info --as user --url "https://xxx.feishu.cn/sheets/<TOKEN>" --format json

# Read a range as CSV, then read the same range with formulas and styles
lark-cli sheets +csv-get --as user --url "https://xxx.feishu.cn/sheets/<TOKEN>" \
  --sheet-name "销售明细" --range "A1:F200" --format json
lark-cli sheets +cells-get --as user --spreadsheet-token "<TOKEN>" --sheet-id "<SHEET_ID>" \
  --range "A1:F20" --include value,formula,style,comment --format json

# Create a workbook with typed data and styles in one call (payload via stdin)
lark-cli sheets +workbook-create --as user --title "Q1 预算" --sheets - < ./payload.json

# Write a formula block with +cells-set, then gate on formula health
lark-cli sheets +cells-set --as user --spreadsheet-token "<TOKEN>" --sheet-name "汇总" \
  --range 'F2:F100' --cells - < ./formula-cells.json
lark-cli sheets +formula-verify --as user --spreadsheet-token "<TOKEN>" \
  --sheet-name "汇总" --exit-on-error --format json

# Find, then replace with a dry-run preflight showing would_replace_count
lark-cli sheets +cells-search --as user --spreadsheet-token "<TOKEN>" --sheet-name "台账" \
  --find "待跟进" --match-entire-cell --format json
lark-cli sheets +cells-replace --as user --spreadsheet-token "<TOKEN>" --sheet-name "台账" \
  --find "待跟进" --replacement "进行中" --dry-run

# Sort a data block while protecting the header row
lark-cli sheets +range-sort --as user --spreadsheet-token "<TOKEN>" --sheet-name "台账" \
  --range 'A1:H500' --has-header --sort-keys '[{"column":"D","ascending":false}]'

# Land a pivot on a brand-new sheet (no target flags = zero overwrite risk)
lark-cli sheets +pivot-create --as user --spreadsheet-token "<TOKEN>" \
  --source "'台账'!A1:H500" --properties - < ./pivot.json

# Chart JSON goes through a quoted heredoc so the 'Sheet'! prefix survives
lark-cli sheets +chart-create --as user --spreadsheet-token "<TOKEN>" --sheet-name "看板" \
  --properties - <<'JSON'
{"position":{"row":1,"col_idx":8},"snapshot":{"data":{"refs":[{"value":"'台账'!B1:C20","direction":"column"}]},"plotArea":{"plot":{"type":"column"}}}}
JSON

# Freeze the header, then widen several columns atomically
lark-cli sheets +dim-freeze --as user --spreadsheet-token "<TOKEN>" --sheet-name "台账" \
  --dimension row --count 1
lark-cli sheets +cols-resize --as user --spreadsheet-token "<TOKEN>" --sheet-name "台账" \
  --widths '{"A":90,"B:D":140}' --type pixel

# Destructive clear: preview first, execute only after the user agrees
lark-cli sheets +cells-batch-clear --as user --spreadsheet-token "<TOKEN>" \
  --ranges '["台账!A2:Z1000"]' --scope all --dry-run
lark-cli sheets +cells-batch-clear --as user --spreadsheet-token "<TOKEN>" \
  --ranges '["台账!A2:Z1000"]' --scope all --yes

# Review what an edit actually changed (window capped at 20 revisions)
lark-cli sheets +changeset-get --as user --spreadsheet-token "<TOKEN>" \
  --start-revision 412 --format json
```
