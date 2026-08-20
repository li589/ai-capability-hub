# Industry Baseline

Use this file to calibrate diagnosis against Kubernetes official behavior and common production practice.

## Cgroup driver consistency

Official Kubernetes guidance states that when kubelet uses the `systemd` cgroup driver, the container runtime must also use `systemd` as its cgroup driver.

References:

- Kubernetes Container Runtimes: https://kubernetes.io/docs/setup/production-environment/container-runtimes/
- Kubernetes Configure cgroup driver: https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/configure-cgroup-driver/

Operational baseline:

```text
OS cgroup v2 + kubelet cgroupDriver=systemd + containerd/runc SystemdCgroup=true
```

What to verify:

```bash
stat -fc %T /sys/fs/cgroup
grep -i cgroupDriver /var/lib/kubelet/config.yaml
crictl info | grep -i SystemdCgroup
containerd config dump | grep -i -A20 -B5 SystemdCgroup
```

Important pitfall:

`/etc/containerd/config.toml` can contain multiple config paths or later override blocks. Effective values from `crictl info` or `containerd config dump` are stronger evidence than raw grep.

## Container runtime debugging with crictl

Kubernetes documents `crictl` as the command-line tool for inspecting CRI-compatible runtimes on nodes.

Reference:

- Debugging Kubernetes nodes with crictl: https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/

Baseline commands:

```bash
crictl info
crictl pods
crictl ps -a
crictl logs <container-id>
crictl stats -a
```

Interpretation:

- `crictl info` gives effective CRI runtime configuration.
- `crictl ps -a` shows restart patterns and attempt counts.
- `crictl logs` confirms whether an app crashed or received external termination.

## kubelet and sandbox reconciliation

Kubelet is the node agent. It continuously reconciles desired Pod state with the container runtime state.

Baseline interpretation:

```text
SandboxChanged
No ready sandbox
CreatePodSandbox
StopPodSandbox
Killing container
```

These messages mean kubelet is acting on Pod sandbox state. They are not root causes by themselves.

Use them to trace upward:

```text
Why did kubelet think the sandbox changed?
Was runtime state stale?
Did CNI fail?
Did cgroup/runtime config drift?
Did kubelet relist multiple old sandboxes?
```

## etcd static Pod diagnosis

In kubeadm-style control planes, etcd usually runs as a static Pod managed by kubelet.

Baseline evidence:

```text
opened backend db
recovered v3 backend from snapshot
initial corruption checking passed; no corruption
ready to serve client requests
received signal; shutting down
```

Interpretation:

- Ready + corruption check passed means etcd data is probably not corrupted.
- `received signal; shutting down` points to external stop, often kubelet/containerd.
- apiserver readiness depends on local etcd when configured with `--etcd-servers=https://127.0.0.1:2379`.

## CNI and flannel baseline

flannel commonly writes runtime subnet information to:

```text
/run/flannel/subnet.env
```

CNI plugin errors such as this block ordinary Pod sandbox creation:

```text
loadFlannelSubnetEnv failed: open /run/flannel/subnet.env: no such file or directory
```

Interpretation:

- If flannel cannot reach apiserver, `subnet.env` may not be written.
- If `cni0` has an address outside the node PodCIDR, local CNI state is stale.
- Do not fix flannel in isolation until apiserver and kube-proxy reachability are understood.

## kube-proxy and Service VIP baseline

Kubernetes Service ClusterIPs are implemented by kube-proxy using a service proxy mode such as iptables, IPVS, or nftables.

Reference:

- Virtual IPs and Service Proxies: https://kubernetes.io/docs/reference/networking/virtual-ips/

For IPVS mode, kube-proxy checks kernel IPVS modules. Low-impact checks:

```bash
lsmod | grep -E '^ip_vs|^nf_conntrack'
ip addr show kube-ipvs0
cat /proc/net/ip_vs
iptables-save -t nat | grep KUBE
```

Interpretation:

- `10.96.0.1:443` timeout from a Pod usually means service proxy path, apiserver endpoint, or local network proxying is broken.
- kube-proxy must reach apiserver to watch Services and Endpoints.

## Project-specific control-plane entrypoint

Some installer designs use local haproxy on `127.0.0.1:6444` as the apiserver entrypoint for local components.

This is not universal Kubernetes behavior.

For kapp/kURL-style environments where this is documented as required, verify:

```bash
ss -tlnp | grep 6444
curl -k --max-time 3 https://127.0.0.1:6444/readyz
```

If kube-proxy logs show `https://localhost:6444` connection refused, missing haproxy is a direct control-plane entrypoint failure for that deployment design.

## Cold-start versus warm-state baseline

A node can appear healthy before reboot because old runtime state still exists:

```text
old containers
old Pod sandboxes
old cgroups
old veth/netns
old /run/flannel/subnet.env
old kube-proxy rules
```

After reboot, all ephemeral state must be recreated. That is when config drift becomes visible.

Cold-start analysis should always ask:

```text
What is created first?
What depends on it?
Which dependency is missing when the first failure appears?
```

## Minimum peer comparison baseline

For multi-master or homogeneous worker pools, always compare at least one healthy peer.

Required peer diff fields:

```text
OS/kernel
containerd version
runc version
containerd config format
kubelet cgroup driver
effective SystemdCgroup
CNI config path
CRI endpoint
node labels/roles
PodCIDR
```

Do not conclude from one node alone unless no peer exists.
