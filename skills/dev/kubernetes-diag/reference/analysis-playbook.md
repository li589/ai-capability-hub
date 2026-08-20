# Analysis Playbook

Use this playbook to turn node diagnostic bundles into a root cause report. It is intentionally layered: classify first, prove with evidence, then recommend minimal repair.

## Layer 1: Fault Classification

Classify the incident before naming a root cause.

### A. Control-plane startup failure

Typical signs:

- etcd, kube-apiserver, scheduler, controller-manager restart.
- apiserver cannot connect to `127.0.0.1:2379`.
- kube-proxy or flannel cannot reach apiserver.

Primary files:

- `20-etcd-container.log`
- kube-apiserver logs if collected by `crictl ps -a` and manual follow-up
- `20-kube-proxy-container.log`

### B. Runtime/cgroup configuration drift

Typical signs:

- failing node differs from healthy peers in `SystemdCgroup`, runtime type, containerd version, endpoint, rootDir/stateDir.
- kubelet uses `cgroupDriver: systemd` while runtime uses non-systemd cgroups.
- many unrelated Pods restart together.

Primary files:

- `00-runtime-summary.txt`
- `19-crictl-info.txt`
- `03-containerd.log`
- `01-kubelet.log`

### C. kubelet/containerd sandbox state corruption

Typical signs:

- `SandboxChanged`.
- `No ready sandbox`.
- multiple Ready/NotReady sandbox entries for one Pod.
- container exits caused by SIGTERM/SIGKILL.

Primary files:

- `01c-kubelet-grep.log`
- `03b-containerd-grep.log`
- `05-crictl-restart-pattern.txt`
- `17-crictl-ps-a.txt`

### D. CNI / PodCIDR mismatch

Typical signs:

- `failed to set bridge addr`.
- `cni0 already has an IP address different from ...`.
- `/run/flannel/subnet.env` missing.
- `cni0` address does not match Node PodCIDR.

Primary files:

- `01c-kubelet-grep.log`
- `20-flannel-container.log`
- `24c-cni-flannel-state.txt`
- kubectl node description from healthy peer if local apiserver is down.

### E. Service proxy / kube-proxy failure

Typical signs:

- Pod cannot reach `10.96.0.1:443`.
- apiserver aggregator cannot reach ClusterIP-backed services.
- `kube-ipvs0` missing VIPs.
- `/proc/net/ip_vs` empty or missing while kube-proxy is configured for IPVS.

Primary files:

- `20-kube-proxy-container.log`
- `24d-service-proxy-state.txt`
- Component-specific entrypoint checks when the installer model is confirmed.

### F. OS/kernel/resource/time issue

Typical signs:

- OOM killer.
- kernel panic / hung task / soft lockup.
- disk full or filesystem readonly.
- high IO wait.
- large chrony offset.

Primary files:

- `06-vmstat.txt`
- `11b-dmesg-grep.txt`
- `12-free.txt`
- `13-df.txt`
- `14-iostat.txt`
- `16-chronyc-tracking.txt`

### G. External automation or package/config change

Typical signs:

- package version differs from expected baseline.
- config timestamp near incident time.
- apt/dpkg history shows containerd/runc/kubelet install or upgrade.
- cron/systemd timers run around the incident.

Primary files:

- `25-crontabs.txt`
- `25b-systemd-timers.txt`
- `25c-package-history.txt`

## Layer 2: Evidence Protocol

For every hypothesis, gather evidence from at least two layers.

### Runtime drift evidence

Required:

1. Effective runtime field from `crictl info` or `containerd config dump`.
2. Peer-node contrast showing healthy nodes differ.
3. kubelet config showing expected cgroup driver.
4. symptom alignment, such as sandbox churn or broad container restart pattern.

Do not rely only on `/etc/containerd/config.toml` grep. It may contain obsolete paths or override blocks.

### etcd evidence

Required:

1. etcd startup log around backend recovery.
2. corruption check result.
3. ready-to-serve marker.
4. exit reason.

Decision:

- If etcd reaches ready then logs `received signal; shutting down`, treat etcd as externally stopped until proven otherwise.
- If etcd logs data corruption, WAL errors, or fails before ready, treat etcd storage as a primary suspect.

### CNI evidence

Required:

1. kubelet network setup error.
2. CNI config file contents.
3. `cni0` / `flannel.1` state.
4. node PodCIDR if available.

Decision:

- `cni0` mismatch is real CNI state corruption.
- `subnet.env` missing may be a consequence of flannel not reaching apiserver.

### Service proxy evidence

Required:

1. kube-proxy log.
2. Service VIP state via `kube-ipvs0`, `/proc/net/ip_vs`, or iptables NAT rules.
3. apiserver/ClusterIP timeout evidence.
4. control-plane entrypoint check if the installer uses one.

Decision:

- If kube-proxy cannot reach apiserver, Service rules may not recover.
- If IPVS modules or VIPs are missing, service ClusterIP timeouts are expected.

### OS evidence

Required:

1. dmesg signal.
2. resource pressure signal.
3. time sync signal.
4. service restart signal.

Decision:

No OS/kernel root cause without concrete kernel/resource/time evidence.

## Layer 3: Default Decisions

Use these defaults unless evidence contradicts them.

