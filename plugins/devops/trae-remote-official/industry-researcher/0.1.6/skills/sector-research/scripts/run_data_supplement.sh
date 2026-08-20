#!/bin/bash
# dataSupplement 数据层启动脚本（自适应沙箱/本地）
# 用法: bash scripts/run_data_supplement.sh "from domains.quotes import realtime_quote; print(realtime_quote('600519'))"
# 或:   bash scripts/run_data_supplement.sh scripts/verify_data_supplement.py   (传入 .py 文件路径)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${SKILL_DIR}/dataSupplement"
VENV_DIR="${SKILL_DIR}/.venv"
PYTHON="${VENV_DIR}/bin/python"
REQUIREMENTS="${SKILL_DIR}/requirements.txt"

# --- 判断是否在沙箱环境（PYTHONHOME 劫持） ---
SANDBOXED=false
if [ -n "${PYTHONHOME:-}" ]; then
    SANDBOXED=true
fi

# --- 获取干净的 Python 路径 ---
_find_python() {
    for p in python3.12 python3.11 python3; do
        local path
        path="$(command -v "$p" 2>/dev/null || true)"
        if [ -n "$path" ]; then
            echo "$path"
            return
        fi
    done
    echo "python3"
}
BASE_PYTHON="$(_find_python)"

# --- 自动创建 venv + 安装依赖 ---
if [ ! -f "$PYTHON" ]; then
    echo "[SETUP] 首次使用，创建虚拟环境..."

    if [ "$SANDBOXED" = true ]; then
        # 沙箱环境：必须 env -i 清除 PYTHONHOME 才能创建 venv
        env -i HOME="$HOME" PATH="/usr/local/bin:/usr/bin:/bi/opt/.local/bin" \
            "$BASE_PYTHON" -m venv "$VENV_DIR"
    else
        "$BASE_PYTHON" -m venv "$VENV_DIR"
    fi

    echo "[SETUP] 安装依赖（约 1-2 分钟）..."
    if [ "$SANDBOXED" = true ]; then
        env -i HOME="$HOME" PATH="/usr/local/bin:/usr/bin:/bin:${VENV_DIR}/bin" \
            "$VENV_DIR/bin/pip" install --quiet --upgrade pip
        env -i HOME="$HOME" PATH="/usr/local/bin:/usr/bin:/bin:${VENV_DIR}/bin" \
            "$VENV_DIR/bin/pip" install --quiet -r "$REQUIREMENTS"
    else
        "$VENV_DIR/bin/pip" install --quiet --upgrade pip
        "$VENV_DIR/bin/pip" install --quiet -r "$REQUIREMENTS"
    fi

    echo "[SETUP] 虚拟环境就绪: $VENV_DIR"
fi

# --- 判断输入是代码还是文件 ---
INPUT="$1"
if [[ "$INPUT" == *.py ]]; then
    EXEC_ARGS=("$INPUT")
else
    EXEC_ARGS=(-c "$INPUT")
fi

# --- 执行 ---
if [ "$SANDBOXED" = true ]; then
    exec env -i \
        HOME="$HOME" \
        PATH="/usr/local/bin:/usr/bin:/bin:${VENV_DIR}/bin" \
        PYTHONPATH="$DATA_DIR" \
        "$PYTHON" "${EXEC_ARGS[@]}"
else
    export PYTHONPATH="$DATA_DIR"
    exec "$PYTHON" "${EXEC_ARGS[@]}"
fi
