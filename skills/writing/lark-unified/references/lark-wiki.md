# Wiki — knowledge spaces, nodes and space members

Owns Lark Wiki structure: listing and creating knowledge spaces, deleting a space, browsing/creating/copying/deleting nodes, resolving a node from a token or a Lark URL, moving nodes inside Wiki, migrating a Drive document into Wiki, moving a node out to Drive, and managing space members and their roles. Also the right owner for `/wiki/` URLs even on non-Feishu hosts (routing follows the URL path pattern and token, not the domain). Does **not** own uploading/downloading files under a node (drive domain, `drive +upload --wiki-token`), editing document/spreadsheet/Base content (doc / sheets / base domains), or searching documents by name plus comments and permissions (drive domain).

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+space-list` | `--page-size`, `--page-token`, `--page-all`, `--page-limit` | List spaces visible to the caller; source of numeric `space_id` |
| `+space-create` | `--name` (required), `--description` | Create a space (**user identity only**) |
| `+delete-space` | `--space-id`, `--yes` | Delete a space; polls the async task (high-risk write) |
| `+node-list` | `--space-id`, `--parent-node-token`, `--page-size`, `--page-token`, `--page-all`, `--page-limit` | List nodes in a space or under a parent node |
| `+node-get` | `--node-token` (alias `--token`), `--obj-type`, `--space-id` | Resolve a node by node_token / obj_token / Lark URL |
| `+node-create` | `--space-id`, `--parent-node-token`, `--title`, `--node-type`, `--obj-type`, `--origin-node-token` | Create a node or a shortcut node |
| `+node-copy` | `--space-id`, `--node-token`, `--target-space-id`, `--target-parent-node-token`, `--title`, `--yes` | Copy a node into a target space/parent (high-risk write) |
| `+node-delete` | `--node-token`, `--obj-type`, `--space-id`, `--include-children`, `--yes` | Delete a node, polling the async task (high-risk write) |
| `+move` | `--node-token`, `--source-space-id`, `--target-space-id`, `--target-parent-token`, `--obj-type`, `--obj-token`, `--apply` | Move a node inside/across Wiki, or pull a Drive doc into Wiki |
| `+move-to-drive` | `--node-token`, `--folder-token` | Move a node out of Wiki into a Drive folder (async) |
| `+member-add` | `--space-id`, `--member-id`, `--member-type`, `--member-role`, `--need-notification` | Grant a user / chat / department / app access to a space |
| `+member-list` | `--space-id`, `--page-size`, `--page-token`, `--page-all`, `--page-limit` | List space members and their roles |
| `+member-remove` | `--space-id`, `--member-id`, `--member-type`, `--member-role` | Revoke a grant (tuple must match the original) |

## Key parameters

**`--space-id`** — the numeric space ID, or the literal alias `my_library` for the caller's personal document library. Never pass a wiki URL, a node token, a doc token or a space name; `--space-id "https://.../wiki/<token>"` is a common and rejected mistake. Resolve a URL with `lark-cli wiki spaces get_node --params '{"token":"<wiki_token>"}' --format json` and read `data.node.space_id`; resolve a name by walking `+space-list`. `my_library` is per-user and only valid with `--as user` (bot identity errors out explicitly).

**`--node-token`** — for `+node-get` and `+node-delete` it accepts a raw token (`wikcnXXX`, `docxXXX`, …) or a Lark URL such as `https://feishu.cn/wiki/<token>` / `https://feishu.cn/docx/<token>`; URL paths also imply `--obj-type`. For `+move-to-drive` it must be the **wiki node_token**, not the backing document's `obj_token` — check with `+node-get` when unsure. `--token` on `+node-get` is the deprecated original name, kept for compatibility.

**`--obj-type`** — enum differs per command. `+node-create`: `sheet | mindnote | bitable | docx | slides` (default `docx`). `+node-get`: `doc | docx | sheet | bitable | mindnote | slides | file`. `+node-delete`: those plus `wiki`. `+move` (Drive-to-Wiki mode): `doc | sheet | bitable | mindnote | docx | file | slides`.

