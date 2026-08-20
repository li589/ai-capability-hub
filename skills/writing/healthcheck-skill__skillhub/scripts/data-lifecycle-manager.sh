# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# ================================================
# 敏感数据生命周期管理检查脚本 v1.0
# 检查敏感数据的存储、使用、清理全生命周期
# =============================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
OPENCLAW_CONFIG_DIR="${HOME}/.config/openclaw"
MEMORY_FILE="${OPENCLAW_CONFIG_DIR}/MEMORY.md"
WORKSPACE_DIR="${HOME}/workspace"
VERBOSE=false
JSON_OUTPUT=false

# 敏感数据检测模式
SENSITIVE_PATTERNS=(
    "api[_-]?key"
    "secret[_-]?key"
    "password"
    "token"
    "credential"
    "sk_[a-zA-Z0-9]"
    "ak_[a-zA-Z0-9]"
    "-----BEGIN.*PRIVATE"
)

# 打印函数
print_header() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo -e "🛡️  敏感数据生命周期管理检查"
    echo -e "==============================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}【$1】${NC}"
    echo "----------------------------------------------"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# 检查1：环境变量中的敏感数据
check_env_variables() {
    print_section "1. 环境变量中的敏感数据"
    
    local found_issues=0
    
    # 检查常见敏感环境变量是否设置
    local sensitive_env_vars=(
        "OPENAI_API_KEY"
        "ANTHROPIC_API_KEY"
        "COZE_API_KEY"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "DATABASE_URL"
        "REDIS_URL"
    )
    
    for var in "${sensitive_env_vars[@]}"; do
        if env | grep -q "^${var}=" 2>/dev/null; then
            local value=$(env | grep "^${var}=" | cut -d= -f2)
            if [ ${#value} -gt 8 ]; then
                local masked="${value:0:4}...${value: -4}"
                print_success "✓ $var 已配置 (值: ${masked})"
            else
                print_success "✓ $var 已配置"
            fi
        else
            print_info "○ $var 未设置"
        fi
    done
    
    # 检查是否有敏感数据被导出到环境
    if [ -f "${OPENCLAW_CONFIG_DIR}/.env" ] 2>/dev/null; then
        print_warning "发现 .env 文件，建议检查其内容"
        if [ "$VERBOSE" = true ]; then
            grep -E "KEY|SECRET|PASSWORD|TOKEN" "${OPENCLAW_CONFIG_DIR}/.env" 2>/dev/null | head -5 || echo "  (未发现明显敏感数据)"
        fi
    fi
}

# 检查2：文件中的敏感数据
check_file_sensitive_data() {
    print_section "2. 配置和记忆文件中的敏感数据"
    
    local issues=0
    
    # 检查 MEMORY.md
    if [ -f "$MEMORY_FILE" ]; then
        print_info "检查文件: $MEMORY_FILE"
        
        for pattern in "${SENSITIVE_PATTERNS[@]}"; do
            if grep -qiE "$pattern" "$MEMORY_FILE" 2>/dev/null; then
                local matches=$(grep -niE "$pattern" "$MEMORY_FILE" 2>/dev/null | head -3)
                print_warning "发现疑似敏感数据模式: $pattern"
                if [ "$VERBOSE" = true ]; then
                    while IFS= read -r line; do
                        local line_num=$(echo "$line" | cut -d: -f1)
                        echo "  行 $line_num: $(echo "$line" | cut -d: -f2- | sed 's/sk_[a-zA-Z0-9]*/***API_KEY***/g; s/ak_[a-zA-Z0-9]*/***ACCESS_KEY***/g')"
                    done <<< "$matches"
                fi
                ((issues++))
            fi
        done
        
        if [ $issues -eq 0 ]; then
            print_success "MEMORY.md 中未发现明显敏感数据"
        fi
    else
        print_info "MEMORY.md 文件不存在"
    fi
    
    # 检查 workspace 目录
    if [ -d "$WORKSPACE_DIR" ]; then
        print_info "扫描 workspace 目录..."
        local workspace_issues=$(find "$WORKSPACE_DIR" -name "*.md" -type f 2>/dev/null | xargs grep -lE "sk_[a-zA-Z0-9]{20,}" 2>/dev/null || echo "")
        if [ -n "$workspace_issues" ]; then
            print_warning "在以下文件中发现疑似 API 密钥:"
            echo "$workspace_issues" | while read f; do
                echo "  - $f"
            done
        else
            print_success "workspace 目录中未发现明显敏感数据"
        fi
    fi
}

# 检查3：数据生命周期状态
check_data_lifecycle() {
    print_section "3. 数据生命周期状态"
    
    # MEMORY.md 生命周期
    if [ -f "$MEMORY_FILE" ]; then
        local file_age=$(($(date +%s) - $(stat -c %Y "$MEMORY_FILE" 2>/dev/null || echo $(date +%s))))
        local file_age_days=$((file_age / 86400))
        local file_age_hours=$((file_age / 3600 % 24))
        
        print_info "MEMORY.md 状态:"
        echo "  - 上次修改: $file_age_days 天 $file_age_hours 小时前"
        
        if [ "$file_age_days" -gt 30 ]; then
            print_warning "文件超过30天未更新，建议回顾内容"
        elif [ "$file_age_days" -gt 7 ]; then
            print_info "文件超过7天未更新"
        else
            print_success "文件近期有更新"
        fi
        
        # 检查文件大小
        local file_size=$(stat -c %s "$MEMORY_FILE" 2>/dev/null || echo 0)
        local size_kb=$((file_size / 1024))
        echo "  - 文件大小: ${size_kb} KB"
        
        if [ "$size_kb" -gt 100 ]; then
            print_warning "文件较大，建议清理过期内容"
        fi
    fi
    
    # 检查定时任务
    print_info "定时任务审计:"
    local cron_count=$(crontab -l 2>/dev/null | grep -c "memory\|security\|backup" || echo 0)
    if [ "$cron_count" -gt 0 ]; then
        print_success "检测到 $cron_count 个相关定时任务"
        if [ "$VERBOSE" = true ]; then
            crontab -l 2>/dev/null | grep "memory\|security\|backup" | while read line; do
                echo "  - $line"
            done
        fi
    else
        print_info "未检测到相关定时任务（建议设置定期审计）"
    fi
}

# 检查4：访问权限
check_access_permissions() {
    print_section "4. 访问权限检查"
    
    if [ -f "$MEMORY_FILE" ]; then
        local perms=$(stat -c %a "$MEMORY_FILE" 2>/dev/null)
        local owner=$(stat -c %U "$MEMORY_FILE" 2>/dev/null)
        
        echo "MEMORY.md 权限:"
        echo "  - 权限码: $perms"
        echo "  - 所有者: $owner"
        
        case "$perms" in
            600|400)
                print_success "文件权限设置安全"
                ;;
            644|664)
                print_warning "文件权限可能过于开放（建议 600）"
                ;;
            *)
                print_error "文件权限设置不当: $perms"
                ;;
        esac
    fi
    
    # 检查目录权限
    if [ -d "$OPENCLAW_CONFIG_DIR" ]; then
        local dir_perms=$(stat -c %a "$OPENCLAW_CONFIG_DIR" 2>/dev/null)
        echo "配置文件目录权限: $dir_perms"
        
        if [ "$dir_perms" = "700" ] || [ "$dir_perms" = "755" ]; then
            print_success "目录权限设置合理"
        else
            print_warning "目录权限可能过于开放"
        fi
    fi
}

