# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# ================================================
# 记忆文件审计脚本 v1.0
# 用于扫描记忆文件中的敏感数据并生成清理建议
# ================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
SCAN_DIR="${HOME}/.config/openclaw"
MEMORY_FILE=""
SENSITIVE_PATTERNS_FILE=""
VERBOSE=false
AUTO_FIX=false
REPORT_FORMAT="terminal"

# 敏感数据检测模式
SENSITIVE_PATTERNS=(
    "password"
    "secret"
    "api[_-]?key"
    "token"
    "credential"
    "ak[_-]?sk"
    "access[_-]?key"
    "private[_-]?key"
    "auth"
)

# 初始化
init() {
    # 默认扫描路径
    if [ -z "$MEMORY_FILE" ]; then
        MEMORY_FILE="${HOME}/.config/openclaw/MEMORY.md"
    fi
    
    if [ -z "$SENSITIVE_PATTERNS_FILE" ]; then
        SENSITIVE_PATTERNS_FILE="$(dirname "$0")/data/sensitive-patterns.txt"
    fi
}

# 打印彩色消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# 检查文件是否存在
check_files() {
    if [ ! -f "$MEMORY_FILE" ]; then
        print_warning "MEMORY.md 文件不存在: $MEMORY_FILE"
        print_info "将扫描整个配置目录: $SCAN_DIR"
        SCAN_DIR="$MEMORY_FILE"
        MEMORY_FILE=""
    fi
}

# 扫描敏感数据
scan_sensitive_data() {
    local file="$1"
    local findings=()
    
    # 检查常见敏感数据模式
    while IFS= read -r line; do
        local pattern="$line"
        if grep -qiE "$pattern" "$file" 2>/dev/null; then
            local matches=$(grep -niE "$pattern" "$file" 2>/dev/null | head -5)
            findings+=("发现敏感模式: $pattern")
            if [ "$VERBOSE" = true ]; then
                while IFS= read -r match; do
                    findings+=("  行内容: $(echo "$match" | sed 's/:.*/: ***敏感数据***/')")
                done <<< "$matches"
            fi
        fi
    done < <(printf '%s\n' "${SENSITIVE_PATTERNS[@]}")
    
    printf '%s\n' "${findings[@]}"
}

# 检查凭证存储方式
check_credential_storage() {
    local file="$1"
    local issues=()
    local recommendations=()
    
    # 检查是否直接存储密钥
    if grep -qiE "sk_[a-zA-Z0-9]" "$file" 2>/dev/null; then
        issues+=("⚠️ 发现疑似API密钥明文存储")
        recommendations+=("✓ 使用环境变量存储API密钥，不要直接写入文件")
    fi
    
    # 检查是否使用环境变量
    if grep -qiE '\\\$[A-Z_]+\\\$' "$file" 2>/dev/null; then
        print_success "检测到使用环境变量存储敏感信息"
    else
        issues+=("⚠️ 未检测到环境变量使用模式")
        recommendations+=("✓ 推荐使用 \${VAR_NAME} 格式引用环境变量")
    fi
    
    # 检查日志中的敏感信息
    if grep -qiE "password.*=|token.*=" "$file" 2>/dev/null; then
        issues+=("⚠️ 配置中可能包含敏感参数")
        recommendations+=("✓ 确保敏感参数通过环境变量或安全配置注入")
    fi
    
    printf '%s\n' "${issues[@]}"
    printf '%s\n' "${recommendations[@]}"
}

# 检查数据生命周期
check_data_lifecycle() {
    local file="$1"
    local issues=()
    local recommendations=()
    
    # 检查数据创建时间
    if [ -f "$file" ]; then
        local last_modified=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1)
        local file_age_days=$(( ($(date +%s) - $(stat -c %Y "$file")) / 86400 ))
        
        if [ "$file_age_days" -gt 90 ]; then
            issues+=("⚠️ 文件超过90天未更新: ${file_age_days}天")
            recommendations+=("✓ 建议定期审计和清理过期数据")
        fi
        
        if [ "$file_age_days" -gt 30 ]; then
            issues+=("⚠️ 文件超过30天未更新")
            recommendations+=("✓ 建议回顾并更新记忆内容，删除过期信息")
        fi
    fi
    
    # 检查临时数据
    local temp_patterns=("tmp" "temp" "cache" "backup")
    for pattern in "${temp_patterns[@]}"; do
        if grep -qiE "$pattern" "$file" 2>/dev/null; then
            issues+=("⚠️ 发现疑似临时数据引用")
            recommendations+=("✓ 临时数据应及时清理，避免长期保留")
            break
        fi
    done
    
    printf '%s\n' "${issues[@]}"
    printf '%s\n' "${recommendations[@]}"
}

# 检查访问权限
check_permissions() {
    local file="$1"
    local issues=()
    
    if [ -f "$file" ]; then
        local perms=$(stat -c %a "$file" 2>/dev/null)
        
        # 检查是否过于开放
        if [ "$perms" = "777" ] || [ "$perms" = "666" ]; then
            issues+=("⚠️ 文件权限过于开放: $perms")
            issues+=("✓ 建议设置权限为 600 或 640")
        elif [ "$perms" = "755" ] || [ "$perms" = "644" ]; then
            print_success "文件权限设置合理: $perms"
        else
            print_info "文件权限: $perms"
        fi
    fi
    
    # 检查目录权限
    local dir=$(dirname "$file")
    if [ -d "$dir" ]; then
        local dir_perms=$(stat -c %a "$dir" 2>/dev/null)
        if [ "$dir_perms" = "777" ] || [ "$dir_perms" = "775" ]; then
            issues+=("⚠️ 目录权限可能过于开放: $dir_perms")
            issues+=("✓ 建议设置目录权限为 700 或 750")
        fi
    fi
    
    printf '%s\n' "${issues[@]}"
}

