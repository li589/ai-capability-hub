# Calendar — events, availability, and meeting rooms

Owns calendar events and room booking: viewing and searching a user's agenda, creating and updating events (including recurring ones), managing attendees, querying free/busy, recommending viable time slots, finding available meeting rooms, replying to invitations, and retrieving the video-meeting ID attached to an event. Does **not** own past video-meeting records (VC domain), meeting minutes or transcripts (Minutes / Note domains), to-do tasks (Task domain), contact lookup (Contact domain), or physical room facility administration.

## Shortcuts

| Command | Key parameters | Purpose |
|---|---|---|
| `+agenda` | `--start`, `--end`, `--calendar-id` | List events in a time window; defaults to today |
| `+search-event` | `--query`, `--start`, `--end`, `--attendee-ids`, `--calendar-id`, `--page-token`, `--page-size` | Keyword / range / attendee search returning basic fields only |
| `+get` | `--event-id` (required), `--calendar-id` | Full detail of one event, `description` as Markdown |
| `+create` | `--start` (required), `--end` (required), `--summary`, `--description`, `--attendee-ids`, `--calendar-id`, `--rrule`, `--dry-run` | Create an event and invite attendees |
| `+update` | `--event-id` (required), `--start` + `--end`, `--summary`, `--description`, `--rrule`, `--add-attendee-ids`, `--remove-attendee-ids`, `--notify`, `--calendar-id` | Edit fields, or incrementally add/remove attendees and rooms |
| `+freebusy` | `--start`, `--end`, `--user-id` | Busy intervals and RSVP state on a user's primary calendar |
| `+suggestion` | `--start`, `--end`, `--attendee-ids`, `--duration-minutes`, `--event-rrule`, `--timezone`, `--exclude` | Recommend viable time blocks when the time is not yet fixed |
| `+room-find` | `--slot` (required, repeatable), `--city`, `--building`, `--floor`, `--room-name`, `--min-capacity`, `--max-capacity`, `--attendee-ids`, `--event-rrule`, `--timezone` | Find available rooms for one or more **definite** time blocks |
| `+rsvp` | `--event-id` (required), `--rsvp-status` (required), `--calendar-id` | Reply accept / decline / tentative |
| `+meeting` | `--event-ids` (required, comma-separated), `--calendar-id` | Fetch the video-meeting ID and meeting note attached to events |

Deleting an event and fetching a share link are not shortcuts — they go through the generic service path: `lark-cli calendar events delete --calendar-id <id> --event-id <id>` and `lark-cli calendar events share_info ...`. Resources are `calendars`, `events`, `event.attendees`, `freebusys`; inspect them with `lark-cli calendar <resource> -h` or `lark-cli schema calendar.<resource>.<method>`.

## Key parameters

**`--calendar-id`** — Optional everywhere it appears; omitting it means `primary`, the calling identity's own primary calendar. You may also pass the literal string `primary`.

**`+create`** — `--start` and `--end` are the only required flags and **must carry a timezone offset** (`2026-03-12T14:00+08:00`). Without an offset the value is parsed in the process timezone, which typically shifts by 8 hours. `--summary` should not embed time, place or people. `--attendee-ids` is comma-separated and accepts users (`ou_`), chats (`oc_`) and rooms (`omm_`) — prefixes must be preserved, and a bot is a legitimate attendee here. `--rrule` is RFC 5545. `--description` is Markdown and accepts `@file` or `-` for stdin.

**`+update`** — `--event-id` required. `--start` and `--end` must be passed together; passing one alone is rejected. Attendee changes are incremental via `--add-attendee-ids` / `--remove-attendee-ids`, not a full replacement list. `--notify` defaults `true`, so attendees are notified unless you turn it off. Passing an empty `--description` clears the description.

**`+suggestion`** — Everything optional. `--start` defaults to the current moment, `--end` to the end of that day. `--attendee-ids` accepts users (`ou_`) and chats (`oc_`) only. `--duration-minutes` is an integer; use the user's explicit value, infer from context, otherwise omit. `--exclude` takes comma-separated `start~end` ISO 8601 windows.

**`+room-find`** — `--slot` is the only required flag, formatted `start~end`, and repeatable for multiple candidate blocks (the CLI fans them out concurrently and aggregates one result). `--floor` must be normalised (`2楼` / `二楼` / `2F` all become `F2`) and must not carry zone or room-number information. `--room-name` is comma-separated for multiple names, so "rooms 16 through 20" becomes `--room-name "16,17,18,19,20"`. `--city` may only be set when the user literally named a city — never infer it from a campus or building name, and do not repeat the city prefix inside `--building`. `--min-capacity` / `--max-capacity` are positive integers.

