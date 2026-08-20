#!/usr/bin/env bash
# diag-bundle.sh — Kubernetes node diagnostic bundle entry point
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULES_DIR="$SCRIPT_DIR/modules"
SINCE="${1:-8 hours ago}"
UNTIL="${2:-now}"
HOSTNAME_SHORT=$(hostname)
TS=$(date +%Y%m%d-%H%M%S)
OUTDIR="/tmp/node-diag-${HOSTNAME_SHORT}-${TS}"
TARBALL="/tmp/node-diag-${HOSTNAME_SHORT}-${TS}.tar.gz"

# INSPECT_ALL=1 forces running every collector (inspection mode, unknown cluster)
INSPECT_ALL="${INSPECT_ALL:-0}"

mkdir -p "$OUTDIR"
export OUTDIR

echo "=== K8s diagnostic bundle ==="
echo "Node: $HOSTNAME_SHORT"
echo "Window: $SINCE ~ $UNTIL"
echo "Output: $OUTDIR"
echo ""

run_module() {
    local module="$1"; local name="$2"
    if [ -f "$MODULES_DIR/$module" ]; then
        echo "=== Running: $name ==="
        bash "$MODULES_DIR/$module" "$OUTDIR" "$SINCE" "$UNTIL" || echo "  -> $name completed with warnings"
    else
        echo "  -> module $module not found, skipping $name"
    fi
}

# Always run
run_module "diag-core.sh" "core"
run_module "diag-kubelet.sh" "kubelet"

# Detect container runtime (still print to log; conditional unless INSPECT_ALL)
RUNTIME="unknown"
if command -v crictl &>/dev/null; then
    RUNTIME_INFO=$(crictl info 2>/dev/null || true)
    if echo "$RUNTIME_INFO" | grep -qi containerd; then
        RUNTIME="containerd"
    elif command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        RUNTIME="docker"
    fi
fi

if [ "$RUNTIME" = "containerd" ] || [ "$RUNTIME" = "unknown" ] || [ "$INSPECT_ALL" = "1" ]; then
    run_module "diag-containerd.sh" "containerd"
fi

if command -v docker &>/dev/null || [ "$INSPECT_ALL" = "1" ]; then
    run_module "diag-docker.sh" "docker"
fi

# Detect deployment type
DEPLOYMENT="unknown"
if [ -f /etc/kubernetes/manifests/kube-apiserver.yaml ] || [ -f /etc/kubernetes/kubelet.conf ]; then
    DEPLOYMENT="kubeadm"
elif command -v k3s &>/dev/null || systemctl is-active k3s &>/dev/null 2>&1; then
    DEPLOYMENT="k3s"
fi

if [ "$DEPLOYMENT" = "kubeadm" ] || [ "$DEPLOYMENT" = "unknown" ] || [ "$INSPECT_ALL" = "1" ]; then
    run_module "diag-kubeadm-controlplane.sh" "kubeadm-controlplane"
fi

if [ "$DEPLOYMENT" = "k3s" ] || [ "$DEPLOYMENT" = "unknown" ] || [ "$INSPECT_ALL" = "1" ]; then
    run_module "diag-k3s.sh" "k3s"
fi

# Always collect CNI/service/etcd (inspection requires full coverage)
run_module "diag-cni-service.sh" "cni-service"
run_module "diag-etcd.sh" "etcd"

if [ "$INSPECT_ALL" = "1" ]; then
    echo ""
    echo "=== Inspection mode: collecting dynamic cluster-wide inventory ==="
    if command -v kubectl &>/dev/null; then
        KUBECTL_OK=0
        if timeout 5 kubectl get --raw='/healthz' --request-timeout=3s >/dev/null 2>&1; then
            KUBECTL_OK=1
        fi
        if [ "$KUBECTL_OK" -eq 1 ]; then
            {
                echo "### command: kubectl get nodes -o wide"; echo "### $(date -Iseconds)"; echo "---"
                kubectl get nodes -o wide 2>&1
                echo ""; echo "### command: kubectl get pods -A"
                echo "---"
                kubectl get pods -A 2>&1
                echo ""; echo "### command: kubectl get events -A --sort-by=.lastTimestamp"
                echo "---"
                kubectl get events -A --sort-by=.lastTimestamp 2>&1 | tail -200
            } > "$OUTDIR/26-kubectl-cluster-inventory.txt" || true
        fi
    fi
fi

# Package
echo ""
echo "=== Collecting all files ==="
ls -R "$OUTDIR" | head -200

echo ""
echo "=== Packaging ==="
tar -czf "$TARBALL" -C "$(dirname "$OUTDIR")" "$(basename "$OUTDIR")"
echo ""
echo "Diagnostic bundle ready: $TARBALL"
ls -lh "$TARBALL"
echo ""
echo "Send this file for analysis."
