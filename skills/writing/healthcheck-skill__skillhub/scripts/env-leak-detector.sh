# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"


#!/bin/bash
# =============================================================================
# 环境变量泄露检测脚本 v1.0
# 
# 功能：检测环境变量中的敏感信息泄露风险
# 来源：@minima_digital_butler_4782 的专业建议
#
# 检测项：
#   1. /proc/{pid}/environ 泄露检测
#   2. 容器环境权限控制
#   3. API Key 轮换机制检查
#   4. 敏感变量暴露检测
#
# 使用方法：
#   ./env-leak-detector.sh              # 完整检测
#   ./env-leak-detector.sh --quick        # 快速检测
#   ./env-leak-detector.sh --fix          # 自动修复建议
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 敏感关键词
SENSITIVE_PATTERNS="API_KEY|APIKEY|SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|AUTH|CREDENTIAL|ACCESS_KEY|SECRET_KEY"

# 日志目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports"
ENV_LEAK_LOG="${REPORT_DIR}/env-leak-detection-$(date +%Y%m%d).log"

# 创建报告目录
mkdir -p "$REPORT_DIR"

# =============================================================================
# 辅助函数
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$ENV_LEAK_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$ENV_LEAK_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$ENV_LEAK_LOG"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$ENV_LEAK_LOG"
}

# =============================================================================
# 检测函数
# =============================================================================

# 检测当前环境的敏感变量
check_current_env() {
    log_info "=== 检测当前环境中的敏感变量 ==="
    
    local sensitive_count=0
    local sensitive_vars=()
    
    # 检查常见敏感环境变量
    for var in $(env | grep -iE "$SENSITIVE_PATTERNS" | cut -d= -f1); do
        sensitive_count=$((sensitive_count + 1))
        sensitive_vars+=("$var")
    done
    
    if [ $sensitive_count -gt 0 ]; then
        log_warn "发现 $sensitive_count 个敏感环境变量："
        for var in "${sensitive_vars[@]}"; do
            echo "  - $var"
        done
        echo "  建议：使用环境变量引用而非直接定义敏感值"
        return 1
    else
        log_success "未在当前环境中发现明显暴露的敏感变量"
        return 0
    fi
}

