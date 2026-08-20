#!/bin/sh
# Official WorkBuddy launcher for yc-cloud CLI.
# Fetches manifest from CDN, downloads SHA256-verified loader, then execs it.
# Agents must call this script only; do not replicate download/exec logic manually.
set -eu

MANIFEST_URL="https://staticcdn.jinbizhihui.com/js/v1.0.0_pay-202607290702/yc-cloud-binaries-prod.env"
CDN_BASE="${MANIFEST_URL%/*}"
YC_HOME="$HOME/.yc-cloud"
MANIFEST_CACHE="$YC_HOME/manifest.env"
mkdir -p "$YC_HOME"

if [ "${1:-}" = "clear-env" ]; then
  rm -f "$YC_HOME/config.json" "$YC_HOME/settings.json" "$YC_HOME/device-id"
  rm -rf "$YC_HOME/core" "$YC_HOME/loader"
  rm -f "$MANIFEST_CACHE" "$YC_HOME/manifest-source.txt"
  printf '已清空 ~/.yc-cloud 全部缓存（config、loader、core、manifest）\n'
  exit 0
fi

# --- Version upgrade detection ---
MANIFEST_SOURCE_FILE="$YC_HOME/manifest-source.txt"
PREV_MANIFEST_URL=""
if [ -f "$MANIFEST_SOURCE_FILE" ]; then
  PREV_MANIFEST_URL=$(cat "$MANIFEST_SOURCE_FILE")
fi
if [ -n "$PREV_MANIFEST_URL" ] && [ "$PREV_MANIFEST_URL" != "$MANIFEST_URL" ]; then
  printf 'Upgrade detected: clearing loader/core cache\n' >&2
  rm -rf "$YC_HOME/core" "$YC_HOME/loader"
  rm -f "$MANIFEST_CACHE"
fi
printf '%s' "$MANIFEST_URL" > "$MANIFEST_SOURCE_FILE"

# --- Platform detection ---
OS="$(uname -s)"
case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    case "$MANIFEST_URL" in
      *binaries-test.env) PS1_NAME="yc-cloud-test.ps1" ;;
      *) PS1_NAME="yc-cloud.ps1" ;;
    esac
    PS1_URL="$CDN_BASE/$PS1_NAME"
    PS1_CACHE="$YC_HOME/$PS1_NAME"
    if ! curl -fsSL --retry 3 -o "$PS1_CACHE" "$PS1_URL" 2>/dev/null; then
      printf 'ERROR: failed to download Windows launcher: %s\n' "$PS1_URL" >&2
      exit 1
    fi
    WIN_PATH="$PS1_CACHE"
    if command -v cygpath >/dev/null 2>&1; then
      WIN_PATH="$(cygpath -w "$PS1_CACHE")"
    fi
    exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WIN_PATH" "$@"
    ;;
  Darwin)
    ;;
  Linux)
    ;;
  *)
    printf 'ERROR: unsupported OS: %s (only macOS, Linux and Windows are supported)\n' "$OS" >&2
    exit 1
    ;;
esac

# --- macOS flow ---
if ! curl -fsSL --retry 3 -o "$MANIFEST_CACHE.tmp" "$MANIFEST_URL" 2>/dev/null; then
  printf 'WARN: manifest fetch failed, using cache\n' >&2
  if [ ! -f "$MANIFEST_CACHE" ]; then
    printf 'ERROR: no manifest available: %s\n' "$MANIFEST_URL" >&2
    exit 1
  fi
else
  mv "$MANIFEST_CACHE.tmp" "$MANIFEST_CACHE"
fi

