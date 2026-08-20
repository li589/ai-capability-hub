# IM — messages, chats, threads, reactions, feed

Owns everything inside a conversation: sending and replying to messages, reading chat/thread history, searching messages, listing chat members, downloading message resources, and managing the caller's own bookmarks (flags) and feed shortcuts/groups. Does **not** own document content, Drive files, or permissions on cloud docs — a message that links to a doc is IM, the doc body is not.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+messages-send` | `--chat-id` / `--user-id`, `--text` / `--markdown` / `--content`, `--image` / `--file` / `--video` + `--video-cover` / `--audio`, `--msg-type`, `--idempotency-key` | Send to a group or a DM |
| `+messages-reply` | `--message-id`, same content flags, `--reply-in-thread`, `--idempotency-key` | Reply to one message, optionally inside its thread |
| `+chat-messages-list` | `--chat-id` / `--user-id`, `--start`, `--end`, `--order`, `--page-size`, `--page-all`, `--no-reactions`, `--download-resources` | Read a conversation's history |
| `+threads-messages-list` | `--thread`, `--order`, `--page-size`, `--page-all`, `--download-resources` | Read replies under one thread |
| `+messages-mget` | `--message-ids`, `--no-reactions`, `--download-resources` | Batch fetch up to 50 `om_` ids |
| `+messages-search` | `--query`, `--chat-id`, `--sender`, `--sender-type`, `--exclude-sender-type`, `--is-at-me`, `--at-chatter-ids`, `--include-attachment-type`, `--chat-type`, `--start`, `--end`, `--page-all` | Cross-chat message search (user identity only) |
| `+messages-resources-download` | `--message-id`, `--file-key`, `--type`, `--output` | Pull one image/file binary out of a message |
| `+chat-search` | `--query`, `--member-ids`, `--search-types`, `--chat-modes`, `--is-manager`, `--sort`, `--exclude-muted`, `--page-all` | Resolve `chat_id` from a group name |
| `+chat-list` | `--types`, `--sort-by`, `--exclude-muted`, `--page-all` | List chats the caller belongs to |
| `+chat-members-list` | `--chat-id`, `--member-types`, `--member-id-type`, `--page-all`, `--page-limit`, `--page-delay` | List `users[]` / `bots[]` of a chat |
| `+chat-create` | `--name`, `--description`, `--chat-mode`, `--users`, `--bots`, `--owner`, `--set-bot-manager` | Create a group or topic chat |
| `+chat-update` | `--chat-id`, `--name`, `--description` | Rename / re-describe a group |
| `+flag-create` / `+flag-cancel` / `+flag-list` | `--message-id`, `--flag-type`, `--page-all`, `--page-limit` | Bookmark messages/threads (user only) |
| `+feed-shortcut-create` / `+feed-shortcut-remove` / `+feed-shortcut-list` | `oc_` chat ids, `--head` / `--tail`, `--page-token`, `--no-detail` | Pin chats to the feed sidebar (user only) |
| `+feed-group-list` / `+feed-group-list-item` / `+feed-group-query-item` | `--page-all` | Read feed groups (tags) and their members (user only) |

## Key parameters

**`+messages-send` / `+messages-reply`** — exactly one target (`--chat-id` for `oc_xxx`, `--user-id` for a DM `ou_xxx`) and exactly one content flag. `--text`, `--markdown`, `--content` and the media flags are mutually exclusive, and the media flags are mutually exclusive with each other. `--markdown` always forces `msg_type=post` (single `zh_cn` locale, no post title); use `--msg-type post --content` when you need a title or multiple locales. `--idempotency-key` is max 50 chars and dedupes for 1 hour. `--msg-type` accepts `text` / `post` / `image` / `file` / `audio` / `media` / `share_chat` / `share_user` / `interactive`, but is inferred from the content flag — setting a conflicting value fails validation.

**`+chat-messages-list`** — `--chat-id` XOR `--user-id`. `--start` / `--end` accept ISO 8601 or date-only (`2026-03-10`). `--order` is `asc` | `desc` (default `desc`) and is the *only* sort axis — there is no sort-by-sender. `--page-size` default 50, max 50. `--page-all` is capped by `--page-limit` (default 10, range 1-1000).

**`+messages-search`** — `--page-size` default 20, range 1-50; `--page-all` caps at 40 pages, `--page-limit` default 20 / max 40, and setting it alone already enables auto-pagination. `--include-attachment-type` is `file` / `image` / `video` / `link`; `--chat-type` is `group` / `p2p`; `--sender-type` and `--exclude-sender-type` are `user` / `bot`. `--start` / `--end` require an explicit timezone offset, e.g. `2026-03-24T00:00:00+08:00`.

