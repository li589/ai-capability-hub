---
name: kubernetes-debugging
description: Debug, troubleshoot, diagnose, and analyze Kubernetes clusters with kubectl (get, describe, logs, exec, debug). Interpret pod status (CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled), analyze events, inspect containers, check resources. Use when pods crash, services fail, deployments hang, or containers won't start.
license: MIT
metadata:
  version: 1.0.0
  audience: developers
  workflow: debugging
install_source: official
install_method: download
skill_id: official_WuxVdJJF
enabled_at: 1787232489044
version: 1.0.0
name_zh: K8s调试助手
---

# Kubernetes Debugging

Diagnose and troubleshoot Kubernetes workloads using safe kubectl inspection commands. Fast incident response for pod crashes, scheduling failures, and service issues.

## What I Do

- Interpret pod statuses and identify root causes (OOMKilled, CrashLoopBackOff, ImagePullBackOff)
- Extract and analyze container logs including previous crash logs
- Debug scheduling failures, resource constraints, and node issues
- Inspect network connectivity between pods and services
- Use ephemeral debug containers for distroless/crashed pods

## When to Use Me

- Pod stuck in CrashLoopBackOff, ImagePullBackOff, Pending, or Evicted
- Container exits with OOMKilled or non-zero exit code
- Deployment rollout hangs or fails
- Service endpoints missing or not routing traffic
- Debugging distroless or crashed containers

## Quick Start

```bash
kubectl get pods -o wide                    # Pod status
kubectl describe pod <name>                 # Details + events
kubectl logs <name>                         # Container logs
kubectl logs <name> --previous              # Crash logs
kubectl get events --sort-by='.metadata.creationTimestamp'  # Recent events (reliable)
```

## Context and Namespace

```bash
# Check current context
kubectl config current-context
kubectl config get-contexts

# Switch namespace
kubectl config set-context --current --namespace=my-ns

# Explicit namespace (safer)
kubectl get pods -n production
kubectl logs -n production pod-name
```

## Diagnostic Commands

### Logs

```bash
kubectl logs <pod> -c <container>           # Specific container
kubectl logs <pod> --previous               # Previous crash
kubectl logs -f <pod>                       # Follow real-time
kubectl logs --tail=100 --since=1h <pod>    # Recent lines
```

### Interactive Shell

```bash
kubectl exec -it <pod> -- /bin/sh
kubectl exec -it <pod> -c <container> -- /bin/sh
kubectl exec <pod> -- cat /etc/config
```

### Ephemeral Debug Containers

```bash
# Add debug container to running pod
kubectl debug -it <pod> --image=busybox --target=<container>

# Create pod copy with debug container
kubectl debug <pod> -it --image=nicolaka/netshoot --copy-to=debug-pod

# Debug node (host filesystem at /host)
kubectl debug node/<node> -it --image=busybox
```

### Resources

```bash
kubectl top pods --containers
kubectl top nodes
```

## Pod Status Interpretation

| Status | Meaning | First Check |
|--------|---------|-------------|
| `CrashLoopBackOff` | Container crashing repeatedly | `kubectl logs --previous` |
| `ImagePullBackOff` | Cannot pull image | Image name, registry auth |
| `Pending` | Not scheduled | Events, node resources |
| `Evicted` | Node pressure | Node conditions |
| `OOMKilled` | Exceeded memory limit | Increase limits |
| `CreateContainerConfigError` | Missing ConfigMap/Secret | Verify config exists |

## Common Failure Modes

### CrashLoopBackOff
```bash
kubectl describe pod <name>           # Exit code in events
kubectl logs <name> --previous        # Crash logs
```
**Causes:** App error, missing config, dependency unavailable, OOM

### ImagePullBackOff
```bash
kubectl describe pod <name>           # Error in events
```
**Causes:** Typo, image doesn't exist, missing imagePullSecret

### Pending Pod
```bash
kubectl describe pod <name>           # Scheduler events
kubectl describe nodes                # Available resources
```
**Causes:** Insufficient resources, taints, PVC pending, quota exceeded

### Service Not Working
```bash
kubectl get endpoints <service>       # Pod IPs registered?
kubectl describe svc <service>        # Verify selector
```

## Networking Triage

```bash
# Check network policies
kubectl get netpol -A

# DNS debugging (from inside pod)
kubectl exec -it <pod> -- nslookup kubernetes.default
kubectl exec -it <pod> -- cat /etc/resolv.conf

# Service endpoints
kubectl get endpoints <service>
kubectl describe svc <service>

# Using netshoot for network debugging
kubectl debug <pod> -it --image=nicolaka/netshoot --target=<container>
```

## Rollout Status

```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl get replicasets -l app=<name>
kubectl describe rs <replicaset-name>
```

## Quick Decision Matrix

| Symptom | Command | Look For |
|---------|---------|----------|
| Pod not starting | `kubectl describe pod` | Events |
| App crashing | `kubectl logs --previous` | Stack trace |
| High latency | `kubectl top pods` | CPU/memory |
| Service down | `kubectl get endpoints` | Missing IPs |
| Node issues | `kubectl describe node` | Conditions |

## Context7 Integration

Use Context7 MCP server for up-to-date kubectl documentation:
- Latest kubectl command syntax
- New debugging features
- Ephemeral container options

## Debugging Checklist

**Tier 1 (30s):** `get pods` -> `describe pod` -> `logs`
**Tier 2 (2-5m):** `logs --previous` -> `get events` -> `top pods` -> `exec`
**Tier 3:** `kubectl debug` -> full YAML review -> network policies

## Common Errors

| Error | Solution |
|-------|----------|
| `Error from server (NotFound)` | Check name, namespace |
| `unable to upgrade connection` | Check API server connectivity |
| `Error from server (Forbidden)` | Request RBAC permissions |
| `container not found` | Use correct container name |

## Useful Debug Images

- `busybox` - Lightweight shell
- `nicolaka/netshoot` - Network tools (curl, dig, nmap)
- `curlimages/curl` - HTTP testing

> See `references/research.md` for detailed examples and advanced patterns.

## Related Skills

- `gke-deployment` - GKE-specific patterns
- `helm-charts` - Helm release debugging

## Resources

- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [kubectl debug](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/)
