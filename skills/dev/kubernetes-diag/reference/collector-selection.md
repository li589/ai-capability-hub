# Collector Selection Map

Translate deployment type, runtime, symptoms, and user hints into which collector modules to run.

## Rules

- Unknown → run more, not fewer.
- All modules are read-only.
- User-discovered hints are clues, not replacement for modules.
- Collectors produce normalized output into one bundle directory.

## Always run

| Module | When |
|---|---|
| `diag-core.sh` | always |
| `diag-kubelet.sh` | always |

## By deployment type

| Module | When |
|---|---|
| `diag-kubeadm-controlplane.sh` | kubeadm / self-managed control-plane / unknown |
| `diag-k3s.sh` | k3s / unknown |

## By container runtime

| Module | When |
|---|---|
| `diag-containerd.sh` | containerd / unknown |
| `diag-docker.sh` | docker / cri-dockerd / unknown |

## By symptom or user hint

| Module | When |
|---|---|
| `diag-cni-service.sh` | Pod sandbox network failures, Service ClusterIP unreachable, DNS failures, unknown |
| `diag-etcd.sh` | control-plane / etcd cluster / apiserver startup failures / unknown |
| `diag-k8s-resource.sh <type> <ns?> <pattern>` | any specific Pod, Deployment, DaemonSet, StatefulSet, Service named by user |
| `diag-systemd-service.sh <pattern>` | any specific systemd service named by user (e.g. kubelet, containerd, haproxy) |

## By specific component hint

Use [component-specific-checks.md](component-specific-checks.md) to decide when to trigger deep-dive per-component checks that are not universal Kubernetes.

## Default collector set (offline, unknown cluster)

```text
diag-core.sh
diag-kubelet.sh
diag-containerd.sh
diag-docker.sh
diag-kubeadm-controlplane.sh
diag-k3s.sh
diag-cni-service.sh
diag-etcd.sh
```

## Scope note

This file is generic Kubernetes. Project-specific or installer-specific checks are NOT listed in the default set. They are triggered by [component-specific-checks.md](component-specific-checks.md) only when user evidence or collected data confirms the deployment model.
