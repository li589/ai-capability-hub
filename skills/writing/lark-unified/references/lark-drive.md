# Drive — cloud space files, folders, permissions, comments

Owns the container layer of Lark cloud space: uploading/downloading files, creating folders, moving/copying/deleting resources, resolving URLs and tokens, import/export conversions, local-to-Drive sync, version history, collaborators and permission settings, secure labels, and document comments. Does **not** own document body edits (Docs domain), sheet cells or Base records, Wiki node hierarchy, or native `.md` file patch/diff.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+inspect` | `--url`, `--type` | Resolve a URL/token to real `type` / `token` / `title`; unwraps wiki links |
| `+search` | `--query`, `--doc-types`, `--folder-tokens`, `--space-ids`, `--mine`, `--created-by-me`, `--edited-since`, `--opened-since`, `--commented-since`, `--created-since`, `--sort`, `--page-size`, `--page-token` | Find docs / Wiki / sheets / folders |
| `+upload` | `--file`, `--folder-token` / `--wiki-token`, `--file-token`, `--name` | Upload a local file, or overwrite one in place |
| `+download` | `--file-token`, `--output` | Download a Drive file |
| `+preview` | `--file-token`, `--list-only`, `--type`, `--output`, `--if-exists`, `--version` | Inspect available preview formats and fetch PDF/HTML/text/image renditions |
| `+cover` | `--file-token`, `--list-only`, `--spec`, `--output`, `--if-exists` | List cover specs, then download one |
| `+create-folder` | `--folder-token`, `--name` | Create a folder |
| `+create-shortcut` | target + parent folder tokens | Create a shortcut to an existing file |
| `+move` | `--file-token`, `--type`, `--folder-token` | Move a file or folder |
| `+delete` | `--file-token`, `--type`, `--yes` | Delete to trash (high-risk write) |
| `+import` | `--file`, `--type`, `--folder-token`, `--name`, `--target-token` | Convert a local file into docx / sheet / bitable / slides |
| `+export` | `--url` / `--token`, `--doc-type`, `--file-extension`, `--sub-id`, `--only-schema`, `--file-name`, `--output-dir`, `--overwrite` | Export a cloud doc to a local file |
| `+export-download` | `--file-token`, `--file-name`, `--output-dir`, `--overwrite` | Download an already-produced export artifact |
| `+task_result` | `--scenario`, `--ticket`, `--task-id`, `--file-token` | Poll async import/export/delete/move tasks |
| `+status` / `+pull` / `+push` / `+sync` | `--local-dir`, `--folder-token`, `--quick`, `--if-exists`, `--on-conflict`, `--on-duplicate-remote`, `--delete-remote` / `--delete-local`, `--yes` | Compare and sync a local directory with a Drive folder |
| `+version-history` / `+version-get` / `+version-revert` / `+version-delete` | `--file-token`, `--version`, `--limit`, `--cursor`, `--output`, `--overwrite` | Manage file versions |
| `+member-list` | `--token`, `--type`, `--fields`, `--perm-type` | List collaborators |
| `+member-add` | `--token`, `--type`, `--member-id`, `--member-type`, `--member-kind`, `--perm`, `--perm-type`, `--need-notification`, `--yes` | Add up to 10 collaborators |
| `+permission-get-setting` | `--token`, `--type` | Read one resource's own public/share/comment settings |
| `+apply-permission` | `--token`, `--type`, `--perm`, `--remark` | Ask the owner for access (user identity) |
| `+secure-label-list` / `+secure-label-update` | `--token`, `--type`, `--label-id`, `--lang`, `--page-size`, `--page-token` | Read and set secure (classification) labels |
| `+add-comment` / `+list-comments` / `+batch-query-comments` / `+resolve-comment` / `+restore-comment` | `--doc`, `--content`, `--block-id`, `--full-comment`, `--comment-scope`, `--solved-status`, `--need-reaction`, `--need-relation`, `--page-size`, `--page-token` | Document comment lifecycle |
| `+add-reply` / `+list-replies` / `+update-reply` / `+delete-reply` / `+react-reply` | comment + reply ids, `--content`, `--yes` | Comment reply lifecycle |

## Key parameters

**`+search`** — `--query` is capped at **30 characters** (Unicode code points, CJK counts 1 each); exceeding it returns `99992402 field validation failed` rather than truncating. `--page-size` default 15, max 20 (values above 20 clamp, `<= 0` falls back to 15, non-numeric errors out). `--doc-types` accepts `doc,sheet,bitable,mindnote,file,wiki,docx,folder,catalog,slides,shortcut`. `--folder-tokens` and `--space-ids` are mutually exclusive. `--mine` / `--creator-ids` mean **owner**, while `--created-by-me` / `--original-creator-ids` mean the original creator; the paired flags in each group are mutually exclusive. `--sort` accepts only `default`, `edit_time`, `edit_time_asc`, `open_time`, `create_time`. Time values accept `7d` / `1m` (fixed 30 days, not a calendar month) / `1y` / `YYYY-MM-DD` / RFC3339 / a 10-digit Unix second.

**`+upload`** — `--file` is required. `--folder-token` maps to `parent_type=explorer`, `--wiki-token` maps to `parent_type=wiki` and must be a wiki **node** token, not a `space_id`; the two are mutually exclusive and passing an empty string to either is an error. Omit both to land in the Drive root. `--file-token` switches to overwrite-in-place semantics and keeps the token.

**`+export`** — `--url` XOR `--token`; a bare token requires `--doc-type` (`doc` / `docx` / `sheet` / `bitable` / `slides` / `wiki`). `--file-extension` accepts `docx` / `pdf` / `xlsx` / `csv` / `markdown` / `base` / `pptx`, constrained by source: `doc` → docx/pdf; `docx` → docx/pdf/markdown; `sheet` → xlsx/csv; `bitable` → xlsx/csv/base; `slides` → pptx/pdf. `csv` requires `--sub-id`. `--only-schema` is valid only for `bitable` + `base`. Internal polling is fixed at 10 attempts, 5 s apart.

**`+import`** — `--file` and `--type` are required; `--type` is `docx` / `sheet` / `bitable` / `slides`. Extension must match the target: `.docx/.doc/.txt/.md/.html` → docx only; `.xlsx`/`.csv` → sheet or bitable; `.xls` → sheet; `.base` → bitable; `.pptx` → slides. Size caps are enforced locally before upload: `.doc/.docx` 600 MB, `.xlsx` 800 MB, `.pptx` 500 MB, `.csv` 100 MB into bitable but 20 MB into sheet, `.txt/.md/.html/.xls/.base` 20 MB. `--target-token` mounts data into an existing bitable and only works with `--type bitable`.

**`+delete`** — `--file-token`, `--type` and `--yes` are all required. `--type` accepts `file` / `docx` / `bitable` / `doc` / `sheet` / `mindnote` / `folder` / `shortcut` / `slides`. Rate limit is 5 QPS and 10,000 calls/day, and the endpoint does not support concurrency.

**`+push` / `+sync`** — `--local-dir` and `--folder-token` required. `--if-exists` is `skip` (default) / `smart` / `overwrite`. `--on-duplicate-remote` is `fail` (default) / `newest` / `oldest`. `--on-conflict` on `+sync` is `local-wins` / `remote-wins` / `keep-both` / `ask`. `--quick` compares modified time instead of SHA-256. `--delete-remote` requires `--yes` and only mirrors files, never removing remote-only directories.

**`+member-list` / `+permission-get-setting`** — `--token` takes a bare token or a URL (`/folder/`, `/docx/`, `/doc/`, `/sheets/`, `/base/`, `/bitable/`, `/wiki/`, `/file/`, `/mindnotes/`, `/slides/`, `/minutes/`, `/page/`). A bare token requires `--type` from `doc` / `sheet` / `file` / `wiki` / `bitable` / `docx` / `mindnote` / `minutes` / `slides` / `folder` / `apps`; a URL plus a conflicting `--type` is rejected. `--fields` accepts `name` / `type` / `avatar` / `external_label` or `*`. `--perm-type` (`container` / `single_page`) only applies to `--type wiki`.

## Gotchas

- **Wiki tokens are not file tokens.** A `/wiki/<token>` may be backed by docx, sheet, bitable, slides or file. Resolve with `+inspect` first; guessing gives `not exist` or `1069914`.
- **High-risk writes gate on exit code 10.** Calling `+delete`, `+delete-reply`, `+push --delete-remote` etc. without `--yes` exits `10` with `error.type == "confirmation"` and `subtype == "confirmation_required"`. Show `error.action` and `error.risk` to the user, get explicit approval, then re-run the *original* argv with `--yes` appended. Never auto-append `--yes`, and never treat this as a network or permission error. `--dry-run` previews without tripping the gate.
- **Vague deletion requests are not confirmations.** "Delete the useless files" only states a goal. List resolvable candidates with `+search` / `+inspect`, explain the filter, and stop for confirmation; heuristics like open time or title patterns can shortlist but never authorize.
- **Concurrent imports to the same destination collide.** Same `--folder-token`, same default root, or same `--target-token` must run serially. `232140101` / `232140100` / `233523001` in the error or `job_error_msg` means exactly this: serialize, wait a few seconds, retry at most 3 times, then report.
- **Copying a document uses the native copy API,** not export + import and not fetch + create. Resolve wiki sources with `+inspect` first so `params.file_token` is the real underlying token.
- **Polling timeout is not failure.** `+export` / `+import` / `+delete` may return `ready=false`, `timed_out=true`, a `ticket` or `task_id`, and a `next_command`; continue with `+task_result --scenario import|export|task_check`. Conversely a `deleted=true` with no `next_command` is already done, and a `task_id` alone is not a success signal.
- **File paths must be cwd-relative.** `--file`, `--output`, `--output-dir`, `--local-dir` and `@file` inputs reject absolute paths with `unsafe file path`.
- **Bots cannot see a user's personal space.** Use `--as user` for "my space" work. When `--as bot` creates or uploads something, the CLI tries to grant the current CLI user `full_access` and reports `permission_grant` (`granted` / `skipped` / `failed`); an overwrite via `--file-token` deliberately does not touch permissions. Never transfer ownership without separate confirmation. The version commands support both identities, so automation should prefer `--as bot`.
- **`drive:drive` is disabled by policy in some tenants.** That is why `+push` / `+pull` / `+status` declare only fine-grained scopes; do not "fix" a missing scope by asking for the broad one.
- **`--query` is for real keywords only.** Action or aggregation words ("all documents", "statistics", "recently updated") over-constrain the search — use `--query ""` plus filters instead.
- **`total` in search results is unreliable** (officially acknowledged). Count deduplicated `results` across pages instead. Highlight fields `title_highlighted` / `summary_highlighted` may contain `<h>` / `<hb>` tags that must be stripped before comparison.
- **`--opened-*` windows are capped at 90 days server-side.** 91-365 days are auto-narrowed to the most recent 90-day slice with a stderr notice listing the remaining slices; over 365 days is a validation error. `--page-token` is only valid inside one slice, and you must use that slice's literal timestamps, not relative values like `1y`, or the token binds to a drifting window.
- **`+permission-get-setting` does not recurse.** `--type folder` reads that folder's own settings only, never its children.
- **A missing field in a member response is not an empty value.** Field-level permission gaps make the server omit fields while still returning success; `name` / `avatar` additionally need `contact:user.base:readonly`.
- **`99992351` on search is a contact-visibility problem,** not a missing `search:docs:read` scope — the `open_id` is outside the app's address-book visibility.
- **`403` on `+download` is often recoverable** via `+preview` to fetch a rendition instead.
- **Judge success by `ok == true` or the exit code, never `code == 0`.** This matters most for wrapped write commands, where a false negative can bypass idempotency logic and duplicate resources.
- **Batch deletes and moves should be serial.** Concurrency triggers server-side locking and partial failures that need per-item retries.

## Permissions

| Operation | Scope |
|---|---|
| Folder / metadata listing, `+inspect` | `drive:drive.metadata:readonly` |
| `+download`, `+preview`, `+cover`, `+version-history`, `+version-get` | `drive:file:download` |
| `+upload`, `+version-revert`, `+version-delete` | `drive:file:upload` (+ `drive:drive.metadata:readonly`) |
| `+create-folder` | `space:folder:create` |
| `+move` | `space:document:move` |
| `+create-shortcut` | `space:document:shortcut` |
| `+delete` | `space:document:delete` + `drive:drive.metadata:readonly` |
| `+push` | `drive:drive.metadata:readonly` + `drive:file:upload` + `space:folder:create`; `--delete-remote --yes` additionally pre-checks `space:document:delete` |
| `+pull` | `drive:drive.metadata:readonly` + `drive:file:download` |
| `+export` | `docs:document.content:read` + `docs:document:export` + `docx:document:readonly` + `drive:drive.metadata:readonly` |
| `+export-download` | `docs:document:export` |
| `+import` | `docs:document.media:upload` + `docs:document:import` |
| `+search` | `search:docs:read` |
| `+member-list` | `docs:permission.member:retrieve` (+ `contact:user.base:readonly` for `name` / `avatar`) |
| `+member-add` | `docs:permission.member:create` |
| `+apply-permission` | `docs:permission.member:apply` |
| `+permission-get-setting` | `docs:permission.setting:read` |
| `+secure-label-list` / `+secure-label-update` | `docs:secure_label:readonly` / `docs:secure_label:write_only` |
| Comment read / create / write | `docs:document.comment:read`, `docs:document.comment:create`, `docs:document.comment:write_only` |
| `+add-comment` (full set) | `drive:drive.metadata:readonly` + `docx:document:readonly` + `docs:document.comment:create` + `docs:document.comment:write_only` |
| Wiki resolution on the way in | `wiki:node:read` / `wiki:node:retrieve` |

## Examples

```bash
# Always resolve an ambiguous or wiki URL before acting on it
lark-cli drive +inspect --as user --url 'https://xxx.feishu.cn/wiki/<WIKI_NODE_TOKEN>' --format json

