# API Reference

## Contents

- [Agents](#agents)
- [Environments](#environments)
- [Sessions](#sessions)
- [Events](#events)
- [Files](#files)
- [Memory Stores](#memory-stores)
- [Skills](#skills)
- [Common Response Codes](#common-response-codes)

---

All endpoints are under `https://api.qoder.com/api/v1/cloud`.

Every request requires:
```
Authorization: Bearer <PAT>
Content-Type: application/json
```

Pagination: cursor-based with `after_id` / `before_id` query params. Response shape: `{data: [...], first_id, last_id, has_more}`.

---

## Agents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agents` | Create agent |
| GET | `/agents` | List agents (excludes archived) |
| GET | `/agents/{id}` | Get agent |
| PUT | `/agents/{id}` | Update agent |
| POST | `/agents/{id}/archive` | Archive agent |
| DELETE | `/agents/{id}` | Delete agent (archive optional) |

### POST /agents

```json
{
  "name": "my-agent",
  "description": "Optional description",
  "system": "You are a helpful assistant.",
  "model": "ultimate",
  "tools": []
}
```

Response `201`:
```json
{
  "id": "agent_xxx",
  "name": "my-agent",
  "description": "Optional description",
  "system": "You are a helpful assistant.",
  "model": "ultimate",
  "tools": [],
  "version": 1,
  "archived": false,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### PUT /agents/{id}

**Partial update**: send only the fields you want to change, plus the required `version` field for optimistic locking. Fields you omit are preserved, NOT cleared — e.g. updating `name` alone leaves `system`, `model`, and `tools` untouched.

```json
{
  "name": "updated-name",
  "version": 1
}
```

> The `version` field is **required** — omitting it returns 400 `Field 'version' is required.`. It must also match the agent's current version (from GET); a stale value returns 409 conflict (`Version conflict. Expected version X, got Y.`). On success, `version` increments automatically.

Returns updated agent.

### POST /agents/{id}/archive

No body. Returns `200` with `{"archived": true, "archived_at": "..."}`.

### DELETE /agents/{id}

No body. Returns `200`. Can be called directly without archiving first.

---

## Environments

| Method | Path | Description |
|--------|------|-------------|
| POST | `/environments` | Create environment |
| GET | `/environments` | List environments |
| GET | `/environments/{id}` | Get environment |
| PUT | `/environments/{id}` | Update environment |
| POST | `/environments/{id}/archive` | Archive environment |
| DELETE | `/environments/{id}` | Delete environment |

### POST /environments

```json
{
  "name": "my-env",
  "config": {
    "type": "cloud",
    "networking": {
      "type": "unrestricted"
    }
  }
}
```

> **Critical**: The `config` field with `type` and `networking` is required. Sending only `{name}` returns 400.

Response `201`:
```json
{
  "id": "env_xxx",
  "name": "my-env",
  "config": {
    "type": "cloud",
    "networking": {"type": "unrestricted"}
  },
  "status": "provisioning",
  "archived": false,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

> Environment `status` transitions: `provisioning` → `ready`. Wait for `ready` before using in sessions.

---

## Sessions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create session |
| GET | `/sessions` | List sessions |
| GET | `/sessions/{id}` | Get session |
| POST | `/sessions/{id}/archive` | Archive session |
| DELETE | `/sessions/{id}` | Delete session |
| POST | `/sessions/{id}/cancel` | Cancel running turn |

### POST /sessions

```json
{
  "agent": "agent_xxx",
  "environment_id": "env_xxx",
  "resources": [
    {"file_id": "file_xxx"}
  ]
}
```

> **Critical**: field name is `agent`, NOT `agent_id`.
>
> `resources` is optional. To make uploaded files visible to the agent, list them as `[{"file_id": "..."}]`; each entry is mounted in the container at `/data/<file_id>`. Omit `resources` when the session does not need pre-attached files.

Response `201`:
```json
{
  "id": "sess_xxx",
  "agent": "agent_xxx",
  "environment_id": "env_xxx",
  "status": "idle",
  "resources": [
    {"file_id": "file_xxx", "path": "/data/file_xxx", "type": "file"}
  ],
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### POST /sessions/{id}/cancel

No body. Returns `202`:
```json
{
  "status": "canceling"
}
```

Session settles to `idle` asynchronously. See `shared/client-patterns.md` Pattern 3.

---

## Events

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{id}/events` | Send event (user message) |
| GET | `/sessions/{id}/events` | List events (paginated) |
| GET | `/sessions/{id}/events/stream` | SSE stream |

### POST /sessions/{id}/events

```json
{
  "events": [
    {
      "type": "user.message",
      "content": "Hello, what can you do?"
    }
  ]
}
```

> **Critical**: The body must wrap events in an `events` array. Sending a bare event object returns 400.

Response `202`:
```json
{
  "data": [
    {
      "id": "evt_xxx",
      "type": "user.message",
      "session_id": "sess_xxx",
      "turn_id": "turn_xxx",
      "content": "Hello, what can you do?",
      "created_at": "2026-01-01T00:00:00Z",
      "schema_version": "1.0"
    }
  ]
}
```

### GET /sessions/{id}/events/stream

SSE endpoint. Query params:
- `after_id` — Resume from after this event ID (for reconnection)

Headers:
```
Authorization: Bearer <PAT>
Accept: text/event-stream
```

Returns `text/event-stream`. See `shared/events.md` for event types and format.

### GET /sessions/{id}/events

Query params: `after_id`, `before_id`, `limit` (default 20, max 100).

Response:
```json
{
  "data": [{ "id": "evt_xxx", "type": "...", ... }],
  "first_id": "evt_aaa",
  "last_id": "evt_zzz",
  "has_more": false
}
```

---

## Files

| Method | Path | Description |
|--------|------|-------------|
| POST | `/files` | Upload file |
| GET | `/files` | List files |
| GET | `/files/{id}` | Get file metadata |
| GET | `/files/{id}/content` | Get a presigned download URL |
| DELETE | `/files/{id}` | Delete file |

### POST /files

Multipart form upload:
```
Content-Type: multipart/form-data
- file: <binary>
- purpose: "session_resource"   # use this purpose to make the file readable from a session
```

Response `201`:
```json
{
  "file_id": "file_xxx",
  "filename": "data.csv",
  "purpose": "session_resource",
  "size_bytes": 1024,
  "mime_type": "text/csv",
  "status": "ready",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

> Uploading creates the file but does not by itself attach it to any session. To let an agent read the file, pass `resources: [{"file_id": "file_xxx"}]` on `POST /sessions` — the file is then mounted at `/data/<file_id>` inside the container.

### GET /files/{id}/content

Returns a short-lived presigned download URL. The endpoint itself is JSON; the file body lives behind the URL.

Response `200`:
```json
{
  "url": "https://<storage-host>/...?Signature=...",
  "expires_at": "2026-01-01T01:00:00Z"
}
```

Fetch the file with `curl -L "$url"` — no Authorization header is needed because the signature is in the URL. Mint a fresh URL by calling this endpoint again if the previous one has expired.

### Agent-produced files

When an agent writes a file under `/data/` inside its container, the platform automatically uploads it as a new file with `purpose: "agent_output"` and emits an `agent.artifact_delivered` event on the SSE stream (see `shared/events.md`). The event payload carries the new `file_id`; use `GET /files/{id}/content` to download the result.

---

## Memory Stores

| Method | Path | Description |
|--------|------|-------------|
| POST | `/memory_stores` | Create memory store |
| GET | `/memory_stores` | List memory stores |
| GET | `/memory_stores/{id}` | Get memory store |
| DELETE | `/memory_stores/{id}` | Delete memory store |
| POST | `/memory_stores/{id}/memories` | Create memory entry |
| GET | `/memory_stores/{id}/memories` | List memories |
| PUT | `/memory_stores/{id}/memories/{mem_id}` | Update memory |
| DELETE | `/memory_stores/{id}/memories/{mem_id}` | Delete memory |

### POST /memory_stores

```json
{
  "name": "project-knowledge"
}
```

### POST /memory_stores/{id}/memories

```json
{
  "content": "The deployment target is us-west-2.",
  "metadata": {"category": "infra"}
}
```

---

## Skills

| Method | Path | Description |
|--------|------|-------------|
| POST | `/skills` | Upload skill (multipart/form-data) |
| GET | `/skills` | List skills |
| GET | `/skills/{id}` | Get skill |
| DELETE | `/skills/{id}` | Delete skill (no archive needed) |

### POST /skills

Multipart form upload — the skill must be a `.zip` file with `SKILL.md` at the zip root:
```
Content-Type: multipart/form-data
- file: <skill.zip>
- name: "my-skill" (optional, overridden by SKILL.md frontmatter)
- description: "..." (optional, overridden by SKILL.md frontmatter)
```

> **Note**: This endpoint requires `multipart/form-data` with a zip file, NOT JSON. The `name` and `description` in the SKILL.md frontmatter take priority over form fields.

Response `201`:
```json
{
  "id": "skill_xxx",
  "name": "my-skill",
  "description": "...",
  "skill_type": "custom",
  "status": "active",
  "version": 1,
  "content_sha256": "abc123...",
  "content_size": 4096,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### DELETE /skills/{id}

No body. Returns `204` (empty body). Skill is immediately deleted — **no archive step required**.

### Binding Skills to Agents

Add skills when creating or updating an agent via `PUT /agents/{id}`:

```json
{
  "skills": [
    {"type": "custom", "skill_id": "skill_xxx"}
  ]
}
```

> **Known limitation**: The `skills` field is accepted on write (version increments), but `GET /agents/{id}` does not return it in the response. Verify binding by testing agent behavior, not by reading the agent object.

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PUT, DELETE, archive) |
| 201 | Created (POST create) |
| 202 | Accepted (async operations: send event, cancel) |
| 204 | No Content (DELETE /skills — empty body) |
| 400 | Bad request (missing/invalid fields) |
| 401 | Unauthorized (invalid/missing PAT) |
| 404 | Resource not found |
| 409 | Conflict (e.g., version mismatch on PUT) |
| 429 | Rate limited |
| 500 | Internal server error |
