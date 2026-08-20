#!/usr/bin/env bash
# diag-systemd-service.sh — systemd service deep-dive (fuzzy match)
set -uo pipefail

usage() {
    echo "usage: $0 <pattern> [outdir] [since] [until]"
    echo "  pattern: fuzzy service name match (e.g. 'kubelet', 'containerd', 'haproxy')"
    echo ""
    echo "output: <outdir>/systemd-services/<name>/"
    exit 1
}

PATTERN="${1:-}"
OUTDIR="${2:-/tmp/kubernetes-diag}"
SINCE="${3:-8 hours ago}"
UNTIL="${4:-now}"

[ -z "$PATTERN" ] && usage

TS=$(date +%Y%m%d-%H%M%S)
SERVICEDIR="$OUTDIR/systemd-services"
mkdir -p "$SERVICEDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[systemd] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } || true
}

echo "[systemd] finding services matching '${PATTERN}'"

# List all systemd services matching pattern
MATCHED_UNITS=$(systemctl list-units --type=service --all --no-pager 2>/dev/null | grep -i "$PATTERN" | awk '{print $1}' || true)

if [ -z "$MATCHED_UNITS" ]; then
    echo "[systemd] no services matching '${PATTERN}'"
    exit 0
fi

echo "[systemd] matched units:"
echo "$MATCHED_UNITS"

collect_one() {
    local unit="$1"
    local unit_dir="$SERVICEDIR/$(echo "$unit" | tr '/' '_')"
    mkdir -p "$unit_dir"

    echo "[systemd] collecting: $unit"

    run "$unit status" "$unit_dir/status.txt" "systemctl status '$unit' -l --no-pager"
    run "$unit show" "$unit_dir/show.txt" "systemctl show '$unit'"
    run "$unit journal" "$unit_dir/journal.log" "journalctl -u '$unit' --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager"
    run "$unit journal grep" "$unit_dir/journal-grep.log" "journalctl -u '$unit' --since '${SINCE}' --until '${UNTIL}' -o short-iso --no-pager | grep -iE 'error|fail|timeout|killed|restart|stop'"

    # Try to get the binary path and version
    local exec_path
    exec_path=$(systemctl show "$unit" -p ExecStart 2>/dev/null | sed 's/^ExecStart={ path=//;s/;.*//;s/ .*//' 2>/dev/null || true)
    if [ -n "$exec_path" ] && [ -x "$exec_path" ]; then
        run "$unit binary version" "$unit_dir/version.txt" "$exec_path --version 2>&1 || true"
    fi
}

while IFS= read -r unit; do
    [ -n "$unit" ] && collect_one "$unit"
done <<< "$MATCHED_UNITS"

echo "[systemd] done"
