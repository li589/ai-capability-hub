#!/usr/bin/env bash
# diag-containerd.sh — containerd runtime collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[containerd] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "containerd logs" "03-containerd.log" "journalctl -u containerd --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager"
run "containerd grep" "03b-containerd-grep.log" "journalctl -u containerd --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager | grep -iE 'StopContainer|StopPodSandbox|exit_status|signal terminated|shim disconnected|cgroup|error|timeout|deadline|oom|panic|failed'"
run "containerd status" "04-containerd-status.txt" "systemctl status containerd -l --no-pager; echo '--- NRestarts ---'; systemctl show containerd -p NRestarts -p ActiveEnterTimestamp -p ActiveState"
run "containerd config dump" "19c-containerd-config-dump.txt" "containerd config dump 2>/dev/null | grep -i -A20 -B5 SystemdCgroup"
run "crictl info" "19-crictl-info.txt" "crictl info"
run "crictl ps -a" "17-crictl-ps-a.txt" "crictl ps -a"
run "crictl pods" "17b-crictl-pods.txt" "crictl pods"
run "crictl stats" "18-crictl-stats.txt" "crictl stats -a"

echo "[containerd] done"