get_manifest_value() {
  key="$1"
  case "$key" in
    DARWIN_ARM64_LOADER_URL|DARWIN_ARM64_LOADER_SHA256|DARWIN_ARM64_CORE_URL|DARWIN_ARM64_CORE_PKG_SHA256|DARWIN_ARM64_CORE_BIN_SHA256|DARWIN_ARM64_CORE_RELEASE_ID|DARWIN_ARM64_CORE_VERSION|DARWIN_ARM64_CORE_PLATFORM|DARWIN_X64_LOADER_URL|DARWIN_X64_LOADER_SHA256|DARWIN_X64_CORE_URL|DARWIN_X64_CORE_PKG_SHA256|DARWIN_X64_CORE_BIN_SHA256|DARWIN_X64_CORE_RELEASE_ID|DARWIN_X64_CORE_VERSION|DARWIN_X64_CORE_PLATFORM|LINUX_X64_LOADER_URL|LINUX_X64_LOADER_SHA256|LINUX_X64_CORE_URL|LINUX_X64_CORE_PKG_SHA256|LINUX_X64_CORE_BIN_SHA256|LINUX_X64_CORE_RELEASE_ID|LINUX_X64_CORE_VERSION|LINUX_X64_CORE_PLATFORM|LINUX_ARM64_LOADER_URL|LINUX_ARM64_LOADER_SHA256|LINUX_ARM64_CORE_URL|LINUX_ARM64_CORE_PKG_SHA256|LINUX_ARM64_CORE_BIN_SHA256|LINUX_ARM64_CORE_RELEASE_ID|LINUX_ARM64_CORE_VERSION|LINUX_ARM64_CORE_PLATFORM)
      ;;
    *)
      printf 'ERROR: unsupported manifest key: %s\n' "$key" >&2
      exit 1
      ;;
  esac
  value=$(awk -F= -v wanted="$key" '$1 == wanted { sub(/^[^=]*=/, ""); print; exit }' "$MANIFEST_CACHE")
  printf '%s' "$value"
}

verify_sha256() {
  file="$1"
  expected="$2"
  actual=$(shasum -a 256 "$file" | awk '{print $1}')
  [ "$actual" = "$expected" ]
}