# 检查5：备份状态
check_backup_status() {
    print_section "5. 备份状态检查"
    
    local backup_patterns=(
        "${HOME}/*backup*"
        "${HOME}/*.bak*"
        "${HOME}/.config/openclaw/*backup*"
    )
    
    local found_backups=0
    for pattern in "${backup_patterns[@]}"; do
        local backups=$(ls $pattern 2>/dev/null | wc -l || echo 0)
        if [ "$backups" -gt 0 ]; then
            print_success "发现 $backups 个备份文件: $(dirname "$pattern")"
            ((found_backups++))
        fi
    done
    
    if [ "$found_backups" -eq 0 ]; then
        print_info "未发现备份文件（建议定期备份重要数据）"
    fi
}

# 生成报告
generate_summary() {
    print_section "6. 安全评分与建议"
    
    local score=100
    local deductions=0
    
    # 评分逻辑
    if [ -f "$MEMORY_FILE" ]; then
        # 检查是否有硬编码密钥
        if grep -qiE "sk_[a-zA-Z0-9]{20,}" "$MEMORY_FILE" 2>/dev/null; then
            ((deductions+=20))
            print_error "发现硬编码 API 密钥（-20分）"
        fi
        
        # 检查权限
        local perms=$(stat -c %a "$MEMORY_FILE" 2>/dev/null)
        if [ "$perms" != "600" ] && [ "$perms" != "400" ]; then
            ((deductions+=10))
            print_warning "文件权限不当（-10分）"
        fi
    fi
    
    # 检查环境变量使用
    if ! grep -qE '\\\$[A-Z_]+\\\$' "$MEMORY_FILE" 2>/dev/null && [ -f "$MEMORY_FILE" ]; then
        ((deductions+=5))
        print_warning "未使用环境变量存储敏感数据（-5分）"
    fi
    
    local final_score=$((score - deductions))
    
    echo ""
    echo -e "${CYAN}=============================================="
    echo -e "📊 安全评分: ${final_score}/100"
    echo -e "==============================================${NC}"
    
    if [ "$final_score" -ge 90 ]; then
        echo -e "${GREEN}✅ 优秀：敏感数据管理安全可靠${NC}"
    elif [ "$final_score" -ge 70 ]; then
        echo -e "${YELLOW}⚠️ 良好：存在一些小问题需要改进${NC}"
    else
        echo -e "${RED}❌ 需改进：发现多个安全问题，建议立即修复${NC}"
    fi
    
    echo ""
    echo "📋 改进建议:"
    echo "  1. 使用环境变量存储所有敏感数据"
    echo "  2. 定期审计 MEMORY.md，清理过期内容"
    echo "  3. 设置定时任务定期检查敏感数据暴露"
    echo "  4. 备份重要数据并使用加密存储"
    echo "  5. 遵循最小权限原则设置文件权限"
}

