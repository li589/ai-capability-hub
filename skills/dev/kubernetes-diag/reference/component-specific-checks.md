# Component-Specific Checks

This file describes when and how to trigger deep-dive checks for components that are NOT universal across all Kubernetes deployments. These checks are NOT in the baseline collector set.

## Trigger rules

Component-specific checks are triggered when:

1. The user explicitly mentions the component name in Phase 0.2 or Phase 0.3.
2. Collected evidence shows the component is running and may be involved.
3. The analysis phase narrows the root cause to this component's domain.

Do NOT trigger these checks just because the component might exist. The default collector set already covers universal Kubernetes components.

## How to trigger

When a component meets trigger conditions, use the generic resource scripts:

```bash
bash diag-k8s-resource.sh <type> <namespace?> <pattern>
bash diag-systemd-service.sh <pattern>
```

These scripts accept fuzzy patterns and do NOT require exact names or namespaces.

## Example triggers

### User says "haproxy pod problems"

```bash
bash diag-k8s-resource.sh pod "" haproxy
bash diag-systemd-service.sh haproxy
```

The empty `""` for namespace means "search all namespaces".

### User says "kapp-web frontend errors"

```bash
bash diag-k8s-resource.sh deployment "" kapp-web
```

### User says "metallb speaker not working"

```bash
bash diag-k8s-resource.sh daemonset metallb-system speaker
bash diag-k8s-resource.sh pod metallb-system speaker
```

### User says "CoreDNS not resolving"

```bash
bash diag-k8s-resource.sh deployment kube-system coredns
bash diag-k8s-resource.sh service kube-system kube-dns
```

## Project-specific note

For kapp/kURL-style deployments with local haproxy:

This installer design uses a local haproxy Pod or systemd service on `127.0.0.1:6444` as the apiserver entrypoint.

Trigger the haproxy check only when:

- User mentions haproxy, 6444, or the kapp installer.
- Collected evidence shows haproxy processes, Pods, or 6444 listener.
- kube-proxy logs show `localhost:6444 connect refused`.

When triggered:

```bash
bash diag-k8s-resource.sh pod "" haproxy
bash diag-systemd-service.sh haproxy
```

The analyzer should verify `ss -tlnp | grep 6444` and `curl -k https://127.0.0.1:6444/readyz`.

Do NOT present haproxy 6444 as a universal Kubernetes requirement. Always mark it as kapp-installer-specific in reports.