**`+chat-search`** — at least one of `--query` (max 64 chars) or `--member-ids` (up to 50 `ou_xxx`). `--search-types` takes `private` / `external` / `public_joined` / `public_not_joined`; `--chat-modes` takes `group` / `topic`. `--sort` accepts `create_time` / `update_time` / `member_count` and is **always descending** — do not pass `asc` or invent `member_count_asc`. `--page-size` 1-100 default 20.

**`+chat-members-list`** — `--chat-id` required. `--member-types` is `user` / `bot`; `--member-id-type` is `open_id` (default) / `union_id` / `user_id`. `--page-size` 1-100 default 20; with `--page-all` and no explicit `--page-size` the CLI uses 100. `--page-limit` default 10 where `0` means unlimited, `--page-delay` default 200 ms where `0` disables throttling.

**`+messages-resources-download`** — `--message-id`, `--file-key` and `--type` (`image` | `file`) are all required. `--output` is optional; extension is inferred from `Content-Disposition` / `Content-Type`. Large files download via 8 MB HTTP Range chunks after a 128 KB probe.

## Gotchas

- **Sender names come from the server, not from contacts.** Read commands surface `sender_name` / `sender_i18n_names` as `name` for users and bots alike. No contact scope and no `application:bot.basic_info:read` are needed. When the server sends no name, the id is shown and the command still exits 0 — there is no contact-directory fallback. `msg_type: system` messages have no sender name; that is normal.
- **`--download-resources` is off by default.** Without it you only get resource markers (`![Image](img_xxx)`, `<audio key="file_xxx" .../>`) and zero extra requests. With it, eligible resources land in `./lark-im-resources/` and each message gains a `resources` array. Stickers are never downloadable.
- **`--video` must be paired with `--video-cover`,** and `--video-cover` cannot be used alone. Omitting the cover is a validation failure, not a server error.
- **File paths must be cwd-relative.** `--image ./photo.png` works; `/tmp/photo.png` is rejected as `unsafe file path`. Copy the file into the working directory or run from its directory. This also applies to `--output`.
- **`--markdown` does not upload local images.** `![x](./a.png)` silently fails to render. Pre-upload with `im images create --data '{"image_type":"message"}' --file ./x.png` and reference the returned `img_xxx`. Remote `https://` URLs are resolved at runtime but dropped with a warning if download/upload fails.
- **`--audio` is Opus-only** (`.opus` or Ogg Opus `.ogg`). Send mp3/wav as `--file` instead, or convert first.
- **User vs bot changes the answer, not just the token.** `--as user` uses UAT and is checked against that person's chat membership; `--as bot` uses TAT and is checked against bot membership, app visibility and availability range. The same API can succeed under one identity and fail under the other. `+messages-search`, all `+flag-*`, all `+feed-*` are **user only**. `--user-id` on `+chat-messages-list` needs `--as user`, because p2p resolution is UAT-only. `--exclude-muted` is silently inactive under `--as bot`.
- **The default identity is resolved from config, not hardcoded to bot.** Always pass `--as user` explicitly when touching personal resources (DMs, flags, feed shortcuts, message search).
- **Member lists can be truncated server-side.** A non-empty `truncations[]` (e.g. `[{"limit":100,"member_type":"user"}]`) means the list is incomplete and paging further will not fix it.
- **Judge success by `ok == true` or the exit code, never `code == 0`.** Success envelopes have no top-level `code`; `code` only exists inside an error envelope.
- **Reactions are attached automatically** to the four message-pulling shortcuts, plus `update_time` on edited messages. Pass `--no-reactions` to skip the extra round-trip and its scope requirement.
- **Do not fall back to `+chat-list` when `+chat-search` returns nothing.** The list API has no keyword filter; ask the user to refine the keyword instead.
- **Never hand-write interactive card JSON.** Card payloads for `--msg-type interactive --content` must come from the official card-creation workflow.
- **Error codes 234002 / 14005 on resource download mean no access or a deleted file,** not a missing scope. Do not retry.

## Permissions

