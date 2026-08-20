# Events

The event system is the core communication channel between client and Cloud Agent sessions. You send events (user messages) and receive events (agent responses, status changes) via SSE streaming or polling.

---

## Sending Events

Send events to a session via `POST /sessions/{id}/events`.

Currently supported outbound event type:

### user.message

```json
{
  "events": [
    {
      "type": "user.message",
      "content": "Your message text here"
    }
  ]
}
```

> **Note**: Wrap in an `events` array. A bare event object returns 400.

Returns `202` with `{data: [...]}` containing the event object(s) with `id`, `turn_id`, `session_id`.

---

## Receiving Events (SSE Stream)

Connect to `GET /sessions/{id}/events/stream` for real-time events.

```
GET /sessions/{id}/events/stream?after_id=evt_last_seen
Authorization: Bearer <PAT>
Accept: text/event-stream
```

### SSE Wire Format

Each event is delivered as:
```
event: <event_type>
data: {"id":"evt_xxx","type":"<event_type>","session_id":"sess_xxx",...}

```

Heartbeats (every ~15s) use a dual-line format:
```
: heartbeat
event: heartbeat
data: {}

```

> Filter both the comment line (`: heartbeat`) and the `event: heartbeat` when parsing meaningful events.

---

## Event Types

### Lifecycle Events (in order of typical appearance)

| Event Type | Meaning | Payload highlights |
|---|---|---|
| `user.message` | Echoed user message | `content`, `turn_id` |
| `session.status_running` | Session began processing | `status: "running"` |
| `span.model_request_start` | Model inference started | `span_id` |
| `agent.thinking` | Agent internal reasoning | `content` (may be partial) |
| `agent.tool_use` | Agent invoked a built-in tool (Bash / Read / Write / ...) | `tool_name`, `tool_input`, `tool_use_id` |
| `agent.tool_result` | Tool returned to the agent | `tool_use_id`, `content` |
| `agent.artifact_delivered` | Agent wrote a file under `/data/` and the platform uploaded it as a result file. Download via `GET /files/{id}/content`. | `file_id`, `original_filename`, `content_type`, `size` |
| `agent.message` | Agent response | `content: [{"text":"...","type":"text"}]` |
| `session.status_idle` | **Turn complete** | `usage`, `stop_reason` |
| `span.model_request_end` | Model request closed | `span_id` |
| `session.error` | Processing error | `error: {message, type}` |

### Typical Turn Lifecycle

```
user.message
  → session.status_running
    → span.model_request_start
      → agent.thinking (0 or more)
      → agent.message (1 or more)
    → session.status_idle          ← USE THIS as stop signal
    → span.model_request_end       ← arrives AFTER idle
```

> **Ordering note**: `session.status_idle` fires BEFORE `span.model_request_end`. Always use `idle` as your stop signal, not `span.model_request_end`.

---

## session.status_idle Payload

This is the richest event — carries token usage and stop reason:

```json
{
  "id": "evt_xxx",
  "type": "session.status_idle",
  "session_id": "sess_xxx",
  "turn_id": "turn_xxx",
  "status": "idle",
  "usage": {
    "input_tokens": 245,
    "output_tokens": 18,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0
  },
  "stop_reason": {
    "type": "end_turn"
  },
  "schema_version": "1.0"
}
```

Use `usage` for token consumption tracking. Use `stop_reason.type` to determine why the turn ended:
- `"end_turn"` — Agent finished naturally (or cancel settled)
- `"max_tokens"` — Hit token limit

---

## agent.message Content Format

The `content` field is always an **array**, not a plain string:

```json
{
  "type": "agent.message",
  "content": [
    {"text": "Hello! How can I help?", "type": "text"}
  ]
}
```

To extract text: `event.content[0].text` (or iterate for multi-block responses).

---

## Reconnection

If your SSE connection drops, reconnect using `after_id`:

```
GET /sessions/{id}/events/stream?after_id=<last_received_event_id>
```

This resumes from after the specified event. Deduplicate by `event.id` in case of overlap.

---

## Polling (Alternative to SSE)

If SSE is impractical, poll `GET /sessions/{id}/events?after_id=<last_id>` periodically.

Recommended interval: 1-2 seconds while session status is `running`, stop polling once you receive `session.status_idle`.
