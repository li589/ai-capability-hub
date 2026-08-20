# Case Study: Redis Silent Failure Causing Login Hang

## Incident Summary

**Date:** 2026-08-08
**Symptom:** All users unable to log in. Login page loads, but after submitting credentials, the button shows "登录中..." (Logging in...) indefinitely.
**Duration:** ~2 hours
**Root cause:** Redis (running 333 days without restart) silently returned null/empty data for `getPublicKey` and session-related keys, causing the backend to return HTTP 200 with null payload. The frontend JavaScript hung waiting for valid data.

## What the logs showed

### Frontend (nginx) log
```
getPublicKey.do → status:200, upstream_status:200, upstream_addr:10.96.1.208:8080
```
Request reached the backend Service and returned 200 — but the response body was null.

### Backend (mservice) log
```
getUserId → success (userId resolved from DB)
```
Login traceIds disappeared after `getUserId`. No `getPublicKey` traceId found in backend logs.

### Middleware logs
- **Redis:** Only startup logs from 333 days ago. No runtime logs, no errors.
- **PG:** Checkpoint latency up to 152s, many `Connection reset by peer`, but no slow queries, no lock contention.
- **MQ:** No activity after 01:14 AM (10+ hours before incident).
- **ZK:** Normal, all distributed locks acquired/released successfully.

## How the diagnosis went wrong

### The diagnostic path taken
1. Analyzed mservice.log → found login traceIds disappearing after `getUserId`.
2. Analyzed pg.log → found checkpoint 152s and Connection Reset.
3. Found Druid `removeAbandoned=true` → **anchored on this as the root cause.**
4. Restarted mservice → still broken.
5. Checked PG disk IO → healthy.
6. User restarted Redis → **problem resolved.**

### Why Redis was missed
1. **Anchoring bias:** The Druid `removeAbandoned` finding was a real problem (it can cause connection pool issues), but it was not THE problem in this case. Once anchored, we stopped investigating other components.
2. **Redis had no errors:** Redis logs showed only startup messages from 333 days ago. No errors, no warnings. The absence of errors was misinterpreted as "healthy."
3. **HTTP 200 misdirection:** `getPublicKey` returned HTTP 200 (not 500), so the frontend nginx log showed success. The null payload was only visible in the browser's network tab.
4. **Did not trace component dependencies:** We never asked "what does `getPublicKey` depend on?" The answer would have been Redis, and we would have checked Redis state.

## What should have been done

### Correct diagnostic flow

**Step 1: Reconstruct the call chain**
```
Frontend log: getPublicKey.do → 200, upstream 200, traceId:58d1e01745e223c1
Backend log: traceId:58d1e01745e223c1 → NOT FOUND
```
→ Request reached the Service but no backend Pod processed it? Or the traceId was not logged?

**Step 2: Verify cross-Pod routing**
```bash
kubectl get po -n kd-cosmic-xk | grep mservice
# Only 1 replica → routing is not the issue
```

**Step 3: Infer component dependency**
```
getPublicKey → likely reads from Redis (public key cache)
```
→ Check Redis state.

**Step 4: Generate targeted verification**
```bash
# Check if Redis is responsive
redis-cli -h redis-headless.redis-system.svc -a Cosmic@2025 PING

# Check Redis stats for anomalies
redis-cli -h redis-headless.redis-system.svc -a Cosmic@2025 INFO stats

# Check for keys related to public key
redis-cli -h redis-headless.redis-system.svc -a Cosmic@2025 KEYS "*publickey*"

# Check Redis connected clients
redis-cli -h redis-headless.redis-system.svc -a Cosmic@2025 CLIENT LIST
```

## Lessons learned

1. **HTTP 200 + null payload is a red flag for middleware silent failure.** When an API returns 200 with null/empty data, the middleware (Redis, cache, DB) is the prime suspect.
2. **"No errors in logs" ≠ "healthy."** Redis running 333 days without any runtime log entries is itself suspicious — a healthy Redis should log periodic BGSAVE, client connections, or eviction events.
3. **Don't anchor on the first plausible explanation.** The Druid `removeAbandoned` finding was valid but incomplete. Always ask: "Does this explanation account for ALL observed symptoms?"
4. **Trace component dependencies before diving into infrastructure.** Before checking kubelet, CNI, or disk IO, trace what components the failing request depends on.
5. **Middleware-first for business failures.** When all Pods are Running and healthy, the problem is overwhelmingly likely to be in a middleware component.