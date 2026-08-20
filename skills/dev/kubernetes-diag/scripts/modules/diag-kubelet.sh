#!/usr/bin/env bash
# diag-kubelet.sh — always-run kubelet collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[kubelet] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "kubelet logs" "01-kubelet.log" "journalctl -u kubelet --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager"
run "kubelet grep" "01c-kubelet-grep.log" "journalctl -u kubelet --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager | grep -iE 'PLEG|SandboxChanged|RunPodSandbox|CreatePodSandbox|StopPodSandbox|No ready sandbox|Killing container|KillPod|cgroup|probe|BackOff|context deadline exceeded|rpc error|not healthy|NodeNotReady|failed to setup network|subnet.env'"
run "kubelet status" "02-kubelet-status.txt" "systemctl status kubelet -l --no-pager; echo '--- NRestarts ---'; systemctl show kubelet -p NRestarts -p ActiveEnterTimestamp -p ActiveState"

echo "[kubelet] done"
