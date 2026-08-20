#!/usr/bin/env bash
# diag-k3s.sh — k3s collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[k3s] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "k3s version" "28-k3s-version.txt" "k3s --version 2>/dev/null; k3s check-config 2>/dev/null || true"
run "k3s service status" "28b-k3s-status.txt" "systemctl status k3s -l --no-pager 2>/dev/null || true"
run "k3s-agent status" "28c-k3s-agent-status.txt" "systemctl status k3s-agent -l --no-pager 2>/dev/null || true"
run "k3s journal" "28d-k3s-journal.log" "journalctl -u k3s --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager 2>/dev/null || true"
run "k3s-agent journal" "28e-k3s-agent-journal.log" "journalctl -u k3s-agent --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager 2>/dev/null || true"
run "k3s config" "28f-k3s-config.txt" "cat /etc/rancher/k3s/config.yaml 2>/dev/null; cat /etc/rancher/k3s/registries.yaml 2>/dev/null || true"
run "k3s containerd config" "28g-k3s-containerd-config.txt" "cat /var/lib/rancher/k3s/agent/etc/containerd/config.toml 2>/dev/null || true"

echo "[k3s] done"
