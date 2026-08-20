# Tools and Resources

How to configure agent tools, manage environments, and work with files.

---

## Agent Tools

Tools are configured on the Agent object (not the session). Two tool types are available:

### agent_toolset (Built-in Tools)

The platform provides a standard toolset that gives the agent capabilities like code execution, file operations, and web browsing within its container environment.

```json
{
  "name": "my-agent",
  "system": "You are a coding assistant.",
  "model": "ultimate",
  "tools": [
    {
      "type": "agent_toolset_20260401"
    }
  ]
}
```

This single declaration enables the full built-in toolset. The `20260401` suffix is the toolset version.

### MCP Tools (Model Context Protocol)

Connect external tool servers via MCP:

```json
{
  "name": "my-agent",
  "system": "You are a research assistant.",
  "model": "ultimate",
  "tools": [
    {
      "type": "agent_toolset_20260401"
    },
    {
      "type": "mcp_toolset",
      "mcp_servers": [
        {
          "name": "my-tools",
          "url": "https://my-mcp-server.example.com/mcp",
          "auth": {
            "type": "bearer",
            "token": "sk-xxx"
          }
        }
      ]
    }
  ]
}
```

MCP servers must be publicly accessible from the cloud environment. The agent discovers available tools from the MCP server at session start.

---

## Environments

Environments define the execution context for sessions — the container where the agent's tools run.

### Creating an Environment

```json
POST /environments
{
  "name": "dev-env",
  "config": {
    "type": "cloud",
    "networking": {
      "type": "unrestricted"
    }
  }
}
```

> **No default environment exists.** Every new account must create at least one environment before starting sessions. The `config` field is required — omitting it returns 400.

### Environment Status

After creation, environment transitions: `provisioning` → `ready`.

**Only `ready` environments can be used in sessions.** Poll `GET /environments/{id}` until status is `ready`, or list and pick an existing ready environment.

### Environment Lifecycle

- Environments are reusable across multiple sessions
- Archive when no longer needed: `POST /environments/{id}/archive`
- Archived environments cannot be used for new sessions
- Delete when no longer needed: `DELETE /environments/{id}` (archive first for soft-hide, or delete directly)

---

## Files

Upload files to make them available to sessions.

### Uploading

```bash
curl -X POST "$BASE/files" \
  -H "Authorization: Bearer $PAT" \
  -F "file=@./data.csv" \
  -F "purpose=session_resource"
```

### File Purposes

- `session_resource` — Available to session for reading/processing

### Using Files in Sessions

Files can be referenced when creating sessions or sending messages, making them accessible to the agent within its container environment.

---

## Memory Stores

Persistent knowledge that survives across sessions. Useful for:
- Shared project context across multiple agent sessions
- Accumulating learnings over time
- Cross-agent collaboration (multiple agents reading the same store)

### Setup

```json
POST /memory_stores
{
  "name": "project-knowledge"
}

POST /memory_stores/{store_id}/memories
{
  "content": "Production database is PostgreSQL 15 on us-west-2.",
  "metadata": {"category": "infra", "confidence": "high"}
}
```

### Attaching to Sessions

Memory stores are attached to agents via configuration, making their contents available during all sessions with that agent.

---

## Skills

Reusable capability packages uploaded as zip files and bound to agents.

### Uploading a Skill

Skills must be uploaded as a `.zip` file via `multipart/form-data`. The zip must contain `SKILL.md` at its root level:

```bash
# Create the zip
zip -r my-skill.zip SKILL.md shared/ curl/

# Upload
curl -X POST "$BASE/skills" \
  -H "Authorization: Bearer $PAT" \
  -F "file=@./my-skill.zip"
```

> This is NOT a JSON endpoint. Sending `{"name":"..."}` as JSON returns an error.

### Binding to an Agent

`PUT /agents/{id}` is a partial update, so binding skills only needs the `version` and `skills` fields — the agent's existing `name`, `system`, `model`, and `tools` are preserved. The `version` field is **required** (omitting it returns 400); fetch the current value from `GET /agents/{id}` first.

```json
PUT /agents/{id}
{
  "version": 1,
  "skills": [
    {"type": "custom", "skill_id": "skill_xxx"}
  ]
}
```

The agent will have access to the skill's content during sessions. Note: `GET /agents/{id}` currently does not include the `skills` field in its response (backend serialization gap), but the binding is effective.

### Lifecycle

- Skills can be directly deleted (`DELETE /skills/{id}`) without archiving first
- No `archive` endpoint exists for skills
- Deleting a skill that is bound to an agent does not automatically unbind it — update the agent separately
