# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# Permission Fixer - 权限修复脚本
# 版本: 4.0.0
# 用途: 修复不安全的文件权限

set -e

DATA_DIR="${HOME}/.openclawhealthcheck"
CONFIG_DIR="${DATA_DIR}/config"

echo "🔒 修复配置文件权限"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 创建必要的目录
mkdir -p "$DATA_DIR" "$CONFIG_DIR"

# 设置安全的目录权限
echo "1/5: 设置目录权限..."
chmod 700 "$DATA_DIR" 2>/dev/null && echo "    ✅ DATA_DIR: 700" || echo "    ⚠️  DATA_DIR权限设置失败"
chmod 700 "$CONFIG_DIR" 2>/dev/null && echo "    ✅ CONFIG_DIR: 700" || echo "    ⚠️  CONFIG_DIR权限设置失败"

# 设置安全的配置文件权限
echo "2/5: 检查配置文件权限..."
sensitive_files=(
    "$CONFIG_DIR/config.json"
    "$CONFIG_DIR/credentials.json"
    "$CONFIG_DIR/api_keys.json"
)

for file in "${sensitive_files[@]}"; do
    if [ -f "$file" ]; then
        chmod 600 "$file" 2>/dev/null && echo "    ✅ $(basename $file): 600" || echo "    ⚠️  $(basename $file)权限设置失败"
    fi
done

# 设置公共配置文件权限
echo "3/5: 检查公共配置文件权限..."
public_files=(
    "$CONFIG_DIR/settings.json"
    "$CONFIG_DIR/monitoring.json"
)

for file in "${public_files[@]}"; do
    if [ -f "$file" ]; then
        chmod 640 "$file" 2>/dev/null && echo "    ✅ $(basename $file): 640" || echo "    ⚠️  $(basename $file)权限设置失败"
    fi
done

# 检查脚本权限
echo "4/5: 检查脚本权限..."
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
find "$script_dir/scripts" -type f -name "*.sh" -exec chmod 700 {} \; 2>/dev/null
echo "    ✅ 所有脚本已设置为700权限"

# 检查日志文件权限
echo "5/5: 检查日志文件权限..."
log_files=(
    "$DATA_DIR/logs/healthcheck.log"
    "$DATA_DIR/reports/detection-history.db"
)

for file in "${log_files[@]}"; do
    if [ -f "$file" ]; then
        chmod 600 "$file" 2>/dev/null && echo "    ✅ $(basename $file): 600" || echo "    ⚠️  $(basename $file)权限设置失败"
    fi
done

echo ""
echo "✅ 权限修复完成"
echo ""
echo "权限总结:"
echo "  敏感配置: 600 (仅所有者读写)"
echo "  公共配置: 640 (所有者读写,组只读)"
echo "  脚本文件: 700 (仅所有者执行)"
echo "  数据目录: 700 (仅所有者访问)"
