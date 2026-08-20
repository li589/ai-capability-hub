#!/bin/bash
# ─────────────────────────────────────────────────────────
# Node.js LTS + UTP CLI 安装脚本（Windows / Git Bash）
# 无需管理员权限，zip 解压到用户目录 + setx 写入 PATH
#
# 用法:
#   bash install-win.sh
#
# 环境变量可覆盖默认 registry / 包名（见 UTP_NPM_REGISTRY / UTP_NPM_PACKAGE）
# ─────────────────────────────────────────────────────────
set -euo pipefail

INSTALL_DIR="$HOME/nodejs"
TEMP_DIR="$HOME/nodejs-install"

# 包源配置（默认公网；内网用户通过环境变量覆盖）
NPM_PACKAGE="@ut-protocol/utp"
NPM_REGISTRY="https://registry.npmjs.org"

# ── 0. 检查是否已安装 ─────────────────────────────────────
if command -v node &>/dev/null; then
    current=$(node --version 2>/dev/null || echo "unknown")
    echo "[INFO] 已检测到 Node.js: $current，将覆盖安装"
fi

# ── 1. 查询最新 LTS 版本号 ────────────────────────────────
echo "[1/7] 查询最新 LTS 版本..."
version=$(curl -sf https://nodejs.org/dist/latest-v24.x/ \
    | grep -o 'node-v[0-9]*\.[0-9]*\.[0-9]*' \
    | head -1 \
    | sed 's/node-v//')

if [[ -z "$version" ]]; then
    echo "[WARN] 无法查询 v24.x，尝试 v22.x..."
    version=$(curl -sf https://nodejs.org/dist/latest-v22.x/ \
        | grep -o 'node-v[0-9]*\.[0-9]*\.[0-9]*' \
        | head -1 \
        | sed 's/node-v//')
fi

if [[ -z "$version" ]]; then
    echo "[ERROR] 无法获取版本号，请检查网络连接。"
    exit 1
fi
echo "[OK] 目标版本: v$version"

# ── 2. 下载 zip ───────────────────────────────────────────
zip_name="node-v${version}-win-x64.zip"
download_url="https://nodejs.org/dist/v${version}/${zip_name}"
temp_zip="$TEMP_DIR/$zip_name"

mkdir -p "$TEMP_DIR"

if [[ -f "$temp_zip" ]]; then
    echo "[2/7] 安装包已存在，跳过下载: $temp_zip"
else
    echo "[2/7] 下载 Node.js v$version ..."
    echo "       $download_url"
    curl -L -o "$temp_zip" "$download_url" --progress-bar
    file_size=$(du -h "$temp_zip" | cut -f1)
    echo "[OK] 下载完成 ($file_size)"
fi

# ── 3. 解压 ───────────────────────────────────────────────
echo "[3/7] 解压到 $INSTALL_DIR ..."
extracted_dir="$HOME/node-v${version}-win-x64"

# 清理旧的解压目录（如果有）
[[ -d "$extracted_dir" ]] && rm -rf "$extracted_dir"

unzip -q -o "$temp_zip" -d "$HOME"

# 移动到固定路径
if [[ -d "$INSTALL_DIR" ]]; then
    backup="${INSTALL_DIR}-backup-$(date +%Y%m%d%H%M%S)"
    echo "[INFO] 备份旧版本到 $backup"
    mv "$INSTALL_DIR" "$backup"
fi
mv "$extracted_dir" "$INSTALL_DIR"
echo "[OK] 解压完成"

# ── 4. 写入 PATH ──────────────────────────────────────────
echo "[4/7] 配置 PATH ..."

# 检查用户级 PATH 是否已包含目标目录
current_user_path=$(cmd.exe //c "echo %PATH%" 2>/dev/null | tr -d '\r' || echo "")

if echo "$current_user_path" | grep -qi "nodejs"; then
    # 已有 nodejs 相关路径，检查是否指向我们的目录
    echo "[INFO] PATH 中已有 nodejs 相关条目，跳过 setx"
else
    # 用 setx 写入用户级 PATH
    win_path="C:\\Users\\${USERNAME}\\nodejs"
    cmd.exe //c "setx Path \"${win_path}\"" >/dev/null 2>&1
    echo "[OK] 已写入用户 PATH: $win_path"
fi

# ── 5. 验证 ───────────────────────────────────────────────
echo "[5/7] 验证安装..."
export PATH="$INSTALL_DIR:$PATH"

if command -v node &>/dev/null && command -v npm &>/dev/null; then
    node_ver=$(node --version)
    npm_ver=$(npm --version)
    echo ""
    echo "========================================="
    echo "  Node.js 安装成功！"
    echo "  node: $node_ver ($INSTALL_DIR/node.exe)"
    echo "  npm:  $npm_ver"
    echo "========================================="
    echo ""
    echo "[TIP] 新开的终端会自动生效。当前终端已临时生效。"
else
    echo ""
    echo "[WARN] 安装完成，但当前终端未检测到。"
    echo "       请关闭并重新打开终端，然后运行:"
    echo "         node --version"
    echo "         npm --version"
fi

# ── 清理临时文件 ──────────────────────────────────────────────
rm -rf "$TEMP_DIR"

# ── 6. 安装 utp CLI ─────────────────────────────────────────────
echo "[6/7] 安装 utp CLI..."

# 环境变量覆盖默认值（公网用户无需设置；内网用户设置 UTP_NPM_REGISTRY / UTP_NPM_PACKAGE）
NPM_PACKAGE="${UTP_NPM_PACKAGE:-$NPM_PACKAGE}"
NPM_REGISTRY="${UTP_NPM_REGISTRY:-$NPM_REGISTRY}"

npm install -g "${NPM_PACKAGE}@latest" --registry "${NPM_REGISTRY}" --silent 2>/dev/null
if command -v utp &>/dev/null; then
    utp_ver=$(utp --version 2>/dev/null || echo "unknown")
    echo "[OK] utp CLI 已安装: $utp_ver"
else
    echo "[ERROR] utp 安装失败，请检查网络和 npm 配置后重试"
    echo "        可稍后手动运行: npm install -g ${NPM_PACKAGE} --registry ${NPM_REGISTRY}"
    exit 1
fi

# ── 7. 执行 utp install ─────────────────────────────────────────
echo "[7/7] 执行 utp install..."
utp install
echo "[OK] utp install 完成"

echo ""
echo "完成！"
