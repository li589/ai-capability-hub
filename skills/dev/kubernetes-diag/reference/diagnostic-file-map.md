# Diagnostic File Map

This reference maps diagnostic bundle output files to concrete analysis tasks. Use it after bundles from all relevant nodes have been normalized into `node-diag-<hostname>-<timestamp>/` directories.

Only generic Kubernetes files are listed here. Project-specific or installer-specific files are described in `component-specific-checks.md`.

## 00-runtime-summary.txt

### What to look for
- cgroup filesystem, usually `cgroup2fs` on modern Linux.
- kubelet `cgroupDriver`.
- containerd and runc versions.
- effective `SystemdCgroup` from `crictl info` and `containerd config dump`.
- CRI endpoint, rootDir, stateDir, CNI config paths.

### Horizontal comparison
Compare failing node against healthy peers. A single differing runtime field on the failing node is high-signal.

### Warning signals
- Failing node `SystemdCgroup=false`, healthy peers `true`.
- Different containerd major version or config format.
- Different CRI endpoint path.
- Different CNI conf_dir/bin_dirs.

## 01-kubelet.log / 01c-kubelet-grep.log

### What to look for
- `SandboxChanged`
- `No ready sandbox`
- `CreatePodSandbox`
- `StopPodSandbox`
- `Killing container`
- `PLEG is not healthy`
- probe failures and `BackOff`
- `failed to setup network`

### Interpretation
These logs show kubelet's decision. If kubelet says `KillPod: true` or `SandboxChanged`, container exit is usually orchestration-driven, not app-driven.

### Case pattern
`SandboxChanged` plus many unrelated containers restarting indicates node/runtime-level churn.

## 02-kubelet-status.txt

### What to look for
- kubelet service active state.
- `NRestarts`.
- service restart timestamps.

### Interpretation
If kubelet itself restarts frequently, prioritize systemd/unit/resource issues. If kubelet is stable but Pods churn, prioritize runtime/sandbox/CNI state.

## 03-containerd.log / 03b-containerd-grep.log

### What to look for
- `StopContainer`
- `StopPodSandbox`
- `exit_status`
- `shim disconnected`
- cgroup errors
- timeout/deadline/OOM/panic

### Interpretation
- `exit_status:143` means SIGTERM.
- `exit_status:137` often means SIGKILL or forced sandbox teardown.
- Stop events aligned with kubelet `Killing container` confirm kubelet/containerd-driven exits.

## 04-containerd-status.txt

### What to look for
- containerd service active state.
- `NRestarts`.

### Interpretation
If containerd service is stable while containers restart, do not call it a containerd daemon crash. Look at CRI reconciliation and kubelet decisions.

## 05-crictl-restart-pattern.txt / 17-crictl-ps-a.txt

### What to look for
- container `ATTEMPT` counts.
- created timestamps.
- Running vs Exited distribution.
- whether many unrelated components restart together.

### Interpretation
- One app restarting points to app/container issue.
- etcd, apiserver, flannel, kube-proxy, node-exporter all increasing attempts points to node/runtime-level issue.

## 06-vmstat.txt / 07-mpstat.txt / 08-uptime.txt / 10-lscpu.txt

### What to look for
- CPU steal time `st`.
- run queue and load.
- CPU topology after VM changes.
- uptime relative to incident time.

### Interpretation
High steal or severe CPU starvation can explain timeouts, but not persistent `SystemdCgroup` mismatch. Treat CPU pressure as contributing evidence unless logs show direct scheduling failure.

## 09-hostnamectl.txt

### What to look for
- OS version.
- kernel version.
- virtualization platform.
- hostname consistency.

### Interpretation
Use it for environment inventory and to compare node versions.

## 11-dmesg.txt / 11b-dmesg-grep.txt

### What to look for
- OOM killer.
- soft lockup / hung task.
- filesystem readonly.
- disk I/O errors.
- kernel panic.

### Interpretation
Do not blame OS/kernel without these signals.

