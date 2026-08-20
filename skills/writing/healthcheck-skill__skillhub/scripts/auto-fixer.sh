# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# ================================================
# 自动化安全修复脚本 v1.0
# 实现自动检测和修复安全问题
# ================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
DRY_RUN=false
AUTO_FIX=false
BACKUP_DIR="${HOME}/.config/openclaw/backups"
LOG_FILE="/tmp/security-fix-$(date +%Y%m%d).log"

# 检测到的修复项
declare -a FIX_ITEMS=()
declare -a FIXED_ITEMS=()
declare -a FAILED_ITEMS=()

# 初始化
init() {
    mkdir -p "$BACKUP_DIR"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 自动化修复开始" >> "$LOG_FILE"
}

# 打印函数
print_header() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo -e "🛡️  OpenClaw 自动化安全修复"
    echo -e "==============================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[INFO] $1" >> "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    echo "[SUCCESS] $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

# 创建备份
create_backup() {
    local target="$1"
    local backup_file="${BACKUP_DIR}/backup-$(basename "$target")-$(date +%Y%m%d%H%M%S)"
    
    if [ -f "$target" ]; then
        cp "$target" "$backup_file"
        print_info "已创建备份: $backup_file"
        echo "$backup_file"
    elif [ -d "$target" ]; then
        tar -czf "$backup_file.tar.gz" "$target" 2>/dev/null || cp -r "$target" "$backup_file"
        print_info "已创建备份: $backup_file.tar.gz"
        echo "$backup_file.tar.gz"
    fi
}

# 检查1: 文件权限
check_file_permissions() {
    print_info "检查1: 文件权限..."
    
    local issues=()
    
    # 检查MEMORY.md权限
    if [ -f "${HOME}/.config/openclaw/MEMORY.md" ]; then
        local perms=$(stat -c %a "${HOME}/.config/openclaw/MEMORY.md" 2>/dev/null || echo "unknown")
        if [ "$perms" != "600" ] && [ "$perms" != "400" ]; then
            issues+=("MEMORY.md权限: $perms (应为600或400)")
        fi
    fi
    
    # 检查SSH目录权限
    if [ -d "${HOME}/.ssh" ]; then
        local ssh_perms=$(stat -c %a "${HOME}/.ssh" 2>/dev/null || echo "unknown")
        if [ "$ssh_perms" != "700" ] && [ "$ssh_perms" != "600" ]; then
            issues+=(".ssh目录权限: $ssh_perms (应为700或600)")
        fi
    fi
    
    # 检查配置目录权限
    if [ -d "${HOME}/.config/openclaw" ]; then
        local config_perms=$(stat -c %a "${HOME}/.config/openclaw" 2>/dev/null || echo "unknown")
        if [ "$config_perms" = "777" ] || [ "$config_perms" = "775" ]; then
            issues+=("openclaw配置目录权限: $config_perms (应为700或750)")
        fi
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        print_warning "发现权限问题:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    else
        print_success "文件权限检查通过"
        return 0
    fi
}

