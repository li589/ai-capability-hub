# Client Patterns

Practical patterns for building robust Cloud Agent clients. These are derived from real-world usage and address behaviors that official documentation may not fully cover.

---

## Pattern 1: Use `session.status_idle` as Universal Stop Signal

**Problem**: Multiple events signal "completion" (`span.model_request_end`, `session.status_idle`). Which one should you wait for?

**Solution**: Always use `session.status_idle` as your stop signal.

- It fires BEFORE `span.model_request_end`
- It carries `usage` (token counts) and `stop_reason`
- It is the single source of truth for "this turn is done"

```javascript
// Pseudocode
for await (const event of sseStream) {
  if (event.type === 'agent.message') {
    appendToUI(event.content[0].text);
  }
  if (event.type === 'session.status_idle') {
    // Turn is done. Safe to send next message or close.
    break;
  }
}
```

Do NOT wait for `span.model_request_end` — it arrives after idle and adds unnecessary delay.

---

## Pattern 2: Cold-Start Awareness

**Problem**: After sending the first message to a new session, there's silence for 5-60 seconds before any agent response.

**Cause**: The container environment is being provisioned (cold start). Subsequent turns in the same session are fast.

**Solution**:
- Set SSE read timeout to at least 90 seconds for the first turn
- Show a "thinking..." or loading indicator in your UI
- Do NOT retry or abort during this window
- Heartbeats (every ~15s) confirm the connection is alive during cold start

```
Timeline:
  0s   — POST /events (send message)
  0s   — GET /events/stream connected
  15s  — : heartbeat (connection alive, still provisioning)
  27s  — session.status_running (container ready, processing starts)
  28s  — span.model_request_start
  29s  — agent.message
  29s  — session.status_idle
```

---

## Pattern 3: Cancel Handling

**Problem**: You cancel a session but need to know when it's actually stopped.

**Behavior**:
1. `POST /sessions/{id}/cancel` returns `202` with `{"status":"canceling"}`
2. Session transitions asynchronously to `idle`
3. The stream emits `session.status_idle` with `stop_reason: {"type":"end_turn"}`

**Solution**: After calling cancel, continue reading the SSE stream until you see `session.status_idle`. That's your confirmation the cancel settled.

```javascript
// Cancel and wait for settlement
await fetch(`${BASE}/sessions/${id}/cancel`, { method: 'POST', headers });

// Keep reading stream until idle
for await (const event of sseStream) {
  if (event.type === 'session.status_idle') {
    // Cancel settled. Session is idle.
    break;
  }
}
```

> Note: The `stop_reason` after cancel is `end_turn` (same as normal completion). There is no distinct "cancelled" stop reason at the event level. If you need to distinguish, track your own cancel state client-side.

---

## Pattern 4: SSE Reconnection with Dedup

**Problem**: Network interruptions drop the SSE connection mid-turn.

**Solution**:
1. Track the `id` of every received event
2. On disconnect, reconnect with `?after_id=<last_received_id>`
3. Deduplicate by event `id` (server may replay the boundary event)

```javascript
let lastEventId = null;

function connect() {
  const url = lastEventId
    ? `${BASE}/sessions/${id}/events/stream?after_id=${lastEventId}`
    : `${BASE}/sessions/${id}/events/stream`;

  const es = new EventSource(url, { headers });

  es.onmessage = (msg) => {
    const event = JSON.parse(msg.data);
    if (event.id === lastEventId) return; // dedup
    lastEventId = event.id;
    handleEvent(event);
  };

  es.onerror = () => {
    es.close();
    setTimeout(connect, 2000); // reconnect with backoff
  };
}
```

---

## Pattern 5: Multi-Turn Conversation

**Problem**: You want to send follow-up messages in the same session.

**Rule**: Wait for `session.status_idle` before sending the next `user.message`.

```javascript
async function chat(sessionId, message) {
  // Send message
  await sendEvent(sessionId, { type: 'user.message', content: message });

  // Collect response
  const response = [];
  for await (const event of streamEvents(sessionId)) {
    if (event.type === 'agent.message') {
      response.push(event.content[0].text);
    }
    if (event.type === 'session.status_idle') {
      break; // Safe to send next message now
    }
  }
  return response.join('');
}

// Usage: sequential turns
const reply1 = await chat(sessId, "What is 2+2?");
const reply2 = await chat(sessId, "Now multiply that by 3");
```

The session automatically maintains conversation context across turns — no need to resend history.

---

## Pattern 6: Error Recovery

**Problem**: Session encounters an error during processing.

**Signal**: `session.error` event in the stream.

```json
{
  "type": "session.error",
  "error": {
    "message": "Model inference failed",
    "type": "internal_error"
  }
}
```

**Recovery strategy**:
1. Log the error details
2. Check session status via `GET /sessions/{id}` — if `idle`, you can retry the message
3. If persistent errors, create a new session (the environment/agent are still valid)

---

## Pattern 7: Resource Cleanup

**Best practice**: Always clean up resources after use, especially in automated/test scenarios.

**Recommended order**:
1. Cancel session if running (`POST /cancel`, wait for idle)
2. Delete session (`DELETE /sessions/{id}`)
3. Delete agent (`DELETE /agents/{id}`)

> Archiving before deletion is optional — resources can be deleted directly. However, if you want to soft-remove without permanent deletion, use archive. Environments are typically long-lived and shared; only delete test environments.

---

## Pattern 8: Rate Limit (429) Backoff

**Problem**: Under bursty load — e.g., fanning out messages to many sessions at once — the API returns `429 Too Many Requests`.

**Why it matters**: Retrying immediately makes things worse; you keep hitting the limiter and never drain the burst. The fix is to back off so the limiter's window can refill.

**Solution**:
1. On `429`, wait before retrying. If the response carries a `Retry-After` header, honor it; otherwise use exponential backoff (e.g., 1s → 2s → 4s, capped).
2. Add a little jitter so parallel clients don't retry in lockstep and re-collide.
3. Cap total retries so a sustained limit surfaces as an error instead of hanging forever.

```javascript
async function sendWithBackoff(url, body, headers, maxRetries = 5) {
  let delay = 1000; // 1s
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fetch(url, { method: 'POST', headers, body });
    if (res.status !== 429) return res;

    const retryAfter = res.headers.get('Retry-After');
    const waitMs = retryAfter
      ? Number(retryAfter) * 1000
      : delay + Math.random() * 250; // exponential + jitter

    await new Promise(r => setTimeout(r, waitMs));
    delay = Math.min(delay * 2, 16000); // cap at 16s
  }
  throw new Error('Rate limit: exhausted retries');
}
```

> For high-fanout workloads, prefer limiting concurrency client-side (a small worker pool) over firing all requests at once — it avoids tripping the limiter in the first place.
