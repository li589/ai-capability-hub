#!/bin/sh
# Unix launcher for the qodersec binary. qodersec-launch.cmd delegates here on
# macOS/Linux so its Windows batch section never needs shell heredoc tricks.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export QODER_PLUGIN_ROOT="$PLUGIN_ROOT"
export CODESEC_LOG_NAME="qodersec"

# Pinned dependency versions (updated when plugin is published).
export QODERSEC_CLI_VERSION_GLOBAL="0.8.0"
export QODERSEC_CLI_VERSION_CN="0.8.0"
export CODESEC_CLI_VERSION_GLOBAL="0.8.0"
export CODESEC_CLI_VERSION_CN="0.8.0"
export QODERCLI_VERSION_GLOBAL="1.0.45"
export QODERCLI_VERSION_CN="1.0.45"

# Hooks may run with a minimal PATH; add the usual install directories.
export PATH="$HOME/.qodersec/bin:$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

# ONE root for config + credentials + logs + state.
if [ -n "${QODERSEC_HOME:-}" ]; then
    _CHOME="$QODERSEC_HOME"
elif [ -n "${CODESEC_HOME:-}" ]; then
    _CHOME="$CODESEC_HOME"
else
    _CHOME="$HOME/.qodersec"
fi
mkdir -p "$_CHOME" 2>/dev/null
mkdir -p "$_CHOME/logs" 2>/dev/null
_QODERSEC_LOG="$_CHOME/logs/qodersec.log"

export QODERSEC_HOME="$_CHOME"
export CODESEC_HOME="$_CHOME"

# Seed/refresh the persistent config when the plugin version changes.
PLUGIN_VERSION=""
if [ -f "$PLUGIN_ROOT/.qoder-plugin/plugin.json" ]; then
    PLUGIN_VERSION="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$PLUGIN_ROOT/.qoder-plugin/plugin.json" | head -1)"
fi
VERSION_MARKER="$_CHOME/.config-version"
NEED_CONFIG=0
if [ ! -f "$_CHOME/config.yaml" ]; then
    NEED_CONFIG=1
elif [ -n "$PLUGIN_VERSION" ] && [ -f "$VERSION_MARKER" ]; then
    INSTALLED_VERSION="$(cat "$VERSION_MARKER" 2>/dev/null)"
    if [ "$INSTALLED_VERSION" != "$PLUGIN_VERSION" ]; then
        NEED_CONFIG=1
    fi
elif [ -n "$PLUGIN_VERSION" ] && [ ! -f "$VERSION_MARKER" ]; then
    NEED_CONFIG=1
fi
if [ "$NEED_CONFIG" = "1" ]; then
    if [ -f "$PLUGIN_ROOT/config.yaml" ]; then
        cp "$PLUGIN_ROOT/config.yaml" "$_CHOME/config.yaml" 2>/dev/null
    elif [ -f "$PLUGIN_ROOT/config.yaml.example" ]; then
        cp "$PLUGIN_ROOT/config.yaml.example" "$_CHOME/config.yaml" 2>/dev/null
    fi
    [ -n "$PLUGIN_VERSION" ] && printf '%s' "$PLUGIN_VERSION" > "$VERSION_MARKER"
fi

# Prevent the SDK-spawned inner qodercli from recursively entering hooks.
if [ "${CODESEC_REVIEW_SUBPROCESS:-}" = "1" ]; then
    if [ "${CODESEC_DEBUG:-}" = "1" ]; then
        printf '[%s] [launcher] skip inner subprocess\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$_QODERSEC_LOG" 2>/dev/null
    fi
    cat >/dev/null 2>&1 || true
    exit 0
fi

if [ "${CODESEC_DEBUG:-}" = "1" ]; then
    printf '[%s] [launcher] exec cmd=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$_QODERSEC_LOG" 2>/dev/null
fi

CLI="$_CHOME/bin/qodersec"
TARGET_CLI_VERSION="$QODERSEC_CLI_VERSION_GLOBAL"
if [ "${QODER_SITE:-}" = "CN" ] || [ "${QODER_SITE:-}" = "cn" ]; then
    TARGET_CLI_VERSION="$QODERSEC_CLI_VERSION_CN"
fi
INSTALLED_CLI_VERSION=""
if [ -x "$CLI" ]; then
    INSTALLED_CLI_VERSION="$("$CLI" version 2>/dev/null | awk 'NR == 1 { print $2 }')"
fi

if [ "$INSTALLED_CLI_VERSION" != "$TARGET_CLI_VERSION" ]; then
    if [ -f "$SCRIPT_DIR/bootstrap.sh" ]; then
        printf '[%s] [launcher] qodersec update current=%s target=%s\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$INSTALLED_CLI_VERSION" "$TARGET_CLI_VERSION" >> "$_QODERSEC_LOG" 2>/dev/null
        QODERSEC_FORCE_UPDATE=1 sh "$SCRIPT_DIR/bootstrap.sh" >&2 || {
            printf '[%s] [launcher] bootstrap failed target=%s\n' \
                "$(date '+%Y-%m-%d %H:%M:%S')" "$TARGET_CLI_VERSION" >> "$_QODERSEC_LOG" 2>/dev/null
            echo "qodersec-launch: bootstrap failed" >&2
            exit 127
        }
        INSTALLED_CLI_VERSION="$("$CLI" version 2>/dev/null | awk 'NR == 1 { print $2 }')"
        if [ "$INSTALLED_CLI_VERSION" != "$TARGET_CLI_VERSION" ]; then
            printf '[%s] [launcher] bootstrap verification failed current=%s target=%s\n' \
                "$(date '+%Y-%m-%d %H:%M:%S')" "$INSTALLED_CLI_VERSION" "$TARGET_CLI_VERSION" >> "$_QODERSEC_LOG" 2>/dev/null
            echo "qodersec-launch: expected qodersec $TARGET_CLI_VERSION, got $INSTALLED_CLI_VERSION" >&2
            exit 127
        fi
        printf '[%s] [launcher] bootstrap done version=%s\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$INSTALLED_CLI_VERSION" >> "$_QODERSEC_LOG" 2>/dev/null
    fi
    if [ ! -x "$CLI" ]; then
        printf '[%s] [launcher] fatal: qodersec not found after bootstrap\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$_QODERSEC_LOG" 2>/dev/null
        echo "qodersec-launch: qodersec not found in $_CHOME/bin after bootstrap" >&2
        exit 127
    fi
fi

exec "$CLI" "$@"