| Operation | Scope |
|---|---|
| Read messages (`+chat-messages-list`, `+messages-mget`, `+threads-messages-list`, `+messages-resources-download`) | `im:message:readonly` |
| Read as user, group / p2p history | `im:message.group_msg:get_as_user`, `im:message.p2p_msg:get_as_user` |
| Read as bot, group / p2p history | `im:message.group_msg`, `im:message.p2p_msg:readonly` |
| Reaction enrichment on read commands | `im:message.reactions:read` |
| Send / reply as bot | `im:message:send_as_bot` |
| Send / reply as user | `im:message.send_as_user` + `im:message` |
| Message search | `search:message` (+ `im:message.reactions:read` for enrichment) |
| Chat read / search / list | `im:chat:read` |
| Chat member list | `im:chat.members:read` |
| Create chat (user / bot) | `im:chat:create_by_user` / `im:chat:create` |
| Update chat | `im:chat:update` |
| Add / remove members, managers | `im:chat.members:write_only`, `im:chat.managers:write_only` |
| Reactions write / read | `im:message.reactions:write_only`, `im:message.reactions:read` |
| Pins | `im:message.pins:write_only`, `im:message.pins:read` |
| Recall a message | `im:message:recall` |
| Urgent app / phone / sms | `im:message.urgent`, `im:message.urgent:phone`, `im:message.urgent:sms` |
| Upload image resource | `im:resource` |
| Flags (bookmarks) | `im:feed.flag:read`, `im:feed.flag:write` |
| Feed shortcuts | `im:feed.shortcut:read`, `im:feed.shortcut:write` |
| Feed groups (tags) | `im:feed_group_v1:read`, `im:feed_group_v1:write` |

## Native API fallback

When no shortcut covers the operation, run `lark-cli schema im.<resource>.<method>` **first** to read the `--data` / `--params` structure, then `lark-cli im <resource> <method>`. Identity limits are real and differ per method:

| Resource.method | Identity | Note |
|---|---|---|
| `images.create` | bot only | Upload an image to get `img_xxx`; needed before `--markdown` image references |
| `messages.delete` | user + bot | Recall; a bot must be in the chat, and needs owner/admin/creator status to recall someone else's |
| `messages.forward` / `threads.forward` | user + bot | Forward one message or a whole thread |
| `messages.merge_forward` | bot only | Merge-forward several messages |
| `messages.read_users` | bot only | Read receipts, own messages only, last 7 days |
| `messages.urgent_app` / `urgent_phone` / `urgent_sms` | bot only | Bot must be the sender and in the conversation |
| `reactions.create` / `delete` / `list` / `batch_query` | user + bot | Deleting is limited to reactions the caller added |
| `pins.create` / `delete` / `list` | user + bot | Chat pins |
| `chats.create` / `get` / `link` / `update` | `create` bot only; rest user + bot | `link` needs owner/admin when sharing is restricted |
| `chat.members.create` / `delete` | user + bot | Max 50 users or 5 bots per request |
| `chat.managers.add_managers` / `delete_managers` | user + bot | Owner only; max 10 managers per chat, 5 bots per request |
| `chat.moderation.get` / `update` | user + bot | Update is owner-only |
| `chat.nickname.get` / `update` / `delete` | user only | Self only; nickname max 300 bytes |
| `chat.user_setting.batch_query` / `batch_update` | user only | Up to 10 chats per request (`is_muted`, `is_mute_at_all`) |
| `feed.groups.*` | user only | Feed group CRUD and member batch add/remove |

## Examples

```bash
# Resolve a chat by name, then read the last page of its history
lark-cli im +chat-search --as user --query "design review" --format json
lark-cli im +chat-messages-list --as user --chat-id oc_xxx --order desc --page-size 50 --format json

# Read a date range and download every attachment into ./lark-im-resources/
lark-cli im +chat-messages-list --as user --chat-id oc_xxx \
  --start 2026-03-10 --end 2026-03-11 --download-resources --format json

# Weekly-report sweep: no keyword, filter by sender and time, drain all pages
lark-cli im +messages-search --as user --query "" --chat-id oc_xxx --sender ou_me \
  --start "2026-03-18T00:00:00+08:00" --end "2026-03-25T23:59:59+08:00" \
  --page-size 50 --page-all --format json

# Send a formatted update as the logged-in user
lark-cli im +messages-send --as user --chat-id oc_xxx --markdown $'## Status\n\n- build green\n- deploy pending'

# Send exact plain text (logs, code) — no Markdown conversion
lark-cli im +messages-send --as user --chat-id oc_xxx --text $'```bash\nmake test\nmake lint\n```'

# Send a video with its mandatory cover, both cwd-relative
lark-cli im +messages-send --as bot --chat-id oc_xxx --video ./demo.mp4 --video-cover ./cover.png

# Reply inside the thread, with an idempotency key
lark-cli im +messages-reply --as user --message-id om_xxx --text "Taking a look" \
  --reply-in-thread --idempotency-key review-ack-2026-03-20

# Drain a large member list without hammering the API
lark-cli im +chat-members-list --as user --chat-id oc_xxx \
  --member-types user --page-all --page-limit 0 --page-delay 200 --format json

# Pull one image binary out of a message
lark-cli im +messages-resources-download --as user --message-id om_xxx \
  --file-key img_v3_xxx --type image --output ./diagram.png
```
