# Docs — Docx content read and write

Owns the body of a Lark Docx (and Wiki URLs that resolve to a Docx): reading content as XML/Markdown, creating documents, precise block-level and string-level edits, media insert/download/preview, cover resources, and version history with revert. Does **not** own comments, file/folder management, permissions, sheet cells or Base records — those belong to the Drive domain and the sheets/base domains.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+fetch` | `--doc`, `--doc-format`, `--detail`, `--scope`, `--start-block-id`, `--end-block-id`, `--keyword`, `--max-depth`, `--context-before`, `--context-after`, `--revision-id` | Read a document, whole or partial |
| `+create` | `--content`, `--title`, `--doc-format`, `--parent-token`, `--parent-position`, `--reference-map` | Create a Docx from XML or Markdown |
| `+update` | `--doc`, `--command`, `--content`, `--pattern`, `--block-id`, `--src-block-ids`, `--doc-format`, `--revision-id` | Eight edit instructions, string or block level |
| `+media-insert` | `--doc`, `--from-clipboard` / `--file`, `--type`, `--align`, `--caption`, `--width`, `--height` | Append an image or file at the document end |
| `+media-download` | `--token`, `--output`, `--type`, `--overwrite` | Download a media asset or a whiteboard thumbnail |
| `+media-preview` | `--token`, `--output`, `--overwrite` | Preview a media asset (not whiteboards) |
| `+media-upload` | `--file`, `--doc-id`, `--parent-type`, `--parent-node` | Upload a media asset and get its `file_token` |
| `+resource-download` / `+resource-update` / `+resource-delete` | `--doc`, `--type cover`, `--file` / `--from-clipboard` / `--url`, `--offset-ratio-x`, `--offset-ratio-y`, `--output` | Manage the Docx cover image |
| `+history-list` | `--doc`, `--page-size`, `--page-token` | List history versions |
| `+history-revert` | `--doc`, `--history-version-id`, `--wait-timeout-ms` | Revert to a history version |
| `+history-revert-status` | `--doc`, `--task-id` | Poll an in-flight revert |
| `+search` | `--query`, `--filter`, `--page-size`, `--page-token` | Search docs / Wiki / sheets (user identity only) |

## Key parameters

**`+fetch`** — `--doc` (required) takes a URL or a bare token, `/docx/` and `/wiki/` both work. `--doc-format` is `xml` (default) / `markdown` / `im-markdown`, where `im-markdown` exists only to hand content off to an IM message. `--detail` is `simple` (default, no block ids) / `with-ids` (block ids, needed for `--block-id` and for `docURL#block_id` deep links) / `full` (ids + styles + reference metadata, use before rewriting). `--scope` is `full` (default, whole doc) / `outline` / `section` / `range` / `keyword` and is orthogonal to `--detail`. `section` requires `--start-block-id`; `range` needs at least one of `--start-block-id` / `--end-block-id` where `-1` means "through the end"; `keyword` takes `--keyword` with `|` as an OR separator and four fallback layers (substring → normalized → tokenized → RE2). `--max-depth` is a heading-level cap under `outline` and a subtree depth elsewhere (`-1` unlimited, `0` block only). `--revision-id` defaults to `-1` (latest).

**`+create`** — `--content` is required unless `--title` is given; it accepts inline text, `@file`, or stdin. `--doc-format` is `xml` (default) or `markdown`. With XML, put the title inside the content as `<title>...</title>`; when `--title` is also passed it is prepended and wins. `--parent-token` (folder or wiki node) and `--parent-position` (e.g. `my_library`) are mutually exclusive.

**`+update`** — `--command` accepts exactly eight values: `str_replace`, `block_insert_after`, `block_copy_insert_after`, `block_replace`, `block_delete`, `block_move_after`, `overwrite`, `append`. Required companions: `str_replace` → `--pattern` + `--content` (empty content deletes); `block_insert_after` / `block_replace` → `--block-id` + `--content`; `block_delete` → `--block-id` (comma-separated for batch); `block_copy_insert_after` / `block_move_after` → `--block-id` + `--src-block-ids`; `overwrite` / `append` → `--content`. `--block-id` accepts `-1` for the document end. `--revision-id` defaults to `-1`.