**`+search-event`** — All flags optional. `--page-size` defaults 20 with range 1-30, and `--page-token` continues from a previous page. `--attendee-ids` auto-detects `ou_` / `oc_` / `omm_` prefixes. Returns only `event_id` / `summary` / `start` / `end`-level fields; call `+get` for detail.

**`+freebusy`** — `--user-id` is an `ou_` open_id, defaults to the current user, and **must be supplied explicitly under bot identity**. Returns busy intervals only, with no titles or other private content, and covers the primary calendar alone.

## Gotchas

- **Always pass `--as user` for personal calendars.** A bot cannot see user resources: `--as bot +agenda` returns the bot's own (empty) calendar rather than an error, which silently produces "your schedule is clear". Only use `--as bot` for events the bot itself created or owns.
- **Convert between date strings and timestamps with an external tool, never mentally, and never relying on the container default timezone** (usually UTC, which introduces an 8-hour skew). Always specify the target timezone explicitly.
- **`--start` / `--end` on `+create` need an explicit offset.** ISO 8601 without an offset is parsed in the process timezone. `+agenda` and `+freebusy` are more lenient, accepting ISO 8601, `YYYY-MM-DD`, or Unix seconds, and `+search-event` accepts ISO 8601 or `YYYY-MM-DD`.
- **`COUNT` is not supported in any rrule.** Both `--rrule` and `--event-rrule` reject it; convert a repeat count into an `UNTIL` date. For recurring rooms, verify the returned `reserve_until_time` actually covers the recurrence span.
- **`+agenda` windows over 40 days are auto-split and merged.** The underlying `instance_view` endpoint caps at 40 days (`193103`) and 1000 instances (`193104`); the CLI recursively narrows and recombines, but a very dense range can still bottom out and ask you to narrow it. Cancelled events are filtered out, so an empty result genuinely means nothing is scheduled.
- **`+room-find` requires definite time blocks, not ranges.** If the user says "find me a room this afternoon" with no fixed time, run `+suggestion` first to obtain concrete blocks, then feed those to `+room-find`. Guessing a time and calling directly is prohibited.
- **Strip bots out of `--attendee-ids` for `+suggestion` and `+room-find`.** A bot occupies no seat, has no free/busy semantics and no room preference, so including it skews recommendations. On `+create`, by contrast, a bot is a valid attendee.
- **A room is an attendee, not a bookable standalone object.** Rooms are resource attendees (`omm_` prefix) and cannot be reserved outside an event. When editing an existing event, "add a room" is incremental by default — keep the existing rooms unless the user explicitly says replace or remove.
- **Distinguish edit from create.** If the user references an existing anchor (a title, a time slot, "this event", "that meeting") together with a change verb, that is an edit via `+update`; do not create a duplicate event.
- **Recurring events need an explicit scope.** For "this occurrence only" use the instance's own `event_id`; for "all" or "this and following" operate on the original event's `event_id`. Ask the user which scope they mean rather than defaulting to this-occurrence, and remember that a previously edited occurrence became an independent exception event with its own `event_id` that will linger unless handled.
- **`+create` silently applies defaults** you may need to disclose: `attendee_ability: can_modify_event`, `free_busy_status: busy`, a 5-minute reminder, and a Lark video meeting (`vchat.vc_type: vc`). Anything else — `location`, `visibility`, custom reminders, optional attendees, all-day events, or a room needing `approval_reason` — requires the full API path (`calendar event.attendees create --as user`). If attendee addition fails, the CLI rolls back by deleting the just-created empty event.
- **`+meeting` only returns a `meeting_id` if a video meeting actually took place on that event.** To reach AI summaries or transcripts, chain `+meeting` → VC `+detail` → Note / Minutes `+detail`.
- **Questions about *past* meetings belong to the VC domain,** since meeting data includes ad-hoc meetings that never existed as calendar events. Calendar covers current and future schedules plus keyword search.
- **Contact search does not support bot identity.** `lark-cli contact +search-user --query <q> --as user` is the way to resolve names into the `ou_` open_ids that attendee flags need.
- **Do not re-query to "confirm" a write.** Report from the create / update / RSVP response directly; only query again if the user explicitly asks for verification or the response lacks what they asked about.
- **Week boundaries are Monday-first.** Monday is day one, Sunday is last; compute "next Monday" from the real current date. "Tomorrow" or "today" means the whole day — do not silently narrow it. Fully-past times cannot be booked; the sole exception is an event that straddles now (starts in the past, ends in the future).
- **File paths must be cwd-relative.** A local image inside `--description` Markdown is auto-uploaded only when the path is relative and inside the current working directory; absolute or out-of-cwd paths are rejected as `unsafe file path`, as are `@file` inputs.
- **Only `--format json|pretty|table|ndjson|csv` exists.** There is no standalone `--table`, `--csv`, `--yaml` or `--raw`. Pagination is `--page-all` / `--page-limit` / `--page-delay`, with `--page-size` / `--page-token` on `+search-event`. Identity is `--as user|bot|auto`.
- **Judge success by `ok == true` or the exit code, never `code == 0`.** Success envelopes carry no top-level `code`; that field only appears inside error envelopes as the upstream OpenAPI code, so old-style checks would misread every success as a failure and could duplicate events.
- **No calendar shortcut is currently marked `high-risk-write`** — `+create`, `+update` and `+rsvp` are plain `write`, the rest are `read`. But if any write ever exits `10` with `error.type == "confirmation"`, treat it as a gate rather than a failure: surface `error.action` and `error.risk`, get explicit approval, then re-run the original argv with `--yes` appended. Never auto-append `--yes`. Note that deleting an event via `calendar events delete` is genuinely irreversible and should always be confirmed with the user first.