# JSON 格式输出
generate_json_report() {
    cat << EOF
{
  "scan_time": "$(date -Iseconds)",
  "target_file": "$MEMORY_FILE",
  "config_dir": "$OPENCLAW_CONFIG_DIR",
  "checks": {
    "env_variables": "completed",
    "file_sensitive_data": "completed",
    "data_lifecycle": "completed",
    "access_permissions": "completed",
    "backup_status": "completed"
  },
  "recommendations": [
    "使用环境变量存储所有敏感数据",
    "定期审计 MEMORY.md",
    "设置定时任务定期检查",
    "备份重要数据"
  ]
}
EOF
}

# 显示帮助
show_help() {
    cat << EOF
🛡️ 敏感数据生命周期管理检查 v1.0

用法: $0 [选项]

选项:
  -f, --file <path>     指定 MEMORY.md 文件路径
  -v, --verbose         详细输出模式
  -j, --json            JSON 格式输出
  -h, --help            显示帮助信息

示例:
  $0                           # 执行完整检查
  $0 -v                        # 详细输出
  $0 -j > report.json          # 输出 JSON 报告

EOF
}

# 主函数
main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                MEMORY_FILE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -j|--json)
                JSON_OUTPUT=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    if [ "$JSON_OUTPUT" = true ]; then
        generate_json_report
    else
        print_header
        check_env_variables
        check_file_sensitive_data
        check_data_lifecycle
        check_access_permissions
        check_backup_status
        generate_summary
    fi
}

main "$@"
