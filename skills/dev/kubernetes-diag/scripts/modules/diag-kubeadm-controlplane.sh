#!/usr/bin/env bash
# diag-kubeadm-controlplane.sh — kubeadm/static-pod control-plane collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[kubeadm-cp] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "static pod manifests" "27-static-pod-manifests.txt" "ls -la /etc/kubernetes/manifests 2>/dev/null; for f in /etc/kubernetes/manifests/*.yaml /etc/kubernetes/manifests/*.yml 2>/dev/null; do echo \"--- \$f ---\"; cat \"\$f\" 2>/dev/null; done"
run "kubelet config" "27b-kubelet-config.txt" "cat /var/lib/kubelet/config.yaml 2>/dev/null || true"
run "cert dates" "27c-cert-dates.txt" "for f in /etc/kubernetes/pki/*.crt /etc/kubernetes/pki/etcd/*.crt 2>/dev/null; do echo \"--- \$f ---\"; openssl x509 -in \"\$f\" -noout -dates 2>/dev/null || true; done"
run "kubeadm-config" "27d-kubeadm-config.txt" "kubectl -n kube-system get cm kubeadm-config -o yaml 2>/dev/null || true; cat /etc/kubernetes/kubeadm-config.yaml 2>/dev/null || true"
run "control-plane ports" "27e-control-plane-ports.txt" "ss -tlnp | grep -E '2379|2380|2381|6443|6444|10250|10257|10259' || true"

echo "[kubeadm-cp] done"
