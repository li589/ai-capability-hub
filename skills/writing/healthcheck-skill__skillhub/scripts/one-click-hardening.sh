# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# ================================================
# 一键自动加固脚本 v1.0
# 快速修复所有安全问题
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
INTERACTIVE=true
AUTO_APPROVE=false
BACKUP_ENABLED=true
BACKUP_DIR="${HOME}/.config/openclaw/backups"
LOG_FILE="/tmp/hardening-$(date +%Y%m%d-%H%M%S).log"

# 统计
FIXED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0

# 初始化
init() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/pre-hardening"
    
    echo "==============================================" > "$LOG_FILE"
    echo "OpenClaw 一键加固日志" >> "$LOG_FILE"
    echo "开始时间: $(date)" >> "$LOG_FILE"
    echo "==============================================" >> "$LOG_FILE"
}

# 打印函数
print_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "步骤 $1: $2"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_ok() {
    echo -e "  ${GREEN}✓${NC} $1"
    echo "[OK] $1" >> "$LOG_FILE"
}

print_skip() {
    echo -e "  ${YELLOW}○${NC} $1"
    echo "[SKIP] $1" >> "$LOG_FILE"
}

print_fail() {
    echo -e "  ${RED}✗${NC} $1"
    echo "[FAIL] $1" >> "$LOG_FILE"
}

print_info() {
    echo -e "  ${BLUE}→${NC} $1"
    echo "[INFO] $1" >> "$LOG_FILE"
}

# 备份文件
backup_file() {
    local file="$1"
    local backup_dir="$BACKUP_DIR/pre-hardening"
    
    if [ -f "$file" ]; then
        local filename=$(basename "$file")
        local backup_path="${backup_dir}/${filename}.$(date +%Y%m%d%H%M%S).bak"
        cp "$file" "$backup_path"
        print_info "已备份: $filename → $backup_path"
    fi
}

