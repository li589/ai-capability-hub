#!/usr/bin/env bash
# diag-cni-service.sh — CNI, flannel, kube-proxy, Service network collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[cni-svc] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "cni config" "24c-cni-flannel-state.txt" \
    "echo '--- /etc/cni/net.d ---'; ls -la /etc/cni/net.d 2>/dev/null; for f in /etc/cni/net.d/* 2>/dev/null; do echo \"--- \$f ---\"; cat \"\$f\" 2>/dev/null; done; echo '--- /run/flannel ---'; ls -la /run/flannel 2>/dev/null; cat /run/flannel/subnet.env 2>/dev/null || true; echo '--- cni0/flannel.1 ---'; ip addr show cni0 2>/dev/null || true; ip addr show flannel.1 2>/dev/null || true"

run "service proxy state" "24d-service-proxy-state.txt" \
    "echo '--- ports ---'; ss -tlnp | grep -E '2379|2380|2381|6443|6444' || true; echo '--- ipvs modules ---'; lsmod | grep -E '^ip_vs|^nf_conntrack|^br_netfilter' || true; echo '--- kube-ipvs0 ---'; ip addr show kube-ipvs0 2>/dev/null || true; echo '--- /proc/net/ip_vs ---'; cat /proc/net/ip_vs 2>/dev/null | head -120 || true; echo '--- iptables KUBE nat ---'; iptables-save -t nat 2>/dev/null | grep -E 'KUBE|10\\.96\\.' | head -200 || true"

run "kube-proxy container log" "20-kube-proxy-container.log" \
    "KCID=\$(crictl ps -a --name kube-proxy -q 2>/dev/null | head -n1); if [ -n \"\${KCID:-}\" ]; then crictl logs \"\$KCID\"; fi"

run "flannel container log" "20-flannel-container.log" \
    "FCID=\$(crictl ps -a --name kube-flannel -q 2>/dev/null | head -n1); if [ -n \"\${FCID:-}\" ]; then crictl logs \"\$FCID\"; fi"

echo "[cni-svc] done"