# 生成安全建议
generate_recommendations() {
    echo ""
    echo "=============================================="
    echo "🛡️  安全存储最佳实践"
    echo "=============================================="
    echo ""
    echo "1. 【敏感数据处理】"
    echo "   • API密钥、密码、Token等敏感信息不要直接写入文件"
    echo "   • 使用环境变量存储: export API_KEY=\${API_KEY}"
    echo "   • 在脚本中使用: \${VAR_NAME} 格式引用"
    echo ""
    echo "2. 【数据生命周期管理】"
    echo "   • 定期审计记忆文件（建议每30天）"
    echo "   • 及时清理过期的敏感数据和临时文件"
    echo "   • 记录数据创建和更新时间，便于追踪"
    echo ""
    echo "3. 【访问权限控制】"
    echo "   • 文件权限设置为 600 或 640"
    echo "   • 目录权限设置为 700 或 750"
    echo "   • 避免使用过于开放的权限如 777"
    echo ""
    echo "4. 【备份与恢复】"
    echo "   • 敏感数据备份时使用加密"
    echo "   • 备份文件存储在安全位置"
    echo "   • 记录备份时间便于管理"
    echo ""
    echo "5. 【监控与告警】"
    echo "   • 配置定时任务定期检查敏感数据暴露"
    echo "   • 设置异常访问告警"
    echo "   • 记录安全审计日志"
    echo ""
}

# 执行修复
apply_fixes() {
    local file="$1"
    
    if [ "$AUTO_FIX" = true ]; then
        print_info "正在应用自动修复..."
        
        # 备份原文件
        local backup="${file}.bak.$(date +%Y%m%d%H%M%S)"
        cp "$file" "$backup"
        print_success "已创建备份: $backup"
        
        # 修复权限
        chmod 600 "$file"
        print_success "已修复文件权限为 600"
        
        # 修复目录权限
        local dir=$(dirname "$file")
        chmod 700 "$dir"
        print_success "已修复目录权限为 700"
        
        print_success "自动修复完成！"
    else
        print_info "使用 --fix 参数可启用自动修复"
    fi
}

# 生成报告
generate_report() {
    local file="$1"
    local report_file=""
    
    if [ "$REPORT_FORMAT" = "json" ]; then
        report_file="/tmp/memory-audit-$(date +%Y%m%d).json"
        cat > "$report_file" << EOF
{
  "scan_time": "$(date -Iseconds)",
  "target_file": "$file",
  "sensitive_findings": [],
  "credential_issues": [],
  "lifecycle_issues": [],
  "permission_issues": [],
  "recommendations": []
}
EOF
        print_success "JSON报告已生成: $report_file"
    else
        echo ""
        echo "=============================================="
        echo "📋 记忆文件审计报告"
        echo "=============================================="
        echo "扫描时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "目标文件: $file"
        echo ""
        
        # 敏感数据扫描
        echo "【敏感数据扫描】"
        local sensitive_findings=$(scan_sensitive_data "$file")
        if [ -n "$sensitive_findings" ]; then
            echo "$sensitive_findings"
        else
            print_success "未发现明显敏感数据模式"
        fi
        echo ""
        
        # 凭证存储检查
        echo "【凭证存储方式】"
        check_credential_storage "$file"
        echo ""
        
        # 数据生命周期检查
        echo "【数据生命周期】"
        check_data_lifecycle "$file"
        echo ""
        
        # 权限检查
        echo "【访问权限】"
        check_permissions "$file"
        echo ""
        
        # 安全建议
        generate_recommendations
        
        # 修复选项
        if [ "$AUTO_FIX" = false ]; then
            echo "=============================================="
            echo "🔧 可用修复选项"
            echo "=============================================="
            echo "  --fix    应用自动修复（备份+修复权限）"
            echo "=============================================="
        fi
    fi
}

# 显示帮助
show_help() {
    cat << EOF
🛡️ 记忆文件审计工具 v1.0

用法: $0 [选项]

选项:
  -f, --file <path>        指定要审计的记忆文件路径
  -d, --dir <path>          指定要扫描的目录
  -v, --verbose             详细输出模式
  -f, --fix                 应用自动修复
  -o, --output <format>     输出格式 (terminal/json)
  -h, --help                显示帮助信息

示例:
  $0                                    # 审计默认 MEMORY.md
  $0 -f ~/memory.txt                   # 审计指定文件
  $0 -d ~/.config/openclaw -v          # 详细扫描目录
  $0 --fix                              # 审计并自动修复

EOF
}

# 主函数
main() {
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                MEMORY_FILE="$2"
                shift 2
                ;;
            -d|--dir)
                SCAN_DIR="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --fix)
                AUTO_FIX=true
                shift
                ;;
            -o|--output)
                REPORT_FORMAT="$2"
                shift 2
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
    
    # 初始化
    init
    
    # 检查文件
    check_files
    
    # 执行审计
    print_info "开始审计记忆文件..."
    
    if [ -n "$MEMORY_FILE" ] && [ -f "$MEMORY_FILE" ]; then
        generate_report "$MEMORY_FILE"
        apply_fixes "$MEMORY_FILE"
    elif [ -d "$SCAN_DIR" ]; then
        print_info "扫描目录: $SCAN_DIR"
        while IFS= read -r file; do
            if [[ "$file" == *.md ]] || [[ "$file" == *memory* ]]; then
                echo ""
                echo ">>> 审计文件: $file"
                generate_report "$file"
            fi
        done < <(find "$SCAN_DIR" -type f 2>/dev/null)
    else
        print_error "未找到有效的文件或目录"
        exit 1
    fi
    
    print_success "审计完成！"
}

# 运行主函数
main "$@"
