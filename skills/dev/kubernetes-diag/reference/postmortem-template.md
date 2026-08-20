# Postmortem Template

Use this template after completing the diagnostic workflow.

## Title

Use a concrete title:

```text
[cluster/node] [main symptom] caused by [confirmed root cause]
```

Example:

```text
master01 control-plane restart loop caused by containerd cgroup config drift and missing installer control-plane entrypoint
```

## Incident Overview

Include:

- customer/environment context;
- affected nodes;
- affected components;
- user-visible impact;
- time window.

Template:

```markdown
## 事件概述 → Incident Overview

[Environment] experienced [symptoms] around [time window]. Primary impact on [nodes/components], user-visible as [impact description].
```

## Impact

Separate cluster-wide impact from node-local impact.

```markdown
## 影响范围 → Impact scope

- Node impact: ...
- Control-plane impact: ...
- Workload Pod impact: ...
- etcd quorum affected: ...
```

## Final Root Cause

Use a layered root cause structure.

```markdown
## 最终根因 → Final root cause

### Upper-layer cause
[External change, config drift, upgrade, recovery step omission]

### Mid-layer mechanism
[kubelet/containerd/CNI/control-plane dependency behavior]

### Lower-layer trigger
[reboot, cold start, service proxy, haproxy, stale CNI state]
```

## Evidence Chain

Use a table:

```markdown
| Evidence | Source file | Meaning |
|---|---|---|
| `SystemdCgroup=false` on failing node | `19-crictl-info.txt` | runtime effective config differs from peers |
| `received signal; shutting down` | `20-etcd-container.log` | etcd was externally stopped |
```

## Timeline

Use exact timestamps when available.

```markdown
## 时间线 → Timeline

| Time | Event | Evidence |
|---|---|---|
| HH:MM | Node rebooted | `08-uptime.txt` |
| HH:MM | kubelet started killing sandbox | `01-kubelet.log` |
```

## What Made It Hard

Name diagnostic traps directly.

Examples:

- CNI error was real but not the full root cause.
- `RuntimeReady=true` hid runtime config drift.
- `SystemdCgroup=false` was present in early data but not horizontally diffed.
- haproxy 6444 is installer-specific, not generic Kubernetes.

## Fix

Include exact actions and verification.

```markdown
## 修复方案 → Fix

1. [Action]
   - Why: ...
   - Verify: ...
   - Risk: ...
```

## Prevention

Include process and tooling changes.

```markdown
## 预防措施 → Prevention

- Add runtime config horizontal diff to diagnostic scripts.
- Pin or validate containerd/runc versions.
- Verify effective `SystemdCgroup`, not only config file text.
- Add installer-specific haproxy 6444 check when applicable.
```

## Reusable Lessons

Keep this short and general.

```markdown
## 可复用经验 → Reusable lessons

- `RuntimeReady=true` does not mean runtime config is correct.
- `SandboxChanged` is a symptom, not a root cause.
- Multi-node clusters must compare against healthy peers horizontally.
```

## Built-in Case Example

Use this only when it matches evidence.

```text
customer installed/upgraded containerd
  -> master01 config format changed to containerd v2/v3 style
  -> effective SystemdCgroup=false on master01
  -> master02/master03 effective SystemdCgroup=true
  -> kubelet uses cgroupDriver=systemd
  -> kubelet/containerd disagree on sandbox/cgroup state
  -> reboot triggers cold recreation of all runtime state
  -> kubelet repeatedly StopContainer/StopPodSandbox
  -> etcd/apiserver/flannel/kube-proxy appear unstable
  -> installer-specific haproxy 6444 omission amplifies service-network failure
```

Do not use this chain blindly. Replace any unmatched step with the actual evidence.

## Customer Explanation Snippet

```text
This incident was not a single container or etcd data corruption failure. It was a compounded node runtime configuration and control-plane recovery chain issue. The failing node's effective containerd config differed from healthy control-plane nodes. kubelet and containerd disagreed on Pod sandbox/cgroup state. After reboot, all cold-start paths recreated runtime state, causing kubelet to repeatedly StopContainer/StopPodSandbox. The recovery flow also required restoring the installer-specific control-plane entrypoint; without it, kube-proxy and flannel would remain affected.
```
