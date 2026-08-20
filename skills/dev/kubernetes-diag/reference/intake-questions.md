# Baseline Intake Questions

Ask these before collecting any diagnostic data. Only ask objective, answerable facts. Never ask the user to classify the root cause or name the primary symptom.

## Ground rules (read this first)

All questions in this checklist are **optional**. For any item, the user may answer "unknown", leave it blank, or skip it entirely. The agent will:

- Run diagnostic scripts to collect and verify all of the data automatically.
- Treat every user answer as a **hypothesis to verify**, never as confirmed evidence.
- Cross-check user descriptions against the actual collected bundles in later phases.

**Only exception — mode B (offline):** the agent still needs to know on which node(s) the customer can run the collection script. That is handled in Step 0.1 (mode and access gate), not in this checklist. Do not re-ask the access question here.

**Forbidden follow-up:** if the user answers "unknown" or leaves an item blank, the agent must not mechanically re-ask the same question. The agent may re-engage the user only if a *concrete clue* surfaces during diagnosis (for example, kubelet restarted three times at 23:00 — then it is fair to ask "did anything happen around 23:00 last night?"). Empty follow-up is not allowed.

## Group A — agent auto-collects and verifies (answering is optional)

These facts are obtainable from the cluster or the node environment. The agent will collect and verify them regardless of the user's answer. User input is treated as a hint that may speed up triage, never as ground truth.

1. How many nodes in total? How many control-plane/master, how many worker? *(Optional — answer "unknown" if unsure.)*
2. Which nodes are currently considered problematic? Include hostname or IP if known. *(Optional — answer "unknown" if unsure.)*
3. What is the Kubernetes deployment type? *(Optional — answer "unknown" if unsure.)*
   - kubeadm
   - k3s
   - rke / rke2
   - Managed cloud K8s
   - Self-built installer
   - Unknown
4. What container runtime is used? *(Optional — answer "unknown" if unsure.)*
   - containerd
   - docker / cri-dockerd
   - CRI-O
   - Unknown

## Group B — high-value hint, agent cannot infer from the environment (strongly encouraged)

The agent has no way to read "what the user clicked yesterday" from the cluster. If the user happens to know, this is gold. If they do not, the agent will fall back to observable evidence on each node.

5. What operations happened right before the problem started? *(Optional — answer "unknown" if unsure.)*
   - Reboot?
   - OS or package upgrade?
   - VM configuration change (CPU, memory, disk)?
   - Runtime change (containerd/docker upgrade or config modification)?
   - Kubernetes operation (kubeadm reset/join, certificate rotation)?
   - CNI or network change?
   - Manual script or automation run?
   - Unknown (write "unknown")

   **How the agent infers when the user does not know:**
   - `journalctl -u kubelet --since "24h ago"` → kubelet restart timeline
   - `kubectl get events --sort-by=.lastTimestamp` → cluster event timeline
   - `/var/log/audit/audit.log` → syscall-level change record
   - File mtimes under `/etc/kubernetes`, `/etc/containerd`, `/var/lib/etcd` → config drift
   - etcd revision growth rate → recent write activity
   - User shell history if accessible

6. When did the problem first occur, and when was it first noticed? *(Optional — answer "unknown" if unsure.)*
   - Approximate onset time (when the problem likely started)
   - First detection time (when someone noticed the symptom)
   - Time gap between onset and detection (e.g., "started at 14:00, noticed at 16:00")

   **Why time window matters:** knowing the onset→detection window is critical for `journalctl --since` and event backtracking depth. A silent failure with a large gap requires wider collection; a sudden crash requires tight focus.

   **How the agent infers when the user does not know:**
   - Default to broad window: `journalctl --since "7 days ago"` on all nodes
   - Narrow down by log density: identify restart spikes, error bursts
   - Cross-reference `kubectl get events --sort-by=.lastTimestamp` for cluster-wide timeline
   - If onset still unclear after first-pass analysis, expand collection to `--since "14 days ago"`

## Open supplement

7. Is there anything else that might be relevant? Any error messages, screenshots, observability data, restrictions, or context you think might help?

   Write "nothing else" if not applicable.

## Rules

- User answers are hints, not evidence. Always verify against collected node bundles.
- Do not skip collection because a user said something looks normal.
- Do not change the analysis direction based on user symptom labels alone.
- The final report should compare the initial user description with the actual evidence findings.
- If the user says "unknown" on any item, the agent must not mechanically re-ask. The agent may only re-engage with a *concrete clue* found in the data.
- The agent must actively reconstruct operation history from observable signals (journalctl, audit log, events, file mtimes), instead of passively waiting for the user to volunteer it.
- The "Can the agent run commands on customer nodes?" question is the Step 0.1 mode gate, not part of this baseline. Do not re-ask it here.
