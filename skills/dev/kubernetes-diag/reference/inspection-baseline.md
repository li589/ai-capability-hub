# Inspection Baseline

Health thresholds for proactive cluster inspection (mode C). Score each dimension as HEALTHY / WARNING / CRITICAL.

## Scoring Rules

- Each dimension contributes equally to the overall health score (0-100).
- HEALTHY = full points for that dimension.
- WARNING = half points.
- CRITICAL = zero points.
- Overall score = sum of dimension scores / total dimensions * 100, rounded.

## Dimensions

### 1. Runtime Config Consistency

Source: `00-runtime-summary.txt`, `19-crictl-info.txt` across all nodes.

| Status | Condition |
|--------|-----------|
| HEALTHY | All nodes identical: cgroupDriver, SystemdCgroup, containerd version, runtimeType, CRI endpoint, CNI paths |
| WARNING | Minor version difference (patch level) but cgroup/SystemdCgroup consistent |
| CRITICAL | Any node differs in cgroupDriver, SystemdCgroup, or runtimeType |

### 2. Certificate Expiry

Source: `27c-cert-dates.txt`.

| Status | Condition |
|--------|-----------|
| HEALTHY | All certs expire > 30 days from now |
| WARNING | Any cert expires in 7-30 days |
| CRITICAL | Any cert expires < 7 days or already expired |

### 3. Resource Pressure

Source: `12-free.txt`, `13-df.txt`, `14-iostat.txt`, `06-vmstat.txt`.

| Status | Condition |
|--------|-----------|
| HEALTHY | Disk < 80%, memory < 85%, IO wait < 20%, CPU steal < 5% |
| WARNING | Disk 80-90%, or memory 85-95%, or IO wait 20-40%, or steal 5-15% |
| CRITICAL | Disk > 90%, or memory > 95%, or IO wait > 40%, or steal > 15%, or filesystem readonly |

Check these paths specifically: `/var/lib/etcd`, `/var/lib/containerd`, `/var/lib/kubelet`, `/var/lib/cni`, `/`.

### 4. Time Sync

Source: `15-timedatectl.txt`, `16-chronyc-tracking.txt`.

| Status | Condition |
|--------|-----------|
| HEALTHY | NTP enabled, offset < 50ms |
| WARNING | Offset 50-500ms, or NTP source degraded |
| CRITICAL | NTP disabled, or offset > 500ms, or no reachable source |

### 5. Container Restart Anomalies

Source: `17-crictl-ps-a.txt`, `17b-crictl-pods.txt`.

| Status | Condition |
|--------|-----------|
| HEALTHY | No unexpected restarts. ATTEMPT stable. Stale Pods identified and classified |
| WARNING | 1-2 containers with growing ATTEMPT but service still available |
| CRITICAL | Multiple unrelated containers restarting, or control-plane components restarting |

Note: Apply the Pod Status ≠ Service Status Protocol. Stale Pods (ContainerStatusUnknown + high AGE + replicas satisfied) are classified as STALE and do NOT count as anomalies.

### 6. CNI / Service Network Integrity

Source: `24c-cni-flannel-state.txt`, `24d-service-proxy-state.txt`, `20-kube-proxy-container.log`, `20-flannel-container.log`.

| Status | Condition |
|--------|-----------|
| HEALTHY | cni0/flannel.1 present, subnet.env exists, kube-proxy Running, IPVS/iptables rules populated |
| WARNING | Minor: flannel log shows transient apiserver timeout, or kube-proxy restart count > 0 but currently Running |
| CRITICAL | cni0 missing, subnet.env missing, kube-proxy not Running, or no KUBE iptables/IPVS rules |

### 7. etcd Cluster Health

Source: `etcd-member-list.txt`, `etcd-ports.txt`, `etcd-data-size.txt`, `20-etcd-container.log`.

| Status | Condition |
|--------|-----------|
| HEALTHY | All members started, endpoint health OK, db size < 2GB, no corruption errors |
| WARNING | db size 2-6GB, or one member recently restarted but currently healthy |
| CRITICAL | Member list incomplete, endpoint unhealthy, corruption detected, or db size > 6GB |

### 8. Package Version Consistency

Source: `25c-package-history.txt`, `00-runtime-summary.txt`.

| Status | Condition |
|--------|-----------|
| HEALTHY | All nodes same containerd/runc/kubelet version. No recent unattended upgrades |
| WARNING | Patch-level difference between nodes, or recent upgrade detected but consistent |
| CRITICAL | Major/minor version mismatch between nodes, or evidence of partial upgrade |

### 9. Stale / Orphan Pod Inventory

Source: `kubectl get pods -A` (if apiserver reachable), `17-crictl-ps-a.txt`.

| Status | Condition |
|--------|-----------|
| HEALTHY | No stale Pods, or all stale Pods identified with STALE verdict |
| WARNING | 1-5 stale Pods pending GC (safe to delete) |
| CRITICAL | > 5 stale Pods accumulating, suggesting GC mechanism broken |

Note: Stale Pods do not impact service but indicate housekeeping debt.

## Threshold Override

Users may specify custom thresholds. If provided, override defaults and note the override in the report.

## Multi-node Aggregation

- Report per-node scores AND cluster-wide score.
- Cluster score = lowest node score (weakest link principle).
- List per-node deviations in the risk items.