# 获取用户确认
confirm() {
    if [ "$AUTO_APPROVE" = true ]; then
        return 0
    fi
    
    read -p "  是否执行此修复? (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# 修复1: 文件权限
fix_permissions() {
    print_step "1" "修复文件权限"
    
    local config_dir="${HOME}/.config/openclaw"
    local fixed=0
    
    # 修复配置目录权限
    if [ -d "$config_dir" ]; then
        local current_perms=$(stat -c %a "$config_dir" 2>/dev/null || echo "???")
        if [ "$current_perms" != "700" ] && [ "$current_perms" != "750" ]; then
            print_info "当前目录权限: $current_perms"
            if confirm; then
                backup_file "$config_dir"
                chmod 700 "$config_dir"
                print_ok "已修复: 目录权限 → 700"
                ((fixed++))
            else
                print_skip "跳过: 目录权限修复"
                ((SKIPPED_COUNT++))
            fi
        else
            print_ok "无需修复: 目录权限已是 $current_perms"
        fi
    fi
    
    # 修复MEMORY.md权限
    local memory_file="${config_dir}/MEMORY.md"
    if [ -f "$memory_file" ]; then
        local current_perms=$(stat -c %a "$memory_file" 2>/dev/null || echo "???")
        if [ "$current_perms" != "600" ]; then
            print_info "MEMORY.md当前权限: $current_perms"
            if confirm; then
                backup_file "$memory_file"
                chmod 600 "$memory_file"
                print_ok "已修复: MEMORY.md权限 → 600"
                ((fixed++))
            else
                print_skip "跳过: MEMORY.md权限修复"
                ((SKIPPED_COUNT++))
            fi
        else
            print_ok "无需修复: MEMORY.md权限已是 $current_perms"
        fi
    fi
    
    # 修复.ssh目录权限
    local ssh_dir="${HOME}/.ssh"
    if [ -d "$ssh_dir" ]; then
        local current_perms=$(stat -c %a "$ssh_dir" 2>/dev/null || echo "???")
        if [ "$current_perms" != "700" ]; then
            print_info ".ssh目录当前权限: $current_perms"
            if confirm; then
                backup_file "$ssh_dir"
                chmod 700 "$ssh_dir"
                # 同时修复SSH文件权限
                chmod 600 "$ssh_dir"/* 2>/dev/null || true
                print_ok "已修复: .ssh目录权限 → 700"
                ((fixed++))
            else
                print_skip "跳过: .ssh目录权限修复"
                ((SKIPPED_COUNT++))
            fi
        else
            print_ok "无需修复: .ssh目录权限已是 $current_perms"
        fi
    fi
    
    ((FIXED_COUNT+=fixed))
}

# 修复2: Gateway配置
fix_gateway_config() {
    print_step "2" "加固Gateway配置"
    
    local config_file="${HOME}/.config/openclaw/config.json"
    
    if [ ! -f "$config_file" ]; then
        print_skip "配置文件不存在，跳过Gateway加固"
        ((SKIPPED_COUNT++))
        return
    fi
    
    local changes=0
    
    # 检查并修复每项配置
    if grep -q '"allowCustomGatewayUrl":\s*true' "$config_file"; then
        print_info "发现: 允许自定义Gateway URL (不安全)"
        if confirm; then
            backup_file "$config_file"
            sed -i 's/"allowCustomGatewayUrl":\s*true/"allowCustomGatewayUrl": false/g' "$config_file"
            print_ok "已修复: 禁止自定义Gateway URL"
            ((changes++))
        else
            print_skip "跳过: Gateway URL配置"
        fi
    else
        print_ok "无需修复: Gateway URL已是安全设置"
    fi
    
    if grep -q '"verifyOrigin":\s*false' "$config_file"; then
        print_info "发现: WebSocket未验证Origin"
        if confirm; then
            backup_file "$config_file"
            sed -i 's/"verifyOrigin":\s*false/"verifyOrigin": true/g' "$config_file"
            print_ok "已修复: 启用Origin验证"
            ((changes++))
        else
            print_skip "跳过: Origin验证配置"
        fi
    else
        print_ok "无需修复: Origin验证已是启用状态"
    fi
    
    if grep -q '"requireConfirmation":\s*false' "$config_file"; then
        print_info "发现: 设备配对未要求确认"
        if confirm; then
            backup_file "$config_file"
            sed -i 's/"requireConfirmation":\s*false/"requireConfirmation": true/g' "$config_file"
            print_ok "已修复: 启用配对确认"
            ((changes++))
        else
            print_skip "跳过: 配对确认配置"
        fi
    else
        print_ok "无需修复: 配对确认已是启用状态"
    fi
    
    if grep -q '"localhostExempt":\s*true' "$config_file"; then
        print_info "发现: 速率限制豁免localhost"
        if confirm; then
            backup_file "$config_file"
            sed -i 's/"localhostExempt":\s*true/"localhostExempt": false/g' "$config_file"
            print_ok "已修复: 禁用localhost豁免"
            ((changes++))
        else
            print_skip "跳过: 速率限制配置"
        fi
    fi
    
    ((FIXED_COUNT+=changes))
}

# 修复3: SSH配置
fix_ssh_config() {
    print_step "3" "加固SSH配置"
    
    local sshd_config="/etc/ssh/sshd_config"
    local user_ssh_config="${HOME}/.ssh/config"
    
    # 检查SSH配置可修改性
    if [ -f "$sshd_config" ] && [ -w "$sshd_config" ]; then
        print_info "系统SSH配置可修改（需要sudo权限）"
        print_info "建议手动执行以下命令:"
        echo "    sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"
        echo "    sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
        echo "    sudo systemctl restart sshd"
        print_skip "跳过: 系统SSH配置（需要root权限）"
        ((SKIPPED_COUNT++))
    else
        print_info "系统SSH配置不可修改，跳过"
        ((SKIPPED_COUNT++))
    fi
    
    # 用户SSH配置
    if [ -f "$user_ssh_config" ]; then
        print_ok "用户SSH配置文件存在"
    else
        print_info "创建用户SSH配置..."
        cat > "$user_ssh_config" << 'EOF'
# SSH Client Configuration
Host *
    StrictHostKeyChecking ask
    IdentityFile ~/.ssh/id_ed25519
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
        chmod 600 "$user_ssh_config"
        print_ok "已创建用户SSH配置文件"
        ((FIXED_COUNT++))
    fi
}

# 修复4: 防火墙配置
fix_firewall() {
    print_step "4" "检查防火墙状态"
    
    # 检查ufw
    if command -v ufw &> /dev/null; then
        local ufw_status=$(sudo ufw status 2>/dev/null | head -1)
        if [[ "$ufw_status" == *"inactive"* ]]; then
            print_info "防火墙状态: 未激活"
            if confirm; then
                sudo ufw enable
                print_ok "已启用防火墙"
                ((FIXED_COUNT++))
            else
                print_skip "跳过: 防火墙启用"
                ((SKIPPED_COUNT++))
            fi
        else
            print_ok "防火墙已是激活状态"
        fi
    else
        print_info "ufw未安装，跳过防火墙配置"
        print_info "如需配置防火墙，请手动安装: sudo apt install ufw"
        ((SKIPPED_COUNT++))
    fi
}

# 修复5: 敏感数据检查
fix_sensitive_data() {
    print_step "5" "敏感数据安全检查"
    
    local memory_file="${HOME}/.config/openclaw/MEMORY.md"
    
    if [ ! -f "$memory_file" ]; then
        print_skip "MEMORY.md不存在，跳过敏感数据检查"
        ((SKIPPED_COUNT++))
        return
    fi
    
    # 检查硬编码密钥
    if grep -qiE "sk_[a-zA-Z0-9]{20,}" "$memory_file" 2>/dev/null; then
        print_fail "发现疑似硬编码API密钥!"
        print_info "建议:"
        echo "    1. 将密钥移至环境变量"
        echo "    2. 使用 \${API_KEY} 格式引用"
        echo "    3. 运行 memory-auditor.sh 进行完整审计"
        print_info "使用 memory-auditor.sh --fix 自动处理"
        ((FAILED_COUNT++))
    else
        print_ok "未发现明显硬编码密钥"
    fi
    
    # 检查环境变量使用
    if ! grep -qE '\$\{[A-Z_]+\}' "$memory_file" 2>/dev/null; then
        print_info "建议使用环境变量存储敏感信息"
        print_info "格式: export API_KEY=\${API_KEY}"
    else
        print_ok "已使用环境变量存储敏感信息"
    fi
}

# 修复6: 定时任务
fix_cron_jobs() {
    print_step "6" "配置定时安全检查"
    
    print_info "推荐设置以下定时任务:"
    echo ""
    echo "  # 每日安全检查 (每天 9:00)"
    echo "  0 9 * * * /path/to/scripts/security-checks.sh"
    echo ""
    echo "  # 每周权限审计 (每周一 9:00)"
    echo "  0 9 * * 1 /path/to/scripts/memory-auditor.sh"
    echo ""
    echo "  # 每月全面检查 (每月1号 9:00)"
    echo "  0 9 1 * * /path/to/scripts/auto-fixer.sh -c"
    echo ""
    
    print_info "使用 OpenClaw cron 功能配置定时任务"
    print_info "或参考 SKILL.md 中的定期自动检查章节"
    
    ((SKIPPED_COUNT++))
}

# 生成报告
generate_report() {
    echo ""
    echo "=============================================="
    echo -e "${CYAN}📊 一键加固完成报告${NC}"
    echo "=============================================="
    echo "完成时间: $(date)"
    echo ""
    echo -e "  ${GREEN}✓${NC} 已修复: $FIXED_COUNT 项"
    echo -e "  ${YELLOW}○${NC} 已跳过: $SKIPPED_COUNT 项"
    echo -e "  ${RED}✗${NC} 需手动处理: $FAILED_COUNT 项"
    echo ""
    echo "详细日志: $LOG_FILE"
    echo "备份目录: $BACKUP_DIR/pre-hardening/"
    echo ""
    
    if [ $FAILED_COUNT -gt 0 ]; then
        echo -e "${RED}⚠️  存在需要手动处理的问题，请查看上方详情${NC}"
    fi
    
    if [ $FIXED_COUNT -gt 0 ]; then
        echo -e "${GREEN}✅ 安全加固完成！建议重启OpenClaw服务使配置生效${NC}"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
🛡️ OpenClaw 一键自动加固工具 v1.0

用法: $0 [选项]

选项:
  -y, --yes          自动确认所有修复（无需交互）
  -h, --help         显示帮助信息

示例:
  $0                  # 交互式加固
  $0 -y               # 自动加固（所有确认）

安全检查项目:
  1. 文件权限（MEMORY.md、配置目录）
  2. Gateway安全配置
  3. SSH配置
  4. 防火墙状态
  5. 敏感数据检查
  6. 定时任务配置

注意:
  - 所有修复前会自动备份
  - 系统级配置可能需要sudo权限
  - 建议在非生产环境先测试

EOF
}

# 主函数
main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes)
                AUTO_APPROVE=true
                shift
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
    
    echo -e "${CYAN}"
    echo "=============================================="
    echo "🛡️  OpenClaw 一键自动加固"
    echo "=============================================="
    echo -e "${NC}"
    echo "开始时间: $(date)"
    echo ""
    
    init
    
    echo -e "${YELLOW}⚠️  开始加固前，请确保已阅读并理解每个修复项${NC}"
    echo ""
    
    fix_permissions
    fix_gateway_config
    fix_ssh_config
    fix_firewall
    fix_sensitive_data
    fix_cron_jobs
    
    generate_report
}

# 启动
main "$@"