**`+media-insert`** — `--doc` accepts a document id or a `/docx/<id>` URL only; `/wiki/...` URLs are **not** auto-resolved here. `--from-clipboard` and `--file` are mutually exclusive. `--type` is `image` (default) or `file`; clipboard input only produces images. `--align` is `left` / `center` (default) / `right`. `--width` / `--height` are pixels; give one and the other is derived from the aspect ratio for PNG / JPEG / GIF, but WebP / BMP require both. Files over 20 MB auto-switch to multipart upload.

**`+history-list` / `+history-revert`** — `--page-size` range 1-20, default 20. `--history-version-id` must be > 0 and comes from `+history-list`; passing a `revision_id` there is wrong. `--wait-timeout-ms` range 0-30000, default 30000; `0` fires the task without waiting. Terminal statuses are `done`, `partial_failed`, `failed`; only `done` is success.

## Gotchas

- **`--scope` here is a read-range flag, not an OAuth scope.** Local reads beat full reads: prefer `outline` → `section`, or `keyword`, and only omit `--scope` when the whole document is genuinely needed.
- **`<excerpt>` means you are looking at a slice.** Partial reads wrap content in `<fragment>`; a child `<excerpt top-block-id="..." parent-block-path="...">` is a container or table slice, never the full top-level block. Tables are slimmed by default to `thead` + matching rows — use `range --start-block-id <table-id> --end-block-id <table-id>` for the whole table.
- **Block ids expire after writes.** After `overwrite` / `block_replace` / `block_delete` the affected ids are dead; after `block_insert_after` / `append` / `block_copy_insert_after` the anchor survives but new content has new ids; after `block_move_after` the id survives but position/section/range semantics shift. Re-fetch before chaining another block-level edit.
- **`str_replace` match range depends on format.** In XML mode `--pattern` is inline-only and cannot cross blocks or paragraphs — use `block_replace` instead. In `--doc-format markdown` it can match multiline text and also supports `prefix...suffix` ellipsis matching, where everything between the two anchors is replaced.
- **The same block can only be replaced once per call.** Merge multiple edits to one block into a single `block_replace`.
- **`overwrite` is destructive.** It clears and rebuilds the body, regenerates block ids, and can lose images and comments. Prefer `block_insert_after` + `block_delete` for restructuring.
- **`append` is not "fill in chapter by chapter".** It is equivalent to `block_insert_after --block-id -1`; per-section writing needs `block_insert_after` with that heading's `--block-id`.
- **Markdown carries no block ids and no styling** (colors, alignment, callouts). For precise edits stay on XML, the default; do not switch to Markdown just because it is easier to type.
- **Local file paths must be cwd-relative.** `--file ./image.png`, `--output ./asset.png`, `@content.xml` are fine; absolute paths are rejected as `unsafe file path`. Prefer stdin for large JSON/XML payloads.
- **`--markdown` image syntax with local paths never uploads.** In documents, `<img href="https://...">` can be inserted directly via `+update`; local files go through `+media-insert` or `+media-upload`.
- **`+media-preview` cannot handle whiteboards.** Whiteboard thumbnails require `+media-download --type whiteboard`. On `HTTP 403` for a normal asset, try `+media-preview` before giving up.
- **`+update` cannot edit an existing whiteboard's content** — it can only add new whiteboard blocks. Editing existing boards is a whiteboard-domain job using the `<whiteboard token="...">` value.
- **Embedded sheets and Bases are opaque here.** `<sheet token=... sheet-id=...>`, `<bitable token=... table-id=...>` and `<cite file-type="sheets|bitable">` must be handed to the sheets/base domains by token; do not present the raw tag as the answer.
- **Docs default to `--as user`.** A bot cannot see a user's personal docs, and a doc created with `--as bot` is owned by the bot; the CLI then tries to grant the current CLI user `full_access` and reports it in `permission_grant` (`granted` / `skipped` / `failed`). Never transfer ownership without a separate confirmation.
- **`+create` with `--as bot` in a wiki context may return a `/wiki/...` URL.** Pass the returned `document_id`, not that URL, to `+media-insert`.
- **Copying a document is not a Docs operation.** Do not rebuild the body with `+fetch` + `+create`, and do not round-trip through export/import — use the Drive copy path.
- **Judge success by `ok == true` or the exit code, never `code == 0`.** Also check `result` (`success` / `partial_success` / `failed`) and `warnings` on write responses.
- **Keep `content` and `reference_map` together.** `reference_map` is the structured sidecar for in-body references; when replaying content, pass it back via `--reference-map`.

## Permissions