**`--node-type` / `--origin-node-token`** — `--node-type` is `origin` (default) or `shortcut`. A `shortcut` node **requires** `--origin-node-token`, and passing `--origin-node-token` with a non-shortcut type is rejected. With both `--space-id` and `--parent-node-token` omitted, user identity falls back to `my_library`.

**`--member-type` / `--member-role`** — `--member-type` is one of `openid | userid | email | unionid | openchat | opendepartmentid | appid`; `--member-role` is `admin` or `member`. Both are required on `+member-add` and `+member-remove`. Prefer `openid` for people (resolve via `contact +search-user`), `openchat` for groups (`im +chat-search`), `appid` for apps (`cli_xxx`), `email` when you only have a mailbox. `opendepartmentid` has no shortcut resolver — get `open_department_id` from the native contact department search.

**`+move` vs `+move-to-drive` vs `drive +move`** — moving a node within Wiki: `+move --node-token`. Pulling a Drive document into Wiki: `+move --obj-type --obj-token`. Moving a Wiki node out to a Drive folder or "My Space" root: `+move-to-drive` (omit `--folder-token` for the personal-space root). A source already in Drive: `drive +move`. Treat "my document library" / "personal knowledge base" / `my_library` as a **Wiki** personal library, not the Drive root.

**`--target-space-id` / `--target-parent-node-token`** — `+node-copy` requires **at least one** of them. Omit `--title` to keep the original node title.

## Gotchas

- **Prefer `--as user`.** Spaces and nodes are personal resources, and `--as` defaults to `auto` which frequently resolves to bot — listing the app's spaces instead of the user's. Use `--as bot` only when the user explicitly asks for the application's view.
- **Department members cannot be added as a bot.** `--as bot` maps to a `tenant_access_token`, and that identity may not add space members by `opendepartmentid`. When the target is a department and the user insists on bot identity, stop and explain that the path is impossible — do not silently switch to `--as user`, and do not "try `+member-add` first" to discover the error.
- **`+space-create` is user-only.** The create API rejects a tenant/bot token. `--name` is mandatory, since an unnamed space is nearly impossible to find later.
- **`+space-list` never returns `my_library`.** Resolve the personal library separately with `wiki spaces get --params '{"space_id":"my_library"}'`.
- **Deleting a space needs a human choice.** Even when a name lookup matches exactly one candidate, present `name` + `space_id` + `description` + `space_type` and let the user pick before running `+delete-space --yes`. When matching by name, stop paginating as soon as a page yields an exact match; only fall back to loose matching (trim, case-insensitive, substring) after `has_more=false` with no exact hit. Zero matches → ask the user whether the name is wrong or the caller lacks permission; never invent a different name and retry.
- **`+node-delete` needs care.** Deletion is irreversible; confirm `--node-token` and `--obj-type` with `+node-get` first. When `--space-id` is omitted the CLI auto-resolves it via `get_node`, which additionally needs `wiki:node:retrieve` — pass `--space-id` explicitly if your token only carries `wiki:node:create`.
- **Async writes return a task.** `+delete-space`, `+node-delete`, `+move` (docs-to-wiki) and `+move-to-drive` poll for a bounded window, then print a follow-up `drive +task_result` command / `next_command` — continue with that instead of assuming failure.
- **Moving out of Wiki changes permissions.** `+move-to-drive` removes the node from the Wiki tree and replaces inherited Wiki permissions with the target Drive folder's model. Confirm source and destination first.
- **`+member-remove` must match the original grant.** Revoking a `(member_id, member_type, member_role)` tuple that was never granted is an API error, not a no-op success. Run `+member-list` when in doubt. To change admin ↔ member, remove the old role and then `+member-add` with the new one.
- **List shortcuts fetch one page by default.** `+space-list`, `+node-list` and `+member-list` need an explicit `--page-all` for full enumeration; large knowledge bases can be huge, so keep `--page-limit` in mind.
- **Do not retry-loop on validation errors.** For `invalid_parameters`, `not_found` or `permission_denied` from `+node-list`, fix `--space-id` / `--parent-node-token` / permissions per the hint. Only `rate_limit` deserves a backoff retry.
- **Resolve the member type before calling.** Classify the target as user / chat / department / app first and set `--member-type` accordingly, instead of calling `+member-add` and reverse-engineering the type from the error.
- **Native-API-only areas:** `spaces.get`, `spaces.get_node`, `spaces.list`, `members.list` and friends are available as raw calls (`lark-cli schema wiki.<resource>.<method>` first); the space-member APIs uniformly key on `space_id`, so resolve a URL to `space_id` before touching them.

