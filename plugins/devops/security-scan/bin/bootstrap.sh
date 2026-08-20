#!/bin/sh
# bootstrap.sh — Download qodersec binary for the current platform.
#
# Pure shell, minimal logic. Version is read from QODERSEC_CLI_VERSION_* env vars
# (set by qodersec-launch.cmd, with CODESEC_CLI_VERSION_* fallback for compat).
# All JSON parsing and qodercli download is handled by `qodersec ensure-deps`
# after bootstrap completes.
#
# Download strategy: read latest/manifest.json to get version, then download
# from the versioned directory (e.g. /0.6.0/). The default Qoder distribution
# endpoints serve signed binaries so macOS/Windows hosts accept them.
# OSS package name stays codesec-cli-*.tar.gz (CI/CD compat); binary is renamed
# to qodersec after extraction.
set -e

# Resolve home: QODERSEC_HOME > CODESEC_HOME > ~/.qodersec
if [ -n "${QODERSEC_HOME:-}" ]; then
    _CHOME="$QODERSEC_HOME"
elif [ -n "${CODESEC_HOME:-}" ]; then
    _CHOME="$CODESEC_HOME"
else
    _CHOME="$HOME/.qodersec"
fi
BIN_DIR="${_CHOME}/bin"
BINARY_NAME="qodersec"
QODERSEC_BIN="${BIN_DIR}/${BINARY_NAME}"

# Download URL: QODERSEC_OSS_URL > CODESEC_OSS_URL > default Qoder signed endpoint.
BUCKET_URL="${QODERSEC_OSS_URL:-${CODESEC_OSS_URL:-https://static.qoder.com.cn/security/qodersec}}"

# Skip if already installed unless launcher detected a pinned-version change.
if [ -x "$QODERSEC_BIN" ] && [ "${QODERSEC_FORCE_UPDATE:-}" != "1" ]; then
    exit 0
fi

# Read version from env (set by qodersec-launch.cmd)
VERSION="${QODERSEC_CLI_VERSION_GLOBAL:-${CODESEC_CLI_VERSION_GLOBAL:-0.5.0}}"
if [ "${QODER_SITE}" = "CN" ] || [ "${QODER_SITE}" = "cn" ]; then
    VERSION="${QODERSEC_CLI_VERSION_CN:-${CODESEC_CLI_VERSION_CN:-${VERSION}}}"
else
    # Non-CN users default to the global Qoder signed endpoint (unless overridden).
    BUCKET_URL="${QODERSEC_OSS_URL:-${CODESEC_OSS_URL:-https://qoder-ide.oss-accelerate.aliyuncs.com/security/qodersec}}"
fi

# Detect platform
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "${OS}" in
    linux)  OS="linux" ;;
    darwin) OS="darwin" ;;
    *)      echo "[bootstrap] unsupported OS: ${OS}" >&2; exit 1 ;;
esac
case "${ARCH}" in
    x86_64|amd64)  ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *)             echo "[bootstrap] unsupported arch: ${ARCH}" >&2; exit 1 ;;
esac

# Resolve actual version: use pinned VERSION from env, or fall back to manifest
resolve_version() {
    # If pinned version is set via env, use it directly
    if [ -n "${VERSION}" ] && [ "${VERSION}" != "0.5.0" ]; then
        echo "${VERSION}"
        return
    fi
    # Otherwise read from manifest
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "${BUCKET_URL}/latest/manifest.json" 2>/dev/null | \
            grep '"latest"' | sed 's/.*"latest"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- "${BUCKET_URL}/latest/manifest.json" 2>/dev/null | \
            grep '"latest"' | sed 's/.*"latest"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
    else
        echo "${VERSION}"
    fi
}

RESOLVED_VERSION="$(resolve_version)"
[ -n "${RESOLVED_VERSION}" ] || { echo "[bootstrap] failed to resolve version" >&2; exit 1; }

# Construct download URL from versioned directory
# OSS package name stays codesec-cli-* for CI/CD compatibility
FILENAME="codesec-cli-${OS}-${ARCH}.tar.gz"
DOWNLOAD_URL="${BUCKET_URL}/${RESOLVED_VERSION}/${FILENAME}"

echo "[bootstrap] downloading qodersec ${RESOLVED_VERSION} (${OS}/${ARCH})..."
echo "[bootstrap] ${DOWNLOAD_URL}"

mkdir -p "${BIN_DIR}" 2>/dev/null

# Download
TMPFILE="$(mktemp "${TMPDIR:-/tmp}/qodersec-XXXXXX.tar.gz")"
trap 'rm -f "${TMPFILE}"' EXIT

if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${TMPFILE}" "${DOWNLOAD_URL}" || { echo "[bootstrap] download failed" >&2; exit 1; }
elif command -v wget >/dev/null 2>&1; then
    wget -qO "${TMPFILE}" "${DOWNLOAD_URL}" || { echo "[bootstrap] download failed" >&2; exit 1; }
else
    echo "[bootstrap] curl or wget required" >&2; exit 1
fi

# Extract — OSS package contains codesec-cli binary, rename to qodersec
tar xzf "${TMPFILE}" -C "${BIN_DIR}" 2>/dev/null || tar xzf "${TMPFILE}" --strip-components=1 -C "${BIN_DIR}" 2>/dev/null || { echo "[bootstrap] extraction failed" >&2; exit 1; }

# Rename: OSS package ships codesec-cli, we rename to qodersec on disk
if [ -f "${BIN_DIR}/codesec-cli" ]; then
    mv "${BIN_DIR}/codesec-cli" "${BIN_DIR}/qodersec"
fi
chmod +x "${QODERSEC_BIN}" 2>/dev/null

# Write version.json (format matches ensure-deps)
CHANNEL="global"
[ "${QODER_SITE}" = "CN" ] || [ "${QODER_SITE}" = "cn" ] && CHANNEL="cn"
UPDATED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo 'unknown')"
printf '{\n  "version": "%s",\n  "channel": "%s",\n  "updated_at": "%s"\n}\n' \
    "${RESOLVED_VERSION}" "${CHANNEL}" "${UPDATED_AT}" > "${BIN_DIR}/qodersec-version.json"

echo "[bootstrap] installed qodersec ${RESOLVED_VERSION}"