## 12-free.txt / 13-df.txt / 13b-du-etcd-containerd.txt / 14-iostat.txt

### What to look for
- memory pressure.
- disk full.
- etcd/containerd/kubelet/CNI data directory size.
- disk latency and utilization.

### Interpretation
Disk full or high I/O wait can break etcd/containerd. If clean, keep focus on runtime/CNI/control-plane chain.

## 15-timedatectl.txt / 16-chronyc-tracking.txt / 16b-chronyc-sources.txt

### What to look for
- time sync enabled.
- large offset.
- unstable sources.

### Interpretation
Large time jumps can break TLS, etcd elections, leases, and apiserver readiness.

## 18-crictl-stats.txt

### What to look for
- per-container CPU/memory.
- runaway component.

### Interpretation
Useful for resource pressure, not primary for config drift.

## 19-crictl-info.txt

### What to look for
- `RuntimeReady`, `NetworkReady`.
- `defaultRuntimeName`.
- `runtimeType`.
- `options.SystemdCgroup`.
- `containerdEndpoint`.
- `rootDir`, `stateDir`.
- CNI plugin config.

### Horizontal comparison
This is one of the most important files. Compare effective runtime config across all peer nodes.

### Warning signals
- Failing node `SystemdCgroup=false`, peers `true`.
- Runtime type or endpoint differs.
- CNI config paths differ.

### Rule
`RuntimeReady=true` only means the runtime responds. It does not mean runtime config matches kubelet or peer nodes.

## 20-etcd-container.log

### What to look for
- backend open/recover.
- corruption check.
- peer activity.
- `ready to serve client requests`.
- `received signal; shutting down`.

### Interpretation
If etcd reaches ready and then receives SIGTERM, etcd data is probably not the root cause. Trace kubelet/containerd stop events.

## 20-kube-proxy-container.log

### What to look for
- kube-proxy mode: iptables/IPVS/nftables.
- apiserver connection errors.
- IPVS module errors.
- sync proxy rules errors.

### Interpretation
If Service ClusterIP is unreachable, kube-proxy log is primary evidence.

## 20d-flannel-container.log

### What to look for
- inClusterConfig access to apiserver.
- PodCIDR / subnet manager errors.
- `/run/flannel/subnet.env` creation.

### Interpretation
`subnet.env` missing can be cause for ordinary Pod sandbox failures, but often result of flannel not reaching apiserver.

## 21-kubectl-SKIPPED-see-note.txt / 21-23b kubectl files

### What to look for
- whether local apiserver was reachable.
- Node conditions.
- Pod events.
- `SandboxChanged`, `BackOff`, `Unhealthy` events.

### Interpretation
If local apiserver is skipped on failing master but works from healthy master, collect node/pod descriptions from healthy peer.

## 24-ip-link-stats.txt / 24b-ethtool-stats.txt

### What to look for
- network interface drops/errors.
- cni0/flannel.1/kube-ipvs0 existence.

### Interpretation
Use to distinguish packet loss/NIC errors from kube-proxy/CNI configuration problems.

## 24c-cni-flannel-state.txt

### What to look for
- `/etc/cni/net.d` contents.
- `/run/flannel/subnet.env`.
- `cni0` and `flannel.1` addresses.

### Interpretation
Compare node PodCIDR to `cni0` address. Mismatch is direct CNI state evidence.

## 24d-service-proxy-state.txt

### What to look for
- listening ports `2379/2380/2381/6443/6444`.
- IPVS modules.
- `kube-ipvs0`.
- `/proc/net/ip_vs`.
- `KUBE-*` iptables NAT rules.

### Interpretation
Use when Service ClusterIP such as `10.96.0.1:443` times out.

## 25-crontabs.txt / 25b-systemd-timers.txt / 25c-package-history.txt

### What to look for
- external scheduled scripts.
- package upgrade/install history.
- containerd/runc/kubelet config timestamps.

### Interpretation
Use to find customer changes, unattended upgrades, manual package installs, or automation overwriting runtime config.
