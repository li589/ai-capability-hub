#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

ENTRYPOINT="${PAPERLESS_ENTRYPOINT:-app.py}"
VENV_DIR=".venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[PYTHON_NOT_FOUND] 未检测到 Python 3.10 或更高版本。"
  echo "为了安全，启动器不会联网下载、运行安装器或申请管理员权限。"
  echo "请让 IT 管理员安装 Python，安装后再次运行本启动器。"
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)'; then
  echo "[PYTHON_VERSION_UNSUPPORTED] Python 版本过低；需要 Python 3.10 或更高版本。"
  exit 1
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "[信息] 正在创建项目虚拟环境..."
  python3 -m venv "$VENV_DIR" || {
    echo "[VENV_CREATE_FAILED] 虚拟环境创建失败；请检查 Python 安装和项目目录写入权限。"
    exit 1
  }
fi

VENV_PY="$VENV_DIR/bin/python"
if [ ! -f "scripts/install_dependencies.py" ]; then
  echo "[DEPENDENCY_HELPER_MISSING] 缺少依赖安装助手；请重新解压完整系统 ZIP。"
  exit 2
fi

echo "[信息] 正在校验已验证的离线依赖；启动器不会联网安装..."
"$VENV_PY" "scripts/install_dependencies.py" "." --offline-only || {
  echo "[DEPENDENCY_INSTALL_FAILED] 依赖准备失败；数据库未修改。"
  echo "处理建议：请由 IT 准备带 SHA-256 清单的 wheels；不要临时关闭安全策略。"
  exit 2
}

if [ ! -f "$ENTRYPOINT" ]; then
  echo "[ENTRYPOINT_MISSING] 找不到程序入口：$ENTRYPOINT；请重新解压完整系统 ZIP。"
  exit 2
fi

if [ -f "scripts/preflight_check.py" ]; then
  echo "[信息] 正在执行启动前自检..."
  "$VENV_PY" "scripts/preflight_check.py" "." || {
    echo "[PREFLIGHT_FAILED] 启动前自检未通过；请按上方中文解决步骤处理后重试。"
    exit 2
  }
fi

echo "[信息] 正在启动无纸化业务系统..."
exec "$VENV_PY" "$ENTRYPOINT"