# Filter-only browse: docs I own, created in an explicit calendar month
lark-cli drive +search --as user --query "" --mine \
  --created-since 2026-03-01 --created-until 2026-04-01 --doc-types docx --format json

# Keyword plus recency, sorted by edit time
lark-cli drive +search --as user --query "预算" --opened-since 7d --sort edit_time --format json

# Upload into a folder, then overwrite the same file in place later
lark-cli drive +upload --as user --file ./report.pdf --folder-token <FOLDER_TOKEN> --name "Q1 report.pdf"
lark-cli drive +upload --as user --file ./report.pdf --file-token <EXISTING_FILE_TOKEN>

# Export a doc to PDF by URL, letting the CLI infer type and token
lark-cli drive +export --as user --url "https://xxx.feishu.cn/docx/<TOKEN>" \
  --file-extension pdf --file-name "weekly-report.pdf" --output-dir ./exports

# If polling timed out, continue with the returned ticket, then download
lark-cli drive +task_result --as user --scenario export --ticket "<TICKET>" --file-token "<DOC_TOKEN>"
lark-cli drive +export-download --as user --file-token "<EXPORTED_FILE_TOKEN>" --output-dir ./exports

# Import a spreadsheet as a Base (serial when several go to the same folder)
lark-cli drive +import --as user --file ./crm.xlsx --type bitable \
  --folder-token <FOLDER_TOKEN> --name "客户台账"

# Read one resource's own sharing settings and its collaborator list
lark-cli drive +permission-get-setting --as user --token '<FOLDER_TOKEN>' --type folder --format json
lark-cli drive +member-list --as user --token '<DOCX_TOKEN>' --type docx \
  --fields 'name,type,external_label' --format json

# Preview a destructive delete first, then execute only after the user agrees
lark-cli drive +delete --as user --file-token <FILE_TOKEN> --type file --dry-run
lark-cli drive +delete --as user --file-token <FILE_TOKEN> --type file --yes

# Compare a local directory against a Drive folder before pushing
lark-cli drive +status --as user --local-dir ./docs --folder-token <FOLDER_TOKEN> --format json
lark-cli drive +push --as user --local-dir ./docs --folder-token <FOLDER_TOKEN> --if-exists smart
```
