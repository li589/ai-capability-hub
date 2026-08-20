# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# 快速上手指南 - Quick Start Guide for Beginners
# 让新用户在 30 秒内完成第一次安全检查

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

clear

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     🛡️  OpenClaw 主机安全加固工具 - 快速上手指南            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: 检测环境
echo -e "${BOLD}[Step 1/3] 检测环境...${NC}"

if [ -f /.dockerenv ]; then
    ENV_TYPE="container"
    echo -e "  ${GREEN}✓${NC} 容器环境（Docker/K8s）"
elif [ -f /proc/1/cgroup ] && grep -q "kubepods\|docker" /proc/1/cgroup 2>/dev/null; then
    ENV_TYPE="container"
    echo -e "  ${GREEN}✓${NC} 容器环境"
elif command -v systemctl &>/dev/null && systemctl is-system-running &>/dev/null; then
    ENV_TYPE="server"
    echo -e "  ${GREEN}✓${NC} 服务器环境"
else
    ENV_TYPE="local"
    echo -e "  ${GREEN}✓${NC} 本地环境"
fi

echo ""

# Step 2: 推荐命令
echo -e "${BOLD}[Step 2/3] 为您推荐：${NC}"
echo ""

case "$ENV_TYPE" in
    container)
        echo "  📦 容器环境推荐："
        echo "    $ openclaw status                    # 查看状态"
        echo "    $ ./scripts/security-checks.sh       # 安全检查"
        echo "    $ ./scripts/env-leak-detector.sh     # 环境变量检测"
        ;;
    server)
        echo "  🖥️ 服务器环境推荐："
        echo "    $ openclaw status --all              # 详细状态"
        echo "    $ openclaw security audit            # 安全审计"
        echo "    $ ./scripts/one-click-hardening.sh   # 一键加固"
        ;;
    *)
        echo "  💻 本地环境推荐："
        echo "    $ openclaw status                    # 查看状态"
        echo "    $ ./scripts/env-leak-detector.sh     # 敏感数据检测"
        echo "    $ ./examples/scripts/basic-cve-check.sh  # CVE检查"
        ;;
esac

echo ""

# Step 3: 快速检查
echo -e "${BOLD}[Step 3/3] 快速安全检查...${NC}"
echo ""

# 检查 1: OpenClaw 状态
echo -n "  [1/5] OpenClaw 状态... "
if command -v openclaw &>/dev/null; then
    echo -e "${GREEN}✓ 已安装${NC}"
else
    echo -e "${YELLOW}⚠ 未安装${NC}"
fi

# 检查 2: SSH 密钥权限
echo -n "  [2/5] SSH 密钥权限... "
if [ -f ~/.ssh/id_rsa ]; then
    perms=$(stat -c %a ~/.ssh/id_rsa 2>/dev/null || stat -f %Lp ~/.ssh/id_rsa 2>/dev/null)
    if [ "$perms" = "600" ]; then
        echo -e "${GREEN}✓ 安全${NC}"
    else
        echo -e "${YELLOW}⚠ 需修复 (chmod 600)${NC}"
    fi
else
    echo -e "${GREEN}✓ 无密钥文件${NC}"
fi

# 检查 3: 敏感变量
echo -n "  [3/5] 环境变量泄露... "
sensitive=$(env 2>/dev/null | grep -ciE "API_KEY|SECRET|TOKEN|PASSWORD" || echo 0)
if [ "$sensitive" -eq 0 ]; then
    echo -e "${GREEN}✓ 无明显泄露${NC}"
else
    echo -e "${YELLOW}⚠ 发现 $sensitive 个敏感变量${NC}"
fi

# 检查 4: Root 权限
echo -n "  [4/5] 运行权限... "
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${YELLOW}⚠ 以 root 运行${NC}"
else
    echo -e "${GREEN}✓ 非 root 用户${NC}"
fi

# 检查 5: 开放端口
echo -n "  [5/5] 监听端口... "
ports=$(ss -tuln 2>/dev/null | grep -c LISTEN || echo 0)
if [ "$ports" -gt 10 ]; then
    echo -e "${YELLOW}⚠ $ports 个端口${NC}"
else
    echo -e "${GREEN}✓ $ports 个端口${NC}"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BOLD}📖 后续步骤：${NC}"
echo "  1. 完整审计：${CYAN}openclaw security audit${NC}"
echo "  2. 查看文档：${CYAN}cat SKILL.md | head -100${NC}"
echo "  3. 社区支持：${CYAN}https://discord.gg/clawd${NC}"
echo ""
echo -e "${GREEN}✓ 快速上手完成！${NC}"
