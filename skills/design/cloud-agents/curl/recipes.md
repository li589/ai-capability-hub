# curl Recipes

Pure curl recipes for all common Cloud Agent workflows. Each recipe is self-contained — set the variables at the top and run.

## Setup

```bash
# Required: set these before running any recipe
export BASE="https://api.qoder.com/api/v1/cloud"
export PAT="pt-YOUR_TOKEN_HERE"   # Create/copy your PAT at https://qoder.com/cloud/pat-keys (or https://qoder.com/account/integrations)
```

### Windows / Git-Bash note

On Windows Git-Bash (MSYS2 / MINGW), two quirks can corrupt the recipes below. Apply these and they run unchanged:

- **Disable POSIX path conversion.** MSYS rewrites any `/`-leading value passed to a native `.exe` (e.g. `jq.exe`, `curl.exe`) into a Windows path — so a `file_path` like `/data/file_xxx` arrives as `C:/Program Files/Git/data/file_xxx`. Export `MSYS_NO_PATHCONV=1` (or `MSYS2_ARG_CONV_EXCL='*'`) once per shell to turn this off.
- **Avoid fragile backslash line-continuations.** When a script is pasted with CRLF line endings, a trailing `\` stops continuing the line and the next line (`-F ...`, `--arg ...`) runs as its own command. Prefer single-line commands, and for JSON bodies write the payload to a file and send it with `curl -d @body.json` instead of inlining a `jq -n '{...}'` program as a curl argument.

```bash
# Recommended on Git-Bash:
export MSYS_NO_PATHCONV=1
# Build a JSON body in a file, then post it (robust against quoting/continuation issues):
jq -n --arg a "$AGENT_ID" --arg e "$ENV_ID" --arg f "$FILE_ID" \
  '{agent:$a, environment_id:$e, resources:[{file_id:$f}]}' > body.json
curl -s -X POST "$BASE/sessions" -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" -d @body.json | jq -r '.id'
```

---

## Recipe 1: Verify Connectivity

```bash
curl -s "$BASE/agents" \
  -H "Authorization: Bearer $PAT" | jq .
```

Expected output (empty account):
```json
{"data": [], "first_id": null, "last_id": null, "has_more": false}
```

If you get 401, your PAT is invalid. If connection timeout, check network.

---

## Recipe 2: Create Environment

> Skip if you already have a ready environment.

**Option A** — Quick check (prints full response):
```bash
curl -s -X POST "$BASE/environments" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-env", "config": {"type": "cloud", "networking": {"type": "unrestricted"}}}' | jq .
```

**Option B** — Save the ID to a variable (use this for subsequent recipes):
```bash
ENV_ID=$(curl -s -X POST "$BASE/environments" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-env", "config": {"type": "cloud", "networking": {"type": "unrestricted"}}}' | jq -r '.id')
echo "Environment: $ENV_ID"
```

> Pick **one** of the above — running both creates two environments.

> **Note**: The `config` field is required. `{type: "cloud", networking: {type: "unrestricted"}}` is the standard config. Omitting it returns 400.

Wait for `status: ready`:
```bash
curl -s "$BASE/environments/$ENV_ID" \
  -H "Authorization: Bearer $PAT" | jq '.status'
```

---

## Recipe 3: Create Agent

```bash
AGENT_ID=$(curl -s -X POST "$BASE/agents" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg name "my-agent" \
    --arg system "You are a helpful assistant. Reply concisely." \
    '{name: $name, system: $system, model: "ultimate", tools: [{type: "agent_toolset_20260401"}]}'
  )" | jq -r '.id')
echo "Agent: $AGENT_ID"
```

> Use `jq -n --arg` for safe JSON construction. Never interpolate shell variables directly into JSON strings.

---

## Recipe 4: Create Session + Send Message + Stream

```bash
# Create session
SESS_ID=$(curl -s -X POST "$BASE/sessions" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg agent "$AGENT_ID" \
    --arg env "$ENV_ID" \
    '{agent: $agent, environment_id: $env}'
  )" | jq -r '.id')
echo "Session: $SESS_ID"

# Send message
MESSAGE="Hello! What can you do?"
EVENT_ID=$(curl -s -X POST "$BASE/sessions/$SESS_ID/events" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg content "$MESSAGE" \
    '{events: [{type: "user.message", content: $content}]}'
  )" | jq -r '.data[0].id')
echo "Event sent: $EVENT_ID"

# Stream response (timeout: use `timeout` on Linux/Git Bash, `gtimeout` on macOS with coreutils, or omit and Ctrl+C manually)
timeout 90 curl -s -N "$BASE/sessions/$SESS_ID/events/stream" \
  -H "Authorization: Bearer $PAT" \
  -H "Accept: text/event-stream"
```

The stream outputs SSE events. Look for `event: agent.message` for the response and `event: session.status_idle` for turn completion.

---

## Recipe 5: Multi-Turn Conversation

After Recipe 4, send another message to the same session (wait for idle first):

```bash
MESSAGE2="Now explain that in more detail."
EVENT2_ID=$(curl -s -X POST "$BASE/sessions/$SESS_ID/events" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg content "$MESSAGE2" \
    '{events: [{type: "user.message", content: $content}]}'
  )" | jq -r '.data[0].id')
echo "Event sent: $EVENT2_ID"

# Stream again — use after_id to skip previously received events
timeout 60 curl -s -N "$BASE/sessions/$SESS_ID/events/stream?after_id=$EVENT2_ID" \
  -H "Authorization: Bearer $PAT" \
  -H "Accept: text/event-stream"
```

> **Important**: Always pass `after_id` with the last received event ID when streaming subsequent turns. Without it, the stream replays all events from the session start.

---

## Recipe 6: Cancel a Running Session

```bash
# Cancel (returns 202)
curl -s -X POST "$BASE/sessions/$SESS_ID/cancel" \
  -H "Authorization: Bearer $PAT" | jq .
# → {"status": "canceling"}

# Wait for idle confirmation via stream or poll:
curl -s "$BASE/sessions/$SESS_ID" \
  -H "Authorization: Bearer $PAT" | jq '.status'
# → "idle" (when settled)
```

---

## Recipe 7: Full Cleanup

```bash
# 1. Cancel if running (safe to call even if already idle)
curl -s -X POST "$BASE/sessions/$SESS_ID/cancel" \
  -H "Authorization: Bearer $PAT" > /dev/null 2>&1 || true

# 2. Delete session (archive is optional)
curl -s -X DELETE "$BASE/sessions/$SESS_ID" \
  -H "Authorization: Bearer $PAT" | jq .

# 3. Delete agent
curl -s -X DELETE "$BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $PAT" | jq .

# 4. Delete environment (only if it was created for this test)
curl -s -X DELETE "$BASE/environments/$ENV_ID" \
  -H "Authorization: Bearer $PAT" | jq .

echo "Cleanup complete."
```

> Resources can be deleted directly without archiving. Archiving is optional — use it if you want to soft-hide resources from list results before permanent deletion.

---

## Recipe 8: List & Filter Resources

```bash
# List all agents (non-archived)
curl -s "$BASE/agents" \
  -H "Authorization: Bearer $PAT" | jq '.data[] | {id, name, version}'

# List all sessions for inspection
curl -s "$BASE/sessions" \
  -H "Authorization: Bearer $PAT" | jq '.data[] | {id, status, agent}'

# List environments (check status)
curl -s "$BASE/environments" \
  -H "Authorization: Bearer $PAT" | jq '.data[] | {id, name, status}'

# Paginate: get next page
curl -s "$BASE/agents?after_id=agent_last_id_here" \
  -H "Authorization: Bearer $PAT" | jq .
```

---

## Recipe 9: Upload File and Attach to a Session

Upload a file once via `POST /files`, then make it visible to the agent by listing its `file_id` in the session's `resources` array. The container mounts the file at `/data/<file_id>`. Use this whenever the agent needs to process a non-trivial dataset (CSV, JSON, log, transcript, source code) — pass the data through the filesystem, not through the message body.

```bash
# 1) Upload the file.
FILE_ID=$(curl -s -X POST "$BASE/files" \
  -H "Authorization: Bearer $PAT" \
  -F "file=@./feedback.csv" \
  -F "purpose=session_resource" | jq -r '.file_id')
echo "File: $FILE_ID"

# 2) Create a session with the file in `resources`.
SESSION_ID=$(curl -s -X POST "$BASE/sessions" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg agent "$AGENT_ID" --arg env "$ENV_ID" --arg fid "$FILE_ID" \
        '{agent: $agent, environment_id: $env, resources: [{file_id: $fid}]}')" | jq -r '.id')
echo "Session: $SESSION_ID"

# 3) Tell the agent where to read it. The mount path is /data/<file_id>.
curl -s -X POST "$BASE/sessions/$SESSION_ID/events" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg fid "$FILE_ID" \
        '{events:[{type:"user.message",content:[{type:"text",text:("Read /data/\($fid) and report the row count excluding the header.")}]}]}')"

