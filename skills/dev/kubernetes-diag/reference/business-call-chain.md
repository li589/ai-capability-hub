# Business Call Chain and Component Dependency Analysis

When a business-level symptom is reported (login failure, API returning null, page timeout), do NOT immediately jump to node-level diagnosis. Trace the request boundary first.

## Step 1: Trace the request boundary

1. Ask the user: **"Can you find the failing request in both the frontend/ingress log and the backend application log?"**

2. The user may use any correlation mechanism their system provides:
   - Distributed tracing ID (e.g., Jaeger, Zipkin, OpenTelemetry traceId)
   - Request ID from HTTP headers (e.g., `X-Request-Id`, `X-Trace-Id`)
   - Timestamp matching (± a few seconds)
   - Source IP of the request
   - URL path keyword search (e.g., grep for "login" or "getPublicKey")

3. Interpret the result:

| Frontend log | Backend log | Meaning | Action |
|:---:|:---:|---|---|
| ✅ Found | ❌ Not found | Request was **intercepted or dropped before reaching application** | Investigate middleware: proxy, cache, message queue, API gateway |
| ✅ Found | ✅ Found | Request reached the application | Investigate application logic, downstream calls, error handling |
| ❌ Not found | — | Request never reached the cluster | Investigate client-side, DNS, external load balancer, firewall |

## Step 2: Infer component dependencies from the failing request

For each failing request, ask the user:

- **"What data does this endpoint read or write?"**
- **"Which storage or service backs this data?"**

Guide the user by asking about the typical layers:

```
User → Frontend (nginx, CDN)
     → Backend (application Pod)
        → Cache layer? (Redis, Memcached, local cache)
        → Database? (PostgreSQL, MySQL, MongoDB)
        → Message queue? (RabbitMQ, Kafka)
        → Coordination? (Zookeeper, etcd)
        → External API? (third-party service)
```

**The user's answers are clues, not confirmed facts.** Always verify by checking the suspected component's logs, connectivity, and state.

## Step 3: Middleware-first principle

When all application Pods are Running and healthy but a business operation fails, the problem is overwhelmingly likely in a middleware component — NOT in Kubernetes itself.

**Why:** Infrastructure failures (node, kubelet, CNI) produce broad, visible symptoms: Pod restarts, NotReady status, network timeouts across many services. Middleware failures often produce **silent failures** — the application returns HTTP 200 with null/empty data, without throwing exceptions or writing ERROR logs. The middleware component itself may also have no error logs.

**Diagnostic priority order:**

1. **Cache** (Redis, Memcached) — returns stale/null data, connection silently broken
2. **Database** — connection pool exhaustion, slow queries, dead connections
3. **Message Queue** (RabbitMQ, Kafka) — queue buildup, silent disconnection
4. **Coordination Service** (ZK, etcd) — stale data, election issues
5. **Only then:** node health, kubelet, CNI, OS

## Step 4: Generate targeted verification commands

When existing logs are insufficient to determine the root cause, generate **read-only diagnostic commands** specific to the inferred component and ask the user to run them.

**Rules for generated commands:**
- Must be read-only (no mutations).
- Must be bounded by timeout.
- Must be specific to the component and the suspected failure mode.
- Must use the actual connection parameters (host, port, credentials) from the user's configuration.
- Must NOT be generic templates — tailor them to the specific situation.

**Template for asking the user:**

```text
The failing request <URI> likely reads from <component>. Let me verify:

From your configuration (<config source>), the connection is <host>:<port>.
Run these read-only checks:

<command 1>  # checks <what>
<command 2>  # checks <what>

Please share the output.
```

## Step 5: When to stop and ask for more data

If after steps 1-4 the root cause is still unclear, do NOT continue guessing. Instead:

1. State what you have ruled out and why.
2. State what remains unknown.
3. Ask the user for specific additional data (logs from a specific component, configuration values, timestamps).
4. If the user cannot provide the data, generate a script that collects it.
