# Kubernetes Debugging Research

> Comprehensive reference for Kubernetes troubleshooting patterns and kubectl diagnostic commands

---

## Core Diagnostic Commands

### Pod Status and Details

```bash
# List all pods with status
kubectl get pods -o wide
kubectl get pods --all-namespaces

# Detailed pod information with events
kubectl describe pod <pod-name>
kubectl describe pod <pod-name> -n <namespace>

# Get pod YAML for full configuration review
kubectl get pod <pod-name> -o yaml

# Watch pods in real-time
kubectl get pods -w
```

### Container Logs

```bash
# Current container logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>

# Previous container crash logs
kubectl logs <pod-name> --previous
kubectl logs <pod-name> -c <container-name> --previous

# Follow logs in real-time
kubectl logs -f <pod-name>

# Tail last N lines
kubectl logs --tail=100 <pod-name>

# Logs since timestamp
kubectl logs --since=1h <pod-name>
kubectl logs --since-time="2024-01-01T00:00:00Z" <pod-name>

# All containers in pod
kubectl logs <pod-name> --all-containers=true
```

### Events

```bash
# Cluster events (recent first)
kubectl get events --sort-by='.lastTimestamp'

# Events for specific namespace
kubectl get events -n <namespace>

# Events for specific pod
kubectl get events --field-selector involvedObject.name=<pod-name>

# Watch events in real-time
kubectl get events -w
```

### Resource Usage

```bash
# Pod resource consumption (requires metrics-server)
kubectl top pods
kubectl top pods -n <namespace>
kubectl top pods --containers

# Node resource consumption
kubectl top nodes

# Sort by memory/cpu
kubectl top pods --sort-by=memory
kubectl top pods --sort-by=cpu
```

---

## Pod Status Interpretation

### Pod Phases

| Phase | Description | Action |
|-------|-------------|--------|
| `Pending` | Pod accepted but not scheduled/running | Check events, node resources, taints |
| `Running` | Pod bound to node, all containers created | Check container states |
| `Succeeded` | All containers terminated successfully | Normal for Jobs |
| `Failed` | All containers terminated, at least one failed | Check logs, exit codes |
| `Unknown` | Pod state cannot be determined | Check node health |

### Container States

| State | Description |
|-------|-------------|
| `Waiting` | Container not running, preparing to start |
| `Running` | Container executing normally |
| `Terminated` | Container finished execution |

### Common Status Conditions

| Status | Root Cause | Diagnostic Steps |
|--------|------------|------------------|
| `CrashLoopBackOff` | Container repeatedly crashes | `kubectl logs --previous`, check exit codes |
| `ImagePullBackOff` | Cannot pull container image | Check image name, registry auth, network |
| `ErrImagePull` | Image pull failed | Verify image exists, check imagePullSecrets |
| `CreateContainerConfigError` | ConfigMap/Secret missing | Verify referenced configs exist |
| `Pending` (long) | Scheduling issues | Check node resources, taints, affinity |
| `Terminating` (stuck) | Finalizers blocking deletion | Check finalizers, force delete if needed |
| `OOMKilled` | Container exceeded memory limit | Increase limits or optimize app |
| `Evicted` | Node pressure (disk, memory) | Check node conditions, reclaim resources |

---

## kubectl exec - Interactive Debugging

```bash
# Get shell in running container
kubectl exec -it <pod-name> -- /bin/sh
kubectl exec -it <pod-name> -- /bin/bash

# Specific container
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh

# Run specific command
kubectl exec <pod-name> -- cat /etc/config
kubectl exec <pod-name> -- env
kubectl exec <pod-name> -- ls -la /app

# Check networking from inside pod
kubectl exec <pod-name> -- nslookup kubernetes
kubectl exec <pod-name> -- wget -qO- http://service-name:port
kubectl exec <pod-name> -- curl -v http://service-name:port
```

---

## kubectl debug - Ephemeral Containers

Ephemeral containers are useful when:
- Container image lacks debugging tools
- Container crashed and cannot exec into it
- Need to debug distroless images