## Permissions

| Command | Scopes |
|---|---|
| `+space-list` | `wiki:space:retrieve` |
| `+space-create` | `wiki:space:write_only` |
| `+delete-space` | `wiki:space:write_only` + `wiki:space:read` |
| `+node-list` `+node-get` | `wiki:node:retrieve` |
| `+node-create` | `wiki:node:create` + `wiki:node:read` + `wiki:space:read` |
| `+node-copy` | `wiki:node:copy` |
| `+node-delete` | `wiki:node:create` (plus `wiki:node:retrieve` when `--space-id` is omitted) |
| `+move` | `wiki:node:move` + `wiki:node:read` + `wiki:space:read` |
| `+move-to-drive` | `space:document:move` + `wiki:space:read` |
| `+member-add` | `wiki:member:create` |
| `+member-list` | `wiki:member:retrieve` |
| `+member-remove` | `wiki:member:update` |

## Output, pagination and confirmation

Output format is only `--format json|pretty|table|ndjson|csv`; there is no independent `--table`, `--csv`, `--yaml` or `--raw`. Pagination is `--page-all` / `--page-limit` / `--page-delay`, with `--page-size` / `--page-token` on the list shortcuts. Success is `ok == true` or the exit code, not `code == 0`. High-risk writes (`+delete-space`, `+node-delete`, `+node-copy`) run without `--yes` exit with code **10** and `error.type == "confirmation"` — that is a request for user approval, not a failure, and must not be auto-retried with `--yes`.

## Examples

```bash
# Discover space IDs, then list the top level of one space
lark-cli wiki +space-list --as user --page-all --format json
lark-cli wiki +node-list --as user --space-id 7012345678901234567 --page-all --format json

# Drill into a sub-directory of a space
lark-cli wiki +node-list --as user --space-id 7012345678901234567 \
  --parent-node-token wikcnXXXX --page-all --page-delay 200 --format json

# Resolve a Lark URL into node_token / space_id / obj_type before mutating anything
lark-cli wiki +node-get --as user --node-token "https://feishu.cn/wiki/wikcnXXXX" --format json

# Create a docx node under a parent, and a shortcut pointing at an existing node
lark-cli wiki +node-create --as user --space-id 7012345678901234567 \
  --parent-node-token wikcnXXXX --title "Design review" --obj-type docx --format json
lark-cli wiki +node-create --as user --space-id 7012345678901234567 \
  --title "Link to spec" --node-type shortcut --origin-node-token wikcnYYYY --format json

# Create a node in the personal document library (user identity only)
lark-cli wiki +node-create --as user --space-id my_library --title "Scratch notes" --format json

# Copy a node into another space, keeping the original title
lark-cli wiki +node-copy --as user --space-id 7012345678901234567 \
  --node-token wikcnXXXX --target-space-id 7098765432109876543 --yes --format json

# Move a node across spaces, then move another node out to a Drive folder
lark-cli wiki +move --as user --node-token wikcnXXXX \
  --source-space-id 7012345678901234567 --target-space-id 7098765432109876543 --format json
lark-cli wiki +move-to-drive --as user --node-token wikcnZZZZ --folder-token fldcnXXXX --format json

# Grant a user admin rights via email, then audit and revoke a matching tuple
lark-cli wiki +member-add --as user --space-id 7012345678901234567 \
  --member-type email --member-id alice@example.com --member-role admin --need-notification --format json
lark-cli wiki +member-list --as user --space-id 7012345678901234567 --page-all --format json
lark-cli wiki +member-remove --as user --space-id 7012345678901234567 \
  --member-type openid --member-id ou_xxx --member-role member --format json

# Delete a space only after the user picked the space_id from a candidate list
lark-cli wiki +delete-space --as user --space-id 7012345678901234567 --yes --format json
```