# Then stream as in Recipe 5 and wait for session.status_idle.
```

### Retrieving the agent's output

If the agent writes its result to a file under `/data/` inside the container, the SSE stream will emit an `agent.artifact_delivered` event carrying a new `file_id`. Two steps to download:

```bash
# Captured from the event payload:
ART_ID=file_xxx

# Step 1: get a presigned download URL.
URL=$(curl -s "$BASE/files/$ART_ID/content" \
  -H "Authorization: Bearer $PAT" | jq -r '.url')

# Step 2: fetch the file (no Authorization header — signature is in the URL).
curl -sL -o classified.csv "$URL"
```

---

## Recipe 10: Memory Store Operations

```bash
# Create store
STORE_ID=$(curl -s -X POST "$BASE/memory_stores" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d '{"name": "project-kb"}' | jq -r '.id')
echo "Store: $STORE_ID"

# Add memory entry
curl -s -X POST "$BASE/memory_stores/$STORE_ID/memories" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg content "Production uses PostgreSQL 15 in us-west-2" \
    '{content: $content, metadata: {category: "infra"}}'
  )" | jq .

# List memories
curl -s "$BASE/memory_stores/$STORE_ID/memories" \
  -H "Authorization: Bearer $PAT" | jq '.data'
```

---

## Recipe 11: Skill Upload + Bind to Agent

```bash
# Create a zip with SKILL.md at root
zip -r my-skill.zip SKILL.md shared/ curl/

# Upload skill
SKILL_ID=$(curl -s -X POST "$BASE/skills" \
  -H "Authorization: Bearer $PAT" \
  -F "file=@./my-skill.zip" | jq -r '.id')
echo "Skill: $SKILL_ID"

# Bind to existing agent (requires current version for optimistic lock)
AGENT_VERSION=$(curl -s "$BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $PAT" | jq '.version')
curl -s -X PUT "$BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg skill_id "$SKILL_ID" \
    --argjson version "$AGENT_VERSION" \
    '{version: $version, skills: [{type: "custom", skill_id: $skill_id}]}'
  )" | jq '{id, version}'

# Delete skill (no archive needed)
curl -s -X DELETE "$BASE/skills/$SKILL_ID" \
  -H "Authorization: Bearer $PAT"
echo "Skill deleted."
```

> Skills use `multipart/form-data` for upload (like Files), NOT JSON. Delete is direct — no archive step required.
