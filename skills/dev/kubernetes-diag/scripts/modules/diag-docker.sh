#!/usr/bin/env bash
# diag-docker.sh — docker/cri-docker runtime collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[docker] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "docker version" "26-docker-version.txt" "docker version 2>/dev/null || true"
run "docker info" "26b-docker-info.txt" "docker info 2>/dev/null || true"
run "docker ps -a" "26c-docker-ps.txt" "docker ps -a 2>/dev/null || true"
run "docker daemon config" "26d-docker-daemon-json.txt" "cat /etc/docker/daemon.json 2>/dev/null || true"
run "docker service status" "26e-docker-status.txt" "systemctl status docker -l --no-pager 2>/dev/null || true"
run "cri-docker status" "26f-cri-docker-status.txt" "systemctl status cri-docker -l --no-pager 2>/dev/null || true"
run "docker journal" "26g-docker-journal.log" "journalctl -u docker --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager 2>/dev/null || true"
run "cri-docker journal" "26h-cri-docker-journal.log" "journalctl -u cri-docker --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager 2>/dev/null || true"

echo "[docker] done"
