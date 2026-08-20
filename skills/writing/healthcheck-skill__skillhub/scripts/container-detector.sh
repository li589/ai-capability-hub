#!/bin/bash
# =============================================================================
# 容器环境检测脚本 | Container Environment Detector
# =============================================================================
# 版本: 4.7.0
# 功能: 自动检测容器环境，动态调整安全检查策略
# 来源: v4.7.0 新增 - 响应 @jarvis_431488 建议
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测结果变量
IS_CONTAINER=false
IS_PRIVILEGED=false
CONTAINER_TYPE=""
SKIP_PROC_ENVIRON=false
SKIP_SSH_CHECK=false
SKIP_FIREWALL_CHECK=false

# =============================================================================
# 检测函数
# =============================================================================

# 检测是否在容器内
detect_container() {
    # 方法1: 检查 .dockerenv 文件
    if [ -f /.dockerenv ]; then
        IS_CONTAINER=true
        CONTAINER_TYPE="docker"
        return 0
    fi
    
    # 方法2: 检查 cgroup
    if [ -f /proc/1/cgroup ] && grep -qE "docker|containerd|kubepods" /proc/1/cgroup 2>/dev/null; then
        IS_CONTAINER=true
        if grep -q "kubepods" /proc/1/cgroup 2>/dev/null; then
            CONTAINER_TYPE="kubernetes"
        else
            CONTAINER_TYPE="docker"
        fi
        return 0
    fi
    
    # 方法3: 检查 container 环境变量
    if [ -n "${container:-}" ]; then
        IS_CONTAINER=true
        CONTAINER_TYPE="$container"
        return 0
    fi
    
    # 方法4: 检查其他容器标记
    if [ -f /run/.containerenv ] || [ -d /run/containers ]; then
        IS_CONTAINER=true
        CONTAINER_TYPE="podman"
        return 0
    fi
    
    return 1
}

# 检测是否为特权容器
detect_privileged() {
    # 方法1: 检查是否可写 /proc/sys/kernel
    if [ -w /proc/sys/kernel ] 2>/dev/null; then
        IS_PRIVILEGED=true
        return 0
    fi
    
    # 方法2: 检查 cap_sys_admin (添加超时避免卡住)
    if command -v capsh >/dev/null 2>&1; then
        if timeout 2 capsh --print 2>/dev/null | grep -q "cap_sys_admin"; then
            IS_PRIVILEGED=true
            return 0
        fi
    fi
    
    # 方法3: 尝试访问主机设备
    if [ -r /dev/sda ] 2>/dev/null || [ -r /dev/mem ] 2>/dev/null; then
        IS_PRIVILEGED=true
        return 0
    fi
    
    return 1
}

# 确定需要跳过的检查项
determine_skip_items() {
    if [ "$IS_CONTAINER" = false ]; then
        # 宿主机环境 - 执行完整检查
        SKIP_PROC_ENVIRON=false
        SKIP_SSH_CHECK=false
        SKIP_FIREWALL_CHECK=false
        return
    fi
    
    if [ "$IS_PRIVILEGED" = true ]; then
        # 特权容器 - 执行大部分检查
        echo -e "${YELLOW}⚠️  检测到特权容器${NC}"
        SKIP_PROC_ENVIRON=false
        SKIP_SSH_CHECK=true   # 容器内通常无 SSH
        SKIP_FIREWALL_CHECK=true  # 容器网络隔离
    else
        # 非特权容器 - 跳过受限检查
        echo -e "${YELLOW}ℹ️  检测到非特权容器${NC}"
        SKIP_PROC_ENVIRON=true    # 无法访问其他进程的 /proc
        SKIP_SSH_CHECK=true       # 容器内通常无 SSH
        SKIP_FIREWALL_CHECK=true  # 容器网络隔离
    fi
}

# =============================================================================
# 输出函数
# =============================================================================

print_detection_result() {
    echo -e "${BLUE}🐳 容器环境检测报告${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ "$IS_CONTAINER" = true ]; then
        echo -e "环境类型: ${GREEN}容器 ($CONTAINER_TYPE)${NC}"
        
        if [ "$IS_PRIVILEGED" = true ]; then
            echo -e "特权模式: ${RED}是${NC}"
        else
            echo -e "特权模式: ${GREEN}否${NC}"
        fi
        
        echo ""
        echo "检查项调整:"
        
        if [ "$SKIP_PROC_ENVIRON" = true ]; then
            echo -e "  ${YELLOW}⚠️  /proc/environ 检查: 跳过${NC} (非特权容器)"
        else
            echo -e "  ${GREEN}✅ /proc/environ 检查: 执行${NC}"
        fi
        
        if [ "$SKIP_SSH_CHECK" = true ]; then
            echo -e "  ${YELLOW}⚠️  SSH 配置检查: 跳过${NC} (容器环境)"
        else
            echo -e "  ${GREEN}✅ SSH 配置检查: 执行${NC}"
        fi
        
        if [ "$SKIP_FIREWALL_CHECK" = true ]; then
            echo -e "  ${YELLOW}⚠️  防火墙检查: 跳过${NC} (容器网络隔离)"
        else
            echo -e "  ${GREEN}✅ 防火墙检查: 执行${NC}"
        fi
        
    else
        echo -e "环境类型: ${GREEN}宿主机${NC}"
        echo ""
        echo -e "${GREEN}✅ 所有检查项将正常执行${NC}"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 导出变量供其他脚本使用
export_variables() {
    echo ""
    echo "环境变量导出（供其他脚本使用）:"
    echo "export HEALTHCHECK_IS_CONTAINER=$IS_CONTAINER"
    echo "export HEALTHCHECK_CONTAINER_TYPE=$CONTAINER_TYPE"
    echo "export HEALTHCHECK_IS_PRIVILEGED=$IS_PRIVILEGED"
    echo "export HEALTHCHECK_SKIP_PROC_ENVIRON=$SKIP_PROC_ENVIRON"
    echo "export HEALTHCHECK_SKIP_SSH_CHECK=$SKIP_SSH_CHECK"
    echo "export HEALTHCHECK_SKIP_FIREWALL_CHECK=$SKIP_FIREWALL_CHECK"
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    echo "🔍 正在检测容器环境..."
    echo ""
    
    # 执行检测
    detect_container || true
    
    if [ "$IS_CONTAINER" = true ]; then
        detect_privileged || true
    fi
    
    # 确定跳过的检查项
    determine_skip_items
    
    # 输出结果
    print_detection_result
    
    # 如果带了 --export 参数，导出环境变量
    if [ "${1:-}" = "--export" ]; then
        export_variables
    fi
    
    # 返回退出码供其他脚本使用
    if [ "$IS_CONTAINER" = true ]; then
        if [ "$IS_PRIVILEGED" = true ]; then
            exit 2  # 特权容器
        else
            exit 1  # 非特权容器
        fi
    else
        exit 0  # 宿主机
    fi
}

# 执行主函数
main "$@"