| Operation | Scope |
|---|---|
| `+fetch`, `+history-list`, `+history-revert-status` | `docx:document:readonly` |
| `+update`, `+history-revert` | `docx:document:write_only` + `docx:document:readonly` |
| `+create` | `docx:document:create` |
| `+media-insert` | `docs:document.media:upload` + `docx:document:write_only` + `docx:document:readonly` |
| `+media-upload` | `docs:document.media:upload` |
| `+media-download`, `+media-preview` | `docs:document.media:download` |
| `+resource-download --type cover` | `docx:document:readonly` + `docs:document.media:download` |
| `+resource-update --type cover` | `docx:document:readonly` + `docx:document:write_only` + `docs:document.media:upload` |
| `+resource-delete --type cover` | `docx:document:readonly` + `docx:document:write_only` |
| `+search` | `search:docs:read` |
| Wiki URL resolution on the way in | `wiki:node:read` / `wiki:node:retrieve` |

## Choosing `--scope` and `--detail`

Pick `--detail` by intent: `simple` to read or summarize, `with-ids` when you need block ids to edit or to build a `docURL#block_id` link, `full` when faithfully rewriting existing content.

Pick `--scope` by the shape of the request, in this order:

1. The user names a concrete term, error code or identifier → `keyword` directly; widen later with the returned `top-block-id` via `section` / `range`.
2. The user points at a chapter or heading ("rewrite section 3", "summarize the XX part") → `outline --max-depth 3` first, then `section --start-block-id <heading id>`.
3. You already know exact endpoints or need a continuous cross-section span → `range`.
4. Structure unknown and no keyword clue → `outline` to probe, then back to step 2 or 3.
5. Only omit `--scope` when the whole document is genuinely required.

`outline` flattens every heading including ones nested inside containers such as callouts, and those ids are valid anchors for `section` / `range`. `--context-before` / `--context-after` apply only to whole top-level units — when a hit lands inside a container or table the slice is returned and the context flags are ignored, so widen with `section` / `range` instead.

## Handling embedded assets

Document content surfaces assets as XML tags: `<img token="..." url="..."/>`, `<source token="..." url="..." name="..."/>`, `<whiteboard token="..."/>`. When a `url` attribute is present, a plain HTTP GET is enough and no shortcut is needed. Without a `url`, or when previewing, use `+media-preview --token <token>`; for an explicit download, or for any whiteboard, use `+media-download`. Cover images are not body assets — they only go through `+resource-download` / `+resource-update` / `+resource-delete --type cover`.

## Examples

```bash
# Cheap structural probe before touching anything
lark-cli docs +fetch --as user --doc "https://xxx.feishu.cn/docx/<TOKEN>" \
  --scope outline --max-depth 3 --format json

# Read exactly one section, with block ids for the follow-up edit
lark-cli docs +fetch --as user --doc "<TOKEN>" \
  --scope section --start-block-id <HEADING_BLOCK_ID> --detail with-ids --format json

# Locate content by synonyms (OR branches) with one sibling block of context
lark-cli docs +fetch --as user --doc "<TOKEN>" \
  --scope keyword --keyword "部署|发布|上线" --context-before 1 --context-after 1 --detail with-ids

# Create an XML document under a specific folder
lark-cli docs +create --as user --parent-token <FOLDER_TOKEN> \
  --content '<title>Release plan</title><h1>Goals</h1><p>Ship v2 this week.</p>'

# Inline replacement, no block ids needed
lark-cli docs +update --as user --doc "<TOKEN>" --command str_replace \
  --pattern "v1.0" --content "v2.0"

# Replace one block with rebuilt XML
lark-cli docs +update --as user --doc "<TOKEN>" --command block_replace \
  --block-id blkcnXXXX --content '<h2>Rollout</h2><ul><li>Stage 1</li><li>Stage 2</li></ul>'

# Batch delete stale blocks
lark-cli docs +update --as user --doc "<TOKEN>" --command block_delete \
  --block-id "blkcnA,blkcnB,blkcnC"

# Insert a screenshot straight from the clipboard, centered with a caption
lark-cli docs +media-insert --as user --doc <DOCUMENT_ID> --from-clipboard \
  --align center --caption "架构图" --width 800

# Revert to a history version, then confirm the terminal status
lark-cli docs +history-list --as user --doc "<TOKEN>" --page-size 20 --format json
lark-cli docs +history-revert --as user --doc "<TOKEN>" --history-version-id 42
```