## Permissions

| Operation | Scope |
|---|---|
| `+agenda`, `+get`, `+search-event`, `+meeting` | `calendar:calendar.event:read` |
| `+create` | `calendar:calendar.event:create` + `calendar:calendar.event:update` |
| `+update` | `calendar:calendar.event:update` |
| `+rsvp` | `calendar:calendar.event:reply` |
| `+freebusy`, `+suggestion`, `+room-find` | `calendar:calendar.free_busy:read` |
| Resolving names to `ou_` ids (Contact domain, user identity only) | `contact:user.base:readonly` |

## Examples

```bash
# Today's agenda for the logged-in user (bot identity would return an empty bot calendar)
lark-cli calendar +agenda --as user --format json

# A one-week window, grouped and sorted downstream into a readable timeline
lark-cli calendar +agenda --as user --start 2026-08-10 --end 2026-08-17 --format json

# Keyword + range + attendee search, then pull full detail for one hit
lark-cli calendar +search-event --as user --query "周会" \
  --start 2026-08-10 --end 2026-08-17 --page-size 30 --format json
lark-cli calendar +get --as user --event-id "<EVENT_ID>" --format json

# Is this person free? (busy intervals only, no titles)
lark-cli calendar +freebusy --as user --start 2026-08-05 --end 2026-08-06 --user-id ou_xxx --format json

# Time not fixed yet: get candidate blocks first, excluding lunch
lark-cli calendar +suggestion --as user \
  --start "2026-08-05T09:00:00+08:00" --end "2026-08-05T18:00:00+08:00" \
  --attendee-ids ou_aaa,ou_bbb --duration-minutes 60 \
  --exclude "2026-08-05T12:00:00+08:00~2026-08-05T13:00:00+08:00" --format json

# Only now, with definite blocks, look for rooms
lark-cli calendar +room-find --as user \
  --slot "2026-08-05T14:00:00+08:00~2026-08-05T15:00:00+08:00" \
  --slot "2026-08-05T16:00:00+08:00~2026-08-05T17:00:00+08:00" \
  --city "北京" --building "学清嘉创大厦B座" --floor "F2" --min-capacity 8 --format json

# Preview the create call, then create with an explicit timezone offset
lark-cli calendar +create --as user --summary "产品评审" \
  --start "2026-08-05T14:00:00+08:00" --end "2026-08-05T15:00:00+08:00" \
  --attendee-ids ou_aaa,ou_bbb,omm_room1 --dry-run
lark-cli calendar +create --as user --summary "产品评审" \
  --start "2026-08-05T14:00:00+08:00" --end "2026-08-05T15:00:00+08:00" \
  --attendee-ids ou_aaa,ou_bbb,omm_room1 --description ./agenda.md

# Weekly recurrence bounded by UNTIL, because COUNT is unsupported
lark-cli calendar +create --as user --summary "双周同步" \
  --start "2026-08-06T10:00:00+08:00" --end "2026-08-06T10:30:00+08:00" \
  --rrule "FREQ=WEEKLY;INTERVAL=2;UNTIL=20261231T000000Z"

# Move an event (start and end must travel together) and add an attendee incrementally
lark-cli calendar +update --as user --event-id "<EVENT_ID>" \
  --start "2026-08-05T16:00:00+08:00" --end "2026-08-05T17:00:00+08:00" \
  --add-attendee-ids ou_ccc

# Reply to an invitation
lark-cli calendar +rsvp --as user --event-id "<EVENT_ID>" --rsvp-status accept

# From an event to its video meeting, en route to summaries/transcripts
lark-cli calendar +meeting --as user --event-ids "<EVENT_ID_1>,<EVENT_ID_2>" --format json
```