```bash
# Add debug container to running pod
kubectl debug -it <pod-name> --image=busybox --target=<container-name>
kubectl debug -it <pod-name> --image=nicolaka/netshoot --target=<container-name>

# Create pod copy with debug container
kubectl debug <pod-name> -it --image=busybox --copy-to=<debug-pod-name>

# Copy pod with different command
kubectl debug <pod-name> -it --copy-to=<debug-pod-name> --container=<container> -- sh

# Copy pod with changed image
kubectl debug <pod-name> --copy-to=<debug-pod-name> --set-image=*=busybox

# Debug node (creates pod with host access)
kubectl debug node/<node-name> -it --image=busybox

# Debug profiles
kubectl debug <pod-name> -it --image=busybox --profile=general
kubectl debug <pod-name> -it --image=busybox --profile=netadmin
kubectl debug <pod-name> -it --image=busybox --profile=sysadmin
```

### Debug Profiles

| Profile | Use Case |
|---------|----------|
| `legacy` | Backwards compatibility |
| `general` | Generic debugging |
| `baseline` | PodSecurityStandard baseline |
| `restricted` | PodSecurityStandard restricted |
| `netadmin` | Network debugging (NET_ADMIN) |
| `sysadmin` | Full privileges (root) |

---

## Deployment and ReplicaSet Debugging

```bash
# Deployment status
kubectl get deployment <name>
kubectl describe deployment <name>

# Check rollout status
kubectl rollout status deployment/<name>

# Rollout history
kubectl rollout history deployment/<name>

# ReplicaSet details
kubectl get replicasets
kubectl describe rs <replicaset-name>
```

---

## Service and Network Debugging

### Service Diagnostics

```bash
# List services
kubectl get svc
kubectl get svc -o wide

# Service details
kubectl describe svc <service-name>

# Check endpoints (pods backing the service)
kubectl get endpoints <service-name>
kubectl get endpointslices -l kubernetes.io/service-name=<service-name>
```

### Network Troubleshooting

```bash
# DNS resolution test
kubectl run dnstest --image=busybox:1.28 --rm -it --restart=Never -- nslookup kubernetes

# Connectivity test
kubectl run nettest --image=nicolaka/netshoot --rm -it --restart=Never -- curl -v http://<service>:<port>

# Check network policies
kubectl get networkpolicies
kubectl describe networkpolicy <name>
```

### Service Debugging Checklist

1. Verify service exists: `kubectl get svc <name>`
2. Check endpoints: `kubectl get endpoints <name>`
3. Verify pod labels match selector: `kubectl get pods --selector=<labels>`
4. Test DNS: `kubectl exec <pod> -- nslookup <service>`
5. Test connectivity: `kubectl exec <pod> -- curl <service>:<port>`

---

## Node Debugging

```bash
# Node status
kubectl get nodes
kubectl get nodes -o wide

# Node details
kubectl describe node <node-name>

# Node conditions
kubectl get nodes -o jsonpath='{.items[*].status.conditions}'

# Debug node (creates privileged pod)
kubectl debug node/<node-name> -it --image=busybox
# Host filesystem at /host
```

### Node Conditions

| Condition | Healthy | Meaning |
|-----------|---------|---------|
| `Ready` | True | Node healthy and accepting pods |
| `MemoryPressure` | False | Node has sufficient memory |
| `DiskPressure` | False | Node has sufficient disk space |
| `PIDPressure` | False | Node has sufficient PIDs |
| `NetworkUnavailable` | False | Node network configured correctly |

---

## Common Failure Patterns

### 1. CrashLoopBackOff

**Symptoms:** Pod restarts repeatedly, increasing backoff delay

**Diagnosis:**
```bash
kubectl describe pod <pod-name>  # Check events, exit codes
kubectl logs <pod-name> --previous  # Check crash logs
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].state}'
```

**Common Causes:**
- Application error/panic
- Missing configuration (env vars, config files)
- Dependency unavailable (database, service)
- Resource constraints (OOM)
- Liveness probe misconfiguration

