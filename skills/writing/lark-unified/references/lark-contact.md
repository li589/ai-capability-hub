# Contact — resolving people and bots to IDs

Owns directory lookups: turning a name / email / phone into an `open_id`, reading a profile back from an `open_id` (name, department, email, contact details), and searching the bots / agents visible to the current user. Does **not** own department-tree traversal, listing employees by department or org-chart work (native OpenAPI), sending messages (im domain) or scheduling (calendar domain) — if you already have an `open_id` and only need to message or invite someone, skip contact entirely.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+search-user` | `--query`, `--queries`, `--user-ids`, `--has-chatted`, `--has-enterprise-email`, `--exclude-external-users`, `--left-organization`, `--lang`, `--page-size` | Search employees by name / email / phone, or hydrate known `open_id`s (user identity only) |
| `+get-user` | `--user-id` (omit for self), `--user-id-type` | Read one user's profile; the only path available to a bot |
| `+search-bot` | `--query`, `--queries`, `--chat-ids`, `--has-chatted`, `--page-size` | Search bots / agents visible to the current user (user identity only) |

## Key parameters

**`--query` vs `--queries`** — `--query` is a single keyword; `--queries` takes a comma-separated list and fans out one search per term (`--queries 'alice,bob,张三'`), which is the right way to resolve several names in one call instead of looping.

**`--user-ids` on `+search-user`** — a comma-separated list of user `open_id`s used as a hydration path (pass `me` for the current user). This is how a **user** identity reads someone else's profile; `--query` may be omitted when a filter such as `--user-ids` or `--has-chatted` is supplied.

**`--user-id` / `--user-id-type` on `+get-user`** — `--user-id-type` is `open_id` (default), `union_id` or `user_id`. Omitting `--user-id` means "current user" and is only valid under user identity — a bot must pass an explicit `--user-id`.

**Filters** — `--has-chatted` narrows to people (or bots) the caller has actually talked to and sharply improves precision on common names; `--exclude-external-users` drops guests from other tenants; `--has-enterprise-email` keeps only accounts with a corporate mailbox; `--left-organization` includes departed employees. `--lang` (e.g. `zh_cn`, `en_us`) overrides the locale of `localized_name`.

**`--chat-ids` on `+search-bot`** — restricts the bot search to specific chats. `+search-bot` cannot look up a bot by ID; it only searches by keyword and returns bot `open_id`s (also `ou_`-prefixed).

## Gotchas

- **User and bot are two separate paths.** `+search-user` and `+search-bot` are `AuthTypes: user` only — a bot token cannot search the directory at all. Under bot identity the sole option is `+get-user --user-id <id>`. Pass `--as user` explicitly for anything search-shaped.
- **No auto-pagination.** These commands honour `--page-size` but do not accept `--page-all`. When the result carries `has_more=true`, add filters or tighten `--query` rather than expecting more pages.
- **A name does not tell you the type.** "Set up a meeting with reviewDuck" could mean a colleague or a bot. When the name contains bot / agent / AI / assistant / 助手 / 机器人 / 智能体, search bots first; when genuinely unsure, run both.
- **Never auto-pick the first hit.** If a search returns multiple candidates and the next step has side effects (sending a message, inviting to a meeting), present the candidate list and let the user choose.
- **`41050` / permission denied is a visibility limit**, not necessarily a missing scope: all three commands are bounded by what the current identity is allowed to see in the directory.
- **Cross-tenant users come back mostly empty.** With `is_cross_tenant=true` most business fields are empty strings by Lark's visibility rules — handle null/empty downstream instead of treating it as an error.
- **Personal status / signature is not a shortcut.** Batch-query them through the native API (`lark-cli schema contact.user_profiles.batch_query`, then `lark-cli contact user_profiles batch_query --params ... --data ... --as user`), and reach for the OpenAPI explorer for department trees.

## Permissions

| Command | Scopes |
|---|---|
| `+search-user` | `contact:user:search` (user identity) |
| `+search-bot` | `search:bot` (user identity) |
| `+get-user` | user identity: `contact:user.basic_profile:readonly` · bot identity: `contact:user.base:readonly` + `contact:contact.base:readonly` |

## Output and conventions

Output format is only `--format json|pretty|table|ndjson|csv` — there is no separate `--table`, `--csv`, `--yaml` or `--raw`. Identity is `--as user|bot|auto`; because directory search is a personal-visibility resource, always pass `--as user` explicitly instead of relying on `auto`. Success is `ok == true` or the exit code, not `code == 0`. All three commands are read-only, so `--yes` and the exit-code-10 confirmation flow do not apply here.

## Examples

```bash
# Resolve a colleague, then message them (contact is only the lookup step)
lark-cli contact +search-user --as user --query "张三" --has-chatted --format json
lark-cli im +messages-send --as user --user-id ou_xxx --text "Hi!"

# Disambiguate a common name: internal accounts you have actually chatted with
lark-cli contact +search-user --as user --query "李伟" \
  --has-chatted --exclude-external-users --format json

# Resolve several names in one call instead of looping
lark-cli contact +search-user --as user --queries "alice,bob,张三" --page-size 20 --format json

# Hydrate known open_ids (user identity), including yourself
lark-cli contact +search-user --as user --user-ids "ou_xxx,ou_yyy,me" --format json

# Bot identity can only read a specific profile, never search
lark-cli contact +get-user --as bot --user-id ou_xxx --user-id-type open_id --format json

# Look up your own profile, and read someone by union_id
lark-cli contact +get-user --as user --format json
lark-cli contact +get-user --as user --user-id on_xxx --user-id-type union_id --format json

# Search bots / agents by keyword, single and fanned out
lark-cli contact +search-bot --as user --query "会议助手" --format json
lark-cli contact +search-bot --as user --queries "会议助手,日报助手,审批助手" --format json

# Personal status / signature is native API only
lark-cli schema contact.user_profiles.batch_query
lark-cli contact user_profiles batch_query --as user \
  --params '{"user_id_type":"open_id"}' \
  --data '{"user_ids":["ou_xxx"],"query_option":{"include_personal_status":true,"include_description":true}}'
```
