#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/qodersec-launch.sh" review settings --platform=qoder --format=json
