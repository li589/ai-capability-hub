#!/usr/bin/env bash
# ifind-api wrapper — 首次运行自动下载对应平台的二进制
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="${SCRIPT_DIR}/ifind-api"
VERSION="v1.0.0"
BASE_URL="https://pub-0b3b619f0de9403693d49773b53a4564.r2.dev/${VERSION}"

# 已下载则直接执行
if [ -x "$BINARY" ]; then
  exec "$BINARY" "$@"
fi

# 检测平台
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "${OS}-${ARCH}" in
  darwin-arm64)   FILE="ifind-api-darwin-arm64" ;;
  linux-x86_64)   FILE="ifind-api-linux-amd64" ;;
  linux-amd64)    FILE="ifind-api-linux-amd64" ;;
  *)
    echo "{\"error\": \"不支持的平台: ${OS}-${ARCH}\"}" >&2
    exit 1
    ;;
esac

echo "首次运行，正在下载 ifind-api (${FILE})..." >&2
curl -fsSL "${BASE_URL}/${FILE}" -o "$BINARY"
chmod +x "$BINARY"
echo "下载完成。" >&2

exec "$BINARY" "$@"