arch="$(uname -m)"
case "$OS:$arch" in
  Darwin:arm64|Darwin:aarch64)
    LOADER_URL=$(get_manifest_value DARWIN_ARM64_LOADER_URL)
    LOADER_SHA=$(get_manifest_value DARWIN_ARM64_LOADER_SHA256)
    YC_CLOUD_CORE_URL=$(get_manifest_value DARWIN_ARM64_CORE_URL)
    YC_CLOUD_CORE_PKG_SHA256=$(get_manifest_value DARWIN_ARM64_CORE_PKG_SHA256)
    YC_CLOUD_CORE_BIN_SHA256=$(get_manifest_value DARWIN_ARM64_CORE_BIN_SHA256)
    YC_CLOUD_CORE_RELEASE_ID=$(get_manifest_value DARWIN_ARM64_CORE_RELEASE_ID)
    YC_CLOUD_CORE_VERSION=$(get_manifest_value DARWIN_ARM64_CORE_VERSION)
    YC_CLOUD_CORE_PLATFORM=$(get_manifest_value DARWIN_ARM64_CORE_PLATFORM)
    ;;
  Darwin:x86_64|Darwin:amd64)
    LOADER_URL=$(get_manifest_value DARWIN_X64_LOADER_URL)
    LOADER_SHA=$(get_manifest_value DARWIN_X64_LOADER_SHA256)
    YC_CLOUD_CORE_URL=$(get_manifest_value DARWIN_X64_CORE_URL)
    YC_CLOUD_CORE_PKG_SHA256=$(get_manifest_value DARWIN_X64_CORE_PKG_SHA256)
    YC_CLOUD_CORE_BIN_SHA256=$(get_manifest_value DARWIN_X64_CORE_BIN_SHA256)
    YC_CLOUD_CORE_RELEASE_ID=$(get_manifest_value DARWIN_X64_CORE_RELEASE_ID)
    YC_CLOUD_CORE_VERSION=$(get_manifest_value DARWIN_X64_CORE_VERSION)
    YC_CLOUD_CORE_PLATFORM=$(get_manifest_value DARWIN_X64_CORE_PLATFORM)
    ;;
  Linux:x86_64|Linux:amd64)
    LOADER_URL=$(get_manifest_value LINUX_X64_LOADER_URL)
    LOADER_SHA=$(get_manifest_value LINUX_X64_LOADER_SHA256)
    YC_CLOUD_CORE_URL=$(get_manifest_value LINUX_X64_CORE_URL)
    YC_CLOUD_CORE_PKG_SHA256=$(get_manifest_value LINUX_X64_CORE_PKG_SHA256)
    YC_CLOUD_CORE_BIN_SHA256=$(get_manifest_value LINUX_X64_CORE_BIN_SHA256)
    YC_CLOUD_CORE_RELEASE_ID=$(get_manifest_value LINUX_X64_CORE_RELEASE_ID)
    YC_CLOUD_CORE_VERSION=$(get_manifest_value LINUX_X64_CORE_VERSION)
    YC_CLOUD_CORE_PLATFORM=$(get_manifest_value LINUX_X64_CORE_PLATFORM)
    ;;
  Linux:aarch64|Linux:arm64)
    LOADER_URL=$(get_manifest_value LINUX_ARM64_LOADER_URL)
    LOADER_SHA=$(get_manifest_value LINUX_ARM64_LOADER_SHA256)
    YC_CLOUD_CORE_URL=$(get_manifest_value LINUX_ARM64_CORE_URL)
    YC_CLOUD_CORE_PKG_SHA256=$(get_manifest_value LINUX_ARM64_CORE_PKG_SHA256)
    YC_CLOUD_CORE_BIN_SHA256=$(get_manifest_value LINUX_ARM64_CORE_BIN_SHA256)
    YC_CLOUD_CORE_RELEASE_ID=$(get_manifest_value LINUX_ARM64_CORE_RELEASE_ID)
    YC_CLOUD_CORE_VERSION=$(get_manifest_value LINUX_ARM64_CORE_VERSION)
    YC_CLOUD_CORE_PLATFORM=$(get_manifest_value LINUX_ARM64_CORE_PLATFORM)
    ;;
  *)
    printf 'ERROR: unsupported architecture: %s on %s\n' "$arch" "$OS" >&2
    exit 1
    ;;
esac

for required in "$LOADER_URL" "$LOADER_SHA" "$YC_CLOUD_CORE_URL" "$YC_CLOUD_CORE_PKG_SHA256" "$YC_CLOUD_CORE_BIN_SHA256" "$YC_CLOUD_CORE_RELEASE_ID" "$YC_CLOUD_CORE_VERSION" "$YC_CLOUD_CORE_PLATFORM"; do
  if [ -z "$required" ]; then
    printf 'ERROR: manifest missing required encrypted release field\n' >&2
    exit 1
  fi
done

LOADER_DIR="$YC_HOME/loader/$(printf '%.8s' "$LOADER_SHA")"
LOADER_BIN="$LOADER_DIR/yc-cloud-loader"

if [ ! -f "$LOADER_BIN" ] || ! verify_sha256 "$LOADER_BIN" "$LOADER_SHA"; then
  printf 'Downloading yc-cloud loader...\n' >&2
  mkdir -p "$LOADER_DIR"
  curl -fSL --retry 3 -o "$LOADER_BIN" "$LOADER_URL"
  if ! verify_sha256 "$LOADER_BIN" "$LOADER_SHA"; then
    rm -f "$LOADER_BIN"
    printf 'ERROR: loader SHA256 verification failed\n' >&2
    exit 1
  fi
  chmod +x "$LOADER_BIN"
fi

export YC_CLOUD_CORE_URL
export YC_CLOUD_CORE_PKG_SHA256
export YC_CLOUD_CORE_BIN_SHA256
export YC_CLOUD_CORE_RELEASE_ID
export YC_CLOUD_CORE_VERSION
export YC_CLOUD_CORE_PLATFORM

exec "$LOADER_BIN" "$@"
