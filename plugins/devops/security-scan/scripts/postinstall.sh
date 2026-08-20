#!/bin/sh
# postinstall.sh — Make launcher scripts executable after npm install.
# Runs automatically via npm's postinstall lifecycle hook.
# Safe to run on Windows (no-op if chmod unavailable).
set -e

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Make shell scripts executable
if command -v chmod >/dev/null 2>&1; then
    for f in "${PLUGIN_ROOT}"/bin/*.sh; do
        [ -f "$f" ] && chmod +x "$f"
    done
fi

# On Unix, make .cmd launcher executable too (it's a polyglot that delegates to .sh)
if [ "$(uname -s)" != "Windows_NT" ]; then
    [ -f "${PLUGIN_ROOT}/bin/qodersec-launch.cmd" ] && \
        chmod +x "${PLUGIN_ROOT}/bin/qodersec-launch.cmd" 2>/dev/null || true
fi
