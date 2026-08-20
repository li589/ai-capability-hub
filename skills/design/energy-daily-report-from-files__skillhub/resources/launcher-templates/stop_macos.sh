#!/bin/bash
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PYTHON_CMD=""
if [ -x ".venv/bin/python" ]; then
  PYTHON_CMD=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="$(command -v python)"
fi

if [ -z "$PYTHON_CMD" ]; then
  printf '[停止失败] 未找到可用 Python。请按运行说明检查环境。\n'
  exit 2
fi
if [ ! -f "stop_server.py" ]; then
  printf '[停止失败] 当前目录缺少 stop_server.py。\n'
  exit 3
fi

"$PYTHON_CMD" "stop_server.py"
