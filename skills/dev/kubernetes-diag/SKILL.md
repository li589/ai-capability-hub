---
name: kubernetes-diag
description: Diagnose Kubernetes node and control-plane failures, and perform proactive cluster health inspections. Analyzes kubelet, containerd, crictl, CNI, flannel, kube-proxy, etcd, OS resources, time sync, and network data. Use when investigating K8s NodeNotReady, SandboxChanged, CrashLoopBackOff, container runtime drift, cgroup driver mismatch, Service ClusterIP failures, multi-master control-plane recovery issues, or when performing cluster health inspection, patrol, 巡检, post-deploy verification, or periodic health check.
install_source: official
install_method: download
skill_id: 061bb0d9-7abc-4c81-b781-cd7b34f1b7b0
enabled_at: 1787232491559
version: 1.0.1
name_zh: Kubernetes 诊断
---

# Kubernetes Diagnostic Workflow

Diagnose Kubernetes node failures by collecting consistent node bundles, comparing nodes horizontally, then tracing one node vertically from kubelet to container runtime, CNI, control-plane, and OS evidence.

## Quick Reference

- [intake-questions.md](reference/intake-questions.md) — Baseline fact-finding checklist. Ask only objective background, never root-cause classification.
- [collector-selection.md](reference/collector-selection.md) — Map deployment type, runtime, symptoms to collector modules.
- [component-specific-checks.md](reference/component-specific-checks.md) — When and how to trigger per-component deep-dive scripts.
- [diagnostic-file-map.md](reference/diagnostic-file-map.md) — What each generic collected file means.
- [analysis-playbook.md](reference/analysis-playbook.md) — Layered diagnosis protocol: classify, collect evidence, decide.
- [industry-baseline.md](reference/industry-baseline.md) — Official baselines for cgroup, CRI, kube-proxy, CNI, and node debugging.
- [inspection-baseline.md](reference/inspection-baseline.md) — Health thresholds for inspection mode.
- [inspection-report-template.md](reference/inspection-report-template.md) — Inspection report output format.
- [postmortem-template.md](reference/postmortem-template.md) — Reusable incident report template.
- [business-call-chain.md](reference/business-call-chain.md) — Reconstruct business call chains, infer component dependencies, and generate targeted verification commands.
- [redis-silent-failure.md](examples/redis-silent-failure.md) — Real-world case study: Redis silent failure misdiagnosed as database connection pool issue.

## Phase 0: Intake and Collection Plan

### Step 0.1: Mode and access gate

Ask the user to choose the working mode:

```text
A. [Diagnosis - Live] Agent is inside the customer environment and can directly execute commands on target nodes.
B. [Diagnosis - Offline] Agent is not inside the customer environment. Generate a one-shot script bundle for the customer to run, then analyze returned diagnostic bundles.
C. [Inspection] No active failure. Perform a proactive health inspection (巡检) of the cluster.
```

Default to **B** when unclear. Do not assume customer environment access.

For mode C, skip Step 0.2/0.3 symptom intake and go directly to Step 0.4 collector selection with full module set. After collection, enter Phase I (Inspection) instead of Phase 1.

### Step 0.2: Baseline facts

Use [intake-questions.md](reference/intake-questions.md).

Rules:

- Only ask objective background and recent operations.
- Never ask the user to classify the main symptom or identify root cause.
- Never include project-specific components in the baseline checklist.
- User answers are hints, not evidence. Always verify against collected bundles.
- **All baseline questions are optional.** If the user answers "unknown" or leaves an item blank, the agent must not mechanically re-ask the same question. Treat every user answer as a *hypothesis to verify* against collected bundles, never as confirmed evidence.
- **Clue-driven follow-up is allowed.** The agent may re-engage the user only when a *concrete clue* surfaces during diagnosis (for example, kubelet restarted three times at 23:00 → "did anything happen around 23:00 last night?"). Empty follow-up is forbidden.
- **Agent must actively reconstruct operation history** from observable signals when the user does not know: `journalctl` for service restart timelines, `kubectl get events` for cluster events, `/var/log/audit/audit.log` for syscalls, file mtimes under `/etc/kubernetes` and `/etc/containerd` for config drift, etcd revision growth rate for write activity. Do not passively wait for the user to volunteer it.
- **Mode B caveat.** Step 0.1 already resolved the access model and the script-host decision. This checklist assumes the mode is settled. Do not re-ask the access question ("Can the agent run commands on customer nodes?") here.

After the checklist, always ask: "Is there anything else you think is relevant?"

### Step 0.3: Open supplement

The user may provide unstructured information, screenshots, error messages, or known restrictions.

Rules:

- Treat all user-supplemented information as clues only.
- Do not use user descriptions as root cause without bundle verification.
- Allow the user to describe what they observed; do not require correct Kubernetes terminology.

### Step 0.4: Collector selection

Use [collector-selection.md](reference/collector-selection.md) to translate deployment type, runtime, symptoms, and user hints into collector modules.

Default policy: when runtime or deployment type is `unknown`, run more collectors, not fewer. Read-only collection is cheap compared to a second customer round-trip.

### Step 0.5: Normalize diagnostic bundle

All collectors write into the same output hierarchy. Both live-mode and offline-mode bundles must converge to:

```text
node-diag-<hostname>-<timestamp>/
```

Continue to Phase 1 only after bundles from all relevant nodes are normalized.

### Step 0.6: Business call chain and component dependency analysis

When a business-level symptom is reported (login failure, API returning null, page timeout), before entering node-level diagnosis, reconstruct the business call chain to identify which component is actually failing.

**1. Trace the request boundary:**
- Ask the user: "Can you find the failing request in both the frontend/ingress log and the backend log?"
- The user may use any correlation mechanism available to their system: request ID in headers, timestamp matching, source IP, URL keyword search, or their own distributed tracing system.
- If the request appears in the frontend log but NOT in the backend log: the request was likely intercepted or dropped by middleware before reaching the application. Shift focus to middleware components.
- If the request appears in both: the failure is inside the application logic, not the network path.

**2. Infer component dependencies from the failing request:**
- For each failing request, ask the user: "What data does this endpoint read or write?"
- Trace the likely request path: User → Frontend → Backend → (Cache / Database / Message Queue / Coordination Service).
- User answers are clues, not confirmed facts. Verify by checking the component's logs or state.

**3. Middleware-first principle:**
When all Pods are Running and healthy but a business operation fails, the problem is overwhelmingly likely in a middleware component. Check in priority order: cache (Redis, Memcached) → database → message queue → coordination service (ZK, etcd) → only then node/kubelet/CNI.

**4. Generate targeted verification commands:**
When existing logs are insufficient, generate read-only diagnostic commands specific to the inferred component and ask the user to run them. Commands must be tailored to the actual configuration and suspected failure mode, not generic templates.

For detailed methodology, see [reference/business-call-chain.md](reference/business-call-chain.md).
For a real-world case where this approach identified Redis as root cause, see [examples/redis-silent-failure.md](examples/redis-silent-failure.md).

## Phase 1: Inventory, Symptom Validation, and Timeline

Build a compact incident table before hypothesizing.

1. Identify node roles, hostnames, IPs, uptime from evidence.
2. Establish the incident window.
3. List component symptoms by node.
4. **Validate user-reported symptoms** (see below).
5. Separate first failure from later cascade.

### Step 1.4: User-reported symptom validation

User-reported abnormal Pods or services are **hypotheses to verify**, not confirmed facts.

Before accepting a user-reported Pod as evidence of service failure:

1. Check the owning controller (Deployment/ReplicaSet/DaemonSet/StatefulSet) `spec.replicas` vs `status.readyReplicas`.
2. Determine if the Pod is an orphan or historical residue:
   - `ContainerStatusUnknown` + high AGE + node reboot history = stale Pod not yet garbage-collected.
   - `deletionTimestamp` set = already terminating.
   - ATTEMPT count far exceeding peers with same AGE = sandbox churn residue.
3. Verify actual service availability: are there enough Running+Ready replicas to satisfy the controller's desired count?
4. Output a verdict per reported Pod:

```text
Pod: <ns>/<name>
Status: <phase> / <container statuses>
Controller: <kind>/<name>, desired=<N>, ready=<M>
Verdict: [STALE - safe to delete] | [ACTIVE FAILURE - requires diagnosis] | [TRANSIENT - monitor]
Reason: <one-line evidence-based explanation>
```

Rules:

- A single non-Running Pod in a ReplicaSet with sufficient healthy replicas does NOT constitute a service failure.
- `ContainerStatusUnknown` after node restart means kubelet lost container state; it is not a crash.
- Never present stale Pods as root cause evidence. Present them as "observed, assessed, non-impacting".

## Phase 2: Horizontal Runtime Diff

Always compare failing node against healthy peers.

Mandatory diff fields: kubelet cgroupDriver, effective SystemdCgroup, containerd version, runc version, cgroup filesystem, CRI endpoint, CNI config paths.

Use `crictl info` or `containerd config dump` for effective values. Do not rely on raw grep of config files.

## Phase 3: Kubelet and Containerd Restart Chain

Trace whether containers exit by themselves or are killed by kubelet/containerd.

Interpretation rules:

- `received signal; shutting down` in etcd usually means external SIGTERM.
- `SandboxChanged`, `No ready sandbox`, `KillPod: true` point to kubelet sandbox reconciliation.
- Growing `ATTEMPT` across unrelated containers means node/runtime-level churn.

## Phase 4: CNI, Service Network, and Control-Plane Entrypoint

Verify cni0, flannel.1, subnet.env, kube-proxy, IPVS/iptables, and Service VIP reachability.

Only test for project-specific control-plane entrypoints when user evidence or collected data confirms that deployment model.

## Phase 5: OS Resource, Kernel, Time, and External Trigger Checks

Rule in/out host-level causes only with concrete evidence: OOM killer, hung task, filesystem readonly, severe IO errors, large time jumps.

## Phase 6: Root Cause Hypothesis Matrix

Output a ranked table. Hypothesis classes: runtime/cgroup drift, sandbox state corruption, CNI mismatch, service proxy failure, control-plane entrypoint failure, OS/kernel/resource/time issue, external automation or package change.

## Phase 7: Fix Recommendation

By blast radius: effective config repair, restart, CNI repair, controlled reset/rejoin, node rebuild.

## Phase I: Inspection Mode (mode C only)

When the user selected mode C (no active failure), follow this path instead of Phase 1-8.

### Phase I-1: Full-spectrum collection

Run the default collector set (all modules). No symptom-based filtering.

### Phase I-2: Baseline comparison

Use [inspection-baseline.md](reference/inspection-baseline.md) to score each dimension:

1. Runtime config consistency across nodes (horizontal diff).
2. Certificate expiry (warn < 30d, critical < 7d).
3. Resource pressure (disk > 80%, memory > 90%, IO wait > 30%).
4. Time sync drift (offset > 100ms).
5. Container restart anomalies (ATTEMPT growing without active failure).
6. CNI/Service network integrity.
7. etcd cluster health (member list, endpoint health, db size).
8. Package version consistency across nodes.
9. Stale/orphan Pod inventory.

### Phase I-3: Inspection report

Use [inspection-report-template.md](reference/inspection-report-template.md).

Output a health score (0-100), risk items by severity, and recommended actions.

Do NOT produce a root-cause analysis or postmortem for inspection mode.

## Phase 8: Postmortem Report

Use [postmortem-template.md](reference/postmortem-template.md). **Must include all of:** timeline, evidence table, root cause (layered), why earlier signals were missed, fix actions, **prevention measures** (mandatory), and reusable lessons. The Prevention section must propose concrete process/tooling/config changes that would have prevented or detected this failure earlier. Do not skip or leave it generic — each preventive action must reference the specific evidence that justifies it.

## Important Rules

1. Ask Step 0.1 mode and access first. Do not skip.
2. Baseline facts only. Never make the user classify the root cause.
3. User answers are hints. Collected evidence is truth.
4. Compare peer nodes horizontally before deep-diving one node.
5. `crictl info` and `containerd config dump` for effective runtime values, not raw config grep.
6. `RuntimeReady=true` means liveness only, not configuration correctness.
7. `SandboxChanged` is a symptom requiring upstream analysis.
8. Separate generic Kubernetes facts from installer-specific behavior.
9. When deployment type or runtime is unknown, collect more, not fewer, read-only modules.
10. Collectors can be modular. Analysis must converge to one workflow.
11. Prefer evidence tables over narrative guesses.
12. Do not mutate customer systems during diagnosis.
13. **Pod status ≠ service status.** A non-Running Pod is a hypothesis, not a fact. Always verify controller replicas before accepting it as evidence of failure.
14. **Stale Pods are not incidents.** `ContainerStatusUnknown` or `Evicted` Pods with high AGE after node restarts are garbage-collection lag, not active failures. Classify and dismiss them explicitly.
15. **Inspection mode produces a health report, not a root-cause analysis.** Do not force-fit inspection findings into the diagnosis Phase 1-8 flow.
16. **Dynamic collection is encouraged.** When analysis (Phase 2-7) reveals that fixed modules cannot answer the current question, generate a targeted script or command on the spot. Constraints only: (a) read-only; (b) bounded by timeout; (c) output goes to `$OUTDIR/dynamic/`; (d) mode A executes directly, mode B delivers per one-shot execution standard; (e) form is dictated by the specific problem — no fixed template.
17. **Middleware-first for business failures.** When all Pods are Running and healthy but a business operation fails, trace the call chain and check middleware dependencies (Redis → DB → MQ → ZK) before investigating infrastructure. Middleware failures often produce silent failures — HTTP 200 with null payload, no exceptions, no ERROR logs. See [Step 0.6](#step-06-business-call-chain-and-component-dependency-analysis).