# 修复1: 文件权限
fix_file_permissions() {
    print_info "执行修复: 文件权限..."
    
    local fixed=0
    
    # 修复MEMORY.md权限
    if [ -f "${HOME}/.config/openclaw/MEMORY.md" ]; then
        create_backup "${HOME}/.config/openclaw/MEMORY.md"
        chmod 600 "${HOME}/.config/openclaw/MEMORY.md"
        print_success "已修复MEMORY.md权限为600"
        ((fixed++))
    fi
    
    # 修复SSH目录权限
    if [ -d "${HOME}/.ssh" ]; then
        create_backup "${HOME}/.ssh"
        chmod 700 "${HOME}/.ssh"
        chmod 600 "${HOME}/.ssh"/* 2>/dev/null || true
        print_success "已修复.ssh目录权限为700"
        ((fixed++))
    fi
    
    # 修复配置目录权限
    if [ -d "${HOME}/.config/openclaw" ]; then
        create_backup "${HOME}/.config/openclaw"
        chmod 700 "${HOME}/.config/openclaw"
        print_success "已修复配置目录权限为700"
        ((fixed++))
    fi
    
    return $fixed
}

# 检查2: Gateway配置
check_gateway_config() {
    print_info "检查2: Gateway安全配置..."
    
    local issues=()
    
    # 检查OpenClaw配置
    local config_file="${HOME}/.config/openclaw/config.json"
    if [ -f "$config_file" ]; then
        # 检查危险配置
        if grep -q '"allowCustomGatewayUrl":\s*true' "$config_file" 2>/dev/null; then
            issues+=("Gateway允许自定义URL")
        fi
        
        if grep -q '"verifyOrigin":\s*false' "$config_file" 2>/dev/null; then
            issues+=("WebSocket未验证Origin")
        fi
        
        if grep -q '"requireConfirmation":\s*false' "$config_file" 2>/dev/null; then
            issues+=("设备配对未要求确认")
        fi
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        print_warning "发现Gateway配置问题:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    else
        print_success "Gateway配置检查通过"
        return 0
    fi
}

# 修复2: Gateway配置
fix_gateway_config() {
    print_info "执行修复: Gateway配置..."
    
    local config_file="${HOME}/.config/openclaw/config.json"
    
    if [ ! -f "$config_file" ]; then
        print_warning "配置文件不存在，跳过Gateway配置修复"
        return 0
    fi
    
    create_backup "$config_file"
    
    # 创建修复后的配置
    local fixed_config="${config_file}.fixed.$(date +%Y%m%d%H%M%S)"
    cp "$config_file" "$fixed_config"
    
    # 修复危险配置
    sed -i 's/"allowCustomGatewayUrl":\s*true/"allowCustomGatewayUrl": false/g' "$fixed_config"
    sed -i 's/"verifyOrigin":\s*false/"verifyOrigin": true/g' "$fixed_config"
    sed -i 's/"requireConfirmation":\s*false/"requireConfirmation": true/g' "$fixed_config"
    
    # 应用修复
    mv "$fixed_config" "$config_file"
    print_success "已修复Gateway配置"
    
    return 1
}

# 检查3: 敏感数据
check_sensitive_data() {
    print_info "检查3: 敏感数据暴露..."
    
    local issues=()
    
    # 检查MEMORY.md中的敏感数据
    if [ -f "${HOME}/.config/openclaw/MEMORY.md" ]; then
        if grep -qiE "sk_[a-zA-Z0-9]{20,}" "${HOME}/.config/openclaw/MEMORY.md" 2>/dev/null; then
            issues+=("MEMORY.md中疑似包含API密钥")
        fi
    fi
    
    # 检查环境变量使用
    if [ -f "${HOME}/.config/openclaw/MEMORY.md" ]; then
        if ! grep -qE '\$\{[A-Z_]+\}' "${HOME}/.config/openclaw/MEMORY.md" 2>/dev/null; then
            issues+=("未使用环境变量存储敏感信息")
        fi
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        print_warning "发现敏感数据问题:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    else
        print_success "敏感数据检查通过"
        return 0
    fi
}

# 修复3: 敏感数据
fix_sensitive_data() {
    print_info "执行修复: 敏感数据..."
    
    print_warning "建议手动处理敏感数据:"
    echo "  1. 将API密钥移至环境变量"
    echo "  2. 使用 \${VAR_NAME} 格式引用"
    echo "  3. 运行 memory-auditor.sh 进行完整审计"
    
    return 0
}

# 检查4: 恶意技能
check_malicious_skills() {
    print_info "检查4: 恶意技能..."
    
    # 检查技能目录
    local skills_dir="${HOME}/.config/openclaw/skills"
    if [ -d "$skills_dir" ]; then
        local suspicious_count=$(find "$skills_dir" -name "*.js" -exec grep -l "eval\|decodeURIComponent\|atob\|fromCharCode" {} \; 2>/dev/null | wc -l)
        if [ "$suspicious_count" -gt 0 ]; then
            print_warning "发现 $suspicious_count 个可疑技能文件"
            return 1
        fi
    fi
    
    print_success "恶意技能检查通过"
    return 0
}

# 一键修复所有问题
fix_all() {
    print_info "开始一键修复所有问题..."
    
    local total_fixed=0
    local total_failed=0
    
    # 修复文件权限
    if ! check_file_permissions > /dev/null 2>&1; then
        if fix_file_permissions; then
            ((total_fixed++))
        else
            ((total_failed++))
        fi
    fi
    
    # 修复Gateway配置
    if ! check_gateway_config > /dev/null 2>&1; then
        if fix_gateway_config; then
            ((total_fixed++))
        else
            ((total_failed++))
        fi
    fi
    
    # 修复敏感数据（仅提示）
    if ! check_sensitive_data > /dev/null 2>&1; then
        fix_sensitive_data
        print_warning "敏感数据问题需要手动处理"
    fi
    
    echo ""
    echo "=============================================="
    echo -e "${CYAN}📊 修复总结${NC}"
    echo "=============================================="
    echo -e "修复项目: ${GREEN}$total_fixed${NC}"
    echo -e "失败项目: ${RED}$total_failed${NC}"
    echo "日志文件: $LOG_FILE"
    echo ""
    
    return $total_failed
}

# 生成报告
generate_report() {
    echo ""
    echo "=============================================="
    echo -e "${CYAN}📋 安全修复报告${NC}"
    echo "=============================================="
    echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "执行模式: $([ "$AUTO_FIX" = true ] && echo "自动修复" || echo "仅检查")"
    echo ""
    
    echo "【文件权限检查】"
    check_file_permissions
    echo ""
    
    echo "【Gateway配置检查】"
    check_gateway_config
    echo ""
    
    echo "【敏感数据检查】"
    check_sensitive_data
    echo ""
    
    echo "【恶意技能检查】"
    check_malicious_skills
    echo ""
}

# 显示帮助
show_help() {
    cat << EOF
🛡️ OpenClaw 自动化安全修复工具 v1.0

用法: $0 [选项]

选项:
  -c, --check        仅检查不修复
  -f, --fix          自动修复所有问题
  -r, --report       生成详细报告
  -h, --help         显示帮助信息

示例:
  $0 -c                    # 仅检查问题
  $0 -f                    # 一键自动修复
  $0 -r                    # 生成详细报告

注意: 修复前会自动创建备份到 ~/.config/openclaw/backups/

EOF
}

# 主函数
main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--check)
                DRY_RUN=true
                shift
                ;;
            -f|--fix)
                AUTO_FIX=true
                shift
                ;;
            -r|--report)
                print_header
                generate_report
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_header
    
    if [ "$AUTO_FIX" = true ]; then
        print_info "执行模式: 自动修复"
        echo ""
        fix_all
    else
        print_info "执行模式: 仅检查"
        echo ""
        generate_report
        echo ""
        print_info "使用 --fix 参数启用自动修复"
    fi
}

# 启动
init
main "$@"
