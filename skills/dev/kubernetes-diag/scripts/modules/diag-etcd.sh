#!/usr/bin/env bash
# diag-etcd.sh — etcd collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[etcd] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "etcd container log" "20-etcd-container.log" \
    "ECID=\$(crictl ps -a --name etcd -q 2>/dev/null | head -n1); if [ -n \"\${ECID:-}\" ]; then crictl logs \"\$ECID\"; fi"

run "etcd data dir size" "etcd-data-size.txt" \
    "du -sh /var/lib/etcd 2>/dev/null; ls -la /var/lib/etcd/member 2>/dev/null || true"

run "etcd ports" "etcd-ports.txt" \
    "ss -tlnp | grep -E '2379|2380|2381' || true"

run "etcdctl member list" "etcd-member-list.txt" \
    "ECID=\$(crictl ps -a --name etcd -q 2>/dev/null | head -n1); if [ -n \"\${ECID:-}\" ]; then crictl exec \"\$ECID\" etcdctl --endpoints=https://127.0.0.1:2379 --cert=/etc/kubernetes/pki/etcd/peer.crt --key=/etc/kubernetes/pki/etcd/peer.key --cacert=/etc/kubernetes/pki/etcd/ca.crt member list -w table 2>/dev/null; crictl exec \"\$ECID\" etcdctl --endpoints=https://127.0.0.1:2379 --cert=/etc/kubernetes/pki/etcd/peer.crt --key=/etc/kubernetes/pki/etcd/peer.key --cacert=/etc/kubernetes/pki/etcd/ca.crt endpoint health 2>/dev/null; crictl exec \"\$ECID\" etcdctl --endpoints=https://127.0.0.1:2379 --cert=/etc/kubernetes/pki/etcd/peer.crt --key=/etc/kubernetes/pki/etcd/peer.key --cacert=/etc/kubernetes/pki/etcd/ca.crt endpoint status 2>/dev/null; fi"

echo "[etcd] done"