### 2. ImagePullBackOff

**Symptoms:** Container stuck in `Waiting` state

**Diagnosis:**
```bash
kubectl describe pod <pod-name>  # Check events for error details
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[0].image}'
```

**Common Causes:**
- Image name typo
- Image doesn't exist in registry
- Private registry without imagePullSecret
- Registry authentication failure
- Network connectivity issues

### 3. Pending Pod

**Symptoms:** Pod stuck in `Pending` state

**Diagnosis:**
```bash
kubectl describe pod <pod-name>  # Check events for scheduler messages
kubectl get events --field-selector reason=FailedScheduling
kubectl describe nodes  # Check allocatable resources
```

**Common Causes:**
- Insufficient CPU/memory on nodes
- Node taints without tolerations
- Node selector/affinity mismatch
- PersistentVolumeClaim pending
- ResourceQuota exceeded

### 4. Pod Eviction

**Symptoms:** Pod terminated with reason `Evicted`

**Diagnosis:**
```bash
kubectl describe pod <pod-name>  # Check eviction reason
kubectl describe node <node-name>  # Check node conditions
```

**Common Causes:**
- Node memory pressure
- Node disk pressure
- Pod exceeded ephemeral storage limit

### 5. OOMKilled

**Symptoms:** Container terminated with `OOMKilled` reason

**Diagnosis:**
```bash
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].lastState}'
```

**Solutions:**
- Increase memory limits
- Fix memory leaks in application
- Add memory requests to ensure QoS

---

## Debugging Checklist

### Tier 1: Quick Assessment

- [ ] `kubectl get pods -o wide` - Pod status and node placement
- [ ] `kubectl describe pod <name>` - Events and state details
- [ ] `kubectl logs <name>` - Application logs
- [ ] `kubectl get events --sort-by='.lastTimestamp'` - Recent events

### Tier 2: Deep Dive

- [ ] `kubectl logs <name> --previous` - Previous crash logs
- [ ] `kubectl get pod <name> -o yaml` - Full pod specification
- [ ] `kubectl top pods` - Resource consumption
- [ ] `kubectl exec -it <name> -- sh` - Interactive shell

### Tier 3: Advanced

- [ ] `kubectl debug <name> -it --image=busybox` - Ephemeral container
- [ ] `kubectl debug node/<name> -it --image=busybox` - Node debugging
- [ ] Port-forward for local testing
- [ ] Network policy review

---

## Log Aggregation Patterns

### Multi-Container Logs

```bash
# All containers in pod
kubectl logs <pod-name> --all-containers=true

# Specific container
kubectl logs <pod-name> -c <container-name>

# Follow logs from all containers
kubectl logs <pod-name> --all-containers=true -f
```

### Label-Based Log Collection

```bash
# Logs from all pods with label
kubectl logs -l app=myapp
kubectl logs -l app=myapp --all-containers=true

# Combine with tail
kubectl logs -l app=myapp --tail=50
```

---

## Port Forwarding for Local Testing

```bash
# Forward pod port
kubectl port-forward pod/<pod-name> 8080:80

# Forward service port
kubectl port-forward svc/<service-name> 8080:80

# Background and specific address
kubectl port-forward --address 0.0.0.0 pod/<pod-name> 8080:80 &
```

---

## Useful Debug Images

| Image | Use Case |
|-------|----------|
| `busybox` | Basic shell, lightweight |
| `nicolaka/netshoot` | Network debugging (curl, dig, nmap, etc.) |
| `curlimages/curl` | HTTP testing |
| `alpine` | Lightweight Linux with apk |
| `ubuntu` | Full Linux environment |

---

## Context7 Integration

For up-to-date kubectl command documentation and options, query Context7:

```
Use Context7 MCP server to:
- Look up current kubectl command syntax
- Find new debugging features
- Verify command options and flags
- Get examples for specific scenarios
```

---

## Resources

- [Kubernetes Debug Documentation](https://kubernetes.io/docs/tasks/debug/)
- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [kubectl debug Reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/)