# 检测 /proc/{pid}/environ 泄露风险
check_proc_environ() {
    log_info "=== 检测 /proc/{pid}/environ 泄露风险 ==="
    
    # 检查容器环境
    if [ -f /.dockerenv ] || grep -q "docker\|container" /proc/1/cgroup 2>/dev/null; then
        log_info "检测到容器环境"
        
        # 检查进程隔离
        local accessible_proc=$(ls /proc/*/environ 2>/dev/null | wc -l)
        if [ "$accessible_proc" -gt 100 ]; then
            log_error "🔴 发现严重的进程隔离问题"
            echo "  问题：可访问 $accessible_proc 个进程的 /proc/*/environ 文件"
            echo "  风险：可能读取其他容器的敏感环境变量"
            echo "  建议："
            echo "    1. 使用 Kubernetes NetworkPolicy 限制容器间访问"
            echo "    2. 启用 PodSecurityPolicy"
            echo "    3. 使用不同的 Service Account"
            echo "    4. 考虑使用 Secret 管理敏感变量"
            return 2
        else
            log_success "容器进程隔离配置正常"
            return 0
        fi
    else
        log_info "非容器环境，跳过容器特定检查"
        return 0
    fi
}

# 检测 API Key 轮换机制
check_key_rotation() {
    log_info "=== 检测 API Key 轮换机制 ==="
    
    local issues=0
    
    # 检查是否存在密钥配置文件
    local key_config_files=$(find /workspace -name "*.env" -o -name ".env*" -o -name "*secret*" -o -name "*key*" 2>/dev/null | head -20)
    
    if [ -n "$key_config_files" ]; then
        log_warn "发现潜在的密钥配置文件："
        echo "$key_config_files" | head -10 | while read -r file; do
            echo "  - $file"
        done
        
        # 检查是否设置了过期提醒
        if ! grep -rq "ROTATION\|EXPIRE\|RENEW" /workspace 2>/dev/null; then
            log_warn "未检测到密钥轮换相关配置"
            echo "  建议："
            echo "    1. 为每个 API Key 设置有效期"
            echo "    2. 建立密钥轮换提醒机制"
            echo "    3. 记录密钥使用日志"
            echo "    4. 定期审计密钥使用情况"
            issues=$((issues + 1))
        fi
    else
        log_success "未发现明显的密钥配置文件暴露"
    fi
    
    return $issues
}

# 检测敏感信息硬编码
check_hardcoded_secrets() {
    log_info "=== 检测硬编码敏感信息 ==="
    
    local hardcoded_count=0
    
    # 检查常见文件类型中的硬编码密钥
    for ext in "json" "yaml" "yml" "sh" "py" "js" "ts"; do
        local files=$(find /workspace -name "*.$ext" -type f 2>/dev/null | head -50)
        for file in $files; do
            if grep -rqE "[a-zA-Z0-9]{20,}(API|KEY|SECRET|TOKEN)" "$file" 2>/dev/null; then
                hardcoded_count=$((hardcoded_count + 1))
            fi
        done
    done
    
    if [ $hardcoded_count -gt 0 ]; then
        log_error "🔴 发现 $hardcoded_count 个文件可能包含硬编码密钥"
        echo "  建议："
        echo "    1. 将敏感信息移至环境变量"
        echo "    2. 使用 .gitignore 排除敏感文件"
        echo "    3. 使用密钥管理服务（如 AWS Secrets Manager）"
        echo "    4. 启用 Git 钩子防止提交敏感信息"
        return 1
    else
        log_success "未检测到明显的硬编码密钥"
        return 0
    fi
}

# 检测调试接口暴露
check_debug_interfaces() {
    log_info "=== 检测调试接口暴露 ==="
    
    local issues=0
    
    # 检查常见调试端口
    local debug_ports=("9090" "5005" "50051" "8000" "8888" "3000")
    
    # 检查 OpenClaw 相关进程
    if pgrep -f "openclaw" >/dev/null 2>&1; then
        log_info "检测到 OpenClaw 进程运行中"
        
        # 检查是否有暴露的调试端口
        for port in "${debug_ports[@]}"; do
            if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
                log_warn "发现可能暴露的调试端口：$port"
                issues=$((issues + 1))
            fi
        done
    fi
    
    if [ $issues -gt 0 ]; then
        echo "  建议："
        echo "    1. 确保调试端口仅对内网开放"
        echo "    2. 使用防火墙规则限制访问"
        echo "    3. 生产环境禁用调试接口"
        echo "    4. 启用调试认证"
        return 1
    else
        log_success "未发现明显暴露的调试接口"
        return 0
    fi
}

# =============================================================================
# 修复建议生成
# =============================================================================

generate_fix_suggestions() {
    log_info "=== 生成修复建议 ==="
    
    cat << 'EOF'
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    环境变量安全加固建议                              ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  1. 密钥管理最佳实践                                                 ║
    ║     ├─ 使用环境变量引用而非硬编码                                    ║
    ║     ├─ 使用密钥管理服务（AWS Secrets Manager, HashiCorp Vault）      ║
    ║     ├─ 定期轮换密钥（建议每30-90天）                               ║
    ║     └─ 记录密钥使用审计日志                                         ║
    ║                                                                      ║
    ║  2. 容器环境安全                                                    ║
    ║     ├─ 使用 Kubernetes NetworkPolicy 限制容器间通信                   ║
    ║     ├─ 避免在容器中存储敏感信息                                     ║
    ║     ├─ 使用 ReadOnlyRootFilesystem                                   ║
    ║     └─ 启用 Pod Security Context                                    ║
    ║                                                                      ║
    ║  3. 进程隔离                                                        ║
    ║     ├─ 限制 /proc 访问                                              ║
    ║     ├─ 使用 seccomp 限制系统调用                                     ║
    ║     └─ 避免特权容器                                                 ║
    ║                                                                      ║
    ║  4. Git 安全                                                        ║
    ║     ├─ 添加 .gitignore 排除敏感文件                                  ║
    ║     ├─ 使用 pre-commit 钩子检查敏感信息                              ║
    ║     ├─ 定期运行 git-secrets 或 gitleaks                            ║
    ║     └─ 使用 git filter-branch 清除历史敏感信息                       ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
EOF
}

# =============================================================================
# 生成报告
# =============================================================================

generate_report() {
    log_info "=== 生成环境变量安全审计报告 ==="
    
    local report_file="${REPORT_DIR}/env-security-report-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "report_type": "environment_variable_security_audit",
  "timestamp": "$(date -Iseconds)",
  "environment": {
    "hostname": "$(hostname)",
    "user": "$(whoami)",
    "container": "$(grep -q docker /proc/1/cgroup 2>/dev/null && echo 'docker' || echo 'native')"
  },
  "checks": {
    "sensitive_vars": $(check_current_env >/dev/null 2>&1; echo $?),
    "proc_environ": $(check_proc_environ >/dev/null 2>&1; echo $?),
    "key_rotation": $(check_key_rotation >/dev/null 2>&1; echo $?),
    "hardcoded_secrets": $(check_hardcoded_secrets >/dev/null 2>&1; echo $?),
    "debug_interfaces": $(check_debug_interfaces >/dev/null 2>&1; echo $?)
  },
  "recommendations": [
    "使用环境变量引用敏感信息",
    "启用密钥轮换机制",
    "加强容器进程隔离",
    "添加 Git 安全钩子",
    "定期审计敏感信息暴露"
  ],
  "log_file": "$ENV_LEAK_LOG"
}
EOF
    
    log_success "报告已生成：$report_file"
    echo "$report_file"
}

# =============================================================================
# 主流程
# =============================================================================

main() {
    local mode="${1:-full}"
    
    echo "========================================================================"
    echo "           环境变量安全检测 - Environment Variable Security Check"
    echo "========================================================================"
    echo "时间：$(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================================================"
    echo ""
    
    # 初始化日志
    echo "环境变量安全检测开始" > "$ENV_LEAK_LOG"
    
    case $mode in
        --quick|-q)
            log_info "执行快速检测模式"
            check_current_env
            check_proc_environ
            ;;
        --fix|-f)
            log_info "执行完整检测并生成修复建议"
            check_current_env || true
            check_proc_environ || true
            check_key_rotation || true
            check_hardcoded_secrets || true
            check_debug_interfaces || true
            generate_fix_suggestions
            ;;
        *)
            log_info "执行完整环境变量安全检测"
            check_current_env || true
            check_proc_environ || true
            check_key_rotation || true
            check_hardcoded_secrets || true
            check_debug_interfaces || true
            ;;
    esac
    
    echo ""
    echo "========================================================================"
    echo "                         检测完成"
    echo "========================================================================"
    echo "详细日志：$ENV_LEAK_LOG"
    echo ""
}

# 执行主流程
main "$@"