| Symptom | Default interpretation | Next evidence |
|---|---|---|
| `RuntimeReady=true` | Runtime responds, not proof of config correctness | `crictl info`, `containerd config dump`, peer diff |
| `SandboxChanged` | kubelet decided sandbox changed | kubelet PLEG logs, containerd StopPodSandbox |
| etcd `received signal` | externally stopped | kubelet/containerd stop events |
| `cni0 already has an IP address different from` | local CNI state mismatch | PodCIDR, cni0/flannel.1, CNI config |
| `/run/flannel/subnet.env` missing | flannel not initialized or cannot reach apiserver | flannel log, apiserver reachability |
| ClusterIP timeout | kube-proxy/service proxy issue or backend down | kube-proxy log, IPVS/iptables, endpoints |
| all unrelated containers restart | node/runtime/kubelet issue | crictl attempts, kubelet/containerd logs |
| single non-Running Pod, replicas satisfied | stale/orphan Pod, not a service failure | controller replicas, Pod AGE, node reboot history |
| `ContainerStatusUnknown` + high AGE | kubelet lost state after restart, GC lag | node uptime, kubelet restart count, peer Pod status |

## Pod Status ≠ Service Status Protocol

Users frequently report a non-Running Pod as proof of service failure. This is a hypothesis, not evidence.

### Mandatory verification steps

1. **Identify the owning controller**: `kubectl get pod <name> -n <ns> -o jsonpath='{.metadata.ownerReferences}'`
2. **Check replica satisfaction**: `kubectl get <kind> <name> -n <ns> -o jsonpath='{.spec.replicas} {.status.readyReplicas}'`
3. **Assess Pod staleness**:
   - AGE >> sibling Pods → likely historical residue.
   - `ContainerStatusUnknown` → kubelet lost container state (node/containerd restart).
   - `Evicted` → resource pressure at eviction time, may be resolved.
   - `deletionTimestamp` set → already terminating, awaiting GC.
4. **Verify service continuity**: Are endpoints populated? Are healthy replicas serving?

### Verdict classification

| Condition | Verdict | Action |
|-----------|---------|--------|
| readyReplicas >= desired, Pod is old/unknown/evicted | STALE | Safe to `kubectl delete pod --force --grace-period=0` |
| readyReplicas < desired, Pod is CrashLoopBackOff | ACTIVE FAILURE | Enter diagnosis Phase 2+ |
| readyReplicas >= desired, Pod restarting recently | TRANSIENT | Monitor, check events |
| No controller (static Pod / standalone) | ASSESS DIRECTLY | Use container logs + restart pattern |

### Output format

Always present the verdict to the user explicitly:

```text
Pod: envoy-gateway-system/eg-proxy-5c95964d8d-fqqnf
Status: ContainerStatusUnknown, AGE=226d, ATTEMPT=237
Controller: ReplicaSet/eg-proxy-5c95964d8d, desired=1, ready=1 (eg-proxy-5c95964d8d-hgsx6)
Verdict: STALE - safe to delete
Reason: Node restarted ~69d ago; kubelet lost state for this old replica. Current service is healthy via hgsx6.
```

### Anti-patterns

- Do NOT list a stale Pod under "findings" or "issues" without the STALE verdict.
- Do NOT use `kubectl get pods` output alone as evidence of service degradation.
- Do NOT skip replica verification even when the Pod status "looks bad".

## Horizontal Diff Procedure

1. Pick peer set: failing node plus at least one healthy node with same role.
2. Extract `00-runtime-summary.txt` and `19-crictl-info.txt` from each bundle.
3. Build a table:

```text
node | role | cgroup_fs | kubelet_cgroupDriver | containerd_version | runtimeType | SystemdCgroup | endpoint | CNI conf_dir
```

4. Mark all differing fields.
5. Treat a failing-node-only difference as high priority if it touches runtime, cgroup, CNI, or control-plane entrypoint.

## Vertical Chain Procedure

Trace the failing node in this order:

```text
kubelet decision
  -> containerd action
  -> Pod sandbox/container state
  -> etcd/apiserver readiness
  -> flannel/CNI state
  -> kube-proxy/service proxy state
  -> ordinary Pod sandbox results
```

Stop when a layer explains the next layer. Do not jump from flannel errors directly to CNI fix if apiserver/kube-proxy is unavailable.

## Cold Restart Analysis

When the symptom appears only after reboot, inspect cold-start dependencies:

```text
containerd applies current config
kubelet relists runtime state
static Pods are recreated
etcd must become ready
apiserver must connect to etcd
project-specific control-plane entrypoint may need to start
kube-proxy programs Service rules
flannel obtains PodCIDR and writes subnet.env
ordinary Pods create sandbox
```

A change can look fixed before reboot because old running containers, old cgroups, old shim processes, old veths, old `subnet.env`, and old Service rules still exist.

## Fix Recommendation Protocol

Every fix must include:

1. exact cause addressed;
2. commands or config path;
3. expected verification output;
4. risk and rollback;
5. whether it is generic Kubernetes or installer-specific.

Example:

```text
Fix: set effective containerd runc SystemdCgroup=true on master01.
Why: kubelet uses cgroupDriver=systemd and healthy peers have SystemdCgroup=true.
Verify: crictl info or containerd config dump shows SystemdCgroup=true; attempts stop increasing.
Risk: restarting containerd/kubelet may temporarily restart local Pods.
```
